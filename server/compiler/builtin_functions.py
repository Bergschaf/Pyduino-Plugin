from server.compiler.constants import Constants
from server.compiler.error import Error
from server.compiler.utils import StaticUtils



class Builtins:
    def __init__(self, variables, errors):
        self.Variables = variables
        self.errors = errors

    def next_sys_variable(self):
        self.Variables.sysVariableIndex += 1
        return f"__sys_var_{self.Variables.sysVariableIndex}"

    def check_builtin(self, function_name, args, kwargs):
        if function_name == "print":
            return self.do_print(args, kwargs)
        elif function_name == "analogRead":
            return self.do_analog_read(args, kwargs)
        elif function_name == "analogWrite":
            return self.do_analog_write(args, kwargs)
        elif function_name == "delay":
            return self.do_delay(args, kwargs)
        elif function_name == "len":
            return self.do_len(args, kwargs)

    def do_len(self, args, kwargs, after_col=0):
        if len(args) != 1 or len(kwargs) > 0:
            self.errors.append(Error(f"Unexpected argument to function 'len'", self.Variables.currentLineIndex,
                                     self.Variables.currentLine.index("(", after_col),
                                     end_column=StaticUtils.find_closing_bracket_in_value(self.errors, self.Variables,
                                                                                          self.Variables.currentLine,
                                                                                          "(",
                                                                                          self.Variables.currentLine.index(
                                                                                              "(",
                                                                                              after_col))))
            return "", True
        arg, dt = args[0]
        if dt not in Constants.ITERABLES:
            self.errors.append(Error(f"Can only determine length of iterable", self.Variables.currentLineIndex,
                                     self.Variables.currentLine.index(arg, after_col),
                                     end_column=self.Variables.currentLine.index(args[0][0], after_col)
                                                + len(arg)))
            return "", True
        if dt in Constants.PRIMITIVE_ARRAY_TYPES:
            return f"sizeof({arg}) / sizeof({arg}[0])", "int", True


class BuiltinsArduino(Builtins):
    def __init__(self, variables, errors):
        super().__init__(variables, errors)
        self.Variables = variables
        self.errors = errors

    def do_analog_read(self, args, kwargs, after_col=0):
        pin, dt = args[0]
        if dt != "int":
            self.errors.append(
                Error(f"'analogRead()' argument 1 must be 'int', not {dt}", self.Variables.currentLineIndex,
                      self.Variables.currentLine.index(f"analogRead", start=after_col) + 11,
                      end_column=self.Variables.currentLine.index(pin,
                                                                  start=self.Variables.currentLine.index(f"analogRead",
                                                                                                         start=after_col))))
            return None, None, True
        if len(args) > 1:
            self.errors.append(
                Error(f"analogRead() takes 1 positional argument but {len(args)} were given",
                      self.Variables.currentLineIndex,
                      self.Variables.currentLine.index(f"analogRead", start=after_col) + 11,
                      end_column=StaticUtils.find_closing_bracket_in_value(self.errors, self.Variables,
                                                                           self.Variables.currentLine, "(",
                                                                           self.Variables.currentLine.index(f"(",
                                                                                                            start=after_col))))

            return None, None, True
        if len(kwargs.keys()) > 0:
            self.errors.append(
                Error(f"analogRead() got an unexpected keyword argument", self.Variables.currentLineIndex,
                      self.Variables.currentLine.index(f"("),
                      end_column=StaticUtils.find_closing_bracket_in_value(self.errors, self.Variables,
                                                                           self.Variables.currentLine, "(",
                                                                           self.Variables.currentLine.index(f"(",
                                                                                                            start=after_col))))
            return None, None, True
        return f"analogRead(A{pin})", "int", True

    def do_analog_write(self, args, kwargs):
        pos_start = self.Variables.currentLine.index("analogWrite")
        pos_end = StaticUtils.find_closing_bracket_in_value(self.errors, self.Variables, self.Variables.currentLine,
                                                            "(",
                                                            self.Variables.currentLine.index("("))
        pin, dt = args[0]
        value, dt2 = args[1]
        if dt != "int" and dt is not None:
            self.errors.append(
                Error(f"analogWrite() argument 1 must be 'int', not {dt}", self.Variables.currentLineIndex,
                      pos_start, end_column=pos_end))
            return "", None, True
        if dt2 != "int" and dt2 is not None:
            self.errors.append(
                Error(f"analogWrite() argument 2 must be 'int', not {dt}", self.Variables.currentLineIndex,
                      pos_start, end_column=pos_end))
            return "", None, True
        if len(args) != 2:
            self.errors.append(
                Error(F"'analogWrite' expects exactly two arguments", self.Variables.currentLineIndex,
                      pos_start, end_column=pos_end))
            return "", None, True
        if len(kwargs.keys()) > 0:
            self.errors.append(
                Error(f"'analogWrite' got an unexpected keyword argument", self.Variables.currentLineIndex,
                      pos_start, end_column=pos_end))
            return "", None, True
        return f"analogWrite({pin}, {value});", "void", True

    def do_print(self, args, kwargs):
        self.Variables.builtins_needed.append("print")
        self.Variables.connection_needed = True
        newline = "true"
        if "newline" in kwargs.keys():
            newline = "false" if not kwargs["newline"] else "true"
            if len(kwargs.keys()) > 1:
                self.errors.append(
                    Error(f"'print' got an unexpected keyword argument", self.Variables.currentLineIndex,
                          self.Variables.currentLine.index("print") + 6, end_column=
                          StaticUtils.find_closing_bracket_in_value(self.errors, self.Variables,
                                                                    self.Variables.currentLine
                                                                    , "(", self.Variables.currentLine.index("("))))
        else:
            if len(kwargs.keys()) > 0:
                self.errors.append(
                    Error(f"'print' got an unexpected keyword argument", self.Variables.currentLineIndex,
                          self.Variables.currentLine.index("print") + 6, end_column=
                          StaticUtils.find_closing_bracket_in_value(self.errors, self.Variables,
                                                                    self.Variables.currentLine
                                                                    , "(", self.Variables.currentLine.index("("))))
        var = self.next_sys_variable()
        # Check if it is possible to convert arguments to string
        self.Variables.code_done.append(
            f"String {var}[] = {{ {', '.join([f'String({arg[0]})' for arg in args])} }};")
        return f"do_print({var}, {len(args)}, {newline})", None, False

    def do_delay(self, args, kwargs):
        self.Variables.builtins_needed.append("delay")
        if args[0][1] != "int":
            self.errors.append(
                Error(f"'delay' argument 1 must be 'int', not {args[0][1]}", self.Variables.currentLineIndex,
                      self.Variables.currentLine.index("delay") + 6, end_column=
                      StaticUtils.find_closing_bracket_in_value(self.errors, self.Variables,
                                                                self.Variables.currentLine
                                                                , "(", self.Variables.currentLine.index("("))))
            return "", None, True
        return f"betterdelay({args[0][0]})", "void", True


