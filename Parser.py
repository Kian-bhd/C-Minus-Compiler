from anytree import Node, RenderTree


class Parser:
    def __init__(self, grammar_file, scanner):
        self.productions = {}
        self.start_symbol = None
        self.parse_tree = None
        self.token_index = 0
        self.scanner = scanner
        self.load_grammar(grammar_file)

    def load_grammar(self, grammar_file):
        with open(grammar_file, 'r') as file:
            lines = file.readlines()
            for line in lines:
                line = line.strip()
                if line:
                    non_terminal, production = line.split(' -> ')
                    self.productions[non_terminal] = [prod.split() for prod in production.split('|')]
            self.start_symbol = list(self.productions.keys())[0]

    def parse(self):
        self.scanner.run()
        self.parse_tree = Node(self.start_symbol)
        self.token_index = 0
        while self.token_index < len(self.scanner.tokens_list):
            self._parse_node(self.parse_tree)

    def _parse_node(self, node):
        if self.token_index >= len(self.scanner.tokens_list):
            return

        token = self.scanner.tokens_list[self.token_index]

        if len(token) > 0 and token[0] == node.name:
            self.token_index += 1

        if node.name in self.productions:
            production = self.productions[node.name]
            for symbol_seq in production:
                child = Node(symbol_seq[0], parent=node)
                for symbol in symbol_seq[1:]:
                    grandchild = Node(symbol, parent=child)
                    self._parse_node(grandchild)
                    if self.token_index >= len(self.scanner.tokens_list):
                        break

    def save_parse_tree(self, filename):
        with open(filename, 'w') as file:
            for pre, _, node in RenderTree(self.parse_tree):
                file.write("%s%s\n" % (pre, node.name))
