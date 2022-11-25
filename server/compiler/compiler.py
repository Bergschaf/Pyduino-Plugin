from server.compiler.utils import Utils
from server.compiler.builtin_functions import BuiltinsArduino, BuiltinsPC
from server.compiler.constants import Constants
from server.compiler.variables import Variables


class Compiler(Utils):
    def __init__(self, variables: Variables, code: list, mode: str):
        if mode == "arduino":
            builtins = BuiltinsArduino(variables)
        elif mode == "pc":
            builtins = BuiltinsPC(variables)
        else:
            raise Exception("Invalid mode")
        super().__init__(variables, builtins)
        self.code = code
        self.Variables = variables
        self.mode = mode
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
        for self.Variables.currentLineIndex, line in self.Variables.iterator:
            self.Variables.code_done.append(self.do_line(line))

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
            self.Variables.code_done.insert(0,"""#include "SerialCommunication/SerialPc.cpp"
                                using namespace std;""")
        else:
            self.Variables.code_done.insert(0, """#include <iostream>
            using namespace std;""")

        if "delay" in self.Variables.builtins_needed:
            self.Variables.code_done[0] +=  """\n#include <chrono>\n#include <thread>\nusing namespace std::chrono;\nusing namespace std::this_thread;\n"""

        if connection_needed:
            self.Variables.code_done.insert(1,"int main(){ Arduino arduino = Arduino();")
        else:
            self.Variables.code_done.insert(1,"int main(){")
        return "\n".join(self.Variables.code_done)
