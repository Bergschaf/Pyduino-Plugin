############################################################################
# Copyright(c) Open Law Library. All rights reserved.                      #
# See ThirdPartyNotices.txt in the project root for additional notices.    #
#                                                                          #
# Licensed under the Apache License, Version 2.0 (the "License")           #
# you may not use this file except in compliance with the License.         #
# You may obtain a copy of the License at                                  #
#                                                                          #
#     http: // www.apache.org/licenses/LICENSE-2.0                         #
#                                                                          #
# Unless required by applicable law or agreed to in writing, software      #
# distributed under the License is distributed on an "AS IS" BASIS,        #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. #
# See the License for the specific language governing permissions and      #
# limitations under the License.                                           #
############################################################################
import asyncio
import re
import time
import uuid
from typing import Optional

from pygls.lsp.methods import (COMPLETION, TEXT_DOCUMENT_DID_CHANGE,
                               TEXT_DOCUMENT_DID_CLOSE, TEXT_DOCUMENT_DID_OPEN, 
                               TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL,TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
from pygls.lsp.types import (CompletionItem, CompletionList, CompletionOptions,
                             CompletionParams, ConfigurationItem,
                             ConfigurationParams, Diagnostic,
                             DidChangeTextDocumentParams,
                             DidCloseTextDocumentParams,
                             DidOpenTextDocumentParams, MessageType, Position,
                             Range, Registration, RegistrationParams,
                             SemanticTokens, SemanticTokensLegend, SemanticTokensParams,
                             Unregistration, UnregistrationParams)
from pygls.lsp.types.basic_structures import (WorkDoneProgressBegin, 
                                              WorkDoneProgressEnd,
                                              WorkDoneProgressReport)
from pygls.server import LanguageServer

from compiler import Compiler
print("Starting server...")

COUNT_DOWN_START_IN_SECONDS = 10
COUNT_DOWN_SLEEP_IN_SECONDS = 1


class PyduinoLanguageServer(LanguageServer):
    CMD_COUNT_DOWN_BLOCKING = 'countDownBlocking'
    CMD_COUNT_DOWN_NON_BLOCKING = 'countDownNonBlocking'
    CMD_PROGRESS = 'progress'
    CMD_REGISTER_COMPLETIONS = 'registerCompletions'
    CMD_SHOW_CONFIGURATION_ASYNC = 'showConfigurationAsync'
    CMD_SHOW_CONFIGURATION_CALLBACK = 'showConfigurationCallback'
    CMD_SHOW_CONFIGURATION_THREAD = 'showConfigurationThread'
    CMD_UNREGISTER_COMPLETIONS = 'unregisterCompletions'


    CONFIGURATION_SECTION = 'pyduinoServer'

    def __init__(self, *args):
        super().__init__(*args)


json_server = PyduinoLanguageServer('pygls-pyduino-example', 'v0.1')

def _validate(ls, params):

    text_doc = ls.workspace.get_document(params.text_document.uri)

    source = text_doc.source
    print("validating",source)

    diagnostics = _validate_pyduino(source) if source else []

    ls.publish_diagnostics(text_doc.uri, diagnostics)


def _validate_pyduino(source):
    """Validates json file."""
    compiler = Compiler(source.split("\n"),"pc")
    compiler.compile()
    return [error.get_Diagnostic() for error in compiler.errors]
  
@json_server.feature(COMPLETION) # comment  , CompletionOptions(trigger_characters=[',']))
def completions(ls,params: Optional[CompletionParams] = None) -> CompletionList:
    print("complete")
    """Returns completion items."""
    return CompletionList(
        is_incomplete=False,
        items=[
            CompletionItem(label='"'),
            CompletionItem(label='['),
            CompletionItem(label=']'),
            CompletionItem(label='{'),
            CompletionItem(label='}'),
        ]
    )


@json_server.command(PyduinoLanguageServer.CMD_COUNT_DOWN_BLOCKING)
def count_down_10_seconds_blocking(ls, *args):
    """Starts counting down and showing message synchronously.
    It will `block` the main thread, which can be tested by trying to show
    completion items.
    """
    for i in range(COUNT_DOWN_START_IN_SECONDS):
        ls.show_message(f'Counting down... {COUNT_DOWN_START_IN_SECONDS - i}')
        time.sleep(COUNT_DOWN_SLEEP_IN_SECONDS)


@json_server.command(PyduinoLanguageServer.CMD_COUNT_DOWN_NON_BLOCKING)
async def count_down_10_seconds_non_blocking(ls, *args):
    """Starts counting down and showing message asynchronously.
    It won't `block` the main thread, which can be tested by trying to show
    completion items.
    """
    for i in range(COUNT_DOWN_START_IN_SECONDS):
        ls.show_message(f'Counting down...Pyduino {COUNT_DOWN_START_IN_SECONDS - i}')
        await asyncio.sleep(COUNT_DOWN_SLEEP_IN_SECONDS)


@json_server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls, params: DidChangeTextDocumentParams):
    """Text document did change notification."""
    print("change",ls.workspace.get_document(params.text_document.uri).source)
    print("enter validtae")
    _validate(ls, params)


