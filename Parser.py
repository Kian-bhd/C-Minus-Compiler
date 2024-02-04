from anytree import Node, RenderTree

from Codegen import Codegen
from Scanner import Scanner

NODE_NUMBER = 0


class VarNode:  # VarNode class used for parser
    def __init__(self, value, parent=None):
        global NODE_NUMBER
        self.parent = parent
        self.children = []
        self.value = value
        self.valid = True
        self.children_index = 0
        self.node_number = NODE_NUMBER
        NODE_NUMBER += 1

    def destruct(self):
        self.valid = False


class Parser:
    def __init__(self, file_name):
        self.errors = []
        self.cur_root = VarNode('Program')
        self.scanner = Scanner(file_name)
        self.codegen = Codegen()
        self.grammar = {'Program': [['DeclarationList']],
                        'DeclarationList': [['Declaration', 'DeclarationList'], ['epsilon']],
                        'Declaration': [['DeclarationInitial', 'DeclarationPrime']],
                        'DeclarationInitial': [['TypeSpecifier', '#pid_dec', 'ID']],
                        'DeclarationPrime': [['FunDeclarationPrime'], ['VarDeclarationPrime']],
                        'VarDeclarationPrime': [[';'], ['[', '#p_index', 'NUM', '#set_index', ']', ';']],
                        'FunDeclarationPrime': [['#scope_plus', '#func_init', '(', 'Params', ')', '#func_symbol', '#new_rs', 'CompoundStmt', '#end_rs', '#func_fin', '#scope_minus']],
                        'TypeSpecifier': [['#set_id_type', 'int'], ['#set_id_type', 'void']],
                        'Params': [['#set_id_type', 'int', '#pid_dec', 'ID', 'ParamPrime', 'ParamList'], ['#set_id_type', 'void']],
                        'ParamList': [[',', 'Param', 'ParamList'], ['epsilon']],
                        'Param': [['DeclarationInitial', 'ParamPrime']],
                        'ParamPrime': [['[', ']'], ['epsilon']],
                        'CompoundStmt': [['{', 'DeclarationList', 'StatementList', '}']],
                        'StatementList': [['Statement', 'StatementList'], ['epsilon']],
                        'Statement': [['ExpressionStmt'], ['CompoundStmt'], ['SelectionStmt'], ['IterationStmt'],
                                      ['ReturnStmt']],
                        'ExpressionStmt': [['Expression', ';', '#cleanup'], ['break', '#break', ';'], [';']],
                        'SelectionStmt': [['if', '(', 'Expression', ')', '#save', '#scope_plus', 'Statement', '#scope_minus', '#jpf_save', 'else',  '#scope_plus', 'Statement', '#scope_minus', '#jmp']],
                        'IterationStmt': [['while', '#label', '(', 'Expression', ')', '#new_bs', '#save', '#scope_plus', 'Statement', '#scope_minus', '#while', '#end_bs']],
                        'ReturnStmt': [['return', 'ReturnStmtPrime', '#return']],
                        'ReturnStmtPrime': [['#implicit_zero_return', ';'], ['Expression', ';']],
                        'Expression': [['SimpleExpressionZegond'], ['#pid', 'ID', 'B']],
                        'B': [['=', 'Expression', '#assign'], ['[', 'Expression', ']', '#p_array_addr', 'H'], ['SimpleExpressionPrime']],
                        'H': [['=', 'Expression', '#assign'], ['G', 'D', 'C']],
                        'SimpleExpressionZegond': [['AdditiveExpressionZegond', 'C']],
                        'SimpleExpressionPrime': [['AdditiveExpressionPrime', 'C']],
                        'C': [['#push_op', 'Relop', 'AdditiveExpression', '#eval'], ['epsilon']],
                        'Relop': [['<'], ['==']],
                        'AdditiveExpression': [['Term', 'D']],
                        'AdditiveExpressionPrime': [['TermPrime', 'D']],
                        'AdditiveExpressionZegond': [['TermZegond', 'D']],
                        'D': [['#push_op', 'Addop', 'Term', '#eval', 'D'], ['epsilon']],
                        'Addop': [['+'], ['-']],
                        'Term': [['SignedFactor', 'G']],
                        'TermPrime': [['SignedFactorPrime', 'G']],
                        'TermZegond': [['SignedFactorZegond', 'G']],
                        'G': [['#push_op', '*', 'SignedFactor', '#eval', 'G'], ['epsilon']],
                        'SignedFactor': [['+', 'Factor'], ['-', 'Factor', '#neg'], ['Factor']],
                        'SignedFactorPrime': [['FactorPrime']],
                        'SignedFactorZegond': [['+', 'Factor'], ['-', 'Factor', '#neg'], ['FactorZegond']],
                        'Factor': [['(', 'Expression', ')'], ['#pid', 'ID', 'VarCallPrime'], ['#pnum', 'NUM']],
                        'VarCallPrime': [['(', 'Args', ')'], ['VarPrime']],
                        'VarPrime': [['[', 'Expression', '#p_array_addr', ']'], ['epsilon']],
                        'FactorPrime': [['(', 'Args', ')'], ['epsilon']],
                        'FactorZegond': [['(', 'Expression', ')'], ['#pnum', 'NUM']],
                        'Args': [['ArgList'], ['epsilon']],
                        'ArgList': [['Expression', 'ArgListPrime']],
                        'ArgListPrime': [[',', 'Expression', 'ArgListPrime'], ['epsilon']]
                        }
        self.grammar2 = {'Program': [['DeclarationList']],
                            'DeclarationList': [['Declaration', 'DeclarationList'], ['epsilon']],
                            'Declaration': [['DeclarationInitial', 'DeclarationPrime']],
                            'DeclarationInitial': [['TypeSpecifier', 'ID']],
                            'DeclarationPrime': [['FunDeclarationPrime'], ['VarDeclarationPrime']],
                            'VarDeclarationPrime': [[';'], ['[', 'NUM', ']', ';']],
                            'FunDeclarationPrime': [['(', 'Params', ')', 'CompoundStmt']],
                            'TypeSpecifier': [['int'], ['void']],
                            'Params': [['int', 'ID', 'ParamPrime', 'ParamList'], ['void']],
                            'ParamList': [[',', 'Param', 'ParamList'], ['epsilon']],
                            'Param': [['DeclarationInitial', 'ParamPrime']],
                            'ParamPrime': [['[', ']'], ['epsilon']],
                            'CompoundStmt': [['{', 'DeclarationList', 'StatementList', '}']],
                            'StatementList': [['Statement', 'StatementList'], ['epsilon']],
                            'Statement': [['ExpressionStmt'], ['CompoundStmt'], ['SelectionStmt'], ['IterationStmt'],
                                          ['ReturnStmt']],
                            'ExpressionStmt': [['Expression', ';'], ['break', ';'], [';']],
                            'SelectionStmt': [['if', '(', 'Expression', ')', 'Statement', 'else', 'Statement']],
                            'IterationStmt': [['while', '(', 'Expression', ')', 'Statement']],
                            'ReturnStmt': [['return', 'ReturnStmtPrime']],
                            'ReturnStmtPrime': [[';'], ['Expression', ';']],
                            'Expression': [['SimpleExpressionZegond'], ['ID', 'B']],
                            'B': [['=', 'Expression'], ['[', 'Expression', ']', 'H'], ['SimpleExpressionPrime']],
                            'H': [['=', 'Expression'], ['G', 'D', 'C']],
                            'SimpleExpressionZegond': [['AdditiveExpressionZegond', 'C']],
                            'SimpleExpressionPrime': [['AdditiveExpressionPrime', 'C']],
                            'C': [['Relop', 'AdditiveExpression'], ['epsilon']],
                            'Relop': [['<'], ['==']],
                            'AdditiveExpression': [['Term', 'D']],
                            'AdditiveExpressionPrime': [['TermPrime', 'D']],
                            'AdditiveExpressionZegond': [['TermZegond', 'D']],
                            'D': [['Addop', 'Term', 'D'], ['epsilon']],
                            'Addop': [['+'], ['-']],
                            'Term': [['SignedFactor', 'G']],
                            'TermPrime': [['SignedFactorPrime', 'G']],
                            'TermZegond': [['SignedFactorZegond', 'G']],
                            'G': [['*', 'SignedFactor', 'G'], ['epsilon']],
                            'SignedFactor': [['+', 'Factor'], ['-', 'Factor'], ['Factor']],
                            'SignedFactorPrime': [['FactorPrime']],
                            'SignedFactorZegond': [['+', 'Factor'], ['-', 'Factor'], ['FactorZegond']],
                            'Factor': [['(', 'Expression', ')'], ['ID', 'VarCallPrime'], ['NUM']],
                            'VarCallPrime': [['(', 'Args', ')'], ['VarPrime']],
                            'VarPrime': [['[', 'Expression', ']'], ['epsilon']],
                            'FactorPrime': [['(', 'Args', ')'], ['epsilon']],
                            'FactorZegond': [['(', 'Expression', ')'], ['NUM']],
                            'Args': [['ArgList'], ['epsilon']],
                            'ArgList': [['Expression', 'ArgListPrime']],
                            'ArgListPrime': [[',', 'Expression', 'ArgListPrime'], ['epsilon']],
                            }
        self.firsts = self.init_first()
        self.follows = self.init_follow()
        self.stack = ['$', 'Program']
        self.terminals = ["ID", ";", "[", "NUM", "]", "(", ")", "int", "void", ",", "{", "}", "break", "if", "else",
                          "repeat", "until", "return", "=", "<", "==", "+", "-", "*"]
        self.create_table()

    def create_table(self):
        self.table = {}
        # initialize table rows
        for variable in self.grammar.keys():
            self.table[variable] = {}

        for variable in self.grammar.keys():  # each non-terminal
            for production in self.grammar[variable]:  # for each production rule
                first_set = self.first(production)
                if 'epsilon' in first_set:
                    for terminal in first_set:
                        if terminal == 'epsilon':
                            continue
                        self.table[variable][terminal] = ('CORRECT', production)
                    for terminal in self.follows[variable]:
                        self.table[variable][terminal] = ('CORRECT', self.find_nullable_production(variable))
                else:
                    for terminal in first_set:
                        self.table[variable][terminal] = ('CORRECT', production)

        # recovery mode
        for variable in self.grammar.keys():
            for terminal in self.follows[variable]:
                if not terminal in self.table[variable]:
                    self.table[variable][terminal] = ('SYNCH', None)

    def find_nullable_production(self, variable):
        for production in self.grammar[variable]:
            if 'epsilon' in self.first(production):
                return production

    def move_up(self):
        root = self.cur_root
        while root.parent:
            root = root.parent
            root.children_index += 1
            if root.children_index < len(root.children):
                self.cur_root = root.children[root.children_index]
                return
        self.cur_root = root
        # root.children.append(VarNode('$', root))

    def move_down(self, production):
        self.cur_root.children = [VarNode(i, self.cur_root) for i in production]
        self.cur_root = self.cur_root.children[0]

    def Move(self, big_A, small_a, lookahead):
        # print(big_A, ':', small_a, ':', self.stack)
        ret = False
        # base cases
        if big_A == small_a == '$':
            ret = True

        if big_A.startswith('#'):
            self.stack.pop()
            #self.move_up()
            self.codegen.code_gen(big_A, lookahead)
            return ret

        if big_A == 'epsilon':
            self.stack.pop()
            self.move_up()
            return ret

        if big_A not in self.grammar.keys():  # A terminal
            if big_A == small_a:
                temp = self.scanner.show()
                if not self.choose_token(temp) == '$':
                    self.cur_root.value = f'({temp[0]}, {temp[1]})'
                self.scanner.pop()
                self.stack.pop()
                self.move_up()
            else:  # goes to recovery
                if big_A == '$':
                    self.move_up()
                    return True
                _, _, lineno = self.scanner.show()
                self.errors.append(f'#{lineno} : syntax error, missing {self.stack.pop()}')
                self.cur_root.destruct()
                self.move_up()
        else:  # A non-terminal
            if small_a in self.table[big_A]:  # either synch or correct
                state, production = self.table[big_A][small_a]
                if state == 'CORRECT':
                    self.stack.pop()
                    self.stack.extend(production[::-1])
                    self.move_down(production)
                    # print(f'{big_A}->{" ".join(production)}')
                else:  # synch recovery
                    _, _, lineno = self.scanner.show()
                    self.errors.append(f'#{lineno} : syntax error, missing {self.stack.pop()}')
                    self.cur_root.destruct()
                    self.move_up()
            else:  # empty move
                if self.choose_token(self.scanner.show()) == '$':
                    self.errors.append(f'#{self.scanner.show()[2]} : syntax error, Unexpected EOF')
                    self.cur_root.destruct()
                    return True
                token = self.scanner.pop()
                self.errors.append(f'#{token[2]} : syntax error, illegal {self.choose_token(token)}')
        return ret

    def choose_token(self, token):
        if token[0] in self.terminals:
            return token[0]
        return token[1]

    def write_tree(self):
        with open('parse_tree.txt', 'w+') as f:
            f.write(str(self))

    def write_errors(self):
        with open('syntax_errors.txt', 'w+') as f:
            if len(self.errors) == 0:
                f.write('There is no syntax error.')
            else:
                f.write('\n'.join(self.errors))

    def parse(self):
        stack_top, lookahead_top = self.stack[-1], self.scanner.show()
        while not self.Move(stack_top, self.choose_token(lookahead_top), lookahead_top[1]):
            stack_top, lookahead_top = self.stack[-1], self.scanner.show()
        self.write_errors()
        self.codegen.print_output()
        #self.write_tree()

    def init_first(self):
        ret = {}
        arr = ['ID', ';', '[', 'NUM', ']', '(', ')', 'int', 'void', ',', '{', '}', 'break', 'if', 'else', 'while',
               'return', '=', '<', '==', '+', '-', '*', 'epsilon']
        with open('parser/first.txt', 'r') as f:
            for line in f.readlines():
                toks = line.split()
                if toks[0] == '':
                    continue
                temp_arr = []
                for idx, i in enumerate(toks[1:]):
                    if i == '+':
                        temp_arr.append(arr[idx])
                ret[toks[0]] = temp_arr
        return ret

    def init_follow(self):
        ret = {}
        arr = ['ID', ';', '[', 'NUM', ']', '(', ')', 'int', 'void', ',', '{', '}', 'break', 'if', 'else', 'while',
               'return', '=', '<', '==', '+', '-', '*', '$']

        with open('parser/follow.txt', 'r') as f:
            for line in f.readlines():
                toks = line.split()
                if toks[0] == '':
                    continue
                temp_arr = []
                for idx, i in enumerate(toks[1:]):
                    if i == '+':
                        temp_arr.append(arr[idx])
                ret[toks[0]] = temp_arr
        return ret

    def first_variable(self, variable):
        if variable in self.grammar:
            return self.firsts[variable]
        else:
            return {variable}

    def first(self, production):
        ret = set([])
        for variable in production:
            if variable.startswith('#'):
                continue
            temp = self.first_variable(variable)
            if 'epsilon' in temp:
                temp = set([i for i in temp if not i == 'epsilon'])
                ret = ret.union(temp)
            else:
                return ret.union(temp)
        ret.add('epsilon')
        return ret

    def make_nodes(self, root, par):
        if not root.valid:
            return
        if not par:
            n = Node(f'{root.value}%{root.node_number}')

            for i in range(root.children_index + 1):
                if i == len(root.children):
                    break
                self.make_nodes(root.children[i], n)
            return n

        n = Node(f'{root.value}%{root.node_number}', parent=par)
        for i in range(root.children_index + 1):
            if i == len(root.children):
                break
            self.make_nodes(root.children[i], n)
        return None

    def __str__(self):
        while self.cur_root.parent:
            self.cur_root = self.cur_root.parent
        if self.cur_root.children_index == len(self.cur_root.children):
            self.cur_root.children.append(VarNode('$', self.cur_root))
        temp = self.make_nodes(self.cur_root, None)
        # print(temp)
        return '\n'.join([f'{pre}{node.name.split("%")[0]}' for pre, fill, node in RenderTree(temp)])
