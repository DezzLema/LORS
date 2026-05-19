import re
import sys
import os

KEYWORDS = {'var', 'begin', 'end', 'repeat', 'until', 'integer', 'inc'}
OPS = {':=', '+', '-', '*', '/', '=', '<', '>', '<=', '>=', '<>'}
DELIMITERS = {';', ':', ',', '(', ')', '.'}


class Token:
    def __init__(self, type_, value, original=None):
        self.type = type_
        self.value = value
        self.original = original


def lexer(source_code):
    tokens = []
    keywords_table = {}
    identifiers_table = {}
    numbers_table = {}
    keyword_index = 1
    identifier_index = 1
    number_index = 1

    i = 0
    n = len(source_code)

    while i < n:
        ch = source_code[i]

        if ch.isspace():
            i += 1
            continue

        if ch == '{' or (ch == '(' and i + 1 < n and source_code[i + 1] == '*'):
            if ch == '(':
                end_seq = '*)'
                i += 2
            else:
                end_seq = '}'
                i += 1
            while i < n:
                if end_seq == '}' and source_code[i] == '}':
                    i += 1
                    break
                if end_seq == '*)' and source_code[i] == '*' and i + 1 < n and source_code[i + 1] == ')':
                    i += 2
                    break
                i += 1
            continue

        if ch == '/' and i + 1 < n and source_code[i + 1] == '/':
            i += 2
            while i < n and source_code[i] != '\n':
                i += 1
            continue

        if ch.isalpha() or ch == '_':
            start = i
            while i < n and (source_code[i].isalnum() or source_code[i] == '_'):
                i += 1
            word = source_code[start:i]

            if re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_]*', word):
                if word in KEYWORDS:
                    if word not in keywords_table:
                        keywords_table[word] = f'KW{keyword_index}'
                        keyword_index += 1
                    token_value = keywords_table[word]
                    tokens.append(Token('keyword', token_value, word))
                else:
                    if word not in identifiers_table:
                        identifiers_table[word] = f'ID{identifier_index}'
                        identifier_index += 1
                    token_value = identifiers_table[word]
                    tokens.append(Token('identifier', token_value, word))
            else:
                print(f'Error: invalid identifier {word}')
                sys.exit(1)
            continue

        if ch.isdigit():
            start = i
            while i < n and source_code[i].isdigit():
                i += 1
            num = source_code[start:i]
            if num not in numbers_table:
                numbers_table[num] = f'NUM{number_index}'
                number_index += 1
            tokens.append(Token('number', numbers_table[num], num))
            continue

        if ch == ':':
            if i + 1 < n and source_code[i + 1] == '=':
                tokens.append(Token('operator', ':=', ':='))
                i += 2
            else:
                tokens.append(Token('delimiter', ':', ':'))
                i += 1
            continue

        if ch in {'<', '>'}:
            if i + 1 < n and source_code[i + 1] == '=':
                tokens.append(Token('operator', ch + '=', ch + '='))
                i += 2
            elif i + 1 < n and source_code[i + 1] == '>' and ch == '<':
                tokens.append(Token('operator', '<>', '<>'))
                i += 2
            else:
                tokens.append(Token('operator', ch, ch))
                i += 1
            continue

        if ch in {'+', '-', '*', '/', '=', ';', ',', '(', ')', '.'}:
            token_type = 'operator' if ch in {'+', '-', '*', '/', '='} else 'delimiter'
            tokens.append(Token(token_type, ch, ch))
            i += 1
            continue

        print(f'Error: unexpected character {ch}')
        sys.exit(1)

    return tokens


