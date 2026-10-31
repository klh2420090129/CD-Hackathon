"""Lexical analyzer for restricted C-like language.

Converts input source code into a stream of Token objects with exact line and
column positions, distinguishing keywords, numbers, operators, and identifiers.
"""

from dataclasses import dataclass
from typing import List, Optional, Set


class LexerError(Exception):
    """Raised when an unexpected character or malformed token is encountered."""
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"LexerError at line {line}, column {column}: {message}")
        self.message = message
        self.line = line
        self.column = column


@dataclass
class Token:
    type: str
    value: str
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type}, {self.value!r}, {self.line}:{self.column})"


KEYWORDS: Set[str] = {
    "int", "float", "if", "else", "while"
}

# Multi-character operators and single-character operators
MULTI_CHAR_OPS = {
    "&&": "AND",
    "||": "OR",
    "==": "EQ",
    "!=": "NE",
    "<=": "LE",
    ">=": "GE",
}

SINGLE_CHAR_OPS = {
    "+": "PLUS",
    "-": "MINUS",
    "*": "STAR",
    "/": "SLASH",
    "%": "PERCENT",
    "<": "LT",
    ">": "GT",
    "=": "ASSIGN",
    "!": "NOT",
    ";": "SEMICOLON",
    "(": "LPAREN",
    ")": "RPAREN",
    "{": "LBRACE",
    "}": "RBRACE",
}


class Lexer:
    """Handwritten lexer with exact line and column tracking."""

    def __init__(self, source_code: str):
        self.source = source_code
        self.length = len(source_code)
        self.pos = 0
        self.line = 1
        self.column = 1

    def _peek(self, offset: int = 0) -> Optional[str]:
        idx = self.pos + offset
        if idx < self.length:
            return self.source[idx]
        return None

    def _advance(self) -> Optional[str]:
        if self.pos >= self.length:
            return None
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []

        while self.pos < self.length:
            ch = self._peek()

            # Whitespace
            if ch in (" ", "\t", "\r", "\n"):
                self._advance()
                continue

            # Comments
            if ch == "/":
                next_ch = self._peek(1)
                if next_ch == "/":
                    # Single-line comment: skip until newline or EOF
                    self._advance()
                    self._advance()
                    while self.pos < self.length and self._peek() != "\n":
                        self._advance()
                    continue
                elif next_ch == "*":
                    # Multi-line comment: /* ... */
                    start_line = self.line
                    start_col = self.column
                    self._advance()  # /
                    self._advance()  # *
                    terminated = False
                    while self.pos < self.length:
                        if self._peek() == "*" and self._peek(1) == "/":
                            self._advance()  # *
                            self._advance()  # /
                            terminated = True
                            break
                        self._advance()
                    if not terminated:
                        raise LexerError("Unterminated multi-line comment", start_line, start_col)
                    continue

            # Identifiers and Keywords
            if ch.isalpha() or ch == "_":
                token_line = self.line
                token_col = self.column
                buf = []
                while self.pos < self.length and (self._peek().isalnum() or self._peek() == "_"):
                    buf.append(self._advance())
                val = "".join(buf)
                if val in KEYWORDS:
                    tokens.append(Token(val.upper(), val, token_line, token_col))
                else:
                    tokens.append(Token("IDENTIFIER", val, token_line, token_col))
                continue

            # Numbers (integer and float)
            if ch.isdigit():
                token_line = self.line
                token_col = self.column
                buf = []
                has_dot = False

                while self.pos < self.length and (self._peek().isdigit() or self._peek() == "."):
                    if self._peek() == ".":
                        if has_dot:
                            # Second decimal dot is invalid
                            raise LexerError("Malformed number with multiple decimal points", self.line, self.column)
                        has_dot = True
                    buf.append(self._advance())

                # Check if ends with a dot, e.g. "123."
                if buf[-1] == ".":
                    raise LexerError("Malformed float literal ending with decimal point", token_line, token_col)

                # Check if immediately followed by an identifier character (e.g. 123abc)
                if self.pos < self.length and (self._peek().isalpha() or self._peek() == "_"):
                    raise LexerError(f"Invalid identifier or number literal '{''.join(buf)}{self._peek()}'", token_line, token_col)

                val = "".join(buf)
                tok_type = "FLOAT_LITERAL" if has_dot else "INT_LITERAL"
                tokens.append(Token(tok_type, val, token_line, token_col))
                continue

            # Two-character operators (longest match)
            two_chars = self.source[self.pos:self.pos + 2]
            if two_chars in MULTI_CHAR_OPS:
                token_line = self.line
                token_col = self.column
                self._advance()
                self._advance()
                tokens.append(Token(MULTI_CHAR_OPS[two_chars], two_chars, token_line, token_col))
                continue

            # Single-character operators and delimiters
            if ch in SINGLE_CHAR_OPS:
                token_line = self.line
                token_col = self.column
                self._advance()
                tokens.append(Token(SINGLE_CHAR_OPS[ch], ch, token_line, token_col))
                continue

            # Unexpected character
            token_line = self.line
            token_col = self.column
            bad_char = self._advance()
            raise LexerError(f"Unexpected character '{bad_char}'", token_line, token_col)

        # End of file token
        tokens.append(Token("EOF", "", self.line, self.column))
        return tokens
