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


DECLARATION_TYPES = {"int", "float"}


def is_variable(token):
    return token.isalpha()


def is_int(token):
    return token.isdigit()


def is_float(token):
    if token.count(".") != 1:
        return False

    left, right = token.split(".", 1)
    return left.isdigit() and right.isdigit()


def is_number(token):
    return is_int(token) or is_float(token)


def is_relop(token):
    return token in [">", "<", ">=", "<=", "==", "!="]


def make_identifier(name):
    return Node("IDENT", name)


def make_number(value):
    return Node("NUMBER", value)


def make_type(value):
    return Node("TYPE", value)


def semantic_enabled(context):
    return context is not None and "symbol_table" in context


def initialize_context(context):
    if context is None:
        return None

    context.setdefault("symbol_table", {})
    context.setdefault("intermediate_code", [])
    context.setdefault("temp_count", 1)
    return context


def declare_variable(context, name, var_type):
    if context is None:
        return

    context["symbol_table"][name] = var_type


def is_declared(context, name):
    return context is not None and name in context["symbol_table"]


def get_token_type(context, token):
    if is_int(token):
        return "int"
    if is_float(token):
        return "float"
    if is_variable(token):
        return context["symbol_table"].get(token)
    return None


def combine_types(left_type, right_type):
    if left_type == "float" or right_type == "float":
        return "float"
    return "int"


def is_assignment_compatible(target_type, value_type):
    if target_type == value_type:
        return True
    return target_type == "float" and value_type == "int"


def infer_node_type(node, context):
    if node.type == "IDENT":
        return context["symbol_table"].get(node.value)

    if node.type == "NUMBER":
        return "float" if is_float(node.value) else "int"

    if node.type in ["+", "-", "*", "/"]:
        left_type = infer_node_type(node.children[0], context)
        right_type = infer_node_type(node.children[1], context)
        if left_type is None or right_type is None:
            return None
        if node.type == "/":
            return "float" if "float" in [left_type, right_type] else "int"
        return combine_types(left_type, right_type)

    return None


def new_temp(context):
    temp = f"t{context['temp_count']}"
    context["temp_count"] += 1
    return temp


def generate_expr_code(node, context):
    if node.type in ["IDENT", "NUMBER"]:
        return [], node.value

    left_code, left_name = generate_expr_code(node.children[0], context)
    right_code, right_name = generate_expr_code(node.children[1], context)
    temp = new_temp(context)
    code = left_code + right_code + [f"{temp} = {left_name} {node.type} {right_name}"]
    return code, temp


def generate_statement_code(node, context):
    if node.type == "PROGRAM":
        code = []
        for child in node.children:
            code.extend(generate_statement_code(child, context))
        return code

    if node.type in ["MAIN", "BLOCK", "ELSE"]:
        code = []
        for child in node.children:
            code.extend(generate_statement_code(child, context))
        return code

    if node.type == "DECL":
        return []

    if node.type == "ASSIGN":
        expr_code, result_name = generate_expr_code(node.children[1], context)
        target = node.children[0].value
        return expr_code + [f"{target} = {result_name}"]

    if node.type == "INCREMENT":
        target = node.children[0].value
        temp = new_temp(context)
        return [f"{temp} = {target} + 1", f"{target} = {temp}"]

    if node.type == "IF":
        code = []
        for child in node.children[1:]:
            code.extend(generate_statement_code(child, context))
        return code

    if node.type == "WHILE":
        return generate_statement_code(node.children[1], context)

    return []


def set_error(errors, index, message, tokens=None):
    if errors is None or "message" in errors:
        return

    token = "<eof>" if tokens is None or index >= len(tokens) else tokens[index]
    errors["index"] = index
    errors["token"] = token
    errors["message"] = message


def parse_condition(tokens, i, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens):
        set_error(errors, i, "Expected condition", tokens)
        return -1, None

    if not is_variable(tokens[i]):
        set_error(errors, i, "Expected variable on left side of condition", tokens)
        return -1, None
    if semantic_enabled(context) and not is_declared(context, tokens[i]):
        set_error(errors, i, f"Variable '{tokens[i]}' not declared", tokens)
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
        if semantic_enabled(context) and not is_declared(context, tokens[i]):
            set_error(errors, i, f"Variable '{tokens[i]}' not declared", tokens)
            return -1, None
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


