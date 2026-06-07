"""Structured trace log — exactly what the agent process receives, emits, and errors."""

from __future__ import annotations

import json
import os
import queue
import re
import sys
import threading
import time
import traceback
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = Path(os.environ.get("UPLIFT_LOGS_DIR", str(ROOT / "logs"))).resolve()
MAX_ENTRIES = int(os.environ.get("UPLIFT_TRACE_MAX", "5000"))
QUIET = os.environ.get("UPLIFT_QUIET", "").strip() in ("1", "true", "yes")
VERBOSE_STDOUT = os.environ.get("UPLIFT_TRACE_STDOUT", "lines").strip()  # lines | chunks | off

ANSI_RE = re.compile(r"\x1b\[[0-9?0-9;]*[a-zA-Z]")

_lock = threading.Lock()
_entries: deque[dict[str, Any]] = deque(maxlen=MAX_ENTRIES)
_subscribers: list[queue.Queue[dict[str, Any]]] = []
_session_dir: Path | None = None
_jsonl_path: Path | None = None
_stream_jsonl_path: Path | None = None
_line_buf: str = ""
_seq = 0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def set_session_dir(path: Path | None) -> None:
    """Mirror trace + raw PTY transcript into the active session folder."""
    global _session_dir, _jsonl_path, _transcript_path, _stream_jsonl_path
    with _lock:
        _session_dir = path.resolve() if path else None
        if _session_dir:
            _session_dir.mkdir(parents=True, exist_ok=True)
            _jsonl_path = _session_dir / "agent.trace.jsonl"
            _transcript_path = _session_dir / "agent-pty.txt"
            _stream_jsonl_path = _session_dir / "agent.stream.jsonl"
        else:
            LOGS_DIR.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            _jsonl_path = LOGS_DIR / f"trace-{stamp}.jsonl"
            _transcript_path = LOGS_DIR / f"pty-{stamp}.txt"
            _stream_jsonl_path = LOGS_DIR / f"stream-{stamp}.jsonl"


def _write_jsonl(entry: dict[str, Any]) -> None:
    path = _jsonl_path
    if not path:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        path = LOGS_DIR / f"trace-{stamp}.jsonl"
    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        if not QUIET:
            sys.stderr.write(f"[trace] write failed: {exc}\n")


def _append_transcript(data: bytes) -> None:
    path = _transcript_path
    if not path:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        path = LOGS_DIR / f"pty-{stamp}.txt"
    try:
        with path.open("ab") as f:
            f.write(data)
    except OSError:
        pass


def _emit(entry: dict[str, Any]) -> None:
    global _seq
    _seq += 1
    entry.setdefault("ts", _now_iso())
    entry["seq"] = _seq
    with _lock:
        _entries.append(entry)
        for sub in list(_subscribers):
            try:
                sub.put_nowait(entry)
            except queue.Full:
                pass
    _write_jsonl(entry)
    if not QUIET:
        kind = entry.get("kind", "?")
        msg = entry.get("msg", "")
        extra = entry.get("data") or {}
        detail = ""
        if kind == "stdin":
            detail = f" ({len(extra.get('text', ''))} chars)"
        elif kind == "stdout":
            detail = f" ({extra.get('bytes', 0)} B)"
        elif kind in ("tool", "thinking", "assistant", "result", "agent"):
            detail = f" [{extra.get('event_type', '')}]"
        elif kind == "error":
            detail = f" {extra.get('exc_type', '')}"
        sys.stderr.write(f"[{entry['ts']}] {kind}: {msg}{detail}\n")
        if kind == "error" and extra.get("traceback"):
            sys.stderr.write(extra["traceback"] + "\n")
        sys.stderr.flush()


