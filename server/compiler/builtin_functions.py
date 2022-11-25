from server.compiler.constants import Constants

class Builtins:
    def __init__(self, variables):
        self.Variables = variables
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
            return self.do_len(args,kwargs)

    def do_len(self, args, kwargs):
        if len(args) != 1 or len(kwargs) > 0:
            raise SyntaxError(f"Unexpected argument to function 'len' at line {self.Variables.currentLineIndex}")
        arg, dt = args[0]
        if dt not in Constants.ITERABLES:
            raise SyntaxError(f"Can only determine length of iterable")
        if dt in Constants.PRIMITIVE_ARRAY_TYPES:
            return f"sizeof({arg}) / sizeof({arg}[0])", True


class BuiltinsArduino(Builtins):
    def __init__(self, variables):
        super().__init__(variables)
        self.Variables = variables


    def do_analog_read(self, args, kwargs):
        pin, dt = args[0]
        if dt != "int":
            raise Exception("analogRead() argument 1 must be 'int', not " + dt)
        if len(args) > 1:
            raise Exception("analogRead() takes exactly 1 argument")
        if len(kwargs.keys()) > 0:
            raise Exception("analogRead() got an unexpected keyword argument")
        return f"analogRead(A{pin})", "int", True

    def do_analog_write(self, args, kwargs):
        pin, dt = args[0]
        value, dt2 = args[1]
        if dt != "int" and dt is not None:
            raise Exception("analogWrite() arguments  must be 'int', not " + dt)
        if dt2 != "int" and dt2 is not None:
            raise Exception("analogWrite() arguments  must be 'int', not " + dt2)
        if len(args) > 2:
            raise Exception("analogWrite() takes exactly 2 arguments")
        if len(kwargs.keys()) > 0:
            raise Exception("analogWrite() got an unexpected keyword argument")
        return f"analogWrite({pin}, {value});", "void", True

    def do_print(self, args, kwargs):
        self.Variables.builtins_needed.append("print")
        self.Variables.connection_needed = True
        newline = "true"
        if "newline" in kwargs.keys():
            newline = "false" if not kwargs["newline"] else "true"
            if len(kwargs.keys()) > 1:
                raise Exception("print() got an unexpected keyword argument")
        else:
            if len(kwargs.keys()) > 0:
                raise Exception("print() got an unexpected keyword argument")
        var = self.next_sys_variable()
        self.Variables.code_done.append(
            f"String {var}[] = {{ {', '.join([f'String({arg[0]})' for arg in args])} }};")
        return f"do_print({var}, {len(args)}, {newline})", None, False

    def do_delay(self, args, kwargs):
        self.Variables.builtins_needed.append("delay")
        if args[0][1] != "int":
            raise Exception("delay() argument 1 must be 'int', not " + args[0][1])
        return f"betterdelay({args[0][0]})", "void", True


class BuiltinsPC(Builtins):
    def __init__(self, variables):
        super().__init__(variables)
        self.Variables = variables

    def do_print(self, args, kwargs):
        newline = "<< endl"
        if "newline" in kwargs.keys():
            newline = "" if kwargs["newline"] == "False" else "<< endl"
            if len(kwargs.keys()) > 1:
                raise Exception("print() got an unexpected keyword argument")
        else:
            if len(kwargs.keys()) > 0:
                raise Exception("print() got an unexpected keyword argument")
        res = []
        lastsplit = 0
        space = "<< ' ' <<"
        for i,arg in enumerate(args):
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
            raise Exception("analogRead() argument 1 must be 'int', not " + dt)
        if len(args) > 1:
            raise Exception("analogRead() takes exactly 1 argument")
        if len(kwargs.keys()) > 0:
            raise Exception("analogRead() got an unexpected keyword argument")
        sys_var = self.next_sys_variable()
        code = ["short " + sys_var + ";""arduino.analogRead(" + pin + ", &" + sys_var + ");"]
        [self.Variables.code_done.append(l) for l in code]
        return sys_var, "int", True

    def do_analog_write(self, args, kwargs):
        self.Variables.connection_needed = True
        pin, dt = args[0]
        value, dt2 = args[1]
        if dt != "int" or dt2 != "int":
            raise Exception("analogWrite() arguments  must be 'int', not " + dt)
        if len(args) > 2:
            raise Exception("analogWrite() takes exactly 2 arguments")
        if len(kwargs.keys()) > 0:
            raise Exception("analogWrite() got an unexpected keyword argument")
        return f"arduino.analogWrite(char({pin}), char({value}));", "void", True

    def do_delay(self, args, kwargs):
        self.Variables.builtins_needed.append("delay")
        return f"sleep_for(milliseconds({args[0][0]}));", "void", True
