"""
This file parses the code for the language used in the project.
It builds the tree, checks simple rules, and makes intermediate code.
"""

import re
from collections import deque


# Tree nodes are used to build the AST.
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

    def to_tree_lines(self, indent=0, step=4):
        lines = [" " * indent + self.label()]
        for child in self.children:
            lines.extend(child.to_tree_lines(indent + step, step))
        return lines

    def to_level_lines(self):
        lines = []
        queue = deque([(self, 0)])
        current_level = None
        current_labels = []

        while queue:
            node, level = queue.popleft()

            if current_level is None:
                current_level = level
            elif level != current_level:
                lines.append(f"Level {current_level}: {'  '.join(current_labels)}")
                current_level = level
                current_labels = []

            current_labels.append(node.label())

            for child in node.children:
                queue.append((child, level + 1))

        if current_level is not None:
            lines.append(f"Level {current_level}: {'  '.join(current_labels)}")

        return lines


# Basic language settings and small helper values.
DECLARATION_TYPES = {"int", "float", "char"}
KEYWORDS = {
    "if",
    "else",
    "while",
    "for",
    "do",
    "switch",
    "case",
    "default",
    "return",
    "break",
    "continue",
    "int",
    "float",
    "char",
    "main",
}
SYNC_TOKENS = {";", "{", "}", ")"}
DEBUG = False
IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


# Simple helper checks for tokens and values.
def debug_log(*parts):
    if DEBUG:
        print(*parts)


def is_identifier(token):
    return bool(token) and token not in KEYWORDS and IDENTIFIER_PATTERN.match(token) is not None


def is_variable(token):
    return is_identifier(token)


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


def make_array_size(value):
    return Node("SIZE", value)


def make_empty_statement():
    return Node("EMPTY")


# Context helpers keep track of scope and semantic state.
def semantic_enabled(context):
    return context is not None and "symbol_table" in context


def initialize_context(context):
    if context is None:
        return None

    context.setdefault("symbol_table", {})
    context.setdefault("scopes", [context["symbol_table"]])
    context.setdefault("intermediate_code", [])
    context.setdefault("temp_count", 1)
    context.setdefault("loop_depth", 0)
    context.setdefault("switch_depth", 0)
    return context


def make_symbol_entry(var_type, is_array=False, array_size=None):
    return {
        "type": var_type,
        "is_array": is_array,
        "size": array_size,
    }


def declare_variable(context, name, var_type, is_array=False, array_size=None):
    if context is None:
        return

    entry = make_symbol_entry(var_type, is_array=is_array, array_size=array_size)
    current_scope(context)[name] = entry
    context["symbol_table"][name] = entry


def is_declared(context, name):
    return lookup_variable_entry(context, name) is not None


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


def enter_loop(context):
    if context is None:
        return
    initialize_context(context)
    context["loop_depth"] += 1


def exit_loop(context):
    if context is None:
        return
    initialize_context(context)
    if context["loop_depth"] > 0:
        context["loop_depth"] -= 1


def is_inside_loop(context):
    if context is None:
        return False
    initialize_context(context)
    return context["loop_depth"] > 0


def enter_switch(context):
    if context is None:
        return
    initialize_context(context)
    context["switch_depth"] += 1


def exit_switch(context):
    if context is None:
        return
    initialize_context(context)
    if context["switch_depth"] > 0:
        context["switch_depth"] -= 1


def is_inside_switch(context):
    if context is None:
        return False
    initialize_context(context)
    return context["switch_depth"] > 0


def is_inside_breakable(context):
    return is_inside_loop(context) or is_inside_switch(context)


# Type helpers and symbol lookup functions.
def lookup_variable_type(context, name):
    entry = lookup_variable_entry(context, name)
    if entry is None:
        return None
    return entry["type"]


def lookup_variable_entry(context, name):
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


def is_array_variable(context, name):
    entry = lookup_variable_entry(context, name)
    return entry is not None and entry.get("is_array", False)


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


