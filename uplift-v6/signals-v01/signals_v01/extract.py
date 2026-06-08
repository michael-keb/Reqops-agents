"""Staggered signals-v01 extract — title agent then description agent per card."""

from __future__ import annotations

import json
import os
import queue
import sys
import threading
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .cancel_registry import clear_run, is_cancelled, register_run
from .column_runner import (
    ColumnRunResult,
    fill_card_description,
    make_description_agent,
    make_title_agent,
    run_column_titles,
)
from .columns import COLUMN_BY_ID, SIGNAL_COLUMNS, SignalColumn
from .remote_store import RemoteSignalStore
from .store import SignalStore
from .transcript import build_transcript

Store = SignalStore | RemoteSignalStore

UPLIFT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(UPLIFT_ROOT) not in sys.path:
    sys.path.insert(0, str(UPLIFT_ROOT))

from bridge import session as sess  # noqa: E402
from bridge import trace  # noqa: E402

ProgressFn = Callable[[str], None]
MutationFn = Callable[[dict[str, Any]], None]


def _mock_mode() -> bool:
    return os.environ.get("UPLIFT_MOCK_AGENT", "").strip() in ("1", "true", "yes")


def _new_run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"extract-{ts}"


def _make_store(
    session_dir: Path,
    *,
    mutate_url: str | None = None,
    snapshot_url: str | None = None,
    mutate_token: str | None = None,
    run_id: str,
) -> Store:
    if mutate_url and snapshot_url:
        return RemoteSignalStore(
            mutate_url=mutate_url,
            snapshot_url=snapshot_url,
            mutate_token=mutate_token,
            run_id=run_id,
        )
    store = SignalStore(session_dir=session_dir)
    store.load()
    return store


