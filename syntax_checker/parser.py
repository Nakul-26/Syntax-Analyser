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


DECLARATION_TYPES = {"int", "float", "char"}
KEYWORDS = {"if", "else", "while", "for", "return", "break", "continue", "int", "float", "char", "main"}
SYNC_TOKENS = {";", "{", "}", ")"}


def is_variable(token):
    if not token or token in KEYWORDS:
        return False
    if not (token[0].isalpha() or token[0] == "_"):
        return False
    return all(char.isalnum() or char == "_" for char in token)


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
    context.setdefault("scopes", [context["symbol_table"]])
    context.setdefault("intermediate_code", [])
    context.setdefault("temp_count", 1)
    return context


def declare_variable(context, name, var_type):
    if context is None:
        return

    current_scope(context)[name] = var_type
    context["symbol_table"][name] = var_type


def is_declared(context, name):
    return lookup_variable_type(context, name) is not None


def current_scope(context):
    if context is None:
        return {}
    initialize_context(context)
    return context["scopes"][-1]


def push_scope(context):
    if context is None:
        return
    initialize_context(context)
    context["scopes"].append({})


def pop_scope(context):
    if context is None:
        return
    initialize_context(context)
    if len(context["scopes"]) > 1:
        context["scopes"].pop()


def lookup_variable_type(context, name):
    if context is None:
        return None

    initialize_context(context)
    for scope in reversed(context["scopes"]):
        if name in scope:
            return scope[name]
    return None


def is_declared_in_current_scope(context, name):
    if context is None:
        return False
    return name in current_scope(context)


def is_function_name(token):
    return token == "main" or is_variable(token)


def get_token_type(context, token):
    if is_int(token):
        return "int"
    if is_float(token):
        return "float"
    if is_variable(token):
        return lookup_variable_type(context, token)
    return None


def combine_types(left_type, right_type):
    if left_type == "float" or right_type == "float":
        return "float"
    if left_type == "char" and right_type == "char":
        return "char"
    return "int"


def is_assignment_compatible(target_type, value_type):
    if target_type == value_type:
        return True
    return target_type == "float" and value_type == "int"


def infer_node_type(node, context):
    if node.type == "IDENT":
        return lookup_variable_type(context, node.value)

    if node.type == "NUMBER":
        return "float" if is_float(node.value) else "int"

    if node.type == "CALL":
        return "int"

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

    if node.type == "CALL":
        arg_code = []
        arg_values = []
        for child in node.children:
            child_code, child_name = generate_expr_code(child, context)
            arg_code.extend(child_code)
            arg_values.append(child_name)
        temp = new_temp(context)
        call_text = f"{node.value}({', '.join(arg_values)})"
        return arg_code + [f"{temp} = {call_text}"], temp

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

    if node.type == "FUNCTION":
        return generate_statement_code(node.children[-1], context)

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

    if node.type == "CALL_STMT":
        call_expr = Node("CALL", node.value)
        for child in node.children:
            call_expr.add(child)
        call_code, _ = generate_expr_code(call_expr, context)
        return call_code

    if node.type == "RETURN":
        expr_code, result_name = generate_expr_code(node.children[0], context)
        return expr_code + [f"return {result_name}"]

    if node.type in ["BREAK", "CONTINUE"]:
        return [node.type.lower()]

    if node.type == "IF":
        code = []
        for child in node.children[1:]:
            code.extend(generate_statement_code(child, context))
        return code

    if node.type == "WHILE":
        return generate_statement_code(node.children[1], context)

    if node.type == "FOR":
        code = []
        for child in node.children:
            code.extend(generate_statement_code(child, context))
        return code

    return []


def set_error(errors, index, message, tokens=None):
    if errors is None:
        return

    token = "<eof>" if tokens is None or index >= len(tokens) else tokens[index]
    line_numbers = errors.get("line_numbers", [])
    line = None
    if 0 <= index < len(line_numbers):
        line = line_numbers[index]

    item = {
        "index": index,
        "token": token,
        "line": line,
        "message": message,
    }
    errors.setdefault("items", []).append(item)

    if "message" not in errors:
        errors["index"] = index
        errors["token"] = token
        errors["line"] = line
        errors["message"] = message


def has_recorded_errors(errors):
    return errors is not None and bool(errors.get("items"))


def get_last_error_index(errors, fallback_index):
    if errors is None:
        return fallback_index
    items = errors.get("items", [])
    if not items:
        return fallback_index
    last_index = items[-1].get("index", fallback_index)
    if last_index is None or last_index < fallback_index:
        return fallback_index
    return last_index


