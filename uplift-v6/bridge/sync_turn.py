"""Synchronous discovery turn for ReqOps HTTP API (SDK or headless CLI, session-scoped)."""

from __future__ import annotations

import os
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from . import session as sess
from . import trace
from .discovery_context import valid_discovery_response
from .discovery_format import (
    WORKSHOP_CODE_RETRY_MESSAGE,
    WORKSHOP_TOOL_RETRY_MESSAGE,
    bootstrap_message,
    wrap_discovery_message,
)
from .headless_agent import HeadlessAgent
from .mock_agent import MockAgent
from .sdk_agent import ChatOnlyToolViolation, InvalidWorkshopResponse, SdkAgent

ROOT = Path(__file__).resolve().parent.parent
MOCK = os.environ.get("UPLIFT_MOCK_AGENT", "").strip() in ("1", "true", "yes")

_global_turn_lock = threading.Lock()
_session_locks: dict[str, threading.Lock] = {}
_sdk_agents: dict[str, SdkAgent] = {}

ProgressFn = Callable[[str], None]

AgentLike = HeadlessAgent | MockAgent | SdkAgent


def _discovery_runner() -> str:
    return os.environ.get("UPLIFT_DISCOVERY_RUNNER", "sdk").strip().lower()


def _turn_lock(session_id: str) -> threading.Lock:
    if _discovery_runner() == "sdk":
        if session_id not in _session_locks:
            _session_locks[session_id] = threading.Lock()
        return _session_locks[session_id]
    return _global_turn_lock


def _discovery_workspace(session_dir: Path) -> Path:
    """Isolate discovery agent cwd to the workshop session folder only."""
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir.resolve()


def _make_agent(session_dir: Path) -> AgentLike:
    workspace = _discovery_workspace(session_dir)
    if MOCK:
        return MockAgent(cwd=workspace, env_extra={"UPLIFT_SESSION": str(session_dir)})
    if _discovery_runner() == "sdk":
        sid = session_dir.name
        agent = _sdk_agents.get(sid)
        if agent is not None and (
            not agent.chat_only or agent.cwd.resolve() != workspace
        ):
            try:
                agent.stop()
            except Exception as exc:
                trace.warn("lifecycle", "discovery agent stop failed", detail=str(exc))
            del _sdk_agents[sid]
            agent = None
        if agent is None:
            agent = SdkAgent(
                cwd=workspace,
                session_dir=session_dir,
                chat_only=True,
                cli_mode="ask",
            )
            _sdk_agents[sid] = agent
        return agent
    return HeadlessAgent(
        cwd=workspace,
        env_extra={"UPLIFT_SESSION": str(session_dir)},
        cli_mode="ask",
    )


def _latest_response(events: list[dict]) -> str:
    last = next((e for e in reversed(events) if e.get("type") == "turn_complete"), None)
    if not last:
        return ""
    return str(last.get("response") or "").strip()


