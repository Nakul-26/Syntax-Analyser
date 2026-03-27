class Node:
    def __init__(self, type, value=None):
        self.type = type
        self.value = value
        self.children = []

    def add(self, node):
        if node is not None:
            self.children.append(node)

    def label(self):
        return self.type if self.value is None else f"{self.type} ({self.value})"

    def to_lines(self, indent=0):
        lines = ["  " * indent + self.label()]
        for child in self.children:
            lines.extend(child.to_lines(indent + 1))
        return lines


def is_variable(token):
    return token.isalpha()


def is_number(token):
    return token.isdigit()


def is_relop(token):
    return token in [">", "<", ">=", "<=", "==", "!="]


def make_identifier(name):
    return Node("IDENT", name)


def make_number(value):
    return Node("NUMBER", value)


def set_error(errors, index, message, tokens=None):
    if errors is None or "message" in errors:
        return

    token = "<eof>" if tokens is None or index >= len(tokens) else tokens[index]
    errors["index"] = index
    errors["token"] = token
    errors["message"] = message


def parse_condition(tokens, i, errors=None):
    if i >= len(tokens):
        set_error(errors, i, "Expected condition", tokens)
        return -1, None

    if not is_variable(tokens[i]):
        set_error(errors, i, "Expected variable on left side of condition", tokens)
        return -1, None

    left = make_identifier(tokens[i])
    i += 1

    if i >= len(tokens) or not is_relop(tokens[i]):
        set_error(errors, i, "Expected relational operator", tokens)
        return -1, None

    op = tokens[i]
    i += 1

    if i >= len(tokens):
        set_error(errors, i, "Expected right side of condition", tokens)
        return -1, None

    if is_variable(tokens[i]):
        right = make_identifier(tokens[i])
    elif is_number(tokens[i]):
        right = make_number(tokens[i])
    else:
        set_error(errors, i, "Expected variable or number on right side of condition", tokens)
        return -1, None

    condition = Node("CONDITION", op)
    condition.add(left)
    condition.add(right)
    return i + 1, condition


def parse_factor(tokens, i, errors=None):
    if i >= len(tokens):
        set_error(errors, i, "Expected operand", tokens)
        return -1, None

    if is_variable(tokens[i]):
        return i + 1, make_identifier(tokens[i])

    if is_number(tokens[i]):
        return i + 1, make_number(tokens[i])

    set_error(errors, i, "Expected operand", tokens)
    return -1, None


def parse_term(tokens, i, errors=None):
    i, node = parse_factor(tokens, i, errors)
    if i == -1:
        return -1, None

    while i < len(tokens) and tokens[i] in ["*", "/"]:
        op = tokens[i]
        i += 1
        i, right = parse_factor(tokens, i, errors)
        if i == -1:
            return -1, None

        expr = Node(op)
        expr.add(node)
        expr.add(right)
        node = expr

    return i, node


def parse_expr(tokens, i, errors=None):
    i, node = parse_term(tokens, i, errors)
    if i == -1:
        return -1, None

    while i < len(tokens) and tokens[i] in ["+", "-"]:
        op = tokens[i]
        i += 1
        i, right = parse_term(tokens, i, errors)
        if i == -1:
            return -1, None

        expr = Node(op)
        expr.add(node)
        expr.add(right)
        node = expr

    return i, node


def parse_assignment(tokens, i, errors=None):
    if i >= len(tokens) or not is_variable(tokens[i]):
        set_error(errors, i, "Expected assignment target", tokens)
        return -1, None

    assignment = Node("ASSIGN")
    assignment.add(make_identifier(tokens[i]))
    i += 1

    if i >= len(tokens) or tokens[i] != "=":
        set_error(errors, i, "Expected '='", tokens)
        return -1, None
    i += 1

    i, expr = parse_expr(tokens, i, errors)
    if i == -1:
        return -1, None
    assignment.add(expr)

    if i >= len(tokens) or tokens[i] != ";":
        set_error(errors, i, "Expected ';'", tokens)
        return -1, None

    return i + 1, assignment


def parse_increment(tokens, i, errors=None):
    if i >= len(tokens) or not is_variable(tokens[i]):
        set_error(errors, i, "Expected increment target", tokens)
        return -1, None

    increment = Node("INCREMENT")
    increment.add(make_identifier(tokens[i]))
    i += 1

    if i >= len(tokens) or tokens[i] != "++":
        set_error(errors, i, "Expected '++'", tokens)
        return -1, None
    i += 1

    if i >= len(tokens) or tokens[i] != ";":
        set_error(errors, i, "Expected ';'", tokens)
        return -1, None

    return i + 1, increment


def parse_block(tokens, i, errors=None):
    if i >= len(tokens) or tokens[i] != "{":
        set_error(errors, i, "Missing '{'", tokens)
        return -1, None

    block = Node("BLOCK")
    i += 1

    while i < len(tokens) and tokens[i] != "}":
        i, statement = parse_statement(tokens, i, errors)
        if i == -1:
            return -1, None
        block.add(statement)

    if i >= len(tokens) or tokens[i] != "}":
        set_error(errors, i, "Missing '}'", tokens)
        return -1, None

    return i + 1, block


