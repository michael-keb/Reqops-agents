"""Bridge hooks for signals-v01 agent pack."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
_PKG = _ROOT / "signals-v01"
if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))

from signals_v01.cancel_registry import cancel as cancel_signals  # noqa: E402
from signals_v01.extract import extract_signals  # noqa: E402
from signals_v01.store import SignalStore  # noqa: E402


def load_store(session_dir: Path) -> SignalStore:
    store = SignalStore(session_dir=session_dir)
    store.load()
    return store


def list_store_nodes(session_dir: Path) -> list[dict[str, Any]]:
    store = load_store(session_dir)
    return store.list_active_nodes()


def apply_mutation(session_dir: Path, action: dict[str, Any], *, run_id: str) -> dict[str, Any]:
    store = load_store(session_dir)
    result = store.mutate(action, run_id=run_id)
    return {
        "ok": result.ok,
        "action": result.action,
        "error": result.error,
        "conflict": result.conflict,
        "not_found": result.not_found,
        "node": result.node,
    }