def run_turn(
    session_id: str,
    text: str,
    *,
    on_progress: ProgressFn | None = None,
) -> dict[str, Any]:
    """Run one discovery turn; block until complete. Returns turn payload."""
    path = sess.activate_session(session_id)
    trace.set_session_dir(path)

    def prog(msg: str) -> None:
        if on_progress:
            on_progress(msg)

    events: list[dict] = []
    agent = _make_agent(path)
    runner = _discovery_runner()
    max_attempts = 3

    def on_event(payload: dict) -> None:
        events.append(payload)
        kind = payload.get("type")
        if kind == "turn_start":
            prog("Running agent…")
        elif kind == "turn_complete":
            prog(f"Done · {payload.get('elapsed_s', '?')}s")
        elif kind in ("turn_failed", "exit", "turn_timeout"):
            prog(payload.get("message") or "Turn failed")
        elif kind == "tool_violation":
            prog("Tool use blocked — retrying as workshop…")
        elif kind == "workshop_invalid":
            prog("Invalid output — retrying workshop format…")

    agent.on_event(on_event)

    user_text = text.strip()
    wrapped = wrap_discovery_message(user_text, session_dir=path)

    with _turn_lock(session_id):
        prog("Connecting to agent-sdk…" if runner == "sdk" else "Connecting to agent…")
        if not agent.alive:
            agent.start()
        for attempt in range(1, max_attempts + 1):
            prog("Thinking…")
            prompt = wrapped
            if attempt == 2:
                prompt = f"{WORKSHOP_TOOL_RETRY_MESSAGE}\n\n{wrapped}"
            elif attempt >= 3:
                prompt = f"{WORKSHOP_CODE_RETRY_MESSAGE}\n\n{WORKSHOP_TOOL_RETRY_MESSAGE}\n\n{wrapped}"
            try:
                agent.send(prompt, on_progress=prog)
            except ChatOnlyToolViolation:
                if attempt >= max_attempts:
                    raise RuntimeError(
                        "Discovery agent attempted file tools after retries — workshop is chat-only"
                    ) from None
                trace.warn("validation", "discovery tool violation — retrying turn", attempt=attempt)
                prog("Retrying without tools…")
                continue
            except InvalidWorkshopResponse:
                if attempt >= max_attempts:
                    raise RuntimeError(
                        "Discovery agent failed to produce Reflection + 5 MCQs after retries"
                    ) from None
                trace.warn("validation", "discovery invalid output — retrying turn", attempt=attempt)
                prog("Retrying workshop format…")
                continue

            if MOCK:
                break
            response = _latest_response(events)
            if valid_discovery_response(response):
                break
            if attempt >= max_attempts:
                raise RuntimeError(
                    "Discovery agent returned non-workshop output (expected Reflection + Questions)"
                )
            trace.warn(
                "validation",
                "discovery output rejected — not valid workshop MCQs",
                attempt=attempt,
            )
            prog("Invalid workshop output — retrying…")

    last = next((e for e in reversed(events) if e.get("type") == "turn_complete"), None)
    failed = next(
        (e for e in reversed(events) if e.get("type") in ("turn_failed", "exit", "turn_timeout")),
        None,
    )
    if failed and not last:
        msg = failed.get("message") or "agent turn failed"
        raise RuntimeError(msg)

    turn_n = int(last.get("turn") or sess.turn_count(path)) if last else sess.turn_count(path)
    turn_data = sess.load_turn_json(path, turn_n) or {}
    reflection = (turn_data.get("reflection") or "").strip()
    questions = turn_data.get("questions") if isinstance(turn_data.get("questions"), list) else []

    td = sess.turn_dir(path, turn_n)
    response_md = ""
    if td and (td / "response.md").is_file():
        response_md = (td / "response.md").read_text(encoding="utf-8")

    return {
        "session_id": session_id,
        "turn": turn_n,
        "elapsed_s": last.get("elapsed_s") if last else None,
        "reflection": reflection,
        "questions": questions,
        "response_md": response_md,
        "events": events,
        "runner": runner,
    }


def start_session(
    pitch: str,
    *,
    session_id: str | None = None,
    bootstrap: bool = True,
    on_progress: ProgressFn | None = None,
) -> dict[str, Any]:
    """Create or activate session; optionally run bootstrap turn."""
    sid = sess.validate_session_id(session_id) if session_id else None
    created = False
    if sid and sess.session_exists(sid):
        path = sess.activate_session(sid)
    else:
        path = sess.create_session(pitch, session_id=sid)
        sid = path.name
        created = True

    trace.set_session_dir(path)
    out: dict[str, Any] = {"session_id": sid, "created": created, **sess.session_state_for(sid)}

    if bootstrap:
        def prog(msg: str) -> None:
            if on_progress:
                on_progress(msg)

        turn = run_turn(
            sid,
            bootstrap_message(pitch=pitch, session_dir=str(path)),
            on_progress=prog,
        )
        out["bootstrap_turn"] = turn
        out.update(sess.session_state_for(sid))

    return out
