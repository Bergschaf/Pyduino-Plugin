import subprocess
import os

class Runner:
    def __init__(self, compiler_pc, compiler_board, runner_id = 0):
        self.compiler_pc = compiler_pc
        self.compiler_board = compiler_board
        self.connection_needed = False
        self.runner_id = runner_id

    def compile(self):
        if self.compiler_pc is not None and self.compiler_board is not None:
            self.compiler_board.compile()
            self.compile_pc()
            self.compile_board()
        elif self.compiler_pc is not None:
            self.compile_pc()
        elif self.compiler_board is not None:
            self.compile_board()

    def run(self, compiled = False):
        if not compiled:
            self.compile()
        if self.compiler_pc is not None:
            self.run_pc()
        if self.compiler_board is not None:
            self.run_board()

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
        with open("temp.ino", "w") as f:
            f.write(code)
        subprocess.run(["arduino-cli", "compile", "-b", "arduino:avr:uno", "--fqbn", "arduino:avr:uno", "temp.ino"])

    def get_output_pc(self):
        self.compile_pc()
        return subprocess.getoutput(f"temp_{self.runner_id}.exe")

    def run_board(self):
        subprocess.run(["arduino-cli", "upload", "-b", "arduino:avr:uno", "--fqbn", "arduino:avr:uno", "temp.ino"])

    def stop(self):
        subprocess.run(["taskkill", "/f", "/im", f"temp_{self.runner_id}.exe"])
        self.clear()

    def clear(self):
        try:
            os.remove(f"temp_{self.runner_id}.exe")
            os.remove(f"temp_{self.runner_id}.cpp")
        except Exception:
            print("Error deleting files")

if __name__ == '__main__':
    from compiler import Compiler
    c = Compiler(["#main","int i = (2+2)+2"], "pc")
    #r = Runner(c, None)
    #r.run()
    #r.stop()
    c.compile()
    print(c.finish(False))