class ASTNode:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value
        self.children = []

    def add_child(self, child):
        self.children.append(child)


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self, expected_type=None, expected_value=None):
        token = self.current()
        if token is None:
            self.error('Unexpected end of input')
        if expected_type and token.type != expected_type:
            self.error(f'Expected {expected_type}, got {token.type} ({token.original})')
        if expected_value and token.value != expected_value:
            self.error(f'Expected {expected_value}, got {token.value} ({token.original})')
        self.pos += 1
        return token

    def error(self, msg):
        token = self.current()
        line_info = f'at token {token.value} ({token.original})' if token else 'at end of input'
        print(f'Syntax error: {msg} {line_info}')
        sys.exit(1)

    def parse(self):
        return self.program()

    def program(self):
        node = ASTNode('program')
        node.add_child(self.var_declaration())
        node.add_child(self.block())
        self.consume('delimiter', '.')
        return node

    def var_declaration(self):
        node = ASTNode('var_declaration')
        self.consume('keyword', None)
        id_list = self.identifier_list()
        self.consume('delimiter', ':')
        self.consume('keyword', None)
        self.consume('delimiter', ';')
        for identifier in id_list:
            var_node = ASTNode('variable', identifier)
            node.add_child(var_node)
        return node

    def identifier_list(self):
        identifiers = []
        token = self.consume('identifier')
        identifiers.append(token.original)
        while self.current() and self.current().value == ',':
            self.consume('delimiter', ',')
            token = self.consume('identifier')
            identifiers.append(token.original)
        return identifiers

    def block(self):
        node = ASTNode('block')
        self.consume('keyword', None)
        node.add_child(self.statement_list())
        self.consume('keyword', None)
        return node

    def statement_list(self):
        node = ASTNode('statement_list')
        while self.current() and self.current().original not in {'end', 'until'}:
            node.add_child(self.statement())
        return node

    def statement(self):
        token = self.current()
        if token.type == 'identifier':
            return self.assignment()
        elif token.type == 'keyword':
            if token.original == 'repeat':
                return self.repeat_until()
            elif token.original == 'inc':
                return self.inc_statement()
            else:
                self.error(f'Unexpected keyword {token.original}')
        self.error(f'Unexpected token {token.original}')

    def assignment(self):
        node = ASTNode('assignment')
        token = self.consume('identifier')
        node.add_child(ASTNode('identifier', token.original))
        self.consume('operator', ':=')
        node.add_child(self.expression())
        self.consume('delimiter', ';')
        return node

    def inc_statement(self):
        node = ASTNode('inc')
        self.consume('keyword', None)
        self.consume('delimiter', '(')
        token = self.consume('identifier')
        node.add_child(ASTNode('identifier', token.original))
        self.consume('delimiter', ')')
        self.consume('delimiter', ';')
        return node

    def repeat_until(self):
        node = ASTNode('repeat_until')
        self.consume('keyword', None)
        node.add_child(self.statement_list())
        self.consume('keyword', None)
        node.add_child(self.expression())
        self.consume('delimiter', ';')
        return node

    def expression(self):
        token = self.current()
        if token and token.type == 'operator' and token.value in {'=', '<', '>', '<=', '>=', '<>'}:
            op_node = ASTNode('operator', token.original)
            self.consume('operator')
            right = self.term()
            op_node.add_child(right)
            return op_node
        left = self.term()
        token = self.current()
        if token and token.type == 'operator' and token.value in {'=', '<', '>', '<=', '>=', '<>'}:
            op_node = ASTNode('operator', token.original)
            self.consume('operator')
            right = self.term()
            op_node.add_child(left)
            op_node.add_child(right)
            return op_node
        return left

    def term(self):
        token = self.current()
        if token.type == 'identifier':
            self.consume('identifier')
            return ASTNode('identifier', token.original)
        elif token.type == 'number':
            self.consume('number')
            return ASTNode('number', token.original)
        self.error(f'Expected identifier or number, got {token.original}')