# Read the AST and guess the type of an expression.
def infer_node_type(node, context):
    if node.type == "IDENT":
        return lookup_variable_type(context, node.value)

    if node.type == "ARRAY_ACCESS":
        return lookup_variable_type(context, node.value)

    if node.type == "NUMBER":
        return "float" if is_float(node.value) else "int"

    if node.type == "CALL":
        return "int"

    if node.type in ["+", "-", "*", "/", "%"]:
        left_type = infer_node_type(node.children[0], context)
        right_type = infer_node_type(node.children[1], context)
        if left_type is None or right_type is None:
            return None
        if node.type == "/":
            return "float" if "float" in [left_type, right_type] else "int"
        return combine_types(left_type, right_type)

    if node.type in ["UNARY+", "UNARY-", "NOT"]:
        child_type = infer_node_type(node.children[0], context)
        if child_type is None:
            return None
        if node.type == "NOT":
            return "int"
        return child_type

    if node.type in ["INCREMENT", "DECREMENT"]:
        # child is IDENT
        if not node.children:
            return None
        child = node.children[0]
        if child.type == "IDENT":
            return lookup_variable_type(context, child.value)
        return None

    return None


def new_temp(context):
    temp = f"t{context['temp_count']}"
    context["temp_count"] += 1
    return temp


# Build three-address style code for expressions and statements.
def generate_expr_code(node, context):
    if node.type in ["IDENT", "NUMBER"]:
        return [], node.value

    if node.type == "ARRAY_ACCESS":
        index_code, index_name = generate_expr_code(node.children[0], context)
        temp = new_temp(context)
        return index_code + [f"{temp} = {node.value}[{index_name}]"], temp

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

    # unary increment/decrement used as expression
    if node.type in ["INCREMENT", "DECREMENT"]:
        target_node = node.children[0]
        target = target_node.value if target_node.type == "IDENT" else None
        if target is None:
            return [], None
        op_char = "+" if node.type == "INCREMENT" else "-"
        if node.value == "postfix":
            temp = new_temp(context)
            return [f"{temp} = {target}", f"{target} = {target} {op_char} 1"], temp
        # prefix
        temp = new_temp(context)
        return [f"{target} = {target} {op_char} 1", f"{temp} = {target}"], temp

    if node.type in ["UNARY+", "UNARY-", "NOT"]:
        child_code, child_name = generate_expr_code(node.children[0], context)
        temp = new_temp(context)
        if node.type == "UNARY-":
            op = "-"
        elif node.type == "UNARY+":
            op = "+"
        else:
            op = "!"
        return child_code + [f"{temp} = {op}{child_name}"], temp

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

    if node.type == "FUNCTION_PROTO":
        return []

    if node.type in ["MAIN", "BLOCK", "ELSE", "DECL_GROUP"]:
        code = []
        for child in node.children:
            code.extend(generate_statement_code(child, context))
        return code

    if node.type == "EMPTY":
        return []

    if node.type == "DECL":
        if len(node.children) >= 3 and node.children[-1].type == "INIT":
            expr_code, result_name = generate_expr_code(node.children[-1].children[0], context)
            target = node.children[1].value
            return expr_code + [f"{target} = {result_name}"]
        return []

    if node.type == "ASSIGN":
        expr_code, result_name = generate_expr_code(node.children[1], context)
        target_node = node.children[0]
        op = node.value if node.value is not None else "="
        # handle array targets
        if target_node.type == "ARRAY_ACCESS":
            index_code, index_name = generate_expr_code(target_node.children[0], context)
            if op == "=":
                return index_code + expr_code + [f"{target_node.value}[{index_name}] = {result_name}"]
            base_op = op[0]
            temp = new_temp(context)
            return index_code + expr_code + [f"{temp} = {target_node.value}[{index_name}] {base_op} {result_name}", f"{target_node.value}[{index_name}] = {temp}"]
        # non-array targets
        if op == "=":
            return expr_code + [f"{target_node.value} = {result_name}"]
        base_op = op[0]
        return expr_code + [f"{target_node.value} = {target_node.value} {base_op} {result_name}"]

    if node.type == "INCREMENT":
        target = node.children[0].value
        temp = new_temp(context)
        return [f"{temp} = {target} + 1", f"{target} = {temp}"]

    if node.type == "DECREMENT":
        target = node.children[0].value
        temp = new_temp(context)
        return [f"{temp} = {target} - 1", f"{target} = {temp}"]

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

    if node.type == "DO_WHILE":
        return generate_statement_code(node.children[0], context)

    if node.type == "FOR":
        code = []
        for child in node.children:
            code.extend(generate_statement_code(child, context))
        return code

    if node.type in ["SWITCH", "CASE", "DEFAULT"]:
        code = []
        start_index = 1 if node.type == "SWITCH" else 0
        for child in node.children[start_index:]:
            code.extend(generate_statement_code(child, context))
        return code

    return []


