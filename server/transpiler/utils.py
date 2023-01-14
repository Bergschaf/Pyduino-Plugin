from server.transpiler.constants import Constants
from server.transpiler.error import Error


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
                                 self.Variables.currentLineIndex, self.Variables.currentLine.find(value),
                                 line_offset=self.line_offset))

    def do_arguments(self, argstring, after_col=0):
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
            if " = " not in arg:  # TODO accept kwargs if = is without spaces
                if kwargs:
                    self.errors.append(Error(f"Non-keyword argument '{arg}' after keyword argument",
                                             self.Variables.currentLineIndex,
                                             self.Variables.currentLine.find(arg, after_col),
                                             line_offset=self.line_offset))

                args.append(self.do_value(arg))
            else:
                name, value = arg.split("=")
                name = name.strip()
                value = value.strip()
                kwargs[name] = self.do_value(value)
        return args, kwargs

    def do_line(self, line):
        self.Variables.currentLine = line
        instruction = line.strip()
        if instruction == "":
            return ""

        if self.get_line_indentation(line) != self.Variables.inIndentation:
            self.errors.append(
                Error(f"Indentation error", self.Variables.currentLineIndex, 0, line_offset=self.line_offset))

        if (len(line) - len(line.lstrip())) % Constants.DEFAULT_INDEX_LEVEL != 0:
            self.errors.append(
                Error(f"Indentation error", self.Variables.currentLineIndex, 0, line_offset=self.line_offset))
        if instruction == "":
            return ""
        self.Variables.currentColumnIndex = line.find(instruction)
        if instruction[0] == "#":
            return ""
        elif any([instruction.startswith(i) for i in
                  Constants.PRIMITIVE_TYPES + Constants.PRIMITIVE_ARRAY_TYPES]):
            if (f := self.check_function_definition(instruction)) is not None:
                return f
            else:
                return self.do_variable_definition(instruction)
        elif (f := self.check_function_execution(instruction)) is not None:
            return f[0]
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
                                     self.Variables.currentLineIndex, 0, end_column=len(self.Variables.currentLine),
                                     line_offset=self.line_offset))
            return ""

    def check_function_definition(self, line):
        pass

    def check_function_execution(self, value, value_used=True):
        value = value.strip()
        if "(" not in value:
            return
        first_bracket = value.find("(")
        function_name = value[:first_bracket]

        second_bracket = self.find_closing_bracket_in_value(value, "(", first_bracket)
        if second_bracket is None:
            return
        if second_bracket != len(value) - 1:
            return
        arguments = value[first_bracket + 1:second_bracket]
        # TODO was wenn , in arguemtns?
        args, kwargs = self.do_arguments(arguments)
        if (f := self.Builtins.check_builtin(function_name, args, kwargs)) is not None:
            # and f[2]: TODO only let functions like cout through if the return value isn'T used  (value used kwarg)
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
                                     self.Variables.currentLineIndex, self.Variables.currentLine.find(line),
                                     line_offset=self.line_offset))
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
                                             self.Variables.currentLine.find(line), line_offset=self.line_offset))
                    return ""
            if self.variable_in_scope(name, self.Variables.currentLineIndex)[1]:
                self.errors.append(Error(f"Variable '{name}' already defined in this scope",
                                         self.Variables.currentLineIndex, self.Variables.currentLine.find(name),
                                         line_offset=self.line_offset))
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
                                             self.Variables.currentLine.find(line), line_offset=self.line_offset))
            if self.variable_in_scope(name, self.Variables.currentLineIndex)[1]:
                self.errors.append(Error(f"Variable '{name}' already defined in this scope",
                                         self.Variables.currentLineIndex, self.Variables.currentLine.find(name),
                                         line_offset=self.line_offset))
                return ""
            self.add_variable_to_scope(name, datatype, self.Variables.currentLineIndex)
            return f"{datatype[:-2]} {name}[] = {value};"
        else:
            self.errors.append(Error(f"Datatype '{datatype}' not supported", self.Variables.currentLineIndex,
                                     self.Variables.currentLine.find(datatype), line_offset=self.line_offset))
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
                                     self.Variables.currentLine.find(name), line_offset=self.line_offset))
            return ""
        if dt != self.variable_in_scope(name, self.Variables.currentLineIndex)[1] and dt is not None:
            self.errors.append(
                Error(f"Datatype mismatch: {self.variable_in_scope(name, self.Variables.currentLineIndex)[1]} != {dt}",
                      self.Variables.currentLineIndex, self.Variables.currentLine.find(line),
                      line_offset=self.line_offset))
            return ""
        return f"{name} = {value};"

    def do_if(self, line):
        col_index = line.find("if") + 2

        if line.strip()[-1] != ":":
            self.errors.append(
                Error("Expected ':' after if", self.Variables.currentLineIndex, len(self.Variables.currentLine) - 1,
                      line_offset=self.line_offset))

        row = self.Variables.currentLineIndex
        col = len(line) - 1
        condition = self.do_value(line[col_index + 1:col])[0]
        if self.Variables.indentations[row] + 1 != self.Variables.indentations[row + 1]:
            self.errors.append(Error("Expected indentation", row + 1, self.Variables.indentations[row + 1] * 4 + 1,
                                     line_offset=self.line_offset))
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
        self.Variables.code_done.extend(if_code)
        if_code.clear()
        # check for elif
        while True:
            if self.Variables.currentLineIndex < self.Variables.totalLineCount - 1:
                if self.Variables.code[self.Variables.currentLineIndex + 1].strip().startswith("elif"):
                    row = self.Variables.currentLineIndex + 1
                    if self.Variables.indentations[row] + 1 != self.Variables.indentations[row + 1]:
                        self.errors.append(
                            Error("Expected indentation", row + 1, self.Variables.indentations[row + 1] * 4 + 1,
                                  line_offset=self.line_offset))
                        return ""
                    for i in range(row + 1, self.Variables.totalLineCount):
                        if self.Variables.indentations[i] < self.Variables.indentations[row + 1]:
                            end_indentation_index = i - 1
                            break
                    else:
                        end_indentation_index = self.Variables.totalLineCount - 1

                    self.Variables.currentLineIndex, self.Variables.currentLine = next(self.Variables.iterator)
                    self.Variables.currentLine = self.Variables.code[self.Variables.currentLineIndex]
                    condition = self.do_value(
                        self.Variables.currentLine[self.Variables.currentLine.find("elif") + 4:].strip()[:-1])[0]
                    self.Variables.code_done.append(f"else if ({condition}){{")
                    self.Variables.inIndentation += 1
                    while self.Variables.currentLineIndex < end_indentation_index:
                        self.Variables.currentLineIndex, l = next(self.Variables.iterator)
                        if_code.append(self.do_line(l))
                    self.Variables.inIndentation -= 1
                    if_code.append("}")
                    self.Variables.code_done.extend(if_code)
                    if_code.clear()
                else:
                    break
            else:
                break
        # check for else
        if self.Variables.currentLineIndex < self.Variables.totalLineCount - 1:
            if self.Variables.code[self.Variables.currentLineIndex + 1].strip().startswith("else"):
                row = self.Variables.currentLineIndex + 1
                if self.Variables.indentations[row] + 1 != self.Variables.indentations[row + 1]:
                    self.errors.append(
                        Error("Expected indentation", row + 1, self.Variables.indentations[row + 1] * 4 + 1,
                              line_offset=self.line_offset))
                    return ""
                for i in range(row + 1, self.Variables.totalLineCount):
                    if self.Variables.indentations[i] < self.Variables.indentations[row + 1]:
                        end_indentation_index = i - 1
                        break
                else:
                    end_indentation_index = self.Variables.totalLineCount - 1

                self.Variables.currentLineIndex, self.Variables.currentLine = next(self.Variables.iterator)
                self.Variables.currentLine = self.Variables.code[self.Variables.currentLineIndex]
                self.Variables.code_done.append("else {")
                self.Variables.inIndentation += 1
                while self.Variables.currentLineIndex < end_indentation_index:
                    self.Variables.currentLineIndex, l = next(self.Variables.iterator)
                    if_code.append(self.do_line(l))
                self.Variables.inIndentation -= 1
                if_code.append("}")
        return "\n".join(if_code)

    def do_while(self, line):
        col_index = line.find("while") + 5
        if line.strip()[-1] != ":":
            self.errors.append(
                Error("Expected ':' after while", self.Variables.currentLineIndex, len(self.Variables.currentLine) - 1,
                      line_offset=self.line_offset))

        row = self.Variables.currentLineIndex
        col = len(line) - 1
        condition = self.do_value(line[col_index + 1:col])[0]
        if self.Variables.indentations[row] + 1 != self.Variables.indentations[row + 1]:
            self.errors.append(Error("Expected indentation", row + 1, self.Variables.indentations[row + 1] * 4 + 1,
                                     line_offset=self.line_offset))
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
        col_index = line.find("for") + 3
        if line.strip()[-1] != ":":
            self.errors.append(
                Error("Expected ':' after for", self.Variables.currentLineIndex, len(self.Variables.currentLine) - 1,
                      line_offset=self.line_offset))

        row = self.Variables.currentLineIndex
        elements = [x.strip() for x in line[col_index + 1:-1].split("in")]
        dt = "int[]"
        if len(elements) != 2:
            self.errors.append(Error("Expected 'in' in for loop", self.Variables.currentLineIndex,
                                     self.Variables.currentLine.find("for"),
                                     end_column=len(self.Variables.currentLine), line_offset=self.line_offset))
            return ""

        counter_variable = elements[0]
        if self.Variables.indentations[row] + 1 != self.Variables.indentations[row + 1]:
            self.errors.append(Error("Expected indentation", row + 1, self.Variables.indentations[row + 1] * 4 + 1,
                                     line_offset=self.line_offset))
            return ""
        for i in range(row + 1, self.Variables.totalLineCount):
            if self.Variables.indentations[i] < self.Variables.indentations[row + 1]:
                end_indentation_index = i - 1
                break
        else:
            end_indentation_index = self.Variables.totalLineCount - 1

        range_three = False # range has three arguments
        if elements[1][:5] == "range":
            if elements[1][5] != "(":
                self.errors.append(Error("Expected '(' after range", self.Variables.currentLineIndex,
                                         self.Variables.currentLineIndex, len(self.Variables.currentLine) - 1,
                                         line_offset=self.line_offset))
                elements[1] += ")"
            range_arguments, range_kwargs = self.do_arguments(elements[1][6:-1])
            if any([x[1] != "int" and x[1] != "short" and x[1] != "long" and x[1] is not None for x in
                    range_arguments]):
                self.errors.append(
                    Error("Expected int, short or long as argument in 'range'", self.Variables.currentLineIndex
                          , self.Variables.currentLine.find("range") + 5,
                          end_column=len(self.Variables.currentLine) - 2, line_offset=self.line_offset))
                return ""
            if len(range_kwargs) != 0:
                self.errors.append(Error("Expected no keyword arguments in 'range'", self.Variables.currentLineIndex,
                                         self.Variables.currentLine.find("range") + 5,
                                         end_column=len(self.Variables.currentLine) - 2, line_offset=self.line_offset))
                return ""

            if len(range_arguments) == 1:
                for_code = [
                    f"for (int {counter_variable} = 0; {counter_variable} < {range_arguments[0][0]} ; {counter_variable}++) {{"]
            elif len(range_arguments) == 2:
                for_code = [
                    f"for (int {counter_variable} = {range_arguments[0][0]}; {counter_variable} < {range_arguments[1][0]} ; {counter_variable}++) {{"]
            elif len(range_arguments) == 3:
                # should also work if the third argument is negative and the first argument is greater than the second
                range_three = True
                for_code = [
                    f"if ({range_arguments[0][0]} < {range_arguments[1][0]}) {{",
                    f"for (int {counter_variable} = {range_arguments[0][0]}; {counter_variable} < {range_arguments[1][0]} ; {counter_variable} += {range_arguments[2][0]}) {{"]

            else:
                self.errors.append(Error("Expected 1 or 2 arguments in 'range'", self.Variables.currentLineIndex,
                                         self.Variables.currentLine.find("range") + 5,
                                         end_column=len(self.Variables.currentLine) - 2, line_offset=self.line_offset))
                for_code = []
        else:
            val, dt = self.do_value(elements[1])
            if dt in Constants.ITERABLES:

                for_code = [
                    f"for (int {(sys_var := self.next_sys_variable())} = 0; {sys_var} < sizeof({self.do_value(elements[1])[0]}) / sizeof(*{self.do_value(elements[1])[0]}); {sys_var}++) {{",
                    f"auto {counter_variable} = {self.do_value(elements[1])[0]}[{sys_var}];"]
            else:
                self.errors.append(Error("Expected 'range' or iterable after for", self.Variables.currentLineIndex,
                                         self.Variables.currentLine.find("for"),
                                         end_column=len(self.Variables.currentLine), line_offset=self.line_offset))
                for_code = []
        if dt != -1:
            self.add_variable_to_scope(counter_variable, dt[:-2], self.Variables.currentLineIndex)
        [self.Variables.code_done.append(x) for x in for_code]
        self.Variables.inLoop += 1
        self.Variables.inIndentation += 1
        start_len = len(self.Variables.code_done)
        while self.Variables.currentLineIndex < end_indentation_index:
            self.Variables.currentLineIndex, l = next(self.Variables.iterator)
            self.Variables.code_done.append(self.do_line(l))

        if range_three:
            self.Variables.code_done.extend(["}", "}", "else {", f"for (int {counter_variable} = {range_arguments[0][0]}; {counter_variable} > {range_arguments[1][0]} ; {counter_variable} += {range_arguments[2][0]}) {{"])
            self.Variables.code_done.extend(self.Variables.code_done[start_len:-4])
            self.Variables.code_done.append("}")

        self.Variables.inLoop -= 1
        self.Variables.inIndentation -= 1
        return "}\n"

    def do_break_continue(self, line):
        if 0 == self.Variables.inLoop:
            self.errors.append(Error(f"Can only {line} in a loop", self.Variables.currentLineIndex,
                                     self.Variables.indentations[self.Variables.currentLineIndex] * 4,
                                     end_column=len(self.Variables.currentLine), line_offset=self.line_offset))
            return ""
        return line + ";"

    def do_operation(self, left, right, operator, after_col=0):
        if operator[1] != "operator":
            self.errors.append(Error(f"Expected operator, got {operator[0]}", self.Variables.currentLineIndex,
                                     self.Variables.currentLine.find(operator[0], after_col),
                                     line_offset=self.line_offset))

        if operator[0] in Constants.COMPAIRSON:
            if left[1] in Constants.NUMERIC_TYPES and right[1] in Constants.NUMERIC_TYPES:
                return f"({left[0]} {operator[0]} {right[0]})", "bool"
            else:
                self.errors.append(
                    Error(f"Expected numeric types, got {left[1]} and {right[1]}", self.Variables.currentLineIndex,
                          self.Variables.currentLine.find(operator[0], after_col), line_offset=self.line_offset))
        operator = operator[0]

        if left[1] == "int" and right[1] == "int" and operator in Constants.ARITHMETIC_OPERATORS:
            if (operator == "/" or operator == "//") and right[0] == "0":
                self.errors.append(Error("Division by zero", self.Variables.currentLineIndex,
                                         self.Variables.currentLine.find(left[0], after_col) + len(left[0]),
                                         end_column=self.Variables.currentLine.find(right[0], after_col) + len(
                                             right[0]), line_offset=self.line_offset))
                return "", "float"
            if operator == "/":
                return f"((float){left[0]} / (float){right[0]})", "float"
            if operator == "//":
                return f"{left[0]} / {right[0]}", "int"
            if operator == "**":
                return f"pow({left[0]}, {right[0]})", "float"
            return f"{left[0]} {operator} {right[0]}", "int"
        elif left[1] == "float" or right[1] == "float" and operator in Constants.ARITHMETIC_OPERATORS:
            if (operator == "%" or operator == "//") and right[1] == "float":
                self.errors.append(Error("Can't use floor division or modulo with float as second argument",
                                         self.Variables.currentLineIndex,
                                         self.Variables.currentLine.find(right[0], after_col),
                                         end_column=self.Variables.currentLine.find(right[0], after_col) + len(
                                             right[0]), line_offset=self.line_offset))
                return "", "int"
            if operator == "//":
                return f"floor({left[0]} / {right[0]})", "int"
            if operator == "**":
                return f"pow({left[0]}, {right[0]})", "float"
            return f"(float){left[0]} {operator} (float){right[0]}", "float"

        elif left[1] == "bool" and right[1] == "bool":
            if operator in Constants.BOOLEAN_OPERATORS:
                return f"({left[0]} {operator} {right[0]})", "bool"
            else:
                self.errors.append(Error("Can't use operator on booleans", self.Variables.currentLineIndex,
                                         self.Variables.currentLine.find(left[0], after_col) + len(left[0]),
                                         end_column=self.Variables.currentLine.find(right[0], after_col) + len(
                                             right[0]), line_offset=self.line_offset))
            return "", "bool"
        self.errors.append(Error("Can't use operator on these types", self.Variables.currentLineIndex,
                                 self.Variables.currentLine.find(left[0], after_col) + len(left[0]),
                                 end_column=self.Variables.currentLine.find(right[0], after_col) + len(right[0]),
                                 line_offset=self.line_offset))
        return "", None

    def do_value(self, value, after_col=0):
        """
        :param after_col: value is the first occurence of the string value after this  column in the current line
        :param value:
        :return: "",-1 if there is an error
        """
        value = value.strip()
        if len(value) == 0:
            return "", None

        if self.check_function_execution(value) is not None:
            return self.check_function_execution(value)


        if value.count("'") % 2 == 1:
            self.errors.append(Error("Expected \"'\" after character", self.Variables.currentLineIndex,
                                     self.Variables.currentLine.find(value, after_col),
                                     end_column=len(self.Variables.currentLine), line_offset=self.line_offset))
            return "", -1
        if value.count('"') % 2 == 1:
            self.errors.append(Error("Expected '\"' after string", self.Variables.currentLineIndex,
                                     self.Variables.currentLine.find(value, after_col),
                                     end_column=len(self.Variables.currentLine), line_offset=self.line_offset))
            return "", -1

        if value[0] == '"':
            if value[-1] == '"':
                return value, "string"
        elif value[0] == "'":
            if value[-1] == "'" and len(value) == 3:
                return value, "char"

        value = value.replace(" and ", "&&")
        value = value.replace(" or ", "||")
        value = value.replace(" not ", "!")
        value = value.replace(" ", "")
        valueList = []
        lastsplit = 0
        iterator = iter(range(len(value)))
        for i in iterator:
            if i + 1 < len(value) and value[i + 1] == "(" and value[i] in Constants.VALID_NAME_LETTERS:
                if lastsplit != i:
                    valueList.append(self.do_value(value[lastsplit:i]))

                for j in range(i, -1, -1):
                    if value[j] in Constants.ALL_SYNTAX_ELEMENTS:
                        start_col = j + 1
                        break
                else:
                    start_col = 0
                end_col = self.find_closing_bracket_in_value(value, "(", i + 1)
                valueList.append(self.check_function_execution(value[start_col:end_col + 1]))
                lastsplit = end_col + 1
                while i < lastsplit:
                    i = next(iterator)

            elif i + 2 < len(value) and value[
                                        i:i + 2] in Constants.CONDITION_OPERATORS_LEN2 + Constants.ARITHMETIC_OPERATORS_LEN2:
                if lastsplit != i:
                    valueList.append(self.do_value(value[lastsplit:i]))
                valueList.append((value[i:i + 2], "operator"))
                lastsplit = i + 2
                next(iterator)
            elif value[i] in Constants.CONDITION_OPERATORS_LEN1 + Constants.ARITHMETIC_OPERATORS_LEN1 + ["(", ")"]:
                if lastsplit != i:
                    valueList.append(self.do_value(value[lastsplit:i]))
                valueList.append((value[i], "operator"))
                lastsplit = i + 1

        if len(valueList) > 0:
            if value[lastsplit:] != "":
                if value[lastsplit:] == ")":
                    valueList.append(("(", "operator"))
                elif lastsplit != len(value):
                    valueList.append(self.do_value(value[lastsplit:]))
            if "(" in [x[0] for x in valueList]:
                newValueList = []
                lastsplit = 0
                iterator = iter(range(len(valueList)))
                for i in iterator:
                    if valueList[i][0] == "(":
                        closing_bracket = self.find_closing_bracket_in_value([x[0] for x in valueList], "(", i)
                        for ii in range(lastsplit, i):
                            newValueList.append(valueList[ii])
                        value, dt = self.do_value("".join([x[0] for x in valueList[i + 1:closing_bracket]]))
                        newValueList.append((f"({value})", dt))
                        lastsplit = closing_bracket + 1
                        for _ in range(i, closing_bracket):
                            next(iterator)
                for i in range(lastsplit, len(valueList)):
                    newValueList.append(valueList[i])
                valueList = newValueList.copy()
            for o in Constants.OPERATION_ORDER:
                while True:
                    for i in range(len(valueList)-1):
                        if valueList[i][1] == "operator" and valueList[i][0] in o:
                            # Negation
                            if (valueList[i-1][0] in "()" or i == 0) and valueList[i][0] in "+-":
                                if valueList[i+1][1] in Constants.NUMERIC_TYPES:
                                    valueList[i+1] = (f"{valueList[i][0]}({valueList[i + 1][0]})", valueList[i+1][1])
                                    del valueList[i]
                                else:
                                    self.errors.append(Error("Can't negate this type", self.Variables.currentLineIndex,
                                                             self.Variables.currentLine.find(valueList[i][0], after_col),
                                                             end_column=self.Variables.currentLine.find(valueList[i][0], after_col) + len(valueList[i][0]),
                                                             line_offset=self.line_offset))
                                break
                            # Normal operation
                            res = self.do_operation(valueList[i - 1], valueList[i + 1], valueList[i])
                            valueList[i - 1] = res
                            del valueList[i + 1]
                            del valueList[i]
                            break
                    else:
                        break
            return valueList[0][0], valueList[0][1]

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
                                     self.Variables.currentLine.find(value),
                                     end_column=len(self.Variables.currentLine), line_offset=self.line_offset))
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
                                     self.Variables.currentLine.find(value, after_col),
                                     end_column=len(self.Variables.currentLine), line_offset=self.line_offset))
            return "", -1

        elif "[" in value and value[-1] == "]":
            start = value.find("[")
            arg, dt = self.variable_in_scope(value[:start], self.Variables.currentLineIndex, after_col=after_col)
            if not dt:
                self.errors.append(Error(f"Variable is not defined in this scope", self.Variables.currentLineIndex,
                                         self.Variables.currentLine.find(value, after_col),
                                         self.Variables.currentLine.find(value, after_col) + len(value),
                                         line_offset=self.line_offset))
                return "", -1

            if dt not in Constants.ITERABLES:
                self.errors.append(Error(f"Can only get element out of iterable type, not out of '{dt}'",
                                         self.Variables.currentLineIndex,
                                         self.Variables.currentLine.find(value, after_col),
                                         end_column=len(value) + self.Variables.currentLine.find(value)))
                return "", -1

            if dt in Constants.PRIMITIVE_ARRAY_TYPES:
                index, dtid = self.do_value(value[start + 1:-1])
                if dtid != "int":
                    self.errors.append(Error(f"Array Index must be int, not '{dtid}'", self.Variables.currentLineIndex,
                                             self.Variables.currentLine.find(value, after_col),
                                             end_column=len(value) + self.Variables.currentLine.find(value),
                                             line_offset=self.line_offset))
                    return "", -1
                return f"{arg}[{index}]", dt[:-2]
            else:
                self.errors.append(Error("Iterable type not yet implemented", self.Variables.currentLineIndex,
                                         self.Variables.currentLine.find(value, after_col),
                                         end_column=len(value) + self.Variables.currentLine.find(value),
                                         line_offset=self.line_offset))

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
                                     self.Variables.currentLine.find(value, after_col),
                                     end_column=len(self.Variables.currentLine), line_offset=self.line_offset))
            return "", -1

    def add_variable_to_scope(self, name, datatype, line_index):
        for start, end in self.Variables.scope.keys():
            if start <= line_index <= end and self.Variables.indentations[line_index] == \
                    self.Variables.indentations[start]:
                self.Variables.scope[(start, end)][0].append((name, datatype, line_index))

    def variable_in_scope(self, name, line_index, after_col=0):
        """
        :return: (name, datatype) if variable is in scope, -1,-1 if there is an error
        """
        if "[" in name and name[-1] == "]":
            start = name.find("[")
            index = name[start + 1:-1]
            name = name[:start]
            _, dt = self.variable_in_scope(name, line_index, after_col=after_col)
            if not dt:
                return False, False
            if dt not in Constants.ITERABLES:
                self.errors.append(Error(f"Can only get element out of iterable type, not out of '{dt}'",
                                         self.Variables.currentLineIndex,
                                         self.Variables.currentLine.find(name),
                                         end_column=len(name) + self.Variables.currentLine.find(name),
                                         line_offset=self.line_offset))
                return "", None
            if dt in Constants.PRIMITIVE_ARRAY_TYPES:
                _, dti = self.do_value(index)
                if dti != "int":
                    self.errors.append(Error(f"Array Index must be int, not '{dti}'",
                                             self.Variables.currentLineIndex,
                                             self.Variables.currentLine.find(name) + len(name),
                                             end_column=len(name) + self.Variables.currentLine.find(name) + len(
                                                 index), line_offset=self.line_offset))
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
                                     self.Variables.currentLine.find(value),
                                     end_column=len(value) + self.Variables.currentLine.find(value),
                                     line_offset=self.line_offset))
            return "", -1
        args, kwargs = self.do_arguments(value[1:-1])
        if len(kwargs) != 0:
            self.errors.append(
                Error(f"Array initializer can not have keyword arguments (= sign)",
                      self.Variables.currentLineIndex, self.Variables.currentLine.find(value),
                      line_offset=self.line_offset))
            return -1
        dt = args[0][1]
        if any([x[1] != dt for x in args]):
            self.errors.append(
                Error(f"Array initializer can not have different datatypes at line {self.Variables.currentLineIndex}",
                      self.Variables.currentLineIndex, self.Variables.currentLine.find(value),
                      line_offset=self.line_offset))
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
