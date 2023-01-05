import time
from server.transpiler.runner import Runner
from server.transpiler.transpiler import Transpiler
import os
FILES = os.listdir("test")
if __name__ == '__main__':
    for file in FILES:
        start = time.time()
        compiler_pc, compiler_board = Transpiler.get_transpiler(open(f"test/{file}", "r").read().splitlines())
        runner = Runner(compiler_pc, compiler_board)
        runner.compile()
        print(f"{file} took {(time.time() - start).__round__(3)} seconds")
        runner.clear()