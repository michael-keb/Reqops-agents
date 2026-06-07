#!/usr/bin/env python3
"""
Uplift v5 UI bridge — thin HTTP server. Persistent agent chat per session.

  python bridge/server.py
  → http://127.0.0.1:8785

Set UPLIFT_MOCK_AGENT=1 for Playwright / e2e (no real agent calls).
"""

from __future__ import annotations

import json
import os
import queue as queue_mod
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import ThreadingMixIn
from urllib.parse import urlparse

# Allow `python bridge/server.py` from uplift-v5/
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridge.logging_util import log  # noqa: E402
from bridge.session_pool import (  # noqa: E402
    MODE,
    POOL,
    ROOT as POOL_ROOT,
    SESSIONS_DIR,
    agent_available,
    prepare_test_sessions_dir,
    reset_for_tests,
    run_turn,
    session_state,
)
from bridge.terminal_log import clear as clear_terminal  # noqa: E402
from bridge.terminal_log import history as terminal_history  # noqa: E402
from bridge.terminal_log import subscribe as terminal_subscribe  # noqa: E402
from bridge.terminal_log import unsubscribe as terminal_unsubscribe  # noqa: E402

UI_DIR = POOL_ROOT / "ui"
PORT = int(os.environ.get("UPLIFT_UI_PORT", "8785"))


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class Handler(BaseHTTPRequestHandler):
    def _json(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _html(self, content: str) -> None:
        data = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _sse_event(self, payload: dict) -> None:
        self.wfile.write(f"data: {json.dumps(payload)}\n\n".encode("utf-8"))
        self.wfile.flush()

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(f"[ui] {fmt % args}\n")

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            index = UI_DIR / "index.html"
            if not index.is_file():
                self._json(500, {"error": f"missing {index}"})
                return
            self._html(index.read_text(encoding="utf-8"))
        elif path.startswith("/static/"):
            rel = path[len("/static/") :]
            if ".." in rel or rel.startswith("/"):
                self._json(404, {"error": "not found"})
                return
            static = UI_DIR / rel
            if not static.is_file():
                self._json(404, {"error": "not found"})
                return
            ctype = "application/javascript" if rel.endswith(".js") else "text/css"
            data = static.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", f"{ctype}; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)
        elif path == "/api/state":
            self._json(200, session_state())
        elif path == "/api/terminal/history":
            self._json(200, {"lines": terminal_history()})
        elif path == "/api/terminal/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            for entry in terminal_history():
                self._sse_event(entry)
            sub = terminal_subscribe()
            try:
                while True:
                    try:
                        entry = sub.get(timeout=25)
                        self._sse_event(entry)
                    except queue_mod.Empty:
                        self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
            finally:
                terminal_unsubscribe(sub)
        elif path == "/api/health":
            st = session_state()
            self._json(
                200,
                {
                    "agent": agent_available(),
                    "root": str(POOL_ROOT),
                    "mock": st.get("mock", False),
                    "cli_live": st.get("cli_live", False),
                    "mode": st.get("mode"),
                    "persistent": st.get("persistent", False),
                },
            )
        elif path == "/api/reset" and os.environ.get("UPLIFT_MOCK_AGENT", "").strip() in ("1", "true", "yes"):
            reset_for_tests()
            self._json(200, {"ok": True})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
        except json.JSONDecodeError:
            self._json(400, {"error": "invalid json"})
            return

        if path == "/api/start":
            pitch = (body.get("pitch") or "").strip()
            if not pitch:
                self._json(400, {"error": "pitch required"})
                return
            log("[ui] POST /api/start")
            try:
                data = run_turn(pitch, new_pitch=pitch)
            except Exception as exc:
                log(f"ERROR: {exc}", kind="err")
                self._json(500, {"error": str(exc)})
                return
            self._json(200, data)
        elif path == "/api/turn":
            text = (body.get("text") or "").strip()
            if not text:
                self._json(400, {"error": "text required"})
                return
            log("[ui] POST /api/turn")
            try:
                data = run_turn(text)
            except Exception as exc:
                log(f"ERROR: {exc}", kind="err")
                self._json(500, {"error": str(exc)})
                return
            self._json(200, data)
        elif path == "/api/reset" and os.environ.get("UPLIFT_MOCK_AGENT", "").strip() in ("1", "true", "yes"):
            reset_for_tests()
            self._json(200, {"ok": True})
        else:
            self._json(404, {"error": "not found"})


def main() -> None:
    open_browser = "--open" in sys.argv
    if not UI_DIR.is_dir():
        sys.exit(f"UI directory missing: {UI_DIR}")

    mock = os.environ.get("UPLIFT_MOCK_AGENT", "").strip() in ("1", "true", "yes")
    if mock and os.environ.get("UPLIFT_SESSIONS_DIR"):
        prepare_test_sessions_dir()
    else:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    if mock:
        reset_for_tests()
    else:
        clear_terminal()

    url = f"http://127.0.0.1:{PORT}/"
    log(f"Uplift v5 UI → {url}")
    if mock:
        log("MOCK agent mode (UPLIFT_MOCK_AGENT=1) — no Cursor API calls.")
    else:
        log("Mode: cli — same agent chat per session (headless -p, readable output).")
        log("Requires: agent login")
    if not agent_available():
        log("Warning: `agent` not on PATH. Install Cursor CLI and run `agent login`.", kind="err")
    log("Ctrl-C to stop.")
    print(f"Uplift v5 UI → {url}", flush=True)

    if open_browser:
        webbrowser.open(url)

    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down", flush=True)
    finally:
        POOL.close_all()


if __name__ == "__main__":
    main()