@json_server.feature(TEXT_DOCUMENT_DID_CLOSE)
def did_close(server: PyduinoLanguageServer, params: DidCloseTextDocumentParams):
    """Text document did close notification."""
    server.show_message('Text Document Did Close')


@json_server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    ls.show_message('Text Document Did Open')
    _validate(ls, params)


@json_server.feature(
    TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL,
    SemanticTokensLegend(
        token_types = ["operator"],
        token_modifiers = []
    )
)
def semantic_tokens(ls: PyduinoLanguageServer, params: SemanticTokensParams):
    """See https://microsoft.github.io/language-server-protocol/specification#textDocument_semanticTokens
    for details on how semantic tokens are encoded."""
    
    TOKENS = re.compile('".*"(?=:)')
    
    uri = params.text_document.uri
    doc = ls.workspace.get_document(uri)

    last_line = 0
    last_start = 0

    data = []

    for lineno, line in enumerate(doc.lines):
        last_start = 0

        for match in TOKENS.finditer(line):
            start, end = match.span()
            data += [
                (lineno - last_line),
                (start - last_start),
                (end - start),
                0, 
                0
            ]

            last_line = lineno
            last_start = start

    return SemanticTokens(data=data)



@json_server.command(PyduinoLanguageServer.CMD_PROGRESS)
async def progress(ls: PyduinoLanguageServer, *args):
    """Create and start the progress on the client."""
    token = 'token'
    # Create
    await ls.progress.create_async(token)
    # Begin
    ls.progress.begin(token, WorkDoneProgressBegin(title='Indexing', percentage=0))
    # Report
    for i in range(1, 10):
        ls.progress.report(
            token,
            WorkDoneProgressReport(message=f'{i * 10}%', percentage= i * 10),
        )
        await asyncio.sleep(2)
    # End
    ls.progress.end(token, WorkDoneProgressEnd(message='Finished'))


@json_server.command(PyduinoLanguageServer.CMD_REGISTER_COMPLETIONS)
async def register_completions(ls: PyduinoLanguageServer, *args):
    """Register completions method on the client."""
    params = RegistrationParams(registrations=[
                Registration(
                    id=str(uuid.uuid4()),
                    method=COMPLETION,
                    register_options={"triggerCharacters": "[':']"})
             ])
    response = await ls.register_capability_async(params)
    if response is None:
        ls.show_message('Successfully registered completions method')
    else:
        ls.show_message('Error happened during completions registration.',
                        MessageType.Error)


@json_server.command(PyduinoLanguageServer.CMD_SHOW_CONFIGURATION_ASYNC)
async def show_configuration_async(ls: PyduinoLanguageServer, *args):
    """Gets exampleConfiguration from the client settings using coroutines."""
    try:
        config = await ls.get_configuration_async(
            ConfigurationParams(items=[
                ConfigurationItem(
                    scope_uri='',
                    section=PyduinoLanguageServer.CONFIGURATION_SECTION)
        ]))

        example_config = config[0].get('exampleConfiguration')

        ls.show_message(f'jsonServer.exampleConfiguration value: {example_config}')

    except Exception as e:
        ls.show_message_log(f'Error ocurred: {e}')


