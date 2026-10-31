// Interactive ThreeAddrGen Laboratory Client

document.addEventListener("DOMContentLoaded", () => {
  const editor = document.getElementById("source-editor");
  const lineNumbers = document.getElementById("line-numbers");
  const lineInfo = document.getElementById("line-info");
  const btnCompile = document.getElementById("btn-compile");
  const btnClear = document.getElementById("btn-clear");
  const sampleSelect = document.getElementById("sample-select");
  const errorBar = document.getElementById("error-bar");
  const errorMessage = document.getElementById("error-message");
  const successBar = document.getElementById("success-bar");
  const successMessage = document.getElementById("success-message");

  // Output panels
  const outputTac = document.getElementById("output-tac");
  const outputAst = document.getElementById("output-ast");
  const outputPostfix = document.getElementById("output-postfix");
  const outputSdt = document.getElementById("output-sdt");
  const outputSymbols = document.getElementById("output-symbols");
  const outputBackpatch = document.getElementById("output-backpatch");
  const outputTokens = document.getElementById("output-tokens");

  // AST Controls
  const btnAstExpand = document.getElementById("btn-ast-expand");
  const btnAstCollapse = document.getElementById("btn-ast-collapse");

  // Tab switching
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      const targetPane = document.getElementById(btn.getAttribute("data-tab"));
      if (targetPane) targetPane.classList.add("active");
    });
  });

  // Line numbers & Cursor tracking
  function updateLineNumbers() {
    const lines = editor.value.split("\n");
    const count = lines.length;
    let nums = "";
    for (let i = 1; i <= count; i++) {
      nums += i + "\n";
    }
    lineNumbers.textContent = nums;
  }

  function updateCursorPos() {
    const textLines = editor.value.substr(0, editor.selectionStart).split("\n");
    const line = textLines.length;
    const col = textLines[textLines.length - 1].length + 1;
    lineInfo.textContent = `Line ${line}, Col ${col}`;
  }

  editor.addEventListener("input", () => {
    updateLineNumbers();
    updateCursorPos();
  });
  editor.addEventListener("keyup", updateCursorPos);
  editor.addEventListener("click", updateCursorPos);
  editor.addEventListener("scroll", () => {
    lineNumbers.scrollTop = editor.scrollTop;
  });

  // Clear Editor
  btnClear.addEventListener("click", () => {
    editor.value = "";
    updateLineNumbers();
    updateCursorPos();
    clearOutputs();
    hideStatus();
  });

  function hideStatus() {
    errorBar.classList.add("hidden");
    successBar.classList.add("hidden");
  }

  function clearOutputs() {
    outputTac.innerHTML = '<div class="empty-state">No TAC instructions generated yet. Click "Compile Program".</div>';
    outputAst.innerHTML = '<div class="empty-state">No AST available. Click "Compile Program".</div>';
    outputPostfix.innerHTML = '<div class="empty-state">No postfix expressions generated yet.</div>';
    outputSdt.innerHTML = '<div class="empty-state">No SDT attribute trace available yet.</div>';
    outputSymbols.innerHTML = '<div class="empty-state">No symbols registered yet.</div>';
    outputBackpatch.innerHTML = '<div class="empty-state">No backpatching operations performed yet.</div>';
    outputTokens.innerHTML = '<div class="empty-state">No tokens scanned yet.</div>';
  }

  // Load Presets from API
  let loadedSamples = {};
  fetch("/api/samples")
    .then((res) => res.json())
    .then((samples) => {
      loadedSamples = samples;
      sampleSelect.innerHTML = '<option value="">-- Select Preset --</option>';
      const sampleKeys = Object.keys(samples);
      sampleKeys.forEach((name) => {
        const opt = document.createElement("option");
        opt.value = name;
        opt.textContent = name;
        sampleSelect.appendChild(opt);
      });

      // Default load first sample
      if (sampleKeys.length > 0) {
        sampleSelect.value = sampleKeys[0];
        editor.value = samples[sampleKeys[0]];
        updateLineNumbers();
        updateCursorPos();
      }

      sampleSelect.addEventListener("change", () => {
        const sel = sampleSelect.value;
        if (sel && loadedSamples[sel]) {
          editor.value = loadedSamples[sel];
          updateLineNumbers();
          updateCursorPos();
          hideStatus();
        }
      });
    })
    .catch((err) => {
      console.error("Failed to fetch samples:", err);
      sampleSelect.innerHTML = '<option value="">Failed to load samples</option>';
    });

  // Compile Trigger
  btnCompile.addEventListener("click", compileCode);

  async function compileCode() {
    hideStatus();
    const source = editor.value.trim();
    if (!source) {
      errorMessage.textContent = "Cannot compile empty source code. Please enter code or load a preset.";
      errorBar.classList.remove("hidden");
      return;
    }

    btnCompile.disabled = true;
    document.getElementById("compile-spinner").classList.remove("hidden");
    document.getElementById("compile-btn-text").textContent = "Compiling...";

    try {
      const resp = await fetch("/api/compile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source }),
      });
      const data = await resp.json();

      if (data.success) {
        successMessage.textContent = `Compilation Successful! Generated ${data.tac_quadruples ? data.tac_quadruples.length : 0} TAC instructions.`;
        successBar.classList.remove("hidden");

        renderTAC(data.tac_quadruples || []);
        renderAST(data.ast);
        renderPostfix(data.postfix || []);
        renderSDT(data.sdt_trace || []);
        renderSymbols(data.symbol_table || {});
        renderBackpatch(data.backpatch_trace || []);
        renderTokens(data.tokens || []);
      } else {
        const err = data.error || { type: "Error", message: "Compilation failed", line: 0, column: 0 };
        errorMessage.textContent = `${err.type}: ${err.message} (Line ${err.line}, Col ${err.column})`;
        errorBar.classList.remove("hidden");
        clearOutputs();
      }
    } catch (err) {
      errorMessage.textContent = "Server communication error: " + err.message;
      errorBar.classList.remove("hidden");
    } finally {
      btnCompile.disabled = false;
      document.getElementById("compile-spinner").classList.add("hidden");
      document.getElementById("compile-btn-text").textContent = "Compile Program";
    }
  }

  // --- Renderers ---

  function renderTAC(quadruples) {
    if (!quadruples || quadruples.length === 0) {
      outputTac.innerHTML = '<div class="empty-state">No instructions emitted.</div>';
      return;
    }

    outputTac.innerHTML = "";
    quadruples.forEach((q) => {
      const row = document.createElement("div");
      let typeClass = "type-arith";

      if (q.op === "=") typeClass = "type-assign";
      else if (q.op.startsWith("if_")) typeClass = "type-cond";
      else if (q.op === "goto") typeClass = "type-uncond";
      else if (q.op === "halt") typeClass = "type-halt";

      row.className = `tac-row ${typeClass}`;
      row.innerHTML = `
        <span class="tac-idx">(${q.index})</span>
        <span class="tac-code">${escapeHtml(q.formatted || `${q.op} ${q.arg1 || ""} ${q.arg2 || ""} ${q.result || ""}`)}</span>
      `;
      outputTac.appendChild(row);
    });
  }

  function renderAST(astNode) {
    if (!astNode) {
      outputAst.innerHTML = '<div class="empty-state">No AST available.</div>';
      return;
    }
    outputAst.innerHTML = "";
    outputAst.appendChild(buildTreeNode(astNode));
  }

  function buildTreeNode(node) {
    const container = document.createElement("div");
    container.className = "tree-node";

    const header = document.createElement("div");
    header.className = "node-header";

    let label = "";
    let children = [];

    if (node.type === "Program" || node.type === "Block") {
      children = node.statements || [];
      label = `[${children.length} statements]`;
    } else if (node.type === "VarDecl") {
      label = `${node.type_name} ${node.name}`;
      if (node.initializer) children.push({ key: "init", ...node.initializer });
    } else if (node.type === "Assign") {
      label = `${node.target} =`;
      if (node.expr) children.push(node.expr);
    } else if (node.type === "BinaryOp") {
      label = `'${node.op}'`;
      if (node.left) children.push(node.left);
      if (node.right) children.push(node.right);
    } else if (node.type === "UnaryOp") {
      label = `'${node.op}'`;
      if (node.operand) children.push(node.operand);
    } else if (node.type === "IfStmt") {
      if (node.condition) children.push({ key: "cond", ...node.condition });
      if (node.then_branch) children.push({ key: "then", ...node.then_branch });
      if (node.else_branch) children.push({ key: "else", ...node.else_branch });
    } else if (node.type === "WhileStmt") {
      if (node.condition) children.push({ key: "cond", ...node.condition });
      if (node.body) children.push({ key: "body", ...node.body });
    } else if (node.type === "Identifier") {
      label = node.name;
    } else if (node.type === "NumberLiteral") {
      label = `${node.value} (${node.is_float ? "float" : "int"})`;
    }

    const hasChildren = children.length > 0;
    const toggleIcon = hasChildren ? "▼" : "•";

    header.innerHTML = `
      <span class="node-toggle">${toggleIcon}</span>
      <span class="node-type">${node.type}</span>
      ${label ? `<span class="node-label">${escapeHtml(label)}</span>` : ""}
      <span class="node-loc">(L${node.line || 0}:C${node.column || 0})</span>
    `;

    container.appendChild(header);

    if (hasChildren) {
      const childrenBox = document.createElement("div");
      childrenBox.className = "node-children";
      children.forEach((c) => {
        childrenBox.appendChild(buildTreeNode(c));
      });
      container.appendChild(childrenBox);

      header.addEventListener("click", () => {
        childrenBox.classList.toggle("collapsed");
        const toggleSpan = header.querySelector(".node-toggle");
        toggleSpan.textContent = childrenBox.classList.contains("collapsed") ? "▶" : "▼";
      });
    }

    return container;
  }

  btnAstExpand.addEventListener("click", () => {
    document.querySelectorAll(".node-children").forEach((c) => c.classList.remove("collapsed"));
    document.querySelectorAll(".node-toggle").forEach((t) => { if (t.textContent === "▶") t.textContent = "▼"; });
  });

  btnAstCollapse.addEventListener("click", () => {
    document.querySelectorAll(".node-children").forEach((c) => c.classList.add("collapsed"));
    document.querySelectorAll(".node-toggle").forEach((t) => { if (t.textContent === "▼") t.textContent = "▶"; });
  });

  function renderPostfix(expressions) {
    if (!expressions || expressions.length === 0) {
      outputPostfix.innerHTML = '<div class="empty-state">No postfix expressions found.</div>';
      return;
    }

    let html = `
      <table class="data-table">
        <thead>
          <tr>
            <th>Line</th>
            <th>Context</th>
            <th>Postfix Notation</th>
          </tr>
        </thead>
        <tbody>
    `;

    expressions.forEach((p) => {
      html += `
        <tr>
          <td>${p.line}</td>
          <td>${escapeHtml(p.context)}</td>
          <td><strong>${escapeHtml(p.postfix)}</strong></td>
        </tr>
      `;
    });

    html += `</tbody></table>`;
    outputPostfix.innerHTML = html;
  }

  function renderSDT(trace) {
    if (!trace || trace.length === 0) {
      outputSdt.innerHTML = '<div class="empty-state">No SDT trace available.</div>';
      return;
    }

    let html = `
      <table class="data-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Kind</th>
            <th>Node</th>
            <th>Attribute</th>
            <th>Computed Value</th>
            <th>Details</th>
          </tr>
        </thead>
        <tbody>
    `;

    trace.forEach((step, idx) => {
      const tagClass = step.kind === "synthesized" ? "tag-synth" : "tag-inh";
      html += `
        <tr>
          <td>${idx + 1}</td>
          <td><span class="${tagClass}">${step.kind}</span></td>
          <td>${escapeHtml(step.node)}</td>
          <td><strong>${escapeHtml(step.attribute)}</strong></td>
          <td><code>${escapeHtml(step.value)}</code></td>
          <td style="color: var(--text-dim);">${escapeHtml(step.details || "")}</td>
        </tr>
      `;
    });

    html += `</tbody></table>`;
    outputSdt.innerHTML = html;
  }

  function renderSymbols(symbols) {
    const keys = Object.keys(symbols);
    if (keys.length === 0) {
      outputSymbols.innerHTML = '<div class="empty-state">No symbols recorded in symbol table.</div>';
      return;
    }

    let html = `
      <table class="data-table">
        <thead>
          <tr>
            <th>Identifier</th>
            <th>Datatype</th>
            <th>Scope</th>
          </tr>
        </thead>
        <tbody>
    `;

    keys.forEach((id) => {
      html += `
        <tr>
          <td><strong>${escapeHtml(id)}</strong></td>
          <td><code>${escapeHtml(symbols[id])}</code></td>
          <td>Global</td>
        </tr>
      `;
    });

    html += `</tbody></table>`;
    outputSymbols.innerHTML = html;
  }

  function renderBackpatch(trace) {
    if (!trace || trace.length === 0) {
      outputBackpatch.innerHTML = '<div class="empty-state">No backpatching operations performed (program contains no jumps).</div>';
      return;
    }

    let html = `
      <table class="data-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Operation</th>
            <th>Instruction Indices</th>
            <th>Target</th>
            <th>Result List</th>
            <th>Explanation</th>
          </tr>
        </thead>
        <tbody>
    `;

    trace.forEach((ev, idx) => {
      html += `
        <tr>
          <td>${idx + 1}</td>
          <td><strong>${escapeHtml(ev.operation)}</strong></td>
          <td>${JSON.stringify(ev.indices || [])}</td>
          <td>${ev.target !== null ? `<strong>${ev.target}</strong>` : "-"}</td>
          <td>${JSON.stringify(ev.result_list || [])}</td>
          <td style="color: var(--text-muted);">${escapeHtml(ev.explanation || "")}</td>
        </tr>
      `;
    });

    html += `</tbody></table>`;
    outputBackpatch.innerHTML = html;
  }

  function renderTokens(tokens) {
    if (!tokens || tokens.length === 0) {
      outputTokens.innerHTML = '<div class="empty-state">No tokens scanned.</div>';
      return;
    }

    let html = `
      <table class="data-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Token Type</th>
            <th>Lexeme</th>
            <th>Line</th>
            <th>Column</th>
          </tr>
        </thead>
        <tbody>
    `;

    tokens.forEach((t, idx) => {
      html += `
        <tr>
          <td>${idx + 1}</td>
          <td><strong>${escapeHtml(t.type)}</strong></td>
          <td><code>${escapeHtml(t.value || "EOF")}</code></td>
          <td>${t.line}</td>
          <td>${t.column}</td>
        </tr>
      `;
    });

    html += `</tbody></table>`;
    outputTokens.innerHTML = html;
  }

  function escapeHtml(str) {
    if (typeof str !== "string") str = String(str);
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
