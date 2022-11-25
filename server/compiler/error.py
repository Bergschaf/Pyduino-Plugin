from pygls.lsp.types import (Range,Position,Diagnostic)

class Error:
    def __init__(self, message, line, column, end_line=None, end_column=None):
        self.message = message
        self.line = line  # because the line is 0 indexed
        self.column = column  # because the column is 0 indexed
        self.end_line = end_line if end_line is not None else line 
        self.end_column = end_column if end_column is not None else column

    def __str__(self):
        return f"{self.message} at line {self.line} - {self.end_line}, column {self.column} - {self.end_column}"

    def get_Diagnostic(self):
        return Diagnostic(            range=Range(
                start=Position(line=self.line, character=self.column),
                end=Position(line=self.end_line, character=self.end_line)
            ),
            message=self.message,
            source="Pyduino Languge server"
        )
