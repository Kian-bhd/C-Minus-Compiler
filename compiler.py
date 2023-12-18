'''
C-Minus Compiler (Phase 1: Scanner)
Hamraz Arafati  99109799
Kian Bahadori   99105312
'''
from collections import defaultdict

symbol_table = {}
symbol_tokens = [';', ':', ',', '[', ']', '(', ')', '{', '}', '+', '-', '*', '=', '<', '=', '/']
whitespace_tokens = [' ', '\n', '\r', '\t', '\v', '\f']
keyword_tokens = ['if', 'else', 'void', 'int', 'while', 'break', 'return']

tokens_list = defaultdict(list)
errors_list = defaultdict(list)


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


class Scanner:
    def __init__(self, path):
        self.input_path = path
        self.line_num = 1
        self.cursor = 0
        self.finished = False

        init_keywords()
        self.input_stream = self.read_input()

    def read_input(self):
        f = open(self.input_path, 'r')
        lines = []
        while True:
            line = f.readline()

            if not line:
                break
            lines.append(line)

        return ''.join(lines)

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
                    return self.get_next_token()
            elif multiline:
                if cur_char == '*' and self.input_stream[self.cursor + 1] == '/':  # check doesn't crash
                    self.cursor += 2
                    return self.get_next_token()

            self.cursor += 1

    def get_next_token(self):
        lexeme = ''
        while self.cursor < len(self.input_stream):
            cur_char = self.input_stream[self.cursor]
            lexeme += cur_char

            if cur_char in whitespace_tokens:
                if cur_char == '\n':
                    self.line_num += 1
                self.cursor += 1
                return self.get_next_token()

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
                    return (get_token(lexeme), install_id(lexeme)), None
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
            token, error = self.get_next_token()
            self.cursor += 1
            if token[0] == 'INVALID' or token[0] == 'DONE':
                if token[0] == 'INVALID':
                    errors_list[error[1]].append((token[1], error[0]))
                continue
            tokens_list[self.line_num].append(token)

        save_symbols()
        save_tokens()
        save_errors()


def save_tokens():
    f = open('tokens.txt', 'w+')
    for line in tokens_list:
        if len(tokens_list[line]) > 0:
            line_string = str(line) + '.\t'
            for token in tokens_list[line]:
                line_string += str(f"({token[0]}, {token[1]}) ")
            line_string += '\n'
            f.write(line_string)

    f.close()


def save_symbols():
    symbols = ''
    i, j = 0, 0
    for i in range(len(symbol_table['keywords'])):
        symbols += f"{(i + 1)}.\t{symbol_table['keywords'][i]}\n"
    for j in range(len(symbol_table['ids'])):
        symbols += f"{(i + 1) + (j + 1)}.\t{symbol_table['ids'][j]}\n"

    f = open('symbol_table.txt', 'w+')
    f.write(symbols)
    f.close()


def save_errors():
    errors_string = ''
    for line in errors_list:
        if len(errors_list[line]) > 0:
            line_string = str(line) + '.\t'
            for error in errors_list[line]:
                line_string += str(f"({error[0]}, {error[1]}) ")
            errors_string += line_string + '\n'

    f = open("lexical_errors.txt", 'w+')
    f.write('There is no lexical error.' if len(errors_string) == 0 else errors_string)
    f.close()


if __name__ == '__main__':
    Scanner("input.txt").run()
