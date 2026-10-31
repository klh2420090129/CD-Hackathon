# ThreeAddrGen — Source to Three-Address Code Translator

**PS-06 | Compiler Design Hackathon 2026**

---

## 1. Project Overview & Objectives

**ThreeAddrGen** is a complete, educational, and interactive compiler laboratory that translates a restricted C-like source language into Three-Address Code (TAC).

### Key Compiler Features
- **Restricted C-like Language Support:** Type declarations (`int`, `float`), arithmetic assignments, nested expressions with parentheses, relational checks (`<`, `<=`, `>`, `>=`, `==`, `!=`), `if-else` conditionals, `while` loops, and short-circuit Boolean expressions (`&&`, `||`, `!`).
- **Abstract Syntax Tree (AST):** Visual expandable/collapsible tree displaying expression and statement relationships.
- **Syntax-Directed Translation (SDT):** Real translation attributing synthesized attributes ($E.addr$, $E.type$, $E.code$) and inherited attributes ($S.\text{target\_type}$, $\text{scope\_level}$).
- **Postfix Notation:** Operator precedence handling and step-by-step conversion for arithmetic expressions.
- **Three-Address Code Generation:** Quadruple emission with temporary variable allocation ($t_1, t_2, \dots$) and zero-based contiguous instruction numbering.
- **Boolean Translation & Backpatching:** Short-circuit control flow using textbook `makelist`, `merge`, and `backpatch` algorithms.
- **Compiler Lab Web Interface:** Modern, clean, browser-based developer laboratory built with vanilla HTML5/CSS/JavaScript and Python's standard library.

---

## 2. Technology Stack

- **Backend & Compiler Logic:** Python 3.12 (Pure Standard Library: `http.server`, `json`, `dataclasses`, `urllib`).
- **Frontend:** Vanilla HTML5, CSS3, JavaScript (zero external node dependencies).
- **Testing:** Python `pytest` and `unittest`.
- **Version Control:** Git on branch `hackathon/threeaddrgen`.

---

## 3. Directory Structure

```
CD-Hackathon/
├── compiler/
│   ├── __init__.py         # Package initialization
│   ├── lexer.py            # Tokenizer with line & column tracking
│   ├── ast_nodes.py        # Typed AST node structures with .to_dict()
│   ├── parser.py           # Recursive-descent parser
│   ├── sdt.py              # SDT engine (Synthesized & Inherited attributes)
│   ├── postfix.py          # Postfix notation emitter
│   ├── tac.py              # Quadruple model & TAC code generation
│   ├── backpatch.py        # Backpatching list operations (makelist, merge, backpatch)
│   └── driver.py           # Unified compilation pipeline
├── web/
│   ├── server.py           # Python HTTP server & /api/compile, /api/samples
│   └── static/
│       ├── index.html      # Compiler laboratory UI
│       ├── style.css       # Clean IDE theme & styling
│       └── app.js          # Interactive frontend logic & visualizers
├── tests/
│   ├── __init__.py
│   ├── test_lexer.py       # Lexer unit tests
│   ├── test_parser.py      # Parser and AST tests
│   ├── test_postfix.py     # Postfix generation tests
│   ├── test_sdt.py         # SDT and type checking tests
│   ├── test_tac.py         # TAC generation and control flow tests
│   ├── test_backpatch.py   # Backpatching primitive tests
│   └── test_regression.py  # Nested control flow and API regression tests
├── samples/
│   ├── 01_arithmetic.c              # Basic arithmetic expressions
│   ├── 02_if_else.c                 # If-Else control flow
│   ├── 03_while_loop.c              # While loop control flow
│   └── 04_boolean_short_circuit.c   # Compound Boolean conditions
├── requirements.txt
└── README.md
```

---

## 4. Compilation Pipeline

```
Source Code (.c)
       │
       ▼
 [1. Lexer] ─────────────► Tokens + Line/Column positions
       │
       ▼
 [2. Parser] ────────────► Abstract Syntax Tree (AST)
       │
       ├─────────────────► [3. Postfix Generator] ──► Postfix Expressions
       │
       ├─────────────────► [4. SDT Annotator] ────► Synthesized & Inherited Attributes
       │
       ▼
 [5. TAC Generator & Backpatching Engine] ────────► Three-Address Code Quadruples
```

---

## 5. Overview of UI Output Panels

1. **Three-Address Code:** Color-coded list of generated instructions (`Assignment`, `Arithmetic`, `Conditional Jump`, `Unconditional Jump`, `Halt`).
2. **AST Tree:** Interactive, expandable/collapsible tree showing syntax nodes, operators, and statement hierarchy.
3. **Postfix:** Contextual table displaying arithmetic expressions in Reverse Polish Notation.
4. **SDT Attributes:** Step-by-step trace showing each attribute evaluation event, attribute name, direction (`synthesized` vs `inherited`), and computed value.
5. **Symbol Table:** Variable registry displaying declared identifiers, datatypes, and scope.
6. **Backpatching:** Chronological log of `makelist`, `merge`, and `backpatch` operations with targets and explanations.
7. **Tokens:** Table of all scanned lexical tokens with lexemes, line numbers, and column offsets.

---

## 6. How to Run the Application & Tests

### A. Launch Interactive Compiler Laboratory (Browser)
```bash
python web/server.py 8000
```
Open **[http://localhost:8000](http://localhost:8000)** in any modern web browser.

### B. Run via Command Line Compiler
```bash
python -m compiler.driver samples/01_arithmetic.c
```

### C. Run All Test Suites
```bash
pytest tests/ -v
# or
python -m unittest discover tests
```
All 57 unit and regression tests will execute.
