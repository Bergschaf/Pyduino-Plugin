from server.compiler.constants import Constants
from server.compiler.error import Error

class Utils:
    def __init__(self, variables, builtins, errors):
        self.errors = errors
        self.Variables = variables
        self.Builtins = builtins

    def reset_sys_variable(self):
        self.Variables.sysVariableIndex = 0

    def next_sys_variable(self):
        self.Variables.sysVariableIndex += 1
        return f"_sys_var_{self.Variables.sysVariableIndex}"

    def find_closing_bracket_in_value(self, value, bracket, start_col):
        """
        :param value: the value to search in
        :param bracket: the bracket to search for
        :param start_col: the column to start searching from
        """
        if type(bracket) is not str or len(bracket) != 1:
            raise SyntaxError(f"Bracket has to be a string of length 1")
        if bracket not in "([{":
            raise SyntaxError(f"'{bracket}' is not a valid opening bracket")
        if value[start_col] != bracket:
            raise SyntaxError(f"Value does not start with '{bracket}'")
        closing_bracket = Constants.CLOSING_BRACKETS[bracket]
        bracket_level_1 = 0
        bracket_level_2 = 0
        bracket_level_3 = 0
        if bracket == "(":
            bracket_level_1 = 1
        elif bracket == "[":
            bracket_level_2 = 1
        elif bracket == "{":
            bracket_level_3 = 1
        col = start_col + 1
        while col < len(value):
            if value[col] == Constants.BRACKETS[0]:
                bracket_level_1 += 1
            elif value[col] == Constants.BRACKETS[1]:
                bracket_level_1 -= 1
            elif value[col] == Constants.BRACKETS[2]:
                bracket_level_2 += 1
            elif value[col] == Constants.BRACKETS[3]:
                bracket_level_2 -= 1
            elif value[col] == Constants.BRACKETS[4]:
                bracket_level_3 += 1
            elif value[col] == Constants.BRACKETS[5]:
                bracket_level_3 -= 1
            if value[col] == closing_bracket and bracket_level_1 == 0 and bracket_level_2 == 0 and bracket_level_3 == 0:
                return col
            col += 1

        self.errors.append(Error(f"No closing bracket found for '{bracket}'",
                                 self.Variables.currentLineIndex, self.Variables.currentLine.find(value)))

    def do_arguments(self, argstring):
        """
        :param argstring: all arguments as a string WITHOUT the brackets
        :return: argument list, kwarg dictionary
        """
        args = []  # Format: (name, datatype)
        kwargs = {}
        all_args = []
        # split the args, but ignore commas in brackets
        last_split = 0
        closing_bracket = 0
        for i in range(len(argstring)):
            if closing_bracket > i:
                continue
            if argstring[i] == ",":
                all_args.append(argstring[last_split:i])
                last_split = i + 1
            elif argstring[i] in Constants.OPENING_BRACKETS:
                closing_bracket = self.find_closing_bracket_in_value(argstring, argstring[i], i)
        all_args.append(argstring[last_split:])
        for arg in all_args:
            arg = arg.strip()
            if "=" not in arg:
                if kwargs:
                    self.errors.append(Error(f"Non-keyword argument '{arg}' after keyword argument",
                                             self.Variables.currentLineIndex, self.Variables.currentLine.find(arg)))
                    return -1

                args.append(self.do_value(arg))
            else:
                name, value = arg.split("=")
                name = name.strip()
                value = value.strip()
                kwargs[name] = self.do_value(value)
        return args, kwargs

    def do_line(self, line):
        instruction = line.strip()
        if instruction == "":
            return ""

        if self.get_line_indentation(line) != self.Variables.inIndentation:
            self.errors.append(Error(f"Indentation error", self.Variables.currentLineIndex, 0))

        if (len(line) - len(line.lstrip())) % Constants.DEFAULT_INDEX_LEVEL != 0:
            self.errors.append(Error(f"Indentation error", self.Variables.currentLineIndex, 0))
        if instruction == "":
            return ""
        self.Variables.currentColumnIndex = line.index(instruction)
        self.Variables.currentLine = line
        if instruction[0] == "#":
            return ""
        elif any([instruction.startswith(i) for i in
                  Constants.PRIMITIVE_TYPES + Constants.PRIMITIVE_ARRAY_TYPES]):
            if (f := self.check_function_definition(instruction)) is not None:
                return f
            else:
                return self.do_variable_definition(instruction)
        elif (f := self.check_function_execution(instruction)) is not None:
            return f[0] + ";"
        elif instruction[:2] == "if":
            return self.do_if(instruction)
        elif instruction[:5] == "while":
            return self.do_while(instruction)
        elif instruction[:3] == "for":
            return self.do_for(instruction)
        # TODO: das am Ende
        elif "=" in instruction:
            return self.do_variable_assignment(instruction)
        elif instruction == "break" or instruction == "continue":
            return self.do_break_continue(instruction)
        else:
            self.errors.append(Error(f"Unknown instruction '{instruction}'",
                                     self.Variables.currentLineIndex, 0, end_column=len(self.Variables.currentLine)))
            return ""

    def check_function_definition(self, line):
        pass

    def check_function_execution(self, value):
        value = value.strip()
        if "(" not in value:
            return
        first_bracket = value.index("(")
        function_name = value[:first_bracket]

        second_bracket = self.find_closing_bracket_in_value(value, "(", first_bracket)
        arguments = value[first_bracket + 1:second_bracket]
        # TODO was wenn , in arguemtns?
        args, kwargs = self.do_arguments(arguments)
        if (f := self.Builtins.check_builtin(function_name, args, kwargs)) is not None:
            # and f[2]: TODO only let functions like cout through if the return value isn'T used
            return f[0], f[1]
            #  TODO check if function is defined

        """
        :return: (function translated to C++, return type, False here if the C++ representation works not as a function
        call with return type else True)
        """
        pass

    def do_variable_definition(self, line):
        """
        :param line: The complete line of the variable definition
        :return: The definition converted to C++
        """
        if "=" not in line:
            self.errors.append(Error("No value assigned to variable",
                                     self.Variables.currentLineIndex, self.Variables.currentLine.find(line)))
            return ""
        line = line.strip()
        datatype = line.split("=")[0].strip().split(" ")[0].strip()
        if datatype in Constants.PRIMITIVE_TYPES:
            name = line.split("=")[0].strip().split(" ")[1].strip()
            value = line.split("=")[1].strip()
            value, dt = self.do_value(value)
            if dt != -1:
                if dt != datatype:
                    self.errors.append(Error(f"Datatype mismatch: {datatype} != {dt}", self.Variables.currentLineIndex,
                                             self.Variables.currentLine.find(line)))
                    return ""
            if self.variable_in_scope(name, self.Variables.currentLineIndex)[1]:
                self.errors.append(Error(f"Variable '{name}' already defined in this scope",
                                         self.Variables.currentLineIndex, self.Variables.currentLine.find(name)))
                return ""
            self.add_variable_to_scope(name, datatype, self.Variables.currentLineIndex)
            return f"{datatype} {name} = {value};"
        elif datatype in Constants.PRIMITIVE_ARRAY_TYPES:
            name = line.split("=")[0].strip().split(" ")[1].strip()
            value = line.split("=")[1].strip()
            value, dt = self.do_array_intializer(value)
            if dt != -1:
                if dt != datatype[:-2]:
                    self.errors.append(Error(f"Datatype mismatch: {datatype} != {dt}", self.Variables.currentLineIndex,
                                             self.Variables.currentLine.find(line)))
            if self.variable_in_scope(name, self.Variables.currentLineIndex)[1]:
                self.errors.append(Error(f"Variable '{name}' already defined in this scope",
                                         self.Variables.currentLineIndex, self.Variables.currentLine.find(name)))
                return ""
            self.add_variable_to_scope(name, datatype, self.Variables.currentLineIndex)
            return f"{datatype[:-2]} {name}[] = {value};"
        else:
            self.errors.append(Error(f"Datatype '{datatype}' not supported", self.Variables.currentLineIndex,
                                     self.Variables.currentLine.find(datatype)))
            return ""

    def do_variable_assignment(self, line):
        """
        :param line: The complete line of the variable assignment
        :return: The assignment converted to C++
        """
        line = line.strip()
        name = line.split("=")[0].strip()
        value = line.split("=")[1].strip()
        value, dt = self.do_value(value)
        if dt == -1:
            return ""
        if not self.variable_in_scope(name, self.Variables.currentLineIndex)[0]:
            self.errors.append(Error(f"Variable '{name}' not defined in this scope", self.Variables.currentLineIndex,
                                     self.Variables.currentLine.find(name)))
            return ""
        if dt != self.variable_in_scope(name, self.Variables.currentLineIndex)[1] and dt is not None:
            self.errors.append(
                Error(f"Datatype mismatch: {self.variable_in_scope(name, self.Variables.currentLineIndex)[1]} != {dt}",
                      self.Variables.currentLineIndex, self.Variables.currentLine.find(line)))
            return ""
        return f"{name} = {value};"

    def do_if(self, line):
        col_index = line.index("if") + 2
        if line.strip()[-1] != ":":
            self.errors.append(
                Error("Expected ':' after if", self.Variables.currentLineIndex, len(self.Variables.currentLine) - 1))

        row = self.Variables.currentLineIndex
        col = len(line) - 1
        condition = self.do_value(line[col_index + 1:col])[0]
        if self.Variables.indentations[row] + 1 != self.Variables.indentations[row + 1]:
            self.errors.append(Error("Expected indentation", row + 1, self.Variables.indentations[row + 1] * 4 + 1))
            return ""
        for i in range(row + 1, self.Variables.totalLineCount):
            if self.Variables.indentations[i] < self.Variables.indentations[row + 1]:
                end_indentation_index = i - 1
                break
        else:
            end_indentation_index = self.Variables.totalLineCount - 1
        self.Variables.code_done.append(f"if ({condition}) {{")
        if_code = []
        self.Variables.inIndentation += 1
        while self.Variables.currentLineIndex < end_indentation_index:
            self.Variables.currentLineIndex, l = next(self.Variables.iterator)
            if_code.append(self.do_line(l))
        self.Variables.inIndentation -= 1
        if_code.append("}")
        return "\n".join(if_code)

    def do_while(self, line):
        col_index = line.index("while") + 5
        if line.strip()[-1] != ":":
            self.errors.append(
                Error("Expected ':' after while", self.Variables.currentLineIndex, len(self.Variables.currentLine) - 1))

        row = self.Variables.currentLineIndex
        col = len(line) - 1
        condition = self.do_value(line[col_index + 1:col])[0]
        if self.Variables.indentations[row] + 1 != self.Variables.indentations[row + 1]:
            self.errors.append(Error("Expected indentation", row + 1, self.Variables.indentations[row + 1] * 4 + 1))
            return ""
        for i in range(row + 1, self.Variables.totalLineCount):
            if self.Variables.indentations[i] < self.Variables.indentations[row + 1]:
                end_indentation_index = i - 1
                break
        else:
            end_indentation_index = self.Variables.totalLineCount - 1
        self.Variables.code_done.append(f"while ({condition}) {{")
        if_code = []
        self.Variables.inLoop += 1
        self.Variables.inIndentation += 1
        while self.Variables.currentLineIndex < end_indentation_index:
            self.Variables.currentLineIndex, l = next(self.Variables.iterator)
            if_code.append(self.do_line(l))
        self.Variables.inLoop -= 1
        self.Variables.inLoop -= 1
        if_code.append("}")
        return "\n".join(if_code)

    def do_for(self, line):
        col_index = line.index("for") + 3
        if line.strip()[-1] != ":":
            self.errors.append(
                Error("Expected ':' after for", self.Variables.currentLineIndex, len(self.Variables.currentLine) - 1))

        row = self.Variables.currentLineIndex
        elements = [x.strip() for x in line[col_index + 1:-1].split("in")]
        dt = "int[]"
        if len(elements) != 2:
            self.errors.append(Error("Expected 'in' in for loop", self.Variables.currentLineIndex,
                                     self.Variables.currentLine.index("for"),
                                     end_column=len(self.Variables.currentLine)))
            return ""

        counter_variable = elements[0]
        if self.Variables.indentations[row] + 1 != self.Variables.indentations[row + 1]:
            self.errors.append(Error("Expected indentation", row + 1, self.Variables.indentations[row + 1] * 4 + 1))
            return ""
        for i in range(row + 1, self.Variables.totalLineCount):
            if self.Variables.indentations[i] < self.Variables.indentations[row + 1]:
                end_indentation_index = i - 1
                break
        else:
            end_indentation_index = self.Variables.totalLineCount - 1

        if elements[1][:5] == "range":
            if elements[1][5] != "(":
                self.errors.append(Error("Expected '(' after range", self.Variables.currentLineIndex,
                                         self.Variables.currentLineIndex, len(self.Variables.currentLine) - 1))
                elements[1] += ")"
            range_arguments, range_kwargs = self.do_arguments(elements[1][6:-1])
            if any([x[1] != "int" and x[1] != "short" and x[1] != "long" and x[1] is not None for x in
                    range_arguments]):
                self.errors.append(
                    Error("Expected int, short or long as argument in 'range'", self.Variables.currentLineIndex
                          , self.Variables.currentLine.index("range") + 5,
                          end_column=len(self.Variables.currentLine) - 2))
                return ""
            if len(range_kwargs) != 0:
                self.errors.append(Error("Expected no keyword arguments in 'range'", self.Variables.currentLineIndex,
                                         self.Variables.currentLine.index("range") + 5,
                                         end_column=len(self.Variables.currentLine) - 2))
                return ""
            if len(range_arguments) == 1:
                range_arguments.append(("0", "int"))
            elif len(range_arguments) > 2:
                self.errors.append(Error("Expected 1 or 2 arguments in 'range'", self.Variables.currentLineIndex,
                                         self.Variables.currentLine.index("range") + 5,
                                         end_column=len(self.Variables.currentLine) - 2))
                return ""

            if len(range_arguments) == 1:
                for_code = [
                    f"for (int {counter_variable} = 0; {counter_variable} < {range_arguments[0][0]} ; {counter_variable}++) {{"]
            elif len(range_arguments) == 2:
                for_code = [
                    f"for (int {counter_variable} = {range_arguments[0][0]}; {counter_variable} < {range_arguments[1][0]} ; {counter_variable}++) {{"]
            elif len(range_arguments) == 3:
                for_code = [
                    f"for (int {counter_variable} = {range_arguments[0][0]}; {counter_variable} < {range_arguments[1][0]} ; {counter_variable} += {range_arguments[2][0]}) {{"]
            else:
                self.errors.append(Error("Expected 1 or 2 arguments in 'range'", self.Variables.currentLineIndex,
                                         self.Variables.currentLine.index("range") + 5,
                                         end_column=len(self.Variables.currentLine) - 2))
                for_code = []
        else:
            val, dt = self.do_value(elements[1])
            if dt in Constants.ITERABLES:

                for_code = [
                    f"for (int {(sys_var := self.next_sys_variable())} = 0; {sys_var} < sizeof({self.do_value(elements[1])[0]}) / sizeof(*{self.do_value(elements[1])[0]}); {sys_var}++) {{",
                    f"auto {counter_variable} = {self.do_value(elements[1])[0]}[{sys_var}];"]
            else:
                self.errors.append(Error("Expected 'range' or iterable after for", self.Variables.currentLineIndex,
                                         self.Variables.currentLine.index("for"),
                                         end_column=len(self.Variables.currentLine)))
                for_code = []
        if dt != -1:
            self.add_variable_to_scope(counter_variable, dt[:-2], self.Variables.currentLineIndex)
        [self.Variables.code_done.append(x) for x in for_code]
        self.Variables.inLoop += 1
        self.Variables.inIndentation += 1
        while self.Variables.currentLineIndex < end_indentation_index:
            self.Variables.currentLineIndex, l = next(self.Variables.iterator)
            self.Variables.code_done.append(self.do_line(l))
        self.Variables.inLoop -= 1
        self.Variables.inIndentation -= 1
        return "}\n"

    def do_break_continue(self, line):
        if 0 == self.Variables.inLoop:
            self.errors.append(Error(f"Can only {line} in a loop", self.Variables.currentLineIndex,
                                     self.Variables.indentations[self.Variables.currentLineIndex] * 4,
                                     end_column=len(self.Variables.currentLine)))
            return ""
        return line + ";"

    def do_value(self, value, after_col=0):
        """
        :param after_col: value is the first occurence of the string value after this  column in the current line
        :param value:
        :return: "",-1 if there is an error
        """
        value = value.strip()
        if len(value) == 0:
            return "", None

        if value.count("'") % 2 == 1:
            self.errors.append(Error("Expected \"'\" after character", self.Variables.currentLineIndex,
                                     self.Variables.currentLine.index(value, start=after_col),
                                     end_column=len(self.Variables.currentLine)))
            return "", -1
        if value.count('"') % 2 == 1:
            self.errors.append(Error("Expected '\"' after string", self.Variables.currentLineIndex,
                                     self.Variables.currentLine.index(value, start=after_col),
                                     end_column=len(self.Variables.currentLine)))
            return "", -1

        if value[0] == '"':
            if value[-1] == '"':
                return value, "string"
        elif value[0] == "'":
            if value[-1] == "'" and len(value) == 3:
                return value, "char"

        value = value.strip()
        valueList = []
        last_function_end = 0
        for i in range(len(value) - 1):
            if value[i + 1] == "(" and value[i] in Constants.VALID_NAME_LETTERS:
                for j in range(i, -1, -1):
                    if j in Constants.ALL_SYNTAX_ELEMENTS:
                        start_col = j + 1

                        break
                else:
                    start_col = 0
                end_col = self.find_closing_bracket_in_value(value, "(", i + 1)
                valueList.append(self.do_value(value[last_function_end:start_col]))
                valueList.append(self.check_function_execution(value[start_col:end_col + 1]))
                last_function_end = end_col + 1
        if len(valueList) > 0:
            valueList.append(self.do_value(value[last_function_end:]))
            # TODO return datatype here
            if not any([x is None or x[1] == -1 for x in valueList]):
                return " ".join([x[0] for x in valueList]), valueList[0][1]
            return "", -1

        # TODO split by operators

        lastsplit = 0
        for i in range(len(value) - 1):
            # check if the value is and with whitespace aroud it
            if value[i] == " " and value[i + 1] != " ":
                if value[lastsplit:i].strip() in Constants.OPERATORS + ["and", "or", "not"]:
                    if value[lastsplit:i].strip() == "and":
                        valueList.append("&&")
                    elif value[lastsplit:i].strip() == "or":
                        valueList.append("||")
                    elif value[lastsplit:i].strip() == "not":
                        valueList.append("!")
                    else:
                        valueList.append(value[lastsplit:i])
                    lastsplit = i + 1
                else:
                    valueList.append(self.do_value(value[lastsplit:i]))
                    lastsplit = i + 1
        if len(valueList) > 0:
            valueList.append(self.do_value(value[lastsplit:]))
            return "".join([x[0] for x in valueList]), valueList[-1][1]

        if value[0] in Constants.NUMBERS:
            for i in range(len(value)):
                if value[i] not in Constants.NUMBERS and value[i] != "." and value[i] != " ":
                    break
            else:
                if "." in value:
                    return value, "float"
                else:
                    return value, "int"
            self.errors.append(Error("Value is not a number", self.Variables.currentLineIndex,
                                     self.Variables.currentLine.index(value),
                                     end_column=len(self.Variables.currentLine)))
            return "", -1

        if value[0] == "-" or value[0] == "+" and value[1] in Constants.NUMBERS:
            for i in range(1, len(value)):
                if value[i] not in Constants.NUMBERS and value[i] != "." and value[i] != " ":
                    break
            else:
                if "." in value:
                    return value, "float"
                else:
                    return value, "int"
            self.errors.append(Error("Value is not a number", self.Variables.currentLineIndex,
                                     self.Variables.currentLine.index(value, after_col),
                                     end_column=len(self.Variables.currentLine)))
            return "", -1

        elif "[" in value and value[-1] == "]":
            start = value.index("[")
            arg, dt = self.variable_in_scope(value[:start], self.Variables.currentLineIndex, after_col=after_col)
            if not dt:
                self.errors.append(Error(f"Variable is not defined in this scope", self.Variables.currentLineIndex,
                                         self.Variables.currentLine.index(value, after_col),
                                         self.Variables.currentLine.index(value, after_col) + len(value)))
                return "", -1

            if dt not in Constants.ITERABLES:
                self.errors.append(Error(f"Can only get element out of iterable type, not out of '{dt}'",
                                         self.Variables.currentLineIndex,
                                         self.Variables.currentLine.index(value, after_col),
                                         end_column=len(value) + self.Variables.currentLine.index(value)))
                return "", -1

            if dt in Constants.PRIMITIVE_ARRAY_TYPES:
                index, dtid = self.do_value(value[start + 1:-1])
                if dtid != "int":
                    self.errors.append(Error(f"Array Index must be int, not '{dtid}'", self.Variables.currentLineIndex,
                                             self.Variables.currentLine.index(value, after_col),
                                             end_column=len(value) + self.Variables.currentLine.index(value)))
                    return "", -1
                return f"{arg}[{index}]", dt[:-2]
            else:
                self.errors.append(Error("Iterable type not yet implemented", self.Variables.currentLineIndex,
                                         self.Variables.currentLine.index(value, after_col),
                                         end_column=len(value) + self.Variables.currentLine.index(value)))

        elif value == "True":
            return "true", "bool"

        elif value == "False":
            return "false", "bool"

        elif s := self.variable_in_scope(value, self.Variables.currentLineIndex, after_col=after_col)[1]:
            return value, s

        elif (f := self.check_function_execution(value)) is not None:
            return f[0], f[1]
        else:
            self.errors.append(Error("Value is not defined", self.Variables.currentLineIndex,
                                     self.Variables.currentLine.index(value, after_col),
                                     end_column=len(self.Variables.currentLine)))
            return "", -1

    def add_variable_to_scope(self, name, datatype, line_index):
        print("add to scope", name, datatype)
        for start, end in self.Variables.scope.keys():
            if start <= line_index <= end and self.Variables.indentations[line_index] == \
                    self.Variables.indentations[start]:
                self.Variables.scope[(start, end)][0].append((name, datatype, line_index))

    def variable_in_scope(self, name, line_index, after_col=0):
        """
        :return: (name, datatype) if variable is in scope, -1,-1 if there is an error
        """
        if "[" in name and name[-1] == "]":
            start = name.index("[")
            index = name[start + 1:-1]
            name = name[:start]
            _, dt = self.variable_in_scope(name, line_index, after_col=after_col)
            if not dt:
                return False, False
            if dt not in Constants.ITERABLES:
                self.errors.append(Error(f"Can only get element out of iterable type, not out of '{dt}'",
                                         self.Variables.currentLineIndex,
                                         self.Variables.currentLine.index(name),
                                         end_column=len(name) + self.Variables.currentLine.index(name)))
                return "", None
            if dt in Constants.PRIMITIVE_ARRAY_TYPES:
                _, dti = self.do_value(index)
                if dti != "int":
                    self.errors.append(Error(f"Array Index must be int, not '{dti}'",
                                             self.Variables.currentLineIndex,
                                             self.Variables.currentLine.index(name) + len(name),
                                             end_column=len(name) + self.Variables.currentLine.index(name) + len(
                                                 index)))
                    return "", None
                return f"{name}[{index}]", dt[:-2]

        for start, end in self.Variables.scope.keys():
            if start <= line_index <= end:
                for i in self.Variables.scope[(start, end)][0]:
                    if i[0] == name and i[2] <= line_index:
                        return i[:2]
        return False, False

    @staticmethod
    def get_line_indentation(line):
        """
        :return: Indentation level of the line ALWAYS ROUNDS DOWN
        """
        return (len(line) - len(line.lstrip())) // Constants.DEFAULT_INDEX_LEVEL

    def do_array_intializer(self, value):
        if not (value[0] == "[" and value[-1] == "]"):
            self.errors.append(Error("Array initializer must start with '[' and end with ']'",
                                     self.Variables.currentLineIndex,
                                     self.Variables.currentLine.index(value),
                                     end_column=len(value) + self.Variables.currentLine.index(value)))
            return "", -1
        args, kwargs = self.do_arguments(value[1:-1])
        if len(kwargs) != 0:
            self.errors.append(
                Error(f"Array initializer can not have keyword arguments (= sign)",
                      self.Variables.currentLineIndex, self.Variables.currentLine.index(value)))
            return -1
        dt = args[0][1]
        if any([x[1] != dt for x in args]):
            self.errors.append(
                Error(f"Array initializer can not have different datatypes at line {self.Variables.currentLineIndex}",
                      self.Variables.currentLineIndex, self.Variables.currentLine.index(value)))
            return "", -1

        return f"{{{', '.join([x[0] for x in args])}}}", dt


