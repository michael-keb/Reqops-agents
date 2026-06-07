#!/usr/bin/env python3
"""DEPRECATED — use the CLI instead of this HTTP server.

  cd Call-backup && ./uplift              # interactive REPL (v4)
  ./uplift --new "your pitch"

Legacy web UI (v3 only, needs markdown parser + browser):
  UPLIFT_WEB_LEGACY=1 python uplift-v3.0/web/server.py
  → http://127.0.0.1:8765
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

WEB_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = WEB_DIR.parent
REPO_ROOT = PROJECT_ROOT.parent
HARNESS = PROJECT_ROOT / "test-rubric.py"
SESSIONS_DIR = PROJECT_ROOT / "sessions"
ACTIVE_FILE = SESSIONS_DIR / ".active"
HTML_PATH = WEB_DIR / "index.html"

PORT = int(os.environ.get("UPLIFT_WEB_PORT", "8765"))


def harness_python() -> str:
    """Use project .venv python if present (openai installed); else current interpreter."""
    for candidate in (
        PROJECT_ROOT / ".venv" / "bin" / "python",
        REPO_ROOT / ".venv" / "bin" / "python",
    ):
        if candidate.is_file():
            return str(candidate)
    return sys.executable


def _clean_mcq_header(header: str) -> str:
    return re.sub(r"\*\*", "", header).strip().strip("`")


def _parse_mcq_header(header: str) -> tuple[str | None, str | None]:
    """Return (gap_code_or_none, title). gap may be None for human-only titles."""
    header = _clean_mcq_header(header)
    if not header:
        return None, None

    # ### 1. G1 — Title  |  ### GA — Title  |  ### 1. `G2` — Title
    m = re.match(
        r"(?:\d+\.\s+)?([GQ][0-9A-D])\s*[—–-]\s*(.+)$",
        header,
    )
    if m:
        return m.group(1), m.group(2).strip()

    # ### 1. **What job, measurably?**  (assessment-first / v4 phrasing — no gap prefix)
    m = re.match(r"(?:\d+\.\s+)?(.+)$", header)
    if m:
        title = m.group(1).strip()
        return None, title or None

    return None, None


def load_gap_hints(turn_dir: Path) -> list[str]:
    """Gap codes from question-plan (v3) or selection (v4) when MCQ headers omit them."""
    hints: list[str] = []

    qp = turn_dir / "question-plan.json"
    if qp.is_file():
        try:
            plan = json.loads(qp.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            plan = {}
        for slot in plan.get("slots") or []:
            gap = slot.get("gap")
            if gap:
                hints.append(gap)
        if not hints:
            assessment = (plan.get("constraints") or {}).get("assessment") or {}
            if assessment.get("primary_gap"):
                hints.append(assessment["primary_gap"])

    sel = turn_dir / "selection.json"
    if not hints and sel.is_file():
        try:
            sel_data = json.loads(sel.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            sel_data = {}
        primary = sel_data.get("primary") or {}
        if primary.get("gap"):
            hints.append(primary["gap"])

    return hints


def parse_mcq_response(reply: str, *, gap_hints: list[str] | None = None) -> dict:
    """Parse a markdown LLM reply into structured MCQ data."""
    out: dict = {
        "reflection": None,
        "questions": [],
        "state_codes": None,
        "phase_gate": False,
        "phase_gate_note": None,
        "raw": reply,
    }
    gap_hints = list(gap_hints or [])

    m = re.search(r"## Reflection\s*\n(.*?)(?=\n## |\Z)", reply, re.DOTALL)
    if m:
        out["reflection"] = m.group(1).strip()

    m = re.search(r"## State codes\s*\n(.*?)(?=\n## |\Z)", reply, re.DOTALL)
    if m:
        out["state_codes"] = m.group(1).strip()

    if "_(no MCQs this turn — phase gate)_" in reply:
        out["phase_gate"] = True
        m = re.search(r"## Questions\s*\n(.*?)(?=\n## |\Z)", reply, re.DOTALL)
        if m:
            note = re.sub(
                r"_\(no MCQs this turn — phase gate\)_",
                "",
                m.group(1),
            ).strip()
            out["phase_gate_note"] = note or None
        return out

    # Tolerantly find all ### MCQ blocks anywhere in the reply.
    parts = re.split(r"(?:^|\n)### ", reply)
    q_idx = 0
    for part in parts[1:]:
        part = part.strip()
        if not part:
            continue
        if "\n## " in part:
            part = part.split("\n## ", 1)[0]
        lines = part.split("\n")
        gap, title = _parse_mcq_header(lines[0])
        if not title:
            continue
        if gap is None:
            gap = gap_hints[q_idx] if q_idx < len(gap_hints) else f"Q{q_idx + 1}"
        opt_start = None
        for i, line in enumerate(lines[1:], start=1):
            if re.match(r"^\s*-\s*[A-D]\)", line):
                opt_start = i
                break
        stem = "\n".join(lines[1:opt_start]).strip() if opt_start else ""
        opts: list[dict] = []
        if opt_start:
            for line in lines[opt_start:]:
                om = re.match(r"^\s*-\s*([A-D])\)\s*(.+)$", line)
                if om:
                    opts.append({"letter": om.group(1), "text": om.group(2).strip()})
        if not opts:
            continue
        out["questions"].append(
            {"gap": gap, "title": title, "stem": stem, "options": opts}
        )
        q_idx += 1

    return out


def read_active_state() -> dict | None:
    """Return latest parsed turn from active session, or None if no active session."""
    if not ACTIVE_FILE.is_file():
        return None
    sid = ACTIVE_FILE.read_text(encoding="utf-8").strip()
    session_dir = SESSIONS_DIR / sid
    if not session_dir.is_dir():
        return None

    turns_dir = session_dir / "turns"
    if not turns_dir.is_dir():
        return None

    turn_nums = sorted(
        int(p.name)
        for p in turns_dir.iterdir()
        if p.is_dir() and re.fullmatch(r"\d{2}", p.name)
    )
    if not turn_nums:
        return None
    latest = turn_nums[-1]
    reply_path = turns_dir / f"{latest:02d}" / "llm-response.txt"
    if not reply_path.is_file():
        return None
    turn_dir = turns_dir / f"{latest:02d}"
    reply = reply_path.read_text(encoding="utf-8")
    parsed = parse_mcq_response(reply, gap_hints=load_gap_hints(turn_dir))

    user_input_path = turns_dir / f"{latest:02d}" / "user-input.txt"
    parsed["last_user_input"] = (
        user_input_path.read_text(encoding="utf-8").strip()
        if user_input_path.is_file()
        else None
    )
    parsed["session_id"] = sid
    parsed["turn"] = latest
    return parsed


def run_turn(text: str, *, new: bool) -> dict:
    """Spawn the harness as a subprocess, then return the latest parsed turn."""
    flag = "--new" if new else "--continue"
    before_turn = None
    if not new and ACTIVE_FILE.is_file():
        state_before = read_active_state()
        if state_before:
            before_turn = state_before.get("turn")

    proc = subprocess.run(
        [harness_python(), str(HARNESS), flag, text],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=180,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"harness exited {proc.returncode}\nstderr:\n{proc.stderr}\nstdout:\n{proc.stdout}"
        )
    state = read_active_state()
    if state is None:
        raise RuntimeError("turn ran but no active session state could be read")
    if before_turn is not None and state.get("turn") == before_turn:
        raise RuntimeError(
            "Harness finished but turn number did not advance. "
            "Check OPENAI_API_KEY in .env or harness logs."
        )
    state["harness_stdout_tail"] = "\n".join(proc.stdout.splitlines()[-8:])
    return state


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body, ctype: str = "application/json") -> None:
        if isinstance(body, (dict, list)):
            body = json.dumps(body)
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(f"[{self.log_date_time_string()}] {fmt % args}\n")

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            if not HTML_PATH.is_file():
                self._send(500, {"error": f"missing {HTML_PATH}"})
                return
            self._no_cache_html(HTML_PATH.read_text(encoding="utf-8"))
        elif self.path == "/api/state":
            state = read_active_state()
            self._send(200, state or {"session_id": None})
        else:
            self._send(404, {"error": "not found"})

    def _no_cache_html(self, html: str) -> None:
        data = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        if self.path != "/api/turn":
            self._send(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid json"})
            return
        text = (body.get("text") or "").strip()
        if not text:
            self._send(400, {"error": "text required"})
            return
        new = bool(body.get("new"))
        try:
            data = run_turn(text, new=new)
        except Exception as exc:
            import traceback

            traceback.print_exc()
            self._send(500, {"error": str(exc)})
            return
        self._send(200, data)


def main() -> None:
    import os

    if not os.environ.get("UPLIFT_WEB_LEGACY"):
        sys.stderr.write(
            "\nUplift web UI is disabled. Use the CLI (no HTTP API):\n\n"
            "  ./uplift                 interactive discovery REPL\n"
            "  ./uplift --new \"pitch\"   start a session\n"
            "  ./uplift --list          list sessions\n\n"
            "From repo root (Call-backup). Legacy browser UI:\n"
            "  UPLIFT_WEB_LEGACY=1 python uplift-v3.0/web/server.py\n\n"
        )
        sys.exit(1)

    if not HARNESS.is_file():
        sys.exit(f"Harness not found: {HARNESS}")
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Uplift 3.0 web frontend → http://127.0.0.1:{PORT}", flush=True)
    print("Ctrl-C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down", flush=True)


if __name__ == "__main__":
    main()
