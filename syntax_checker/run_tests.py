from parser import parse, parse_if, parse_program, parse_while
from tokenizer import tokenize, tokenize_with_lines


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


def run_program_case(source, expected):
    errors = {}
    context = {"symbol_table": {}}
    actual = parse_program(tokenize(source), errors, context) is not None
    status = "PASS" if actual == expected else "FAIL"
    print(f"[{status}] PARSE {source!r}")
    print(f"       expected = {expected}, actual = {actual}")
    return status == "PASS"


def run_program_artifacts(source):
    errors = {}
    context = {"symbol_table": {}}
    tree = parse_program(tokenize(source), errors, context)
    return tree, errors, context


def run_program_with_lines(source, context=None):
    tokens, line_numbers = tokenize_with_lines(source)
    errors = {"line_numbers": line_numbers}
    tree = parse_program(tokens, errors, context)
    return tree, errors, context


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

    float_tokenizer_expected = ["float", "b", ";", "a", "=", "b", "+", "1.5", ";"]
    float_tokenizer_actual = tokenize("float b; a=b+1.5;")
    float_tokenizer_ok = float_tokenizer_actual == float_tokenizer_expected

    print("[PASS]" if float_tokenizer_ok else "[FAIL]", "TOKENIZER supports float literals")
    print(f"       expected = {float_tokenizer_expected}")
    print(f"       actual   = {float_tokenizer_actual}")

    identifier_tokenizer_expected = ["char", "_value1", ";", "_value1", "=", "(", "_value1", "+", "2", ")", "*", "3", ";"]
    identifier_tokenizer_actual = tokenize("char _value1; _value1=(_value1+2)*3;")
    identifier_tokenizer_ok = identifier_tokenizer_actual == identifier_tokenizer_expected

    print("[PASS]" if identifier_tokenizer_ok else "[FAIL]", "TOKENIZER supports underscores and parentheses")
    print(f"       expected = {identifier_tokenizer_expected}")
    print(f"       actual   = {identifier_tokenizer_actual}")

    main_tokenizer_expected = [
        "int", "main", "(", ")", "{", "int", "i", ";", "while", "(", "i", "<", "10", ")", "{",
        "i", "=", "i", "+", "1", ";", "}", "}",
    ]
    main_tokenizer_actual = tokenize("int main(){ int i; while(i<10){ i=i+1; } }")
    main_tokenizer_ok = main_tokenizer_actual == main_tokenizer_expected

    print("[PASS]" if main_tokenizer_ok else "[FAIL]", "TOKENIZER supports main wrapper")
    print(f"       expected = {main_tokenizer_expected}")
    print(f"       actual   = {main_tokenizer_actual}")

    call_tokenizer_expected = ["result", "=", "add", "(", "x", ",", "2", ")", ";"]
    call_tokenizer_actual = tokenize("result=add(x,2);")
    call_tokenizer_ok = call_tokenizer_actual == call_tokenizer_expected

    print("[PASS]" if call_tokenizer_ok else "[FAIL]", "TOKENIZER supports function call commas")
    print(f"       expected = {call_tokenizer_expected}")
    print(f"       actual   = {call_tokenizer_actual}")

    cases = [
        ("if", "if(a>b) a=a+1;", True),
        ("if", "if(a>5) a=a+1;", True),
        ("if", "if(a>b a=a+1;", False),
        ("if", "if(a>b) a=a+b;", True),
        ("if", "if(a>=b) a=a+1;", True),
        ("if", "if(a>b) a=a+b*5-c;", True),
        ("if", "if((a+1)>(b*2)) a=(a+b)*(c-1);", True),
        ("if", "if(a>b){a=a+1;}else if(a<b){a=a+2;}else{a=a+3;}", True),
        ("while", "while(b<10) b++;", True),
        ("while", "while(x!=9) x++;", True),
        ("while", "while(b<10 b++;", False),
        ("while", "while(b<10) b=b+1;", True),
        ("while", "while(7<b) b++;", True),
        ("if", "if(a>b){a=a+1;}", True),
        ("while", "while(b<10){b++;}", True),
        ("while", "while(b<10){continue;}", True),
    ]

    parse_cases = [
        ("int a; int b; if(a>b){ a=a+1; while(b<10){ b++; } }", True),
        ("int a; int b; int x; if(a>b){ while(b<10){ if(x!=9){ x=x+1; } } }", True),
        ("if(a>b){ a=a+1; ", False),
        ("int a; int b; while(b<10){ if(a>b) a=a+1; }", True),
        ("if(a>b){ invalid }", False),
        ("int a; float b; float c; if(a>b){ b=b+c*5.0; }else if(a<b){ a=a+2; }else{ c=c+3.5; }", True),
        ("int main(){ int a; int b; int i; if(a>b){ a=a+b*5; } while(i<10){ i=i+1; } }", True),
        ("int a; int b; if(a>b)\n{\n    a=a+1;\n    while(b<10)\n    {\n        b++;\n    }\n}", True),
        ("char flag; int a; int b; if((a+1)>(b*2)){ { a=(a+b)*(a-1); } }", True),
        ("{ int a; a=(3+4)*5; }", True),
        ("int i; for(i=0; i<10; i++){ i=i+1; }", True),
        ("int x; int y; x=add(y,2); print(x);", True),
        ("int main(){ int i; for(i=0; i<10; i++){ continue; } return 0; }", True),
        ("int b; while(b<10){ break; }", True),
        ("int add(int a, int b){ return a+b; } int main(){ int x; x=add(5,10); return x; }", True),
        ("int inc(int a){ return a+1; } int dbl(int b){ return inc(b)+inc(b); } int main(){ int x; x=dbl(3); return x; }", True),
        ("int sum(int a, int b, int c){ return a+b+c; } int main(){ int x; x=sum(1,2,3); return x; }", True),
        ("int main(){ int i; for(; i<10; i++){ print(i); } return 0; }", True),
        ("int main(){ int i; for(i=0; i<10; ){ i++; } return 0; }", True),
        ("int main(){ int x; x=add(mul(2,3),inc(4)); return x; }", True),
        ("int add(int a, int b){ return a+b; } int main(){ return add(add(1,2), add(3,4)); }", True),
    ]

    error_cases = [
        ("if(a>b { a=a+1; }", ("Missing ')'", "{", 6)),
        ("while(b<10){ b++ }", ("Expected ';'", "}", 10)),
        ("if(>b){ a=a+1; }", ("Expected operand", ">", 3)),
        ("if(a>b) a=a+;", ("Expected operand", ";", 11)),
        ("int main(){ int a; int b; if(a>b){ a=a+1; }", ("Missing '}'", "<eof>", 26)),
        ("int a; if((a+1)>b{ a=a+1; }", ("Missing ')'", "{", 13)),
        ("for(i=0 i<10; i++){ i=i+1; }", ("Expected ';' after for initializer", "i", 6)),
        ("return 0", ("Expected ';'", "<eof>", 3)),
        ("foo(1,);", ("Expected operand", ")", 5)),
        ("int add(int a float b){ return a+b; }", ("Missing ')'", "float", 6)),
        ("int add(int a,){ return a; }", ("Expected parameter type", ")", 6)),
        ("int add(, int b){ return b; }", ("Expected parameter type", ",", 4)),
        ("int main(){ int x; x=add((1+2); return x; }", ("Missing ')'", ";", 12)),
        ("int main(){ for(i=0; i<10 i++){ i++; } }", ("Expected ';' after for condition", "i", 10)),
        ("int main(){ return add(1 2); }", ("Missing ')' in function call", "2", 10)),
    ]

    semantic_error_cases = [
        ("a=5;", ("Variable 'a' not declared", "a", 1)),
        ("int a; b=10;", ("Variable 'b' not declared", "b", 4)),
        ("int a; a=b+1;", ("Variable 'b' not declared", "b", 6)),
        ("int a; int a;", ("Variable 'a' already declared", "a", 5)),
        ("int main(){ int a; if(a>b){ a=a+1; } }", ("Variable 'b' not declared", "b", 13)),
        ("int a; if((a+1)>(b*2)){ a=a+1; }", ("Variable 'b' not declared", "b", 13)),
    ]

    type_error_cases = [
        ("int a; float b; a=b+1;", ("Type mismatch: cannot assign float to int", ";", 12)),
        ("int main(){ int a; float b; a=b+1; }", ("Type mismatch: cannot assign float to int", ";", 17)),
    ]

    stress_error_cases = [
        ("int main(){ break; }", ("break outside loop accepted by current grammar", True)),
        ("int main(){ continue; }", ("continue outside loop accepted by current grammar", True)),
    ]

    recovery_source = "int a\na = ;\nif(a>b {\n    a = a + ;\n}\n"
    recovery_expected = [
        ("Expected ';'", "a", 2),
        ("Missing ')'", "{", 3),
        ("Expected operand", ";", 4),
        ("Unexpected token", "}", 5),
    ]

    nested_recovery_source = "int main(){\n    int a;\n    if(a>0){\n        a = ;\n        a++;\n    }\n}\n"
    nested_recovery_expected = [
        ("Expected operand", ";", 4),
    ]

    block_recovery_source = "{\n    int a\n    a = 1;\n    a++;\n}\n"
    block_recovery_expected = [
        ("Expected ';'", "a", 3),
    ]

    tree_source = "int main(){ int a; int b; int c; int i; if(a>b){ a=a+b*5-c; }else if(a<b){ a=a+2; }else{ a=a+3; } while(i<10){ i=i+1; } }"
    tree_expected = [
        "PROGRAM",
        "  FUNCTION (main)",
        "    TYPE (int)",
        "    BLOCK",
        "      DECL (int)",
        "        TYPE (int)",
        "        IDENT (a)",
        "      DECL (int)",
        "        TYPE (int)",
        "        IDENT (b)",
        "      DECL (int)",
        "        TYPE (int)",
        "        IDENT (c)",
        "      DECL (int)",
        "        TYPE (int)",
        "        IDENT (i)",
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

    tac_source = "int a; int b; int c; if(a>b){ a=b+c*5; } while(a<10){ a=a+1; }"
    tac_expected = [
        "t1 = c * 5",
        "t2 = b + t1",
        "a = t2",
        "t3 = a + 1",
        "a = t3",
    ]

    passed = 0
    total = 0

    for ok in [tokenizer_ok, comment_ok, expr_tokenizer_ok, float_tokenizer_ok, identifier_tokenizer_ok, main_tokenizer_ok, call_tokenizer_ok]:
        total += 1
        if ok:
            passed += 1

    for kind, source, expected in cases:
        total += 1
        if run_case(kind, source, expected):
            passed += 1

    for source, expected in parse_cases:
        total += 1
        if run_program_case(source, expected):
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

    for source, expected in semantic_error_cases:
        total += 1
        errors = {}
        context = {"symbol_table": {}}
        parse_program(tokenize(source), errors, context)
        actual = (
            errors.get("message"),
            errors.get("token"),
            errors.get("index", -1) + 1,
        )
        status = "PASS" if actual == expected else "FAIL"
        print(f"[{status}] SEMANTIC {source!r}")
        print(f"       expected = {expected}, actual = {actual}")
        if actual == expected:
            passed += 1

    for source, expected in type_error_cases:
        total += 1
        errors = {}
        context = {"symbol_table": {}}
        parse_program(tokenize(source), errors, context)
        actual = (
            errors.get("message"),
            errors.get("token"),
            errors.get("index", -1) + 1,
        )
        status = "PASS" if actual == expected else "FAIL"
        print(f"[{status}] TYPE {source!r}")
        print(f"       expected = {expected}, actual = {actual}")
        if actual == expected:
            passed += 1

    total += 1
    tree = parse_program(tokenize(tree_source), {}, {"symbol_table": {}})
    actual_tree = tree.to_lines() if tree is not None else None
    tree_ok = actual_tree == tree_expected
    print(f"[{'PASS' if tree_ok else 'FAIL'}] TREE {tree_source!r}")
    print(f"       expected = {tree_expected}")
    print(f"       actual   = {actual_tree}")
    if tree_ok:
        passed += 1

    total += 1
    _, tac_errors, tac_context = run_program_artifacts(tac_source)
    actual_tac = tac_context.get("intermediate_code") if not tac_errors else None
    tac_ok = actual_tac == tac_expected
    print(f"[{'PASS' if tac_ok else 'FAIL'}] TAC {tac_source!r}")
    print(f"       expected = {tac_expected}")
    print(f"       actual   = {actual_tac}")
    if tac_ok:
        passed += 1

    total += 1
    recovery_tree, recovery_errors, _ = run_program_with_lines(recovery_source, None)
    actual_recovery = [
        (item.get("message"), item.get("token"), item.get("line"))
        for item in recovery_errors.get("items", [])
    ]
    recovery_ok = recovery_tree is None and actual_recovery == recovery_expected
    print(f"[{'PASS' if recovery_ok else 'FAIL'}] RECOVERY {recovery_source!r}")
    print(f"       expected = {recovery_expected}")
    print(f"       actual   = {actual_recovery}")
    if recovery_ok:
        passed += 1

    total += 1
    nested_recovery_tree, nested_recovery_errors, _ = run_program_with_lines(nested_recovery_source, {"symbol_table": {}})
    actual_nested_recovery = [
        (item.get("message"), item.get("token"), item.get("line"))
        for item in nested_recovery_errors.get("items", [])
    ]
    nested_recovery_ok = nested_recovery_tree is None and actual_nested_recovery == nested_recovery_expected
    print(f"[{'PASS' if nested_recovery_ok else 'FAIL'}] NESTED RECOVERY {nested_recovery_source!r}")
    print(f"       expected = {nested_recovery_expected}")
    print(f"       actual   = {actual_nested_recovery}")
    if nested_recovery_ok:
        passed += 1

    total += 1
    block_recovery_tree, block_recovery_errors, _ = run_program_with_lines(block_recovery_source, None)
    actual_block_recovery = [
        (item.get("message"), item.get("token"), item.get("line"))
        for item in block_recovery_errors.get("items", [])
    ]
    block_recovery_ok = block_recovery_tree is None and actual_block_recovery == block_recovery_expected
    print(f"[{'PASS' if block_recovery_ok else 'FAIL'}] BLOCK RECOVERY {block_recovery_source!r}")
    print(f"       expected = {block_recovery_expected}")
    print(f"       actual   = {actual_block_recovery}")
    if block_recovery_ok:
        passed += 1

    for source, expected in stress_error_cases:
        total += 1
        errors = {}
        context = {"symbol_table": {}}
        actual = parse_program(tokenize(source), errors, context) is not None
        status = "PASS" if actual == expected[1] else "FAIL"
        print(f"[{status}] STRESS {source!r}")
        print(f"       note     = {expected[0]}")
        print(f"       accepted = {actual}")
        if actual == expected[1]:
            passed += 1

    print(f"\nSummary: {passed}/{total} tests passed")


if __name__ == "__main__":
    main()
