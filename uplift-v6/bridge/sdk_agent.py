"""Agent-sdk HTTP adapter — HeadlessAgent-compatible interface for column agents."""

from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.request
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import artifacts
from . import session as sess
from . import trace

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SDK_URL = os.environ.get("UPLIFT_AGENT_SDK_URL", "http://127.0.0.1:7778")
AGENT_TIMEOUT = int(os.environ.get("UPLIFT_AGENT_TIMEOUT", "600"))

# Cursor CLI ask mode + claude disallowedTools — chat-only workshop agents.
CHAT_ONLY_DISALLOWED_TOOLS = [
    "Read",
    "Grep",
    "Glob",
    "List",
    "Search",
    "Edit",
    "Write",
    "Shell",
    "Delete",
    "ApplyPatch",
    "Bash",
    "Task",
    "WebFetch",
    "WebSearch",
]


class ChatOnlyToolViolation(RuntimeError):
    """Raised when a chat-only agent attempts file or shell tools."""


class InvalidWorkshopResponse(RuntimeError):
    """Raised when a chat-only agent returns non-workshop output."""


def _sdk_provider() -> str:
    return (os.environ.get("UPLIFT_SDK_PROVIDER", "unix_local") or "unix_local").strip().lower()


def _sdk_agent_type() -> str:
    return (os.environ.get("UPLIFT_SDK_AGENT_TYPE", "cursor") or "cursor").strip().lower()

EventFn = Callable[[dict], None]
ChunkFn = Callable[[bytes], None]
ProgressFn = Callable[[str], None]


def _progress_from_sdk_update(update: dict) -> str | None:
    su = update.get("sessionUpdate") or ""
    if su == "agent_thought_chunk":
        return "Thinking…"
    if su in ("agent_message_chunk", "agent_message_delta"):
        content = update.get("content") or {}
        if content.get("type") == "text" and content.get("text"):
            one_line = " ".join(str(content["text"]).split())[:80]
            return f"Drafting… {one_line}" if one_line else "Drafting response…"
    if su == "tool_call":
        title = update.get("title") or update.get("toolCallId") or "tool"
        return f"Tool: {title}"
    if su == "tool_call_update":
        status = update.get("status") or ""
        title = update.get("title") or "tool"
        if status:
            return f"{title} ({status})"
        return f"{title}…"
    return None


def _extract_text_chunk(event: dict) -> str:
    if event.get("method") != "session/update":
        return ""
    update = (event.get("params") or {}).get("update") or {}
    if update.get("sessionUpdate") not in ("agent_message_chunk", "agent_message_delta"):
        return ""
    content = update.get("content") or {}
    if content.get("type") == "text":
        return str(content.get("text") or "")
    return ""


def _is_tool_session_update(update: dict) -> bool:
    su = (update.get("sessionUpdate") or "").lower()
    if su in ("tool_call", "tool_call_update", "execute_tool_started", "execute_tool_completed"):
        return True
    if update.get("toolCallId") or update.get("toolName"):
        return True
    return False


def _extract_stream_error(event: dict) -> str:
    if "error" in event:
        err = event["error"]
        if isinstance(err, dict):
            return str(err.get("message") or err)
        return str(err)
    update = (event.get("params") or {}).get("update") or {}
    if update.get("sessionUpdate") == "error":
        return str(update.get("message") or update)
    return ""