def parse_factor(tokens, i, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens):
        set_error(errors, i, "Expected operand", tokens)
        return -1, None

    if is_variable(tokens[i]):
        if semantic_enabled(context) and not is_declared(context, tokens[i]):
            set_error(errors, i, f"Variable '{tokens[i]}' not declared", tokens)
            return -1, None
        return i + 1, make_identifier(tokens[i])

    if is_number(tokens[i]):
        return i + 1, make_number(tokens[i])

    set_error(errors, i, "Expected operand", tokens)
    return -1, None


def parse_term(tokens, i, errors=None, context=None):
    initialize_context(context)
    i, node = parse_factor(tokens, i, errors, context)
    if i == -1:
        return -1, None

    while i < len(tokens) and tokens[i] in ["*", "/"]:
        op = tokens[i]
        i += 1
        i, right = parse_factor(tokens, i, errors, context)
        if i == -1:
            return -1, None

        expr = Node(op)
        expr.add(node)
        expr.add(right)
        node = expr

    return i, node


def parse_expr(tokens, i, errors=None, context=None):
    initialize_context(context)
    i, node = parse_term(tokens, i, errors, context)
    if i == -1:
        return -1, None

    while i < len(tokens) and tokens[i] in ["+", "-"]:
        op = tokens[i]
        i += 1
        i, right = parse_term(tokens, i, errors, context)
        if i == -1:
            return -1, None

        expr = Node(op)
        expr.add(node)
        expr.add(right)
        node = expr

    return i, node


def parse_assignment(tokens, i, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens) or not is_variable(tokens[i]):
        set_error(errors, i, "Expected assignment target", tokens)
        return -1, None
    if semantic_enabled(context) and not is_declared(context, tokens[i]):
        set_error(errors, i, f"Variable '{tokens[i]}' not declared", tokens)
        return -1, None

    target_name = tokens[i]
    assignment = Node("ASSIGN")
    assignment.add(make_identifier(target_name))
    i += 1

    if i >= len(tokens) or tokens[i] != "=":
        set_error(errors, i, "Expected '='", tokens)
        return -1, None
    i += 1

    i, expr = parse_expr(tokens, i, errors, context)
    if i == -1:
        return -1, None
    assignment.add(expr)

    if semantic_enabled(context):
        target_type = context["symbol_table"][target_name]
        expr_type = infer_node_type(expr, context)
        if expr_type is None:
            set_error(errors, i, "Unable to infer expression type", tokens)
            return -1, None
        if not is_assignment_compatible(target_type, expr_type):
            set_error(errors, i, f"Type mismatch: cannot assign {expr_type} to {target_type}", tokens)
            return -1, None

    if i >= len(tokens) or tokens[i] != ";":
        set_error(errors, i, "Expected ';'", tokens)
        return -1, None

    return i + 1, assignment


def parse_increment(tokens, i, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens) or not is_variable(tokens[i]):
        set_error(errors, i, "Expected increment target", tokens)
        return -1, None
    if semantic_enabled(context) and not is_declared(context, tokens[i]):
        set_error(errors, i, f"Variable '{tokens[i]}' not declared", tokens)
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


def parse_block(tokens, i, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens) or tokens[i] != "{":
        set_error(errors, i, "Missing '{'", tokens)
        return -1, None

    block = Node("BLOCK")
    i += 1

    while i < len(tokens) and tokens[i] != "}":
        i, statement = parse_statement(tokens, i, errors, context)
        if i == -1:
            return -1, None
        block.add(statement)

    if i >= len(tokens) or tokens[i] != "}":
        set_error(errors, i, "Missing '}'", tokens)
        return -1, None

    return i + 1, block


