import unittest
from compiler import Compiler
from runner import Runner
import multiprocessing


def compilation(code, expected, connection_needed=False):
    compiler = Compiler(code, "pc")
    compiler.compile()
    if compiler.errors:
        raise Exception("Compiler error ", [str(e) for e in compiler.errors])
    code = compiler.finish(connection_needed)
    assert code == expected


def output(code, expected, runner_id=0):
    compiler = Compiler(code, "pc")
    compiler.compile()
    if compiler.errors:
        # print in the color red
        print("\n\n\n", "\n".join([str(e) for e in compiler.errors]), "\n\n\n")

        raise Exception("Compiler error ", [str(e) for e in compiler.errors])
    runner = Runner(compiler, None, runner_id=runner_id)
    out = runner.get_output_pc()
    runner.clear()
    if out != expected:
        print(f"\n\nout\n{out}\nexpected\n{expected}\nrunner_id {runner_id}")
    assert out == expected


def multiprocess_output(pairs: list):
    with multiprocessing.Pool() as pool:
        pool.starmap(output, [(x[0], x[1], i) for i, x in enumerate(pairs)])


class Tests(unittest.TestCase):
    def test(self):
        # Print
        code = [(["#main", "print(2+2)"], "4"),
                (["#main", "print(1)", "print(2)"], "1\n2"),
                (["#main", "print(1+2)"], "3"),
                (["#main", "print(1,2,3)"], "1 2 3"),
                (['#main', 'print(1,2,"hello")'], '1 2 hello'),
                (['#main', 'print("Hello","World")'], 'Hello World'),
                # Variables
                (['#main', 'int i = 2', 'print(i)'], '2'),
                (['#main', 'int i = 2', 'print(i+2)'], '4'),
                (['#main', 'int i = 2', 'print(i+2)', 'print(i)'], '4\n2'),
                (['#main', 'int i = 2', 'print(i+2)', 'print(i)', 'i = 3', 'print(i)'], '4\n2\n3'),
                (["#main", "int i = 2", "int j = 3", "print(i+j)"], "5"),
                (["#main", "int i = 2", "int j = 3", "print(i+j)", "print(i)"], "5\n2"),
                # arrays
                (["#main", "int[] i = [1,2,3,4]", "print(i[0])"], "1"),
                (["#main", "int[] i = [1,2,3,4]", "print(i)"], "[1, 2, 3, 4]"),
                (["#main", "int[] i = [1,2,3,4]", "print(i[0]+i[1])"], "3"),
                (["#main", "int[] i = [3,4,5,6]", "for j in i:", "    print(j)"], "3\n4\n5\n6"),
                (["#main", "int[] i = [3,4,5,6]", "for j in i:", "    print(j)", "print(i)"],
                 "3\n4\n5\n6\n[3, 4, 5, 6]"),
                # Operators
                (["#main", "int i = 2", "int j = 3", "print(i+j)"], "5"),
                (["#main", "int i = 2", "int j = 3", "print(i-j)"], "-1"),
                (["#main", "int i = 2", "int j = 3", "print(i*j)"], "6"),
                (["#main", "int i = 2", "int j = 4", "print(i/j)"], "0.5"),
                (["#main", "int i = 2", "int j = 4", "print(i%j)"], "2"),
                (["#main", "int i = 2", "int j = 4", "print(i**j)"], "16"),
                (["#main", "int i = 2", "int j = 4", "print(i//j)"], "0"),
                (["#main", "int i = 2", "int j = 4", "print(i==j)"], "0"),
                (["#main", "int i = 2", "int j = 4", "print(i!=j)"], "1"),
                (["#main", "int i = 2", "int j = 4", "print(i<j)"], "1"),
                (["#main", "int i = 2", "int j = 4", "print(i<=j)"], "1"),
                (["#main", "int i = 2", "int j = 4", "print(i>j)"], "0"),
                (["#main", "int i = 2", "int j = 4", "print(i>=j)"], "0"),
                (["#main", "int i = 2", "int j = 4", "print(i<j and i>j)"], "0"),
                (["#main", "int i = 2", "int j = 4", "print(i<j or i>j)"], "1"),  # TODO implement not operator

                # - sign
                (["#main", "print((-2 + 2) * (-2))"], "0"),
                (["#main", "print(-2 + 2 * (-2))"], "-6"),
                (["#main", "int[] i = [1,2,3,4]", "print(-i[0])"], "-1"),
                (["#main", "int[] i = [1,2,3,4]", "print(-len(i))"], "-4"),
                (["#main", "int[] i = [1,2,3,4]", "print(-i[0]+i[1])"], "1"),
                (["#main", "int[] i = [1,2,3,4]", "print(-i[0]+len(i))"], "-3"),
                (["#main", "print(-2**2)"], "-4"),
                (["#main", "print(-2/2)"], "-1"),
                (["#main", "print(-(2 * 2 * (-2)))"], "8"),
                (["#main", "print(-(((2)) * 2 * (-2)))"], "8"),

                # If
                (["#main", "int i = 2", "if i == 2:", "    print(1)"], "1"),
                (["#main", "int i = 2", "if i == 1:", "    print(1)", "else:", "    print(2)"], "2"),
                (["#main", "int i = 2", "if i == 1:", "    print(1)", "elif i == 2:", "    print(2)"], "2"),
                (["#main", "int i = 2", "if i == 1:", "    print(1)", "elif i == 2:", "    print(2)", "else:",
                  "    print(3)"], "2"),
                (["#main", "int i = 2", "if i == 1:", "    print(1)", "elif i == 2:", "    print(2)", "else:",
                  "    print(3)", "print(4)"], "2\n4"),
                (["#main", "int i = 2", "if i == 1:", "    print(1)", "elif i == 2:", "    print(2)", "else:",
                  "    print(3)", "print(4)", "if i == 2:", "    print(5)"], "2\n4\n5"),
                # len
                (["#main", "int[] i = [1,2,3,4]", "print(len(i))"], "4"),
                (["#main", "int[] i = [1,2,3,4]", "print(len(i)+1)"], "5"),
                (["#main", "int[] i = [1,2,3,4]", "print(len(i)+1)", "print(len(i))"], "5\n4"),


                ]
        multiprocess_output(code)

    def test_sort(self):
        code = [(["#main",
                  "# selectionsort",
                  "int[] array = [5, 2, 4, 6, 1, 3]",
                  "for i in range(len(array)):",
                  "    int min = i",
                  "    for j in range(i + 1, len(array)):",
                  "        if array[j] < array[min]:",
                  "            min = j",
                  "    int temp = array[i]",
                  "    array[i] = array[min]",
                  "    array[min] = temp",
                  "print(array)"], "[1, 2, 3, 4, 5, 6]"),
                (["#main",
                    "# bubblesort",
                    "int[] array = [5, 2, 4, 6, 1, 3]",
                    "for i in range(len(array)):",
                    "    for j in range(len(array) - 1):",
                    "        if array[j] > array[j + 1]:",
                    "            int temp = array[j]",
                    "            array[j] = array[j + 1]",
                    "            array[j + 1] = temp",
                    "print(array)"], "[1, 2, 3, 4, 5, 6]")
               ]
        multiprocess_output(code)



if __name__ == '__main__':
    unittest.main()
