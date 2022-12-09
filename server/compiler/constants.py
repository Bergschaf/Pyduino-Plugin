class Constants:
    FILENAME = "../testPyduino.pino"

    DEFAULT_INDEX_LEVEL = 4  # spaces

    OPENING_BRACKETS = ["{", "(", "["]
    CLOSING_BRACKETS = {"(": ")", "[": "]", "{": "}"}
    BRACKETS = ["(", ")", "[", "]", "{", "}"]

    VALID_NAME_START_LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    VALID_NAME_LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"

    PRIMITIVE_TYPES = ["int", "float", "char", "bool"]
    PRIMITIVE_ARRAY_TYPES = ["int[]", "float[]", "char[]", "bool[]"]
    PRIMITIVE_LIST_TYPES = ["list<int>", "list<float>", "list<char>", "list<bool>","list<byte>", "list<long>", "list<double>", "list<short>"]
    ITERABLES = PRIMITIVE_ARRAY_TYPES + PRIMITIVE_LIST_TYPES

    NUMBERS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    ARITHMETIC_OPERATORS = ["+", "-", "*", "/", "%", "**", "//"]
    ARITHMETIC_OPERATORS_LEN1 = ["+", "-", "*", "/", "%"]
    ARITHMETIC_OPERATORS_LEN2 = ["**", "//"]

    CONDITION_OPERATORS_LEN1 = ["<", ">"]
    CONDITION_OPERATORS_LEN2 = ["==", "!=", "<=", ">=", "&&", "||"]
    COMPAIRSON = ["<", ">", "==", "!=", "<=", ">="]

    OPERATORS = ARITHMETIC_OPERATORS + CONDITION_OPERATORS_LEN1 + CONDITION_OPERATORS_LEN2

    CONDITION_CONDITIONS = ["and", "or"]

    WHITESPACE = '" "'

    ALL_SYNTAX_ELEMENTS = OPERATORS + CONDITION_CONDITIONS + BRACKETS