class StaticUtils:
    @staticmethod
    def find_closing_bracket_in_value(errors, variables, value, bracket, start_col):
        """
        :param value: the value to search in
        :param bracket: the bracket to search for
        :param start_col: the column to start searching from
        """
        if type(bracket) is not str or len(bracket) != 1:
            raise SyntaxError(f"Bracket has to be a string of length 1")
        if bracket not in "([{":
            raise SyntaxError(f"'{bracket}' is not a valid opening bracket")
        if value[start_col] != bracket:
            raise SyntaxError(f"Value does not start with '{bracket}'")
        closing_bracket = Constants.CLOSING_BRACKETS[bracket]
        bracket_level_1 = 0
        bracket_level_2 = 0
        bracket_level_3 = 0
        if bracket == "(":
            bracket_level_1 = 1
        elif bracket == "[":
            bracket_level_2 = 1
        elif bracket == "{":
            bracket_level_3 = 1
        col = start_col + 1
        while col < len(value):
            if value[col] == Constants.BRACKETS[0]:
                bracket_level_1 += 1
            elif value[col] == Constants.BRACKETS[1]:
                bracket_level_1 -= 1
            elif value[col] == Constants.BRACKETS[2]:
                bracket_level_2 += 1
            elif value[col] == Constants.BRACKETS[3]:
                bracket_level_2 -= 1
            elif value[col] == Constants.BRACKETS[4]:
                bracket_level_3 += 1
            elif value[col] == Constants.BRACKETS[5]:
                bracket_level_3 -= 1
            if value[col] == closing_bracket and bracket_level_1 == 0 and bracket_level_2 == 0 and bracket_level_3 == 0:
                return col
            col += 1

        errors.append(Error(f"No closing bracket found for '{bracket}'",
                            variables.currentLineIndex, variables.currentLine.find(value)))