def extract_signals(
    session_id: str,
    *,
    column_ids: list[str] | None = None,
    run_id: str | None = None,
    on_progress: ProgressFn | None = None,
    on_mutation: MutationFn | None = None,
    mutate_url: str | None = None,
    snapshot_url: str | None = None,
    mutate_token: str | None = None,
) -> dict[str, Any]:
    path = sess.session_path(session_id)
    if not path.is_dir():
        raise ValueError(f"session not found: {session_id}")

    trace.set_session_dir(path)
    transcript = build_transcript(path, reflection_only=True)
    if not transcript.strip():
        raise ValueError("session has no conversation to extract")

    selected: list[SignalColumn] = list(SIGNAL_COLUMNS)
    if column_ids:
        wanted = {c.strip() for c in column_ids if c.strip()}
        selected = [c for c in SIGNAL_COLUMNS if c.id in wanted]
        if not selected:
            raise ValueError(f"no matching columns: {column_ids}")

    run_id = run_id or _new_run_id()
    register_run(session_id)

    store = _make_store(
        path,
        mutate_url=mutate_url,
        snapshot_url=snapshot_url,
        mutate_token=mutate_token,
        run_id=run_id,
    )

    extract_dir = path / "signals-v01" / run_id
    extract_dir.mkdir(parents=True, exist_ok=True)

    if on_progress:
        on_progress(
            f"signals-v01 · {len(selected)} columns · staggered titles→descriptions · run {run_id}"
        )

    started = time.monotonic()
    results: dict[str, ColumnRunResult] = {}
    errors: dict[str, str] = {}
    desc_errors: list[str] = []
    desc_turn = 0

    title_agent = None
    desc_agent = None
    desc_queue: queue.Queue[dict[str, Any] | None] = queue.Queue()

    def description_worker() -> None:
        nonlocal desc_turn
        while True:
            item = desc_queue.get()
            try:
                if item is None:
                    break
                column = COLUMN_BY_ID.get(str(item.get("column") or ""))
                if not column:
                    desc_errors.append(f"unknown column for card {item.get('id')}")
                    continue
                turn = desc_turn
                ok = fill_card_description(
                    session_id=session_id,
                    session_dir=path,
                    column=column,
                    transcript=transcript,
                    store=store,
                    run_id=run_id,
                    card=item,
                    agent=desc_agent,
                    on_progress=on_progress,
                    on_mutation=on_mutation,
                    desc_turn=turn,
                )
                if ok:
                    desc_turn += 1
                if not ok:
                    desc_errors.append(
                        f"description failed for {item.get('title') or item.get('id')}"
                    )
            except Exception as exc:
                trace.error("description worker failed", exc)
                desc_errors.append(str(exc))
            finally:
                desc_queue.task_done()

    desc_thread = threading.Thread(target=description_worker, name="signal-desc-worker", daemon=True)
    desc_thread.start()

    if not _mock_mode():
        runner = os.environ.get("UPLIFT_SIGNALS_RUNNER", "sdk").strip().lower()
        title_agent = make_title_agent(session_dir=path, run_id=run_id)
        desc_agent = make_description_agent(session_dir=path, run_id=run_id)
        trace.info("lifecycle", f"signals extract runner: {runner}", run_id=run_id)
        title_agent.start()
        desc_agent.start()
        if on_progress:
            on_progress(
                f"agent ready ({runner}) — staggered titles→descriptions (2 persistent sessions)"
            )
    elif on_progress:
        on_progress("mock mode — staggered title/description pipeline")

    def enqueue_title(node: dict[str, Any]) -> None:
        title = node.get("title") or node.get("id")
        if on_progress:
            on_progress(f"title landed · {title} → description queued")
        desc_queue.put(dict(node))

    try:
        for index, col in enumerate(selected, start=1):
            if is_cancelled(session_id, col.id):
                errors[col.id] = "cancelled"
                if title_agent is not None:
                    title_agent.interrupt()
                if desc_agent is not None:
                    desc_agent.interrupt()
                break

            if on_progress:
                on_progress(f"column {index}/{len(selected)} · {col.title} · titles")

            try:
                results[col.id] = run_column_titles(
                    session_id=session_id,
                    session_dir=path,
                    column=col,
                    transcript=transcript,
                    store=store,
                    run_id=run_id,
                    agent=title_agent,
                    on_progress=on_progress,
                    on_mutation=on_mutation,
                    on_title_added=enqueue_title,
                )
            except Exception as exc:
                trace.error(f"signals column {col.id} failed", exc)
                errors[col.id] = str(exc)

            if results.get(col.id) and results[col.id].status == "cancelled":
                break

        if on_progress:
            on_progress("waiting for descriptions to finish…")
        desc_queue.join()
    finally:
        desc_queue.put(None)
        if desc_thread is not None:
            desc_thread.join(timeout=5.0)
        if title_agent is not None:
            title_agent.stop()
        if desc_agent is not None:
            desc_agent.stop()
        clear_run(session_id)

    elapsed = round(time.monotonic() - started, 2)

    columns_out = [
        {
            "id": col.id,
            "status": results[col.id].status if col.id in results else "error",
            "summary": results[col.id].summary if col.id in results else "",
            "mutations": results[col.id].mutations if col.id in results else [],
            "errors": results[col.id].errors if col.id in results else [errors.get(col.id, "")],
            "elapsed_s": results[col.id].elapsed_s if col.id in results else None,
            "mutation_count": len(results[col.id].mutations) if col.id in results else 0,
        }
        for col in selected
    ]

    mutations_total = sum(c.get("mutation_count", 0) for c in columns_out)
    columns_failed = sum(
        1
        for c in columns_out
        if c["status"] == "error"
        or (c.get("errors") and c["status"] != "cancelled" and c.get("mutation_count", 0) == 0)
    )

    manifest = {
        "session_id": session_id,
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_s": elapsed,
        "mode": "staggered_title_description",
        "summary": {
            "columns_total": len(columns_out),
            "columns_ok": len(columns_out) - columns_failed,
            "columns_failed": columns_failed,
            "mutations_total": mutations_total,
        },
        "columns": columns_out,
        "errors": errors,
        "description_errors": desc_errors,
    }
    (extract_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if isinstance(store, SignalStore):
        store.save()

    store_path = str(store.store_path) if isinstance(store, SignalStore) else None

    return {
        "session_id": session_id,
        "run_id": run_id,
        "manifest_path": str(extract_dir / "manifest.json"),
        "store_path": store_path,
        "elapsed_s": elapsed,
        "summary": manifest["summary"],
        "columns": columns_out,
        "errors": errors,
        "description_errors": desc_errors,
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m signals_v01.extract SESSION_ID [column_id ...]")
        raise SystemExit(2)

    sig_pkg = Path(__file__).resolve().parent.parent
    if str(sig_pkg) not in sys.path:
        sys.path.insert(0, str(sig_pkg))

    session_id = sys.argv[1]
    column_ids = sys.argv[2:] or None

    def prog(msg: str) -> None:
        print(msg, flush=True)

    result = extract_signals(session_id, column_ids=column_ids, on_progress=prog)
    print(f"Run {result['run_id']} · {result['elapsed_s']}s · store {result['store_path']}")
    if result["errors"]:
        print("Errors:", result["errors"], file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
