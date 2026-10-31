"""Tests for Lexer module."""

import pytest
from compiler.lexer import Lexer, LexerError, Token


def test_keywords_and_identifiers():
    code = "int float if else while x myVar var_1"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    types = [t.type for t in tokens]
    values = [t.value for t in tokens]

    assert types == [
        "INT", "FLOAT", "IF", "ELSE", "WHILE",
        "IDENTIFIER", "IDENTIFIER", "IDENTIFIER", "EOF"
    ]
    assert values == [
        "int", "float", "if", "else", "while",
        "x", "myVar", "var_1", ""
    ]


def test_numeric_literals():
    code = "42 0 3.14159 0.005"
    lexer = Lexer(code)
    tokens = lexer.tokenize()

    assert tokens[0] == Token("INT_LITERAL", "42", 1, 1)
    assert tokens[1] == Token("INT_LITERAL", "0", 1, 4)
    assert tokens[2] == Token("FLOAT_LITERAL", "3.14159", 1, 6)
    assert tokens[3] == Token("FLOAT_LITERAL", "0.005", 1, 14)


def test_operators_longest_match():
    code = "+ - * / % < <= > >= == != && || ! ="
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    types = [t.type for t in tokens[:-1]]

    assert types == [
        "PLUS", "MINUS", "STAR", "SLASH", "PERCENT",
        "LT", "LE", "GT", "GE", "EQ", "NE", "AND", "OR", "NOT", "ASSIGN"
    ]


def test_comments():
    code = """
    // Single line comment
    int a = 5; /* multi-line
                  comment */
    float b = 2.5;
    """
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    types = [t.type for t in tokens]

    assert types == [
        "INT", "IDENTIFIER", "ASSIGN", "INT_LITERAL", "SEMICOLON",
        "FLOAT", "IDENTIFIER", "ASSIGN", "FLOAT_LITERAL", "SEMICOLON",
        "EOF"
    ]


def test_line_column_tracking():
    code = "int a;\na = 10;"
    lexer = Lexer(code)
    tokens = lexer.tokenize()

    assert tokens[0] == Token("INT", "int", 1, 1)
    assert tokens[1] == Token("IDENTIFIER", "a", 1, 5)
    assert tokens[2] == Token("SEMICOLON", ";", 1, 6)
    assert tokens[3] == Token("IDENTIFIER", "a", 2, 1)
    assert tokens[4] == Token("ASSIGN", "=", 2, 3)
    assert tokens[5] == Token("INT_LITERAL", "10", 2, 5)
    assert tokens[6] == Token("SEMICOLON", ";", 2, 7)


def test_invalid_character_error():
    code = "int a = 10 @ 5;"
    lexer = Lexer(code)
    with pytest.raises(LexerError) as exc_info:
        lexer.tokenize()
    assert "Unexpected character '@'" in str(exc_info.value)
    assert exc_info.value.line == 1
    assert exc_info.value.column == 12


def test_unterminated_comment():
    code = "int a = 5; /* unterminated comment"
    lexer = Lexer(code)
    with pytest.raises(LexerError) as exc_info:
        lexer.tokenize()
    assert "Unterminated multi-line comment" in str(exc_info.value)
    assert exc_info.value.line == 1


def test_malformed_numbers():
    # Multiple decimal dots
    with pytest.raises(LexerError) as exc1:
        Lexer("int x = 12.34.56;").tokenize()
    assert "multiple decimal points" in str(exc1.value)

    # Dot without trailing digit
    with pytest.raises(LexerError) as exc2:
        Lexer("float f = 12.;").tokenize()
    assert "ending with decimal point" in str(exc2.value)

    # Number immediately followed by identifier
    with pytest.raises(LexerError) as exc3:
        Lexer("int 123abc = 5;").tokenize()
    assert "Invalid identifier or number literal" in str(exc3.value)
