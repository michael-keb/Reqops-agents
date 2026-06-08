"""Per-column headless CLI agent loop — parse ## Action, mutate store, continue."""

from __future__ import annotations

import json
import os
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .actions import parse_action_blocks
from .cancel_registry import is_cancelled
from .columns import SignalColumn
from .prompts import (
    column_prompt,
    continuation_prompt,
    description_card_prompt,
    description_continuation_prompt,
    description_repair_prompt,
    repair_prompt,
    title_column_prompt,
    title_continuation_prompt,
)
from .store import MutationResult, SignalStore

StoreLike = SignalStore

UPLIFT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(UPLIFT_ROOT) not in sys.path:
    sys.path.insert(0, str(UPLIFT_ROOT))

from bridge.headless_agent import HeadlessAgent  # noqa: E402
from bridge.sdk_agent import SdkAgent  # noqa: E402

MAX_AGENT_TURNS = int(os.environ.get("UPLIFT_SIGNAL_MAX_TURNS", "30"))
MAX_ATTEMPTS = 3
MAX_PARSE_RETRIES = int(os.environ.get("UPLIFT_SIGNAL_PARSE_RETRIES", "5"))
BACKOFF_S = (2, 4, 8)


def _mock_mode() -> bool:
    return os.environ.get("UPLIFT_MOCK_AGENT", "").strip() in ("1", "true", "yes")


def _signals_runner_mode() -> str:
    return os.environ.get("UPLIFT_SIGNALS_RUNNER", "sdk").strip().lower()


def extract_agent_dir(session_dir: Path, run_id: str) -> Path:
    return session_dir / "signals-v01" / run_id / "agent"


def title_agent_dir(session_dir: Path, run_id: str) -> Path:
    return session_dir / "signals-v01" / run_id / "title-agent"


def description_agent_dir(session_dir: Path, run_id: str) -> Path:
    return session_dir / "signals-v01" / run_id / "description-agent"


# Signal agents get prompts inline — isolate cwd to agent artifact dir, chat-only (no repo reads).
def _make_persisted_agent(*, agent_dir: Path) -> HeadlessAgent | SdkAgent:
    agent_dir.mkdir(parents=True, exist_ok=True)
    workspace = agent_dir.resolve()
    if _signals_runner_mode() == "sdk":
        return SdkAgent(cwd=workspace, session_dir=agent_dir, chat_only=True, cli_mode="ask")
    return HeadlessAgent(
        cwd=workspace,
        env_extra={
            "UPLIFT_SESSION": str(agent_dir),
            "UPLIFT_STREAM_PARTIAL": "0",
            "UPLIFT_APPROVE_MCPS": "0",
        },
        cli_mode="ask",
    )


def make_extract_agent(*, agent_dir: Path) -> HeadlessAgent | SdkAgent:
    """One shared CLI agent for a full extract run (all columns sequential)."""
    return _make_persisted_agent(agent_dir=agent_dir)


def make_title_agent(*, session_dir: Path, run_id: str) -> HeadlessAgent | SdkAgent:
    return _make_persisted_agent(agent_dir=title_agent_dir(session_dir, run_id))


def make_description_agent(*, session_dir: Path, run_id: str) -> HeadlessAgent | SdkAgent:
    return _make_persisted_agent(agent_dir=description_agent_dir(session_dir, run_id))


def _make_signal_agent(*, col_dir: Path) -> HeadlessAgent | SdkAgent:
    if _signals_runner_mode() == "sdk":
        return SdkAgent(cwd=UPLIFT_ROOT, session_dir=col_dir)
    return HeadlessAgent(
        cwd=UPLIFT_ROOT,
        env_extra={
            "UPLIFT_SESSION": str(col_dir),
            "UPLIFT_STREAM_PARTIAL": "0",
            "UPLIFT_APPROVE_MCPS": "0",
        },
    )


ProgressFn = Callable[[str], None]
MutationFn = Callable[[dict[str, Any]], None]
TitleAddedFn = Callable[[dict[str, Any]], None]


@dataclass
class DraftCard:
    column_id: str
    node_id: str
    title: str
    updated_at: str


@dataclass
class ColumnRunResult:
    column_id: str
    status: str
    summary: str = ""
    mutations: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    elapsed_s: float = 0.0
    raw_path: str = ""


def _signals_col_dir(session_dir: Path, column: SignalColumn) -> Path:
    return session_dir / "signals" / column.slug


