symbol_table = {}
symbol_tokens = [';', ':', ',', '[', ']', '(', ')', '{', '}', '+', '-', '*', '=', '<', '=', '/']
whitespace_tokens = [' ', '\n', '\r', '\t', '\v', '\f']
keyword_tokens = ['if', 'else', 'void', 'int', 'while', 'break', 'return']


class Scanner:
    def __init__(self, path):
        self.input_path = path
        self.line_num = 1
        self.cursor = 0
        self.finished = False

        self.tokens_list = {}

        Scanner.init_keywords()
        self.input_stream = self.read_input()
        self.shown_index = 0
        self.shown_tokens = []

        self.max_lines = 0
        with open(path, 'r') as f:
            temp = f.readlines()
            self.max_lines = len(temp)
            if temp[-1][-1] == '\n':
                self.max_lines += 1

    def read_input(self):
        f = open(self.input_path, 'r')
        lines = []
        while True:
            line = f.readline()

            if not line:
                break
            lines.append(line)

        return ''.join(lines)

    def init_keywords():
        symbol_table['keywords'] = keyword_tokens
        symbol_table['ids'] = []

    def get_token(lexeme):
        if lexeme in keyword_tokens:
            return 'KEYWORD'
        return 'ID'

    def install_id(lexeme):
        if lexeme in symbol_table['keywords']:
            return lexeme

        for i in symbol_table['ids']:
            if lexeme == i:
                return i
        symbol_table['ids'].append(lexeme)
        return lexeme

    def get_comment(self, multiline, starting_line):
        starting_point = self.cursor
        while self.cursor < len(self.input_stream):
            if self.cursor == len(self.input_stream) - 2:
                if not (self.input_stream[self.cursor] == '*' and self.input_stream[self.cursor + 1] == '/'):
                    self.cursor += 1
                    return ('INVALID',
                            self.input_stream[starting_point:starting_point + 7] + '...' if starting_point < len(
                                self.input_stream) else self.input_stream[starting_point:]), (
                        'Unclosed comment', starting_line)
            cur_char = self.input_stream[self.cursor]
            if cur_char == '\n':
                self.line_num += 1
                if not multiline:
                    self.cursor += 1
                    return self._get_next_token()
            elif multiline:
                if cur_char == '*' and self.input_stream[self.cursor + 1] == '/':  # check doesn't crash
                    self.cursor += 2
                    return self._get_next_token()

            self.cursor += 1

    def _get_next_token(self):
        lexeme = ''
        while self.cursor < len(self.input_stream):
            cur_char = self.input_stream[self.cursor]
            lexeme += cur_char

            if cur_char in whitespace_tokens:
                if cur_char == '\n':
                    self.line_num += 1
                self.cursor += 1
                return self._get_next_token()

            elif cur_char in symbol_tokens:
                if cur_char == '=':
                    if self.input_stream[self.cursor + 1] == '=':
                        self.cursor += 1
                        return ('SYMBOL', '=='), None
                    else:
                        return ('SYMBOL', '='), None

                elif cur_char == '/':
                    if self.input_stream[self.cursor + 1] == '*':
                        return self.get_comment(multiline=True, starting_line=self.line_num)
                    elif not self.input_stream[self.cursor + 1].isalnum() \
                            and not self.input_stream[self.cursor + 1] in whitespace_tokens \
                            and not self.input_stream[self.cursor + 1] in symbol_tokens:
                        self.cursor += 1
                        lexeme += self.input_stream[self.cursor]
                        return ('INVALID', lexeme), ('Invalid input', self.line_num)

                elif cur_char == '*':
                    if self.input_stream[self.cursor + 1] == '/':
                        self.cursor += 1
                        return ('INVALID', '*/'), ('Unmatched comment', self.line_num)
                    elif not self.input_stream[self.cursor + 1].isalnum() \
                            and not self.input_stream[self.cursor + 1] in whitespace_tokens \
                            and not self.input_stream[self.cursor + 1] in symbol_tokens:
                        self.cursor += 1
                        lexeme += self.input_stream[self.cursor]
                        return ('INVALID', lexeme), ('Invalid input', self.line_num)

                return ('SYMBOL', lexeme), None

            elif cur_char.isdigit():
                while self.cursor + 1 < len(self.input_stream) and self.input_stream[self.cursor + 1].isdigit():
                    self.cursor += 1
                    lexeme += self.input_stream[self.cursor]

                if self.cursor == len(self.input_stream) - 1 \
                        or self.input_stream[self.cursor + 1] in symbol_tokens \
                        or self.input_stream[self.cursor + 1] in whitespace_tokens:
                    return ('NUM', lexeme), None
                else:
                    self.cursor += 1
                    lexeme += self.input_stream[self.cursor]
                    return ('INVALID', lexeme), ('Invalid number', self.line_num)

            elif cur_char.isalpha():
                while self.cursor + 1 < len(self.input_stream) and self.input_stream[self.cursor + 1].isalnum():
                    self.cursor += 1
                    lexeme += self.input_stream[self.cursor]

                if self.cursor == len(self.input_stream) - 1 \
                        or self.input_stream[self.cursor + 1] in symbol_tokens \
                        or self.input_stream[self.cursor + 1] in whitespace_tokens:
                    return (Scanner.get_token(lexeme), Scanner.install_id(lexeme)), None
                else:
                    self.cursor += 1
                    lexeme += self.input_stream[self.cursor]
                    return ('INVALID', lexeme), ('Invalid input', self.line_num)

            else:
                return ('INVALID', lexeme), ('Invalid input', self.line_num)

        self.finished = True
        return ('DONE', '$'), None

    def run(self):
        while not self.finished:
            token, error = self._get_next_token()
            self.cursor += 1
            if token[0] == 'INVALID' or token[0] == 'DONE':
                if token[0] == 'INVALID':
                    pass
                    # self.errors_list[error[1]].append((token[1], error[0]))
                continue
            if not self.line_num in self.tokens_list:
                self.tokens_list[self.line_num] = []
            self.tokens_list[self.line_num].append(token)
        for line in sorted(self.tokens_list.keys()):
            if len(self.tokens_list[line]) > 0:
                for token in self.tokens_list[line]:
                    self.shown_tokens.append((token[0], token[1], line))
        self.shown_tokens.append(('$', '$', self.max_lines))

    def show(self):
        if len(self.shown_tokens) == 0:
            self.run()
        return self.shown_tokens[self.shown_index]

    def pop(self):
        if len(self.shown_tokens) == 0:
            self.run()
        self.shown_index += 1
        return self.shown_tokens[self.shown_index - 1]

    def show_prev(self):
        if len(self.shown_tokens) == 0:
            self.run()
        if self.shown_index == 0:
            return self.shown_tokens[0]
        # print(self.shown_tokens[self.shown_index - 5:self.shown_index + 1])
        # exit(0)
        return self.shown_tokens[self.shown_index - 1]

    def find_last_assign(self):
        temp = self.shown_index
        while (self.shown_tokens[temp][1] != '='):
            temp -= 1
            if temp == -1:
                raise Exception("Abalfazlll")
        return self.shown_tokens[temp - 1][1]

    def find_last_operator(self, right=True):
        temp = self.shown_index
        while not (self.shown_tokens[temp][1] in ['+', '-', '*', '==', '<']):
            temp -= 1
            if temp == -1:
                raise Exception("Abalfazlll")
        return self.shown_tokens[temp + 1 if right else temp - 1][1]

    def find_last_arg(self):
        print(self.shown_tokens[self.shown_index - 5:self.shown_index])
        exit(0)
        temp = self.shown_index
        while not (self.shown_tokens[temp][1] in ['+', '-', '*', '==', '<']):
            temp -= 1
            if temp == -1:
                raise Exception("Abalfazlll")
        return self.shown_tokens[temp + 1 if right else temp - 1][1]