def recover_to_sync(tokens, start_index, sync_tokens=None, consume=True):
    sync_tokens = SYNC_TOKENS if sync_tokens is None else sync_tokens
    i = max(0, start_index)

    while i < len(tokens) and tokens[i] not in sync_tokens:
        i += 1

    if i < len(tokens):
        if not consume or tokens[i] == "{":
            return max(i, start_index + 1)
        return max(i + 1, start_index + 1)
    return len(tokens)


def recover_statement(tokens, errors, start_index, block_terminators=None):
    sync_tokens = set(SYNC_TOKENS)
    if block_terminators is not None:
        sync_tokens.update(block_terminators)

    return recover_to_sync(tokens, get_last_error_index(errors, start_index), sync_tokens, consume=False)


def parse_condition(tokens, i, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens):
        set_error(errors, i, "Expected condition", tokens)
        return -1, None

    i, left = parse_expr(tokens, i, errors, context)
    if i == -1:
        set_error(errors, i, "Expected expression on left side of condition", tokens)
        return -1, None

    if i >= len(tokens) or not is_relop(tokens[i]):
        set_error(errors, i, "Expected relational operator", tokens)
        return -1, None

    op = tokens[i]
    i += 1

    i, right = parse_expr(tokens, i, errors, context)
    if i == -1:
        set_error(errors, i, "Expected expression on right side of condition", tokens)
        return -1, None

    condition = Node("CONDITION", op)
    condition.add(left)
    condition.add(right)
    return i, condition


def parse_factor(tokens, i, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens):
        set_error(errors, i, "Expected operand", tokens)
        return -1, None

    if is_variable(tokens[i]):
        if i + 1 < len(tokens) and tokens[i + 1] == "(":
            return parse_call_expression(tokens, i, errors, context)
        if semantic_enabled(context) and not is_declared(context, tokens[i]):
            set_error(errors, i, f"Variable '{tokens[i]}' not declared", tokens)
            return -1, None
        return i + 1, make_identifier(tokens[i])

    if is_number(tokens[i]):
        return i + 1, make_number(tokens[i])

    if tokens[i] == "(":
        i, expr = parse_expr(tokens, i + 1, errors, context)
        if i == -1:
            return -1, None
        if i >= len(tokens) or tokens[i] != ")":
            set_error(errors, i, "Missing ')'", tokens)
            return -1, None
        return i + 1, expr

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
    i, assignment = parse_assignment_core(tokens, i, errors, context)
    if i == -1:
        return -1, None

    if i >= len(tokens) or tokens[i] != ";":
        set_error(errors, i, "Expected ';'", tokens)
        return -1, None

    return i + 1, assignment


def parse_assignment_core(tokens, i, errors=None, context=None):
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

    return i, assignment


def parse_increment(tokens, i, errors=None, context=None):
    i, increment = parse_increment_core(tokens, i, errors, context)
    if i == -1:
        return -1, None

    if i >= len(tokens) or tokens[i] != ";":
        set_error(errors, i, "Expected ';'", tokens)
        return -1, None

    return i + 1, increment


def parse_increment_core(tokens, i, errors=None, context=None):
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

    return i, increment


def parse_argument_list(tokens, i, errors=None, context=None):
    args = []

    if i < len(tokens) and tokens[i] == ")":
        return i, args

    while True:
        i, expr = parse_expr(tokens, i, errors, context)
        if i == -1:
            return -1, None
        args.append(expr)

        if i >= len(tokens) or tokens[i] != ",":
            break
        i += 1

    return i, args


def parse_call_expression(tokens, i, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens) or not is_variable(tokens[i]):
        set_error(errors, i, "Expected function name", tokens)
        return -1, None

    call = Node("CALL", tokens[i])
    i += 1

    if i >= len(tokens) or tokens[i] != "(":
        set_error(errors, i, "Missing '(' after function name", tokens)
        return -1, None
    i += 1

    i, args = parse_argument_list(tokens, i, errors, context)
    if i == -1:
        return -1, None

    if i >= len(tokens) or tokens[i] != ")":
        set_error(errors, i, "Missing ')' in function call", tokens)
        return -1, None

    for arg in args:
        call.add(arg)

    return i + 1, call


