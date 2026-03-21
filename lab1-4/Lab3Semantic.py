import os
import xml.etree.ElementTree as ET


def load_ast(path):
    return ET.parse(path).getroot()


def analyze(root):
    declared = {}
    errors = []

    def declare(name, line):
        if name in declared:
            errors.append(f"Строка {line}: повторное объявление идентификатора '{name}'")
        else:
            declared[name] = line

    def check_used(name, line):
        if name not in declared:
            errors.append(f"Строка {line}: использование необъявленного идентификатора '{name}'")

    def walk(el):
        if el.tag == 'var_decl':
            type_name = el.find('type').attrib['name']
            for ident in el.findall('ident'):
                declare(ident.attrib['name'], ident.attrib.get('line', '?'))
            return

        if el.tag == 'assign':
            check_used(el.attrib['var'], el.attrib.get('line', '?'))
        if el.tag == 'increment':
            check_used(el.attrib['var'], el.attrib.get('line', '?'))
        if el.tag == 'ident':
            check_used(el.attrib['name'], el.attrib.get('line', '?'))

        for child in el:
            walk(child)

    walk(root)
    return declared, errors


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ast_path = os.path.join(here, 'xml', 'ast.xml')

    if not os.path.exists(ast_path):
        print("[ОШИБКА] Файл ast.xml не найден. Сначала запустите парсер.")
        return

    root = load_ast(ast_path)
    declared, errors = analyze(root)

    print("Таблица объявленных идентификаторов")
    for name, line in declared.items():
        print(f"  {name}")

    if errors:
        print("\nСемантические ошибки")
        for e in errors:
            print(f"  [ОШИБКА] {e}")
    else:
        print("\nСемантических ошибок не обнаружено.")


if __name__ == '__main__':
    main()