# Save parse errors in a simple format.
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


def format_error(item):
    line = item.get("line")
    message = item.get("message", "Invalid program")
    token = item.get("token", "<eof>")
    prefix = f"Line {line}" if line is not None else f"Token {item.get('index', 0) + 1}"
    if token == "<eof>":
        return f"{prefix}: {message}"
    return f"{prefix}: {message} near '{token}'"


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


# Skip tokens until the parser can safely continue.
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


# Parse conditions with the same order used by the language.
def parse_condition(tokens, i, errors=None, context=None):
    return parse_logical_or(tokens, i, errors, context)


def parse_logical_or(tokens, i, errors=None, context=None):
    i, node = parse_logical_and(tokens, i, errors, context)
    if i == -1:
        return -1, None

    while i < len(tokens) and tokens[i] == "||":
        op = tokens[i]
        i += 1
        i, right = parse_logical_and(tokens, i, errors, context)
        if i == -1:
            return -1, None
        logical = Node("LOGICAL_OP", op)
        logical.add(node)
        logical.add(right)
        node = logical

    return i, node


def parse_logical_and(tokens, i, errors=None, context=None):
    i, node = parse_relation(tokens, i, errors, context)
    if i == -1:
        return -1, None

    while i < len(tokens) and tokens[i] == "&&":
        op = tokens[i]
        i += 1
        i, right = parse_relation(tokens, i, errors, context)
        if i == -1:
            return -1, None
        logical = Node("LOGICAL_OP", op)
        logical.add(node)
        logical.add(right)
        node = logical

    return i, node


def parse_relation(tokens, i, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens):
        set_error(errors, i, "Expected condition", tokens)
        return -1, None

    probe_i, left = parse_expr(tokens, i, None, context)
    if probe_i != -1 and probe_i < len(tokens) and is_relop(tokens[probe_i]):
        i = probe_i
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

    if tokens[i] == "(":
        i += 1
        i, node = parse_condition(tokens, i, errors, context)
        if i == -1:
            return -1, None
        if i >= len(tokens) or tokens[i] != ")":
            set_error(errors, i, "Missing ')'", tokens)
            return -1, None
        return i + 1, node

    if probe_i == -1:
        parse_expr(tokens, i, errors, context)
        return -1, None

    if left.type == "NOT":
        return probe_i, left

    set_error(errors, i, "Expected relational operator", tokens)
    return -1, None


# Parse an array name followed by an index.
def parse_array_access(tokens, i, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens) or not is_variable(tokens[i]):
        set_error(errors, i, "Expected array name", tokens)
        return -1, None

    name = tokens[i]
    if semantic_enabled(context):
        if not is_declared(context, name):
            set_error(errors, i, f"Variable '{name}' not declared", tokens)
            return -1, None
        if not is_array_variable(context, name):
            set_error(errors, i, f"Variable '{name}' is not an array", tokens)
            return -1, None
    i += 1

    if i >= len(tokens) or tokens[i] != "[":
        set_error(errors, i, "Missing '[' in array access", tokens)
        return -1, None
    i += 1

    i, index_expr = parse_expr(tokens, i, errors, context)
    if i == -1:
        return -1, None

    if semantic_enabled(context):
        index_type = infer_node_type(index_expr, context)
        if index_type not in ["int", "char"]:
            set_error(errors, i, "Array index must be an integer expression", tokens)
            return -1, None

    if i >= len(tokens) or tokens[i] != "]":
        set_error(errors, i, "Missing ']'", tokens)
        return -1, None

    node = Node("ARRAY_ACCESS", name)
    node.add(index_expr)
    return i + 1, node


