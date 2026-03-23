// =============================================================================
// app.js — BugVortex AI Dashboard Frontend Logic
//
// This file handles:
//   1. Calling the FastAPI /predict_bug endpoint
//   2. Displaying results in the result panel
//   3. Live latency simulation
//   4. UI interactions (language selector, modal, copy)
// =============================================================================

// ---- CONFIGURATION ----
// Change this to match your FastAPI server address
const API_BASE_URL = "http://localhost:8000";

// Current selected language for the code editor
let currentLang = "auto";

// ---- LIVE LATENCY COUNTER ----
// Updates the neural latency display every 3 seconds with a simulated value
function startLatencyPulse() {
  const display = document.getElementById("latency-display");
  setInterval(() => {
    // Simulate latency between 10ms and 22ms
    const ms = Math.floor(Math.random() * 12) + 10;
    display.textContent = `${ms}ms`;
  }, 3000);
}

// ---- LANGUAGE SELECTOR ----
function setLang(btn, lang) {
  // Remove .active from all lang buttons
  document.querySelectorAll(".lang-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  currentLang = lang;
}

// ---- COPY CODE ----
function copyCode() {
  const code = document.getElementById("code-input").value;
  navigator.clipboard.writeText(code).then(() => {
    const btn = document.querySelector(".copy-btn");
    btn.style.color = "var(--accent-cyan)";
    setTimeout(() => { btn.style.color = ""; }, 1200);
  });
}

// ---- MAIN: ANALYZE BUG ----
// Calls POST /predict_bug on the FastAPI server and shows the result
async function analyzeBug() {
  const code = document.getElementById("code-input").value.trim();

  if (!code) {
    showError("Please paste a C or Java code snippet first.");
    return;
  }

  // Show spinner, disable button
  const analyzeBtn = document.querySelector(".analyze-btn");
  const spinner    = document.getElementById("spinner");
  const btnText    = document.querySelector(".btn-text");
  analyzeBtn.disabled = true;
  spinner.style.display = "inline-block";
  btnText.textContent = "SCANNING";

  // Hide previous result
  const resultPanel = document.getElementById("result-panel");
  resultPanel.style.display = "none";

  try {
    // ----------------------------------------------------------------
    // POST request to FastAPI endpoint
    // The body must match the CodeSnippetRequest Pydantic schema:
    //   { "code": "...", "language": "auto" }
    // ----------------------------------------------------------------
    const response = await fetch(`${API_BASE_URL}/predict_bug`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        // If you set API_KEY in .env, uncomment this:
        // "X-API-Key": "your_secret_api_key_here"
      },
      body: JSON.stringify({
        code: code,
        language: currentLang
      })
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || `Server error: ${response.status}`);
    }

    // Parse the BugPredictionResponse JSON
    const data = await response.json();

    // Display the result
    showResult(data);

    // Update the vulnerability counter
    incrementVulnCount(data.bug_detected);

  } catch (error) {
    // ----------------------------------------------------------------
    // If the server is offline, fall back to a local heuristic demo
    // This is useful for presentations when the backend isn't running
    // ----------------------------------------------------------------
    console.warn("[BugVortex] API unavailable, using local heuristic:", error.message);
    const localResult = localHeuristicPredict(code);
    showResult(localResult);
  } finally {
    // Re-enable button
    analyzeBtn.disabled = false;
    spinner.style.display = "none";
    btnText.textContent = "ANALYZE";
  }
}

