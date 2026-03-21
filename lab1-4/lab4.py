import os
import xml.etree.ElementTree as ET


def load_ast(path):
    return ET.parse(path).getroot()


def gen(el):
    tag = el.tag

    if tag == 'program':
        var_block = el.find('var_block')
        block     = el.find('block')
        lines = []
        lines.append('#include <stdio.h>')
        lines.append('')
        lines.append('int main() {')
        lines.append(gen(var_block))
        lines.append(gen(block))
        lines.append('    return 0;')
        lines.append('}')
        return '\n'.join(lines)

    if tag == 'var_block':
        result = []
        for decl in el.findall('var_decl'):
            result.append(gen(decl))
        return '\n'.join(result)

    if tag == 'var_decl':
        type_map = {'integer': 'int', 'real': 'double', 'boolean': 'bool', 'string': 'char*'}
        c_type = type_map.get(el.find('type').attrib['name'], 'int')
        names = ', '.join(i.attrib['name'] for i in el.findall('ident'))
        return f'    {c_type} {names};'

    if tag == 'block':
        return '\n'.join(gen(child) for child in el)

    if tag == 'assign':
        return f'    {el.attrib["var"]} = {gen(el[0])};'

    if tag == 'increment':
        return f'    {el.attrib["var"]}++;'

    if tag == 'repeat':
        children = list(el)
        condition = children[-1]
        body      = children[:-1]
        body_code = '\n'.join(f'    {gen(s)}' for s in body)
        return f'    do {{\n{body_code}\n    }} while ({gen(condition)});'

    if tag == 'condition':
        left, right = list(el)
        return f'{gen(left)} {el.attrib["op"]} {gen(right)}'

    if tag == 'binop':
        left, right = list(el)
        return f'{gen(left)} {el.attrib["op"]} {gen(right)}'

    if tag == 'ident':
        return el.attrib['name']

    if tag == 'number':
        return el.attrib['value']

    raise ValueError(f"Неизвестный узел: {tag}")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ast_path = os.path.join(here, 'xml', 'ast.xml')

    if not os.path.exists(ast_path):
        print("[ОШИБКА] Файл ast.xml не найден. Сначала запустите парсер.")
        return

    root = load_ast(ast_path)

    try:
        code = gen(root)
    except ValueError as e:
        print(f"[ОШИБКА] {e}")
        return

    print(code)

    out_path = os.path.join(here, 'InputOutput', 'output.c')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(code)
    print(f"\nРезультат сохранён в {out_path}")


if __name__ == '__main__':
    main()