# Parse the smallest parts of an expression.
def parse_factor(tokens, i, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens):
        set_error(errors, i, "Expected operand", tokens)
        return -1, None
    # unary prefix: +, -, !, ++, --
    if tokens[i] in ["+", "-", "!"]:
        op = tokens[i]
        i += 1
        i, node = parse_factor(tokens, i, errors, context)
        if i == -1:
            return -1, None
        if op == "+":
            unary = Node("UNARY+")
        elif op == "-":
            unary = Node("UNARY-")
        else:
            unary = Node("NOT")
        unary.add(node)
        return i, unary

    if tokens[i] in ["++", "--"]:
        op = tokens[i]
        i += 1
        if i >= len(tokens) or not is_variable(tokens[i]):
            set_error(errors, i, "Expected increment target", tokens)
            return -1, None
        if semantic_enabled(context) and not is_declared(context, tokens[i]):
            set_error(errors, i, f"Variable '{tokens[i]}' not declared", tokens)
            return -1, None
        node = Node("INCREMENT" if op == "++" else "DECREMENT", "prefix")
        node.add(make_identifier(tokens[i]))
        return i + 1, node

    # identifier, call, or array access (may be postfix ++/--)
    if is_variable(tokens[i]):
        if i + 1 < len(tokens) and tokens[i + 1] == "(":
            return parse_call_expression(tokens, i, errors, context)
        if i + 1 < len(tokens) and tokens[i + 1] == "[":
            return parse_array_access(tokens, i, errors, context)
        if semantic_enabled(context) and not is_declared(context, tokens[i]):
            set_error(errors, i, f"Variable '{tokens[i]}' not declared", tokens)
            return -1, None
        if semantic_enabled(context) and is_array_variable(context, tokens[i]):
            set_error(errors, i, f"Array '{tokens[i]}' requires an index", tokens)
            return -1, None

        ident = make_identifier(tokens[i])
        i += 1
        if i < len(tokens) and tokens[i] in ["++", "--"]:
            op = tokens[i]
            node = Node("INCREMENT" if op == "++" else "DECREMENT", "postfix")
            node.add(ident)
            return i + 1, node
        return i, ident

    # number literal
    if is_number(tokens[i]):
        return i + 1, make_number(tokens[i])

    # string or char literal
    if tokens[i].startswith('"') or tokens[i].startswith("'"):
        lit_type = "STRING" if tokens[i].startswith('"') else "CHAR"
        node = Node(lit_type, tokens[i])
        return i + 1, node

    # parenthesized expression
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


# Parse multiply, divide, and remainder operations.
def parse_term(tokens, i, errors=None, context=None):
    initialize_context(context)
    i, node = parse_factor(tokens, i, errors, context)
    if i == -1:
        return -1, None

    while i < len(tokens) and tokens[i] in ["*", "/", "%"]:
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


# Parse expression values and operators from left to right.
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


# Parse assignment statements and keep their simple form.
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

    assignment = Node("ASSIGN")
    target_name = tokens[i]
    if i + 1 < len(tokens) and tokens[i + 1] == "[":
        i, target = parse_array_access(tokens, i, errors, context)
        if i == -1:
            return -1, None
    else:
        if semantic_enabled(context) and not is_declared(context, target_name):
            set_error(errors, i, f"Variable '{target_name}' not declared", tokens)
            return -1, None
        if semantic_enabled(context) and is_array_variable(context, target_name):
            set_error(errors, i, f"Array '{target_name}' requires an index", tokens)
            return -1, None
        target = make_identifier(target_name)
        i += 1
    assignment.add(target)

    # accept '=' and compound assignments like '+=', '-=', '*=', '/=', '%='
    if i >= len(tokens) or tokens[i] not in ["=", "+=", "-=", "*=", "/=", "%="]:
        set_error(errors, i, "Expected assignment operator", tokens)
        return -1, None
    op = tokens[i]
    assignment.value = op
    i += 1

    i, expr = parse_expr(tokens, i, errors, context)
    if i == -1:
        return -1, None
    assignment.add(expr)

    if semantic_enabled(context):
        target_type = lookup_variable_type(context, target_name)
        expr_type = infer_node_type(expr, context)
        if expr_type is None:
            set_error(errors, i, "Unable to infer expression type", tokens)
            return -1, None
        # for compound assignments, result type is combination of target and expr
        if assignment.value != "=":
            combined = combine_types(target_type, expr_type)
            if not is_assignment_compatible(target_type, combined):
                set_error(errors, i, f"Type mismatch: cannot assign {combined} to {target_type}", tokens)
                return -1, None
        else:
            if not is_assignment_compatible(target_type, expr_type):
                set_error(errors, i, f"Type mismatch: cannot assign {expr_type} to {target_type}", tokens)
                return -1, None

    return i, assignment


