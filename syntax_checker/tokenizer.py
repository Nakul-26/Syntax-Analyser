import re


def tokenize(line):
    tokens = re.findall(r"\w+|\+\+|==|!=|<=|>=|[(){};=+<>]", line)
    return tokens