def record(
    kind: str,
    msg: str,
    *,
    level: str = "info",
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entry = {"kind": kind, "level": level, "msg": msg}
    if data:
        entry["data"] = data
    _emit(entry)
    return entry


def info(kind: str, msg: str, **data: Any) -> None:
    record(kind, msg, level="info", data=data or None)


def warn(kind: str, msg: str, **data: Any) -> None:
    record(kind, msg, level="warn", data=data or None)


def error(msg: str, exc: BaseException | None = None, **data: Any) -> None:
    payload = dict(data)
    if exc is not None:
        payload["exc_type"] = type(exc).__name__
        payload["exc_msg"] = str(exc)
        payload["traceback"] = traceback.format_exc()
    record("error", msg, level="error", data=payload)


def spawn(*, cmd: list[str], cwd: str, pid: int, env_keys: list[str]) -> None:
    record(
        "spawn",
        f"agent pid {pid}",
        data={"cmd": cmd, "cwd": cwd, "pid": pid, "env_keys": env_keys},
    )


def stdin(text: str, *, turn: int | None = None) -> None:
    preview = text.replace("\n", "\\n")
    if len(preview) > 120:
        preview = preview[:117] + "…"
    record(
        "stdin",
        preview or "(empty)",
        data={"text": text, "chars": len(text), "turn": turn},
    )


def stdout_bytes(data: bytes) -> None:
    """Append raw PTY output; emit line-based trace entries."""
    global _line_buf
    if not data:
        return
    _append_transcript(data)
    if VERBOSE_STDOUT == "off":
        return
    text = data.decode("utf-8", errors="replace")
    if VERBOSE_STDOUT == "chunks":
        clean = strip_ansi(text).replace("\r", "")
        if clean.strip():
            record("stdout", clean[:500], data={"bytes": len(data), "mode": "chunk"})
        return
    _line_buf += text
    lines = _line_buf.split("\n")
    _line_buf = lines.pop() if lines else ""
    for part in lines:
        clean = strip_ansi(part.replace("\r", "")).strip()
        if not clean:
            continue
        if len(clean) > 800:
            clean = clean[:797] + "…"
        record("stdout", clean, data={"bytes": len(part.encode("utf-8", errors="replace"))})


def agent_stream_raw(line: str) -> None:
    """Append verbatim agent CLI stream-json line."""
    path = _stream_jsonl_path
    if not path:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        path = LOGS_DIR / f"stream-{stamp}.jsonl"
    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(line.rstrip("\n") + "\n")
    except OSError:
        pass


def agent_internal(kind: str, msg: str, *, turn: int | None = None, **data: Any) -> None:
    """Structured agent stream event (tool, thinking, assistant, etc.)."""
    payload = dict(data)
    if turn is not None:
        payload["turn"] = turn
    record(kind, msg, level="info", data=payload or None)


def event(payload: dict[str, Any]) -> None:
    record("event", payload.get("type", "unknown"), data=payload)


def http(method: str, path: str, *, status: int | None = None, detail: str = "") -> None:
    msg = f"{method} {path}"
    if status is not None:
        msg += f" → {status}"
    if detail:
        msg += f" ({detail})"
    record("http", msg, data={"method": method, "path": path, "status": status, "detail": detail})


def ws(direction: str, msg_type: str, *, detail: str = "") -> None:
    record("ws", f"{direction} {msg_type}", data={"direction": direction, "type": msg_type, "detail": detail})


def turn_boundary(
    *,
    action: str,
    turn: int | None = None,
    elapsed_s: float | None = None,
    idle: bool | None = None,
    text: str = "",
) -> None:
    record(
        "turn",
        action,
        data={
            "action": action,
            "turn": turn,
            "elapsed_s": elapsed_s,
            "idle": idle,
            "text_preview": text[:200] if text else "",
        },
    )


def history(*, limit: int = 500, kind: str | None = None) -> list[dict[str, Any]]:
    with _lock:
        items = list(_entries)
    if kind:
        items = [e for e in items if e.get("kind") == kind]
    return items[-limit:]


def clear() -> None:
    global _line_buf
    with _lock:
        _entries.clear()
        _line_buf = ""
    record("sys", "trace cleared")


def paths() -> dict[str, str | None]:
    return {
        "jsonl": str(_jsonl_path) if _jsonl_path else None,
        "transcript": str(_transcript_path) if _transcript_path else None,
        "stream": str(_stream_jsonl_path) if _stream_jsonl_path else None,
        "session": str(_session_dir) if _session_dir else None,
    }


def subscribe() -> queue.Queue[dict[str, Any]]:
    q: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=1024)
    with _lock:
        _subscribers.append(q)
    return q


def unsubscribe(q: queue.Queue[dict[str, Any]]) -> None:
    with _lock:
        if q in _subscribers:
            _subscribers.remove(q)
