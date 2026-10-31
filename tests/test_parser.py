"""Tests for Parser and AST modules."""

import pytest
from compiler.lexer import Lexer
from compiler.parser import Parser, ParserError
from compiler.ast_nodes import (
    Program, Block, VarDecl, Assign, IfStmt,
    WhileStmt, BinaryOp, UnaryOp, Identifier, NumberLiteral
)


def parse_code(code: str) -> Program:
    tokens = Lexer(code).tokenize()
    return Parser(tokens).parse()


def test_simple_declaration():
    code = "int a; float b;"
    prog = parse_code(code)
    assert len(prog.statements) == 2
    s1, s2 = prog.statements

    assert isinstance(s1, VarDecl)
    assert s1.type_name == "int"
    assert s1.name == "a"
    assert s1.initializer is None

    assert isinstance(s2, VarDecl)
    assert s2.type_name == "float"
    assert s2.name == "b"
    assert s2.initializer is None


def test_initialized_declaration():
    code = "int count = 100;"
    prog = parse_code(code)
    assert len(prog.statements) == 1
    decl = prog.statements[0]

    assert isinstance(decl, VarDecl)
    assert decl.name == "count"
    assert isinstance(decl.initializer, NumberLiteral)
    assert decl.initializer.value == "100"
    assert not decl.initializer.is_float


def test_assignment():
    code = "x = y + 5;"
    prog = parse_code(code)
    assign = prog.statements[0]

    assert isinstance(assign, Assign)
    assert assign.target == "x"
    assert isinstance(assign.expr, BinaryOp)
    assert assign.expr.op == "+"
    assert isinstance(assign.expr.left, Identifier)
    assert assign.expr.left.name == "y"
    assert isinstance(assign.expr.right, NumberLiteral)
    assert assign.expr.right.value == "5"


def test_arithmetic_precedence():
    # a + b * c must be parsed as a + (b * c)
    code = "x = a + b * c;"
    prog = parse_code(code)
    expr = prog.statements[0].expr

    assert isinstance(expr, BinaryOp)
    assert expr.op == "+"
    assert isinstance(expr.left, Identifier)
    assert expr.left.name == "a"
    assert isinstance(expr.right, BinaryOp)
    assert expr.right.op == "*"
    assert expr.right.left.name == "b"
    assert expr.right.right.name == "c"


def test_parenthesized_expressions():
    # (a + b) * c must be parsed with '+' under '*'
    code = "x = (a + b) * c;"
    prog = parse_code(code)
    expr = prog.statements[0].expr

    assert isinstance(expr, BinaryOp)
    assert expr.op == "*"
    assert isinstance(expr.left, BinaryOp)
    assert expr.left.op == "+"
    assert expr.left.left.name == "a"
    assert expr.left.right.name == "b"
    assert isinstance(expr.right, Identifier)
    assert expr.right.name == "c"


def test_if_and_if_else():
    code = """
    if (x > 0) {
        x = x - 1;
    } else {
        x = 0;
    }
    """
    prog = parse_code(code)
    if_stmt = prog.statements[0]

    assert isinstance(if_stmt, IfStmt)
    assert isinstance(if_stmt.condition, BinaryOp)
    assert if_stmt.condition.op == ">"
    assert isinstance(if_stmt.then_branch, Block)
    assert isinstance(if_stmt.else_branch, Block)
    assert len(if_stmt.then_branch.statements) == 1
    assert len(if_stmt.else_branch.statements) == 1


def test_while_loop():
    code = """
    while (i < 10) {
        i = i + 1;
    }
    """
    prog = parse_code(code)
    while_stmt = prog.statements[0]

    assert isinstance(while_stmt, WhileStmt)
    assert isinstance(while_stmt.condition, BinaryOp)
    assert while_stmt.condition.op == "<"
    assert isinstance(while_stmt.body, Block)


def test_nested_blocks():
    code = """
    {
        int x = 1;
        {
            x = x + 2;
        }
    }
    """
    prog = parse_code(code)
    outer_block = prog.statements[0]

    assert isinstance(outer_block, Block)
    assert len(outer_block.statements) == 2
    assert isinstance(outer_block.statements[0], VarDecl)
    inner_block = outer_block.statements[1]
    assert isinstance(inner_block, Block)
    assert len(inner_block.statements) == 1


def test_compound_boolean_expressions():
    # Precedence: || has lower precedence than &&
    # a || b && c should parse as a || (b && c)
    code = "if (a || b && c) { x = 1; }"
    prog = parse_code(code)
    cond = prog.statements[0].condition

    assert isinstance(cond, BinaryOp)
    assert cond.op == "||"
    assert isinstance(cond.left, Identifier)
    assert cond.left.name == "a"
    assert isinstance(cond.right, BinaryOp)
    assert cond.right.op == "&&"
    assert cond.right.left.name == "b"
    assert cond.right.right.name == "c"


def test_unary_operator():
    code = "x = !a + -5;"
    prog = parse_code(code)
    expr = prog.statements[0].expr

    assert isinstance(expr, BinaryOp)
    assert expr.op == "+"
    assert isinstance(expr.left, UnaryOp)
    assert expr.left.op == "!"
    assert isinstance(expr.right, UnaryOp)
    assert expr.right.op == "-"
    assert isinstance(expr.right.operand, NumberLiteral)


def test_syntax_errors():
    # Missing semicolon
    with pytest.raises(ParserError) as exc1:
        parse_code("int a = 5")
    assert "Expected ';'" in str(exc1.value)

    # Missing closing parenthesis
    with pytest.raises(ParserError) as exc2:
        parse_code("if (x > 0 { x = 1; }")
    assert "Expected ')'" in str(exc2.value)

    # Unexpected token
    with pytest.raises(ParserError) as exc3:
        parse_code("int = 5;")
    assert "Expected variable name after type" in str(exc3.value)


def test_ast_json_serialization():
    code = "int a = 10; a = a + 5;"
    prog = parse_code(code)
    json_dict = prog.to_dict()

    assert json_dict["type"] == "Program"
    assert len(json_dict["statements"]) == 2
    assert json_dict["statements"][0]["type"] == "VarDecl"
    assert json_dict["statements"][0]["name"] == "a"
    assert json_dict["statements"][0]["initializer"]["value"] == "10"
    assert json_dict["statements"][1]["type"] == "Assign"
    assert json_dict["statements"][1]["target"] == "a"
    assert json_dict["statements"][1]["expr"]["op"] == "+"
