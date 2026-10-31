"""Recursive-descent parser skeleton."""

from typing import List, Optional
from compiler.lexer import Token
from compiler.ast_nodes import ASTNode


class ParserError(Exception):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"ParserError at line {line}, column {column}: {message}")
        self.message = message
        self.line = line
        self.column = column


class Parser:
    """Parses a token stream into an Abstract Syntax Tree."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> Optional[ASTNode]:
        # Implementation in Milestone 2
        return None

