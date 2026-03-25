from parser import parse_if, parse_while
from tokenizer import tokenize


def run_case(kind, source, expected):
    tokens = tokenize(source)

    if kind == "if":
        actual = parse_if(tokens)
    elif kind == "while":
        actual = parse_while(tokens)
    else:
        raise ValueError(f"Unknown case type: {kind}")

    status = "PASS" if actual == expected else "FAIL"
    print(f"[{status}] {kind.upper():5} {source}")
    print(f"       tokens   = {tokens}")
    print(f"       expected = {expected}, actual = {actual}")
    return status == "PASS"


def main():
    tokenizer_expected = ["if", "(", "a", ">", "b", ")", "a", "=", "a", "+", "1", ";"]
    tokenizer_actual = tokenize("if(a>b) a=a+1;")
    tokenizer_ok = tokenizer_actual == tokenizer_expected

    print("[PASS]" if tokenizer_ok else "[FAIL]", "TOKENIZER if(a>b) a=a+1;")
    print(f"       expected = {tokenizer_expected}")
    print(f"       actual   = {tokenizer_actual}")

    cases = [
        ("if", "if(a>b) a=a+1;", True),
        ("if", "if(a>5) a=a+1;", True),
        ("if", "if(a>b a=a+1;", False),
        ("if", "if(a>b) a=a+b;", False),
        ("if", "if(a>=b) a=a+1;", True),
        ("while", "while(b<10) b++;", True),
        ("while", "while(x!=9) x++;", True),
        ("while", "while(b<10 b++;", False),
        ("while", "while(b<10) b=b+1;", False),
        ("while", "while(7<b) b++;", False),
    ]

    passed = 1 if tokenizer_ok else 0
    total = 1

    for kind, source, expected in cases:
        total += 1
        if run_case(kind, source, expected):
            passed += 1

    print(f"\nSummary: {passed}/{total} tests passed")


if __name__ == "__main__":
    main()
