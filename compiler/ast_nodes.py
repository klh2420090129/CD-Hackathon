"""Abstract Syntax Tree node definitions for restricted C-like language.

All nodes are structured, strongly-typed dataclasses that can be recursively
serialized to JSON-compatible dictionaries for visualization and verification.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ASTNode:
    """Base class for all AST nodes with source coordinates."""
    line: int = 0
    column: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to JSON-serializable dictionary."""
        raise NotImplementedError(f"to_dict not implemented for {self.__class__.__name__}")


@dataclass
class Program(ASTNode):
    """Root node containing a list of top-level statements/declarations."""
    statements: List[ASTNode] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "Program",
            "line": self.line,
            "column": self.column,
            "statements": [stmt.to_dict() for stmt in self.statements],
        }


@dataclass
class Block(ASTNode):
    """Compound statement block { stmt1; stmt2; ... }."""
    statements: List[ASTNode] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "Block",
            "line": self.line,
            "column": self.column,
            "statements": [stmt.to_dict() for stmt in self.statements],
        }


@dataclass
class VarDecl(ASTNode):
    """Variable declaration: type_name identifier [= initializer];"""
    type_name: str = ""
    name: str = ""
    initializer: Optional[ASTNode] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "VarDecl",
            "line": self.line,
            "column": self.column,
            "type_name": self.type_name,
            "name": self.name,
            "initializer": self.initializer.to_dict() if self.initializer else None,
        }


@dataclass
class Assign(ASTNode):
    """Assignment statement: target = expression;"""
    target: str = ""
    expr: Optional[ASTNode] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "Assign",
            "line": self.line,
            "column": self.column,
            "target": self.target,
            "expr": self.expr.to_dict() if self.expr else None,
        }


@dataclass
class IfStmt(ASTNode):
    """If statement: if (condition) then_branch [else else_branch]"""
    condition: Optional[ASTNode] = None
    then_branch: Optional[ASTNode] = None
    else_branch: Optional[ASTNode] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "IfStmt",
            "line": self.line,
            "column": self.column,
            "condition": self.condition.to_dict() if self.condition else None,
            "then_branch": self.then_branch.to_dict() if self.then_branch else None,
            "else_branch": self.else_branch.to_dict() if self.else_branch else None,
        }


@dataclass
class WhileStmt(ASTNode):
    """While loop: while (condition) body"""
    condition: Optional[ASTNode] = None
    body: Optional[ASTNode] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "WhileStmt",
            "line": self.line,
            "column": self.column,
            "condition": self.condition.to_dict() if self.condition else None,
            "body": self.body.to_dict() if self.body else None,
        }


@dataclass
class BinaryOp(ASTNode):
    """Binary operation: left op right (arithmetic, relational, or logical)."""
    op: str = ""
    left: Optional[ASTNode] = None
    right: Optional[ASTNode] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "BinaryOp",
            "line": self.line,
            "column": self.column,
            "op": self.op,
            "left": self.left.to_dict() if self.left else None,
            "right": self.right.to_dict() if self.right else None,
        }


@dataclass
class UnaryOp(ASTNode):
    """Unary operation: op operand (!, +, -)."""
    op: str = ""
    operand: Optional[ASTNode] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "UnaryOp",
            "line": self.line,
            "column": self.column,
            "op": self.op,
            "operand": self.operand.to_dict() if self.operand else None,
        }


@dataclass
class Identifier(ASTNode):
    """Variable reference."""
    name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "Identifier",
            "line": self.line,
            "column": self.column,
            "name": self.name,
        }


@dataclass
class NumberLiteral(ASTNode):
    """Numeric literal (int or float)."""
    value: str = ""
    is_float: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "NumberLiteral",
            "line": self.line,
            "column": self.column,
            "value": self.value,
            "is_float": self.is_float,
        }
