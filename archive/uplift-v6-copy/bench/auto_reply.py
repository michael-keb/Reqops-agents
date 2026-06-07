#!/usr/bin/env python3
"""Auto-reply harness for timed Uplift benchmarks.

Drives the bridge WebSocket with scripted replies so human think-time gaps
do not pollute turn-duration metrics.

Usage:
  ./serve   # in another terminal
  python bench/auto_reply.py --pitch "dog walking app" \\
    --replies "A) busy owners" "B) elderly owners"

  python bench/auto_reply.py --pitch "..." --replies-file replies.txt --json

Env: UPLIFT_PORT (default 8786)
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import aiohttp


@dataclass
class TurnRecord:
    turn: int
    elapsed_s: float
    idle: bool
    reply: str | None
    session_turn: int | None = None


@dataclass
class BenchResult:
    session_id: str | None = None
    turns: list[TurnRecord] = field(default_factory=list)
    bridge_pid: int | None = None
    t0: float = field(default_factory=time.monotonic)

    @property
    def compute_s(self) -> float:
        return sum(t.elapsed_s for t in self.turns)

    def to_dict(self) -> dict[str, Any]:
        wall = time.monotonic() - self.t0
        return {
            "session_id": self.session_id,
            "bridge_pid": self.bridge_pid,
            "turns": [
                {
                    "turn": t.turn,
                    "elapsed_s": t.elapsed_s,
                    "idle": t.idle,
                    "reply": t.reply,
                    "session_turn": t.session_turn,
                }
                for t in self.turns
            ],
            "total_compute_s": round(self.compute_s, 2),
            "total_wall_s": round(wall, 2),
            "gap_excluded_s": round(max(0, wall - self.compute_s), 2),
        }


def _base_url(host: str) -> str:
    if "://" not in host:
        host = f"http://{host}"
    return host.rstrip("/")


def _ws_url(http_base: str) -> str:
    p = urlparse(http_base)
    scheme = "wss" if p.scheme == "https" else "ws"
    port = p.port or (443 if scheme == "wss" else 80)
    netloc = p.hostname or "127.0.0.1"
    if (scheme == "ws" and port != 80) or (scheme == "wss" and port != 443):
        netloc = f"{netloc}:{port}"
    return f"{scheme}://{netloc}/ws"


async def _fetch_state(session: aiohttp.ClientSession, base: str) -> dict[str, Any]:
    async with session.get(f"{base}/api/state") as resp:
        resp.raise_for_status()
        return await resp.json()


async def _fetch_health(session: aiohttp.ClientSession, base: str) -> dict[str, Any]:
    async with session.get(f"{base}/api/health") as resp:
        resp.raise_for_status()
        return await resp.json()


async def _start_session(session: aiohttp.ClientSession, base: str, pitch: str) -> dict[str, Any]:
    async with session.post(f"{base}/api/start", json={"pitch": pitch}) as resp:
        body = await resp.json()
        if resp.status >= 400:
            raise RuntimeError(body.get("error") or resp.reason)
        return body


async def _new_session(session: aiohttp.ClientSession, base: str) -> None:
    async with session.post(f"{base}/api/new-session") as resp:
        resp.raise_for_status()


async def _ws_reader(ws: aiohttp.ClientWebSocketResponse, events: asyncio.Queue[dict]) -> None:
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            await events.put(json.loads(msg.data))
        elif msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
            await events.put({"type": "_ws_closed"})
            return


async def _wait_turn_complete(
    events: asyncio.Queue[dict],
    http: aiohttp.ClientSession,
    base: str,
    timeout_s: float,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        try:
            data = await asyncio.wait_for(events.get(), timeout=remaining)
        except asyncio.TimeoutError:
            break
        if data.get("type") == "_ws_closed":
            raise RuntimeError("WebSocket closed unexpectedly")
        if data.get("type") == "turn_timeout":
            raise TimeoutError("agent reported turn timeout")
        if data.get("type") == "error":
            raise RuntimeError(data.get("message") or "agent error")
        if data.get("type") == "turn_complete":
            return data
    raise TimeoutError(f"no turn_complete within {timeout_s}s")


async def run_bench(
    *,
    base: str,
    pitch: str | None,
    replies: list[str],
    delay_s: float,
    turn_timeout_s: float,
    continue_session: bool,
    reset_first: bool,
) -> BenchResult:
    result = BenchResult()
    ws_url = _ws_url(base)
    events: asyncio.Queue[dict] = asyncio.Queue()

    async with aiohttp.ClientSession() as http:
        health = await _fetch_health(http, base)
        result.bridge_pid = health.get("pid")

        if reset_first:
            await _new_session(http, base)

        async with http.ws_connect(ws_url) as ws:
            reader = asyncio.create_task(_ws_reader(ws, events))

            try:
                if continue_session:
                    state = await _fetch_state(http, base)
                    if not state.get("session_id"):
                        raise RuntimeError("No active session — omit --continue or pass --pitch")
                    result.session_id = state["session_id"]
                    queue = list(replies)
                else:
                    if not pitch:
                        raise RuntimeError("--pitch required unless --continue")
                    start_task = asyncio.create_task(_start_session(http, base, pitch))
                    data = await _wait_turn_complete(events, http, base, turn_timeout_s)
                    start_body = await start_task
                    result.session_id = start_body.get("session_id")
                    state = await _fetch_state(http, base)
                    result.turns.append(
                        TurnRecord(
                            turn=int(data.get("turn") or 1),
                            elapsed_s=float(data.get("elapsed_s") or 0),
                            idle=bool(data.get("idle")),
                            reply=None,
                            session_turn=state.get("turn"),
                        )
                    )
                    queue = list(replies)

                for reply in queue:
                    if delay_s > 0:
                        await asyncio.sleep(delay_s)
                    await ws.send_str(json.dumps({"type": "input", "text": reply}))
                    data = await _wait_turn_complete(events, http, base, turn_timeout_s)
                    state = await _fetch_state(http, base)
                    result.turns.append(
                        TurnRecord(
                            turn=int(data.get("turn") or len(result.turns) + 1),
                            elapsed_s=float(data.get("elapsed_s") or 0),
                            idle=bool(data.get("idle")),
                            reply=reply,
                            session_turn=state.get("turn"),
                        )
                    )
            finally:
                reader.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await reader

    return result


def _load_replies(path: str) -> list[str]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]


def main() -> int:
    import os

    parser = argparse.ArgumentParser(description="Uplift v6 auto-reply benchmark harness")
    parser.add_argument("--host", default=f"http://127.0.0.1:{os.environ.get('UPLIFT_PORT', '8786')}")
    parser.add_argument("--pitch", help="Product pitch (starts new session via /api/start)")
    parser.add_argument("--continue", dest="continue_session", action="store_true", help="Use existing active session")
    parser.add_argument("--new-session", action="store_true", help="POST /api/new-session before starting")
    parser.add_argument("--replies", nargs="*", default=[], help="Replies after bootstrap turn")
    parser.add_argument("--replies-file", help="One reply per line (after bootstrap)")
    parser.add_argument("--delay", type=float, default=0.0, help="Seconds between turn_complete and next send")
    parser.add_argument("--turn-timeout", type=float, default=120.0, help="Max seconds to wait per turn")
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    replies = list(args.replies)
    if args.replies_file:
        replies = _load_replies(args.replies_file)

    try:
        result = asyncio.run(
            run_bench(
                base=_base_url(args.host),
                pitch=args.pitch,
                replies=replies,
                delay_s=args.delay,
                turn_timeout_s=args.turn_timeout,
                continue_session=args.continue_session,
                reset_first=args.new_session,
            )
        )
    except Exception as exc:
        print(f"bench failed: {exc}", file=sys.stderr)
        return 1

    out = result.to_dict()
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print(f"session: {out['session_id']}")
        print(f"bridge pid: {out['bridge_pid']}")
        for t in out["turns"]:
            src = f"session turn {t['session_turn']}" if t.get("session_turn") else "?"
            label = t.get("reply") or "bootstrap"
            if label and len(label) > 50:
                label = label[:50] + "…"
            print(
                f"  turn {t['turn']} ({src}): {t['elapsed_s']}s"
                + (" idle" if t.get("idle") else "")
                + f"  ← {label}"
            )
        print(f"compute: {out['total_compute_s']}s  wall: {out['total_wall_s']}s  gaps excluded: {out['gap_excluded_s']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
