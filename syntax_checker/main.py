from pathlib import Path

from parser import parse_program
from tokenizer import tokenize


def main():
    program_path = Path(__file__).with_name("test_program.txt")

    with program_path.open() as file:
        code = file.read()

    tokens = tokenize(code)
    errors = {}
    context = {"symbol_table": {}}
    tree = parse_program(tokens, errors, context)

    if tree is None:
        error_index = errors.get("index", 0)
        token = errors.get("token", "<eof>")
        message = errors.get("message", "Invalid program")
        print(f"Error at token {error_index + 1} ('{token}'): {message}")
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
