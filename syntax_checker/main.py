from pathlib import Path

from parser import parse_if, parse_while
from tokenizer import tokenize


def check_line(line, line_no):
    tokens = tokenize(line)

    if not tokens:
        return

    if tokens[0] == "if":
        if parse_if(tokens):
            print(f"Line {line_no}: Valid IF statement")
        else:
            print(f"Line {line_no}: Invalid IF syntax")

    elif tokens[0] == "while":
        if parse_while(tokens):
            print(f"Line {line_no}: Valid WHILE statement")
        else:
            print(f"Line {line_no}: Invalid WHILE syntax")


def main():
    program_path = Path(__file__).with_name("test_program.txt")

    with program_path.open() as file:
        lines = file.readlines()

    for i, line in enumerate(lines):
        check_line(line.strip(), i + 1)


if __name__ == "__main__":
    main()