@json_server.command(PyduinoLanguageServer.CMD_SHOW_CONFIGURATION_CALLBACK)
def show_configuration_callback(ls: PyduinoLanguageServer, *args):
    """Gets exampleConfiguration from the client settings using callback."""
    def _config_callback(config):
        try:
            example_config = config[0].get('exampleConfiguration')

            ls.show_message(f'jsonServer.exampleConfiguration value: {example_config}')

        except Exception as e:
            ls.show_message_log(f'Error ocurred: {e}')

    ls.get_configuration(ConfigurationParams(items=[
        ConfigurationItem(
            scope_uri='',
            section=PyduinoLanguageServer.CONFIGURATION_SECTION)
    ]), _config_callback)


@json_server.thread()
@json_server.command(PyduinoLanguageServer.CMD_SHOW_CONFIGURATION_THREAD)
def show_configuration_thread(ls: PyduinoLanguageServer, *args):
    """Gets exampleConfiguration from the client settings using thread pool."""
    try:
        config = ls.get_configuration(ConfigurationParams(items=[
            ConfigurationItem(
                scope_uri='',
                section=PyduinoLanguageServer.CONFIGURATION_SECTION)
        ])).result(2)

        example_config = config[0].get('exampleConfiguration')

        ls.show_message(f'pyduino.exampleConfiguration value: {example_config}')

    except Exception as e:
        ls.show_message_log(f'Error ocurred: {e}')