# Parse prefix and postfix increment or decrement.
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
    # support prefix (++i / --i)
    if i < len(tokens) and tokens[i] in ["++", "--"]:
        op = tokens[i]
        i += 1
        if i >= len(tokens) or not is_variable(tokens[i]):
            set_error(errors, i, "Expected increment target", tokens)
            return -1, None
        if semantic_enabled(context) and not is_declared(context, tokens[i]):
            set_error(errors, i, f"Variable '{tokens[i]}' not declared", tokens)
            return -1, None
        node = Node("INCREMENT" if op == "++" else "DECREMENT", "prefix")
        node.add(make_identifier(tokens[i]))
        return i + 1, node

    # postfix (i++ / i--)
    if i >= len(tokens) or not is_variable(tokens[i]):
        set_error(errors, i, "Expected increment target", tokens)
        return -1, None
    if semantic_enabled(context) and not is_declared(context, tokens[i]):
        set_error(errors, i, f"Variable '{tokens[i]}' not declared", tokens)
        return -1, None
    node = Node("INCREMENT")
    node.add(make_identifier(tokens[i]))
    i += 1
    if i >= len(tokens) or tokens[i] not in ["++", "--"]:
        set_error(errors, i, "Expected '++' or '--'", tokens)
        return -1, None
    op = tokens[i]
    node.type = "INCREMENT" if op == "++" else "DECREMENT"
    node.value = "postfix"
    i += 1
    return i, node


# Parse the values inside a function call.
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


# Parse a function call used inside an expression.
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


# Parse function calls used as standalone statements.
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


# Parse a return statement.
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


# Parse a break statement and check where it can be used.
def parse_break(tokens, i, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens) or tokens[i] != "break":
        set_error(errors, i, "Expected 'break'", tokens)
        return -1, None
    if semantic_enabled(context) and not is_inside_breakable(context):
        set_error(errors, i, "'break' is only allowed inside a loop or switch", tokens)
        return -1, None
    i += 1

    if i >= len(tokens) or tokens[i] != ";":
        set_error(errors, i, "Expected ';'", tokens)
        return -1, None

    return i + 1, Node("BREAK")


# Parse a continue statement and check where it can be used.
def parse_continue(tokens, i, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens) or tokens[i] != "continue":
        set_error(errors, i, "Expected 'continue'", tokens)
        return -1, None
    if semantic_enabled(context) and not is_inside_loop(context):
        set_error(errors, i, "'continue' is only allowed inside a loop", tokens)
        return -1, None
    i += 1

    if i >= len(tokens) or tokens[i] != ";":
        set_error(errors, i, "Expected ';'", tokens)
        return -1, None

    return i + 1, Node("CONTINUE")


# Parse a do-while loop.
def parse_do_while(tokens, i, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens) or tokens[i] != "do":
        set_error(errors, i, "Expected 'do'", tokens)
        return -1, None
    i += 1

    enter_loop(context)
    try:
        i, body = parse_statement(tokens, i, errors, context)
        if i == -1:
            return -1, None
    finally:
        exit_loop(context)

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
        set_error(errors, i, "Expected ')' after do-while condition", tokens)
        return -1, None
    i += 1

    if i >= len(tokens) or tokens[i] != ";":
        set_error(errors, i, "Expected ';'", tokens)
        return -1, None

    node = Node("DO_WHILE")
    node.add(body)
    node.add(condition)
    return i + 1, node


# Parse one statement, then keep going until a stop token.
def parse_statement_list(tokens, i, errors=None, context=None, stop_tokens=None):
    initialize_context(context)
    stop_tokens = {"}"} if stop_tokens is None else set(stop_tokens)

    statements = []
    while i < len(tokens) and tokens[i] not in stop_tokens:
        next_i, statement = parse_statement(tokens, i, errors, context)
        if next_i == -1:
            recovery_index = recover_statement(tokens, errors, i, stop_tokens)
            if recovery_index >= len(tokens):
                return len(tokens), statements
            if tokens[recovery_index] == ";":
                i = recovery_index + 1
                continue
            if tokens[recovery_index] in stop_tokens:
                return recovery_index, statements
            i = max(recovery_index, i + 1)
            continue
        i = next_i
        statements.append(statement)

    return i, statements


