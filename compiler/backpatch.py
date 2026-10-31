"""Backpatching logic for Boolean translation and control flow."""

from typing import List, Dict, Any
from compiler.tac import Quadruple


class BackpatchEngine:
    """Manages makelist, merge, and backpatch operations on TAC instruction lists."""

    def __init__(self, instructions: List[Quadruple]):
        self.instructions = instructions
        self.events: List[Dict[str, Any]] = []

    def makelist(self, index: int) -> List[int]:
        return [index]

    def merge(self, list1: List[int], list2: List[int]) -> List[int]:
        return list1 + list2

    def backpatch(self, indices: List[int], label: str) -> None:
        for idx in indices:
            if 0 <= idx < len(self.instructions):
                self.instructions[idx].target_label = label
                self.instructions[idx].result = label
                self.events.append({
                    "action": "backpatch",
                    "instruction_index": idx,
                    "target_label": label,
                    "instruction_str": str(self.instructions[idx])
                })

