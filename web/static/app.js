// Interactive UI script for ThreeAddrGen Lab

document.addEventListener("DOMContentLoaded", () => {
  const editor = document.getElementById("source-editor");
  const btnCompile = document.getElementById("btn-compile");
  const sampleSelect = document.getElementById("sample-select");
  const errorBar = document.getElementById("error-bar");
  const lineInfo = document.getElementById("line-info");

  const outputTac = document.getElementById("output-tac");
  const outputAst = document.getElementById("output-ast");
  const outputSdt = document.getElementById("output-sdt");
  const outputPostfix = document.getElementById("output-postfix");
  const outputTokens = document.getElementById("output-tokens");

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

  // Track cursor position
  editor.addEventListener("keyup", updateCursorPos);
  editor.addEventListener("click", updateCursorPos);

  function updateCursorPos() {
    const textLines = editor.value.substr(0, editor.selectionStart).split("\n");
    const line = textLines.length;
    const col = textLines[textLines.length - 1].length + 1;
    lineInfo.textContent = `Line ${line}, Col ${col}`;
  }

  // Load samples
  fetch("/api/samples")
    .then((res) => res.json())
    .then((samples) => {
      sampleSelect.innerHTML = '<option value="">-- Choose Sample --</option>';
      for (const [name, content] of Object.entries(samples)) {
        const opt = document.createElement("option");
        opt.value = name;
        opt.textContent = name;
        sampleSelect.appendChild(opt);
      }
      sampleSelect.addEventListener("change", () => {
        const selected = sampleSelect.value;
        if (selected && samples[selected]) {
          editor.value = samples[selected];
          updateCursorPos();
        }
      });
    })
    .catch((err) => console.error("Failed to load samples:", err));

  // Trigger compilation
  btnCompile.addEventListener("click", async () => {
    const source = editor.value.trim();
    if (!source) {
      errorBar.textContent = "Error: Source code is empty.";
      errorBar.classList.remove("hidden");
      return;
    }

    try {
      const resp = await fetch("/api/compile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source }),
      });
      const data = await resp.json();

      if (data.success) {
        errorBar.classList.add("hidden");
        outputTac.textContent = data.tac.length > 0 ? data.tac.join("\n") : "// (No TAC instructions generated)";
        outputAst.textContent = JSON.stringify(data.ast, null, 2);
        outputSdt.textContent = JSON.stringify(data.sdt_trace, null, 2);
        outputPostfix.textContent = JSON.stringify(data.postfix, null, 2);
        outputTokens.textContent = JSON.stringify(data.tokens, null, 2);
      } else {
        const err = data.error;
        errorBar.textContent = `${err.type}: ${err.message} (Line ${err.line}, Col ${err.column})`;
        errorBar.classList.remove("hidden");
      }
    } catch (err) {
      errorBar.textContent = "Server communication error: " + err.message;
      errorBar.classList.remove("hidden");
    }
  });
});

