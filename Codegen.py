




# ------------------------------------------------------------------------------------
# ---
from Scanner import Scanner



# 1: 1, 
# 2: 1, 
# 3: 3, 
# 4: 5, 
# 5: 9, 
# 6: 15, 
# 7: 25, 
# 8: 41, 
# 9: 67, 
# 10: 109,

from Scanner import Scanner


class Codegen:
    def __init__(self, scanner: Scanner):
        self.scanner = scanner
        self.elem_len = 0
        self.return_val_reg = 400
        self.return_addr_reg = 404
        self.stack_pointer = 408
        self.stack_start = 3000
        self.SS = []
        self.PB = [f'ASSIGN, #0, {self.return_addr_reg}, ', f'ASSIGN, #0, {self.return_val_reg}, ',
                   f'ASSIGN, #{self.stack_start}, {self.stack_pointer}']
        self.BS = []
        self.RS = []
        self.main_addr = None
        self.output_addr = 'output'
        self.main_jp = 3
        self.seen_fun = False
        self.i = 3
        self.cur_type = 'void'
        self.cur_scope = 0
        self.addr = 412
        self.ARG_START = 412
        self.temp_addr = 500
        self.symbol_table = []  # [['var1', type1, addr1, size, scope], ['var2', type2, addr2, size, scope], [fun1, 'func', [return_value, argument_list, return_address, cur_i], argcnt, scope, func_addr]]
        self.temp_list = {}
        for i in range(1000):
            self.temp_list[i] = []
        self.op_dict = {'+': 'ADD', '-': 'SUB', '*': 'MULT', '<': 'LT', '==': 'EQ'}
        self.semantic_errors = []
        self.line_no = 0

    def code_gen(self, action, lexeme, lineno):
        self.line_no = lineno
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
            if addr == None:
                self.semantic_errors.append(
                    f'#{self.line_no}: Semantic Error! \'{lexeme}\' is not defined.'
                )
            self.SS.append(addr)
        elif action == '#assign':
            self.insert_code('ASSIGN', self.SS[-1], self.SS[-2])
            self.check_type_mismatch(self.SS[-1], self.SS[-2])
            self.SS.pop()
        elif action == '#p_index':
            self.SS.append(lexeme)
        elif action == '#set_index':
            self.update_index(self.SS[-2], int(self.SS[-1]))
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
            self.check_type_mismatch(first, second)
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
            if '<' not in self.BS:
                self.semantic_errors.append(
                    f'#{self.line_no}: Semantic Error! No \'while\' found for \'break\'.')
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
                self.insert_code('PRINT', f'{self.ARG_START}')
                # self.SS.pop()
            else:
                addr = self.SS[-1]
                for record in self.symbol_table:
                    if record[1] == 'func' and record[-1] == addr:
                        if (self.addr - self.ARG_START) // 4 != record[-3]:
                            self.semantic_errors.append(
                                f'#{self.line_no}: Semantic Error! Mismatch in numbers of arguments of \'{record[0]}\'.'
                            )
                addresses = []
                for item in self.symbol_table:
                    if item[1] != 'func' and item[4] > 0:
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
                self.SS.append(self.find_pb_idx(self.SS.pop()))
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
            self.addr = self.ARG_START
        elif action == '#push_arg':
            if len(self.SS) < 1:
                self.semantic_errors.append(
                    f'#{self.line_no}: Semantic Error! Not enough operands.')
                return

            param_counter = (self.addr - self.ARG_START) // 4
            arg_pointer = self.SS.pop()
            arg_record = []
            if self.SS[-1] != 'output':
                func_name = self.find_func_name(self.SS[-1])
                argcnt = int(self.find_func_argcnt(func_name))
                argcnt -= 1
                func_param_list = []
                if param_counter > argcnt:
                    self.addr += 4
                    return
                for record in self.symbol_table:
                    if record[1] == 'func' and record[0] == func_name:
                        func_param_list = record[2][1][param_counter]
                    elif record[1] != 'func' and record[2] == arg_pointer:
                        arg_record = record
                if str(arg_pointer).startswith('#'):
                    arg_record = ['0', 'int', 'address_ha_ha', 1, 'scope_ha_ha']
                elif len(arg_record) == 0:
                    arg_record = ['0', 'int', 'address_ha_ha', 1, 'scope_ha_ha']
                print(arg_record)
                print(func_param_list)
                if func_param_list[1] != arg_record[1] or (func_param_list[3] > 1 and arg_record[3] == 1) or (func_param_list[3] == 1 and arg_record[3] > 1):
                    self.semantic_errors.append(
                        f'#{self.line_no}: Semantic Error! Mismatch in type of argument {param_counter + 1} of \'{func_name}\'. Expected \'{"int" if func_param_list[3] == 1 else "array"}\' but got \'{"array" if arg_record[3] > 1 else "int"}\' instead.'
                    )
            self.insert_code('ASSIGN', f'{arg_pointer}', f'{self.addr}')
            self.addr += 4

        elif action == '#param_enter':
            self.addr = self.ARG_START
        elif action == '#param_exit':
            self.addr = self.ARG_START
        elif action == '#param_is_array':
            self.SS.append('#is_array')
        elif action == '#param_assign':
            if len(self.SS) < 1:
                self.semantic_errors.append(
                    f'#{self.line_no}: Semantic Error! Not enough operands.')
                return
            if self.SS[-1] == '#is_array':
                self.SS.pop()
                self.update_index(self.SS[-1], 100)
                self.insert_code('ASSIGN', f'#0', f'{self.SS.pop()}', )
                self.addr += 4
                return
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
                    if insert == True and self.cur_scope > record[4]:
                        break
                    return record[2]

        if not insert:
            return None
        if self.cur_type == 'void' and self.cur_scope > 0:
            self.semantic_errors.append(
                f'#{self.line_no}: Semantic Error! Illegal type of void for \'{lexeme}\'.'
            )
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
        if len(self.semantic_errors) == 0:
            with open('output.txt', 'w+') as f:
                for i in range(len(self.PB)):
                    f.write(f'{i}\t({self.PB[i]})\n')
        else:
            with open('output.txt', 'w+') as f:
                f.write("The code has not been generated.")

    def write_errors(self):
        with open('semantic_errors.txt', 'w+') as f:
            if len(self.semantic_errors) == 0:
                f.write("The input program is semantically correct.")
            else:
                for error in self.semantic_errors:
                    f.write(f'{error}\n')

    def check_type_mismatch(self, first, second):
        if first is None or second is None:
            return
        first_type = 'int'
        second_type = 'int'
        if not str(first).startswith('#'):
            for record in self.symbol_table:
                if record[1] == 'func':
                    continue
                elif record[2] == first:
                    first_type = 'int' if record[3] == 1 else 'array'

        if not str(second).startswith('#'):
            for record in self.symbol_table:
                if record[1] == 'func':
                    continue
                elif record[2] == second:
                    second_type = 'int' if record[3] == 1 else 'array'

        if first_type != second_type:
            self.semantic_errors.append(
                f'#{self.line_no}: Semantic Error! Type mismatch in operands, Got {second_type} instead of {first_type}.'
            )