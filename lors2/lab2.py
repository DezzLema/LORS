# lab2_parser.py
import sys
import os


class ASTNode:
    def __init__(self, node_type, value=None, children=None):
        self.type = node_type
        self.value = value
        self.children = children if children else []

    def add_child(self, child):
        self.children.append(child)


class Parser:
    def __init__(self, token_sequence, keywords_table, identifiers_table, numbers_table):
        self.tokens = token_sequence.split()
        self.pos = 0
        self.n = len(self.tokens)

        # Таблицы: оригинал -> условное
        self.keywords_table = keywords_table
        self.identifiers_table = identifiers_table
        self.numbers_table = numbers_table

        # Обратные отображения: условное -> оригинал
        self.reverse_keywords = {v: k for k, v in keywords_table.items()}
        self.reverse_identifiers = {v: k for k, v in identifiers_table.items()}
        self.reverse_numbers = {v: int(k) for k, v in numbers_table.items()}

        self.ast_root = None

    def parse(self):
        self.ast_root = self._parse_program()

        if self.pos < self.n:
            print(f'Error: extra tokens: {self.tokens[self.pos:]}')
            sys.exit(1)

        return self.ast_root

    def _current_token(self):
        return self.tokens[self.pos] if self.pos < self.n else None

    def _match(self, expected):
        if self._current_token() == expected:
            self.pos += 1
            return True
        return False

    def _expect(self, expected):
        if not self._match(expected):
            print(f'Syntax error: expected {expected}, found {self._current_token()}')
            sys.exit(1)

    def _get_original_identifier(self, token):
        return self.reverse_identifiers.get(token, token)

    def _get_original_number(self, token):
        return self.reverse_numbers.get(token, token)

    def _get_keyword_name(self, token):
        return self.reverse_keywords.get(token, token)

    def _parse_program(self):
        # program
        self._expect('KW1')
        prog_node = ASTNode('Program')

        # Program name
        prog_name_token = self._current_token()
        if not prog_name_token or not prog_name_token.startswith('ID'):
            print('Error: expected program name')
            sys.exit(1)
        prog_node.value = self._get_original_identifier(prog_name_token)
        self.pos += 1

        self._expect(';')

        # Block
        block_node = self._parse_block()
        prog_node.add_child(block_node)

        self._expect('.')

        return prog_node

    def _parse_block(self):
        block_node = ASTNode('Block')

        # Var section (if exists)
        if self._current_token() == 'KW2':
            self.pos += 1
            var_decls = self._parse_var_declarations()
            for decl in var_decls:
                block_node.add_child(decl)

        # begin
        self._expect('KW4')

        # Statements
        stmts_node = self._parse_statements()
        block_node.add_child(stmts_node)

        # end
        self._expect('KW7')

        return block_node

    def _parse_var_declarations(self):
        declarations = []

        while self._current_token() and self._current_token().startswith('ID'):
            identifiers = []
            while True:
                id_token = self._current_token()
                if not id_token or not id_token.startswith('ID'):
                    break
                var_name = self._get_original_identifier(id_token)
                identifiers.append(var_name)
                self.pos += 1

                if self._current_token() == ',':
                    self.pos += 1
                else:
                    break

            self._expect(':')

            # integer
            if self._current_token() != 'KW3':
                print(f'Error: expected integer, found {self._current_token()}')
                sys.exit(1)
            self.pos += 1

            self._expect(';')

            for var_name in identifiers:
                declarations.append(ASTNode('VarDeclaration', var_name))

        return declarations

    def _parse_statements(self):
        stmts_node = ASTNode('Statements')

        while self._current_token() and self._current_token() not in ['KW7', 'KW6']:
            stmt = self._parse_statement()
            if stmt:
                stmts_node.add_child(stmt)

            if self._current_token() == ';':
                self.pos += 1

        return stmts_node

    def _parse_statement(self):
        current = self._current_token()

        if current is None:
            return None

        # Assignment
        if current.startswith('ID'):
            return self._parse_assignment()

        # repeat
        if current == 'KW5':
            return self._parse_repeat_loop()

        print(f'Error: unexpected token {current}')
        sys.exit(1)

    def _parse_assignment(self):
        id_token = self._current_token()
        var_name = self._get_original_identifier(id_token)
        self.pos += 1

        self._expect(':=')

        expr_node = self._parse_expression()

        assign_node = ASTNode('Assignment', var_name)
        assign_node.add_child(expr_node)

        return assign_node

    def _parse_repeat_loop(self):
        self._expect('KW5')

        repeat_node = ASTNode('RepeatLoop')

        body_node = self._parse_statements()
        repeat_node.add_child(body_node)

        self._expect('KW6')

        condition_node = self._parse_condition()
        repeat_node.add_child(condition_node)

        return repeat_node

    def _parse_expression(self):
        left = self._parse_term()

        while self._current_token() in {'+', '-'}:
            op = self._current_token()
            self.pos += 1
            right = self._parse_term()

            binop = ASTNode('BinaryOp', op)
            binop.add_child(left)
            binop.add_child(right)
            left = binop

        return left

    def _parse_term(self):
        left = self._parse_factor()

        while self._current_token() in {'*', '/'}:
            op = self._current_token()
            self.pos += 1
            right = self._parse_factor()

            binop = ASTNode('BinaryOp', op)
            binop.add_child(left)
            binop.add_child(right)
            left = binop

        return left

    def _parse_factor(self):
        current = self._current_token()

        if current.startswith('ID'):
            var_name = self._get_original_identifier(current)
            self.pos += 1
            return ASTNode('Variable', var_name)

        elif current.startswith('NUM'):
            num_val = self._get_original_number(current)
            self.pos += 1
            return ASTNode('Number', num_val)

        elif current == '(':
            self.pos += 1
            expr = self._parse_expression()
            self._expect(')')
            return expr

        print(f'Error in expression: {current}')
        sys.exit(1)

    def _parse_condition(self):
        left = self._parse_expression()

        op = self._current_token()
        if op not in {'=', '<', '>', '<=', '>=', '<>'}:
            print(f'Error: expected comparison operator, found {op}')
            sys.exit(1)
        self.pos += 1

        right = self._parse_expression()

        cond_node = ASTNode('Condition', op)
        cond_node.add_child(left)
        cond_node.add_child(right)

        return cond_node


