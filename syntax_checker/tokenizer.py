import re


TOKEN_PATTERN = r'"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\'|\d+\.\d+|\d+|\w+|\+\+|--|\+=|-=|\*=|/=|%=|&&|\|\||==|!=|<=|>=|[][(),{};:=+\-*/%<>!]'


def strip_comments(source):
    result = []
    i = 0
    in_line_comment = False
    in_block_comment = False
    in_string = False
    in_char = False
    escape = False

    while i < len(source):
        char = source[i]
        next_char = source[i + 1] if i + 1 < len(source) else ""

        if in_line_comment:
            if char == "\n":
                in_line_comment = False
                result.append(char)
            else:
                result.append(" ")
            i += 1
            continue

        if in_block_comment:
            if char == "*" and next_char == "/":
                result.extend("  ")
                in_block_comment = False
                i += 2
            else:
                result.append("\n" if char == "\n" else " ")
                i += 1
            continue

        if in_string:
            result.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            i += 1
            continue

        if in_char:
            result.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == "'":
                in_char = False
            i += 1
            continue

        if char == "/" and next_char == "/":
            result.extend("  ")
            in_line_comment = True
            i += 2
            continue

        if char == "/" and next_char == "*":
            result.extend("  ")
            in_block_comment = True
            i += 2
            continue

        result.append(char)
        if char == '"':
            in_string = True
        elif char == "'":
            in_char = True
        i += 1

    return "".join(result)


def tokenize(source):
    clean_source = strip_comments(source)
    return re.findall(TOKEN_PATTERN, clean_source)


def tokenize_with_lines(source):
    clean_source = strip_comments(source)
    tokens = []
    line_numbers = []

    for line_no, line in enumerate(clean_source.splitlines(), 1):
        parts = re.findall(TOKEN_PATTERN, line)
        tokens.extend(parts)
        line_numbers.extend([line_no] * len(parts))

    return tokens, line_numbers
