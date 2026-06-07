"""Parallel board extraction — one headless CLI agent per column."""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from . import session as sess
from . import trace
from .board_cards import (
    build_transcript,
    column_prompt,
    load_board,
    mock_column_payload,
    persist_column_run,
    save_board,
)
from .board_columns import BOARD_COLUMNS, BoardColumn
from .headless_agent import HeadlessAgent
from .mock_agent import MockAgent

ROOT = Path(__file__).resolve().parent.parent
MOCK = os.environ.get("UPLIFT_MOCK_AGENT", "").strip() in ("1", "true", "yes")
MAX_WORKERS = int(os.environ.get("UPLIFT_BOARD_WORKERS", "9"))

ProgressFn = Callable[[str], None]


def _make_column_agent(column_dir: Path) -> HeadlessAgent | MockAgent:
    env = {"UPLIFT_SESSION": str(column_dir)}
    if MOCK:
        return MockAgent(cwd=ROOT, env_extra=env)
    return HeadlessAgent(cwd=ROOT, env_extra=env)


def _run_column_agent(
    *,
    session_dir: Path,
    column: BoardColumn,
    transcript: str,
    on_progress: ProgressFn | None = None,
) -> dict[str, Any]:
    def prog(msg: str) -> None:
        if on_progress:
            on_progress(f"[{column.title}] {msg}")

    col_dir = session_dir / "board" / column.slug
    col_dir.mkdir(parents=True, exist_ok=True)
    prompt = column_prompt(column=column, transcript=transcript)

    if MOCK:
        time.sleep(0.05)
        payload = mock_column_payload(column=column, transcript=transcript)
        raw = f"## Reflection\n{payload['reflection']}\n\n## Cards\n\n```json\n"
        raw += __import__("json").dumps({"column": column.id, "cards": payload["cards"]}, indent=2)
        raw += "\n```\n"
        (col_dir / "response.raw.md").write_text(raw, encoding="utf-8")
        (col_dir / "column.json").write_text(
            __import__("json").dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        prog("done (mock)")
        return payload

    agent = _make_column_agent(col_dir)
    events: list[dict] = []
    started = time.monotonic()

    def on_event(payload: dict) -> None:
        events.append(payload)
        kind = payload.get("type")
        if kind == "turn_start":
            prog("running…")
        elif kind == "turn_complete":
            prog(f"done · {payload.get('elapsed_s', '?')}s")

    agent.on_event(on_event)
    prog("starting agent…")
    agent.start()
    agent.send(prompt, on_progress=prog)

    failed = next(
        (e for e in reversed(events) if e.get("type") in ("turn_failed", "exit", "turn_timeout")),
        None,
    )
    complete = next((e for e in reversed(events) if e.get("type") == "turn_complete"), None)
    if failed and not complete:
        raise RuntimeError(failed.get("message") or f"{column.title} agent failed")

    elapsed = time.monotonic() - started
    response_text = ""
    if complete and complete.get("response"):
        response_text = str(complete["response"])
    else:
        raw_path = col_dir / "turns" / "01" / "response.raw.md"
        if raw_path.is_file():
            response_text = raw_path.read_text(encoding="utf-8")
        elif (col_dir / "turns" / "01" / "response.md").is_file():
            response_text = (col_dir / "turns" / "01" / "response.md").read_text(encoding="utf-8")

    if not response_text.strip():
        raise RuntimeError(f"{column.title} agent returned empty response")

    return persist_column_run(session_dir, column=column, response_text=response_text, elapsed_s=round(elapsed, 2))


def extract_board(
    session_id: str,
    *,
    column_ids: list[str] | None = None,
    on_progress: ProgressFn | None = None,
) -> dict[str, Any]:
    """Run all column agents in parallel; persist board.json."""
    path = sess.session_path(session_id)
    if not path.is_dir():
        raise ValueError(f"session not found: {session_id}")

    trace.set_session_dir(path)
    transcript = build_transcript(path)
    if not transcript.strip():
        raise ValueError("session has no conversation to extract")

    selected = list(BOARD_COLUMNS)
    if column_ids:
        wanted = {c.strip() for c in column_ids if c.strip()}
        selected = [c for c in BOARD_COLUMNS if c.id in wanted]
        if not selected:
            raise ValueError(f"no matching columns: {column_ids}")

    if on_progress:
        on_progress(f"Extracting {len(selected)} columns in parallel…")

    started = time.monotonic()
    results: dict[str, dict[str, Any]] = {}
    errors: dict[str, str] = {}

    workers = min(MAX_WORKERS, len(selected))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(
                _run_column_agent,
                session_dir=path,
                column=col,
                transcript=transcript,
                on_progress=on_progress,
            ): col
            for col in selected
        }
        for fut in as_completed(futures):
            col = futures[fut]
            try:
                results[col.id] = fut.result()
            except Exception as exc:
                trace.error(f"board column {col.id} failed", exc)
                errors[col.id] = str(exc)

    ordered = [results[c.id] for c in selected if c.id in results]
    elapsed = round(time.monotonic() - started, 2)
    board_path = save_board(path, ordered, elapsed_s=elapsed)

    try:
        board_rel = str(board_path.relative_to(ROOT))
    except ValueError:
        board_rel = str(board_path)

    out: dict[str, Any] = {
        "session_id": session_id,
        "board_path": board_rel,
        "elapsed_s": elapsed,
        "columns": ordered,
        "errors": errors,
    }
    if on_progress:
        on_progress(f"Board saved · {len(ordered)} columns · {elapsed}s")
    return out


def main() -> None:
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m bridge.board_extract SESSION_ID [column_id ...]")
        raise SystemExit(2)

    session_id = sys.argv[1]
    column_ids = sys.argv[2:] or None

    def prog(msg: str) -> None:
        print(msg, flush=True)

    result = extract_board(session_id, column_ids=column_ids, on_progress=prog)
    print(f"Wrote {result['board_path']} ({len(result['columns'])} columns, {result['elapsed_s']}s)")
    if result["errors"]:
        print("Errors:", result["errors"], file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