def parse_if(tokens, i=0, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens) or tokens[i] != "if":
        set_error(errors, i, "Expected 'if'", tokens)
        return -1, None
    i += 1

    if i >= len(tokens) or tokens[i] != "(":
        set_error(errors, i, "Missing '(' after if", tokens)
        return -1, None
    i += 1

    i, condition = parse_condition(tokens, i, errors, context)
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
        i, then_branch = parse_block(tokens, i, errors, context)
    else:
        i, then_branch = parse_statement(tokens, i, errors, context)
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
            i, else_branch = parse_block(tokens, i, errors, context)
        else:
            i, else_branch = parse_statement(tokens, i, errors, context)
        if i == -1:
            return -1, None

        else_node.add(else_branch)
        if_node.add(else_node)

    return i, if_node


def parse_while(tokens, i=0, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens) or tokens[i] != "while":
        set_error(errors, i, "Expected 'while'", tokens)
        return -1, None
    i += 1

    if i >= len(tokens) or tokens[i] != "(":
        set_error(errors, i, "Missing '(' after while", tokens)
        return -1, None
    i += 1

    i, condition = parse_condition(tokens, i, errors, context)
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
        i, body = parse_block(tokens, i, errors, context)
    else:
        i, body = parse_statement(tokens, i, errors, context)
    if i == -1:
        return -1, None

    while_node.add(body)
    return i, while_node


def parse_declaration(tokens, i, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens) or tokens[i] not in DECLARATION_TYPES:
        set_error(errors, i, "Expected type declaration", tokens)
        return -1, None

    var_type = tokens[i]
    i += 1

    if i >= len(tokens) or not is_variable(tokens[i]):
        set_error(errors, i, "Expected variable name", tokens)
        return -1, None
    if semantic_enabled(context) and is_declared(context, tokens[i]):
        set_error(errors, i, f"Variable '{tokens[i]}' already declared", tokens)
        return -1, None

    name = tokens[i]
    declaration = Node("DECL", var_type)
    declaration.add(make_type(var_type))
    declaration.add(make_identifier(name))
    i += 1

    if i >= len(tokens) or tokens[i] != ";":
        set_error(errors, i, "Expected ';'", tokens)
        return -1, None

    declare_variable(context, name, var_type)
    return i + 1, declaration


def parse_statement(tokens, i, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens):
        set_error(errors, i, "Unexpected end of input", tokens)
        return -1, None

    if tokens[i] in DECLARATION_TYPES:
        return parse_declaration(tokens, i, errors, context)

    if tokens[i] == "if":
        return parse_if(tokens, i, errors, context)

    if tokens[i] == "while":
        return parse_while(tokens, i, errors, context)

    if i + 1 < len(tokens) and tokens[i + 1] == "=":
        return parse_assignment(tokens, i, errors, context)

    if i + 1 < len(tokens) and tokens[i + 1] == "++":
        return parse_increment(tokens, i, errors, context)

    set_error(errors, i, "Unexpected token", tokens)
    return -1, None


def parse(tokens, errors=None, context=None):
    initialize_context(context)

    if not tokens:
        set_error(errors, 0, "Empty input", tokens)
        return False

    i = 0
    while i < len(tokens):
        i, _ = parse_statement(tokens, i, errors, context)
        if i == -1:
            return False

    return True


def parse_main(tokens, i, errors=None, context=None):
    initialize_context(context)

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

    i, block = parse_block(tokens, i, errors, context)
    if i == -1:
        return -1, None

    main_node = Node("MAIN")
    main_node.add(block)
    return i, main_node


def parse_program(tokens, errors=None, context=None):
    initialize_context(context)

    if not tokens:
        set_error(errors, 0, "Empty input", tokens)
        return None

    program = Node("PROGRAM")
    i = 0

    if len(tokens) >= 2 and tokens[0] == "int" and tokens[1] == "main":
        i, main_node = parse_main(tokens, 0, errors, context)
        if i == -1:
            return None
        program.add(main_node)
    else:
        while i < len(tokens):
            i, statement = parse_statement(tokens, i, errors, context)
            if i == -1:
                return None
            program.add(statement)

    if i != len(tokens):
        set_error(errors, i, "Unexpected token after program end", tokens)
        return None

    if context is not None:
        context["intermediate_code"] = generate_statement_code(program, context)

    return program
