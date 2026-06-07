"""Minimal SSE parser for uplift / ReqOps stream endpoints."""

from __future__ import annotations

import json
from typing import Any

import httpx


def read_sse_events(
    client: httpx.Client,
    *,
    method: str,
    url: str,
    json_body: dict[str, Any] | None = None,
    timeout: float = 120.0,
    max_events: int = 200,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with client.stream(
        method,
        url,
        json=json_body,
        headers={"Accept": "text/event-stream"},
        timeout=timeout,
    ) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line or not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if not payload:
                continue
            try:
                events.append(json.loads(payload))
            except json.JSONDecodeError:
                continue
            if len(events) >= max_events:
                break
            if events[-1].get("type") in ("result", "error"):
                break
    return events
