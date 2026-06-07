(() => {
  const wsUrl = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`;
  const btnInterrupt = document.getElementById("btn-interrupt");
  const btnNewSession = document.getElementById("btn-new-session");
  const btnTermNew = document.getElementById("btn-term-new");
  const btnTermClear = document.getElementById("btn-term-clear");
  const pillWs = document.getElementById("pill-ws");
  const pillSession = document.getElementById("pill-session");
  const pillTurn = document.getElementById("pill-turn");
  const pillErrors = document.getElementById("pill-errors");
  const diagEl = document.getElementById("ui-diagnostics");
  const modeTag = document.getElementById("mode-tag");
  const termEl = document.getElementById("terminal");
  const mcqList = document.getElementById("mcq-list");

  const upliftDiag = {
    errors: [],
    turnLatencies: [],
    components: {
      ws: "init",
      trace: "init",
      terminal: "init",
      session: "none",
      turn: "idle",
      api: "unknown",
    },
  };

  function flushDiag() {
    if (diagEl) diagEl.textContent = JSON.stringify(upliftDiag);
    if (pillErrors) {
      const n = upliftDiag.errors.length;
      pillErrors.hidden = n === 0;
      pillErrors.textContent = n === 1 ? "1 error" : `${n} errors`;
      pillErrors.className = "pill" + (n ? " err" : "");
    }
  }

  function setComponent(name, state) {
    upliftDiag.components[name] = state;
    flushDiag();
  }

  function recordError(source, message, detail) {
    upliftDiag.errors.push({
      ts: new Date().toISOString(),
      source,
      message: String(message || "unknown"),
      detail: detail ?? null,
    });
    flushDiag();
  }

  function recordTurnLatency(turn, elapsed_s, source) {
    const t = Number(turn);
    const e = Number(elapsed_s);
    if (!t || Number.isNaN(e)) return;
    const existing = upliftDiag.turnLatencies.find((x) => x.turn === t && x.source === source);
    if (existing) existing.elapsed_s = e;
    else upliftDiag.turnLatencies.push({ turn: t, elapsed_s: e, source });
    flushDiag();
  }

  window.__upliftDiag = upliftDiag;
  flushDiag();

  let ws = null;
  let wsConnectToken = 0;
  let reconnectDelayMs = 1500;
  let busy = false;
  let sessionStarted = false;
  let traceSource = null;
  let inputBuffer = "";
  let promptVisible = false;
  let sessionEpoch = 0;
  let suppressSessionReset = false;
  let agentMode = "pty";
  let term = null;
  let fitAddon = null;
  let lastResultText = "";
  let lastResultFingerprint = "";
  let lastRenderedTurn = 0;
  let thinkingShown = false;
  let respondingShown = false;

  function resetActionStream() {
    thinkingShown = false;
    respondingShown = false;
  }

  function writeAction(msg, color = "90") {
    if (promptVisible) {
      promptVisible = false;
      term.write("\r\n");
    }
    term.writeln(`\x1b[${color}m${msg}\x1b[0m`);
  }

  const TERM_OPTS = {
    cursorBlink: true,
    fontSize: 13,
    fontFamily: "Menlo, Monaco, 'Courier New', monospace",
    theme: { background: "#000000", cursor: "#6ea8fe" },
    scrollback: 10000,
  };

  function termSys(msg) {
    if (/^(Error:|error:|agent exited|turn .* failed|timed out)/i.test(msg)) {
      recordError("terminal", msg);
    }
    if (promptVisible) {
      promptVisible = false;
      term.write("\r\n");
    }
    term.writeln(`\x1b[90m${msg}\x1b[0m`);
  }

  function termBanner() {
    term.writeln("\x1b[1;36mUplift v6\x1b[0m — local PTY agent (session stays open)");
    term.writeln(
      "\x1b[90mType a pitch to start · live agent TUI streams here · follow-up turns reuse the same process · /new = fresh session\x1b[0m"
    );
  }

  function showPrompt() {
    if (busy || promptVisible) return;
    promptVisible = true;
    term.write("\r\n\x1b[36m→ \x1b[0m");
  }

  function hidePrompt() {
    if (!promptVisible) return;
    promptVisible = false;
    term.write("\r\n");
  }

  function mountTerminal() {
    if (term) {
      term.dispose();
      termEl.innerHTML = "";
    }
    inputBuffer = "";
    promptVisible = false;
    lastResultText = "";
    lastResultFingerprint = "";
    lastRenderedTurn = 0;
    const FitAddonCtor = window.FitAddon?.FitAddon || window.FitAddon;
    term = new Terminal(TERM_OPTS);
    fitAddon = new FitAddonCtor();
    term.loadAddon(fitAddon);
    term.open(termEl);
    fitAddon.fit();
    term.onData(handleTermData);
    termBanner();
    setComponent("terminal", "ready");
    if (!busy) showPrompt();
    term.focus();
  }

  function clearTerminalScreen() {
    inputBuffer = "";
    promptVisible = false;
    lastResultText = "";
    lastResultFingerprint = "";
    lastRenderedTurn = 0;
    term.clear();
    termBanner();
    if (!busy) showPrompt();
  }

  function resetUiState() {
    sessionStarted = false;
    sessionEpoch += 1;
    setBusy(false);
    pillSession.textContent = "no session";
    pillTurn.textContent = "turn —";
    setComponent("session", "none");
    mountTerminal();
    termSys("New session — fresh terminal. Type a product pitch.");
    showPrompt();
  }

  async function newSession({ confirmPrompt = true } = {}) {
    if (confirmPrompt && busy) {
      if (!window.confirm("Stop the current turn and open a fresh terminal?")) return;
    } else if (confirmPrompt && sessionStarted) {
      if (!window.confirm("Discard this session and start fresh?")) return;
    }
    setBusy(true);
    hidePrompt();
    try {
      sendWs({ type: "interrupt" });
      suppressSessionReset = true;
      const r = await fetch("/api/new-session", { method: "POST" });
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.error || r.statusText);
      }
      resetUiState();
      suppressSessionReset = false;
      connectTrace();
    } catch (err) {
      suppressSessionReset = false;
      setBusy(false);
      recordError("newSession", err.message || String(err));
      termSys(`Error: ${err.message || err}`);
      showPrompt();
    }
  }

  function setBusy(on) {
    busy = on;
    btnInterrupt.disabled = !on;
    setComponent("turn", on ? "running" : "idle");
    pillWs.className = "pill" + (on ? " busy" : ws && ws.readyState === WebSocket.OPEN ? " ok" : "");
    pillWs.textContent = on ? "agent running…" : ws && ws.readyState === WebSocket.OPEN ? "connected" : "disconnected";
    if (on) hidePrompt();
    else {
      showPrompt();
      term.focus();
    }
  }

  function discoveryFingerprint(text) {
    return stripJsonBlocks(text).replace(/\s+/g, " ").trim().slice(0, 240);
  }

  function stripJsonBlocks(text) {
    return text
      .replace(/```(?:json)?\s*\n[\s\S]*?\n```/gi, "")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
  }

  function renderDiscoveryText(text) {
    const cleaned = stripJsonBlocks(text);
    if (!cleaned) return;
    term.writeln("");
    for (const line of cleaned.split("\n")) {
      if (line.startsWith("## ")) term.writeln(`\x1b[1;37m${line}\x1b[0m`);
      else if (line.match(/^-\s*[A-D]\)/)) term.writeln(`\x1b[32m${line}\x1b[0m`);
      else term.writeln(line);
    }
    term.writeln("");
  }

  function writeTraceEntry(entry, { replay = false } = {}) {
    if (!term) return;
    const kind = entry.kind || "sys";
    const msg = entry.msg || "";
    const level = entry.level || "info";

    if (promptVisible && kind !== "assistant") {
      promptVisible = false;
      term.write("\r\n");
    }

    switch (kind) {
      case "tool":
        writeAction(msg, "38;5;214");
        break;
      case "thinking":
        if (busy && (entry.data?.subtype === "completed" || msg === "thinking done") && !thinkingShown) {
          thinkingShown = true;
          writeAction("… thinking");
        }
        break;
      case "assistant":
        if (busy && entry.data?.partial && !respondingShown) {
          respondingShown = true;
          writeAction("… drafting response");
        }
        break;
      case "result": {
        const text = stripJsonBlocks((entry.data?.text || msg || "").trim());
        if (!text) break;
        const turn = entry.data?.turn || 0;
        const fp = discoveryFingerprint(text);
        if (fp && fp === lastResultFingerprint && turn === lastRenderedTurn) break;
        if (text === lastResultText) break;
        lastResultText = text;
        lastResultFingerprint = fp;
        lastRenderedTurn = turn;
        renderDiscoveryText(text);
        break;
      }
      case "error":
      case "exit":
        if (kind === "exit") {
          setBusy(false);
          recordError("trace", msg, entry.data);
          term.writeln(`\x1b[31m${msg}${entry.data?.detail ? " — " + entry.data.detail : ""}\x1b[0m`);
          break;
        }
        recordError("trace", msg, entry.data);
        term.writeln(`\x1b[31m${msg}${entry.data?.traceback ? "\n" + entry.data.traceback : ""}\x1b[0m`);
        break;
      case "validation":
        term.writeln(
          `\x1b[38;5;141m[validation] ${msg}${entry.data?.path ? " · " + entry.data.path : ""}\x1b[0m`
        );
        break;
      case "lifecycle":
      case "spawn":
      case "agent":
        if (replay || busy) {
          if (kind === "spawn" || msg.includes("agent running") || msg.includes("init · model")) {
            writeAction(`[${kind}] ${msg}`);
          } else if (busy && entry.data?.parse_error) {
            const line = msg.trim();
            if (
              line &&
              !line.startsWith("##") &&
              !line.startsWith("- ") &&
              !/^\d+\./.test(line) &&
              line.length < 200 &&
              !line.startsWith("---")
            ) {
              writeAction(`… ${line.length > 100 ? line.slice(0, 100) + "…" : line}`);
            }
          }
        }
        break;
      case "turn":
        if (entry.data?.action === "start") {
          setBusy(true);
          resetActionStream();
        } else if (entry.data?.action === "complete") {
          recordTurnLatency(entry.data.turn, entry.data.elapsed_s, "trace");
          term.writeln(
            `\x1b[90m— turn ${entry.data.turn} done (${entry.data.elapsed_s}s) —\x1b[0m`
          );
          setBusy(false);
          refreshState();
        }
        break;
      case "stdin":
      case "stdout":
      case "event":
      case "http":
      case "ws":
      case "sys":
        break;
      default:
        if (level === "warn" || level === "error") {
          if (level === "error") recordError(`trace:${kind}`, msg, entry.data);
          term.writeln(`\x1b[90m[${kind}] ${msg}\x1b[0m`);
        }
    }
  }

  function connectTrace() {
    if (agentMode === "pty") {
      if (traceSource) traceSource.close();
      traceSource = null;
      setComponent("trace", "pty-ws");
      return;
    }
    if (traceSource) traceSource.close();
    setComponent("trace", "connecting");
    traceSource = new EventSource("/api/trace/stream");
    traceSource.onopen = () => setComponent("trace", "connected");
    traceSource.onmessage = (ev) => {
      try {
        writeTraceEntry(JSON.parse(ev.data));
      } catch (_) {}
    };
    traceSource.onerror = () => {
      setComponent("trace", "reconnecting");
      traceSource.close();
      setTimeout(connectTrace, 4000);
    };
  }

  function parseQuestionsFallback(text) {
    if (!text || !/##\s*Questions/i.test(text)) return [];
    const body = text.split(/##\s*Questions/i)[1] || "";
    const blocks = body.split(/(?=^###\s+\d+\.|^\d+\.\s+\*\*)/m).filter((b) => b.trim());
    const out = [];
    for (const block of blocks) {
      const h3 = block.match(/^###\s+(\d+)\.\s*(.+?)\s*$/m);
      const num = block.match(/^(\d+)\.\s+\*\*(.+?)\*\*/m);
      const hdr = h3 || num;
      if (!hdr) continue;
      const rank = parseInt(hdr[1], 10);
      const title = (hdr[2] || "").replace(/\*\*/g, "").trim();
      const stem = block
        .replace(/^###\s+\d+\..*$/m, "")
        .replace(/^\d+\.\s+\*\*.+?\*\*/m, "")
        .replace(/^-\s*[A-D]\).+$/gm, "")
        .trim();
      out.push({ rank, title, stem, options: [] });
    }
    return out.sort((a, b) => a.rank - b.rank);
  }

  function renderMcq(state) {
    if (!mcqList) return;
    let questions = state?.questions || [];
    const fallbackOnly = !questions.length;
    if (fallbackOnly) questions = parseQuestionsFallback(state?.response || "");
    mcqList.innerHTML = "";
    if (!state?.session_id) {
      mcqList.innerHTML =
        '<p class="mcq-empty">Start a session — MCQ options appear here after each agent turn.</p>';
      return;
    }
    if (!questions.length) {
      mcqList.innerHTML = '<p class="mcq-empty">No questions yet for this turn.</p>';
      return;
    }
    if (fallbackOnly) {
      const warn = document.createElement("p");
      warn.className = "mcq-warn";
      warn.textContent =
        "No A–D options in this turn (agent used open-ended format). Use /new and start again — or type free-text answers in the terminal.";
      mcqList.appendChild(warn);
    }
    for (const q of questions) {
      const wrap = document.createElement("div");
      wrap.className = "mcq-q";
      const h = document.createElement("h3");
      h.textContent = `${q.rank || "?"}. ${q.title || "Question"}`;
      wrap.appendChild(h);
      if (q.stem) {
        const stem = document.createElement("p");
        stem.className = "stem";
        stem.textContent = q.stem;
        wrap.appendChild(stem);
      }
      const opts = q.options || [];
      if (!opts.length && fallbackOnly) {
        const note = document.createElement("p");
        note.className = "stem";
        note.textContent = "(no A–D options — answer in terminal, e.g. Q1: …)";
        wrap.appendChild(note);
      }
      for (const opt of opts) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "mcq-opt";
        btn.textContent = opt;
        btn.addEventListener("click", () => {
          mcqList.querySelectorAll(".mcq-opt").forEach((b) => b.classList.remove("selected"));
          btn.classList.add("selected");
          const pick = opt.trim();
          inputBuffer = inputBuffer ? `${inputBuffer}  ${pick}` : pick;
          if (!promptVisible) showPrompt();
          term.write(`\r\x1b[32myou\x1b[0m › ${inputBuffer}`);
        });
        wrap.appendChild(btn);
      }
      mcqList.appendChild(wrap);
    }
  }

  async function refreshState() {
    try {
      const r = await fetch("/api/state");
      const s = await r.json();
      pillSession.textContent = s.session_id || "no session";
      pillTurn.textContent = s.turn ? `turn ${s.turn}` : "turn —";
      setComponent("session", s.session_id ? "active" : "none");
      setComponent("api", "ok");
      if (s.session_id) sessionStarted = true;
      renderMcq(s);
      return s;
    } catch (err) {
      setComponent("api", "error");
      recordError("refreshState", err.message || String(err));
      return null;
    }
  }

  async function refreshHealth() {
    try {
      const r = await fetch("/api/health");
      const h = await r.json();
      if (h.mode) {
        agentMode = h.mode;
        if (modeTag) modeTag.textContent = h.mode;
        connectTrace();
      }
      if (h.session_id) sessionStarted = true;
      setComponent("api", "ok");
    } catch (err) {
      setComponent("api", "error");
      recordError("refreshHealth", err.message || String(err));
    }
  }

  async function submitLine(text) {
    const line = text.trim();
    if (!line || busy) return;

    if (/^\/new(session)?$/i.test(line)) {
      await newSession({ confirmPrompt: true });
      return;
    }

    if (promptVisible) {
      term.write("\r\n");
      promptVisible = false;
    }

    term.writeln(`\x1b[32myou\x1b[0m › ${line}`);

    try {
      if (!sessionStarted) {
        setBusy(true);
        await startSession(line);
      } else {
        if (!sendWs({ type: "input", text: line })) {
          recordError("ws", "WebSocket disconnected on send");
          termSys("Error: WebSocket disconnected — wait for reconnect, then try again");
          showPrompt();
          return;
        }
        setBusy(true);
      }
    } catch (err) {
      setBusy(false);
      recordError("submitLine", err.message || String(err));
      termSys(`Error: ${err.message || err}`);
    }
  }

  function handleTermData(data) {
    if (data === "\x03") {
      sendWs({ type: "interrupt" });
      inputBuffer = "";
      term.write("^C");
      termSys("interrupt sent");
      return;
    }
    if (busy) return;
    if (!promptVisible) showPrompt();

    for (let i = 0; i < data.length; i++) {
      const ch = data[i];
      if (ch === "\r" || ch === "\n") {
        const line = inputBuffer;
        inputBuffer = "";
        promptVisible = false;
        if (line.trim()) submitLine(line);
        else showPrompt();
        return;
      }
      if (ch === "\x7f" || ch === "\b") {
        if (inputBuffer.length > 0) {
          inputBuffer = inputBuffer.slice(0, -1);
          term.write("\b \b");
        }
        continue;
      }
      if (ch < " " && ch !== "\t") continue;
      inputBuffer += ch;
      term.write(ch);
    }
  }

  function connect() {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      return;
    }
    if (ws) {
      try {
        ws.onclose = null;
        ws.onerror = null;
        ws.onmessage = null;
        ws.onopen = null;
        ws.close();
      } catch (_) {}
    }
    const token = ++wsConnectToken;
    ws = new WebSocket(wsUrl);
    ws.binaryType = "arraybuffer";
    const epochAtConnect = sessionEpoch;

    ws.onopen = () => {
      if (token !== wsConnectToken) return;
      reconnectDelayMs = 1500;
      pillWs.className = "pill ok";
      pillWs.textContent = "connected";
      setComponent("ws", "connected");
    };

    ws.onclose = () => {
      if (token !== wsConnectToken) return;
      pillWs.className = "pill";
      pillWs.textContent = "reconnecting…";
      setComponent("ws", "reconnecting");
      setTimeout(connect, reconnectDelayMs);
      reconnectDelayMs = Math.min(Math.round(reconnectDelayMs * 1.6), 12000);
    };

    ws.onmessage = (ev) => {
      if (epochAtConnect !== sessionEpoch) return;

      // PTY mode: raw bytes. Headless: trace SSE is the single stream (avoid dupes).
      if (ev.data instanceof ArrayBuffer) {
        if (agentMode === "pty") {
          if (promptVisible) {
            promptVisible = false;
            term.write("\r\n");
          }
          term.write(new Uint8Array(ev.data));
        }
        return;
      }

      let data;
      try {
        data = JSON.parse(ev.data);
      } catch {
        return;
      }
      handleEvent(data);
    };
  }

  function handleEvent(data) {
    switch (data.type) {
      case "connected":
        if (!sessionStarted) termSys(data.alive ? `connected · pid ${data.pid}` : "connected");
        if (!busy) showPrompt();
        break;
      case "starting":
        termSys("starting agent…");
        setBusy(true);
        break;
      case "ready":
        setBusy(false);
        break;
      case "turn_start":
        setBusy(true);
        resetActionStream();
        lastResultText = "";
        lastResultFingerprint = "";
        lastRenderedTurn = 0;
        break;
      case "turn_complete":
        setBusy(false);
        if (data.elapsed_s != null) recordTurnLatency(data.turn, data.elapsed_s, "ws");
        refreshState().then((s) => {
          const text = data.response || s?.response || "";
          if (text && /- [A-D]\)/m.test(text)) {
            term.writeln("\x1b[90m── MCQs (A–D) — also in Questions panel ──\x1b[0m");
            lastResultText = "";
            lastResultFingerprint = "";
            renderDiscoveryText(text);
          } else if (text && (data.questions === 0 || !data.questions)) {
            term.writeln(
              "\x1b[33m[bridge] Agent skipped A–D format — restart bridge (./serve) and /new, or run reparse-session.py\x1b[0m"
            );
          }
        });
        break;
      case "turn_failed":
        setBusy(false);
        recordError("agent", `turn ${data.turn || "?"} failed (exit ${data.code})`, data);
        termSys(`turn ${data.turn || "?"} failed (agent exit ${data.code})${data.message ? ": " + data.message : ""}`);
        refreshState();
        break;
      case "turn_timeout":
        setBusy(false);
        recordError("agent", `turn ${data.turn || "?"} timed out`, data);
        termSys(`turn ${data.turn || "?"} timed out`);
        break;
      case "interrupted":
        setBusy(false);
        termSys("interrupted");
        break;
      case "exit":
        setBusy(false);
        recordError("agent", `agent exited (${data.code})`, data);
        termSys(`agent exited (${data.code})${data.message ? " — " + data.message : ""}`);
        break;
      case "error":
        setBusy(false);
        recordError("agent", data.message || "unknown", data);
        termSys(`error: ${data.message || "unknown"}`);
        break;
      case "session_reset":
        if (!suppressSessionReset) resetUiState();
        break;
      default:
        break;
    }
  }

  function sendWs(obj) {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(obj));
      return true;
    }
    return false;
  }

  async function startSession(pitch) {
    const r = await fetch("/api/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pitch }),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      recordError("startSession", err.error || r.statusText);
      throw new Error(err.error || r.statusText);
    }
    sessionStarted = true;
    await refreshState();
    setBusy(false);
  }

  btnInterrupt.addEventListener("click", () => sendWs({ type: "interrupt" }));
  btnNewSession.addEventListener("click", () => newSession());
  btnTermNew.addEventListener("click", () => newSession());
  btnTermClear.addEventListener("click", () => clearTerminalScreen());

  window.addEventListener("resize", () => { if (fitAddon) fitAddon.fit(); });
  termEl.addEventListener("click", () => term?.focus());
  document.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key.toLowerCase() === "n") {
      e.preventDefault();
      newSession();
    }
  });

  mountTerminal();
  refreshHealth().then(async () => {
    connect();
    const s = await refreshState();
    if (sessionStarted) {
      termSys(`Resuming session ${s?.session_id || ""} · turn ${s?.turn || "—"} — answer below or /new for fresh start`);
      try {
        const t = await fetch("/api/trace?limit=300").then((r) => r.json());
        for (const entry of t.entries || []) writeTraceEntry(entry, { replay: true });
      } catch (_) {}
    }
    if (sessionStarted && !busy) showPrompt();
    else if (!sessionStarted) showPrompt();
  });
})();
