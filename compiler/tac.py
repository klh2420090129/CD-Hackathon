"""Three-Address Code (TAC) representation and code generator skeleton."""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Quadruple:
    """Represents a single TAC instruction: result = arg1 op arg2 or control flow."""
    op: str
    arg1: Optional[str] = None
    arg2: Optional[str] = None
    result: Optional[str] = None
    target_label: Optional[str] = None

    def __str__(self) -> str:
        if self.op == "label":
            return f"{self.result}:"
        elif self.op == "goto":
            return f"goto {self.result or self.target_label}"
        elif self.op.startswith("if_"):
            # e.g., if_relop arg1 arg2 goto target
            relop = self.op.replace("if_", "")
            return f"if {self.arg1} {relop} {self.arg2} goto {self.result or self.target_label}"
        elif self.op == "=":
            return f"{self.result} = {self.arg1}"
        else:
            return f"{self.result} = {self.arg1} {self.op} {self.arg2}"


class TACGenerator:
    """Generates Three-Address Code from an AST."""

    def __init__(self, root):
        self.root = root
        self.instructions: List[Quadruple] = []
        self.temp_count = 0
        self.label_count = 0

    def new_temp(self) -> str:
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self) -> str:
        self.label_count += 1
        return f"L{self.label_count}"

    def generate(self) -> List[Quadruple]:
        # Implementation in Milestone 4
        return self.instructions