def _write_memory(col_dir: Path, *, run_id: str, memory: list[dict[str, Any]]) -> None:
    col_dir.mkdir(parents=True, exist_ok=True)
    (col_dir / "column_run_memory.json").write_text(
        json.dumps({"run_id": run_id, "mutations": memory}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _mock_title_response(
    *,
    column: SignalColumn,
    transcript: str,
    turn: int,
    added_this_run: bool,
) -> str:
    snippet = transcript.strip().splitlines()[0][:80] if transcript.strip() else column.title
    if turn == 1 and not added_this_run:
        body = {
            "action": "add_draft",
            "column": column.id,
            "card": {"title": f"{column.title}: {snippet[:40]}" if snippet else column.title},
        }
    else:
        body = {
            "action": "complete",
            "column": column.id,
            "summary": "mock: added 1 draft title" if added_this_run or turn > 1 else "mock: no titles",
        }
    return "## Action\n\n```json\n" + json.dumps(body, indent=2) + "\n```\n"


def _mock_description_response(*, column: SignalColumn, card: dict[str, Any], transcript: str) -> str:
    snippet = transcript.strip().splitlines()[0][:80] if transcript.strip() else "mock evidence"
    body = {
        "action": "edit",
        "column": column.id,
        "id": card["id"],
        "updatedAt": card["updatedAt"],
        "patch": {
            "body": f"Mock description for {card.get('title', 'card')} (UPLIFT_MOCK_AGENT=1).",
            "evidence": [snippet],
            "confidence": "medium",
        },
    }
    return "## Action\n\n```json\n" + json.dumps(body, indent=2) + "\n```\n"


def _mock_response(
    *,
    column: SignalColumn,
    transcript: str,
    turn: int,
    snapshot: list[dict[str, Any]],
    added_this_run: bool,
) -> str:
    return _mock_title_response(
        column=column,
        transcript=transcript,
        turn=turn,
        added_this_run=added_this_run,
    )


def _emit_mutation(
    *,
    on_mutation: MutationFn | None,
    column: SignalColumn,
    verb: str,
    node: dict[str, Any],
) -> None:
    if not on_mutation:
        return
    on_mutation(
        {
            "column": column.id,
            "action": verb,
            "node": {
                "id": node.get("id"),
                "title": node.get("title"),
                "body": node.get("body"),
                "cardState": node.get("cardState"),
                "updatedAt": node.get("updatedAt"),
            },
        }
    )


def _read_latest_turn_text(col_dir: Path) -> str:
    for pattern in ("turns/*/response.full.md", "turns/*/response.raw.md", "turns/*/response.md"):
        paths = sorted(col_dir.glob(pattern))
        for p in reversed(paths):
            text = p.read_text(encoding="utf-8").strip()
            if text:
                return text
    return ""


def _resolve_agent_text(*, col_dir: Path, event_text: str) -> str:
    text = (event_text or "").strip()
    if text and parse_action_blocks(text):
        return text
    disk = _read_latest_turn_text(col_dir)
    if disk and parse_action_blocks(disk):
        return disk
    return text or disk


def _run_agent_turn(
    *,
    agent: HeadlessAgent | SdkAgent,
    prompt: str,
    artifact_dir: Path,
    on_progress: ProgressFn | None,
) -> str:
    events: list[dict] = []
    response_holder: list[str] = []

    def on_event(payload: dict) -> None:
        events.append(payload)
        if payload.get("type") == "turn_complete" and payload.get("response"):
            response_holder.append(str(payload["response"]))

    agent.on_event(on_event)
    agent.send(prompt, on_progress=on_progress)

    failed = next(
        (e for e in reversed(events) if e.get("type") in ("turn_failed", "exit", "turn_timeout")),
        None,
    )
    complete = next((e for e in reversed(events) if e.get("type") == "turn_complete"), None)
    if failed and not complete:
        raise RuntimeError(failed.get("message") or "column agent failed")

    event_text = response_holder[-1] if response_holder else ""
    return _resolve_agent_text(col_dir=artifact_dir, event_text=event_text)


def run_column_titles(
    *,
    session_id: str,
    session_dir: Path,
    column: SignalColumn,
    transcript: str,
    store: StoreLike,
    run_id: str,
    agent: HeadlessAgent | SdkAgent | None = None,
    on_progress: ProgressFn | None = None,
    on_mutation: MutationFn | None = None,
    on_title_added: TitleAddedFn | None = None,
) -> ColumnRunResult:
    def prog(msg: str) -> None:
        if on_progress:
            on_progress(f"[{column.title} · title] {msg}")

    col_dir = _signals_col_dir(session_dir, column)
    col_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    run_memory: list[dict[str, Any]] = []
    errors: list[str] = []
    summary = ""
    status = "done"
    all_stdout: list[str] = []

    snapshot = store.column_snapshot(column.id)
    artifact_dir = title_agent_dir(session_dir, run_id)
    saved_handlers: list | None = None
    if agent is not None and not _mock_mode():
        saved_handlers = list(agent._event_handlers)  # type: ignore[attr-defined]
        agent._event_handlers.clear()  # type: ignore[attr-defined]

    try:
        prompt = title_column_prompt(column=column, transcript=transcript, snapshot=snapshot)
        mock_turn = 0

        for turn in range(1, MAX_AGENT_TURNS + 1):
            if is_cancelled(session_id, column.id):
                status = "cancelled"
                summary = summary or "cancelled"
                prog("cancelled")
                if agent is not None:
                    agent.interrupt()
                break

            prog(f"agent turn {turn}…")

            if _mock_mode():
                mock_turn += 1
                text = _mock_title_response(
                    column=column,
                    transcript=transcript,
                    turn=mock_turn,
                    added_this_run=any(m.get("action") == "add_draft" for m in run_memory),
                )
                time.sleep(0.02)
            else:
                assert agent is not None
                text = _run_agent_turn(
                    agent=agent,
                    prompt=prompt,
                    artifact_dir=artifact_dir,
                    on_progress=on_progress,
                )

            all_stdout.append(text)
            actions = parse_action_blocks(text)
            if not actions:
                errors.append(f"turn {turn}: no ## Action block parsed")
                parse_failures = sum(1 for e in errors if "no ## Action block parsed" in e)
                if parse_failures >= MAX_PARSE_RETRIES:
                    status = "error"
                    prog(f"error · no valid ## Action after {parse_failures} tries")
                    break
                prog("needs valid ## Action JSON — retrying")
                prompt = repair_prompt(column=column)
                continue

            action = actions[-1]
            verb = str(action.get("action") or "").lower()

            if verb == "complete":
                summary = str(action.get("summary") or summary)
                prog(f"done · {summary or 'complete'}")
                break

            if verb != "add_draft":
                errors.append(f"turn {turn}: expected add_draft or complete, got {verb}")
                prompt = title_continuation_prompt(
                    column=column,
                    snapshot=snapshot,
                    run_memory=run_memory,
                )
                continue

            result: MutationResult = store.mutate(action, run_id=run_id)
            if result.ok and result.node:
                run_memory.append(
                    {
                        "action": verb,
                        "id": result.node.get("id"),
                        "title": result.node.get("title"),
                    }
                )
                _write_memory(col_dir, run_id=run_id, memory=run_memory)
                snapshot = store.column_snapshot(column.id)
                prog(f"title ok · {result.node.get('title', result.node.get('id'))}")
                _emit_mutation(
                    on_mutation=on_mutation,
                    column=column,
                    verb=verb,
                    node=result.node,
                )
                if on_title_added:
                    on_title_added({**result.node, "column": column.id})
            elif result.conflict:
                errors.append(f"{verb}: optimistic conflict — skipped")
                snapshot = store.column_snapshot(column.id)
            elif result.not_found:
                errors.append(f"{verb}: id not found — skipped")
            else:
                errors.append(f"{verb}: {result.error or 'rejected'}")

            if is_cancelled(session_id, column.id):
                status = "cancelled"
                if agent is not None:
                    agent.interrupt()
                break

            prompt = title_continuation_prompt(
                column=column,
                snapshot=snapshot,
                run_memory=run_memory,
            )

        if status != "cancelled":
            status = "error" if errors and not run_memory else "done"
    finally:
        if saved_handlers is not None and agent is not None:
            agent._event_handlers = saved_handlers  # type: ignore[attr-defined]

    raw_path = col_dir / "title-response.raw.md"
    raw_path.write_text("\n\n---\n\n".join(all_stdout), encoding="utf-8")
    _write_memory(col_dir, run_id=run_id, memory=run_memory)

    elapsed = round(time.monotonic() - started, 2)
    if status == "error":
        prog(f"error · {errors[-1] if errors else summary or 'column failed'}")

    return ColumnRunResult(
        column_id=column.id,
        status=status,
        summary=summary or f"{len(run_memory)} draft titles",
        mutations=run_memory,
        errors=errors,
        elapsed_s=elapsed,
        raw_path=str(raw_path),
    )


def fill_card_description(
    *,
    session_id: str,
    session_dir: Path,
    column: SignalColumn,
    transcript: str,
    store: StoreLike,
    run_id: str,
    card: dict[str, Any],
    agent: HeadlessAgent | SdkAgent | None = None,
    on_progress: ProgressFn | None = None,
    on_mutation: MutationFn | None = None,
    desc_turn: int = 0,
) -> bool:
    def prog(msg: str) -> None:
        if on_progress:
            on_progress(f"[{column.title} · desc] {msg}")

    col_dir = _signals_col_dir(session_dir, column)
    artifact_dir = description_agent_dir(session_dir, run_id)
    saved_handlers: list | None = None
    if agent is not None and not _mock_mode():
        saved_handlers = list(agent._event_handlers)  # type: ignore[attr-defined]
        agent._event_handlers.clear()  # type: ignore[attr-defined]

    snapshot = store.column_snapshot(column.id)
    card_row = next((c for c in snapshot if c.get("id") == card.get("id")), None)
    if not card_row:
        card_row = {
            "id": card.get("id"),
            "updatedAt": card.get("updatedAt"),
            "title": card.get("title"),
            "body": card.get("body") or "",
            "cardState": card.get("cardState") or "draft",
        }

    title = card_row.get("title") or card.get("title") or card.get("id")
    prog(f"filling · {title}")

    try:
        if desc_turn == 0:
            prompt = description_card_prompt(
                column=column,
                transcript=transcript,
                card=card_row,
                snapshot=snapshot,
            )
        else:
            prompt = description_continuation_prompt(
                column=column,
                card=card_row,
                snapshot=snapshot,
            )

        for attempt in range(1, MAX_PARSE_RETRIES + 1):
            if is_cancelled(session_id, column.id):
                prog("cancelled")
                if agent is not None:
                    agent.interrupt()
                return False

            if _mock_mode():
                text = _mock_description_response(column=column, card=card_row, transcript=transcript)
                time.sleep(0.02)
            else:
                assert agent is not None
                text = _run_agent_turn(
                    agent=agent,
                    prompt=prompt,
                    artifact_dir=artifact_dir,
                    on_progress=on_progress,
                )

            actions = parse_action_blocks(text)
            if not actions:
                prog("needs valid edit ## Action — retrying")
                prompt = description_repair_prompt(column=column, card=card_row)
                continue

            action = actions[-1]
            verb = str(action.get("action") or "").lower()
            if verb != "edit":
                prog(f"expected edit, got {verb} — retrying")
                prompt = description_repair_prompt(column=column, card=card_row)
                continue

            result = store.mutate(action, run_id=run_id)
            if result.ok and result.node:
                prog(f"desc ok · {result.node.get('title', result.node.get('id'))}")
                _emit_mutation(
                    on_mutation=on_mutation,
                    column=column,
                    verb=verb,
                    node=result.node,
                )
                desc_path = col_dir / "description-response.raw.md"
                prior = desc_path.read_text(encoding="utf-8") if desc_path.is_file() else ""
                desc_path.write_text(
                    (prior + "\n\n---\n\n" + text).strip(),
                    encoding="utf-8",
                )
                return True

            prog(f"edit rejected: {result.error or 'unknown'} — retrying")
            snapshot = store.column_snapshot(column.id)
            card_row = next((c for c in snapshot if c.get("id") == card.get("id")), card_row)
            prompt = description_repair_prompt(column=column, card=card_row)

        prog("error · could not fill description")
        return False
    finally:
        if saved_handlers is not None and agent is not None:
            agent._event_handlers = saved_handlers  # type: ignore[attr-defined]


def run_column(
    *,
    session_id: str,
    session_dir: Path,
    column: SignalColumn,
    transcript: str,
    store: StoreLike,
    run_id: str,
    agent: HeadlessAgent | SdkAgent | None = None,
    on_progress: ProgressFn | None = None,
) -> ColumnRunResult:
    def prog(msg: str) -> None:
        if on_progress:
            on_progress(f"[{column.title}] {msg}")

    col_dir = _signals_col_dir(session_dir, column)
    col_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    run_memory: list[dict[str, Any]] = []
    errors: list[str] = []
    summary = ""
    status = "done"
    all_stdout: list[str] = []

    snapshot = store.column_snapshot(column.id)
    own_agent = agent is None
    artifact_dir = col_dir if own_agent else extract_agent_dir(session_dir, run_id)
    saved_handlers: list | None = None
    if not own_agent and agent is not None and not _mock_mode():
        saved_handlers = list(agent._event_handlers)  # type: ignore[attr-defined]
        agent._event_handlers.clear()  # type: ignore[attr-defined]

    try:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            if attempt > 1:
                wait = BACKOFF_S[min(attempt - 2, len(BACKOFF_S) - 1)]
                prog(f"retry attempt {attempt} in {wait}s…")
                time.sleep(wait)

            local_agent: HeadlessAgent | SdkAgent | None = agent
            try:
                prompt = column_prompt(column=column, transcript=transcript, snapshot=snapshot)
                mock_turn = 0

                if not _mock_mode() and own_agent:
                    local_agent = _make_signal_agent(col_dir=col_dir)
                    local_agent.start()

                for turn in range(1, MAX_AGENT_TURNS + 1):
                    if is_cancelled(session_id, column.id):
                        status = "cancelled"
                        summary = summary or "cancelled"
                        prog("cancelled")
                        if local_agent is not None:
                            local_agent.interrupt()
                        break

                    prog(f"agent turn {turn}…")

                    if _mock_mode():
                        mock_turn += 1
                        text = _mock_response(
                            column=column,
                            transcript=transcript,
                            turn=mock_turn,
                            snapshot=snapshot,
                            added_this_run=any(m.get("action") == "add" for m in run_memory),
                        )
                        time.sleep(0.02)
                    else:
                        assert local_agent is not None
                        text = _run_agent_turn(
                            agent=local_agent,
                            prompt=prompt,
                            artifact_dir=artifact_dir,
                            on_progress=on_progress,
                        )

                    all_stdout.append(text)
                    actions = parse_action_blocks(text)
                    if not actions:
                        errors.append(f"turn {turn}: no ## Action block parsed")
                        parse_failures = sum(1 for e in errors if "no ## Action block parsed" in e)
                        if parse_failures >= MAX_PARSE_RETRIES:
                            status = "error"
                            prog(f"error · no valid ## Action after {parse_failures} tries")
                            break
                        prog("needs valid ## Action JSON — retrying")
                        prompt = repair_prompt(column=column)
                        continue

                    action = actions[-1]
                    verb = str(action.get("action") or "").lower()

                    if verb == "complete":
                        summary = str(action.get("summary") or summary)
                        prog(f"done · {summary or 'complete'}")
                        break

                    result: MutationResult = store.mutate(action, run_id=run_id)
                    if result.ok and result.node:
                        run_memory.append(
                            {
                                "action": verb,
                                "id": result.node.get("id"),
                                "title": result.node.get("title"),
                            }
                        )
                        _write_memory(col_dir, run_id=run_id, memory=run_memory)
                        snapshot = store.column_snapshot(column.id)
                        prog(f"{verb} ok · {result.node.get('title', result.node.get('id'))}")
                    elif result.conflict:
                        errors.append(f"{verb}: optimistic conflict — skipped")
                        snapshot = store.column_snapshot(column.id)
                    elif result.not_found:
                        errors.append(f"{verb}: id not found — skipped")
                    else:
                        errors.append(f"{verb}: {result.error or 'rejected'}")

                    if is_cancelled(session_id, column.id):
                        status = "cancelled"
                        if local_agent is not None:
                            local_agent.interrupt()
                        break

                    prompt = continuation_prompt(
                        column=column,
                        snapshot=snapshot,
                        run_memory=run_memory,
                    )

                if status != "cancelled":
                    status = "error" if errors and not run_memory else "done"
                if status == "cancelled":
                    break
                if status == "error" and not run_memory:
                    break
                break

            except Exception as exc:
                errors.append(str(exc))
                if attempt >= MAX_ATTEMPTS:
                    status = "error"
                    summary = str(exc)
            finally:
                if own_agent and local_agent is not None:
                    local_agent.stop()
    finally:
        if not own_agent and saved_handlers is not None and agent is not None:
            agent._event_handlers = saved_handlers  # type: ignore[attr-defined]

    raw_path = col_dir / "response.raw.md"
    raw_path.write_text("\n\n---\n\n".join(all_stdout), encoding="utf-8")
    _write_memory(col_dir, run_id=run_id, memory=run_memory)

    elapsed = round(time.monotonic() - started, 2)
    if status == "error":
        prog(f"error · {errors[-1] if errors else summary or 'column failed'}")

    return ColumnRunResult(
        column_id=column.id,
        status=status,
        summary=summary or f"{len(run_memory)} mutations",
        mutations=run_memory,
        errors=errors,
        elapsed_s=elapsed,
        raw_path=str(raw_path),
    )
