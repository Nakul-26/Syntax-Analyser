from pathlib import Path

from parser import parse_program
from tokenizer import tokenize_with_lines


def main():
    program_path = Path(__file__).with_name("test_program.txt")

    with program_path.open() as file:
        code = file.read()

    tokens, line_numbers = tokenize_with_lines(code)
    errors = {"line_numbers": line_numbers}
    context = {"symbol_table": {}}
    tree = parse_program(tokens, errors, context)

    if tree is None:
        for item in errors.get("items", []):
            line = item.get("line")
            location = f"line {line}" if line is not None else f"token {item.get('index', 0) + 1}"
            print(f"Error at {location} near '{item.get('token', '<eof>')}': {item.get('message', 'Invalid program')}")
        print("Parsing completed with recovery")
        return

    print("Syntax Valid")
    print("Semantic Valid")
    print("Type Safe")

    print("\nSymbol Table:")
    for name, var_type in context["symbol_table"].items():
        print(f"{name}\t{var_type}")

    print("\nIntermediate Code:")
    for line in context["intermediate_code"]:
        print(line)

    print("\nAST:")
    print("\n".join(tree.to_lines()))


if __name__ == "__main__":
    main()