def parse_if(tokens, i=0, errors=None):
    if i >= len(tokens) or tokens[i] != "if":
        set_error(errors, i, "Expected 'if'", tokens)
        return -1, None
    i += 1

    if i >= len(tokens) or tokens[i] != "(":
        set_error(errors, i, "Missing '(' after if", tokens)
        return -1, None
    i += 1

    i, condition = parse_condition(tokens, i, errors)
    if i == -1:
        return -1, None

    if i >= len(tokens) or tokens[i] != ")":
        set_error(errors, i, "Missing ')'", tokens)
        return -1, None
    i += 1

    if_node = Node("IF")
    if_node.add(condition)

    if i >= len(tokens):
        set_error(errors, i, "Expected statement after if condition", tokens)
        return -1, None

    if tokens[i] == "{":
        i, then_branch = parse_block(tokens, i, errors)
    else:
        i, then_branch = parse_statement(tokens, i, errors)
    if i == -1:
        return -1, None
    if_node.add(then_branch)

    if i < len(tokens) and tokens[i] == "else":
        else_node = Node("ELSE")
        i += 1

        if i >= len(tokens):
            set_error(errors, i, "Expected statement after else", tokens)
            return -1, None

        if tokens[i] == "{":
            i, else_branch = parse_block(tokens, i, errors)
        else:
            i, else_branch = parse_statement(tokens, i, errors)
        if i == -1:
            return -1, None

        else_node.add(else_branch)
        if_node.add(else_node)

    return i, if_node


def parse_while(tokens, i=0, errors=None):
    if i >= len(tokens) or tokens[i] != "while":
        set_error(errors, i, "Expected 'while'", tokens)
        return -1, None
    i += 1

    if i >= len(tokens) or tokens[i] != "(":
        set_error(errors, i, "Missing '(' after while", tokens)
        return -1, None
    i += 1

    i, condition = parse_condition(tokens, i, errors)
    if i == -1:
        return -1, None

    if i >= len(tokens) or tokens[i] != ")":
        set_error(errors, i, "Missing ')'", tokens)
        return -1, None
    i += 1

    while_node = Node("WHILE")
    while_node.add(condition)

    if i >= len(tokens):
        set_error(errors, i, "Expected loop body", tokens)
        return -1, None

    if tokens[i] == "{":
        i, body = parse_block(tokens, i, errors)
    else:
        i, body = parse_statement(tokens, i, errors)
    if i == -1:
        return -1, None

    while_node.add(body)
    return i, while_node


def parse_statement(tokens, i, errors=None):
    if i >= len(tokens):
        set_error(errors, i, "Unexpected end of input", tokens)
        return -1, None

    if tokens[i] == "if":
        return parse_if(tokens, i, errors)

    if tokens[i] == "while":
        return parse_while(tokens, i, errors)

    if i + 1 < len(tokens) and tokens[i + 1] == "=":
        return parse_assignment(tokens, i, errors)

    if i + 1 < len(tokens) and tokens[i + 1] == "++":
        return parse_increment(tokens, i, errors)

    set_error(errors, i, "Unexpected token", tokens)
    return -1, None


def parse(tokens, errors=None):
    if not tokens:
        set_error(errors, 0, "Empty input", tokens)
        return False

    i = 0
    while i < len(tokens):
        i, _ = parse_statement(tokens, i, errors)
        if i == -1:
            return False

    return True


def parse_main(tokens, i, errors=None):
    if i >= len(tokens) or tokens[i] != "int":
        set_error(errors, i, "Expected 'int'", tokens)
        return -1, None
    i += 1

    if i >= len(tokens) or tokens[i] != "main":
        set_error(errors, i, "Expected 'main'", tokens)
        return -1, None
    i += 1

    if i >= len(tokens) or tokens[i] != "(":
        set_error(errors, i, "Missing '(' after main", tokens)
        return -1, None
    i += 1

    if i >= len(tokens) or tokens[i] != ")":
        set_error(errors, i, "Missing ')'", tokens)
        return -1, None
    i += 1

    i, block = parse_block(tokens, i, errors)
    if i == -1:
        return -1, None

    main_node = Node("MAIN")
    main_node.add(block)
    return i, main_node


def parse_program(tokens, errors=None):
    if not tokens:
        set_error(errors, 0, "Empty input", tokens)
        return None

    program = Node("PROGRAM")
    i = 0

    if len(tokens) >= 2 and tokens[0] == "int" and tokens[1] == "main":
        i, main_node = parse_main(tokens, 0, errors)
        if i == -1:
            return None
        program.add(main_node)
    else:
        while i < len(tokens):
            i, statement = parse_statement(tokens, i, errors)
            if i == -1:
                return None
            program.add(statement)

    if i != len(tokens):
        set_error(errors, i, "Unexpected token after program end", tokens)
        return None

    return program
