from parser import parse, parse_if, parse_program, parse_while
from tokenizer import tokenize


def run_case(kind, source, expected):
    tokens = tokenize(source)

    if kind == "if":
        actual = parse_if(tokens)[0] == len(tokens)
    elif kind == "while":
        actual = parse_while(tokens)[0] == len(tokens)
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

    comment_expected = ["if", "(", "a", ">", "b", ")", "{", "a", "=", "a", "+", "1", ";", "}"]
    comment_actual = tokenize("if(a>b){ a=a+1; } // comment")
    comment_ok = comment_actual == comment_expected

    print("[PASS]" if comment_ok else "[FAIL]", "TOKENIZER strips comments")
    print(f"       expected = {comment_expected}")
    print(f"       actual   = {comment_actual}")

    expr_tokenizer_expected = ["a", "=", "a", "+", "b", "*", "5", "-", "c", ";"]
    expr_tokenizer_actual = tokenize("a=a+b*5-c;")
    expr_tokenizer_ok = expr_tokenizer_actual == expr_tokenizer_expected

    print("[PASS]" if expr_tokenizer_ok else "[FAIL]", "TOKENIZER supports expression operators")
    print(f"       expected = {expr_tokenizer_expected}")
    print(f"       actual   = {expr_tokenizer_actual}")

    main_tokenizer_expected = [
        "int", "main", "(", ")", "{", "while", "(", "i", "<", "10", ")", "{",
        "i", "=", "i", "+", "1", ";", "}", "}",
    ]
    main_tokenizer_actual = tokenize("int main(){ while(i<10){ i=i+1; } }")
    main_tokenizer_ok = main_tokenizer_actual == main_tokenizer_expected

    print("[PASS]" if main_tokenizer_ok else "[FAIL]", "TOKENIZER supports main wrapper")
    print(f"       expected = {main_tokenizer_expected}")
    print(f"       actual   = {main_tokenizer_actual}")

    cases = [
        ("if", "if(a>b) a=a+1;", True),
        ("if", "if(a>5) a=a+1;", True),
        ("if", "if(a>b a=a+1;", False),
        ("if", "if(a>b) a=a+b;", True),
        ("if", "if(a>=b) a=a+1;", True),
        ("if", "if(a>b) a=a+b*5-c;", True),
        ("if", "if(a>b){a=a+1;}else if(a<b){a=a+2;}else{a=a+3;}", True),
        ("while", "while(b<10) b++;", True),
        ("while", "while(x!=9) x++;", True),
        ("while", "while(b<10 b++;", False),
        ("while", "while(b<10) b=b+1;", True),
        ("while", "while(7<b) b++;", False),
        ("if", "if(a>b){a=a+1;}", True),
        ("while", "while(b<10){b++;}", True),
    ]

    parse_cases = [
        ("if(a>b){ a=a+1; while(b<10){ b++; } }", True),
        ("if(a>b){ while(b<10){ if(x!=9){ x=x+1; } } }", True),
        ("if(a>b){ a=a+1; ", False),
        ("while(b<10){ if(a>b) a=a+1; }", True),
        ("if(a>b){ invalid }", False),
        ("if(a>b){ a=a+b*5-c; }else if(a<b){ a=a+2; }else{ a=a+3; }", True),
        ("int main(){ if(a>b){ a=a+b*5; } while(i<10){ i=i+1; } }", True),
        ("if(a>b)\n{\n    a=a+1;\n    while(b<10)\n    {\n        b++;\n    }\n}", True),
    ]

    error_cases = [
        ("if(a>b { a=a+1; }", ("Missing ')'", "{", 6)),
        ("while(b<10){ b++ }", ("Expected ';'", "}", 10)),
        ("if(>b){ a=a+1; }", ("Expected variable on left side of condition", ">", 3)),
        ("if(a>b) a=a+;", ("Expected operand", ";", 11)),
        ("int main(){ if(a>b){ a=a+1; }", ("Missing '}'", "<eof>", 20)),
    ]

    tree_source = "int main(){ if(a>b){ a=a+b*5-c; }else if(a<b){ a=a+2; }else{ a=a+3; } while(i<10){ i=i+1; } }"
    tree_expected = [
        "PROGRAM",
        "  MAIN",
        "    BLOCK",
        "      IF",
        "        CONDITION (>)",
        "          IDENT (a)",
        "          IDENT (b)",
        "        BLOCK",
        "          ASSIGN",
        "            IDENT (a)",
        "            -",
        "              +",
        "                IDENT (a)",
        "                *",
        "                  IDENT (b)",
        "                  NUMBER (5)",
        "              IDENT (c)",
        "        ELSE",
        "          IF",
        "            CONDITION (<)",
        "              IDENT (a)",
        "              IDENT (b)",
        "            BLOCK",
        "              ASSIGN",
        "                IDENT (a)",
        "                +",
        "                  IDENT (a)",
        "                  NUMBER (2)",
        "            ELSE",
        "              BLOCK",
        "                ASSIGN",
        "                  IDENT (a)",
        "                  +",
        "                    IDENT (a)",
        "                    NUMBER (3)",
        "      WHILE",
        "        CONDITION (<)",
        "          IDENT (i)",
        "          NUMBER (10)",
        "        BLOCK",
        "          ASSIGN",
        "            IDENT (i)",
        "            +",
        "              IDENT (i)",
        "              NUMBER (1)",
    ]

    passed = 0
    total = 0

    for ok in [tokenizer_ok, comment_ok, expr_tokenizer_ok, main_tokenizer_ok]:
        total += 1
        if ok:
            passed += 1

    for kind, source, expected in cases:
        total += 1
        if run_case(kind, source, expected):
            passed += 1

    for source, expected in parse_cases:
        total += 1
        actual = parse_program(tokenize(source), {}) is not None
        status = "PASS" if actual == expected else "FAIL"
        print(f"[{status}] PARSE {source!r}")
        print(f"       expected = {expected}, actual = {actual}")
        if actual == expected:
            passed += 1

    for source, expected in error_cases:
        total += 1
        errors = {}
        parse_program(tokenize(source), errors)
        actual = (
            errors.get("message"),
            errors.get("token"),
            errors.get("index", -1) + 1,
        )
        status = "PASS" if actual == expected else "FAIL"
        print(f"[{status}] ERROR {source!r}")
        print(f"       expected = {expected}, actual = {actual}")
        if actual == expected:
            passed += 1

    total += 1
    tree = parse_program(tokenize(tree_source), {})
    actual_tree = tree.to_lines() if tree is not None else None
    tree_ok = actual_tree == tree_expected
    print(f"[{'PASS' if tree_ok else 'FAIL'}] TREE {tree_source!r}")
    print(f"       expected = {tree_expected}")
    print(f"       actual   = {actual_tree}")
    if tree_ok:
        passed += 1

    print(f"\nSummary: {passed}/{total} tests passed")


if __name__ == "__main__":
    main()
