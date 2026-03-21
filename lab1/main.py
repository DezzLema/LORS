import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

KEYWORDS = {
    'var', 'begin', 'end', 'repeat', 'until',
    'integer', 'real', 'boolean', 'string',
}

OPERATORS = set('+-*/=<>')
DELIMITERS = set(';:,.()')


# Лексер (конечный автомат)

def tokenize(src: str) -> list[dict]:
    tokens = []
    i, line = 0, 1

    def add(kind, val):
        tokens.append({'type': kind, 'value': val, 'line': line})

    while i < len(src):
        ch = src[i]

        if ch in ' \t\r':
            i += 1
            continue

        if ch == '\n':
            line += 1
            i += 1
            continue

        # Комментарий { ... }
        if ch == '{':
            i += 1
            while i < len(src) and src[i] != '}':
                if src[i] == '\n':
                    line += 1
                i += 1
            if i >= len(src):
                raise SyntaxError(f"Строка {line}: незакрытый комментарий")
            i += 1
            continue

        # WORD: ключевое слово или идентификатор
        if ch.isalpha() or ch == '_':
            j = i
            while i < len(src) and (src[i].isalnum() or src[i] == '_'):
                i += 1
            word = src[j:i].lower()
            add('KW' if word in KEYWORDS else 'ID', word)
            continue

        # NUM: число
        if ch.isdigit():
            j = i
            while i < len(src) and (src[i].isdigit() or src[i] == '.'):
                i += 1
            add('NUM', src[j:i])
            continue

        # ASSN: ':=' или просто ':'
        if ch == ':':
            if i + 1 < len(src) and src[i + 1] == '=':
                add('OP', ':=')
                i += 2
            else:
                add('DELIM', ':')
                i += 1
            continue

        # INCR: '++' или просто '+'
        if ch == '+':
            if i + 1 < len(src) and src[i + 1] == '+':
                add('OP', '++')
                i += 2
            else:
                add('OP', '+')
                i += 1
            continue

        # Прочие операторы
        if ch in OPERATORS:
            add('OP', ch)
            i += 1
            continue

        # Разделители
        if ch in DELIMITERS:
            add('DELIM', ch)
            i += 1
            continue

        raise SyntaxError(f"Строка {line}: неизвестный символ '{ch}'")

    return tokens


# Таблицы идентификаторов и ключевых слов
def build_tables(tokens: list[dict]) -> tuple[list, list]:
    kw_table, id_table = [], []
    for t in tokens:
        if t['type'] == 'KW' and t['value'] not in kw_table:
            kw_table.append(t['value'])
        if t['type'] == 'ID' and t['value'] not in id_table:
            id_table.append(t['value'])
    return kw_table, id_table


# Замена токенов условными обозначениями
def encode(tokens, kw_table, id_table) -> list[str]:
    result = []
    for t in tokens:
        if t['type'] == 'KW':
            result.append(f"KW[{kw_table.index(t['value'])}]")
        elif t['type'] == 'ID':
            result.append(f"ID[{id_table.index(t['value'])}]")
        elif t['type'] == 'NUM':
            result.append(f"NUM({t['value']})")
        else:
            result.append(repr(t['value']))
    return result


# Вывод в XML
def to_xml(tokens, kw_table, id_table, encoded) -> str:
    root = ET.Element('lexer_output')

    kw_el = ET.SubElement(root, 'keywords')
    for i, kw in enumerate(kw_table):
        ET.SubElement(kw_el, 'entry', index=str(i)).text = kw

    id_el = ET.SubElement(root, 'identifiers')
    for i, name in enumerate(id_table):
        ET.SubElement(id_el, 'entry', index=str(i)).text = name

    stream = ET.SubElement(root, 'token_stream')
    for t, code in zip(tokens, encoded):
        ET.SubElement(stream, 'token',
                      type=t['type'], line=str(t['line']),
                      value=t['value'], code=code)

    xml_str = ET.tostring(root, encoding='unicode')
    return minidom.parseString(xml_str).toprettyxml(indent='  ')


def main():
    here = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(here, 'InputOutput', 'input.txt'), encoding='utf-8') as f:
        src = f.read()

    print("Исходный код")
    print(src)

    try:
        tokens = tokenize(src)
    except SyntaxError as e:
        print(f"\n[ОШИБКА] {e}")
        return

    kw_table, id_table = build_tables(tokens)
    encoded = encode(tokens, kw_table, id_table)

    print("Таблица ключевых слов")
    for i, kw in enumerate(kw_table):
        print(f"  KW[{i}] = {kw}")

    print("\nТаблица идентификаторов")
    for i, name in enumerate(id_table):
        print(f"  ID[{i}] = {name}")

    print("\nПоток токенов с условными обозначениями")
    print(' '.join(encoded))

    xml_out = to_xml(tokens, kw_table, id_table, encoded)
    out_path = os.path.join(here, 'xml', 'tokens.xml')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(xml_out)


if __name__ == '__main__':
    main()
