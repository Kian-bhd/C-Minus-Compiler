class Codegen:
    def __init__(self):
        self.SS = []
        self.PB = ['JP, ?, , ']
        self.BS = []
        self.RS = []
        self.i = 1
        self.cur_type = 'void'
        self.cur_scope = 0
        self.addr = 100
        self.temp_addr = 500
        self.symbol_table = []  # [['var1', type1, addr1, size, scope], ['var2', type2, addr2, size, scope], ['fun1', 'func', [return_value, argument_list, return_address, cur_i], argcnt, scope]]
        self.op_dict = {'+': 'ADD', '-': 'SUB', '*': 'MULT', '<': 'LT', '==': 'EQ'}
        self.main_addr = None

    def code_gen(self, action, lexeme):
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
            idx = self.SS.pop()
            if str(idx).startswith('#'):
                idx = idx[1:]
            addr = self.SS.pop()
            self.SS.append((int(addr) + 4 * (int(idx))))
        elif action == '#push_op':
            self.SS.append(lexeme)
        elif action == '#eval':
            second = self.SS.pop()
            operator = self.SS.pop()
            first = self.SS.pop()
            result = self.get_temp()
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
            print(jmp_addr)
            print(self.SS)
            self.PB[jmp_addr] = f'JP, {self.i}, , '
        elif action == '#neg':
            result = self.get_temp()
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
            self.cur_scope += 1
        elif action == '#scope_minus':
            for record in self.symbol_table[::-1]:
                print(record)
                if record[4] == self.cur_scope:
                    del self.symbol_table[-1]
            self.cur_scope -= 1
        elif action == '#func_init':
            self.symbol_table.append('>>')
        elif action == '#func_symbol':
            args_idx = self.symbol_table.index('>>')
            args_list = self.symbol_table[args_idx + 1:]
            argcnt = len(args_list)
            self.symbol_table.pop(args_idx)
            return_val = self.get_temp()
            return_addr = self.get_temp()
            self.SS.append(return_val)
            self.SS.append(return_addr)
            func_name = self.symbol_table[args_idx - 1][0]
            self.symbol_table.append([func_name, 'func', [return_val, args_list, return_addr, self.i], argcnt, self.cur_scope])
            if func_name == 'main':
                self.main_addr = self.i
                self.PB[0] = f'JP, {self.main_addr}, , '
        elif action == '#new_rs':
            self.RS.append('<')
        elif action == '#return':
            self.RS.append((self.i, self.SS.pop()))
            self.insert_code('ASSIGN', '?', '?', )
            self.insert_code('JP', '?')
        elif action == '#end_rs':
            return_addr = self.SS.pop()
            return_value = self.SS.pop()
            ret_elem = self.RS.pop()
            while ret_elem != '<':
                self.PB[ret_elem[0]] = f'ASSIGN, {ret_elem[1]}, {return_value}'
                self.PB[ret_elem[0] + 1] = f'JP, @{return_addr}, ,'
                ret_elem = self.RS.pop()
        elif action == '#implicit_zero_return':
            self.SS.append('#0')

    def get_temp(self):
        tmp = self.temp_addr
        self.temp_addr += 4
        return tmp

    def insert_code(self, one, two, three='', four=''):
        self.PB.append(f'{one}, {two}, {three}, {four}')
        self.print_output()
        self.i += 1

    def update_index(self, addr, idx):
        for var in self.symbol_table[::-1]:
            if var[2] == addr:
                var[3] = idx
                print('Symbol Table:')
                print(self.symbol_table)
                return

    def find_addr(self, lexeme, insert=False):
        for record in self.symbol_table[::-1]:
            if record[0] == lexeme:
                return record[2]

        if not insert:
            return None
        self.symbol_table.append([lexeme, self.cur_type, self.temp_addr, 1, self.cur_scope])
        self.temp_addr += 4
        return self.symbol_table[-1][2]

    def print_output(self):
        for i in range(len(self.PB)):
            print(f'{i}\t({self.PB[i]})')