class SemanticAnalyzer:
    def __init__(self):
        self.declared_vars = {}
        self.errors = []

    def analyze(self, node):
        self.visit(node)
        if self.errors:
            for error in self.errors:
                print(f'Semantic error: {error}')
            sys.exit(1)
        return True

    def visit(self, node):
        if node.type == 'program':
            for child in node.children:
                self.visit(child)
        elif node.type == 'var_declaration':
            self.visit_var_declaration(node)
        elif node.type == 'block':
            for child in node.children:
                self.visit(child)
        elif node.type == 'statement_list':
            for child in node.children:
                self.visit(child)
        elif node.type == 'assignment':
            self.visit_assignment(node)
        elif node.type == 'inc':
            self.visit_inc(node)
        elif node.type == 'repeat_until':
            self.visit_repeat_until(node)
        elif node.type == 'expression':
            for child in node.children:
                self.visit(child)
        elif node.type == 'operator':
            for child in node.children:
                self.visit(child)
        elif node.type == 'identifier':
            self.check_identifier(node)
        elif node.type == 'number':
            pass

    def visit_var_declaration(self, node):
        for child in node.children:
            if child.type == 'variable':
                var_name = child.value
                if var_name in self.declared_vars:
                    self.errors.append(f'Variable "{var_name}" is already declared')
                else:
                    self.declared_vars[var_name] = True

    def visit_assignment(self, node):
        for child in node.children:
            self.visit(child)

    def visit_inc(self, node):
        for child in node.children:
            self.visit(child)

    def visit_repeat_until(self, node):
        for child in node.children:
            self.visit(child)

    def check_identifier(self, node):
        var_name = node.value
        if var_name not in self.declared_vars:
            self.errors.append(f'Variable "{var_name}" is not declared')


class CodeGenerator:
    def __init__(self):
        self.indent_level = 0
        self.output = []

    def indent(self):
        return '    ' * self.indent_level

    def emit(self, line):
        self.output.append(self.indent() + line)

    def generate(self, node):
        self.visit(node)
        return '\n'.join(self.output)

    def visit(self, node):
        if node.type == 'program':
            self.emit('#include <stdio.h>')
            self.emit('')
            self.emit('int main() {')
            self.indent_level += 1
            for child in node.children:
                self.visit(child)
            self.emit('return 0;')
            self.indent_level -= 1
            self.emit('}')
        elif node.type == 'var_declaration':
            vars_list = [child.value for child in node.children]
            self.emit(f'int {", ".join(vars_list)};')
        elif node.type == 'block':
            for child in node.children:
                self.visit(child)
        elif node.type == 'statement_list':
            for child in node.children:
                self.visit(child)
        elif node.type == 'assignment':
            identifier = node.children[0].value
            value = self.expression_to_string(node.children[1])
            self.emit(f'{identifier} = {value};')
        elif node.type == 'inc':
            identifier = node.children[0].value
            self.emit(f'{identifier}++;')
        elif node.type == 'repeat_until':
            self.emit('do {')
            self.indent_level += 1
            stmt_list = node.children[0]
            self.visit(stmt_list)
            self.indent_level -= 1
            condition = self.expression_to_string(node.children[1])
            self.emit(f'}} while (!({condition}));')

    def expression_to_string(self, node):
        if node.type == 'identifier':
            return node.value
        elif node.type == 'number':
            return node.value
        elif node.type == 'operator':
            left = self.expression_to_string(node.children[0])
            right = self.expression_to_string(node.children[1])
            op = node.value
            if op == '=':
                op = '=='
            elif op == '<>':
                op = '!='
            return f'({left} {op} {right})'
        return ''


if __name__ == '__main__':
    with open('input.pas', 'r', encoding='utf-8') as f:
        source = f.read()

    tokens = lexer(source)
    parser = Parser(tokens)
    ast = parser.parse()

    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    generator = CodeGenerator()
    c_code = generator.generate(ast)

    os.makedirs('tokens', exist_ok=True)
    with open('tokens/output.c', 'w', encoding='utf-8') as f:
        f.write(c_code)
    print('Done. See tokens/output.c')