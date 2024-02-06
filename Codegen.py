class Codegen:
    def __init__(self):
        self.elem_len = 0
        self.return_val_reg = 96
        self.return_addr_reg = 92
        self.stack_pointer = 88
        self.SS = []
        self.PB = [f'ASSIGN, #0, {self.return_addr_reg}, ', f'ASSIGN, #0, {self.return_val_reg}, ',
                   f'ASSIGN, #3000, {self.stack_pointer}']
        self.BS = []
        self.RS = []
        self.main_addr = None
        self.output_addr = 'output'
        self.main_jp = 3
        self.seen_fun = False
        self.i = 3
        self.cur_type = 'void'
        self.cur_scope = 0
        self.addr = 100
        self.temp_addr = 500
        self.symbol_table = []  # [['var1', type1, addr1, size, scope], ['var2', type2, addr2, size, scope], ['fun1', 'func', [return_value, argument_list, return_address, cur_i], argcnt, scope, func_addr]]
        self.temp_list = {}
        for i in range(100):
            self.temp_list[i] = []
        self.op_dict = {'+': 'ADD', '-': 'SUB', '*': 'MULT', '<': 'LT', '==': 'EQ'}

    def code_gen(self, action, lexeme):
        # print(self.temp_list)
        print('Symbol Table:')
        print(self.symbol_table)
        print(action, ':', lexeme, ':', self.SS)
        if action == '#set_id_type':
            self.cur_type = lexeme
        elif action == '#pid_dec':
            addr = self.find_addr(lexeme, True)
            self.SS.append(addr)
        elif action == '#pid':
            addr = self.find_addr(lexeme, False)
            self.SS.append(addr)
        elif action == '#assign':
            self.insert_code('ASSIGN', self.SS[-1], self.SS[-2])
            self.SS.pop()
        elif action == '#p_index':
            self.SS.append(lexeme)
        elif action == '#set_index':
            self.update_index(self.SS[-2], self.SS[-1])
            self.temp_addr += 4 * (int(self.SS[-1]) - 1)
            self.SS.pop()
            self.SS.pop()
        elif action == '#pnum':
            self.SS.append(f'#{lexeme}')
        elif action == '#p_array_addr':
            temp = self.get_temp()
            self.temp_list[self.cur_scope].append(temp)
            idx = self.SS.pop()
            addr = self.SS.pop()
            self.insert_code('MULT', f'{idx}', '#4', f'{temp}')
            self.insert_code('ADD', f'{addr}', f'{temp}', f'{temp}')
            self.SS.append(f'@{temp}')
        elif action == '#push_op':
            self.SS.append(lexeme)
        elif action == '#eval':
            second = self.SS.pop()
            operator = self.SS.pop()
            first = self.SS.pop()
            result = self.get_temp()
            self.temp_list[self.cur_scope].append(result)
            self.insert_code(self.op_dict[operator], first, second, str(result))
            self.SS.append(result)
        elif action == '#save':
            self.SS.append(self.i)
            self.PB.append('')
            self.i += 1
        elif action == '#jpf_save':
            bp_addr = self.i
            self.PB.append('')
            self.i += 1
            jpf_addr = self.SS.pop()
            jpf_cond = self.SS.pop()
            print(jpf_cond, jpf_addr)
            self.PB[jpf_addr] = f'JPF, {jpf_cond}, {self.i},'
            self.SS.append(bp_addr)
        elif action == '#jmp':
            jmp_addr = self.SS.pop()
            self.PB[jmp_addr] = f'JP, {self.i}, , '
        elif action == '#neg':
            result = self.get_temp()
            self.temp_list[self.cur_scope].append(result)
            self.insert_code('SUB', '#0', self.SS.pop(), str(result))
            self.SS.append(result)
        elif action == '#cleanup':
            self.SS.pop()
        elif action == '#label':
            self.SS.append(self.i)
        elif action == '#while':
            bp_addr = self.SS.pop()
            cond = self.SS.pop()
            jmp_target = self.SS.pop()
            self.PB[bp_addr] = f'JPF, {cond}, {self.i + 1}, '
            self.insert_code('JP', jmp_target)
        elif action == '#new_bs':
            self.BS.append('<')
        elif action == '#break':
            self.BS.append(self.i)
            self.insert_code('JP', '?')
        elif action == '#end_bs':
            break_addr = self.BS.pop()
            while break_addr != '<':
                self.PB[break_addr] = f'JP, {self.i}, , '
                break_addr = self.BS.pop()
        elif action == '#scope_plus':
            if self.seen_fun is False:
                main_meow = self.PB.pop()
                self.PB.append('')
                self.PB.append(main_meow)
                self.main_jp -= 1
                self.i += 1
                self.seen_fun = True
            self.cur_scope += 1
        elif action == '#scope_minus':
            for record in self.symbol_table[::-1]:
                print(record)
                if record[1] != 'func' and record[4] == self.cur_scope:
                    del self.symbol_table[self.symbol_table.index(record)]
            self.temp_list[self.cur_scope].clear()
            self.cur_scope -= 1
        elif action == '#func_init':
            self.symbol_table.append('>>')
        elif action == '#func_symbol':
            args_idx = self.symbol_table.index('>>')
            args_list = self.symbol_table[args_idx + 1:]
            argcnt = len(args_list)
            self.symbol_table.pop(args_idx)

            func_name = self.symbol_table[args_idx - 1][0]
            func_addr = self.symbol_table[args_idx - 1][2]
            del self.symbol_table[args_idx - 1]
            self.symbol_table.append(
                [func_name, 'func', [None, args_list, None, self.i - 1], argcnt, self.cur_scope - 1, func_addr])
            if func_name == 'main':
                self.main_addr = self.i
                if self.main_jp < self.i:
                    self.PB[self.main_jp] = f'JP, {self.main_addr}, , '
                else:
                    self.insert_code('JP', f'{self.main_addr + 1}')
        elif action == '#func_fin':
            pass
        elif action == '#new_rs':
            self.RS.append('<')
        elif action == '#return':
            self.RS.append((self.i, self.SS.pop()))
            self.insert_code('ASSIGN', '?', '?', )
            self.insert_code('JP', '?')
        elif action == '#end_rs':

            ret_elem = self.RS.pop()
            while ret_elem != '<':
                self.PB[ret_elem[0]] = f'ASSIGN, {ret_elem[1]}, {self.return_val_reg}'
                self.PB[ret_elem[0] + 1] = f'JP, @{self.return_addr_reg}, ,'
                ret_elem = self.RS.pop()
        elif action == '#implicit_zero_return':
            self.SS.append('#0')
        elif action == '#func_call':

            if self.SS[-1] == 'output':
                self.insert_code('PRINT', f'{100}')
                # self.SS.pop()
            else:
                addresses = []
                temps = []
                for item in self.symbol_table:
                    if item[1] != 'func' and item[4] == self.cur_scope:
                        addresses.append(item[2])
                for address in addresses:
                    self.insert_code('ASSIGN', f'{address}', f'@{self.stack_pointer}')
                    self.insert_code('ADD', f'{self.stack_pointer}', '#4', f'{self.stack_pointer}')

                for temp in self.temp_list[self.cur_scope]:
                    self.insert_code('ASSIGN', f'{temp}', f'@{self.stack_pointer}')
                    self.insert_code('ADD', f'{self.stack_pointer}', '#4', f'{self.stack_pointer}')

                # self.insert_code('ASSIGN', f'{self.return_val_reg}', f'@{self.stack_pointer}')
                # self.insert_code('ADD', f'{self.stack_pointer}', '#4', f'{self.stack_pointer}')
                self.insert_code('ASSIGN', f'{self.return_addr_reg}', f'@{self.stack_pointer}')
                self.insert_code('ADD', f'{self.stack_pointer}', '#4', f'{self.stack_pointer}')

                self.insert_code('ASSIGN', f'#{self.i + 2}', f'{self.return_addr_reg}')
                self.SS.append(self.find_pb_idx(self.SS.pop()) + 1)
                self.insert_code('JP', f'{self.SS[-1]}')

                self.insert_code('SUB', f'{self.stack_pointer}', '#4', f'{self.stack_pointer}')
                self.insert_code('ASSIGN', f'@{self.stack_pointer}', f'{self.return_addr_reg}', )
                # self.insert_code('SUB', f'{self.stack_pointer}', '#4', f'{self.stack_pointer}')
                # self.insert_code('ASSIGN', f'@{self.stack_pointer}', f'{self.return_val_reg}',)

                for temp in self.temp_list[self.cur_scope][::-1]:
                    self.insert_code('SUB', f'{self.stack_pointer}', '#4', f'{self.stack_pointer}')
                    self.insert_code('ASSIGN', f'@{self.stack_pointer}', f'{temp}', )

                for address in addresses[::-1]:
                    self.insert_code('SUB', f'{self.stack_pointer}', '#4', f'{self.stack_pointer}')
                    self.insert_code('ASSIGN', f'@{self.stack_pointer}', f'{address}', )

                func_temp = self.get_temp()
                self.temp_list[self.cur_scope].append(func_temp)
                self.insert_code('ASSIGN', f'{self.return_val_reg}', f'{func_temp}')
                self.SS.pop()
                self.SS.append(func_temp)
            self.addr = 100
        elif action == '#push_arg':
            self.elem_len = self.find_func_argcnt(self.find_func_name(self.SS[-1]))
            self.insert_code('ASSIGN', f'{self.SS.pop()}', f'{self.addr}')
            self.addr += 4
        elif action == '#param_enter':
            self.addr = 100
        elif action == '#param_exit':
            self.addr = 100
        elif action == '#param_is_array':
            self.SS.append('#is_array')
        elif action == '#param_assign':
            if self.SS[-1] == '#is_array':
                pass
            self.insert_code('ASSIGN', f'{self.addr}', f'{self.SS.pop()}', )
            self.addr += 4

        elif action == '#return_anyway':
            if self.main_addr is None:
                self.insert_code('JP', f'@{self.return_addr_reg}')

    def get_temp(self):
        tmp = self.temp_addr
        self.temp_addr += 4
        return tmp

    def insert_code(self, one, two, three='', four=''):
        self.PB.append(f'{one}, {two}, {three}, {four}')
        self.print_output()
        self.i += 1
        if self.seen_fun is False:
            self.main_jp += 1

    def update_index(self, addr, idx):
        for var in self.symbol_table[::-1]:
            if var[2] == addr:
                var[3] = idx
                return

    def find_addr(self, lexeme, insert=False):
        if lexeme == 'output':
            return lexeme
        for record in self.symbol_table[::-1]:
            if record[0] == lexeme:
                if record[1] == 'func':
                    return record[-1]
                else:
                    return record[2]

        if not insert:
            return None
        self.symbol_table.append([lexeme, self.cur_type, self.temp_addr, 1, self.cur_scope])
        self.insert_code('ASSIGN', '#0', str(self.temp_addr))
        self.temp_addr += 4
        return self.symbol_table[-1][2]

    def find_pb_idx(self, addr):
        print("RECORD", addr)
        for record in self.symbol_table[::-1]:
            print(record)
            if record[1] == 'func' and record[-1] == addr:
                return record[2][-1] - 2 * record[3]

    def find_func_name(self, addr):
        for record in self.symbol_table:
            print(record)
            if record[1] == 'func' and str(record[5]) == str(addr):
                return record[0]

    def find_func_argcnt(self, name):
        for record in self.symbol_table:
            if record[1] == 'func' and record[0] == name:
                return record[3]

    def print_output(self):
        print('Symbol Table:')
        print(self.symbol_table)
        for i in range(len(self.PB)):
            print(f'{i}\t({self.PB[i]})')

    def write_output(self):
        with open('output.txt', 'w+') as f:
            for i in range(len(self.PB)):
                f.write(f'{i}\t({self.PB[i]})\n')
