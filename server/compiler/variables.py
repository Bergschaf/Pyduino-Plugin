
class Variables:
    def __init__(self):
        self.scope = None
        self.connection_needed = False
        self.code_done = []
        self.currentLineIndex = 0
        self.currentColumnIndex = 0
        self.iterator = None
        self.sysVariableIndex = 0
        self.iteratorLineIndex = 0
        self.builtins_needed = []
        self.indentations = []
        self.totalLineCount = 0
        self.inLoop = 0
        self.inIndentation = 0
