"""Tests for BackpatchEngine primitive operations."""

import pytest
from compiler.tac import Quadruple
from compiler.backpatch import BackpatchEngine


def test_makelist():
    instructions = [Quadruple(index=0, op="goto", target_label="_")]
    engine = BackpatchEngine(instructions)

    l = engine.makelist(0)
    assert l == [0]
    assert len(engine.events) == 1
    assert engine.events[0]["operation"] == "makelist"
    assert engine.events[0]["indices"] == [0]


def test_merge():
    instructions = [
        Quadruple(index=0, op="goto", target_label="_"),
        Quadruple(index=1, op="goto", target_label="_")
    ]
    engine = BackpatchEngine(instructions)

    l1 = engine.makelist(0)
    l2 = engine.makelist(1)
    merged = engine.merge(l1, l2)
    assert merged == [0, 1]

    # Test merge with duplicate
    merged_dup = engine.merge([0, 1], [1, 2])
    assert merged_dup == [0, 1, 2]


def test_backpatch_success():
    instructions = [
        Quadruple(index=0, op="if_<", arg1="x", arg2="y", target_label="_"),
        Quadruple(index=1, op="goto", target_label="_"),
        Quadruple(index=2, op="halt")
    ]
    engine = BackpatchEngine(instructions)

    engine.backpatch([0], 2)
    assert instructions[0].target_label == "2"
    assert instructions[0].result == "2"
    assert str(instructions[0]).strip().endswith("goto 2")

    engine.backpatch([1], 2)
    assert instructions[1].target_label == "2"
    assert instructions[1].result == "2"
    assert str(instructions[1]).strip().endswith("goto 2")

    assert len(engine.events) == 2


def test_backpatch_invalid_index():
    instructions = [Quadruple(index=0, op="halt")]
    engine = BackpatchEngine(instructions)

    with pytest.raises(IndexError):
        engine.backpatch([99], 0)
