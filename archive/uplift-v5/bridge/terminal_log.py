"""In-memory terminal log + SSE subscribers for the UI."""

from __future__ import annotations

import queue
import threading
import time
from collections import deque
from typing import Any

MAX_LINES = 3000

_lines: deque[dict[str, Any]] = deque(maxlen=MAX_LINES)
_subscribers: list[queue.Queue[dict[str, Any]]] = []
_lock = threading.Lock()


def emit(line: str, *, kind: str = "sys") -> None:
    entry = {"t": time.time(), "line": line, "kind": kind}
    with _lock:
        _lines.append(entry)
        for sub in _subscribers:
            try:
                sub.put_nowait(entry)
            except queue.Full:
                pass


def history() -> list[dict[str, Any]]:
    with _lock:
        return list(_lines)


def clear() -> None:
    with _lock:
        _lines.clear()


def subscribe() -> queue.Queue[dict[str, Any]]:
    q: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=512)
    with _lock:
        _subscribers.append(q)
    return q


def unsubscribe(q: queue.Queue[dict[str, Any]]) -> None:
    with _lock:
        if q in _subscribers:
            _subscribers.remove(q)
