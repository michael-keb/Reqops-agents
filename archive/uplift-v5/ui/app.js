const $ = (id) => document.getElementById(id);

let termAutoScroll = true;
let termLineCount = 0;

function appendTermLine(entry) {
  const el = $("terminal");
  if (entry?.line == null) return;
  if (termLineCount === 0) el.innerHTML = "";
  const line = document.createElement("div");
  line.className = `term-line ${entry.kind || "sys"}`;
  line.textContent = entry.line;
  el.appendChild(line);
  termLineCount += 1;
  if (termAutoScroll) el.scrollTop = el.scrollHeight;
}

function setTermStatus(text, live = false) {
  const s = $("termStatus");
  s.textContent = text;
  s.classList.toggle("live", live);
}

async function loadTerminalHistory() {
  try {
    const data = await api("/api/terminal/history");
    (data.lines || []).forEach(appendTermLine);
    if (termLineCount === 0) {
      $("terminal").innerHTML = '<div class="term-empty">Waiting for agent output…</div>';
    }
  } catch (_) {
    $("terminal").innerHTML = '<div class="term-empty">Terminal unavailable</div>';
  }
}

function connectTerminal() {
  const es = new EventSource("/api/terminal/stream");
  es.onopen = () => setTermStatus("live", true);
  es.onmessage = (e) => {
    try { appendTermLine(JSON.parse(e.data)); } catch (_) { /* ignore */ }
  };
  es.onerror = () => setTermStatus("reconnecting…", false);
}

$("termClear").addEventListener("click", () => {
  $("terminal").innerHTML = '<div class="term-empty">Cleared — new output will appear below</div>';
  termLineCount = 0;
});

$("terminal").addEventListener("scroll", () => {
  const el = $("terminal");
  termAutoScroll = el.scrollHeight - el.scrollTop - el.clientHeight < 48;
});

function setError(msg) {
  const el = $("error");
  if (!msg) { el.hidden = true; el.textContent = ""; return; }
  el.hidden = false;
  el.textContent = msg;
}

function renderMeta(data) {
  const m = $("meta");
  if (!data?.session_id) {
    const bits = [];
    if (data?.mock) bits.push("mock");
    if (data?.agent === false) bits.push("no agent CLI");
    m.textContent = bits.length ? bits.join(" · ") : "no session";
    return;
  }
  const parts = [
    `<span class="pill">${data.session_id}</span>`,
    `<span class="pill">turn ${String(data.turn || 0).padStart(2, "0")}</span>`,
  ];
  if (data.persistent) parts.push(`<span class="pill ok">persistent</span>`);
  else if (data.mode === "cli") parts.push(`<span class="pill ok">cli live</span>`);
  if (data.elapsed_s != null) parts.push(`<span class="pill">${data.elapsed_s}s</span>`);
  m.innerHTML = parts.join("");
}

function escapeHtml(s) {
  return String(s || "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function simpleMarkdown(text) {
  if (!text) return "";
  let html = escapeHtml(text);
  html = html.replace(/^## (.+)$/gm, "<h3>$1</h3>");
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/^- ([A-D]\) .+)$/gm, "<div class='muted'>$1</div>");
  return html;
}

function renderResponse(data) {
  const text = data.response || "(no response — check sessions/ artifacts)";
  $("response").innerHTML = simpleMarkdown(text);

  const opts = $("options");
  opts.innerHTML = "";
  const tj = data.turn_json;
  const options = tj?.options || [];
  options.forEach((opt, i) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "opt";
    btn.textContent = opt;
    btn.addEventListener("click", () => {
      opts.querySelectorAll(".opt").forEach((b) => b.classList.remove("selected"));
      btn.classList.add("selected");
      $("answer").value = opt.replace(/^[A-D]\)\s*/, "");
    });
    opts.appendChild(btn);
  });
}

function showSession(data) {
  $("startPanel").hidden = true;
  $("sessionPanel").hidden = false;
  renderMeta(data);
  if (data.last_user_input) {
    $("lastPanel").hidden = false;
    $("lastInput").textContent = data.last_user_input;
  } else {
    $("lastPanel").hidden = true;
  }
  renderResponse(data);
  $("answer").value = "";
  $("answer").focus();
}

async function api(path, opts) {
  const res = await fetch(path, opts);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || `HTTP ${res.status}`);
  return body;
}

async function loadHealth() {
  try {
    const h = await api("/api/health");
    if (!h.agent) {
      setError("Cursor agent CLI not on PATH. Run: curl https://cursor.com/install -fsS | bash && agent login");
    }
  } catch (e) {
    setError(e.message);
  }
}

async function loadState() {
  try {
    const data = await api("/api/state");
    if (data.session_id && data.turn > 0) showSession(data);
    else renderMeta(data);
  } catch (e) {
    setError(e.message);
  }
}

async function runAction(fn) {
  setError("");
  const btn = $("submitBtn").disabled ? $("startBtn") : $("submitBtn");
  const orig = btn.innerHTML;
  btn.disabled = true;
  $("submitBtn").disabled = true;
  $("startBtn").disabled = true;
  btn.innerHTML = `<span class="spinner"></span>agent thinking…`;
  try {
    const data = await fn();
    showSession(data);
    if ($("answer").dataset.lastSent) {
      $("lastPanel").hidden = false;
      $("lastInput").textContent = $("answer").dataset.lastSent;
    }
  } catch (e) {
    setError(e.message);
  } finally {
    btn.disabled = false;
    $("submitBtn").disabled = false;
    $("startBtn").disabled = false;
    btn.innerHTML = orig;
  }
}

$("startBtn").addEventListener("click", () => {
  const pitch = $("pitchInput").value.trim();
  if (!pitch) { setError("Enter a pitch."); return; }
  runAction(() => api("/api/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pitch }),
  }));
});

$("submitBtn").addEventListener("click", () => {
  const text = $("answer").value.trim();
  if (!text) { setError("Enter an answer or pick an option."); return; }
  $("answer").dataset.lastSent = text;
  runAction(() => api("/api/turn", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  }));
});

$("newBtn").addEventListener("click", () => {
  if (!confirm("Start a new session? Current session stays on disk.")) return;
  $("sessionPanel").hidden = true;
  $("startPanel").hidden = false;
  $("pitchInput").focus();
});

$("pitchInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") $("startBtn").click();
});

$("answer").addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === "Enter") $("submitBtn").click();
});

loadHealth();
loadState();
loadTerminalHistory();
connectTerminal();
