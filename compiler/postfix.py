"""Postfix notation generator for arithmetic expressions.

Traverses the Abstract Syntax Tree (AST) to generate postfix (Reverse Polish)
representations of all arithmetic expressions in statements and declarations.
Preserves precedence and operator hierarchy through direct AST subtree traversal.
"""

from typing import List, Dict, Any, Optional
from compiler.ast_nodes import (
    ASTNode, Program, Block, VarDecl, Assign, IfStmt,
    WhileStmt, BinaryOp, UnaryOp, Identifier, NumberLiteral
)

ARITHMETIC_OPS = {"+", "-", "*", "/", "%"}


class PostfixGenerator:
    """Generates postfix representations and token sequences from AST expressions."""

    def __init__(self, root: ASTNode):
        self.root = root

    def generate(self) -> List[Dict[str, Any]]:
        """Traverse the AST and extract postfix notation for all arithmetic expressions.
        Returns a list of structured records suitable for display and verification.
        """
        results: List[Dict[str, Any]] = []
        self._collect_statements(self.root, results)
        return results

    def _collect_statements(self, node: Optional[ASTNode], results: List[Dict[str, Any]]) -> None:
        if node is None:
            return

        if isinstance(node, Program) or isinstance(node, Block):
            for stmt in node.statements:
                self._collect_statements(stmt, results)

        elif isinstance(node, VarDecl):
            if node.initializer is not None:
                postfix_tokens = self.expr_to_postfix(node.initializer)
                results.append({
                    "context": f"var {node.name} = ...",
                    "line": node.line,
                    "tokens": postfix_tokens,
                    "postfix": " ".join(postfix_tokens)
                })

        elif isinstance(node, Assign):
            if node.expr is not None:
                postfix_tokens = self.expr_to_postfix(node.expr)
                results.append({
                    "context": f"{node.target} = ...",
                    "line": node.line,
                    "tokens": postfix_tokens,
                    "postfix": " ".join(postfix_tokens)
                })

        elif isinstance(node, IfStmt):
            self._collect_statements(node.then_branch, results)
            if node.else_branch:
                self._collect_statements(node.else_branch, results)

        elif isinstance(node, WhileStmt):
            self._collect_statements(node.body, results)

    def expr_to_postfix(self, expr: ASTNode) -> List[str]:
        """Convert a single expression AST subtree to a list of postfix tokens."""
        tokens: List[str] = []
        self._traverse_expr(expr, tokens)
        return tokens

    def _traverse_expr(self, node: ASTNode, tokens: List[str]) -> None:
        if isinstance(node, NumberLiteral):
            tokens.append(node.value)

        elif isinstance(node, Identifier):
            tokens.append(node.name)

        elif isinstance(node, UnaryOp):
            # For arithmetic postfix, unary '-' is represented as 'u-' or '-'
            self._traverse_expr(node.operand, tokens)
            op_symbol = f"u{node.op}" if node.op in ("+", "-") else node.op
            tokens.append(op_symbol)

        elif isinstance(node, BinaryOp):
            # Postfix order: left, right, op
            self._traverse_expr(node.left, tokens)
            self._traverse_expr(node.right, tokens)
            tokens.append(node.op)
