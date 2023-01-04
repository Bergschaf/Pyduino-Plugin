from server.transpiler.runner import Runner
from server.transpiler.transpiler import Transpiler
import sys
import pyunpack
import os

def runFile(file):
    if os.listdir("mingw") == ["MinGW.7z"]:
        pyunpack.Archive("mingw/mingw.7z").extractall("mingw")

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
