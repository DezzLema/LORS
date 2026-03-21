import os
import xml.etree.ElementTree as ET
from xml.dom import minidom


def load_tokens(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    tokens = []
    for t in root.find('token_stream'):
        tokens.append({'type': t.attrib['type'], 'value': t.attrib['value'], 'line': t.attrib['line']})
    return tokens


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, type_=None, value=None):
        t = self.peek()
        if t is None:
            raise SyntaxError("Неожиданный конец файла")
        if type_ and t['type'] != type_:
            raise SyntaxError(f"Строка {t['line']}: ожидался тип {type_}, получен {t['type']} ('{t['value']}')")
        if value and t['value'] != value:
            raise SyntaxError(f"Строка {t['line']}: ожидалось '{value}', получено '{t['value']}'")
        self.pos += 1
        return t

    def node(self, tag, **attrs):
        el = ET.Element(tag)
        for k, v in attrs.items():
            el.set(k, str(v))
        return el

    def parse_program(self):
        root = self.node('program')
        root.append(self.parse_var_block())
        root.append(self.parse_main_block())
        return root

    def parse_var_block(self):
        block = self.node('var_block')
        self.consume('KW', 'var')
        while self.peek() and self.peek()['value'] != 'begin':
            block.append(self.parse_var_decl())
        return block

    def parse_var_decl(self):
        decl = self.node('var_decl')
        t = self.consume('ID')
        decl.append(self.node('ident', name=t['value'], line=t['line']))
        while self.peek() and self.peek()['value'] == ',':
            self.consume('DELIM', ',')
            t = self.consume('ID')
            decl.append(self.node('ident', name=t['value'], line=t['line']))
        self.consume('DELIM', ':')
        decl.append(self.node('type', name=self.consume('KW')['value']))
        self.consume('DELIM', ';')
        return decl

    def parse_main_block(self):
        block = self.node('block')
        self.consume('KW', 'begin')
        while self.peek() and self.peek()['value'] != 'end':
            block.append(self.parse_statement())
        self.consume('KW', 'end')
        self.consume('DELIM', '.')
        return block

    def parse_statement(self):
        t = self.peek()
        if t['value'] == 'repeat':
            return self.parse_repeat()
        elif t['type'] == 'ID':
            return self.parse_assign_or_incr()
        else:
            raise SyntaxError(f"Строка {t['line']}: неожиданный токен '{t['value']}'")

    def parse_repeat(self):
        node = self.node('repeat')
        self.consume('KW', 'repeat')
        while self.peek() and self.peek()['value'] != 'until':
            node.append(self.parse_statement())
        self.consume('KW', 'until')
        node.append(self.parse_condition())
        self.consume('DELIM', ';')
        return node

    def parse_assign_or_incr(self):
        tok = self.consume('ID')
        ident, line = tok['value'], tok['line']
        t = self.peek()
        if t and t['value'] == '++':
            self.consume('OP', '++')
            self.consume('DELIM', ';')
            return self.node('increment', var=ident, line=line)
        elif t and t['value'] == ':=':
            self.consume('OP', ':=')
            expr = self.parse_expr()
            self.consume('DELIM', ';')
            assign = self.node('assign', var=ident, line=line)
            assign.append(expr)
            return assign
        else:
            raise SyntaxError(f"Строка {t['line']}: ожидался ':=' или '++'")

    def parse_condition(self):
        cond = self.node('condition')
        cond.append(self.parse_expr())
        op = self.consume('OP')
        cond.set('op', op['value'])
        cond.append(self.parse_expr())
        return cond

    def parse_expr(self):
        left = self.parse_atom()
        while self.peek() and self.peek()['type'] == 'OP' and self.peek()['value'] in '+-':
            op = self.consume('OP')['value']
            right = self.parse_atom()
            expr = self.node('binop', op=op)
            expr.append(left)
            expr.append(right)
            left = expr
        return left

    def parse_atom(self):
        t = self.peek()
        if t['type'] == 'ID':
            self.consume('ID')
            return self.node('ident', name=t['value'], line=t['line'])
        elif t['type'] == 'NUM':
            self.consume('NUM')
            return self.node('number', value=t['value'])
        elif t['value'] == '(':
            self.consume('DELIM', '(')
            expr = self.parse_expr()
            self.consume('DELIM', ')')
            return expr
        else:
            raise SyntaxError(f"Строка {t['line']}: неожиданный токен '{t['value']}'")


def pretty(root):
    return minidom.parseString(ET.tostring(root, encoding='unicode')).toprettyxml(indent='  ')


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    tokens_path = os.path.join(here, 'xml', 'tokens.xml')

    if not os.path.exists(tokens_path):
        print("[ОШИБКА] Файл tokens.xml не найден. Сначала запустите лексер (main.py).")
        return

    tokens = load_tokens(tokens_path)

    try:
        ast = Parser(tokens).parse_program()
    except SyntaxError as e:
        print(f"[ОШИБКА] {e}")
        return

    out = pretty(ast)
    out_path = os.path.join(here, 'xml', 'ast.xml')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(out)
    print(out)
    print(f"AST сохранён в {out_path}")


if __name__ == '__main__':
    main()