import subprocess

class Runner:
    def __init__(self, compiler_pc, compiler_board):
        self.compiler_pc = compiler_pc
        self.compiler_board = compiler_board
        self.connection_needed = False

    def compile(self):
        if self.compiler_pc is not None and self.compiler_board is not None:
            self.compile_pc()
            self.compile_board()
        elif self.compiler_pc is not None:
            self.compile_pc()
            self.connection_needed = self.compiler_pc.connection_needed
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
        code = self.compiler_pc.finish()
        with open("temp.c", "w") as f:
            f.write(code)
        subprocess.run(["gcc", "temp.c", "-o", "temp.exe"])
        if self.compiler_pc.connection_needed:
            self.connection_needed = True

    def run_pc(self):
        # get the output in the vscode terminal
        subprocess.run(["cmd", "/c", "start", "temp.exe"], shell=True)

    def compile_board(self):
        self.compiler_board.compile()
        code = self.compiler_board.finish()
        with open("temp.ino", "w") as f:
            f.write(code)
        subprocess.run(["arduino-cli", "compile", "-b", "arduino:avr:uno", "--fqbn", "arduino:avr:uno", "temp.ino"])
        if self.compiler_board.connection_needed:
            self.connection_needed = True

    def run_board(self):
        subprocess.run(["arduino-cli", "upload", "-b", "arduino:avr:uno", "--fqbn", "arduino:avr:uno", "temp.ino"])

    def stop(self):
        subprocess.run(["taskkill", "/f", "/im", "temp.exe"])

if __name__ == '__main__':
    from compiler import Compiler
    c = Compiler(['print("Helllo World")'], "arduino")
    r = Runner(c, None)
    r.run()
