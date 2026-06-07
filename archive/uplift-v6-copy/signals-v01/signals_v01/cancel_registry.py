"""Per-session cancel flags for signal extract runs."""

from __future__ import annotations

import threading

_lock = threading.Lock()
_cancel_all: dict[str, threading.Event] = {}
_cancel_column: dict[tuple[str, str], threading.Event] = {}


def _session_key(session_id: str) -> str:
    return session_id.strip()


def register_run(session_id: str) -> None:
    key = _session_key(session_id)
    with _lock:
        _cancel_all.setdefault(key, threading.Event())
        _cancel_all[key].clear()


def cancel(session_id: str, *, column_id: str | None = None) -> None:
    key = _session_key(session_id)
    with _lock:
        if column_id:
            ev = _cancel_column.setdefault((key, column_id), threading.Event())
            ev.set()
        else:
            ev = _cancel_all.setdefault(key, threading.Event())
            ev.set()
            for (sid, _), col_ev in list(_cancel_column.items()):
                if sid == key:
                    col_ev.set()


def is_cancelled(session_id: str, column_id: str) -> bool:
    key = _session_key(session_id)
    with _lock:
        if _cancel_all.get(key) and _cancel_all[key].is_set():
            return True
        col_ev = _cancel_column.get((key, column_id))
        return bool(col_ev and col_ev.is_set())


def clear_run(session_id: str) -> None:
    key = _session_key(session_id)
    with _lock:
        _cancel_all.pop(key, None)
        for pair in [p for p in _cancel_column if p[0] == key]:
            _cancel_column.pop(pair, None)
