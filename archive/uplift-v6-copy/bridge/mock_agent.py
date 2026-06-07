"""Mock agent for Playwright e2e — no Cursor CLI required."""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import artifacts
from . import session as sess
from . import trace

ROOT = Path(__file__).resolve().parent.parent
MOCK_DELAY_MS = int(os.environ.get("UPLIFT_MOCK_DELAY_MS", "150"))
MOCK_FAIL_TURN = int(os.environ.get("UPLIFT_MOCK_FAIL_TURN", "0") or "0")

EventFn = Callable[[dict], None]
ChunkFn = Callable[[bytes], None]
ProgressFn = Callable[[str], None]

TOPICS = (
    "primary user",
    "trust and safety",
    "core workflow",
    "monetization",
    "go-to-market",
    "retention loop",
    "ops and support",
    "data and privacy",
    "competitive wedge",
    "success metrics",
)


def _response_md(*, turn: int, reflection: str, question: str, options: list[str]) -> str:
    opts = "\n".join(f"- {o}" for o in options)
    if turn == 1:
        return f"## Reflection\n{reflection}\n\n## Question\n**{question}**\n\n{opts}\n"
    return f"## Reflection\n{reflection}\n\n## Question\n**{question}** (turn {turn})\n\n{opts}\n"


def _mock_response(turn: int, user_text: str) -> str:
    topic = TOPICS[(turn - 1) % len(TOPICS)]
    if turn == 1:
        reflection = (
            f"You described {user_text.strip()[:80]} — that sets the product frame. "
            f"The biggest open thread is {topic}."
        )
        blocks: list[str] = [
            "## Reflection",
            reflection,
            "",
            "## Questions",
            "",
        ]
        q_stems = [
            ("Who is the primary user on day one?", TOPICS[0]),
            ("What is the core job-to-be-done in the first session?", TOPICS[1]),
            ("How will you earn trust before money changes hands?", TOPICS[2]),
            ("What is the smallest shippable workflow?", TOPICS[3]),
            ("What would make someone switch from the status quo?", TOPICS[4]),
        ]
        opts = [
            "A) Individual consumers booking directly",
            "B) Small businesses managing a roster",
            "C) Both, but one side leads supply",
        ]
        for i, (stem, _t) in enumerate(q_stems, start=1):
            blocks.append(f"### {i}. {stem}")
            blocks.append("")
            blocks.extend(f"- {o}" for o in opts)
            blocks.append("")
        return "\n".join(blocks).strip() + "\n"
    else:
        reflection = (
            f"You answered: {user_text.strip()[:120]} — that narrows the wedge. "
            f"Next we should pressure-test {topic}."
        )
        question = f"What must be true before someone trusts this with real money or access?"
        options = [
            "A) Reviews and identity verification on both sides",
            "B) Insurance or guarantee from the platform",
            "C) Starts inside existing social trust (friends/referrals)",
        ]
    return _response_md(turn=turn, reflection=reflection, question=question, options=options)


@dataclass
class MockAgent:
    cwd: Path = field(default_factory=lambda: ROOT)
    env_extra: dict[str, str] = field(default_factory=dict)
    _event_handlers: list[EventFn] = field(default_factory=list, init=False)
    _chunk_handlers: list[ChunkFn] = field(default_factory=list, init=False)
    _turn_n: int = field(default=0, init=False)
    _waiting_turn: bool = field(default=False, init=False)
    _chat_id: str = field(default="mock-chat", init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    @property
    def pid(self) -> int | None:
        return 4242

    @property
    def alive(self) -> bool:
        return True

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
        for fn in list(self._chunk_handlers):
            try:
                fn(data)
            except Exception as exc:
                trace.error("chunk handler failed", exc)

    def replay_history(self, _fn: ChunkFn) -> None:
        return

    def start(self) -> None:
        trace.info("lifecycle", "mock agent ready")
        self._emit_event({"type": "ready", "pid": self.pid, "mode": "mock", "chat_id": self._chat_id[:12]})

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
            session_dir = sess.active_session()
            if not session_dir:
                self._waiting_turn = False
                raise RuntimeError("no active session for mock agent")

            try:
                trace.stdin(line, turn=turn)
                trace.turn_boundary(action="start", turn=turn, text=line)
                self._emit_event({"type": "turn_start", "text": line[:200], "turn": turn})

                started = time.monotonic()
                delay = max(MOCK_DELAY_MS / 1000.0, 0.05)

                if MOCK_FAIL_TURN and turn == MOCK_FAIL_TURN:
                    elapsed = time.monotonic() - started
                    trace.record("exit", "mock agent forced failure", level="error", data={"code": 1, "turn": turn})
                    self._emit_event({"type": "exit", "code": 1, "turn": turn, "message": "mock forced failure"})
                    trace.turn_boundary(action="failed", turn=turn, elapsed_s=round(elapsed, 2), text=line)
                    self._emit_event(
                        {
                            "type": "turn_failed",
                            "code": 1,
                            "turn": turn,
                            "elapsed_s": round(elapsed, 2),
                            "message": "mock forced failure",
                        }
                    )
                    return

                if on_progress:
                    on_progress("Running agent…")
                time.sleep(delay * 0.3)
                trace.info("lifecycle", "agent running", pid=self.pid, turn=turn)
                if on_progress:
                    on_progress("Thinking…")
                trace.agent_internal("thinking", "thinking done", turn=turn, subtype="completed")
                time.sleep(delay * 0.2)
                if on_progress:
                    on_progress("Drafting response…")
                trace.agent_internal("assistant", "drafting", turn=turn, partial=True, text="## Reflection")

                pitch = None
                if turn == 1 and "Start uplift discovery for:" in line:
                    for part in line.splitlines():
                        if part.startswith("Start uplift discovery for:"):
                            pitch = part.split(":", 1)[1].strip()
                            break

                user_text = pitch or line
                response = _mock_response(turn, user_text)

                trace.agent_internal("result", f"done · {response[:80]}…", turn=turn, text=response, success=True)

                prior = sess.turn_count(session_dir)
                session_turn = artifacts.persist_turn(session_dir, user_input=line, response_text=response)
                artifacts.verify_turn_tools(turn=turn, is_first_turn=(prior == 0))
                chat_id = f"mock-{session_dir.name[-12:]}"
                (session_dir / ".chat-id").write_text(chat_id, encoding="utf-8")

                elapsed = time.monotonic() - started
                trace.turn_boundary(action="complete", turn=session_turn, elapsed_s=round(elapsed, 2), text=line)
                self._emit_event(
                    {
                        "type": "turn_complete",
                        "elapsed_s": round(elapsed, 2),
                        "idle": False,
                        "turn": session_turn,
                        "bridge_turn": turn,
                    }
                )
            finally:
                self._waiting_turn = False

    def interrupt(self) -> None:
        with self._lock:
            self._waiting_turn = False
        trace.info("lifecycle", "mock interrupt")
        self._emit_event({"type": "interrupted", "turn": self._turn_n})

    def clear_buffers(self) -> None:
        self._turn_n = 0
        self._waiting_turn = False
        self._chat_id = "mock-chat"

    def stop(self) -> None:
        trace.info("lifecycle", "mock agent stopped")
        self._emit_event({"type": "stopped"})