@dataclass
class SdkAgent:
    """Persistent agent-sdk session; one message+stream per turn."""

    cwd: Path = field(default_factory=lambda: ROOT)
    session_dir: Path | None = None
    sdk_url: str = field(default_factory=lambda: DEFAULT_SDK_URL.rstrip("/"))
    agent_type: str = field(default_factory=_sdk_agent_type)
    provider: str = field(default_factory=_sdk_provider)
    chat_only: bool = False
    cli_mode: str | None = None

    _session_id: str | None = field(default=None, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _history: deque[bytes] = field(default_factory=lambda: deque(maxlen=512), init=False, repr=False)
    _chunk_handlers: list[ChunkFn] = field(default_factory=list, init=False, repr=False)
    _event_handlers: list[EventFn] = field(default_factory=list, init=False, repr=False)
    _turn_n: int = field(default=0, init=False, repr=False)
    _waiting_turn: bool = field(default=False, init=False, repr=False)

    @property
    def pid(self) -> int | None:
        return None

    @property
    def alive(self) -> bool:
        return bool(self._session_id)

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

    def _request(
        self,
        method: str,
        path: str,
        body: dict | None = None,
        *,
        timeout: float = 30.0,
    ) -> tuple[int, str]:
        url = f"{self.sdk_url}{path}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8", errors="replace")
        except urllib.error.URLError as exc:
            return 0, str(exc.reason)

    def start(self) -> None:
        if self._session_id:
            trace.info("lifecycle", "reusing sdk session", session_id=self._session_id[:12] + "…")
            self._emit_event(
                {
                    "type": "ready",
                    "pid": None,
                    "mode": "sdk",
                    "session_id": self._session_id[:12],
                }
            )
            return
        create_body: dict = {
            "provider": self.provider,
            "agent_type": self.agent_type,
            "cwd": str(self.cwd),
        }
        mode = self.cli_mode or ("ask" if self.chat_only else None)
        if mode:
            create_body["mode"] = mode
        if self.chat_only:
            create_body["extra_options"] = {"disallowedTools": CHAT_ONLY_DISALLOWED_TOOLS}
        status, raw = self._request(
            "POST",
            "/sessions",
            create_body,
            timeout=120.0,
        )
        if status >= 400:
            raise RuntimeError(f"SDK session create failed ({status}): {raw}")
        payload = json.loads(raw)
        self._session_id = payload.get("session_id") or payload.get("id")
        if not self._session_id:
            raise RuntimeError(f"SDK session create returned no session_id: {raw}")
        trace.spawn(
            cmd=["sdk-agent", "session", self._session_id[:8] + "…"],
            cwd=str(self.cwd),
            pid=0,
            env_keys=["UPLIFT_AGENT_SDK_URL"],
        )
        self._emit_event(
            {
                "type": "ready",
                "pid": None,
                "mode": "sdk",
                "session_id": self._session_id[:12],
            }
        )

    def _stream_message(
        self,
        message: str,
        *,
        on_progress: ProgressFn | None,
    ) -> tuple[str, list[str]]:
        if not self._session_id:
            raise RuntimeError("SDK session not started")
        url = f"{self.sdk_url}/sessions/{self._session_id}/message+stream"
        data = json.dumps({"message": message}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
            method="POST",
        )
        chunks: list[str] = []
        errors: list[str] = []
        started = time.monotonic()
        last_progress_at = 0.0
        last_progress_msg: str | None = None
        tool_violation = False

        with urllib.request.urlopen(req, timeout=AGENT_TIMEOUT) as resp:
            if resp.status >= 400:
                body = resp.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"message+stream failed ({resp.status}): {body}")

            while True:
                if time.monotonic() - started > AGENT_TIMEOUT:
                    raise TimeoutError(f"SDK turn timed out after {AGENT_TIMEOUT}s")
                line = resp.readline()
                if not line:
                    break
                text_line = line.decode("utf-8", errors="replace").strip()
                if not text_line or not text_line.startswith("data:"):
                    continue
                payload = text_line[5:].strip()
                if payload == "[DONE]":
                    break
                try:
                    event = json.loads(payload)
                except json.JSONDecodeError:
                    continue

                err = _extract_stream_error(event)
                if err:
                    errors.append(err)

                chunk = _extract_text_chunk(event)
                if chunk:
                    chunks.append(chunk)
                    self._emit_chunk(chunk.encode("utf-8"))

                update = (event.get("params") or {}).get("update") or {}
                if self.chat_only and _is_tool_session_update(update):
                    tool_violation = True
                    if self._session_id:
                        self._request("POST", f"/sessions/{self._session_id}/cancel", timeout=10.0)
                    break

                if on_progress:
                    pm = _progress_from_sdk_update(update)
                    if pm:
                        now = time.monotonic()
                        if pm == last_progress_msg and pm in ("Thinking…", "Drafting response…"):
                            continue
                        if now - last_progress_at >= 0.8 or pm != last_progress_msg:
                            on_progress(pm)
                            last_progress_at = now
                            last_progress_msg = pm

        if tool_violation:
            raise ChatOnlyToolViolation("chat-only agent attempted a file or shell tool")
        return "".join(chunks), errors

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

        trace.stdin(line, turn=turn)
        trace.turn_boundary(action="start", turn=turn, text=line)
        self._emit_event({"type": "turn_start", "text": line[:200], "turn": turn})

        started = time.monotonic()
        result_text = ""
        stream_errors: list[str] = []
        rc = 0
        err_detail = ""

        try:
            result_text, stream_errors = self._stream_message(line, on_progress=on_progress)
            if stream_errors:
                rc = 1
                err_detail = stream_errors[-1]
        except TimeoutError as exc:
            rc = 1
            err_detail = str(exc)
            elapsed = time.monotonic() - started
            with self._lock:
                self._waiting_turn = False
            trace.turn_boundary(action="timeout", turn=turn, elapsed_s=AGENT_TIMEOUT)
            self._emit_event({"type": "turn_timeout", "turn": turn})
            return
        except ChatOnlyToolViolation:
            with self._lock:
                self._waiting_turn = False
            trace.warn("validation", "chat-only tool violation — turn cancelled", turn=turn)
            self._emit_event({"type": "tool_violation", "turn": turn})
            raise
        except InvalidWorkshopResponse:
            with self._lock:
                self._waiting_turn = False
            trace.warn("validation", "invalid workshop response — turn rejected", turn=turn)
            self._emit_event({"type": "workshop_invalid", "turn": turn})
            raise
        except Exception as exc:
            rc = 1
            err_detail = str(exc)
            trace.error("SDK message+stream failed", exc, turn=turn)
            with self._lock:
                self._waiting_turn = False
            self._emit_event({"type": "error", "message": err_detail, "turn": turn})
            self._emit_event(
                {
                    "type": "turn_failed",
                    "code": rc,
                    "turn": turn,
                    "elapsed_s": round(time.monotonic() - started, 2),
                    "message": err_detail,
                }
            )
            return
        finally:
            with self._lock:
                self._waiting_turn = False

        elapsed = time.monotonic() - started
        captured = (result_text or "").strip()

        if rc == 0 and captured and self.chat_only:
            from .discovery_context import valid_discovery_response

            if not valid_discovery_response(captured):
                trace.warn("validation", "rejecting non-workshop agent output", turn=turn)
                raise InvalidWorkshopResponse("agent output is not valid Reflection + 5 MCQs")

        if rc == 0 and captured:
            session_turn = turn
            if self.session_dir:
                prior = sess.turn_count(self.session_dir)
                session_turn = artifacts.persist_turn(
                    self.session_dir,
                    user_input=line,
                    response_text=captured,
                )
                artifacts.verify_turn_tools(turn=turn, is_first_turn=(prior == 0))
                td = self.session_dir / "turns" / f"{session_turn:02d}"
                full_path = td / "response.full.md"
                if full_path.is_file():
                    captured = full_path.read_text(encoding="utf-8").strip()

            trace.turn_boundary(
                action="complete",
                turn=session_turn,
                elapsed_s=round(elapsed, 2),
                text=line,
            )
            self._emit_event(
                {
                    "type": "turn_complete",
                    "elapsed_s": round(elapsed, 2),
                    "idle": False,
                    "turn": session_turn,
                    "bridge_turn": turn,
                    "questions": 0,
                    "response": captured[:32000] if captured else None,
                }
            )
            return

        if not err_detail:
            err_detail = "empty response from SDK session"
        trace.record(
            "exit",
            f"SDK turn failed {rc}",
            level="error",
            data={"code": rc, "turn": turn, "detail": err_detail},
        )
        self._emit_event(
            {
                "type": "exit",
                "code": rc,
                "turn": turn,
                "message": err_detail,
            }
        )
        trace.turn_boundary(action="failed", turn=turn, elapsed_s=round(elapsed, 2), text=line)
        self._emit_event(
            {
                "type": "turn_failed",
                "code": rc,
                "turn": turn,
                "elapsed_s": round(elapsed, 2),
                "message": err_detail,
            }
        )

    def interrupt(self) -> None:
        if not self._session_id:
            return
        with self._lock:
            self._waiting_turn = False
        status, _ = self._request("POST", f"/sessions/{self._session_id}/cancel")
        if status >= 400 and status != 404:
            trace.warn("lifecycle", "SDK cancel failed", status=status, session_id=self._session_id[:8])
        self._emit_event({"type": "interrupted", "turn": self._turn_n})

    def clear_buffers(self) -> None:
        with self._lock:
            self._history.clear()
            self._turn_n = 0

    def stop(self) -> None:
        sid = self._session_id
        with self._lock:
            self._waiting_turn = False
            self._session_id = None
        if sid:
            status, _ = self._request("DELETE", f"/sessions/{sid}", timeout=60.0)
            if status >= 400 and status != 404:
                trace.warn("lifecycle", "SDK session delete failed", status=status, session_id=sid[:8])
        trace.info("lifecycle", "sdk agent stopped")
        self._emit_event({"type": "stopped"})
