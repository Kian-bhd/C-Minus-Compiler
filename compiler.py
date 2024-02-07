'''
C-Minus Compiler (Phase 3: Parser)
Hamraz Arafati  99109799
Kian Bahadori   99105312
'''
from Parser import Parser


symbol_table = {}
symbol_tokens = [';', ':', ',', '[', ']', '(', ')', '{', '}', '+', '-', '*', '=', '<', '=', '/']
whitespace_tokens = [' ', '\n', '\r', '\t', '\v', '\f']
keyword_tokens = ['if', 'else', 'void', 'int', 'while', 'break', 'return']


if __name__ == '__main__':
    parser = Parser("input.txt")
    parser.parse()
