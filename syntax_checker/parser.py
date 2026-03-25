def is_variable(token):
    return token.isalpha()


def is_number(token):
    return token.isdigit()


def is_relop(token):
    return token in [">", "<", ">=", "<=", "==", "!="]


def parse_condition(tokens, i):
    if (
        i + 2 < len(tokens)
        and is_variable(tokens[i])
        and is_relop(tokens[i + 1])
        and (is_variable(tokens[i + 2]) or is_number(tokens[i + 2]))
    ):
        return i + 3
    return -1


def parse_assignment(tokens, i):
    if (
        i + 5 < len(tokens)
        and is_variable(tokens[i])
        and tokens[i + 1] == "="
        and is_variable(tokens[i + 2])
        and tokens[i + 3] == "+"
        and is_number(tokens[i + 4])
        and tokens[i + 5] == ";"
    ):
        return i + 6
    return -1


def parse_increment(tokens, i):
    if (
        i + 2 < len(tokens)
        and is_variable(tokens[i])
        and tokens[i + 1] == "++"
        and tokens[i + 2] == ";"
    ):
        return i + 3
    return -1


def parse_if(tokens):
    i = 0

    if len(tokens) < 1 or tokens[i] != "if":
        return False
    i += 1

    if i >= len(tokens) or tokens[i] != "(":
        return False
    i += 1

    i = parse_condition(tokens, i)
    if i == -1:
        return False

    if i >= len(tokens) or tokens[i] != ")":
        return False
    i += 1

    i = parse_assignment(tokens, i)
    if i == -1:
        return False

    return i == len(tokens)


def parse_while(tokens):
    i = 0

    if len(tokens) < 1 or tokens[i] != "while":
        return False
    i += 1

    if i >= len(tokens) or tokens[i] != "(":
        return False
    i += 1

    i = parse_condition(tokens, i)
    if i == -1:
        return False

    if i >= len(tokens) or tokens[i] != ")":
        return False
    i += 1

    i = parse_increment(tokens, i)
    if i == -1:
        return False

    return i == len(tokens)


def parse(tokens):
    if not tokens:
        return False

    if tokens[0] == "if":
        return parse_if(tokens)

    if tokens[0] == "while":
        return parse_while(tokens)

    return False
