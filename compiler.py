'''
C-Minus Compiler (Phase 2: Scanner)
Hamraz Arafati  99109799
Kian Bahadori   99105312
'''
from Parser import Parser
from anytree import RenderTree
from Scanner import Scanner


def save_syntax_errors(paser_instance):
    with open('syntax_errors.txt', 'w') as f:
        if not paser_instance.syntax_errors:
            f.write('There is no syntax error.\n')
        else:
            f.write('\n'.join(error for error in paser_instance.syntax_errors))


def save_parse_tree(paser_instance):
    with open('parse_tree.txt', 'w', encoding='utf-8') as f:
        for pre, fill, node in RenderTree(paser_instance.root):
            f.write("%s%s\n" % (pre, node.name))


if __name__ == '__main__':
    grammar_file = 'grammar.txt'
    input_file = 'input.txt'

    scanner = Scanner(input_file)
    parser = Parser(grammar_file, scanner)
    parser.parse()
    parser.save_parse_tree('parse_tree.txt')


