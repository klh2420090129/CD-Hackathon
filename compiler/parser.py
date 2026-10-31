"""Recursive-descent parser for restricted C-like language.

Grammar:
    Program        ::= Statement* EOF
    Statement      ::= VarDeclStmt | AssignStmt | IfStmt | WhileStmt | Block
    Block          ::= "{" Statement* "}"
    VarDeclStmt    ::= ("int" | "float") IDENTIFIER ("=" Expr)? ";"
    AssignStmt     ::= IDENTIFIER "=" Expr ";"
    IfStmt         ::= "if" "(" Expr ")" Statement ("else" Statement)?
    WhileStmt      ::= "while" "(" Expr ")" Statement

Precedence of Expressions (Lowest to Highest):
    Expr           ::= LogicalOr
    LogicalOr      ::= LogicalAnd ("||" LogicalAnd)*
    LogicalAnd     ::= Equality ("&&" Equality)*
    Equality       ::= Relational (("==" | "!=") Relational)*
    Relational     ::= Additive (("<" | "<=" | ">" | ">=") Additive)*
    Additive       ::= Multiplicative (("+" | "-") Multiplicative)*
    Multiplicative ::= Unary (("*" | "/" | "%") Unary)*
    Unary          ::= ("!" | "-" | "+") Unary | Primary
    Primary        ::= IDENTIFIER | INT_LITERAL | FLOAT_LITERAL | "(" Expr ")"
"""

from typing import List, Optional
from compiler.lexer import Token
from compiler.ast_nodes import (
    ASTNode, Program, Block, VarDecl, Assign, IfStmt,
    WhileStmt, BinaryOp, UnaryOp, Identifier, NumberLiteral
)


class ParserError(Exception):
    """Raised when syntax fails grammar validation."""
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"ParserError at line {line}, column {column}: {message}")
        self.message = message
        self.line = line
        self.column = column


