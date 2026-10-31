"""Backpatching logic for Boolean translation and control flow.

Implements standard Dragon Book backpatching procedures:
- makelist(i): create a list containing single instruction index i
- merge(p1, p2): concatenate two lists of instruction indices
- backpatch(p, target): insert jump target label/index into all instructions in list p

Maintains structured trace logs of all backpatch operations for inspection.
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from compiler.tac import Quadruple


class BackpatchEngine:
    """Manages makelist, merge, and backpatch operations on the shared TAC list."""

    def __init__(self, instructions: List[Any]):
        self.instructions = instructions
        self.events: List[Dict[str, Any]] = []

    def makelist(self, index: int) -> List[int]:
        """Creates a new list containing just the instruction index."""
        res = [index]
        self.events.append({
            "operation": "makelist",
            "indices": [index],
            "target": None,
            "result_list": list(res),
            "explanation": f"Created new jump list with instruction index {index}"
        })
        return res

    def merge(self, list1: Optional[List[int]], list2: Optional[List[int]]) -> List[int]:
        """Concatenates two lists of instruction indices."""
        l1 = list1 if list1 is not None else []
        l2 = list2 if list2 is not None else []
        merged = l1 + [x for x in l2 if x not in l1]
        self.events.append({
            "operation": "merge",
            "indices": list(l1) + list(l2),
            "target": None,
            "result_list": list(merged),
            "explanation": f"Merged jump lists {l1} and {l2} into {merged}"
        })
        return merged

    def backpatch(self, indices: Optional[List[int]], target: int) -> None:
        """Sets the jump destination of each instruction in indices to target."""
        if not indices:
            return

        target_str = str(target)
        patched_indices = []

        for idx in indices:
            if 0 <= idx < len(self.instructions):
                instr = self.instructions[idx]
                instr.target_label = target_str
                instr.result = target_str
                patched_indices.append(idx)
            else:
                raise IndexError(f"Cannot backpatch invalid instruction index {idx}")

        self.events.append({
            "operation": "backpatch",
            "indices": patched_indices,
            "target": target,
            "result_list": patched_indices,
            "explanation": f"Patched instructions {patched_indices} to jump to instruction {target}"
        })
