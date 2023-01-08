from server.transpiler.runner import Runner
from server.transpiler.transpiler import Transpiler
import sys


def runFile(file):
    if not file.endswith(".pino"):
        print("File must be a .pino file")
        exit()
    with open(file, "r") as f:
        code = f.read()

    compiler_pc, compiler_board = Transpiler.get_transpiler(code.splitlines())
    runner = Runner(compiler_pc, compiler_board)
    runner.run()


if __name__ == '__main__':
    file = sys.argv[1]
    runFile(file)
