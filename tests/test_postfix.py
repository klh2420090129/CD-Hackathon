"""Tests for PostfixGenerator module."""

import pytest
from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.postfix import PostfixGenerator


def get_postfix(code: str):
    tokens = Lexer(code).tokenize()
    ast = Parser(tokens).parse()
    gen = PostfixGenerator(ast)
    return gen.generate()


def test_simple_addition():
    code = "int x; x = a + b;"
    results = get_postfix(code)
    assert len(results) == 1
    assert results[0]["postfix"] == "a b +"
    assert results[0]["tokens"] == ["a", "b", "+"]


def test_operator_precedence():
    code = "int x; x = a + b * c;"
    results = get_postfix(code)
    assert len(results) == 1
    assert results[0]["postfix"] == "a b c * +"


def test_parenthesized_expressions():
    code = "int x; x = (a + b) * c;"
    results = get_postfix(code)
    assert len(results) == 1
    assert results[0]["postfix"] == "a b + c *"


def test_nested_complex_expression():
    code = "int c; c = a + b * (c - 5) / 2;"
    results = get_postfix(code)
    assert len(results) == 1
    # b * (c - 5) / 2 -> b c 5 - * 2 /
    # a + ... -> a b c 5 - * 2 / +
    assert results[0]["postfix"] == "a b c 5 - * 2 / +"


def test_unary_operators():
    code = "int x; x = -a + 5;"
    results = get_postfix(code)
    assert len(results) == 1
    assert results[0]["postfix"] == "a u- 5 +"


def test_multiple_statements_and_declarations():
    code = """
    int a = 10 + 2;
    int b = 20;
    int c;
    c = a * b;
    """
    results = get_postfix(code)
    assert len(results) == 3
    assert results[0]["context"] == "var a = ..."
    assert results[0]["postfix"] == "10 2 +"
    assert results[1]["context"] == "var b = ..."
    assert results[1]["postfix"] == "20"
    assert results[2]["context"] == "c = ..."
    assert results[2]["postfix"] == "a b *"
