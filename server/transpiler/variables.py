class Variables:
    def __init__(self):
        self.scope: dict[tuple[int, int], list[list[tuple[str, str]], list[tuple[str, str]]]] = None
        self.connection_needed: bool = False
        self.code_done: list[str] = []
        self.currentLineIndex: int = 0
        self.currentColumnIndex: int = 0
        self.iterator: enumerate = None
        self.sysVariableIndex: int = 0
        self.iteratorLineIndex: int = 0
        self.builtins_needed = []
        self.indentations: list[int] = []
        self.totalLineCount = 0
        self.inLoop = 0
        self.inIndentation = 0
