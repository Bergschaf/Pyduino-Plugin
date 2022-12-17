import subprocess
import os
from server.compiler.compiler import Compiler


class Runner:
    def __init__(self, compiler_pc, compiler_board, runner_id=0):
        self.compiler_pc = compiler_pc
        self.compiler_board = compiler_board
        self.connection_needed = False
        self.runner_id = runner_id

    def compile(self):
        if self.compiler_pc is not None and self.compiler_board is not None:
            self.compiler_board.compile()
            self.connection_needed = self.compiler_board.Variables.connection_needed
            self.compile_pc()
            self.compile_board()
        elif self.compiler_pc is not None:
            self.compile_pc()
            if self.connection_needed:
                self.compiler_board = Compiler(["#board"], "arduino")
                self.compile_board()
        elif self.compiler_board is not None:
            self.compile_board()

    def run(self, compiled=False):
        if not compiled:
            self.compile()
        if self.compiler_board is not None:
            self.run_board()
        if self.compiler_pc is not None:
            self.run_pc()

    def compile_pc(self):
        self.compiler_pc.compile()
        if self.compiler_pc.errors:
            raise Exception("Compiler error")
        self.connection_needed = True if self.compiler_pc.Variables.connection_needed else self.connection_needed
        code = self.compiler_pc.finish(self.connection_needed)
        with open(f"temp_{self.runner_id}.cpp", "w") as f:
            f.write(code)
        subprocess.run(["g++", f"temp_{self.runner_id}.cpp", "-o", f"temp_{self.runner_id}.exe"])

    def run_pc(self):
        # show the output in the vscode terminal
        subprocess.Popen(f"temp_{self.runner_id}.exe")
        print("--- Program started ---")

    def compile_board(self):
        self.compiler_board.compile()
        if self.compiler_board.errors:
            raise Exception("Compiler error")
        self.connection_needed = True if self.compiler_board.Variables.connection_needed else self.connection_needed
        code = self.compiler_board.finish(self.connection_needed)
        if not os.path.exists("temp"):
            os.mkdir("temp")
        with open("temp/temp.ino", "w") as f:
            f.write(code)
        subprocess.run(
            ["server/compiler/arduino-cli", "compile", "-b", "arduino:avr:uno", "--fqbn", "arduino:avr:uno", "temp"])

    @staticmethod
    def get_port():
        # TODO selet option
        return ["".join([x for i, x in enumerate(p) if not any([y == " " for y in p[:i + 1]])]) for p in
                subprocess.run(["server/compiler/arduino-cli", "board", "list"], capture_output=True).stdout.decode(
                    "utf-8").split("\n")[1:] if "arduino" in p][0]

    def get_output_pc(self):
        self.compile_pc()
        return subprocess.getoutput(f"temp_{self.runner_id}.exe")

    def run_board(self):
        subprocess.run(
            ["server/compiler/arduino-cli", "upload", "-b", "arduino:avr:uno", "-p", self.get_port(), "temp"])

    def stop(self):
        subprocess.run(["taskkill", "/f", "/im", f"temp_{self.runner_id}.exe"])
        self.clear()

    def clear(self):
        try:
            os.remove(f"temp_{self.runner_id}.exe")
            os.remove(f"temp_{self.runner_id}.cpp")
        except Exception:
            print("Error deleting files")