def parse_case_list(tokens, i, errors=None, context=None):
    initialize_context(context)

    cases = []
    seen_default = False

    while i < len(tokens) and tokens[i] != "}":
        if tokens[i] == "case":
            if seen_default:
                set_error(errors, i, "No case labels allowed after default", tokens)
                return -1, None

            case_node = Node("CASE")
            i += 1

            if i >= len(tokens) or not is_int(tokens[i]):
                set_error(errors, i, "Expected number after case", tokens)
                return -1, None
            case_node.add(make_number(tokens[i]))
            i += 1

            if i >= len(tokens) or tokens[i] != ":":
                set_error(errors, i, "Expected ':' after case value", tokens)
                return -1, None
            i += 1

            i, statements = parse_statement_list(tokens, i, errors, context, {"case", "default", "}"})
            if i == -1:
                return -1, None
            for statement in statements:
                case_node.add(statement)
            cases.append(case_node)
            continue

        if tokens[i] == "default":
            if seen_default:
                set_error(errors, i, "Duplicate default label", tokens)
                return -1, None

            default_node = Node("DEFAULT")
            seen_default = True
            i += 1

            if i >= len(tokens) or tokens[i] != ":":
                set_error(errors, i, "Expected ':' after default", tokens)
                return -1, None
            i += 1

            i, statements = parse_statement_list(tokens, i, errors, context, {"case", "default", "}"})
            if i == -1:
                return -1, None
            for statement in statements:
                default_node.add(statement)
            cases.append(default_node)
            continue

        set_error(errors, i, "Expected 'case', 'default', or '}'", tokens)
        return -1, None

    return i, cases


# Parse a switch block and its case labels.
def parse_switch(tokens, i, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens) or tokens[i] != "switch":
        set_error(errors, i, "Expected 'switch'", tokens)
        return -1, None
    i += 1

    if i >= len(tokens) or tokens[i] != "(":
        set_error(errors, i, "Missing '(' after switch", tokens)
        return -1, None
    i += 1

    i, expr = parse_expr(tokens, i, errors, context)
    if i == -1:
        return -1, None

    if i >= len(tokens) or tokens[i] != ")":
        set_error(errors, i, "Expected ')' after switch expression", tokens)
        return -1, None
    i += 1

    if i >= len(tokens) or tokens[i] != "{":
        set_error(errors, i, "Missing '{' after switch", tokens)
        return -1, None
    i += 1

    switch_node = Node("SWITCH")
    switch_node.add(expr)

    enter_switch(context)
    try:
        i, cases = parse_case_list(tokens, i, errors, context)
        if i == -1:
            return -1, None
    finally:
        exit_switch(context)

    for case in cases:
        switch_node.add(case)

    if i >= len(tokens) or tokens[i] != "}":
        set_error(errors, i, "Missing '}' after switch", tokens)
        return -1, None

    return i + 1, switch_node


# Parse a for loop with init, condition, update, and body.
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
        if tokens[i] in DECLARATION_TYPES:
            init_i, init_node = parse_declaration_core(tokens, i, errors, context)
        else:
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

    enter_loop(context)
    try:
        i, body = parse_statement(tokens, i, errors, context)
        if i == -1:
            return -1, None
    finally:
        exit_loop(context)
    for_node.add(body)
    return i, for_node


# Parse a block wrapped in braces.
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


# Parse an if statement and its optional else part.
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
        set_error(errors, i, "Expected ')' after if condition", tokens)
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


# Parse a while loop.
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
        set_error(errors, i, "Expected ')' after while condition", tokens)
        return -1, None
    i += 1

    while_node = Node("WHILE")
    while_node.add(condition)

    if i >= len(tokens):
        set_error(errors, i, "Expected loop body", tokens)
        return -1, None

    enter_loop(context)
    try:
        if tokens[i] == "{":
            i, body = parse_block(tokens, i, errors, context)
        else:
            i, body = parse_statement(tokens, i, errors, context)
        if i == -1:
            return -1, None
    finally:
        exit_loop(context)

    while_node.add(body)
    return i, while_node