def parse_call_statement(tokens, i, errors=None, context=None):
    i, call = parse_call_expression(tokens, i, errors, context)
    if i == -1:
        return -1, None

    if i >= len(tokens) or tokens[i] != ";":
        set_error(errors, i, "Expected ';'", tokens)
        return -1, None

    call_stmt = Node("CALL_STMT", call.value)
    for arg in call.children:
        call_stmt.add(arg)
    return i + 1, call_stmt


def parse_return(tokens, i, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens) or tokens[i] != "return":
        set_error(errors, i, "Expected 'return'", tokens)
        return -1, None
    i += 1

    i, expr = parse_expr(tokens, i, errors, context)
    if i == -1:
        return -1, None

    if i >= len(tokens) or tokens[i] != ";":
        set_error(errors, i, "Expected ';'", tokens)
        return -1, None

    node = Node("RETURN")
    node.add(expr)
    return i + 1, node


def parse_break(tokens, i, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens) or tokens[i] != "break":
        set_error(errors, i, "Expected 'break'", tokens)
        return -1, None
    i += 1

    if i >= len(tokens) or tokens[i] != ";":
        set_error(errors, i, "Expected ';'", tokens)
        return -1, None

    return i + 1, Node("BREAK")


def parse_continue(tokens, i, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens) or tokens[i] != "continue":
        set_error(errors, i, "Expected 'continue'", tokens)
        return -1, None
    i += 1

    if i >= len(tokens) or tokens[i] != ";":
        set_error(errors, i, "Expected ';'", tokens)
        return -1, None

    return i + 1, Node("CONTINUE")


def parse_for(tokens, i=0, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens) or tokens[i] != "for":
        set_error(errors, i, "Expected 'for'", tokens)
        return -1, None
    i += 1

    if i >= len(tokens) or tokens[i] != "(":
        set_error(errors, i, "Missing '(' after for", tokens)
        return -1, None
    i += 1

    for_node = Node("FOR")

    if i < len(tokens) and tokens[i] != ";":
        init_i, init_node = parse_assignment_core(tokens, i, errors, context)
        if init_i == -1:
            return -1, None
        for_node.add(init_node)
        i = init_i

    if i >= len(tokens) or tokens[i] != ";":
        set_error(errors, i, "Expected ';' after for initializer", tokens)
        return -1, None
    i += 1

    if i < len(tokens) and tokens[i] != ";":
        i, condition = parse_condition(tokens, i, errors, context)
        if i == -1:
            return -1, None
        for_node.add(condition)

    if i >= len(tokens) or tokens[i] != ";":
        set_error(errors, i, "Expected ';' after for condition", tokens)
        return -1, None
    i += 1

    if i < len(tokens) and tokens[i] != ")":
        update_i, update_node = parse_increment_core(tokens, i, errors, context)
        if update_i == -1:
            update_i, update_node = parse_assignment_core(tokens, i, errors, context)
        if update_i == -1:
            set_error(errors, i, "Expected for update expression", tokens)
            return -1, None
        for_node.add(update_node)
        i = update_i

    if i >= len(tokens) or tokens[i] != ")":
        set_error(errors, i, "Missing ')' after for", tokens)
        return -1, None
    i += 1

    i, body = parse_statement(tokens, i, errors, context)
    if i == -1:
        return -1, None
    for_node.add(body)
    return i, for_node


def parse_block(tokens, i, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens) or tokens[i] != "{":
        set_error(errors, i, "Missing '{'", tokens)
        return -1, None

    block = Node("BLOCK")
    i += 1

    while i < len(tokens) and tokens[i] != "}":
        next_i, statement = parse_statement(tokens, i, errors, context)
        if next_i == -1:
            recovery_index = recover_statement(tokens, errors, i, {"}"})
            if recovery_index >= len(tokens):
                break
            if tokens[recovery_index] == ";":
                i = recovery_index + 1
                continue
            if tokens[recovery_index] == "}":
                i = recovery_index
                break
            i = max(recovery_index, i + 1)
            continue
        i = next_i
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
    if semantic_enabled(context) and is_declared_in_current_scope(context, tokens[i]):
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

    if tokens[i] == "for":
        return parse_for(tokens, i, errors, context)

    if tokens[i] == "return":
        return parse_return(tokens, i, errors, context)

    if tokens[i] == "break":
        return parse_break(tokens, i, errors, context)

    if tokens[i] == "continue":
        return parse_continue(tokens, i, errors, context)

    if tokens[i] == "{":
        return parse_block(tokens, i, errors, context)

    if i + 1 < len(tokens) and tokens[i + 1] == "=":
        return parse_assignment(tokens, i, errors, context)

    if i + 1 < len(tokens) and tokens[i + 1] == "++":
        return parse_increment(tokens, i, errors, context)

    if i + 1 < len(tokens) and tokens[i + 1] == "(":
        return parse_call_statement(tokens, i, errors, context)

    set_error(errors, i, "Unexpected token", tokens)
    return -1, None


