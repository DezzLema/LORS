import sys
import os


class ASTNode:
    """Узел AST - нужно для восстановления дерева из текстового файла"""
    def __init__(self, node_type, value=None, children=None):
        self.type = node_type
        self.value = value
        self.children = children if children else []

    def add_child(self, child):
        self.children.append(child)


class ASTParser:
    """Восстанавливает AST из текстового файла"""
    @staticmethod
    def parse_from_file(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        root = None
        stack = []  # хранит (узел, уровень_отступа)

        for line in lines:
            if not line.strip():
                continue

            # Определяем уровень вложенности по отступам
            indent = len(line) - len(line.lstrip())
            content = line.strip()

            # Парсим строку: либо "Тип: значение", либо просто "Тип"
            if ': ' in content:
                parts = content.split(': ', 1)
                node_type = parts[0]
                node_value = parts[1]
            else:
                node_type = content
                node_value = None

            node = ASTNode(node_type, node_value)

            if indent == 0:
                # Корневой узел
                root = node
                stack = [(node, 0)]
            else:
                # Ищем родителя: убираем из стека всех, у кого уровень >= текущего
                while stack and stack[-1][1] >= indent:
                    stack.pop()
                if stack:
                    stack[-1][0].add_child(node)
                stack.append((node, indent))

        return root


class SymbolTable:
    """Таблица символов: хранит все переменные и проверяет их использование"""
    def __init__(self):
        self.symbols = {}   # имя переменной -> {'declared': True, 'used': False}
        self.errors = []

    def declare_variable(self, name):
        if name in self.symbols:
            self.errors.append(f"Error: redeclaration of variable '{name}'")
            return False
        else:
            self.symbols[name] = {'declared': True, 'used': False}
            return True

    def use_variable(self, name):
        if name not in self.symbols:
            self.errors.append(f"Error: use of undeclared variable '{name}'")
            return False
        else:
            self.symbols[name]['used'] = True
            return True

    def get_unused_variables(self):
        return [name for name, info in self.symbols.items() if not info['used']]

    def has_errors(self):
        return len(self.errors) > 0

    def print_errors(self):
        for error in self.errors:
            print(error)


class SemanticAnalyzer:
    """Обходит AST и проверяет семантику: объявлены ли переменные, нет ли повторных объявлений"""
    def __init__(self, ast_root):
        self.ast = ast_root
        self.symbol_table = SymbolTable()

    def analyze(self):
        if not self.ast:
            print('Error: AST not loaded')
            return False

        print('Starting semantic analysis...')

        self._visit_node(self.ast)

        unused = self.symbol_table.get_unused_variables()
        for var in unused:
            print(f"Warning: variable '{var}' declared but not used")

        if self.symbol_table.has_errors():
            self.symbol_table.print_errors()
            return False

        print('Semantic analysis complete. No errors.')
        return True

    def _visit_node(self, node):
        """Рекурсивный обход AST: для каждого типа узла своя логика"""
        node_type = node.type

        if node_type == 'Program':
            for child in node.children:
                self._visit_node(child)

        elif node_type == 'Block':
            for child in node.children:
                self._visit_node(child)

        elif node_type == 'VarDeclaration':
            # Встретили объявление переменной - добавляем в таблицу символов
            var_name = node.value
            self.symbol_table.declare_variable(var_name)

        elif node_type == 'Statements':
            for child in node.children:
                self._visit_node(child)

        elif node_type == 'Assignment':
            # В левой части присваивания - использование переменной
            var_name = node.value
            self.symbol_table.use_variable(var_name)
            for child in node.children:
                self._visit_node(child)

        elif node_type == 'RepeatLoop':
            for child in node.children:
                self._visit_node(child)

        elif node_type == 'Condition':
            for child in node.children:
                self._visit_node(child)

        elif node_type == 'BinaryOp':
            for child in node.children:
                self._visit_node(child)

        elif node_type == 'Variable':
            # Использование переменной в выражении
            var_name = node.value
            self.symbol_table.use_variable(var_name)

        elif node_type == 'Number':
            pass    # числа не нужно проверять

        else:
            for child in node.children:
                self._visit_node(child)

    def get_symbol_table(self):
        return self.symbol_table


class SemanticOutputSaver:
    def __init__(self, symbol_table, output_path):
        self.symbol_table = symbol_table
        self.output_path = output_path

    def save(self):
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write('SEMANTIC ANALYSIS RESULTS\n\n')
            f.write('Symbol Table:\n')
            f.write('-' * 40 + '\n')
            f.write(f"{'Variable':<15} {'Status':<20}\n")
            f.write('-' * 40 + '\n')

            for name, info in self.symbol_table.symbols.items():
                status = 'declared and used' if info['used'] else 'declared, NOT used'
                f.write(f"{name:<15} {status}\n")

            f.write('\n' + '-' * 40 + '\n')

            if self.symbol_table.has_errors():
                f.write('\nErrors found:\n')
                for error in self.symbol_table.errors:
                    f.write(f'  {error}\n')
            else:
                f.write('\nNo errors found.\n')

            unused = self.symbol_table.get_unused_variables()
            if unused:
                f.write(f'\nWarnings: unused variables: {", ".join(unused)}\n')


def main():
    ast_txt_path = 'output/ast.txt'
    if not os.path.exists(ast_txt_path):
        print('Error: output/ast.txt not found. Run lab2_parser.py first.')
        sys.exit(1)

    print('Loading AST from ast.txt...')
    ast_root = ASTParser.parse_from_file(ast_txt_path)

    if ast_root is None:
        print('Error: Failed to parse AST')
        sys.exit(1)

    analyzer = SemanticAnalyzer(ast_root)
    success = analyzer.analyze()

    saver = SemanticOutputSaver(analyzer.get_symbol_table(), 'output/semantic.txt')
    saver.save()

    print('Result saved to output/semantic.txt')

    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()