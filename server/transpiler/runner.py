import subprocess
import os
from server.transpiler.transpiler import Transpiler


class Runner:
    def __init__(self, transpiler_pc, transpiler_board, runner_id=0):
        self.transpiler_pc = transpiler_pc
        self.transpiler_board = transpiler_board
        self.connection_needed = False
        self.runner_id = runner_id
        self.board = None

    def compile(self):
        if self.transpiler_pc is not None and self.transpiler_board is not None:
            self.transpiler_board.transpile()
            self.connection_needed = self.transpiler_board.Variables.connection_needed
            self.compile_pc()
            self.compile_board()
        elif self.transpiler_pc is not None:
            self.compile_pc()
            if self.connection_needed:
                self.transpiler_board = Transpiler(["#board"], "arduino")
                self.compile_board()
        elif self.transpiler_board is not None:
            self.compile_board()
            if self.connection_needed:
                self.transpiler_pc = Transpiler(["#main"], "pc")
                self.compile_pc()

    def run(self, compiled=False):
        if not compiled:
            self.compile()
        if self.transpiler_board is not None:
            self.run_board()
        if self.transpiler_pc is not None:
            self.run_pc()

    def compile_pc(self):
        self.transpiler_pc.transpile()
        if self.transpiler_pc.errors:
            print("Compiler error")
            print("\n".join([str(e) for e in self.transpiler_pc.errors]))
            exit()
        self.connection_needed = True if self.transpiler_pc.Variables.connection_needed else self.connection_needed
        code = self.transpiler_pc.finish(self.connection_needed)
        with open(f"temp_{self.runner_id}.cpp", "w") as f:
            f.write(code)
        # print output
        #print(subprocess.run(["mingw/MinGW/bin/g++.exe", f"temp_{self.runner_id}.cpp", "-o", f"temp_{self.runner_id}.exe"]).stdout)
        print(subprocess.run(["g++", f"temp_{self.runner_id}.cpp", "-o", f"temp_{self.runner_id}.exe"]).stdout)


    def run_pc(self):
        # show the output in the vscode terminal
        subprocess.Popen(f"temp_{self.runner_id}.exe")
        print("--- Program started ---")

    def compile_board(self):
        self.transpiler_board.transpile()
        if self.transpiler_board.errors:
            print("Compiler error")
            print("\n".join([str(e) for e in self.board.errors]))
            exit()
        self.connection_needed = True if self.transpiler_board.Variables.connection_needed else self.connection_needed
        code = self.transpiler_board.finish(self.connection_needed)
        if not os.path.exists("temp"):
            os.mkdir("temp")
        with open("temp/temp.ino", "w") as f:
            f.write(code)
        self.board = self.get_boards()[0]  # TODO select right option
        subprocess.run(
            ["server/transpiler/arduino-cli", "compile", "--fqbn", self.board[1], "temp"])

    @staticmethod
    def get_boards():
        # TODO select option
        boards = [p.split(" ") for p in
                  subprocess.run(["server/transpiler/arduino-cli", "board", "list"], capture_output=True).stdout.decode(
                      "utf-8").split("\n")[1:] if "arduino" in p]
        if len(boards) == 0:
            print("No boards found, connect a board and try again")
            exit()
        print("Boards found:")
        for i, b in enumerate(boards):
            print(f"{i + 1}. {b[0]} - {b[-2]}")
        return [(b[0], b[-2]) for b in boards]

    def get_output_pc(self):
        self.compile_pc()
        return subprocess.getoutput(f"temp_{self.runner_id}.exe")

    def run_board(self):
        subprocess.run(["server/transpiler/arduino-cli", "upload", "-b", self.board[1], "-p", self.board[0], "temp"])

    def stop(self):
        subprocess.run(["taskkill", "/f", "/im", f"temp_{self.runner_id}.exe"])
        self.clear()

    def clear(self):
        try:
            os.remove(f"temp_{self.runner_id}.cpp")
            os.remove(f"temp_{self.runner_id}.exe")
        except Exception:
            print("Error deleting files")
