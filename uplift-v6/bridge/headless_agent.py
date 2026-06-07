"""Headless Cursor `agent` — same chat via --resume, readable stdout per turn."""

from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from shutil import which
from typing import Callable

from . import artifacts
from . import session as sess
from . import trace
from .stream_parser import StreamEvent, parse_stream_line

ROOT = Path(__file__).resolve().parent.parent
AGENT_TIMEOUT = int(os.environ.get("UPLIFT_AGENT_TIMEOUT", "600"))
DEFAULT_OUTPUT = os.environ.get("UPLIFT_AGENT_OUTPUT", "stream-json").strip()
# Parallel column agents all call `agent create-chat` — serialize to avoid cli-config races.
_CLI_INIT_LOCK = threading.Lock()

EventFn = Callable[[dict], None]
ChunkFn = Callable[[bytes], None]
ProgressFn = Callable[[str], None]


def _fmt_cmd(cmd: list[str]) -> str:
    out: list[str] = []
    skip = False
    for i, arg in enumerate(cmd):
        if skip:
            skip = False
            continue
        if arg == "-p" and i + 1 < len(cmd):
            out.extend(["-p", "<prompt>"])
            skip = True
        elif arg == "--resume" and i + 1 < len(cmd):
            cid = cmd[i + 1]
            out.extend(["--resume", cid[:8] + "…" if len(cid) > 8 else cid])
            skip = True
        else:
            out.append(arg)
    return " ".join(out)


