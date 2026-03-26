from pathlib import Path

from parser import parse_program
from tokenizer import tokenize


def main():
    program_path = Path(__file__).with_name("test_program.txt")

    with program_path.open() as file:
        code = file.read()

    tokens = tokenize(code)
    errors = {}
    tree = parse_program(tokens, errors)

    if tree is None:
        error_index = errors.get("index", 0)
        token = tokens[error_index] if error_index < len(tokens) else "<eof>"
        message = errors.get("message", "Error: Invalid syntax")
        print(f"{message} near token: {token}")
        return

    print("Program is syntactically valid")
    print("\nParse Tree:")
    print("\n".join(tree.to_lines()))


if __name__ == "__main__":
    main()
