"""Syntax-Directed Translation (SDT) engine with attribute evaluation.

Evaluates synthesized attributes:
- E.addr: address/name of result (literal, identifier, or temp t1, t2...)
- E.type: inferred datatype ('int' or 'float')
- E.code: list of intermediate 3-address assignment steps (e.g. 't1 = a + b')

Evaluates inherited attributes:
- S.expected_type / E.target_type: datatype context passed down from declarations/assignments
- S.scope_level: nesting level of current block

Performs semantic validation:
- Symbol table lookup for variable declarations and undeclared usage
- Type compatibility checking:
    int op int -> int
    int op float / float op int / float op float -> float
    float assigned to int -> SemanticError
    int assigned to float -> valid (widening)
Records step-by-step evaluation trace detailing node, attribute, direction, and value.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from compiler.ast_nodes import (
    ASTNode, Program, Block, VarDecl, Assign, IfStmt,
    WhileStmt, BinaryOp, UnaryOp, Identifier, NumberLiteral
)


class SemanticError(Exception):
    """Raised on undeclared variables or type mismatches."""
    def __init__(self, message: str, line: int = 0, column: int = 0):
        super().__init__(f"SemanticError at line {line}, column {column}: {message}")
        self.message = message
        self.line = line
        self.column = column


class SDTAnnotator:
    """Performs SDT attribute evaluation and semantic checks on the AST."""

    def __init__(self, root: ASTNode):
        self.root = root
        self.symbol_table: Dict[str, str] = {}  # var_name -> 'int' | 'float'
        self.evaluation_trace: List[Dict[str, Any]] = []
        self.temp_count = 0

    def new_temp(self) -> str:
        self.temp_count += 1
        return f"t{self.temp_count}"

    def _record_trace(self, node: ASTNode, attr_name: str, value: Any,
                      attr_type: str, details: str = "") -> None:
        """Records an attribute evaluation step in the trace."""
        self.evaluation_trace.append({
            "node": node.__class__.__name__,
            "line": node.line,
            "column": node.column,
            "attribute": attr_name,
            "value": str(value),
            "kind": attr_type,  # 'synthesized' or 'inherited'
            "details": details
        })

    def annotate(self) -> ASTNode:
        """Main entry point: evaluates the entire AST."""
        self._evaluate_node(self.root, inherited_attrs={"scope_level": 0})
        return self.root

    def _evaluate_node(self, node: ASTNode, inherited_attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches attribute evaluation based on node type.
        Returns dictionary of synthesized attributes.
        """
        if node is None:
            return {}

        if isinstance(node, Program):
            return self._eval_program(node, inherited_attrs)
        elif isinstance(node, Block):
            return self._eval_block(node, inherited_attrs)
        elif isinstance(node, VarDecl):
            return self._eval_var_decl(node, inherited_attrs)
        elif isinstance(node, Assign):
            return self._eval_assign(node, inherited_attrs)
        elif isinstance(node, IfStmt):
            return self._eval_if(node, inherited_attrs)
        elif isinstance(node, WhileStmt):
            return self._eval_while(node, inherited_attrs)
        elif isinstance(node, BinaryOp):
            return self._eval_binary_op(node, inherited_attrs)
        elif isinstance(node, UnaryOp):
            return self._eval_unary_op(node, inherited_attrs)
        elif isinstance(node, Identifier):
            return self._eval_identifier(node, inherited_attrs)
        elif isinstance(node, NumberLiteral):
            return self._eval_number_literal(node, inherited_attrs)
        return {}

    def _eval_program(self, node: Program, inherited_attrs: Dict[str, Any]) -> Dict[str, Any]:
        scope_level = inherited_attrs.get("scope_level", 0)
        self._record_trace(node, "scope_level", scope_level, "inherited", "Program root scope")

        for stmt in node.statements:
            self._evaluate_node(stmt, inherited_attrs={"scope_level": scope_level})

        return {}

    def _eval_block(self, node: Block, inherited_attrs: Dict[str, Any]) -> Dict[str, Any]:
        scope_level = inherited_attrs.get("scope_level", 0) + 1
        self._record_trace(node, "scope_level", scope_level, "inherited", "Entering nested block")

        for stmt in node.statements:
            self._evaluate_node(stmt, inherited_attrs={"scope_level": scope_level})

        return {}

    def _eval_var_decl(self, node: VarDecl, inherited_attrs: Dict[str, Any]) -> Dict[str, Any]:
        var_name = node.name
        var_type = node.type_name

        self.symbol_table[var_name] = var_type
        self._record_trace(node, "decl_type", var_type, "synthesized", f"Registered variable '{var_name}' as {var_type}")

        if node.initializer is not None:
            # Pass expected type as inherited attribute to initializer
            self._record_trace(node.initializer, "target_type", var_type, "inherited", f"Expected type for {var_name}")
            init_synth = self._evaluate_node(node.initializer, inherited_attrs={"target_type": var_type})

            expr_type = init_synth.get("type", "unknown")
            if var_type == "int" and expr_type == "float":
                raise SemanticError(
                    f"Cannot assign float expression to integer variable '{var_name}'",
                    node.line, node.column
                )

        return {}

    def _eval_assign(self, node: Assign, inherited_attrs: Dict[str, Any]) -> Dict[str, Any]:
        var_name = node.target
        if var_name not in self.symbol_table:
            raise SemanticError(f"Undeclared variable '{var_name}'", node.line, node.column)

        target_type = self.symbol_table[var_name]

        # Pass target_type as inherited attribute to the RHS expression
        self._record_trace(node.expr, "target_type", target_type, "inherited", f"Assignment LHS type for '{var_name}'")
        expr_synth = self._evaluate_node(node.expr, inherited_attrs={"target_type": target_type})

        expr_type = expr_synth.get("type", "unknown")
        if target_type == "int" and expr_type == "float":
            raise SemanticError(
                f"Cannot assign float expression to integer variable '{var_name}'",
                node.line, node.column
            )

        code_step = f"{var_name} = {expr_synth.get('addr')}"
        self._record_trace(node, "Assign.code", code_step, "synthesized", f"Assignment to {var_name}")

        return {"code": [code_step]}

    def _eval_if(self, node: IfStmt, inherited_attrs: Dict[str, Any]) -> Dict[str, Any]:
        # Condition evaluation
        self._evaluate_node(node.condition, inherited_attrs={"target_type": "bool"})
        # Branch evaluations
        self._evaluate_node(node.then_branch, inherited_attrs)
        if node.else_branch:
            self._evaluate_node(node.else_branch, inherited_attrs)
        return {}

    def _eval_while(self, node: WhileStmt, inherited_attrs: Dict[str, Any]) -> Dict[str, Any]:
        self._evaluate_node(node.condition, inherited_attrs={"target_type": "bool"})
        self._evaluate_node(node.body, inherited_attrs)
        return {}

    def _eval_number_literal(self, node: NumberLiteral, inherited_attrs: Dict[str, Any]) -> Dict[str, Any]:
        inferred_type = "float" if node.is_float else "int"
        addr = node.value

        self._record_trace(node, "E.addr", addr, "synthesized", f"Literal value {addr}")
        self._record_trace(node, "E.type", inferred_type, "synthesized", f"Numeric literal type {inferred_type}")
        self._record_trace(node, "E.code", [], "synthesized", "No computation required for literal")

        return {"addr": addr, "type": inferred_type, "code": []}

    def _eval_identifier(self, node: Identifier, inherited_attrs: Dict[str, Any]) -> Dict[str, Any]:
        name = node.name
        if name not in self.symbol_table:
            raise SemanticError(f"Undeclared variable '{name}'", node.line, node.column)

        inferred_type = self.symbol_table[name]
        addr = name

        self._record_trace(node, "E.addr", addr, "synthesized", f"Identifier symbol '{name}'")
        self._record_trace(node, "E.type", inferred_type, "synthesized", f"Symbol table type of '{name}' is {inferred_type}")
        self._record_trace(node, "E.code", [], "synthesized", "No computation required for identifier")

        return {"addr": addr, "type": inferred_type, "code": []}

    def _eval_unary_op(self, node: UnaryOp, inherited_attrs: Dict[str, Any]) -> Dict[str, Any]:
        operand_synth = self._evaluate_node(node.operand, inherited_attrs)

        op = node.op
        operand_type = operand_synth.get("type", "int")
        operand_addr = operand_synth.get("addr", "")
        operand_code = operand_synth.get("code", [])

        if op in ("+", "-"):
            res_type = operand_type
            temp = self.new_temp()
            step = f"{temp} = {op}{operand_addr}"
            code = operand_code + [step]
        elif op == "!":
            res_type = "int"
            temp = self.new_temp()
            step = f"{temp} = !{operand_addr}"
            code = operand_code + [step]
        else:
            res_type = operand_type
            temp = self.new_temp()
            step = f"{temp} = {op} {operand_addr}"
            code = operand_code + [step]

        self._record_trace(node, "E.addr", temp, "synthesized", f"Generated temporary {temp}")
        self._record_trace(node, "E.type", res_type, "synthesized", f"Unary result type {res_type}")
        self._record_trace(node, "E.code", code, "synthesized", f"Step: {step}")

        return {"addr": temp, "type": res_type, "code": code}

    def _eval_binary_op(self, node: BinaryOp, inherited_attrs: Dict[str, Any]) -> Dict[str, Any]:
        left_synth = self._evaluate_node(node.left, inherited_attrs)
        right_synth = self._evaluate_node(node.right, inherited_attrs)

        left_type = left_synth.get("type", "int")
        right_type = right_synth.get("type", "int")
        left_addr = left_synth.get("addr", "")
        right_addr = right_synth.get("addr", "")
        left_code = left_synth.get("code", [])
        right_code = right_synth.get("code", [])

        op = node.op

        # Type inference rule
        if op in ("+", "-", "*", "/", "%"):
            if left_type == "float" or right_type == "float":
                res_type = "float"
            else:
                res_type = "int"
        elif op in ("<", "<=", ">", ">=", "==", "!=", "&&", "||"):
            res_type = "int"  # Boolean expressions evaluate to int representation
        else:
            res_type = "int"

        temp = self.new_temp()
        step = f"{temp} = {left_addr} {op} {right_addr}"
        combined_code = left_code + right_code + [step]

        self._record_trace(node, "E.addr", temp, "synthesized", f"Generated temporary {temp}")
        self._record_trace(node, "E.type", res_type, "synthesized", f"Inferred binary result type: {res_type}")
        self._record_trace(node, "E.code", combined_code, "synthesized", f"Combined SDT code step: {step}")

        return {"addr": temp, "type": res_type, "code": combined_code}
