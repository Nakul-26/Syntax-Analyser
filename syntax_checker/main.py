from pathlib import Path

try:
    from .parser import format_error, parse_program
    from .tokenizer import tokenize_with_lines
except ImportError:
    from parser import format_error, parse_program
    from tokenizer import tokenize_with_lines


def format_symbol_table(symbol_table):
    symbols = []
    for name, entry in symbol_table.items():
        if isinstance(entry, dict):
            var_type = entry["type"]
            kind = "array" if entry.get("is_array") else "variable"
            size = entry.get("size")
            display_type = f"{var_type}[{size}]" if entry.get("is_array") else var_type
        else:
            var_type = entry
            kind = "variable"
            size = None
            display_type = var_type

        symbol = {
            "name": name,
            "type": var_type,
            "display_type": display_type,
            "kind": kind,
        }
        if size is not None:
            symbol["size"] = size
        symbols.append(symbol)
    return symbols


def analyze_code(code):
    tokens, line_numbers = tokenize_with_lines(code)
    errors = {"line_numbers": line_numbers}
    context = {"symbol_table": {}}
    tree = parse_program(tokens, errors, context)

    error_items = errors.get("items", [])
    formatted_errors = [format_error(item) for item in error_items]
    ast_lines = tree.to_lines() if tree is not None else []
    ast_tree_lines = tree.to_tree_lines() if tree is not None else []
    ast_level_lines = tree.to_level_lines() if tree is not None else []

    return {
        "syntax_valid": tree is not None and not error_items,
        "errors": formatted_errors,
        "error_details": error_items,
        "ast": ast_lines,
        "ast_text": "\n".join(ast_lines),
        "ast_tree": ast_tree_lines,
        "ast_tree_text": "\n".join(ast_tree_lines),
        "ast_levels": ast_level_lines,
        "ast_levels_text": "\n".join(ast_level_lines),
        "symbol_table": format_symbol_table(context.get("symbol_table", {})),
        "tac": context.get("intermediate_code", []),
        "tokens": tokens,
    }


def main():
    program_path = Path(__file__).with_name("test_program.txt")

    with program_path.open() as file:
        code = file.read()

    result = analyze_code(code)

    if not result["syntax_valid"]:
        for error in result["errors"]:
            print(error)
        print("Parsing completed with recovery")
        return

    print("Syntax Valid")
    print("Semantic Valid")
    print("Type Safe")

    print("\nSymbol Table:")
    for symbol in result["symbol_table"]:
        print(f"{symbol['name']}\t{symbol['display_type']}")

    print("\nIntermediate Code:")
    for line in result["tac"]:
        print(line)

    print("\nAST Level-wise:")
    print(result["ast_levels_text"])

    print("\nAST Tree:")
    print(result["ast_tree_text"])


if __name__ == "__main__":
    main()