// ---- SHOW RESULT PANEL ----
function showResult(data) {
  const panel           = document.getElementById("result-panel");
  const resultIcon      = document.getElementById("result-icon");
  const resultTitle     = document.getElementById("result-title");
  const bugDetected     = document.getElementById("bug-detected");
  const confidenceScore = document.getElementById("confidence-score");
  const likelyIssue     = document.getElementById("likely-issue");
  const tokensAnalyzed  = document.getElementById("tokens-analyzed");

  if (data.bug_detected) {
    panel.className = "result-panel buggy";
    resultIcon.textContent = "⚠";
    resultIcon.style.color = "var(--accent-red)";
    resultTitle.textContent = "BUG DETECTED";
    resultTitle.style.color = "var(--accent-red)";
    bugDetected.textContent = "YES";
    bugDetected.style.color = "var(--accent-red)";
  } else {
    panel.className = "result-panel clean";
    resultIcon.textContent = "✓";
    resultIcon.style.color = "var(--accent-green)";
    resultTitle.textContent = "CODE LOOKS CLEAN";
    resultTitle.style.color = "var(--accent-green)";
    bugDetected.textContent = "NO";
    bugDetected.style.color = "var(--accent-green)";
  }

  const pct = Math.round(data.confidence_score * 100);
  confidenceScore.textContent = `${pct}%`;
  likelyIssue.textContent     = data.likely_issue || "—";
  tokensAnalyzed.textContent  = data.tokens_analyzed || "—";

  panel.style.display = "block";

  // Smooth scroll to result
  panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// ---- SHOW ERROR ----
function showError(message) {
  const panel = document.getElementById("result-panel");
  panel.className = "result-panel buggy";
  panel.style.display = "block";

  document.getElementById("result-icon").textContent = "✕";
  document.getElementById("result-icon").style.color = "var(--accent-red)";
  document.getElementById("result-title").textContent = "ERROR";
  document.getElementById("result-title").style.color = "var(--accent-red)";
  document.getElementById("bug-detected").textContent = "—";
  document.getElementById("confidence-score").textContent = "—";
  document.getElementById("likely-issue").textContent = message;
  document.getElementById("tokens-analyzed").textContent = "—";
}

// ---- LOCAL HEURISTIC (OFFLINE FALLBACK) ----
// Used when the FastAPI server is not running — for demo/presentation purposes
function localHeuristicPredict(code) {
  const bugPatterns = [
    { pattern: /NULL\s*;[\s\S]*\*ptr/,        issue: "Null Pointer Dereference (C)" },
    { pattern: /null[\s\S]*\.length\(\)/i,    issue: "NullPointerException (Java)" },
    { pattern: /malloc[\s\S]*(?!free)/,        issue: "Memory Leak — malloc without free" },
    { pattern: /\[\s*\d+\s*\]/,               issue: "Potential Array Out-of-Bounds Access" },
    { pattern: /\/\s*0(?!\.)(?!\d)/,           issue: "Division by Zero" },
    { pattern: /= null;[\s\S{0,50}]\*/i,       issue: "Null Pointer Dereference" },
    { pattern: /INT_MAX|2147483647/,           issue: "Integer Overflow Risk" },
    { pattern: /new int\[\d+\][\s\S]*\[\d+\]/,issue: "Array Index Out of Bounds (Java)" },
  ];

  for (const { pattern, issue } of bugPatterns) {
    if (pattern.test(code)) {
      return {
        bug_detected:     true,
        confidence_score: 0.78 + Math.random() * 0.15,
        likely_issue:     issue,
        clean_confidence: 0.15 + Math.random() * 0.1,
        model_version:    "LOCAL-HEURISTIC",
        tokens_analyzed:  Math.floor(code.split(/\s+/).length * 1.3)
      };
    }
  }

  return {
    bug_detected:     false,
    confidence_score: 0.82 + Math.random() * 0.12,
    likely_issue:     "No significant issues detected",
    clean_confidence: 0.82 + Math.random() * 0.12,
    model_version:    "LOCAL-HEURISTIC",
    tokens_analyzed:  Math.floor(code.split(/\s+/).length * 1.3)
  };
}

// ---- INCREMENT VULN COUNTER ----
function incrementVulnCount(wasBuggy) {
  if (!wasBuggy) return;
  const el = document.getElementById("vuln-count");
  const current = parseInt(el.textContent.replace(/,/g, ""), 10);
  const next = current + 1;
  el.textContent = next.toLocaleString();

  // Flash animation
  el.style.color = "var(--accent-cyan)";
  setTimeout(() => { el.style.color = ""; }, 800);
}

// ---- DEPLOY MODAL ----
function openDeployModal() {
  document.getElementById("deploy-modal").classList.add("open");
}

function closeDeployModal(event) {
  // Close if clicking overlay background or close button
  if (!event || event.target === document.getElementById("deploy-modal") || !event.target) {
    document.getElementById("deploy-modal").classList.remove("open");
  }
}

function deployModel() {
  const modelPath = document.getElementById("model-path-input").value;
  const region    = document.getElementById("region-select").value;
  const endpoint  = document.getElementById("api-endpoint-input").value;

  // In production you'd POST to a deploy endpoint
  console.log("[BugVortex] Deploy request:", { modelPath, region, endpoint });

  closeDeployModal();

  // Show brief toast
  const toast = document.createElement("div");
  toast.style.cssText = `
    position: fixed; bottom: 24px; right: 24px; z-index: 999;
    background: var(--bg-card); border: 1px solid var(--border-active);
    color: var(--accent-cyan); font-family: var(--font-mono); font-size: 11px;
    letter-spacing: 1.5px; padding: 12px 20px; border-radius: 8px;
    animation: slideIn 0.2s ease; box-shadow: 0 4px 24px rgba(0,0,0,0.4);
  `;
  toast.textContent = `✓ DEPLOYING TO ${region.toUpperCase()}...`;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// ---- TOP NAV & SIDEBAR ACTIVE STATE ----
document.querySelectorAll(".topnav-link").forEach(link => {
  link.addEventListener("click", e => {
    e.preventDefault();
    document.querySelectorAll(".topnav-link").forEach(l => l.classList.remove("active"));
    link.classList.add("active");
  });
});

document.querySelectorAll(".nav-item").forEach(item => {
  item.addEventListener("click", e => {
    e.preventDefault();
    document.querySelectorAll(".nav-item").forEach(l => l.classList.remove("active"));
    item.classList.add("active");
  });
});

// ---- KEYBOARD SHORTCUT ----
// Ctrl+Enter or Cmd+Enter to analyze
document.getElementById("code-input").addEventListener("keydown", e => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
    e.preventDefault();
    analyzeBug();
  }
});

// ---- INIT ----
document.addEventListener("DOMContentLoaded", () => {
  startLatencyPulse();

  // Pre-fill the code editor with the demo snippet from the screenshot
  const editor = document.getElementById("code-input");
  editor.value =
`import vortex_core as vx

def initialize_neural_bridge(token):
    engine = vx.Engine(mode="reactive")
    patch = engine.scan_repository("root://deploy")
    return patch.apply(verify=True)

_`;
});
