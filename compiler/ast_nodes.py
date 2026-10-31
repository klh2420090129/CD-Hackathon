"""Abstract Syntax Tree node definitions."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ASTNode:
    """Base class for all AST nodes."""
    line: int = 0
    column: int = 0
    # SDT attribute containers
    synthesized: Dict[str, Any] = field(default_factory=dict)
    inherited: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to JSON-serializable dictionary."""
        return {
            "type": self.__class__.__name__,
            "line": self.line,
            "column": self.column,
            "synthesized": self.synthesized,
            "inherited": self.inherited,
        }

