import re


TOKEN_PATTERN = r"\d+\.\d+|\w+|\+\+|&&|\|\||==|!=|<=|>=|[][(),{};=+\-*/<>]"


def tokenize(line):
    source = re.sub(r"//.*", "", line)
    return re.findall(TOKEN_PATTERN, source)


def tokenize_with_lines(source):
    tokens = []
    line_numbers = []

    for line_no, line in enumerate(source.splitlines(), 1):
        clean_line = re.sub(r"//.*", "", line)
        parts = re.findall(TOKEN_PATTERN, clean_line)
        tokens.extend(parts)
        line_numbers.extend([line_no] * len(parts))

    return tokens, line_numbers