class BuiltinsPC(Builtins):
    def __init__(self, variables, errors):
        super().__init__(variables, errors)
        self.Variables = variables
        self.errors = errors

    def do_print(self, args, kwargs):
        newline = "<< endl"
        if "newline" in kwargs.keys():
            newline = "" if kwargs["newline"] == "False" else "<< endl"
            if len(kwargs.keys()) > 1:
                self.errors.append(
                    Error(f"'print' got an unexpected keyword argument", self.Variables.currentLineIndex,
                          self.Variables.currentLine.index("print") + 6, end_column=
                          StaticUtils.find_closing_bracket_in_value(self.errors, self.Variables,
                                                                    self.Variables.currentLine
                                                                    , "(", self.Variables.currentLine.index("("))))

        if len(kwargs.keys()) > 0:
            self.errors.append(
                Error(f"'print' got an unexpected keyword argument", self.Variables.currentLineIndex,
                      self.Variables.currentLine.index("print") + 6, end_column=
                      StaticUtils.find_closing_bracket_in_value(self.errors, self.Variables,
                                                                self.Variables.currentLine
                                                                , "(", self.Variables.currentLine.index("("))))

        res = []
        lastsplit = 0
        space = "<< ' ' <<"
        for i, arg in enumerate(args):
            arg, dt = arg
            if dt in Constants.PRIMITIVE_ARRAY_TYPES:

                if lastsplit < i: res.append(f"cout << {space.join(a[0] for a in args[lastsplit:i])};")
                res.append(f"for (int i = 0; i < sizeof({arg}) / sizeof({arg}[0]); i++) cout << {arg}[i] << ' ';")
                lastsplit = i + 1

        if lastsplit < len(args): res.append(f"cout << {space.join(a[0] for a in args[lastsplit:])};")
        res.append(f"cout {newline};")
        return "".join(res), None, False

    def do_analog_read(self, args, kwargs):
        self.Variables.connection_needed = True
        self.Variables.builtins_needed.append("analogRead")
        pin, dt = args[0]
        if dt != "int":
            self.errors.append(
                Error(f"'analogRead' argument 1 must be 'int', not {dt}", self.Variables.currentLineIndex,
                      self.Variables.currentLine.index("analogRead") + 11, end_column=
                      StaticUtils.find_closing_bracket_in_value(self.errors, self.Variables,
                                                                self.Variables.currentLine
                                                                , "(", self.Variables.currentLine.index("("))))
            return "", None, True
        if len(args) > 1:
            self.errors.append(
                Error(f"'analogRead' takes 1 positional argument but {len(args)} were given",
                      self.Variables.currentLineIndex,
                      self.Variables.currentLine.index("analogRead") + 11, end_column=
                      StaticUtils.find_closing_bracket_in_value(self.errors, self.Variables,
                                                                self.Variables.currentLine
                                                                , "(", self.Variables.currentLine.index("("))))

        if len(kwargs.keys()) > 0:
            self.errors.append(
                Error(f"'analogRead' got an unexpected keyword argument", self.Variables.currentLineIndex,
                      self.Variables.currentLine.index("analogRead") + 11, end_column=
                      StaticUtils.find_closing_bracket_in_value(self.errors, self.Variables,
                                                                self.Variables.currentLine
                                                                , "(", self.Variables.currentLine.index("("))))

        sys_var = self.next_sys_variable()
        code = ["short " + sys_var + ";""arduino.analogRead(" + pin + ", &" + sys_var + ");"]
        [self.Variables.code_done.append(l) for l in code]
        return sys_var, "int", True

    def do_analog_write(self, args, kwargs):
        self.Variables.connection_needed = True
        pin, dt = args[0]
        value, dt2 = args[1]
        if dt != "int" or dt2 != "int":
            self.errors.append(
                Error(f"'analogWrite' argument 1 must be 'int', not {dt}", self.Variables.currentLineIndex,
                      self.Variables.currentLine.index("analogWrite") + 12, end_column=
                      StaticUtils.find_closing_bracket_in_value(self.errors, self.Variables,
                                                                self.Variables.currentLine
                                                                , "(", self.Variables.currentLine.index("("))))
            return "", None, True
        if len(args) != 2:
            self.errors.append(
                Error(f"'analogWrite' takes 2 positional arguments but {len(args)} were given",
                      self.Variables.currentLineIndex,
                      self.Variables.currentLine.index("analogWrite") + 12, end_column=
                      StaticUtils.find_closing_bracket_in_value(self.errors, self.Variables,
                                                                self.Variables.currentLine
                                                                , "(", self.Variables.currentLine.index("("))))

        if len(kwargs.keys()) > 0:
            self.errors.append(
                Error(f"'analogWrite' got an unexpected keyword argument", self.Variables.currentLineIndex,
                      self.Variables.currentLine.index("analogWrite") + 12, end_column=
                      StaticUtils.find_closing_bracket_in_value(self.errors, self.Variables,
                                                                self.Variables.currentLine
                                                                , "(", self.Variables.currentLine.index("("))))
        return f"arduino.analogWrite(char({pin}), char({value}));", "void", True

    def do_delay(self, args, kwargs):
        self.Variables.builtins_needed.append("delay")
        if len(args) != 1:
            self.errors.append(
                Error(f"'delay' takes 1 positional argument but {len(args)} were given",
                      self.Variables.currentLineIndex,
                      self.Variables.currentLine.index("delay") + 6, end_column=
                      StaticUtils.find_closing_bracket_in_value(self.errors, self.Variables,
                                                                self.Variables.currentLine
                                                                , "(", self.Variables.currentLine.index("("))))

        if len(kwargs.keys()) > 0:
            self.errors.append(
                Error(f"'delay' got an unexpected keyword argument", self.Variables.currentLineIndex,
                      self.Variables.currentLine.index("delay") + 6, end_column=
                      StaticUtils.find_closing_bracket_in_value(self.errors, self.Variables,
                                                                self.Variables.currentLine
                                                                , "(", self.Variables.currentLine.index("("))))
        value, dt = args[0]
        print(dt)
        if dt != "int":
            self.errors.append(
                Error(f"'delay' argument 1 must be 'int', not {dt}", self.Variables.currentLineIndex,
                      self.Variables.currentLine.index("delay") + 6, end_column=
                      StaticUtils.find_closing_bracket_in_value(self.errors, self.Variables,
                                                                self.Variables.currentLine
                                                                , "(", self.Variables.currentLine.index("("))))
            return "", None, True
        return f"sleep_for(milliseconds({value}));", "void", True
