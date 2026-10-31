"""Three-Address Code (TAC) representation and code generator.

Uses a single unified instruction quadruple representation:
    index: op arg1 arg2 result (or target_label)
Instruction numbering is zero-based and contiguous.

Supports:
- Arithmetic expressions (+, -, *, /, %) with temporary allocation (t1, t2, ...)
- Assignments and initialized variable declarations
- Relational expressions (<, <=, >, >=, ==, !=)
- Short-circuit Boolean evaluation (&&, ||, !) using truelist and falselist
- Control flow for if, if-else, while loops, and blocks
- Dragon Book backpatching procedures via BackpatchEngine
- Final program termination with halt instruction and complete jump resolution.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from compiler.ast_nodes import (
    ASTNode, Program, Block, VarDecl, Assign, IfStmt,
    WhileStmt, BinaryOp, UnaryOp, Identifier, NumberLiteral
)
from compiler.sdt import SDTAnnotator, SemanticError
from compiler.backpatch import BackpatchEngine


@dataclass
class Quadruple:
    """Represents a single three-address code instruction."""
    index: int
    op: str
    arg1: Optional[str] = None
    arg2: Optional[str] = None
    result: Optional[str] = None
    target_label: Optional[str] = None

    def __str__(self) -> str:
        idx_str = f"({self.index})"
        if self.op == "label":
            return f"{idx_str:<6} {self.result}:"
        elif self.op == "goto":
            target = self.target_label if self.target_label is not None else (self.result or "_")
            return f"{idx_str:<6} goto {target}"
        elif self.op.startswith("if_"):
            relop = self.op.replace("if_", "")
            target = self.target_label if self.target_label is not None else (self.result or "_")
            return f"{idx_str:<6} if {self.arg1} {relop} {self.arg2} goto {target}"
        elif self.op == "=":
            return f"{idx_str:<6} {self.result} = {self.arg1}"
        elif self.op in ("u-", "u+"):
            sign = "-" if self.op == "u-" else "+"
            return f"{idx_str:<6} {self.result} = {sign}{self.arg1}"
        elif self.op == "halt":
            return f"{idx_str:<6} halt"
        else:
            return f"{idx_str:<6} {self.result} = {self.arg1} {self.op} {self.arg2}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "op": self.op,
            "arg1": self.arg1,
            "arg2": self.arg2,
            "result": self.result,
            "target": self.target_label,
            "formatted": str(self)
        }


@dataclass
class BoolResult:
    """Carries truelist and falselist for Boolean expressions during backpatching."""
    truelist: List[int]
    falselist: List[int]


class TACGenerator:
    """Generates Three-Address Code with integrated backpatching."""

    def __init__(self, root: ASTNode, initial_temp_count: int = 0):
        self.root = root
        self.instructions: List[Quadruple] = []
        self.temp_count = initial_temp_count
        self.backpatcher = BackpatchEngine(self.instructions)

    def new_temp(self) -> str:
        self.temp_count += 1
        return f"t{self.temp_count}"

    def next_instr(self) -> int:
        """Returns the zero-based index of the next instruction to be emitted."""
        return len(self.instructions)

    def emit(self, op: str, arg1: Optional[str] = None, arg2: Optional[str] = None,
             result: Optional[str] = None, target_label: Optional[str] = None) -> int:
        """Emits a new quadruple instruction and returns its index."""
        idx = len(self.instructions)
        quad = Quadruple(
            index=idx,
            op=op,
            arg1=arg1,
            arg2=arg2,
            result=result,
            target_label=target_label
        )
        self.instructions.append(quad)
        return idx

    def generate(self) -> List[Quadruple]:
        """Translates the AST into Three-Address Code.
        Performs semantic validation first via SDTAnnotator.
        """
        # Run semantic validation to catch undeclared variables or invalid types
        sdt = SDTAnnotator(self.root)
        sdt.annotate()

        # Translate statements and backpatch root nextlist
        prog_nextlist = self._translate_statement(self.root)

        # Final terminal instruction: halt
        halt_index = self.emit("halt")

        # Backpatch any pending jumps to the halt instruction
        if prog_nextlist:
            self.backpatcher.backpatch(prog_nextlist, halt_index)

        # Verify that all jump instructions have valid integer destinations
        self._verify_jump_targets()

        return self.instructions

    def _verify_jump_targets(self) -> None:
        """Ensures no placeholder jumps remain in the generated instruction list."""
        for instr in self.instructions:
            if instr.op == "goto" or instr.op.startswith("if_"):
                if instr.target_label is None or instr.target_label == "_":
                    raise ValueError(f"Unresolved jump target in instruction {instr.index}: {instr}")
                target_idx = int(instr.target_label)
                if not (0 <= target_idx < len(self.instructions)):
                    raise ValueError(
                        f"Jump instruction {instr.index} targets out-of-bounds instruction index {target_idx}"
                    )

    def _translate_statement(self, node: ASTNode) -> List[int]:
        """Translates a statement node into TAC, returning its nextlist."""
        if node is None:
            return []

        if isinstance(node, Program):
            return self._translate_program(node)
        elif isinstance(node, Block):
            return self._translate_block(node)
        elif isinstance(node, VarDecl):
            return self._translate_var_decl(node)
        elif isinstance(node, Assign):
            return self._translate_assign(node)
        elif isinstance(node, IfStmt):
            return self._translate_if(node)
        elif isinstance(node, WhileStmt):
            return self._translate_while(node)
        return []

    def _translate_program(self, node: Program) -> List[int]:
        nextlist: List[int] = []
        for stmt in node.statements:
            if nextlist:
                M = self.next_instr()
                self.backpatcher.backpatch(nextlist, M)
            nextlist = self._translate_statement(stmt)
        return nextlist

    def _translate_block(self, node: Block) -> List[int]:
        nextlist: List[int] = []
        for stmt in node.statements:
            if nextlist:
                M = self.next_instr()
                self.backpatcher.backpatch(nextlist, M)
            nextlist = self._translate_statement(stmt)
        return nextlist

    def _translate_var_decl(self, node: VarDecl) -> List[int]:
        if node.initializer is not None:
            init_addr = self._translate_expr(node.initializer)
            self.emit("=", arg1=init_addr, result=node.name)
        return []

    def _translate_assign(self, node: Assign) -> List[int]:
        rhs_addr = self._translate_expr(node.expr)
        self.emit("=", arg1=rhs_addr, result=node.target)
        return []

    def _translate_if(self, node: IfStmt) -> List[int]:
        # Condition translation produces truelist and falselist
        b_res = self._translate_bool_expr(node.condition)

        # M1: beginning of then_branch
        M1 = self.next_instr()
        self.backpatcher.backpatch(b_res.truelist, M1)
        then_next = self._translate_statement(node.then_branch)

        if node.else_branch is not None:
            # Emit unconditional jump from then_branch over else_branch
            N = self.emit("goto", target_label="_")

            # M2: beginning of else_branch
            M2 = self.next_instr()
            self.backpatcher.backpatch(b_res.falselist, M2)
            else_next = self._translate_statement(node.else_branch)

            # Combined nextlist = then_next + N + else_next
            combined_then = self.backpatcher.merge(then_next, self.backpatcher.makelist(N))
            return self.backpatcher.merge(combined_then, else_next)
        else:
            # No else branch: nextlist = falselist + then_next
            return self.backpatcher.merge(b_res.falselist, then_next)

    def _translate_while(self, node: WhileStmt) -> List[int]:
        # M1: start of condition test
        M1 = self.next_instr()
        b_res = self._translate_bool_expr(node.condition)

        # M2: start of loop body
        M2 = self.next_instr()
        self.backpatcher.backpatch(b_res.truelist, M2)

        # Loop body translation
        body_next = self._translate_statement(node.body)

        # Body next jumps back to loop condition test (M1)
        if body_next:
            self.backpatcher.backpatch(body_next, M1)

        # Unconditional jump back to test M1
        self.emit("goto", target_label=str(M1), result=str(M1))

        # Loop nextlist is the condition's falselist
        return b_res.falselist

    # --- Arithmetic Expression Translation ---

    def _translate_expr(self, node: ASTNode) -> str:
        """Translates an arithmetic expression subtree, emitting TAC instructions.
        Returns the variable name, literal string, or temporary storing the result.
        """
        if isinstance(node, NumberLiteral):
            return node.value

        elif isinstance(node, Identifier):
            return node.name

        elif isinstance(node, UnaryOp):
            operand_addr = self._translate_expr(node.operand)
            temp = self.new_temp()
            if node.op == "-":
                self.emit("u-", arg1=operand_addr, result=temp)
            elif node.op == "+":
                self.emit("u+", arg1=operand_addr, result=temp)
            else:
                self.emit(node.op, arg1=operand_addr, result=temp)
            return temp

        elif isinstance(node, BinaryOp):
            left_addr = self._translate_expr(node.left)
            right_addr = self._translate_expr(node.right)
            temp = self.new_temp()
            self.emit(node.op, arg1=left_addr, arg2=right_addr, result=temp)
            return temp

        return ""

    # --- Short-Circuit Boolean Translation & Backpatching ---

    def _translate_bool_expr(self, node: ASTNode) -> BoolResult:
        """Translates a Boolean expression subtree using short-circuit logic.
        Returns BoolResult(truelist, falselist).
        """
        if isinstance(node, BinaryOp):
            op = node.op

            if op == "&&":
                # B -> B1 && B2
                b1 = self._translate_bool_expr(node.left)
                M = self.next_instr()
                self.backpatcher.backpatch(b1.truelist, M)
                b2 = self._translate_bool_expr(node.right)

                true_list = b2.truelist
                false_list = self.backpatcher.merge(b1.falselist, b2.falselist)
                return BoolResult(true_list, false_list)

            elif op == "||":
                # B -> B1 || B2
                b1 = self._translate_bool_expr(node.left)
                M = self.next_instr()
                self.backpatcher.backpatch(b1.falselist, M)
                b2 = self._translate_bool_expr(node.right)

                true_list = self.backpatcher.merge(b1.truelist, b2.truelist)
                false_list = b2.falselist
                return BoolResult(true_list, false_list)

            elif op in ("<", "<=", ">", ">=", "==", "!="):
                # Relational condition: E1 relop E2
                left_addr = self._translate_expr(node.left)
                right_addr = self._translate_expr(node.right)

                # if left relop right goto _
                true_idx = self.emit(f"if_{op}", arg1=left_addr, arg2=right_addr, target_label="_")
                # goto _
                false_idx = self.emit("goto", target_label="_")

                return BoolResult(
                    truelist=self.backpatcher.makelist(true_idx),
                    falselist=self.backpatcher.makelist(false_idx)
                )

        elif isinstance(node, UnaryOp) and node.op == "!":
            # B -> !B1
            sub_res = self._translate_bool_expr(node.operand)
            return BoolResult(
                truelist=sub_res.falselist,
                falselist=sub_res.truelist
            )

        # Fallback for identifier or expression used as boolean (e.g., if (x))
        addr = self._translate_expr(node)
        true_idx = self.emit("if_!=", arg1=addr, arg2="0", target_label="_")
        false_idx = self.emit("goto", target_label="_")
        return BoolResult(
            truelist=self.backpatcher.makelist(true_idx),
            falselist=self.backpatcher.makelist(false_idx)
        )