def parse(tokens, errors=None, context=None):
    initialize_context(context)

    if not tokens:
        set_error(errors, 0, "Empty input", tokens)
        return False

    i = 0
    while i < len(tokens):
        next_i, _ = parse_statement(tokens, i, errors, context)
        if next_i == -1:
            i = recover_to_sync(tokens, get_last_error_index(errors, i))
            continue
        i = next_i

    return not has_recorded_errors(errors)


def parse_parameter_list(tokens, i, errors=None, context=None):
    initialize_context(context)

    params = []
    if i < len(tokens) and tokens[i] == ")":
        return i, params

    while True:
        if i >= len(tokens) or tokens[i] not in DECLARATION_TYPES:
            set_error(errors, i, "Expected parameter type", tokens)
            return -1, None
        param_type = tokens[i]
        i += 1

        if i >= len(tokens) or not is_variable(tokens[i]):
            set_error(errors, i, "Expected parameter name", tokens)
            return -1, None
        if semantic_enabled(context) and is_declared_in_current_scope(context, tokens[i]):
            set_error(errors, i, f"Variable '{tokens[i]}' already declared", tokens)
            return -1, None

        param_name = tokens[i]
        i += 1

        declare_variable(context, param_name, param_type)
        param = Node("PARAM", param_type)
        param.add(make_type(param_type))
        param.add(make_identifier(param_name))
        params.append(param)

        if i >= len(tokens) or tokens[i] != ",":
            break
        i += 1

    return i, params


def parse_function_definition(tokens, i, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens) or tokens[i] not in DECLARATION_TYPES:
        set_error(errors, i, "Expected function return type", tokens)
        return -1, None
    return_type = tokens[i]
    i += 1

    if i >= len(tokens) or not is_function_name(tokens[i]):
        set_error(errors, i, "Expected function name", tokens)
        return -1, None
    function_name = tokens[i]
    i += 1

    if i >= len(tokens) or tokens[i] != "(":
        set_error(errors, i, "Missing '(' after function name", tokens)
        return -1, None
    i += 1

    push_scope(context)
    i, params = parse_parameter_list(tokens, i, errors, context)
    if i == -1:
        pop_scope(context)
        return -1, None

    if i >= len(tokens) or tokens[i] != ")":
        set_error(errors, i, "Missing ')'", tokens)
        pop_scope(context)
        return -1, None
    i += 1

    i, block = parse_block(tokens, i, errors, context)
    if i == -1:
        pop_scope(context)
        return -1, None

    function_node = Node("FUNCTION", function_name)
    function_node.add(make_type(return_type))
    for param in params:
        function_node.add(param)
    function_node.add(block)
    pop_scope(context)
    return i, function_node


def parse_main(tokens, i, errors=None, context=None):
    i, function_node = parse_function_definition(tokens, i, errors, context)
    if i == -1:
        return -1, None

    if function_node.value != "main":
        set_error(errors, i, "Expected 'main'", tokens)
        return -1, None

    main_node = Node("MAIN")
    main_node.add(function_node.children[-1])
    return i, main_node


def parse_program(tokens, errors=None, context=None):
    initialize_context(context)

    if not tokens:
        set_error(errors, 0, "Empty input", tokens)
        return None

    program = Node("PROGRAM")
    i = 0

    while i < len(tokens):
        if (
            i + 2 < len(tokens)
            and tokens[i] in DECLARATION_TYPES
            and is_function_name(tokens[i + 1])
            and tokens[i + 2] == "("
        ):
            next_i, function_node = parse_function_definition(tokens, i, errors, context)
            if next_i == -1:
                i = recover_to_sync(tokens, get_last_error_index(errors, i))
                continue
            program.add(function_node)
            i = next_i
            continue

        next_i, statement = parse_statement(tokens, i, errors, context)
        if next_i == -1:
            i = recover_to_sync(tokens, get_last_error_index(errors, i))
            continue
        program.add(statement)
        i = next_i

    if i != len(tokens):
        set_error(errors, i, "Unexpected token after program end", tokens)
        return None

    if has_recorded_errors(errors):
        return None

    if context is not None:
        context["intermediate_code"] = generate_statement_code(program, context)

    return program