class Parser:
    """Recursive-descent parser producing structured AST nodes."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.length = len(tokens)

    def _current(self) -> Token:
        if self.pos < self.length:
            return self.tokens[self.pos]
        return self.tokens[-1]

    def _peek_type(self, offset: int = 0) -> str:
        idx = self.pos + offset
        if idx < self.length:
            return self.tokens[idx].type
        return "EOF"

    def _match(self, *expected_types: str) -> bool:
        return self._current().type in expected_types

    def _consume(self, expected_type: str, err_message: str) -> Token:
        curr = self._current()
        if curr.type != expected_type:
            raise ParserError(
                f"{err_message}. Expected '{expected_type}', found '{curr.type}' ({curr.value!r})",
                curr.line,
                curr.column,
            )
        self.pos += 1
        return curr

    def parse(self) -> Program:
        """Entry point: parses Program ::= Statement* EOF."""
        start_line = self._current().line
        start_col = self._current().column
        statements: List[ASTNode] = []

        while not self._match("EOF"):
            statements.append(self._statement())

        return Program(line=start_line, column=start_col, statements=statements)

    def _statement(self) -> ASTNode:
        curr = self._current()

        if self._match("INT", "FLOAT"):
            return self._var_decl()
        elif self._match("IDENTIFIER"):
            return self._assignment()
        elif self._match("IF"):
            return self._if_statement()
        elif self._match("WHILE"):
            return self._while_statement()
        elif self._match("LBRACE"):
            return self._block()
        else:
            raise ParserError(
                f"Unexpected token in statement: '{curr.value}'",
                curr.line,
                curr.column,
            )

    def _block(self) -> Block:
        lbrace = self._consume("LBRACE", "Expected '{' to start block")
        statements: List[ASTNode] = []
        while not self._match("RBRACE") and not self._match("EOF"):
            statements.append(self._statement())
        self._consume("RBRACE", "Expected '}' to close block")
        return Block(line=lbrace.line, column=lbrace.column, statements=statements)

    def _var_decl(self) -> VarDecl:
        type_tok = self._current()
        self.pos += 1
        id_tok = self._consume("IDENTIFIER", "Expected variable name after type")

        initializer: Optional[ASTNode] = None
        if self._match("ASSIGN"):
            self.pos += 1
            initializer = self._expr()

        self._consume("SEMICOLON", "Expected ';' after variable declaration")
        return VarDecl(
            line=type_tok.line,
            column=type_tok.column,
            type_name=type_tok.value,
            name=id_tok.value,
            initializer=initializer,
        )

    def _assignment(self) -> Assign:
        id_tok = self._consume("IDENTIFIER", "Expected identifier in assignment")
        self._consume("ASSIGN", "Expected '=' in assignment")
        expr_node = self._expr()
        self._consume("SEMICOLON", "Expected ';' after assignment")
        return Assign(
            line=id_tok.line,
            column=id_tok.column,
            target=id_tok.value,
            expr=expr_node,
        )

    def _if_statement(self) -> IfStmt:
        if_tok = self._consume("IF", "Expected 'if'")
        self._consume("LPAREN", "Expected '(' after 'if'")
        condition = self._expr()
        self._consume("RPAREN", "Expected ')' after if-condition")

        then_branch = self._statement()
        else_branch: Optional[ASTNode] = None
        if self._match("ELSE"):
            self.pos += 1
            else_branch = self._statement()

        return IfStmt(
            line=if_tok.line,
            column=if_tok.column,
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch,
        )

    def _while_statement(self) -> WhileStmt:
        while_tok = self._consume("WHILE", "Expected 'while'")
        self._consume("LPAREN", "Expected '(' after 'while'")
        condition = self._expr()
        self._consume("RPAREN", "Expected ')' after while-condition")
        body = self._statement()

        return WhileStmt(
            line=while_tok.line,
            column=while_tok.column,
            condition=condition,
            body=body,
        )

    # --- Expression Parsing with Precedence & Associativity ---

    def _expr(self) -> ASTNode:
        return self._logical_or()

    def _logical_or(self) -> ASTNode:
        node = self._logical_and()
        while self._match("OR"):
            op_tok = self._current()
            self.pos += 1
            right = self._logical_and()
            node = BinaryOp(
                line=op_tok.line,
                column=op_tok.column,
                op=op_tok.value,
                left=node,
                right=right,
            )
        return node

    def _logical_and(self) -> ASTNode:
        node = self._equality()
        while self._match("AND"):
            op_tok = self._current()
            self.pos += 1
            right = self._equality()
            node = BinaryOp(
                line=op_tok.line,
                column=op_tok.column,
                op=op_tok.value,
                left=node,
                right=right,
            )
        return node

    def _equality(self) -> ASTNode:
        node = self._relational()
        while self._match("EQ", "NE"):
            op_tok = self._current()
            self.pos += 1
            right = self._relational()
            node = BinaryOp(
                line=op_tok.line,
                column=op_tok.column,
                op=op_tok.value,
                left=node,
                right=right,
            )
        return node

    def _relational(self) -> ASTNode:
        node = self._additive()
        while self._match("LT", "LE", "GT", "GE"):
            op_tok = self._current()
            self.pos += 1
            right = self._additive()
            node = BinaryOp(
                line=op_tok.line,
                column=op_tok.column,
                op=op_tok.value,
                left=node,
                right=right,
            )
        return node

    def _additive(self) -> ASTNode:
        node = self._multiplicative()
        while self._match("PLUS", "MINUS"):
            op_tok = self._current()
            self.pos += 1
            right = self._multiplicative()
            node = BinaryOp(
                line=op_tok.line,
                column=op_tok.column,
                op=op_tok.value,
                left=node,
                right=right,
            )
        return node

    def _multiplicative(self) -> ASTNode:
        node = self._unary()
        while self._match("STAR", "SLASH", "PERCENT"):
            op_tok = self._current()
            self.pos += 1
            right = self._unary()
            node = BinaryOp(
                line=op_tok.line,
                column=op_tok.column,
                op=op_tok.value,
                left=node,
                right=right,
            )
        return node

    def _unary(self) -> ASTNode:
        if self._match("NOT", "MINUS", "PLUS"):
            op_tok = self._current()
            self.pos += 1
            operand = self._unary()
            return UnaryOp(
                line=op_tok.line,
                column=op_tok.column,
                op=op_tok.value,
                operand=operand,
            )
        return self._primary()

    def _primary(self) -> ASTNode:
        curr = self._current()

        if self._match("INT_LITERAL"):
            self.pos += 1
            return NumberLiteral(
                line=curr.line,
                column=curr.column,
                value=curr.value,
                is_float=False,
            )
        elif self._match("FLOAT_LITERAL"):
            self.pos += 1
            return NumberLiteral(
                line=curr.line,
                column=curr.column,
                value=curr.value,
                is_float=True,
            )
        elif self._match("IDENTIFIER"):
            self.pos += 1
            return Identifier(
                line=curr.line,
                column=curr.column,
                name=curr.value,
            )
        elif self._match("LPAREN"):
            self.pos += 1
            expr_node = self._expr()
            self._consume("RPAREN", "Expected ')' to close parenthesized expression")
            return expr_node
        else:
            raise ParserError(
                f"Expected primary expression (identifier, number, or '('), found '{curr.type}' ({curr.value!r})",
                curr.line,
                curr.column,
            )
