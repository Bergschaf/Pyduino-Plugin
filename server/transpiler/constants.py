class Constants:
    FILENAME = "../testPyduino.pino"

    DEFAULT_INDEX_LEVEL = 4  # spaces

    OPENING_BRACKETS = ["{", "(", "["]
    CLOSING_BRACKETS = {"(": ")", "[": "]", "{": "}"}
    BRACKETS = ["(", ")", "[", "]", "{", "}"]

    VALID_NAME_START_LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    VALID_NAME_LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"

    PRIMITIVE_TYPES = ["int", "float"]
    PRIMITIVE_ARRAY_TYPES = ["int[]", "float[]"]
    NUMERIC_TYPES = ["int", "float"]
    ITERABLES = PRIMITIVE_ARRAY_TYPES

    NUMBERS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    ARITHMETIC_OPERATORS = ["+", "-", "*", "/", "%", "**", "//"]
    ARITHMETIC_OPERATORS_LEN1 = ["+", "-", "*", "/", "%"]
    ARITHMETIC_OPERATORS_LEN2 = ["**", "//"]

    CONDITION_OPERATORS_LEN1 = ["<", ">"]
    CONDITION_OPERATORS_LEN2 = ["==", "!=", "<=", ">=", "&&", "||"]
    BOOLEAN_OPERATORS = ["&&", "||"]
    COMPAIRSON = ["<", ">", "==", "!=", "<=", ">="]
    OPERATION_ORDER = [("**"), ("*", "/", "%", "//"), ("+", "-"), ("==", "!=", "<=", ">=", "<", ">"), ("&&", "||")]


    OPERATORS = ARITHMETIC_OPERATORS + CONDITION_OPERATORS_LEN1 + CONDITION_OPERATORS_LEN2

    CONDITION_CONDITIONS = ["and", "or"]

    WHITESPACE = '" "'

    ALL_SYNTAX_ELEMENTS = OPERATORS + CONDITION_CONDITIONS + BRACKETS

    BUITLIN_FUNCTIONS = [("print", ("*all"), None), ("delay", ("int"), None),
                         ("analogWrite", ("int", "int"), None), ("digitalWrite", ("int", "int"), None),
                         ("analogRead", ("int"), "int"), ("digitalRead", ("int"), "int"),
                         ("len",("iterable"),"int")] # (name, (arg, arg, ...), return)
