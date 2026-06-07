#!/usr/bin/env python3
"""
Watch an Uplift v6 session while a turn is in flight — poll bridge APIs and tail
agent.trace.jsonl so you can see *where* time is going when things look stuck.

Usage:
  ./scripts/trace-wait.py
  ./scripts/trace-wait.py --url http://127.0.0.1:8786 --interval 2
  ./scripts/trace-wait.py --trace path/to/agent.trace.jsonl

Exit codes: 0 = turn completed during watch, 1 = stuck/timeout, 2 = bridge down.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ANSI_RE = re.compile(r"\x1b\[[0-9?0-9;]*[a-zA-Z]")
MEANINGFUL_STDOUT_MIN = 12  # skip PTY per-character echo lines


def _get(url: str, timeout: float = 5.0) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"_error": str(exc)}


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def _parse_ts(ts: str | None) -> float | None:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.timestamp()
    except ValueError:
        return None


def _clip(s: str, n: int = 100) -> str:
    s = ANSI_RE.sub("", s).replace("\n", " ").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


class TraceWatch:
    def __init__(self, *, from_start: bool = False) -> None:
        self.offset = 0
        self._from_start = from_start
        self.open_turn: int | None = None
        self.open_turn_at: float | None = None
        self.last_meaningful_at: float | None = None
        self.last_meaningful: str = ""
        self.last_spawn: str = ""
        self.last_complete_turn: int | None = None
        self.last_complete_at: float | None = None
        self.errors: list[str] = []
        self.char_echo_only = False
        self.meaningful_since_turn = 0

    def seek_end(self, path: Path) -> None:
        if path.is_file() and not self._from_start:
            self.offset = path.stat().st_size

    def ingest_file(self, path: Path) -> list[str]:
        if not path.is_file():
            return []
        events: list[str] = []
        with path.open("rb") as f:
            f.seek(self.offset)
            chunk = f.read()
            self.offset = f.tell()
        if not chunk:
            return events
        for line in chunk.decode("utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            ev = self._ingest_entry(e)
            if ev:
                events.append(ev)
        return events

    def _ingest_entry(self, e: dict) -> str | None:
        kind = e.get("kind") or ""
        msg = (e.get("msg") or "").strip()
        data = e.get("data") or {}
        level = e.get("level") or "info"
        ts = _parse_ts(e.get("ts"))
        now = time.time()

        if level == "error" or kind == "error":
            self.errors.append(_clip(msg or str(data), 120))
            return f"ERROR {kind}: {_clip(msg, 80)}"

        if kind == "turn":
            action = data.get("action")
            turn = data.get("turn")
            if action == "start" and turn is not None:
                self.open_turn = int(turn)
                self.open_turn_at = ts or now
                self.meaningful_since_turn = 0
                self.char_echo_only = False
                preview = _clip(data.get("text_preview") or msg, 70)
                return f"TURN {turn} START — {preview}"
            if action == "complete" and turn is not None:
                elapsed = data.get("elapsed_s")
                self.last_complete_turn = int(turn)
                self.last_complete_at = ts or now
                self.open_turn = None
                self.open_turn_at = None
                idle = data.get("idle")
                return f"TURN {turn} COMPLETE ({elapsed}s, idle={idle})"
            if action in ("timeout", "failed"):
                self.open_turn = None
                return f"TURN {turn} {action.upper()} — {_clip(msg, 80)}"

        if kind == "spawn":
            self.last_spawn = _clip(msg, 120)
            return f"SPAWN {self.last_spawn}"

        if kind == "stdin":
            turn = data.get("turn", "?")
            return f"STDIN turn={turn} ({data.get('chars', '?')} chars)"

        if kind == "lifecycle":
            if msg in ("prompt detected", "turn complete (idle)", "agent ready", "PTY read loop started"):
                return f"LIFECYCLE {msg}"
            return None

        if kind in ("assistant", "agent", "result", "tool", "thinking"):
            text = data.get("text") or msg
            if text and len(_clip(text, 200)) > 10:
                self._mark_meaningful(ts, now, f"{kind}: {_clip(text, 90)}")
                return f"{kind.upper()} {_clip(text, 90)}"
            return None

        if kind == "stdout":
            if len(msg) < MEANINGFUL_STDOUT_MIN and (data.get("bytes") or 0) <= 8:
                if self.open_turn is not None and self.meaningful_since_turn == 0:
                    self.char_echo_only = True
                return None
            self._mark_meaningful(ts, now, f"stdout: {_clip(msg, 90)}")
            return f"OUT {_clip(msg, 90)}"

        if kind == "validation" and "persisted" in msg:
            return f"ARTIFACTS {msg} turn={data.get('turn')}"

        if "unknown option" in msg:
            self.errors.append(msg)
            return f"CLI PARSE ERROR — {_clip(msg, 100)}"

        return None

    def _mark_meaningful(self, ts: float | None, now: float, label: str) -> None:
        self.last_meaningful_at = ts or now
        self.last_meaningful = label
        if self.open_turn is not None:
            self.meaningful_since_turn += 1
            self.char_echo_only = False


def diagnose(w: TraceWatch, health: dict, diag: dict, wall_start: float) -> str:
    mode = health.get("mode") or diag.get("mode") or "?"
    alive = health.get("agent_alive") if "agent_alive" in health else diag.get("agent_alive")
    pid = health.get("pid") or diag.get("agent_pid")
    persisted_turn = health.get("turn") if health.get("turn") is not None else diag.get("turn", 0)
    now = time.time()

    if w.open_turn is None and w.last_complete_turn is not None:
        return f"OK — last completed turn {w.last_complete_turn}; persisted turn={persisted_turn}"

    if w.open_turn is None:
        return f"IDLE — no in-flight turn in trace (persisted turn={persisted_turn}, mode={mode})"

    since_start = (now - w.open_turn_at) if w.open_turn_at else 0
    since_out = (now - w.last_meaningful_at) if w.last_meaningful_at else since_start

    if not alive:
        return f"STUCK — turn {w.open_turn} open {since_start:.0f}s but agent not alive (pid was {pid})"

    if w.errors:
        return f"STUCK — turn {w.open_turn}: {w.errors[-1][:100]}"

    if mode == "pty" and w.char_echo_only and w.meaningful_since_turn == 0 and since_start > 8:
        return (
            f"STUCK — turn {w.open_turn} {since_start:.0f}s: PTY echo only (TUI may not have submitted input; "
            f"no LLM output). pid={pid}"
        )

    if w.meaningful_since_turn == 0 and since_start > 15:
        return (
            f"STUCK — turn {w.open_turn} {since_start:.0f}s: no meaningful stdout/assistant yet "
            f"(mode={mode}, pid={pid}). Last spawn: {w.last_spawn or 'n/a'}"
        )

    if since_out > 30 and since_start > 30:
        return (
            f"STUCK — turn {w.open_turn} {since_start:.0f}s: silent {since_out:.0f}s after "
            f"last activity «{w.last_meaningful or 'none'}»"
        )

    if since_start < 20:
        phase = "cold start / first token"
    elif since_out < 10:
        phase = "agent working"
    else:
        phase = f"waiting ({since_out:.0f}s since last output)"

    return f"WAIT — turn {w.open_turn} {since_start:.0f}s [{phase}] mode={mode} pid={pid}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default="http://127.0.0.1:8786", help="Bridge base URL")
    ap.add_argument("--interval", type=float, default=2.0, help="Poll interval seconds")
    ap.add_argument("--max-duration", type=float, default=600.0, help="Stop after this many seconds")
    ap.add_argument("--trace", type=Path, default=None, help="agent.trace.jsonl (default: from /api/health)")
    ap.add_argument("--quiet-api", action="store_true", help="Only print on change or every 10s")
    ap.add_argument(
        "--from-start",
        action="store_true",
        help="Replay entire trace file (default: tail only — new lines after launch)",
    )
    args = ap.parse_args()

    base = args.url.rstrip("/")
    watch = TraceWatch(from_start=args.from_start)
    wall_start = time.time()
    last_diag = ""
    tick = 0

    print(f"[{_iso_now()}] trace-wait → {base} (interval={args.interval}s, max={args.max_duration}s)")
    print("  Tip: run while UI/API is waiting; Ctrl+C to stop. Use --from-start to replay full trace.\n")

    trace_path: Path | None = args.trace
    while time.time() - wall_start < args.max_duration:
        tick += 1
        health = _get(f"{base}/api/health") or {}
        if health.get("_error"):
            print(f"[{_iso_now()}] BRIDGE DOWN — {health['_error']}")
            return 2

        diag = _get(f"{base}/api/diagnostics") or {}
        if trace_path is None:
            tp = (health.get("trace") or {}).get("jsonl")
            trace_path = Path(tp) if tp else None

        new_events: list[str] = []
        if trace_path:
            if watch.offset == 0 and not args.from_start and trace_path.is_file():
                watch.seek_end(trace_path)
                if tick == 1:
                    print(f"  tailing {trace_path} from offset {watch.offset}\n")
            new_events = watch.ingest_file(trace_path)

        for ev in new_events:
            print(f"  [{_iso_now()}] {ev}")

        status = diagnose(watch, health, diag, wall_start)
        session = health.get("session_id") or diag.get("session_id")
        changed = status != last_diag
        periodic = tick % max(1, int(10 / args.interval)) == 0
        if changed or periodic or new_events or not args.quiet_api:
            if changed or not args.quiet_api or periodic:
                print(
                    f"[{_iso_now()}] t+{time.time() - wall_start:5.1f}s | {status} | "
                    f"session={session or 'none'}"
                )
        last_diag = status

        if status.startswith("OK —") and watch.open_turn is None:
            errs = [e for e in watch.errors if "unknown option" in e]
            if errs:
                print(f"[{_iso_now()}] FAIL — CLI errors in trace: {_clip(errs[-1], 120)}")
                return 1
            print(f"[{_iso_now()}] DONE — turn completed during watch.")
            return 0

        if status.startswith("STUCK —") and (time.time() - wall_start) >= 30:
            # keep watching but user asked for clarity — already printing STUCK
            pass

        time.sleep(args.interval)

    print(f"[{_iso_now()}] TIMEOUT after {args.max_duration:.0f}s — last: {last_diag}")
    if trace_path:
        print(f"  trace file: {trace_path} ({trace_path.stat().st_size if trace_path.exists() else 0} bytes)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
