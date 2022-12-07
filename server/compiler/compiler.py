from server.compiler.utils import Utils
from server.compiler.builtin_functions import BuiltinsArduino, BuiltinsPC
from server.compiler.constants import Constants
from server.compiler.variables import Variables
from server.compiler.error import Error


class Compiler(Utils):
    def __init__(self, code: list, mode: str, variables: Variables = None):
        if variables is None:
            self.Variables = Variables()
        else:
            self.Variables = variables

        self.errors: list[Error] = []
        if mode == "arduino":
            builtins = BuiltinsArduino(self.Variables, self.errors)
        elif mode == "pc":
            builtins = BuiltinsPC(self.Variables, self.errors)
        else:
            raise Exception("Invalid mode")
        super().__init__(self.Variables, builtins, self.errors)
        self.code = code
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
        self.Variables.indentations.append(0)  # copium to prevent index out of range
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
        self.Variables.code = [x.replace("\n","") for x in self.Variables.code]
        self.Variables.iterator = enumerate(self.Variables.code)

    def compile(self):
        self.errors.clear()
        if self.Variables.totalLineCount == 0:
            return
        self.compiling = True
        _ , line = next(self.Variables.iterator)

        if self.mode == "pc":
            if line.replace(" ", "") != "#main":
                print(line)
                print(line.replace(" ", "") + "l")
                self.errors.append(Error("Missing #main at the beginning of the file", 0, 0, end_column=len(line)))
        else:
            if line.replace(" ", "") != "#board":
                self.errors.append(Error("Missing #board at the beginning of the board part", 0, 0, end_column=len(line)))
        self.Variables.inLoop = 0
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
        included = ["#include <iostream>"]
        namespaces = ["using namespace std;"]
        if connection_needed:
            included.append('#include "SerialCommunication/SerialPc.cpp"')

        if "delay" in self.Variables.builtins_needed:

            included.append('#include <chrono>')
            included.append('#include <thread>')
            namespaces.append("using namespace std::chrono;")
            namespaces.append("using namespace std::this_thread;")


        if connection_needed:
            self.Variables.code_done.insert(0, "int main(){ Arduino arduino = Arduino();")
        else:
            self.Variables.code_done.insert(0, "int main(){")

        self.Variables.code_done = included + namespaces + self.Variables.code_done
        return "\n".join(self.Variables.code_done)

    def get_completion(self, line, col):
        while self.compiling:
            pass


    @staticmethod
    def get_compiler(code: list):
        code_pc = []
        code_board = []
        code = [i.replace("\n", "").replace("\r","") for i in code]
        if code[0].replace(" ", "") == "#main":
            for i in range(len(code)):
                if code[i].replace(" ", "") == "#board":
                    code_pc = code[:i]
                    code_board = code[i:]
                    break
            else:
                code_pc = code
        elif code[0].replace(" ", "") == "#board":
            for i in range(len(code)):
                if code[i].replace(" ", "") == "#main":
                    code_board = code[:i]
                    code_pc = code[i:]
                    break
                else:
                    code_board = code
        else:
            code_pc = code.copy()
        if code_board == []:
            return Compiler(code_pc, "pc"), None
        if code_pc == []:
            return None, Compiler(code_board, "arduino")
        else:
            return Compiler(code_pc, "pc"), Compiler(code_board, "arduino")
