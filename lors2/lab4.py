import sys
import os


class ASTNode:
    def __init__(self, node_type, value=None, children=None):
        self.type = node_type
        self.value = value
        self.children = children if children else []

    def add_child(self, child):
        self.children.append(child)


class ASTParser:
    """Parses the AST from text format back into ASTNode structure"""

    @staticmethod
    def parse_from_file(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        root = None
        stack = []

        for line in lines:
            if not line.strip():
                continue

            # Calculate indent level
            indent = len(line) - len(line.lstrip())
            content = line.strip()

            # Parse node type and value
            if ': ' in content:
                parts = content.split(': ', 1)
                node_type = parts[0]
                node_value = parts[1]
            else:
                node_type = content
                node_value = None

            node = ASTNode(node_type, node_value)

            if indent == 0:
                root = node
                stack = [(node, 0)]
            else:
                # Find parent
                while stack and stack[-1][1] >= indent:
                    stack.pop()
                if stack:
                    stack[-1][0].add_child(node)
                stack.append((node, indent))

        return root


class CodeGenerator:
    def __init__(self, ast_root, symbol_table_path):
        self.ast = ast_root
        self.output_code = []
        self.indent_level = 0
        self.symbol_table = self._load_symbol_table(symbol_table_path)

    def _load_symbol_table(self, filepath):
        symbol_table = {}
        if not os.path.exists(filepath):
            return symbol_table

        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        in_table = False
        for line in lines:
            if 'Symbol Table:' in line:
                in_table = True
                continue
            if in_table and line.startswith('-'):
                continue
            if in_table and line.strip() and not line.startswith('-'):
                parts = line.strip().split()
                if parts and not parts[0].startswith('-') and parts[0] not in ['Variable', 'Status']:
                    var_name = parts[0]
                    if var_name and var_name[0].isalpha():
                        symbol_table[var_name] = True

        return symbol_table

    def generate(self):
        if not self.ast:
            print('Error: AST not loaded')
            return ''

        print('Starting code generation...')

        self._visit_node(self.ast)

        return '\n'.join(self.output_code)

    def _emit_line(self, line=''):
        if line:
            self.output_code.append('    ' * self.indent_level + line)
        else:
            self.output_code.append('')

    def _visit_node(self, node):
        node_type = node.type

        if node_type == 'Program':
            prog_name = node.value if node.value else 'main'
            self._emit_line(f'int {prog_name}(void) ' + '{')
            self.indent_level += 1

            for child in node.children:
                self._visit_node(child)

            self.indent_level -= 1
            self._emit_line('}')

        elif node_type == 'Block':
            for child in node.children:
                self._visit_node(child)

        elif node_type == 'VarDeclaration':
            var_name = node.value
            self._emit_line(f'int {var_name};')

        elif node_type == 'Statements':
            for child in node.children:
                self._visit_node(child)

        elif node_type == 'Assignment':
            var_name = node.value
            children = node.children
            if children:
                expr = self._generate_expression(children[0])
                self._emit_line(f'{var_name} = {expr};')

        elif node_type == 'RepeatLoop':
            self._emit_line('do {')
            self.indent_level += 1

            children = node.children
            for child in children:
                if child.type != 'Condition':
                    self._visit_node(child)

            self.indent_level -= 1
            self._emit_line('} while (')

            for child in children:
                if child.type == 'Condition':
                    cond_expr = self._generate_condition(child)
                    self.output_code[-1] = self.output_code[-1] + cond_expr + ');'

        elif node_type == 'Condition':
            pass

        elif node_type == 'BinaryOp':
            pass

        elif node_type == 'Variable':
            pass

        elif node_type == 'Number':
            pass

        else:
            for child in node.children:
                self._visit_node(child)

    def _generate_expression(self, node):
        node_type = node.type

        if node_type == 'BinaryOp':
            children = node.children
            if len(children) >= 2:
                left = self._generate_expression(children[0])
                right = self._generate_expression(children[1])
                op = node.value
                return f'({left} {op} {right})'

        elif node_type == 'Variable':
            return node.value

        elif node_type == 'Number':
            return str(node.value)

        return '0'

    def _generate_condition(self, node):
        children = node.children
        if len(children) >= 2:
            left = self._generate_expression(children[0])
            right = self._generate_expression(children[1])
            op = node.value

            if op == '=':
                op = '=='
            elif op == '<>':
                op = '!='

            return f'{left} {op} {right}'

        return '1'


class CCodeOutputSaver:
    def __init__(self, code, output_path):
        self.code = code
        self.output_path = output_path

    def save(self):
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(self.code)


def main():
    ast_txt_path = 'output/ast.txt'
    semantic_path = 'output/semantic.txt'

    if not os.path.exists(ast_txt_path):
        print('Error: output/ast.txt not found. Run lab2_parser.py first.')
        sys.exit(1)

    print('Loading AST from ast.txt...')
    ast_root = ASTParser.parse_from_file(ast_txt_path)

    if ast_root is None:
        print('Error: Failed to parse AST')
        sys.exit(1)

    generator = CodeGenerator(ast_root, semantic_path)
    output_code = generator.generate()

    saver = CCodeOutputSaver(output_code, 'output/generated_code.с')
    saver.save()

    print('Code generation complete')
    print('Result saved to output/generated_code.txt')


if __name__ == '__main__':
    main()