@json_server.command(PyduinoLanguageServer.CMD_UNREGISTER_COMPLETIONS)
async def unregister_completions(ls: PyduinoLanguageServer, *args):
    """Unregister completions method on the client."""
    params = UnregistrationParams(unregisterations=[
        Unregistration(id=str(uuid.uuid4()), method=COMPLETION)
    ])
    response = await ls.unregister_capability_async(params)
    if response is None:
        ls.show_message('Successfully unregistered completions method')
    else:
        ls.show_message('Error happened during completions unregistration.',
                        MessageType.Error)



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
            return f"sizeof({arg}) / sizeof({arg}[0])", True


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
            Error(f"'analogRead' takes 1 positional argument but {len(args)} were given", self.Variables.currentLineIndex,
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
            Error(f"'analogWrite' takes 2 positional arguments but {len(args)} were given", self.Variables.currentLineIndex,
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
    return f"sleep_for(milliseconds({args[0][0]}));", "void", True

class Constants:
    FILENAME = "../testPyduino.pino"

    DEFAULT_INDEX_LEVEL = 4  # spaces

    OPENING_BRACKETS = ["{", "(", "["]
    CLOSING_BRACKETS = {"(": ")", "[": "]", "{": "}"}
    BRACKETS = ["(", ")", "[", "]", "{", "}"]

    VALID_NAME_START_LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    VALID_NAME_LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"

    PRIMITIVE_TYPES = ["int", "float", "char", "bool","byte", "long", "double", "short"]
    PRIMITIVE_ARRAY_TYPES = ["int[]", "float[]", "char[]", "bool[]","byte[]", "long[]", "double[]", "short[]"]
    PRIMITIVE_LIST_TYPES = ["list<int>", "list<float>", "list<char>", "list<bool>","list<byte>", "list<long>", "list<double>", "list<short>"]
    ITERABLES = PRIMITIVE_ARRAY_TYPES + PRIMITIVE_LIST_TYPES

    NUMBERS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    ARITHMETIC_OPERATORS = ["+", "-", "*", "/", "%"]
    CONDITION_OPERATORS_LEN1 = ["<", ">"]
    CONDITION_OPERATORS_LEN2 = ["==", "!=", "<=", ">=", "&&", "||"]

    OPERATORS = ARITHMETIC_OPERATORS + CONDITION_OPERATORS_LEN1 + CONDITION_OPERATORS_LEN2

    CONDITION_CONDITIONS = ["and", "or"]

    WHITESPACE = '" "'

    ALL_SYNTAX_ELEMENTS = OPERATORS + CONDITION_CONDITIONS + BRACKETS

class Error:
    def __init__(self, message, line, column, end_line=None, end_column=None):
        self.message = message
        self.line = line
        self.column = column
        self.end_line = end_line if end_line is not None else line
        self.end_column = end_column if end_column is not None else column

    def __str__(self):
        return f"{self.message} at line {self.line}, column {self.column}"

    def get_Diagnostic(self):
        return Diagnostic(
            range=Range(
                start=Position(line=self.line, character=self.column),
                end=Position(line=self.end_line, character=self.end_line)
            ),
            message=self.message,
            source="Pyduino Languge server"
        )

class Utils:
    def __init__(self, variables, builtins):
        self.errors = None
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
        # TODO ggf fix
        elif "++" in instruction:
            return instruction + ";"
        else:
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
                self.errors.append(Error(f"Datatype mismatch: {datatype} != {dt}", self.Variables.currentLineIndex,
                                         self.Variables.currentLine.find(line)))
                return ""

            if self.variable_in_scope(name, self.Variables.currentLineIndex):
                self.errors.append(Error(f"Variable '{name}' already defined in this scope",
                                         self.Variables.currentLineIndex, self.Variables.currentLine.find(name)))
                return ""
            self.add_variable_to_scope(name, datatype, self.Variables.currentLineIndex)
            return f"{datatype} {name} = {value};"
        elif datatype in Constants.PRIMITIVE_ARRAY_TYPES:
            name = line.split("=")[0].strip().split(" ")[1].strip()
            value = line.split("=")[1].strip()
            value, dt = self.do_array_intializer(value)
            if dt != datatype[:-2]:
                self.errors.append(Error(f"Datatype mismatch: {datatype} != {dt}", self.Variables.currentLineIndex,
                                         self.Variables.currentLine.find(line)))
                return ""
            if self.variable_in_scope(name, self.Variables.currentLineIndex):
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
        if not self.variable_in_scope(name, self.Variables.currentLineIndex):
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
        while self.Variables.currentLineIndex < end_indentation_index:
            self.Variables.currentLineIndex, l = next(self.Variables.iterator)
            if_code.append(self.do_line(l))
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
        while self.Variables.currentLineIndex < end_indentation_index:
            self.Variables.currentLineIndex, l = next(self.Variables.iterator)
            if_code.append(self.do_line(l))
        if_code.append("}")
        return "\n".join(if_code)

    def do_for(self, line):
        col_index = line.index("for") + 3
        if line.strip()[-1] == ":":
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

        self.add_variable_to_scope(counter_variable, dt[:-2], self.Variables.currentLineIndex)
        [self.Variables.code_done.append(x) for x in for_code]
        while self.Variables.currentLineIndex < end_indentation_index:
            self.Variables.currentLineIndex, l = next(self.Variables.iterator)
            self.Variables.code_done.append(self.do_line(l))
        return "}\n"

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
            arg, dt = self.variable_in_scope(value[:start], self.Variables.currentLineIndex)
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

        elif s := self.variable_in_scope(value, self.Variables.currentLineIndex):
            return value, s[1]

        elif (f := self.check_function_execution(value)) is not None:
            return f[0], f[1]
        else:
            self.errors.append(Error("Value is not defined", self.Variables.currentLineIndex,
                                     self.Variables.currentLine.index(value,after_col),
                                     end_column=len(self.Variables.currentLine)))
            return "", -1

    def add_variable_to_scope(self, name, datatype, line_index):
        for start, end in self.Variables.scope.keys():
            if start <= line_index <= end and self.Variables.indentations[
                line_index] == self.Variables.indentations[start]:
                self.Variables.scope[(start, end)][0].append((name, datatype, line_index))
                return

    def variable_in_scope(self, name, line_index):
        """
        :return: (name, datatype) if variable is in scope, -1,-1 if there is an error
        """
        if "[" in name and name[-1] == "]":
            start = name.index("[")
            index = name[start + 1:-1]
            name = name[:start]
            _, dt = self.variable_in_scope(name, line_index)
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
        return False

        for start, end in self.Variables.scope.keys():
            if start <= line_index <= end:
                for i in self.Variables.scope[(start, end)][0]:
                    if i[0] == name and i[2] <= line_index:
                        return i[:2]

        return -1

    @staticmethod
    def get_line_indentation(line):
        """
        :return: Indentation level of the line ALWAYS ROUNDS DOWN
        """
        return (len(line) - len(line.lstrip())) // Constants.DEFAULT_INDEX_LEVEL

    def do_array_intializer(self, value):
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
            return -1

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


class Variables:
    def __init__(self):
        self.scope = None
        self.connection_needed = False
        self.code_done = []
        self.currentLineIndex = 0
        self.currentColumnIndex = 0
        self.iterator = None
        self.sysVariableIndex = 0
        self.iteratorLineIndex = 0
        self.builtins_needed = []
        self.indentations = []



class Compiler(Utils):
    def __init__(self,code: list, mode: str, variables: Variables = None):
        if variables is None:
            variables = Variables()
        self.errors: list[Error] = []
        if mode == "arduino":
            builtins = BuiltinsArduino(variables,self.errors)
        elif mode == "pc":
            builtins = BuiltinsPC(variables,self.errors)
        else:
            raise Exception("Invalid mode")
        super().__init__(variables, builtins)
        self.code = code
        self.Variables = variables
        self.mode = mode
        self.compiling = False

        self.intialize()

    def intialize(self):
        """
        :param variables: Variables object
        :param code: the code as list of lines
        """
        self.Variables.totalLineCount = len(self.code)
        for line in self.code:
            self.Variables.indentations.append(self.get_line_indentation(line))
        self.Variables.code = self.code.copy()
        self.Variables.code_done = []

        current_id_level = 0
        self.Variables.scope = {(0, self.Variables.totalLineCount): [[], []]}
        tempidscope = {(0, self.Variables.totalLineCount): 0}
        # keeps track of the id levels fo the scopes, so they don't get duplicated
        for pos_i, i in enumerate(self.Variables.indentations):
            if i == current_id_level:
                continue
            for pos_j, j in enumerate(self.Variables.indentations[pos_i + 1:]):
                if j < i:
                    for k in tempidscope.keys():
                        if k[0] <= pos_i <= k[1]:
                            if tempidscope[k] == i:
                                break
                    else:
                        self.Variables.scope[(pos_i, pos_j + pos_i)] = [[], []]
                        tempidscope[(pos_i, pos_j + pos_i)] = i
                    break
            current_id_level = i
        self.Variables.iterator = enumerate(self.Variables.code)

    def compile(self):
        self.errors = []
        self.compiling = True
        for self.Variables.currentLineIndex, line in self.Variables.iterator:
            self.Variables.code_done.append(self.do_line(line))
        self.compiling = False

    def finish(self, connection_needed):
        self.Variables.code_done.append("}")
        if self.mode == "arduino":
            self.Variables.code_done.insert(0, "void setup(){")
            if connection_needed:
                self.Variables.code_done.insert(1, "innit_serial();")

                # insert "checkSerial();" after every line
                for i in range(1, len(self.Variables.code_done) - 1):
                    if self.Variables.code_done[i] == "}":
                        continue
                    self.Variables.code_done.insert(i + i, "checkSerial();")

                if "delay" in self.Variables.builtins_needed:
                    self.Variables.code_done.insert(0, """void betterdelay(int ms){
                                                        unsigned long current = millis();
                                                        while(millis() - current < ms){
                                                        checkSerial();}}""")

                self.Variables.code_done.append("void loop() {checkSerial();}")
            else:
                self.Variables.code_done.insert(0, """void betterdelay(int ms) {
                delay(ms);}""")
                self.Variables.code_done.append("void loop() {}")
            return "\n".join([open("../SerialCommunication/ArduinoSkripts/ArduinoSerial/ArduinoSerial.ino",
                                   "r").read()] + self.Variables.code_done)
        if connection_needed:
            self.Variables.code_done.insert(0, '#include "SerialCommunication/SerialPc.cpp|\nusing namespace std;')
        else:
            self.Variables.code_done.insert(0, "#include <iostream>\nusing namespace std;")

        if "delay" in self.Variables.builtins_needed:
            self.Variables.code_done[
                0] += """\n#include <chrono>\n#include <thread>\nusing namespace std::chrono;\nusing namespace std::this_thread;\n"""

        if connection_needed:
            self.Variables.code_done.insert(1, "int main(){ Arduino arduino = Arduino();")
        else:
            self.Variables.code_done.insert(1, "int main(){")
        return "\n".join(self.Variables.code_done)

    def get_completion(self, line, col):
        while self.compiling:
            pass
