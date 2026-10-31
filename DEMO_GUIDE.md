# ThreeAddrGen — Demonstration & Presentation Guide

**Problem Statement:** PS-06 — Source to Three-Address Code Translator  
**Hackathon:** Compiler Design Hackathon 2026

---

## 1. Project Introduction

**ThreeAddrGen** is a complete, educational, and interactive compiler laboratory that translates a restricted C-like programming language into Three-Address Code (TAC). 

Designed following classical compiler construction principles (Aho, Lam, Sethi, Ullman — *The Dragon Book*), it bridges the gap between high-level language syntax and intermediate code generation through:
- Direct AST generation via recursive descent.
- Syntax-Directed Translation (SDT) with explicit synthesized and inherited attributes.
- Postfix (Reverse Polish) expression translation preserving AST precedence.
- Quadruple-based TAC emission.
- Textbook Boolean backpatching (`makelist`, `merge`, `backpatch`) for short-circuit evaluation.

---

## 2. Compilation Pipeline

```
           Source Code (.c)
                  │
                  ▼
         [1. Lexical Analyzer]
         • Longest-match tokenization
         • Line & column tracking
         • Comments & error reporting
                  │
                  ▼ Tokens
         [2. Recursive-Descent Parser]
         • Documented grammar
         • Explicit operator precedence hierarchy
                  │
                  ▼ Abstract Syntax Tree (AST)
        ┌─────────┴───────────────────────┐
        ▼                                 ▼
[3. Postfix Generator]           [4. SDT Annotator]
• Reverse Polish Notation        • Inferred Types (E.type)
• Respects AST operator tree     • Result Temporaries (E.addr)
                                 • Symbol Table Validation
                                 • Inherited Attributes (target_type)
                                          │
                                          ▼ Validated AST
                         [5. TAC & Backpatching Engine]
                         • Quadruple intermediate code
                         • truelist & falselist evaluation
                         • makelist(), merge(), backpatch()
                         • Terminal halt instruction
```

---

## 3. Recommended 3-Minute Hackathon Demonstration Script

### Step 1: Introduction (30 seconds)
- Open `http://localhost:8000/`.
- Introduce PS-06: *"ThreeAddrGen translates restricted C-like code into intermediate Three-Address Code while visually exposing every internal compiler phase: Lexer tokens, AST hierarchy, Postfix notation, SDT attribute evaluation, and Boolean backpatching."*

### Step 2: Arithmetic Expressions & Precedence (45 seconds)
- Select preset: `01_arithmetic.c`.
- Point out expression: `c = a + b * (c - 5) / 2;`
- Click **"Compile Program"**.
- View **Three-Address Code** tab: show how the operations evaluate in exact precedence order:
  - `(2) t1 = c - 5`
  - `(3) t2 = b * t1`
  - `(4) t3 = t2 / 2`
  - `(5) t4 = a + t3`
  - `(6) c = t4`
- Click **"Postfix"** tab: show `a b c 5 - * 2 / +`.
- Click **"AST Tree"** tab: show the interactive hierarchy and click **"Collapse All" / "Expand All"** to illustrate parent-child syntax structure.

### Step 3: Syntax-Directed Translation & Attributes (30 seconds)
- Click **"SDT Attributes"** tab:
  - Point to **Inherited attributes** (`target_type: int`, `scope_level: 0`) flowing top-down.
  - Point to **Synthesized attributes** (`E.addr`, `E.type`, `E.code`) synthesized bottom-up.
- Click **"Symbol Table"** tab: show registered variable symbols `a`, `b`, `c` and their datatypes.

### Step 4: Boolean Short-Circuit Evaluation & Backpatching (45 seconds)
- Select preset: `04_boolean_short_circuit.c`.
- Source condition: `if ((p < 10 && q > 5) || r != 0) { r = 1; } else { r = 2; }`
- Click **"Compile Program"**.
- View **Three-Address Code** tab:
  - Show short-circuit jumps: `if p < 10 goto 5`, `goto 7`, `if q > 5 goto 9`. Notice how evaluating `false` on `p < 10` skips `q > 5` directly to `r != 0` at index 7!
- Click **"Backpatching"** tab:
  - Highlight chronological operations: `makelist`, `merge`, and `backpatch`.
  - Explain how unresolved jump targets are backpatched once label destinations are discovered.

### Step 5: Semantic & Syntax Validation (30 seconds)
- Click **"Clear"** or edit the code:
  - Enter: `int a; float b; a = b;`
  - Click **"Compile Program"**.
  - Show the clean error notification: `SemanticError: Cannot assign float expression to integer variable 'a' (Line 1, Col 17)`.
- Conclude: *"All 57 test cases pass, verifying edge cases, nested loops, and full pipeline integrity."*

---

## 4. Technical Concepts Reference for Judges

- **Recursive-Descent Parsing:** Top-down parsing technique where each non-terminal in the formal grammar corresponds to a Python function in `compiler/parser.py`.
- **Operator Precedence:** Enforced via nested grammar rules: `Primary` $\to$ `Unary` $\to$ `Multiplicative` $\to$ `Additive` $\to$ `Relational` $\to$ `Equality` $\to$ `LogicalAnd` $\to$ `LogicalOr`.
- **Synthesized Attributes:** Computed bottom-up from child nodes (e.g., $E.\text{addr}$ holds the temporary variable storing the subtree's value, $E.\text{type}$ holds the inferred datatype).
- **Inherited Attributes:** Passed top-down from parent or sibling nodes (e.g., $S.\text{target\_type}$ passed from an assignment LHS to validate RHS expression type compatibility).
- **Three-Address Code (TAC):** Quadruple representation where each instruction has at most one operator and at most three addresses (e.g., `(op, arg1, arg2, result)`).
- **Backpatching (`makelist`, `merge`, `backpatch`):** Passes lists of unresolved jump instruction indices as synthesized attributes; when the target instruction index is known, `backpatch()` fills in all pending targets in a single pass without multi-pass label resolution.
- **Short-Circuit Evaluation:** In $A \text{ \&\& } B$, if $A$ evaluates to false, $B$ is never executed; in $A \text{ || } B$, if $A$ evaluates to true, $B$ is never executed.

---

## 5. Supported Language Subset & Known Limitations

### Supported Subset
- Data types: `int`, `float`.
- Statements: Variable declarations (`int x;`, `float y = 3.14;`), assignments (`x = expr;`), conditionals (`if`, `if-else`), loops (`while`), compound blocks (`{ ... }`).
- Expressions: Arithmetic (`+`, `-`, `*`, `/`, `%`), Relational (`<`, `<=`, `>`, `>=`, `==`, `!=`), Logical (`&&`, `||`, `!`).
- Comments: Single-line (`//`) and multi-line (`/* ... */`).

### Explicitly Excluded (Out of Scope for PS-06)
- Pointers, arrays, structs, and unions.
- Functions and function calls.
- `for`, `do-while`, and `switch` loops (all looping is represented via `while`).
- Code optimization passes (constant folding/dead-code elimination) are intentionally excluded to keep the emitted intermediate code in direct 1:1 correspondence with the SDT definitions.