# Parse one or more declarations in a row.
def parse_declaration_core(tokens, i, errors=None, context=None):
    initialize_context(context)

    if i >= len(tokens) or tokens[i] not in DECLARATION_TYPES:
        set_error(errors, i, "Expected type declaration", tokens)
        return -1, None

    var_type = tokens[i]
    i += 1

    declarations = []

    while True:
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

        is_array = False
        array_size = None
        if i < len(tokens) and tokens[i] == "[":
            is_array = True
            i += 1
            if i >= len(tokens) or not is_int(tokens[i]):
                set_error(errors, i, "Array size must be an integer literal", tokens)
                return -1, None
            array_size = tokens[i]
            declaration.add(make_array_size(array_size))
            i += 1
            if i >= len(tokens) or tokens[i] != "]":
                set_error(errors, i, "Missing ']'", tokens)
                return -1, None
            i += 1

        declare_variable(context, name, var_type, is_array=is_array, array_size=array_size)

        if i < len(tokens) and tokens[i] == "=":
            if is_array:
                set_error(errors, i, "Array initialization is not supported", tokens)
                return -1, None
            i += 1
            i, expr = parse_expr(tokens, i, errors, context)
            if i == -1:
                return -1, None

            expr_type = infer_node_type(expr, context)
            if semantic_enabled(context) and expr_type is None:
                set_error(errors, i, "Unable to infer expression type", tokens)
                return -1, None
            if semantic_enabled(context) and not is_assignment_compatible(var_type, expr_type):
                set_error(errors, i, f"Type mismatch: cannot assign {expr_type} to {var_type}", tokens)
                return -1, None

            init_node = Node("INIT")
            init_node.add(expr)
            declaration.add(init_node)

        declarations.append(declaration)

        if i < len(tokens) and tokens[i] == ",":
            i += 1
            continue
        break

    return i, declarations[0] if len(declarations) == 1 else make_declaration_group(declarations)


def make_declaration_group(declarations):
    group = Node("DECL_GROUP")
    for declaration in declarations:
        group.add(declaration)
    return group


def parse_declaration(tokens, i, errors=None, context=None):
    i, declaration = parse_declaration_core(tokens, i, errors, context)
    if i == -1:
        return -1, None

    if i >= len(tokens) or tokens[i] != ";":
        set_error(errors, i, "Expected ';'", tokens)
        return -1, None

    return i + 1, declaration


# Parse one full statement and choose the right handler.
def parse_statement(tokens, i, errors=None, context=None):
    initialize_context(context)
    debug_log("Parsing statement at token", i, tokens[i] if i < len(tokens) else "<eof>")

    if i >= len(tokens):
        set_error(errors, i, "Unexpected end of input", tokens)
        return -1, None

    if tokens[i] == ";":
        return i + 1, make_empty_statement()

    if tokens[i] in DECLARATION_TYPES:
        return parse_declaration(tokens, i, errors, context)

    if tokens[i] == "if":
        return parse_if(tokens, i, errors, context)

    if tokens[i] == "while":
        return parse_while(tokens, i, errors, context)

    if tokens[i] == "for":
        return parse_for(tokens, i, errors, context)

    if tokens[i] == "do":
        return parse_do_while(tokens, i, errors, context)

    if tokens[i] == "switch":
        return parse_switch(tokens, i, errors, context)

    if tokens[i] == "return":
        return parse_return(tokens, i, errors, context)

    if tokens[i] == "break":
        return parse_break(tokens, i, errors, context)

    if tokens[i] == "continue":
        return parse_continue(tokens, i, errors, context)

    if tokens[i] == "{":
        return parse_block(tokens, i, errors, context)

    if i + 1 < len(tokens) and tokens[i + 1] == "[":
        return parse_assignment(tokens, i, errors, context)

    if i + 1 < len(tokens) and tokens[i + 1] in ["=", "+=", "-=", "*=", "/=", "%="]:
        return parse_assignment(tokens, i, errors, context)

    if tokens[i] in ["++", "--"]:
        return parse_increment(tokens, i, errors, context)

    if i + 1 < len(tokens) and tokens[i + 1] in ["++", "--"]:
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


# Parse a function definition or function prototype.
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

    if i < len(tokens) and tokens[i] == ";":
        prototype_node = Node("FUNCTION_PROTO", function_name)
        prototype_node.add(make_type(return_type))
        for param in params:
            prototype_node.add(param)
        pop_scope(context)
        return i + 1, prototype_node

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


# Parse the main function and keep only its body tree.
def parse_main(tokens, i, errors=None, context=None):
    i, function_node = parse_function_definition(tokens, i, errors, context)
    if i == -1:
        return -1, None

    if function_node.value != "main":
        set_error(errors, i, "Expected 'main'", tokens)
        return -1, None
    if function_node.type != "FUNCTION":
        set_error(errors, i, "'main' must be defined with a function body", tokens)
        return -1, None

    main_node = Node("MAIN")
    main_node.add(function_node.children[-1])
    return i, main_node


# Parse the whole token stream into one program tree.
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
