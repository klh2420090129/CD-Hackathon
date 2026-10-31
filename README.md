# ThreeAddrGen — Source to Three-Address Code Translator

**PS-06 | Compiler Design Hackathon 2026**

---

## 1. Project Overview & Objectives

**ThreeAddrGen** is an educational, interactive compiler laboratory that translates a restricted C-like source language into Three-Address Code (TAC). 

Key project capabilities:
- **Restricted C-like Language Support:** Type declarations (`int`, `float`), arithmetic assignments, nested expressions with parentheses, relational checks, `if-else` conditionals, `while` loops, and short-circuit Boolean expressions (`&&`, `||`, `!`).
- **Abstract Syntax Tree (AST):** Visual hierarchy displaying expression and statement relationships.
- **Syntax-Directed Translation (SDT):** Real translation attributing synthesized attributes ($E.addr$, $E.type$) and inherited attributes ($S.next$, $B.true$, $B.false$).
- **Postfix Notation:** Operator precedence handling and step-by-step conversion for arithmetic expressions.
- **Three-Address Code Generation:** Quadruple emission with temporary variable allocation ($t_1, t_2, \dots$) and label generation ($L_1, L_2, \dots$).
- **Boolean Translation & Backpatching:** Short-circuit flow using `makelist`, `merge`, and `backpatch` algorithms.
- **Compiler Lab Web Interface:** Modern, clean, browser-based interface built with vanilla HTML/CSS/JavaScript and Python's standard library.

---

## 2. Technology Stack

- **Backend & Compiler Logic:** Python 3.12 (Pure Standard Library: `http.server`, `json`, `dataclasses`, `urllib`).
- **Frontend:** Vanilla HTML5, CSS3, JavaScript (no node_modules or heavy external frameworks).
- **Testing:** Python `unittest` / `pytest`.
- **Version Control:** Git on branch `hackathon/threeaddrgen`.

---

## 3. Directory Structure

```
CD-Hackathon/
├── compiler/
│   ├── __init__.py         # Package initialization
│   ├── lexer.py            # Tokenizer with line & column tracking
│   ├── ast_nodes.py        # Typed AST node structures
│   ├── parser.py           # Recursive-descent parser
│   ├── sdt.py              # SDT engine (Synthesized & Inherited attributes)
│   ├── postfix.py          # Postfix notation emitter
│   ├── tac.py              # TAC instruction model & code generation
│   ├── backpatch.py        # Backpatching list operations (makelist, merge, backpatch)
│   └── driver.py           # Unified compiler entry point
├── web/
│   ├── server.py           # Python HTTP server & /api/compile endpoint
│   └── static/
│       ├── index.html      # Compiler laboratory UI
│       ├── style.css       # Clean IDE theme & styling
│       └── app.js          # Interactive frontend logic & tab switching
├── tests/
│   └── __init__.py         # Test package initialization
├── samples/
│   ├── 01_arithmetic.c              # Basic arithmetic expressions
│   ├── 02_if_else.c                 # If-Else control flow
│   ├── 03_while_loop.c              # While loop control flow
│   └── 04_boolean_short_circuit.c   # Compound Boolean conditions
├── requirements.txt
└── README.md
```

---

## 4. Planned Compilation Pipeline

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

## 5. Installation & Setup

1. **Prerequisites:**
   - Python 3.10+ installed.
   - Modern web browser (Chrome, Edge, Firefox).

2. **Clone & Switch to Branch:**
   ```bash
   git clone https://github.com/klh2420090129/CD-Hackathon.git
   cd CD-Hackathon
   git checkout hackathon/threeaddrgen
   ```

3. **Install Optional Test Runner:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 6. How to Run

### A. Run via Command Line Compiler
To compile any source file directly to TAC via CLI:
```bash
python -m compiler.driver samples/01_arithmetic.c
```

### B. Launch the Interactive Web Laboratory
```bash
python web/server.py 8000
```
Open [http://localhost:8000](http://localhost:8000) in your web browser.

### C. Run Test Suite
```bash
python -m unittest discover tests
# or with pytest
pytest tests/ -v
```
