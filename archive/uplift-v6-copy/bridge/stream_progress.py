"""Map Cursor stream-json events to short ReqOps progress lines."""

from __future__ import annotations

import time

from .stream_parser import StreamEvent

_last_assistant_at = 0.0
_ASSISTANT_THROTTLE_S = 0.8


def progress_message_from_event(ev: StreamEvent) -> str | None:
    global _last_assistant_at
    kind = ev.kind
    if kind == "tool":
        return ev.msg.strip()
    if kind == "thinking" and ev.msg == "thinking done":
        return "Thinking…"
    if kind == "assistant":
        text = (ev.data.get("text") or ev.msg or "").strip()
        if not text:
            return None
        if ev.data.get("partial"):
            now = time.monotonic()
            if now - _last_assistant_at < _ASSISTANT_THROTTLE_S:
                return None
            _last_assistant_at = now
            one_line = " ".join(text.split())[:100]
            return f"Drafting… {one_line}" if one_line else "Drafting response…"
        return "Drafting response…"
    if kind == "result":
        return None
    if kind == "agent" and ev.data.get("parse_error"):
        return "Agent output…"
    return None
