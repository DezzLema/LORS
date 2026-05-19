import re
import sys
import os


class Token:
    def __init__(self, type_, value, original=None):
        self.type = type_
        self.value = value
        self.original = original


class Lexer:
    # Ключевые слова в том порядке, в котором они будут пронумерованы
    KEYWORDS = ['program', 'var', 'integer', 'begin', 'repeat', 'until', 'end']

    def __init__(self, source_code):
        self.source = source_code
        self.pos = 0
        self.n = len(source_code)
        self.tokens = []

        self.keywords_table = {}
        self.identifiers_table = {}
        self.numbers_table = {}

        self.keyword_index = 1
        self.identifier_index = 1
        self.number_index = 1

    def tokenize(self):
        while self.pos < self.n:
            ch = self.source[self.pos]

            if ch.isspace():
                self.pos += 1
                continue

            # Комментарии { ... }
            if ch == '{':
                self.pos += 1
                while self.pos < self.n and self.source[self.pos] != '}':
                    self.pos += 1
                self.pos += 1
                continue

            # Комментарии (* ... *)
            if ch == '(' and self.pos + 1 < self.n and self.source[self.pos + 1] == '*':
                self.pos += 2
                while self.pos + 1 < self.n and not (self.source[self.pos] == '*' and self.source[self.pos + 1] == ')'):
                    self.pos += 1
                self.pos += 2
                continue

            # Однострочные комментарии //
            if ch == '/' and self.pos + 1 < self.n and self.source[self.pos + 1] == '/':
                self.pos += 2
                while self.pos < self.n and self.source[self.pos] != '\n':
                    self.pos += 1
                continue

            # Идентификаторы и ключевые слова
            if ch.isalpha() or ch == '_':
                self._read_word()
                continue

            # Числа
            if ch.isdigit():
                self._read_number()
                continue

            # Присваивание :=
            if ch == ':':
                if self.pos + 1 < self.n and self.source[self.pos + 1] == '=':
                    self.tokens.append(Token('operator', ':=', ':='))
                    self.pos += 2
                else:
                    self.tokens.append(Token('delimiter', ':', ':'))
                    self.pos += 1
                continue

            # Операторы сравнения
            if ch in {'<', '>', '='}:
                if self.pos + 1 < self.n and self.source[self.pos + 1] == '=':
                    op = ch + '='
                    self.tokens.append(Token('operator', op, op))
                    self.pos += 2
                elif ch == '<' and self.pos + 1 < self.n and self.source[self.pos + 1] == '>':
                    self.tokens.append(Token('operator', '<>', '<>'))
                    self.pos += 2
                else:
                    self.tokens.append(Token('operator', ch, ch))
                    self.pos += 1
                continue

            # Остальные символы
            if ch in {'+', '-', '*', '/', ';', ',', '(', ')', '.'}:
                token_type = 'operator' if ch in '+-*/' else 'delimiter'
                self.tokens.append(Token(token_type, ch, ch))
                self.pos += 1
                continue

            print(f'Ошибка: неожиданный символ "{ch}" на позиции {self.pos}')
            sys.exit(1)

        return self.tokens, self.keywords_table, self.identifiers_table, self.numbers_table

    def _read_word(self):
        start = self.pos
        while self.pos < self.n and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            self.pos += 1
        word = self.source[start:self.pos]

        if not re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_]*', word):
            print(f'Ошибка: неверный идентификатор "{word}"')
            sys.exit(1)

        # Проверяем ключевое слово
        if word in self.KEYWORDS:
            if word not in self.keywords_table:
                self.keywords_table[word] = f'KW{self.keyword_index}'
                self.keyword_index += 1
            self.tokens.append(Token('keyword', self.keywords_table[word], word))
        else:
            if word not in self.identifiers_table:
                self.identifiers_table[word] = f'ID{self.identifier_index}'
                self.identifier_index += 1
            self.tokens.append(Token('identifier', self.identifiers_table[word], word))

    def _read_number(self):
        start = self.pos
        while self.pos < self.n and self.source[self.pos].isdigit():
            self.pos += 1
        num = self.source[start:self.pos]

        if num not in self.numbers_table:
            self.numbers_table[num] = f'NUM{self.number_index}'
            self.number_index += 1
        self.tokens.append(Token('number', self.numbers_table[num], num))


class LexerOutputSaver:
    def __init__(self, tokens, keywords_table, identifiers_table, numbers_table, output_path):
        self.tokens = tokens
        self.keywords_table = keywords_table
        self.identifiers_table = identifiers_table
        self.numbers_table = numbers_table
        self.output_path = output_path

    def save(self):
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

        with open(self.output_path, 'w', encoding='utf-8') as f:
            # Последовательность токенов
            token_sequence = ' '.join(t.value for t in self.tokens)
            f.write(token_sequence + '\n\n')

            # Таблица ключевых слов
            f.write('KEYWORDS TABLE\n')
            for original, replacement in self.keywords_table.items():
                f.write(f'{replacement}:{original}\n')
            f.write('\n')

            # Таблица идентификаторов
            f.write('IDENTIFIERS TABLE\n')
            for original, replacement in self.identifiers_table.items():
                f.write(f'{replacement}:{original}\n')
            f.write('\n')

            # Таблица чисел
            f.write('NUMBERS TABLE\n')
            for original, replacement in self.numbers_table.items():
                f.write(f'{replacement}:{original}\n')


def main():
    if not os.path.exists('input.pas'):
        print('Ошибка: файл input.pas не найден')
        sys.exit(1)

    with open('input.pas', 'r', encoding='utf-8') as f:
        source_code = f.read()

    print('Начинаем лексический анализ...')

    lexer = Lexer(source_code)
    tokens, keywords_table, identifiers_table, numbers_table = lexer.tokenize()

    saver = LexerOutputSaver(tokens, keywords_table, identifiers_table, numbers_table, 'output/tokens.txt')
    saver.save()

    print(f'Лексический анализ завершён. Найдено токенов: {len(tokens)}')
    print('Результат сохранён в output/tokens.txt')


if __name__ == '__main__':
    main()