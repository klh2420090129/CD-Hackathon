"""Regression tests for Milestone 4 & 5 compiler verification."""

import pytest
from compiler.driver import compile_source
from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.tac import TACGenerator


def test_nested_while_loops():
    """Verify nested while loops and backpatching target resolution."""
    code = """
    int i = 0;
    int j = 0;
    int count = 0;
    while (i < 3) {
        j = 0;
        while (j < 3) {
            count = count + 1;
            j = j + 1;
        }
        i = i + 1;
    }
    """
    res = compile_source(code)
    assert res["success"]
    quads = res["tac_quadruples"]

    # Ensure no unresolved jumps and all destinations are within range
    for q in quads:
        if q["op"] == "goto" or q["op"].startswith("if_"):
            target = int(q["target"])
            assert 0 <= target < len(quads)

    # Final instruction must be halt
    assert quads[-1]["op"] == "halt"


def test_while_inside_if():
    """Verify while loop nested inside an if-statement branch."""
    code = """
    int flag = 1;
    int count = 0;
    if (flag == 1) {
        while (count < 5) {
            count = count + 1;
        }
    }
    """
    res = compile_source(code)
    assert res["success"]
    quads = res["tac_quadruples"]

    for q in quads:
        if q["op"] == "goto" or q["op"].startswith("if_"):
            target = int(q["target"])
            assert 0 <= target < len(quads)


def test_complex_nested_booleans():
    """Verify complex nested Boolean expressions: (a < 1 || b > 2) && !(c == 3)."""
    code = """
    int a = 0;
    int b = 3;
    int c = 4;
    int ans = 0;
    if ((a < 1 || b > 2) && !(c == 3)) {
        ans = 100;
    } else {
        ans = 200;
    }
    """
    res = compile_source(code)
    assert res["success"]
    quads = res["tac_quadruples"]

    for q in quads:
        if q["op"] == "goto" or q["op"].startswith("if_"):
            target = int(q["target"])
            assert 0 <= target < len(quads)

    # Check backpatch trace recorded operations
    bp_trace = res["backpatch_trace"]
    assert len(bp_trace) > 0
    ops = [ev["operation"] for ev in bp_trace]
    assert "makelist" in ops
    assert "merge" in ops
    assert "backpatch" in ops


def test_api_malformed_request_handling():
    """Verify driver handles empty string, syntax errors, and semantic errors."""
    # Empty string
    res_empty = compile_source("")
    assert res_empty["success"]
    assert len(res_empty["tac"]) == 1  # Just halt

    # Syntax error
    res_syntax = compile_source("int x = ;")
    assert not res_syntax["success"]
    assert res_syntax["error"]["type"] == "ParserError"

    # Semantic error
    res_semantic = compile_source("int a = b;")
    assert not res_semantic["success"]
    assert res_semantic["error"]["type"] == "SemanticError"
