"""Tests for Three-Address Code generation and Boolean backpatching."""

import pytest
from compiler.driver import compile_source
from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.tac import TACGenerator


def compile_to_tac(code: str):
    tokens = Lexer(code).tokenize()
    ast = Parser(tokens).parse()
    gen = TACGenerator(ast)
    instructions = gen.generate()
    return instructions, gen


def test_simple_assignment_and_declaration():
    code = """
    int a = 10;
    int b;
    b = a;
    """
    instructions, _ = compile_to_tac(code)
    # (0) a = 10
    # (1) b = a
    # (2) halt
    assert len(instructions) == 3
    assert instructions[0].op == "=" and instructions[0].result == "a" and instructions[0].arg1 == "10"
    assert instructions[1].op == "=" and instructions[1].result == "b" and instructions[1].arg1 == "a"
    assert instructions[2].op == "halt"


def test_arithmetic_precedence_tac():
    code = """
    int a;
    int b;
    int c;
    int d;
    a = b + c * d;
    """
    instructions, _ = compile_to_tac(code)
    # Expected:
    # (0) t1 = c * d
    # (1) t2 = b + t1
    # (2) a = t2
    # (3) halt
    assert len(instructions) == 4
    assert instructions[0].op == "*" and instructions[0].arg1 == "c" and instructions[0].arg2 == "d"
    assert instructions[1].op == "+" and instructions[1].arg1 == "b" and instructions[1].arg2 == "t1"
    assert instructions[2].op == "=" and instructions[2].result == "a" and instructions[2].arg1 == "t2"
    assert instructions[3].op == "halt"


def test_parenthesized_arithmetic_tac():
    code = """
    int a;
    int b;
    int c;
    int x;
    x = (a + b) * c;
    """
    instructions, _ = compile_to_tac(code)
    # Expected:
    # (0) t1 = a + b
    # (1) t2 = t1 * c
    # (2) x = t2
    # (3) halt
    assert len(instructions) == 4
    assert instructions[0].op == "+" and instructions[0].arg1 == "a" and instructions[0].arg2 == "b"
    assert instructions[1].op == "*" and instructions[1].arg1 == "t1" and instructions[1].arg2 == "c"
    assert instructions[2].op == "=" and instructions[2].result == "x" and instructions[2].arg1 == "t2"


def test_unary_arithmetic_tac():
    code = """
    int a;
    int b;
    b = -a + 5;
    """
    instructions, _ = compile_to_tac(code)
    # Expected:
    # (0) t1 = -a
    # (1) t2 = t1 + 5
    # (2) b = t2
    # (3) halt
    assert len(instructions) == 4
    assert instructions[0].op == "u-" and instructions[0].arg1 == "a"
    assert instructions[1].op == "+" and instructions[1].arg1 == "t1" and instructions[1].arg2 == "5"
    assert instructions[2].op == "=" and instructions[2].result == "b" and instructions[2].arg1 == "t2"


def test_relational_condition_if():
    code = """
    int x;
    int y;
    if (x < y) {
        x = x + 1;
    }
    """
    instructions, gen = compile_to_tac(code)
    # Expected:
    # (0) if x < y goto 2
    # (1) goto 4
    # (2) t1 = x + 1
    # (3) x = t1
    # (4) halt
    assert instructions[0].op == "if_<" and instructions[0].target_label == "2"
    assert instructions[1].op == "goto" and instructions[1].target_label == "4"
    assert instructions[2].op == "+"
    assert instructions[3].op == "="
    assert instructions[4].op == "halt"


def test_if_else_control_flow():
    code = """
    int x;
    int y;
    if (x < y) {
        x = 1;
    } else {
        y = 2;
    }
    """
    instructions, _ = compile_to_tac(code)
    # Expected:
    # (0) if x < y goto 2
    # (1) goto 4
    # (2) x = 1
    # (3) goto 5
    # (4) y = 2
    # (5) halt
    assert instructions[0].op == "if_<" and instructions[0].target_label == "2"
    assert instructions[1].op == "goto" and instructions[1].target_label == "4"
    assert instructions[2].op == "=" and instructions[2].result == "x"
    assert instructions[3].op == "goto" and instructions[3].target_label == "5"
    assert instructions[4].op == "=" and instructions[4].result == "y"
    assert instructions[5].op == "halt"


