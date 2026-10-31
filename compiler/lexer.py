"""Lexical analyzer skeleton for restricted C-like language."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Token:
    type: str
    value: str
    line: int
    column: int


class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"LexerError at line {line}, column {column}: {message}")
        self.message = message
        self.line = line
        self.column = column


class Lexer:
    """Tokenizes source code into a sequence of Tokens."""

    def __init__(self, source_code: str):
        self.source_code = source_code
        self.tokens: List[Token] = []

    def tokenize(self) -> List[Token]:
        # Implementation in Milestone 2
        return self.tokens