@dataclass
class HeadlessAgent:
    """Persistent agent *conversation* (chat id on disk); headless -p each turn."""

    cwd: Path = field(default_factory=lambda: ROOT)
    env_extra: dict[str, str] = field(default_factory=dict)
    _chat_id: str | None = field(default=None, init=False, repr=False)
    _proc: subprocess.Popen[str] | None = field(default=None, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _history: deque[bytes] = field(default_factory=lambda: deque(maxlen=512), init=False, repr=False)
    _chunk_handlers: list[ChunkFn] = field(default_factory=list, init=False, repr=False)
    _event_handlers: list[EventFn] = field(default_factory=list, init=False, repr=False)
    _turn_n: int = field(default=0, init=False, repr=False)
    _waiting_turn: bool = field(default=False, init=False, repr=False)

    @property
    def pid(self) -> int | None:
        return self._proc.pid if self._proc and self._proc.poll() is None else None

    @property
    def alive(self) -> bool:
        if self._proc and self._proc.poll() is None:
            return True
        return bool(self._chat_id or self._chat_id_path.is_file())

    @property
    def _session_dir(self) -> Path | None:
        raw = self.env_extra.get("UPLIFT_SESSION")
        return Path(raw) if raw else None

    @property
    def _chat_id_path(self) -> Path:
        base = self._session_dir or self.cwd
        return base / ".chat-id"

    def on_chunk(self, fn: ChunkFn) -> None:
        self._chunk_handlers.append(fn)

    def on_event(self, fn: EventFn) -> None:
        self._event_handlers.append(fn)

    def _emit_event(self, payload: dict) -> None:
        trace.event(payload)
        for fn in list(self._event_handlers):
            try:
                fn(payload)
            except Exception as exc:
                trace.error("event handler failed", exc)

    def _emit_chunk(self, data: bytes, *, trace_stdout: bool = True) -> None:
        if not data:
            return
        if trace_stdout:
            trace.stdout_bytes(data)
        self._history.append(data)
        for fn in list(self._chunk_handlers):
            try:
                fn(data)
            except Exception as exc:
                trace.error("chunk handler failed", exc)

    def _env(self) -> dict[str, str]:
        return {**os.environ, **self.env_extra}

    def _agent_bin(self) -> str:
        path = which("agent")
        if not path:
            raise RuntimeError("agent CLI not on PATH — install Cursor CLI and run `agent login`")
        return path

    def _load_chat_id(self) -> str | None:
        if self._chat_id:
            return self._chat_id
        if self._chat_id_path.is_file():
            cid = self._chat_id_path.read_text(encoding="utf-8").strip()
            if cid:
                self._chat_id = cid
                return cid
        return None

    def _save_chat_id(self, chat_id: str) -> None:
        self._chat_id = chat_id.strip()
        self._chat_id_path.parent.mkdir(parents=True, exist_ok=True)
        self._chat_id_path.write_text(self._chat_id, encoding="utf-8")

    def _ensure_chat(self) -> str:
        existing = self._load_chat_id()
        if existing:
            trace.info("lifecycle", "reusing chat id", chat_id=existing[:12] + "…")
            return existing
        with _CLI_INIT_LOCK:
            existing = self._load_chat_id()
            if existing:
                trace.info("lifecycle", "reusing chat id", chat_id=existing[:12] + "…")
                return existing
            trace.info("lifecycle", "agent create-chat")
            proc = subprocess.run(
                [self._agent_bin(), "create-chat"],
                cwd=str(self.cwd),
                capture_output=True,
                text=True,
                timeout=30,
                env=self._env(),
            )
            if proc.returncode != 0:
                err = (proc.stderr or proc.stdout or "").strip()
                raise RuntimeError(f"agent create-chat failed: {err}")
            chat_id = (proc.stdout or "").strip().splitlines()[-1].strip()
            if not chat_id:
                raise RuntimeError("agent create-chat returned empty id")
            self._save_chat_id(chat_id)
            trace.info("lifecycle", "chat id created", chat_id=chat_id[:12] + "…")
            return chat_id

    def _cmd(self, chat_id: str) -> list[str]:
        """Headless argv only — user text is sent on stdin (MCQ lines start with `-`)."""
        fmt = DEFAULT_OUTPUT if DEFAULT_OUTPUT in ("text", "json", "stream-json") else "stream-json"
        cmd = [
            self._agent_bin(),
            "--resume",
            chat_id,
            "-p",
            "--output-format",
            fmt,
            "--trust",
            "--force",
        ]
        if fmt == "stream-json" and os.environ.get("UPLIFT_STREAM_PARTIAL", "1").strip() not in ("0", "false", "no"):
            cmd.append("--stream-partial-output")
        if os.environ.get("UPLIFT_APPROVE_MCPS", "1").strip() not in ("0", "false", "no"):
            cmd.append("--approve-mcps")
        return cmd

    def _handle_stream_line(self, raw_line: str, *, turn: int) -> StreamEvent | None:
        trace.agent_stream_raw(raw_line)
        ev = parse_stream_line(raw_line, cwd=str(self.cwd), turn=turn)
        if not ev:
            return None
        data = dict(ev.data)
        data.pop("turn", None)
        trace.agent_internal(ev.kind, ev.msg, turn=turn, **data)
        if ev.terminal and ev.kind not in ("assistant", "thinking"):
            self._emit_chunk(ev.terminal.encode("utf-8"), trace_stdout=True)
        return ev

    def history_blob(self, *, max_chunks: int | None = 512) -> bytes:
        chunks = list(self._history)
        if max_chunks is not None and len(chunks) > max_chunks:
            chunks = chunks[-max_chunks:]
        return b"".join(chunks)

    def replay_history(self, fn: ChunkFn) -> None:
        blob = self.history_blob()
        if blob:
            fn(blob)

    def start(self) -> None:
        chat_id = self._ensure_chat()
        trace.spawn(
            cmd=[self._agent_bin(), "--resume", chat_id[:8] + "…", "-p", "<ready>"],
            cwd=str(self.cwd),
            pid=0,
            env_keys=sorted(self._env().keys()),
        )
        self._emit_event({"type": "ready", "pid": None, "mode": "headless", "chat_id": chat_id[:12]})

    def send(self, text: str, *, on_progress: ProgressFn | None = None) -> None:
        line = text.strip()
        if not line:
            return
        with self._lock:
            if self._waiting_turn:
                trace.warn("lifecycle", "send ignored — turn already running")
                self._emit_event({"type": "input_rejected", "reason": "turn_running", "turn": self._turn_n})
                return
            self._waiting_turn = True
            self._turn_n += 1
            turn = self._turn_n
            chat_id = self._ensure_chat()
            cmd = self._cmd(chat_id)
            trace.stdin(line, turn=turn)
            trace.turn_boundary(action="start", turn=turn, text=line)
            trace.info("spawn", _fmt_cmd(cmd), turn=turn)
            self._emit_event({"type": "turn_start", "text": line[:200], "turn": turn})

            started = time.monotonic()
            try:
                self._proc = subprocess.Popen(
                    cmd,
                    cwd=str(self.cwd),
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env=self._env(),
                )
            except Exception as exc:
                self._waiting_turn = False
                trace.error("agent spawn failed", exc, cmd=_fmt_cmd(cmd))
                self._emit_event({"type": "error", "message": str(exc)})
                raise

            if self._proc.stdin:
                try:
                    self._proc.stdin.write(line if line.endswith("\n") else line + "\n")
                    self._proc.stdin.close()
                except OSError as exc:
                    trace.error("stdin write failed", exc, turn=turn)
                    self._proc.kill()
                    self._waiting_turn = False
                    raise

            trace.info("lifecycle", "agent running", pid=self._proc.pid, turn=turn)
            if self._proc.stdout is None:
                self._waiting_turn = False
                raise RuntimeError("agent stdout unavailable")

            result_text = ""
            text_buf: list[str] = []
            plain_lines: list[str] = []
            try:
                fmt = DEFAULT_OUTPUT if DEFAULT_OUTPUT in ("text", "json", "stream-json") else "stream-json"
                for raw_line in self._proc.stdout:
                    if fmt == "stream-json":
                        ev = self._handle_stream_line(raw_line, turn=turn)
                        if on_progress and ev:
                            from .stream_progress import progress_message_from_event

                            pm = progress_message_from_event(ev)
                            if pm:
                                on_progress(pm)
                        if ev and ev.kind == "result" and ev.data.get("text"):
                            result_text = str(ev.data["text"])
                        elif ev and ev.data.get("parse_error") and ev.terminal:
                            plain_lines.append(ev.terminal)
                        elif ev and ev.kind == "assistant" and ev.data.get("text"):
                            plain_lines.append(
                                ev.data["text"] if str(ev.data["text"]).endswith("\n") else str(ev.data["text"]) + "\n"
                            )
                    elif fmt == "json":
                        trace.agent_stream_raw(raw_line)
                        ev = self._handle_stream_line(raw_line, turn=turn)
                        if ev and ev.kind == "result" and ev.data.get("text"):
                            result_text = str(ev.data["text"])
                    else:
                        chunk = raw_line.encode("utf-8", errors="replace")
                        text_buf.append(raw_line)
                        self._emit_chunk(chunk)
            except Exception as exc:
                trace.error("stdout read failed", exc)
                self._proc.kill()
                raise
            finally:
                try:
                    self._proc.wait(timeout=AGENT_TIMEOUT)
                except subprocess.TimeoutExpired:
                    self._proc.kill()
                    self._waiting_turn = False
                    trace.turn_boundary(action="timeout", turn=turn, elapsed_s=AGENT_TIMEOUT)
                    self._emit_event({"type": "turn_timeout", "turn": turn})
                    return

                rc = self._proc.returncode if self._proc.returncode is not None else 1
                elapsed = time.monotonic() - started
                self._proc = None
                self._waiting_turn = False
                if not result_text and text_buf:
                    result_text = "".join(text_buf).strip()
                if not result_text and plain_lines:
                    combined = "".join(plain_lines).strip()
                    m = re.search(r"## Reflection\b", combined, re.IGNORECASE)
                    result_text = combined[m.start() :].strip() if m else combined
                elif result_text and plain_lines:
                    combined = "".join(plain_lines).strip()
                    # Keep stream-json `result` payload when it already has fenced blocks
                    # (plain_lines deltas can be longer but omit ```json fences).
                    if len(combined) > len(result_text) and "```" not in result_text:
                        result_text = combined
                cli_err = "".join(text_buf) + "".join(plain_lines)
                if rc == 0 and re.search(r"^error:", cli_err, re.MULTILINE | re.IGNORECASE):
                    rc = 1
                session_turn = turn
                if rc == 0 and self._session_dir:
                    if result_text:
                        prior = sess.turn_count(self._session_dir)
                        session_turn = artifacts.persist_turn(
                            self._session_dir,
                            user_input=line,
                            response_text=result_text,
                        )
                        artifacts.verify_turn_tools(turn=turn, is_first_turn=(prior == 0))
                    else:
                        trace.warn("validation", "turn finished with no capturable response", turn=turn)
                    trace.turn_boundary(
                        action="complete",
                        turn=session_turn,
                        elapsed_s=round(elapsed, 2),
                        text=line,
                    )
                    formatted = ""
                    qn = 0
                    captured = (result_text or "").strip()
                    if self._session_dir:
                        td = self._session_dir / "turns" / f"{session_turn:02d}"
                        full_path = td / "response.full.md"
                        rp = td / "response.md"
                        tj = td / "turn.json"
                        if full_path.is_file():
                            captured = full_path.read_text(encoding="utf-8").strip()
                        elif rp.is_file():
                            formatted = rp.read_text(encoding="utf-8")
                            if not captured:
                                captured = formatted.strip()
                        if tj.is_file():
                            qn = len(json.loads(tj.read_text(encoding="utf-8")).get("questions") or [])
                    if not captured and formatted:
                        captured = formatted.strip()
                    self._emit_event(
                        {
                            "type": "turn_complete",
                            "elapsed_s": round(elapsed, 2),
                            "idle": False,
                            "turn": session_turn,
                            "bridge_turn": turn,
                            "questions": qn,
                            "response": captured[:32000] if captured else None,
                        }
                    )
                    return

                err_detail = (result_text or "".join(text_buf)).strip()
                if err_detail:
                    err_detail = err_detail.replace("\n", " ")[:240]
                trace.record(
                    "exit",
                    f"agent exited {rc}",
                    level="error",
                    data={"code": rc, "turn": turn, "detail": err_detail},
                )
                self._emit_event(
                    {
                        "type": "exit",
                        "code": rc,
                        "turn": turn,
                        "message": err_detail or f"agent process failed with exit code {rc}",
                    }
                )
                trace.turn_boundary(action="failed", turn=turn, elapsed_s=round(elapsed, 2), text=line)
                self._emit_event(
                    {
                        "type": "turn_failed",
                        "code": rc,
                        "turn": turn,
                        "elapsed_s": round(elapsed, 2),
                        "message": err_detail or f"exit code {rc}",
                    }
                )

    def interrupt(self) -> None:
        with self._lock:
            if self._proc and self._proc.poll() is None:
                trace.info("lifecycle", "killing agent subprocess", pid=self._proc.pid)
                self._proc.kill()
                self._waiting_turn = False
                self._emit_event({"type": "interrupted", "turn": self._turn_n})

    def clear_buffers(self) -> None:
        """Drop terminal replay history and chat binding for a fresh session."""
        with self._lock:
            self._history.clear()
            self._turn_n = 0
            self._chat_id = None

    def stop(self) -> None:
        with self._lock:
            if self._proc and self._proc.poll() is None:
                self._proc.kill()
            self._proc = None
            self._waiting_turn = False
        trace.info("lifecycle", "headless agent stopped")
        self._emit_event({"type": "stopped"})
