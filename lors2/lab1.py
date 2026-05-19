import re
import sys
import os


class Token:
    def __init__(self, type_, value, original=None):
        self.type = type_      # тип токена: keyword, identifier, number, operator, delimiter
        self.value = value     # условное обозначение (KW1, ID1, NUM1, :=, ; и т.д.)
        self.original = original  # исходное значение (program, x, 123 и т.д.)


class Lexer:
    # Ключевые слова в том порядке, в котором они будут пронумерованы
    KEYWORDS = ['program', 'var', 'integer', 'begin', 'repeat', 'until', 'end']

    def __init__(self, source_code):
        self.source = source_code
        self.pos = 0
        self.n = len(source_code)
        self.tokens = []

        # Таблицы для замены исходных значений на условные обозначения
        self.keywords_table = {}
        self.identifiers_table = {}
        self.numbers_table = {}

        # Счётчики для генерации уникальных номеров
        self.keyword_index = 1
        self.identifier_index = 1
        self.number_index = 1

    def tokenize(self):
        """Основной метод: проходим по всему исходному коду и разбиваем на токены"""
        while self.pos < self.n:
            ch = self.source[self.pos]

            # Пропускаем пробельные символы
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

            # Обрабатываем идентификаторы и ключевые слова
            if ch.isalpha() or ch == '_':
                self._read_word()
                continue

            # Обрабатываем числа
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

            # Операторы сравнения (<, >, =, <=, >=, <>)
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

            # Остальные операторы и разделители (+ - * / ; , ( ) .)
            if ch in {'+', '-', '*', '/', ';', ',', '(', ')', '.'}:
                token_type = 'operator' if ch in '+-*/' else 'delimiter'
                self.tokens.append(Token(token_type, ch, ch))
                self.pos += 1
                continue

            # Если дошли сюда - встретили неизвестный символ
            print(f'Ошибка: неожиданный символ "{ch}" на позиции {self.pos}')
            sys.exit(1)

        return self.tokens, self.keywords_table, self.identifiers_table, self.numbers_table

    def _read_word(self):
        """Считываем идентификатор или ключевое слово"""
        start = self.pos
        while self.pos < self.n and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            self.pos += 1
        word = self.source[start:self.pos]

        # Проверяем корректность идентификатора
        if not re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_]*', word):
            print(f'Ошибка: неверный идентификатор "{word}"')
            sys.exit(1)

        # Если это ключевое слово - добавляем в таблицу ключевых слов
        if word in self.KEYWORDS:
            if word not in self.keywords_table:
                self.keywords_table[word] = f'KW{self.keyword_index}'
                self.keyword_index += 1
            self.tokens.append(Token('keyword', self.keywords_table[word], word))
        else:
            # Иначе это идентификатор
            if word not in self.identifiers_table:
                self.identifiers_table[word] = f'ID{self.identifier_index}'
                self.identifier_index += 1
            self.tokens.append(Token('identifier', self.identifiers_table[word], word))

    def _read_number(self):
        """Считываем число"""
        start = self.pos
        while self.pos < self.n and self.source[self.pos].isdigit():
            self.pos += 1
        num = self.source[start:self.pos]

        if num not in self.numbers_table:
            self.numbers_table[num] = f'NUM{self.number_index}'
            self.number_index += 1
        self.tokens.append(Token('number', self.numbers_table[num], num))


class LexerOutputSaver:
    """Сохраняет результаты лексического анализа в файл"""
    def __init__(self, tokens, keywords_table, identifiers_table, numbers_table, output_path):
        self.tokens = tokens
        self.keywords_table = keywords_table
        self.identifiers_table = identifiers_table
        self.numbers_table = numbers_table
        self.output_path = output_path

    def save(self):
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

        with open(self.output_path, 'w', encoding='utf-8') as f:
            # Сначала записываем последовательность токенов
            token_sequence = ' '.join(t.value for t in self.tokens)
            f.write(token_sequence + '\n\n')

            # Затем таблицы для восстановления исходных значений
            f.write('KEYWORDS TABLE\n')
            for original, replacement in self.keywords_table.items():
                f.write(f'{replacement}:{original}\n')
            f.write('\n')

            f.write('IDENTIFIERS TABLE\n')
            for original, replacement in self.identifiers_table.items():
                f.write(f'{replacement}:{original}\n')
            f.write('\n')

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