class Node:
    def __init__(self, name):
        self.name = name
        self.children = []

    def add(self, child):
        self.children.append(child)

    def to_lines(self, indent=0):
        lines = ["  " * indent + self.name]
        for child in self.children:
            lines.extend(child.to_lines(indent + 1))
        return lines


def is_variable(token):
    return token.isalpha()


def is_number(token):
    return token.isdigit()


def is_relop(token):
    return token in [">", "<", ">=", "<=", "==", "!="]


def set_error(errors, index, message):
    if errors is not None and "message" not in errors:
        errors["index"] = index
        errors["message"] = message


def parse_condition(tokens, i, errors=None):
    if i >= len(tokens):
        set_error(errors, i, "Error: Incomplete condition")
        return -1, None

    if not is_variable(tokens[i]):
        set_error(errors, i, "Error: Invalid condition")
        return -1, None

    if i + 1 >= len(tokens) or not is_relop(tokens[i + 1]):
        set_error(errors, i + 1, "Error: Invalid condition")
        return -1, None

    if i + 2 >= len(tokens) or not (is_variable(tokens[i + 2]) or is_number(tokens[i + 2])):
        set_error(errors, i + 2, "Error: Invalid condition")
        return -1, None

    condition = Node(f"CONDITION ({tokens[i]} {tokens[i + 1]} {tokens[i + 2]})")
    return i + 3, condition


def parse_assignment(tokens, i, errors=None):
    if i >= len(tokens) or not is_variable(tokens[i]):
        set_error(errors, i, "Error: Expected assignment statement")
        return -1, None

    if i + 1 >= len(tokens) or tokens[i + 1] != "=":
        set_error(errors, i + 1, "Error: Expected '='")
        return -1, None

    if i + 2 >= len(tokens) or not is_variable(tokens[i + 2]):
        set_error(errors, i + 2, "Error: Expected variable after '='")
        return -1, None

    if i + 3 >= len(tokens) or tokens[i + 3] != "+":
        set_error(errors, i + 3, "Error: Expected '+'")
        return -1, None

    if i + 4 >= len(tokens) or not is_number(tokens[i + 4]):
        set_error(errors, i + 4, "Error: Expected number after '+'")
        return -1, None

    if i + 5 >= len(tokens) or tokens[i + 5] != ";":
        set_error(errors, i + 5, "Error: Expected ';'")
        return -1, None

    assignment = Node(f"ASSIGN ({tokens[i]} = {tokens[i + 2]} + {tokens[i + 4]})")
    return i + 6, assignment


def parse_increment(tokens, i, errors=None):
    if i >= len(tokens) or not is_variable(tokens[i]):
        set_error(errors, i, "Error: Expected increment statement")
        return -1, None

    if i + 1 >= len(tokens) or tokens[i + 1] != "++":
        set_error(errors, i + 1, "Error: Expected '++'")
        return -1, None

    if i + 2 >= len(tokens) or tokens[i + 2] != ";":
        set_error(errors, i + 2, "Error: Expected ';'")
        return -1, None

    increment = Node(f"INCREMENT ({tokens[i]}++)")
    return i + 3, increment


def parse_block(tokens, i, errors=None):
    if i >= len(tokens) or tokens[i] != "{":
        set_error(errors, i, "Error: Missing '{'")
        return -1, None
    i += 1
    block = Node("BLOCK")

    while i < len(tokens) and tokens[i] != "}":
        i, statement = parse_statement(tokens, i, errors)
        if i == -1:
            return -1, None
        block.add(statement)

    if i >= len(tokens) or tokens[i] != "}":
        set_error(errors, i, "Error: Missing '}'")
        return -1, None

    return i + 1, block


def parse_if(tokens, i=0, errors=None):
    if i >= len(tokens) or tokens[i] != "if":
        set_error(errors, i, "Error: Expected 'if'")
        return -1, None
    i += 1

    if i >= len(tokens) or tokens[i] != "(":
        set_error(errors, i, "Error: Missing '('")
        return -1, None
    i += 1

    i, condition = parse_condition(tokens, i, errors)
    if i == -1:
        return -1, None

    if i >= len(tokens) or tokens[i] != ")":
        set_error(errors, i, "Error: Missing ')'")
        return -1, None
    i += 1

    if_node = Node("IF")
    if_node.add(condition)

    if i < len(tokens) and tokens[i] == "{":
        i, block = parse_block(tokens, i, errors)
        if i == -1:
            return -1, None
        if_node.add(block)
        return i, if_node

    i, assignment = parse_assignment(tokens, i, errors)
    if i == -1:
        return -1, None
    if_node.add(assignment)
    return i, if_node


def parse_while(tokens, i=0, errors=None):
    if i >= len(tokens) or tokens[i] != "while":
        set_error(errors, i, "Error: Expected 'while'")
        return -1, None
    i += 1

    if i >= len(tokens) or tokens[i] != "(":
        set_error(errors, i, "Error: Missing '('")
        return -1, None
    i += 1

    i, condition = parse_condition(tokens, i, errors)
    if i == -1:
        return -1, None

    if i >= len(tokens) or tokens[i] != ")":
        set_error(errors, i, "Error: Missing ')'")
        return -1, None
    i += 1

    while_node = Node("WHILE")
    while_node.add(condition)

    if i < len(tokens) and tokens[i] == "{":
        i, block = parse_block(tokens, i, errors)
        if i == -1:
            return -1, None
        while_node.add(block)
        return i, while_node

    i, increment = parse_increment(tokens, i, errors)
    if i == -1:
        return -1, None
    while_node.add(increment)
    return i, while_node


def parse_statement(tokens, i, errors=None):
    if i >= len(tokens):
        set_error(errors, i, "Error: Unexpected end of input")
        return -1, None

    if tokens[i] == "if":
        return parse_if(tokens, i, errors)

    if tokens[i] == "while":
        return parse_while(tokens, i, errors)

    if i + 1 < len(tokens) and tokens[i + 1] == "=":
        return parse_assignment(tokens, i, errors)

    if i + 1 < len(tokens) and tokens[i + 1] == "++":
        return parse_increment(tokens, i, errors)

    set_error(errors, i, f"Error: Unexpected token '{tokens[i]}'")
    return -1, None


def parse(tokens, errors=None):
    if not tokens:
        set_error(errors, 0, "Error: Empty input")
        return False

    i = 0
    while i < len(tokens):
        i, _ = parse_statement(tokens, i, errors)
        if i == -1:
            return False

    return True


def parse_program(tokens, errors=None):
    if not tokens:
        set_error(errors, 0, "Error: Empty input")
        return None

    program = Node("PROGRAM")
    i = 0

    while i < len(tokens):
        i, statement = parse_statement(tokens, i, errors)
        if i == -1:
            return None
        program.add(statement)

    return program
