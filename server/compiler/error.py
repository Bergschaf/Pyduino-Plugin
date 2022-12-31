from lsprotocol.types import (Range,Position,Diagnostic)

class Error:
    def __init__(self, message, line, column, end_line=None, end_column=None, line_offset=0):
        self.message = message
        self.line = line 
        self.column = column
        self.end_line = end_line if end_line is not None else line 
        self.end_column = end_column if end_column is not None else column
        self.line_offset = line_offset

    def __str__(self):
        return f"{self.message} at line {self.line_offset + self.line} - {self.line_offset + self.end_line}, column {self.column} - {self.end_column}"

    def get_Diagnostic(self):
        return Diagnostic(range=Range(
                start=Position(line=self.line + self.line_offset, character=self.column),
                end=Position(line=self.end_line+ self.line_offset, character=self.end_column)
            ),
            message=self.message,
            source="Pyduino Languge server"
        )
