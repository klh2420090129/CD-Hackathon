"""Compiler driver orchestrating all pipeline stages."""

import sys
from typing import Dict, Any
from compiler.lexer import Lexer, LexerError
from compiler.parser import Parser, ParserError
from compiler.sdt import SDTAnnotator
from compiler.postfix import PostfixGenerator
from compiler.tac import TACGenerator


def compile_source(source_code: str) -> Dict[str, Any]:
    """Runs full compilation pipeline on input source code.
    Returns structured results or error payloads.
    """
    try:
        # Stage 1: Lexical Analysis
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()

        # Stage 2: Syntax Analysis (AST Construction)
        parser = Parser(tokens)
        ast = parser.parse()

        # Stage 3: Syntax-Directed Translation
        sdt = SDTAnnotator(ast) if ast else None
        annotated_ast = sdt.annotate() if sdt else None

        # Stage 4: Postfix Generation
        postfix_gen = PostfixGenerator(ast) if ast else None
        postfix_expressions = postfix_gen.generate() if postfix_gen else []

        # Stage 5: Three-Address Code & Backpatching
        tac_gen = TACGenerator(ast) if ast else None
        tac_instructions = tac_gen.generate() if tac_gen else []

        return {
            "success": True,
            "tokens": [t.__dict__ for t in tokens],
            "ast": annotated_ast.to_dict() if annotated_ast else None,
            "postfix": postfix_expressions,
            "tac": [str(instr) for instr in tac_instructions],
            "sdt_trace": sdt.evaluation_trace if sdt else [],
            "error": None
        }
    except (LexerError, ParserError) as err:
        return {
            "success": False,
            "error": {
                "type": err.__class__.__name__,
                "message": err.message,
                "line": err.line,
                "column": err.column
            }
        }
    except Exception as ex:
        return {
            "success": False,
            "error": {
                "type": "GeneralError",
                "message": str(ex),
                "line": 0,
                "column": 0
            }
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m compiler.driver <source_file>")
        sys.exit(1)

    filename = sys.argv[1]
    with open(filename, "r", encoding="utf-8") as f:
        code = f.read()

    result = compile_source(code)
    print("Compilation Result:", result)


if __name__ == "__main__":
    main()

