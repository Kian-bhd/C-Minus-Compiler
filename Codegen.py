class Codegen:
    def __init__(self):
        self.SS = []
        self.PB = []
        self.BS = []
        self.i = 0
        self.cur_type = 'void'
        self.addr = 100
        self.temp_addr = 500
        self.symbol_table = {}  # {'var1'=[type1, addr1, size], 'var2'=[type2, addr2]}
        self.op_dict = {'+': 'ADD', '-': 'SUB', '*': 'MULT', '<': 'LT', '==': 'EQ'}

    def code_gen(self, action, lexeme):
        print(action, ':', lexeme, ':', self.SS)
        if action == '#set_id_type':
            self.cur_type = lexeme
        elif action == '#pid':
            addr = self.find_addr(lexeme)
            self.SS.append(addr)
        elif action == '#assign':
            self.insert_code('ASSIGN', self.SS[-1], self.SS[-2])
            self.SS.pop()
        elif action == '#p_index':
            self.SS.append(lexeme)
        elif action == '#set_index':
            self.update_index(self.SS[-2], self.SS[-1])
            self.addr += 4 * (int(self.SS[-1]) - 1)
            self.SS.pop()
            self.SS.pop()
        elif action == '#pnum':
            self.SS.append(f'#{lexeme}')
        elif action == '#p_array_addr':
            idx = self.SS.pop()
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

    def get_temp(self):
        tmp = self.temp_addr
        self.temp_addr += 4
        return tmp

    def insert_code(self, one, two, three='', four=''):
        self.PB.append(f'{one}, {two}, {three}, {four}')
        self.print_output()
        self.i += 1

    def update_index(self, addr, idx):
        for var in self.symbol_table.keys():
            if self.symbol_table[var][1] == addr:
                self.symbol_table[var][2] = idx
                print('Symbol Table:')
                print(self.symbol_table)
                return

    def find_addr(self, lexeme):
        if lexeme in self.symbol_table.keys():
            return self.symbol_table[lexeme][1]
        else:
            self.symbol_table[lexeme] = [self.cur_type, self.addr, 1]
            self.addr += 4
            return self.symbol_table[lexeme][1]

    def print_output(self):
        for i in range(len(self.PB)):
            print(f'{i}\t({self.PB[i]})')
