"""Long-lived Cursor `agent` CLI on a PTY — stdin/stdout like a real terminal."""

from __future__ import annotations

import os
import pty
import re
import select
import signal
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

ROOT = Path(__file__).resolve().parent.parent
PROMPT_MARK = "→"
# Cursor Agent TUI (2026.05+) shows "Composer …" splash, not always a → glyph.
READY_MARK = "Composer"
IDLE_DONE_S = float(os.environ.get("UPLIFT_IDLE_DONE_S", "2.5"))
STARTUP_TIMEOUT_S = float(os.environ.get("UPLIFT_STARTUP_TIMEOUT_S", "120"))
TURN_TIMEOUT_S = float(os.environ.get("UPLIFT_TURN_TIMEOUT_S", "600"))
ROLLING_BYTES = 200_000

EventFn = Callable[[dict], None]
ChunkFn = Callable[[bytes], None]


@dataclass
class PtyAgent:
    """One persistent agent child process; chat messages go to stdin."""

    cwd: Path = field(default_factory=lambda: ROOT)
    env_extra: dict[str, str] = field(default_factory=dict)
    _master: int | None = field(default=None, init=False, repr=False)
    _proc: subprocess.Popen[bytes] | None = field(default=None, init=False, repr=False)
    _reader: threading.Thread | None = field(default=None, init=False, repr=False)
    _stop: threading.Event = field(default_factory=threading.Event, init=False, repr=False)
    _write_lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _buf: str = field(default="", init=False, repr=False)
    _buf_lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _history: deque[bytes] = field(default_factory=lambda: deque(maxlen=512), init=False, repr=False)
    _chunk_handlers: list[ChunkFn] = field(default_factory=list, init=False, repr=False)
    _event_handlers: list[EventFn] = field(default_factory=list, init=False, repr=False)
    _waiting_turn: bool = field(default=False, init=False, repr=False)
    _turn_started_at: float = field(default=0.0, init=False, repr=False)
    _last_output_at: float = field(default=0.0, init=False, repr=False)
    _turn_n: int = field(default=0, init=False, repr=False)
    _current_input: str = field(default="", init=False, repr=False)

    @property
    def pid(self) -> int | None:
        return self._proc.pid if self._proc else None

    @property
    def alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    @property
    def _session_dir(self) -> Path | None:
        raw = self.env_extra.get("UPLIFT_SESSION")
        return Path(raw) if raw else None

    def _buffer_plain(self) -> str:
        with self._buf_lock:
            return trace.strip_ansi(self._buf).replace("\r", "")

    def _is_at_prompt(self) -> bool:
        plain = self._buffer_plain()
        if PROMPT_MARK in plain:
            return True
        # Warm-start only: splash "Composer …" is not end-of-turn while waiting.
        if self._waiting_turn:
            return False
        return READY_MARK in plain and len(plain.strip()) > 80

    def _extract_turn_response(self) -> str:
        with self._buf_lock:
            raw = trace.strip_ansi(self._buf).replace("\r", "")
        if PROMPT_MARK in raw:
            raw = raw[: raw.rfind(PROMPT_MARK)]
        m = re.search(r"## Reflection\b", raw, re.IGNORECASE)
        if m:
            return raw[m.start() :].strip()
        return raw.strip()

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

    def _emit_chunk(self, data: bytes) -> None:
        if not data:
            return
        trace.stdout_bytes(data)
        self._history.append(data)
        for fn in list(self._chunk_handlers):
            try:
                fn(data)
            except Exception as exc:
                trace.error("chunk handler failed", exc)

    def _agent_bin(self) -> str:
        path = which("agent")
        if not path:
            raise RuntimeError("agent CLI not on PATH — install Cursor CLI and run `agent login`")
        return path

    def _env(self) -> dict[str, str]:
        return {**os.environ, **self.env_extra}

    def _read_loop(self) -> None:
        assert self._master is not None
        trace.info("lifecycle", "PTY read loop started", pid=self.pid)
        try:
            while not self._stop.is_set() and self.alive:
                try:
                    r, _, _ = select.select([self._master], [], [], 0.2)
                    if not r:
                        self._maybe_idle_complete()
                        continue
                    chunk = os.read(self._master, 4096)
                    if not chunk:
                        trace.warn("lifecycle", "PTY read EOF")
                        break
                    now = time.monotonic()
                    self._last_output_at = now
                    text = chunk.decode("utf-8", errors="replace")
                    with self._buf_lock:
                        self._buf = (self._buf + text)[-ROLLING_BYTES:]
                    self._emit_chunk(chunk)
                    if self._waiting_turn and self._is_at_prompt():
                        trace.info("lifecycle", "prompt detected")
                        self._complete_turn()
                    else:
                        self._maybe_idle_complete()
                except OSError as exc:
                    trace.error("PTY read error", exc)
                    break
        except Exception as exc:
            trace.error("PTY read loop crashed", exc)
        finally:
            trace.info("lifecycle", "PTY read loop ended", pid=self.pid)
        rc = self._proc.poll() if self._proc else None
        if rc is not None and not self._stop.is_set():
            trace.record("exit", f"agent exited {rc}", level="warn" if rc else "info", data={"code": rc, "pid": self.pid})
            self._emit_event({"type": "exit", "code": rc})

    def _maybe_idle_complete(self) -> None:
        if not self._waiting_turn:
            return
        if self._last_output_at <= self._turn_started_at:
            return
        # Ignore TUI echo / splash; need real agent output before idle completion.
        plain = self._buffer_plain()
        if not re.search(r"## Reflection\b", plain, re.IGNORECASE) and PROMPT_MARK not in plain:
            return
        idle_for = time.monotonic() - self._last_output_at
        if idle_for >= IDLE_DONE_S:
            trace.info("lifecycle", "turn complete (idle)", idle_s=round(idle_for, 2))
            self._complete_turn(idle=True)

    def _complete_turn(self, *, idle: bool = False) -> None:
        if not self._waiting_turn:
            return
        self._waiting_turn = False
        elapsed = time.monotonic() - self._turn_started_at
        session_turn = self._turn_n
        session_dir = self._session_dir
        if session_dir:
            response_text = self._extract_turn_response()
            if response_text:
                prior = sess.turn_count(session_dir)
                session_turn = artifacts.persist_turn(
                    session_dir,
                    user_input=self._current_input,
                    response_text=response_text,
                )
                artifacts.verify_turn_tools(turn=self._turn_n, is_first_turn=(prior == 0))
            else:
                trace.warn("validation", "turn finished with no capturable response", turn=self._turn_n)
        trace.turn_boundary(
            action="complete",
            turn=session_turn,
            elapsed_s=round(elapsed, 2),
            idle=idle,
            text=self._current_input,
        )
        payload: dict = {
            "type": "turn_complete",
            "elapsed_s": round(elapsed, 2),
            "idle": idle,
            "turn": session_turn,
            "bridge_turn": self._turn_n,
            "questions": 0,
            "response": None,
        }
        if session_dir:
            import json

            td = session_dir / "turns" / f"{session_turn:02d}"
            rp = td / "response.md"
            tj = td / "turn.json"
            if rp.is_file():
                payload["response"] = rp.read_text(encoding="utf-8")[:8000]
            if tj.is_file():
                payload["questions"] = len(json.loads(tj.read_text(encoding="utf-8")).get("questions") or [])
        self._emit_event(payload)

    def _wait_for_prompt(self, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._is_at_prompt():
                return True
            if not self.alive:
                trace.warn("lifecycle", "agent died while waiting for prompt")
                return False
            time.sleep(0.15)
        tail = ""
        with self._buf_lock:
            tail = trace.strip_ansi(self._buf.strip())[-500:]
        trace.warn("lifecycle", "prompt timeout", timeout_s=timeout, tail=tail)
        return False

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
        with self._write_lock:
            if self.alive:
                trace.info("lifecycle", "start skipped — already alive", pid=self.pid)
                return
            self._stop.clear()
            master, slave = pty.openpty()
            cmd = [self._agent_bin()]
            env = self._env()
            try:
                self._proc = subprocess.Popen(
                    cmd,
                    stdin=slave,
                    stdout=slave,
                    stderr=slave,
                    cwd=str(self.cwd),
                    close_fds=True,
                    env=env,
                )
            except Exception as exc:
                trace.error("agent spawn failed", exc, cmd=cmd, cwd=str(self.cwd))
                raise
            finally:
                os.close(slave)
            self._master = master
            with self._buf_lock:
                self._buf = ""
            self._reader = threading.Thread(target=self._read_loop, daemon=True, name="pty-read")
            self._reader.start()
            trace.spawn(cmd=cmd, cwd=str(self.cwd), pid=self._proc.pid, env_keys=sorted(env.keys()))

        self._emit_event({"type": "starting", "pid": self.pid})
        if not self._wait_for_prompt(STARTUP_TIMEOUT_S):
            tail = ""
            with self._buf_lock:
                tail = trace.strip_ansi(self._buf.strip())[-500:]
            self.stop()
            msg = tail or "Agent did not show a prompt — run `agent login`"
            trace.error("startup failed", detail=msg)
            raise RuntimeError(msg)
        trace.info("lifecycle", "agent ready", pid=self.pid)
        self._emit_event({"type": "ready", "pid": self.pid, "mode": "pty"})

    def send(self, text: str) -> None:
        if not self.alive:
            self.start()
        line = text.strip()
        if not line:
            return
        self._turn_n += 1
        self._current_input = line
        trace.stdin(line, turn=self._turn_n)
        trace.turn_boundary(action="start", turn=self._turn_n, text=line)
        with self._write_lock:
            self._waiting_turn = True
            self._turn_started_at = time.monotonic()
            self._last_output_at = self._turn_started_at
            with self._buf_lock:
                idx = self._buf.rfind(PROMPT_MARK)
                if idx >= 0:
                    self._buf = self._buf[idx + len(PROMPT_MARK) :]
            assert self._master is not None
            try:
                os.write(self._master, (line + "\n").encode("utf-8"))
            except OSError as exc:
                trace.error("stdin write failed", exc, turn=self._turn_n)
                self._waiting_turn = False
                raise
        self._emit_event({"type": "turn_start", "text": line[:200], "turn": self._turn_n})

        deadline = time.monotonic() + TURN_TIMEOUT_S
        while self._waiting_turn and time.monotonic() < deadline:
            time.sleep(0.1)
        if self._waiting_turn:
            self._waiting_turn = False
            trace.turn_boundary(action="timeout", turn=self._turn_n, elapsed_s=TURN_TIMEOUT_S)
            self._emit_event({"type": "turn_timeout", "turn": self._turn_n})

    def interrupt(self) -> None:
        if self._proc and self.alive:
            trace.info("lifecycle", "SIGINT sent", pid=self._proc.pid, turn=self._turn_n)
            os.kill(self._proc.pid, signal.SIGINT)
            self._waiting_turn = False
            self._emit_event({"type": "interrupted", "turn": self._turn_n})

    def clear_buffers(self) -> None:
        self._history.clear()
        self._turn_n = 0
        with self._buf_lock:
            self._buf = ""

    def stop(self) -> None:
        with self._write_lock:
            self._stop.set()
            self._waiting_turn = False
            pid = self._proc.pid if self._proc else None
            if self._proc and self.alive:
                try:
                    trace.info("lifecycle", "terminating agent", pid=pid)
                    self._proc.terminate()
                    self._proc.wait(timeout=3)
                except Exception as exc:
                    trace.warn("lifecycle", "terminate failed, killing", pid=pid, exc=str(exc))
                    self._proc.kill()
            if self._master is not None:
                try:
                    os.close(self._master)
                except OSError:
                    pass
            self._master = None
            self._proc = None
        trace.info("lifecycle", "agent stopped", pid=pid)
        self._emit_event({"type": "stopped"})
