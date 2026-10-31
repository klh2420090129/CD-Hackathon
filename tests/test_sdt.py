"""Tests for SDTAnnotator and Semantic Analysis module."""

import pytest
from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.sdt import SDTAnnotator, SemanticError


def run_sdt(code: str):
    tokens = Lexer(code).tokenize()
    ast = Parser(tokens).parse()
    annotator = SDTAnnotator(ast)
    annotator.annotate()
    return annotator


def test_integer_literal_type():
    code = "int a = 42;"
    annotator = run_sdt(code)
    assert annotator.symbol_table["a"] == "int"

    # Find trace for literal 42
    lit_trace = [t for t in annotator.evaluation_trace if t["node"] == "NumberLiteral"]
    assert len(lit_trace) > 0
    type_entry = [t for t in lit_trace if t["attribute"] == "E.type"][0]
    assert type_entry["value"] == "int"
    assert type_entry["kind"] == "synthesized"


def test_float_literal_type():
    code = "float b = 3.14;"
    annotator = run_sdt(code)
    assert annotator.symbol_table["b"] == "float"

    lit_trace = [t for t in annotator.evaluation_trace if t["node"] == "NumberLiteral"]
    type_entry = [t for t in lit_trace if t["attribute"] == "E.type"][0]
    assert type_entry["value"] == "float"
    assert type_entry["kind"] == "synthesized"


def test_identifier_type_resolution():
    code = """
    int x;
    float y;
    int z;
    z = x;
    """
    annotator = run_sdt(code)
    assert annotator.symbol_table == {"x": "int", "y": "float", "z": "int"}

    id_traces = [t for t in annotator.evaluation_trace if t["node"] == "Identifier" and t["attribute"] == "E.type"]
    assert any(t["value"] == "int" for t in id_traces)


def test_integer_arithmetic():
    code = """
    int a;
    int b;
    int c;
    c = a + b * 2;
    """
    annotator = run_sdt(code)
    bin_traces = [t for t in annotator.evaluation_trace if t["node"] == "BinaryOp" and t["attribute"] == "E.type"]
    assert len(bin_traces) == 2
    # Both '*' and '+' should be int
    assert all(t["value"] == "int" for t in bin_traces)


def test_mixed_integer_float_arithmetic():
    code = """
    int a;
    float b;
    float c;
    c = a + b;
    """
    annotator = run_sdt(code)
    bin_traces = [t for t in annotator.evaluation_trace if t["node"] == "BinaryOp" and t["attribute"] == "E.type"]
    assert len(bin_traces) == 1
    # int + float promotes to float
    assert bin_traces[0]["value"] == "float"


def test_temporary_generation_and_e_code():
    code = """
    int a;
    int b;
    int c;
    c = a + b;
    """
    annotator = run_sdt(code)
    temp_traces = [t for t in annotator.evaluation_trace if t["attribute"] == "E.addr" and t["node"] == "BinaryOp"]
    assert len(temp_traces) == 1
    assert temp_traces[0]["value"] == "t1"

    code_traces = [t for t in annotator.evaluation_trace if t["attribute"] == "E.code" and t["node"] == "BinaryOp"]
    assert len(code_traces) == 1
    assert "t1 = a + b" in code_traces[0]["value"]


def test_inherited_attribute_propagation():
    code = """
    int a;
    a = 10;
    """
    annotator = run_sdt(code)
    inherited_traces = [t for t in annotator.evaluation_trace if t["kind"] == "inherited"]
    assert len(inherited_traces) > 0
    # target_type should be passed from assignment LHS to RHS
    target_type_entry = [t for t in inherited_traces if t["attribute"] == "target_type"][0]
    assert target_type_entry["value"] == "int"


def test_undeclared_variable_error():
    code = "x = 10;"
    with pytest.raises(SemanticError) as exc_info:
        run_sdt(code)
    assert "Undeclared variable 'x'" in str(exc_info.value)


def test_invalid_assignment_type_error():
    # float cannot be assigned to int variable
    code = """
    int a;
    float b;
    a = b;
    """
    with pytest.raises(SemanticError) as exc_info:
        run_sdt(code)
    assert "Cannot assign float expression to integer variable 'a'" in str(exc_info.value)


def test_valid_widening_assignment():
    # int assigned to float is allowed
    code = """
    float a;
    int b;
    a = b;
    """
    annotator = run_sdt(code)
    assert annotator.symbol_table["a"] == "float"
    assert annotator.symbol_table["b"] == "int"
