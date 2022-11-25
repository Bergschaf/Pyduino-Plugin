from server.compiler.constants import Constants


class Utils:
    def __init__(self, variables, builtins):
        self.Variables = variables
        self.Builtins = builtins

    def reset_sys_variable(self):
        self.Variables.sysVariableIndex = 0

    def next_sys_variable(self):
        self.Variables.sysVariableIndex += 1
        return f"_sys_var_{self.Variables.sysVariableIndex}"

    @staticmethod
    def find_closing_bracket_in_value(value, bracket, start_col):
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
        raise SyntaxError(
            f"No closing bracket found for '{bracket}' at col {start_col}")

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
                closing_bracket = Utils.find_closing_bracket_in_value(argstring, argstring[i], i)
        all_args.append(argstring[last_split:])
        for arg in all_args:
            arg = arg.strip()
            if "=" not in arg:
                if kwargs:
                    raise SyntaxError(f"Positional (=normal) argument after keyword argument")
                args.append(self.do_value(arg))
            else:
                name, value = arg.split("=")
                name = name.strip()
                value = value.strip()
                kwargs[name] = self.do_value(value)
        return args, kwargs

    def do_line(self, line):

        instruction = line.strip()
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
        # TODO ggf fix
        elif "++" in instruction:
            return instruction + ";"

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
            # TODO check if function is defined

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
        line = line.strip()
        datatype = line.split("=")[0].strip().split(" ")[0].strip()
        if datatype in Constants.PRIMITIVE_TYPES:
            name = line.split("=")[0].strip().split(" ")[1].strip()
            value = line.split("=")[1].strip()
            value, dt = self.do_value(value)
            if dt != datatype and dt is not None:
                raise SyntaxError(
                    f"Datatype of '{name}' at line {self.Variables.currentLineIndex} ({dt} is not {datatype})")
            if self.variable_in_scope(name, self.Variables.currentLineIndex):
                raise SyntaxError(f"Variable {name} at line {self.Variables.currentLineIndex} already defined")
            self.add_variable_to_scope(name, datatype, self.Variables.currentLineIndex)
            return f"{datatype} {name} = {value};"
        elif datatype in Constants.PRIMITIVE_ARRAY_TYPES:
            name = line.split("=")[0].strip().split(" ")[1].strip()
            value = line.split("=")[1].strip()
            value, dt = self.do_array_intializer(value)
            if dt != datatype[:-2]:
                raise SyntaxError(
                    f"Datatype of {name} at line {self.Variables.currentLineIndex} ({dt}) is not {datatype}")
            if self.variable_in_scope(name, self.Variables.currentLineIndex):
                raise SyntaxError(f"Variable {name} at line {self.Variables.currentLineIndex} already defined")
            self.add_variable_to_scope(name, datatype, self.Variables.currentLineIndex)
            return f"{datatype[:-2]} {name}[] = {value};"
        else:
            raise SyntaxError(f"Datatype {datatype} at line {self.Variables.currentLineIndex} is not defined")

    def do_variable_assignment(self, line):
        """
        :param line: The complete line of the variable assignment
        :return: The assignment converted to C++
        """
        line = line.strip()
        name = line.split("=")[0].strip()
        value = line.split("=")[1].strip()
        value, dt = self.do_value(value)
        if not self.variable_in_scope(name, self.Variables.currentLineIndex):
            raise SyntaxError(f"Variable {name} at line {self.Variables.currentLineIndex} not defined")
        if dt != self.variable_in_scope(name, self.Variables.currentLineIndex)[1] and dt is not None:
            raise SyntaxError(f"Datatype of {name} at line {self.Variables.currentLineIndex} is not {dt}")
        return f"{name} = {value};"

    def do_if(self, line):
        col_index = line.index("if") + 2
        if line.strip()[-1] == ":":
            row = self.Variables.currentLineIndex
            col = len(line) - 1
            condition = self.do_value(line[col_index + 1:col])[0]
            if self.Variables.indentations[row] + 1 != self.Variables.indentations[row + 1]:
                raise SyntaxError(f"Expected indentation at line {row + 1}, (indentation = 4 Spaces)")
            for i in range(row + 1, self.Variables.totalLineCount):
                if self.Variables.indentations[i] < self.Variables.indentations[row + 1]:
                    end_indentation_index = i - 1
                    break
            else:
                end_indentation_index = self.Variables.totalLineCount - 1
            self.Variables.code_done.append(f"if ({condition}) {{")
            if_code = []
            while self.Variables.currentLineIndex < end_indentation_index:
                self.Variables.currentLineIndex, l = next(self.Variables.iterator)
                if_code.append(self.do_line(l))
            if_code.append("}")
            return "\n".join(if_code)
        else:
            raise SyntaxError(f"Expected ':' at line {self.Variables.currentLineIndex} col {col_index}")

    def do_while(self, line):
        col_index = line.index("while") + 5
        if line.strip()[-1] == ":":
            row = self.Variables.currentLineIndex
            col = len(line) - 1
            condition = self.do_value(line[col_index + 1:col])[0]
            if self.Variables.indentations[row] + 1 != self.Variables.indentations[row + 1]:
                raise SyntaxError(f"Expected indentation at line {row + 1}, (indentation = 4 Spaces)")
            for i in range(row + 1, self.Variables.totalLineCount):
                if self.Variables.indentations[i] < self.Variables.indentations[row + 1]:
                    end_indentation_index = i - 1
                    break
            else:
                end_indentation_index = self.Variables.totalLineCount - 1
            self.Variables.code_done.append(f"while ({condition}) {{")

            while self.Variables.currentLineIndex < end_indentation_index:
                self.Variables.currentLineIndex, l = next(self.Variables.iterator)
                self.Variables.code_done.append(self.do_line(l))
            self.Variables.code_done.append("}")
            return ""
        else:
            raise SyntaxError(f"Expected ':' at line {self.Variables.currentLineIndex} col {col_index}")

    def do_for(self, line):
        col_index = line.index("for") + 3
        if line.strip()[-1] == ":":
            row = self.Variables.currentLineIndex
            elements = [x.strip() for x in line[col_index + 1:-1].split("in")]
            dt = "int[]"
            if len(elements) != 2:
                raise SyntaxError(f"Expected 'in' at line {self.Variables.currentLineIndex} col {col_index}")
            counter_variable = elements[0]
            if self.Variables.indentations[row] + 1 != self.Variables.indentations[row + 1]:
                raise SyntaxError(f"Expected indentation at line {row + 1}, (indentation = 4 Spaces)")
            for i in range(row + 1, self.Variables.totalLineCount):
                if self.Variables.indentations[i] < self.Variables.indentations[row + 1]:
                    end_indentation_index = i - 1
                    break
            else:
                end_indentation_index = self.Variables.totalLineCount - 1

            if elements[1][:5] == "range":
                if elements[1][5] != "(":
                    raise SyntaxError(f"Expected '(' at line {self.Variables.currentLineIndex} col {col_index}")

                range_arguments, range_kwargs = self.do_arguments(elements[1][6:-1])
                if any([x[1] != "int" and x[1] != "short" and x[1] != "long" and x[1] is not None for x in
                        range_arguments]):
                    raise SyntaxError(
                        f"Expected type numeric type (int, short, long) as range argument in line {self.Variables.currentLineIndex}")
                if len(range_kwargs) != 0:
                    raise SyntaxError(
                        f"Unexpected keyword arguments in range function in line {self.Variables.currentLineIndex}")

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
                    raise SyntaxError(
                        f"Expected 1, 2 or 3 arguments in range() at line {self.Variables.currentLineIndex} col {col_index}")

            else:
                val, dt = self.do_value(elements[1])
                if dt in Constants.ITERABLES:

                    for_code = [

                        f"for (int {(sys_var := self.next_sys_variable())} = 0; {sys_var} < sizeof({self.do_value(elements[1])[0]}) / sizeof(*{self.do_value(elements[1])[0]}); {sys_var}++) {{",
                        f"auto {counter_variable} = {self.do_value(elements[1])[0]}[{sys_var}];"]
                else:
                    raise SyntaxError("Expected array or range() in for loop")
            self.add_variable_to_scope(counter_variable, dt[:-2], self.Variables.currentLineIndex)
            [self.Variables.code_done.append(x) for x in for_code]
            while self.Variables.currentLineIndex < end_indentation_index:
                self.Variables.currentLineIndex, l = next(self.Variables.iterator)
                self.Variables.code_done.append(self.do_line(l))
            return "}\n"
        else:
            raise SyntaxError(f"Expected ':' at line {self.Variables.currentLineIndex} col {col_index}")

    def do_value(self, value):
        value = value.strip()
        if len(value) == 0:
            return "", None

        if value.count("'") % 2 == 1:
            raise SyntaxError(f"unterminated char literal ' at line '{self.Variables.currentLineIndex}'")
        if value.count('"') % 2 == 1:
            raise SyntaxError(f"unterminated string literal \" at line '{self.Variables.currentLineIndex}'")

        if value[0] == '"':
            if value[-1] == '"':
                return value, "string"
            raise SyntaxError(f"'{value}' at line '{self.Variables.currentLineIndex}' is not closed")
        elif value[0] == "'":
            if value[2] == "'" and len(value) == 3:
                return value, "char"
            raise SyntaxError(f"'{value}' at line '{self.Variables.currentLineIndex}' is not a valid character")

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
            return " ".join([x[0] for x in valueList]), valueList[0][1]

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
            print(valueList)

            # TODO datatype
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
            raise SyntaxError(f"'{value}' at line {self.Variables.currentLineIndex} is not a number")
        elif value[0] == "-" or value[0] == "+" and value[1] in Constants.NUMBERS:
            for i in range(1, len(value)):
                if value[i] not in Constants.NUMBERS and value[i] != "." and value[i] != " ":
                    break
            else:
                if "." in value:
                    return value, "float"
                else:
                    return value, "int"
            raise SyntaxError(f"'{value}' at line {self.Variables.currentLineIndex} is not a number")

        elif "[" in value and value[-1] == "]":
            start = value.index("[")
            arg, dt = self.variable_in_scope(value[:start], self.Variables.currentLineIndex)
            if dt not in Constants.ITERABLES:
                raise SyntaxError(
                    f"Can only get an Element out of an Iterable, not {dt} at line {self.Variables.currentLineIndex}")
            if dt in Constants.PRIMITIVE_ARRAY_TYPES:
                index, dtid = self.do_value(value[start + 1:-1])
                if dtid != "int":
                    raise SyntaxError(f"Array index can only be int, not {dtid}")
                return f"{arg}[{index}]", dt[:-2]
            else:
                raise SyntaxError(f"Iterable not implemented")

        elif value == "True":
            return "true", "bool"

        elif value == "False":
            return "false", "bool"

        elif (s := self.variable_in_scope(value, self.Variables.currentLineIndex)) is not None:
            return value, s[1]

        elif (f := self.check_function_execution(value)) is not None:
            return f[0], f[1]
        else:
            raise SyntaxError(f"Value '{value}' at line {self.Variables.currentLineIndex} is not defined")

    def add_variable_to_scope(self, name, datatype, line_index):
        for start, end in self.Variables.scope.keys():
            if start <= line_index <= end and self.Variables.indentations[
                line_index] == self.Variables.indentations[start]:
                self.Variables.scope[(start, end)][0].append((name, datatype, line_index))
                return

    def variable_in_scope(self, name, line_index):
        """
        :return: (name, datatype) if variable is in scope, else None
        """
        if "[" in name and name[-1] == "]":
            start = name.index("[")
            index = name[start + 1:-1]
            name = name[:start]
            _, dt = self.variable_in_scope(name, line_index)
            if dt not in Constants.ITERABLES:
                raise SyntaxError(f"Can only assign element to iterable, not to {self.Variables.currentLineIndex}")
            if dt in Constants.PRIMITIVE_ARRAY_TYPES:
                _, dti = self.do_value(index)
                if dti != "int":
                    raise SyntaxError(f"Array index can only be int, not {dti}")
                return f"{name}[{index}]", dt[:-2]

        for start, end in self.Variables.scope.keys():
            if start <= line_index <= end:
                for i in self.Variables.scope[(start, end)][0]:
                    if i[0] == name and i[2] <= line_index:
                        return i[:2]

    @staticmethod
    def get_line_indentation(line):
        """
        :return: Indentation level of the line ALWAYS ROUNDS DOWN
        """
        return (len(line) - len(line.lstrip())) // Constants.DEFAULT_INDEX_LEVEL

    def do_array_intializer(self, value):
        args, kwargs = self.do_arguments(value[1:-1])
        if len(kwargs) != 0:
            raise SyntaxError(
                f"what is an = sign doing in an array intialization? at line {self.Variables.currentLineIndex}")
        dt = args[0][1]
        if any([x[1] != dt for x in args]):
            raise SyntaxError(f"Array at line {self.Variables.currentLineIndex} has different datatypes")
        return f"{{{', '.join([x[0] for x in args])}}}", dt
