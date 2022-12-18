from server.compiler.runner import Runner
from server.compiler.compiler import Compiler
import sys

if __name__ == '__main__':
    file = sys.argv[1]
    if not file.endswith(".pino"):
        print("File must be a .pino file")
        exit()
    with open(file, "r") as f:
        code = f.read()
    compiler_pc, compiler_board = Compiler.get_compiler(code.splitlines())
    runner = Runner(compiler_pc, compiler_board)
    runner.run()
