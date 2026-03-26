import re


def tokenize(line):
    source = re.sub(r"//.*", "", line)
    tokens = re.findall(r"\w+|\+\+|==|!=|<=|>=|[(){};=+<>]", source)
    return tokens