def test_while_loop_control_flow():
    code = """
    int i = 0;
    while (i < 10) {
        i = i + 1;
    }
    """
    instructions, _ = compile_to_tac(code)
    # Expected:
    # (0) i = 0
    # (1) if i < 10 goto 3
    # (2) goto 6
    # (3) t1 = i + 1
    # (4) i = t1
    # (5) goto 1
    # (6) halt
    assert instructions[0].op == "=" and instructions[0].result == "i"
    assert instructions[1].op == "if_<" and instructions[1].target_label == "3"
    assert instructions[2].op == "goto" and instructions[2].target_label == "6"
    assert instructions[3].op == "+"
    assert instructions[4].op == "="
    assert instructions[5].op == "goto" and instructions[5].target_label == "1"
    assert instructions[6].op == "halt"


def test_short_circuit_and():
    # if (a < 10 && b > 5) x = 1;
    code = """
    int a;
    int b;
    int x;
    if (a < 10 && b > 5) {
        x = 1;
    }
    """
    instructions, _ = compile_to_tac(code)
    # (0) if a < 10 goto 2
    # (1) goto 5
    # (2) if b > 5 goto 4
    # (3) goto 5
    # (4) x = 1
    # (5) halt
    assert instructions[0].op == "if_<" and instructions[0].target_label == "2"
    assert instructions[1].op == "goto" and instructions[1].target_label == "5"
    assert instructions[2].op == "if_>" and instructions[2].target_label == "4"
    assert instructions[3].op == "goto" and instructions[3].target_label == "5"
    assert instructions[4].result == "x"
    assert instructions[5].op == "halt"


def test_short_circuit_or():
    # if (a < 10 || b > 5) x = 1;
    code = """
    int a;
    int b;
    int x;
    if (a < 10 || b > 5) {
        x = 1;
    }
    """
    instructions, _ = compile_to_tac(code)
    # (0) if a < 10 goto 4
    # (1) goto 2
    # (2) if b > 5 goto 4
    # (3) goto 5
    # (4) x = 1
    # (5) halt
    assert instructions[0].op == "if_<" and instructions[0].target_label == "4"
    assert instructions[1].op == "goto" and instructions[1].target_label == "2"
    assert instructions[2].op == "if_>" and instructions[2].target_label == "4"
    assert instructions[3].op == "goto" and instructions[3].target_label == "5"
    assert instructions[4].result == "x"
    assert instructions[5].op == "halt"


def test_logical_not():
    code = """
    int a;
    int x;
    if (!(a == 0)) {
        x = 1;
    }
    """
    instructions, _ = compile_to_tac(code)
    # a == 0 has true at 0, false at 1
    # ! swaps them: true is 1, false is 0
    # True should lead to then branch (x = 1)
    # (0) if a == 0 goto 3 (false destination)
    # (1) goto 2           (true destination)
    # (2) x = 1
    # (3) halt
    assert instructions[0].op == "if_==" and instructions[0].target_label == "3"
    assert instructions[1].op == "goto" and instructions[1].target_label == "2"
    assert instructions[2].result == "x"
    assert instructions[3].op == "halt"


def test_nested_if_in_while():
    code = """
    int i = 0;
    while (i < 5) {
        if (i == 2) {
            i = 10;
        }
        i = i + 1;
    }
    """
    instructions, gen = compile_to_tac(code)
    # Verify no unpatched jumps
    for instr in instructions:
        if instr.op == "goto" or instr.op.startswith("if_"):
            assert instr.target_label is not None
            assert instr.target_label != "_"
            target_idx = int(instr.target_label)
            assert 0 <= target_idx < len(instructions)


def test_semantic_error_blocks_tac():
    # Undeclared variable should raise error during compile_source
    code = "x = 10;"
    result = compile_source(code)
    assert not result["success"]
    assert result["error"]["type"] == "SemanticError"
    assert "Undeclared variable 'x'" in result["error"]["message"]


def test_invalid_type_blocks_tac():
    code = """
    int a;
    float b = 2.5;
    a = b;
    """
    result = compile_source(code)
    assert not result["success"]
    assert result["error"]["type"] == "SemanticError"
    assert "Cannot assign float" in result["error"]["message"]