def load_tables_from_file(filepath):
    """Loads tables from file created by lexical analyzer"""
    keywords_table = {}
    identifiers_table = {}
    numbers_table = {}
    token_sequence = ''

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # First line - token sequence
    i = 0
    if lines:
        token_sequence = lines[0].strip()
        i = 1

    # Skip empty lines
    while i < len(lines) and not lines[i].strip():
        i += 1

    # Read tables
    current_table = None
    while i < len(lines):
        line = lines[i].strip()

        if line == 'KEYWORDS TABLE':
            current_table = 'keywords'
            i += 1
            continue
        elif line == 'IDENTIFIERS TABLE':
            current_table = 'identifiers'
            i += 1
            continue
        elif line == 'NUMBERS TABLE':
            current_table = 'numbers'
            i += 1
            continue

        # Skip empty lines inside table
        if not line:
            i += 1
            continue

        # Parse lines like "KW1:program"
        if current_table and ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                token_name = parts[0]
                original_value = parts[1]

                if current_table == 'keywords':
                    keywords_table[original_value] = token_name
                elif current_table == 'identifiers':
                    identifiers_table[original_value] = token_name
                elif current_table == 'numbers':
                    numbers_table[original_value] = token_name

        i += 1

    return token_sequence, keywords_table, identifiers_table, numbers_table


class ASTSaver:
    def __init__(self, ast_root, output_path):
        self.ast_root = ast_root
        self.output_path = output_path

    def save(self):
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

        with open(self.output_path, 'w', encoding='utf-8') as f:
            self._print_tree(self.ast_root, f, 0)

    def _print_tree(self, node, file, level):
        indent = '  ' * level

        if node.value is not None:
            file.write(f'{indent}{node.type}: {node.value}\n')
        else:
            file.write(f'{indent}{node.type}\n')

        for child in node.children:
            self._print_tree(child, file, level + 1)


def main():
    if not os.path.exists('output/tokens.txt'):
        print('Error: output/tokens.txt not found. Run lab1_lexer.py first.')
        sys.exit(1)

    print('Loading lexical analysis results...')
    token_sequence, keywords_table, identifiers_table, numbers_table = load_tables_from_file('output/tokens.txt')

    print(f'Keywords table: {keywords_table}')
    print(f'Identifiers table: {identifiers_table}')
    print(f'Numbers table: {numbers_table}')

    print('Starting syntax analysis...')

    parser = Parser(token_sequence, keywords_table, identifiers_table, numbers_table)
    ast_root = parser.parse()

    saver = ASTSaver(ast_root, 'output/ast.txt')
    saver.save()

    print('Syntax analysis complete')
    print('AST saved to output/ast.txt')


if __name__ == '__main__':
    main()