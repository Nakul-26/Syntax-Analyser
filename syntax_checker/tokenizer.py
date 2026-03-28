import re


def tokenize(line):
    source = re.sub(r"//.*", "", line)
    tokens = re.findall(r"\d+\.\d+|\w+|\+\+|==|!=|<=|>=|[(){};=+\-*/<>]", source)
    return tokens
