"""aiohttp: static UI + WebSocket bridge to persistent PTY agent."""

from __future__ import annotations

import asyncio
import json
import os
import queue
import sys
import threading
import traceback
from pathlib import Path

from aiohttp import web

from . import session as sess
from . import trace
from .discovery_format import bootstrap_message, wrap_discovery_message
from .headless_agent import HeadlessAgent
from .mock_agent import MockAgent
from .pty_agent import ROOT, PtyAgent
from . import board_cards
from . import board_extract
from . import signals_v01_api
from . import sync_turn

UI_DIR = ROOT / "ui"
PORT = int(os.environ.get("UPLIFT_PORT", "8786"))
MOCK = os.environ.get("UPLIFT_MOCK_AGENT", "").strip() in ("1", "true", "yes")
AGENT_MODE = os.environ.get("UPLIFT_AGENT_MODE", "pty").strip().lower()

_agent: HeadlessAgent | PtyAgent | MockAgent | None = None
_loop: asyncio.AbstractEventLoop | None = None
_ws_clients: set[web.WebSocketResponse] = set()
_broadcast_queue: asyncio.Queue[tuple[str, bytes | str]] | None = None
_broadcast_task: asyncio.Task[None] | None = None


@web.middleware
async def trace_middleware(request: web.Request, handler):
    if request.path.startswith("/api/") and request.path != "/api/trace/stream":
        trace.http(request.method, request.path)
    try:
        response = await handler(request)
        if request.path.startswith("/api/") and request.path != "/api/trace/stream":
            trace.http(request.method, request.path, status=response.status)
        return response
    except web.HTTPException as exc:
        trace.http(request.method, request.path, status=exc.status, detail=str(exc.reason))
        raise
    except Exception as exc:
        trace.error(f"{request.method} {request.path} failed", exc)
        trace.http(request.method, request.path, status=500, detail=type(exc).__name__)
        return web.json_response({"error": str(exc), "trace": traceback.format_exc()}, status=500)


def _agent_env() -> dict[str, str]:
    env: dict[str, str] = {}
    active = sess.active_session()
    if active:
        env["UPLIFT_SESSION"] = str(active)
    return env


def _get_agent() -> HeadlessAgent | PtyAgent | MockAgent:
    global _agent
    if _agent is None:
        env = _agent_env()
        if MOCK:
            _agent = MockAgent(cwd=ROOT, env_extra=env)
        elif AGENT_MODE == "pty":
            _agent = PtyAgent(cwd=ROOT, env_extra=env)
        else:
            _agent = HeadlessAgent(cwd=ROOT, env_extra=env)
        _agent.on_chunk(_broadcast_bytes)
        _agent.on_event(_broadcast_event)
    else:
        _agent.env_extra = _agent_env()
    return _agent


def _warm_pty_agent() -> None:
    """Start one long-lived interactive agent early (PTY mode only)."""
    if MOCK or AGENT_MODE != "pty":
        return
    try:
        agent = _get_agent()
        if not agent.alive:
            agent.start()
            trace.info("sys", "PTY agent warm-started", pid=agent.pid)
    except Exception as exc:
        trace.warn("sys", "PTY warm start failed", detail=str(exc))


async def _broadcast_worker() -> None:
    """Single task drains PTY/agent output — avoids thousands of create_task per chunk."""
    assert _broadcast_queue is not None
    while True:
        kind, payload = await _broadcast_queue.get()
        batch_bytes: list[bytes] = []
        batch_text: list[str] = []
        if kind == "bytes" and isinstance(payload, bytes):
            batch_bytes.append(payload)
        elif kind == "text" and isinstance(payload, str):
            batch_text.append(payload)
        while _broadcast_queue.qsize() > 0 and len(batch_bytes) + len(batch_text) < 48:
            try:
                k2, p2 = _broadcast_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            if k2 == "bytes" and isinstance(p2, bytes):
                batch_bytes.append(p2)
            elif k2 == "text" and isinstance(p2, str):
                batch_text.append(p2)
        dead: list[web.WebSocketResponse] = []
        for ws in list(_ws_clients):
            try:
                if batch_bytes:
                    await ws.send_bytes(b"".join(batch_bytes))
                for msg in batch_text:
                    await ws.send_str(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            _ws_clients.discard(ws)


def _enqueue_broadcast(kind: str, payload: bytes | str) -> None:
    if _loop is None or _broadcast_queue is None:
        return

    def _put() -> None:
        assert _broadcast_queue is not None
        try:
            _broadcast_queue.put_nowait((kind, payload))
        except asyncio.QueueFull:
            pass

    _loop.call_soon_threadsafe(_put)


def _broadcast_bytes(data: bytes) -> None:
    if data:
        _enqueue_broadcast("bytes", data)


def _broadcast_event(payload: dict) -> None:
    _enqueue_broadcast("text", json.dumps(payload))


async def websocket_handler(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse(heartbeat=30.0)
    await ws.prepare(request)
    _ws_clients.add(ws)
    trace.ws("in", "connect")
    agent = _get_agent()
    if hasattr(agent, "history_blob"):
        blob = await asyncio.to_thread(agent.history_blob)
        if blob:
            try:
                await ws.send_bytes(blob)
            except Exception as exc:
                trace.warn("ws", "history replay failed", detail=str(exc))
    await ws.send_str(json.dumps({"type": "connected", "pid": agent.pid, "alive": agent.alive}))
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except json.JSONDecodeError as exc:
                    trace.error("invalid WS JSON", exc, raw=msg.data[:200])
                    continue
                trace.ws("in", data.get("type", "?"), detail=str(data)[:120])
                await _handle_ws_message(data)
            elif msg.type in (web.WSMsgType.ERROR, web.WSMsgType.CLOSE):
                break
    finally:
        _ws_clients.discard(ws)
        trace.ws("in", "disconnect")
    return ws


async def _handle_ws_message(data: dict) -> None:
    kind = data.get("type")
    if kind == "input":
        text = (data.get("text") or "").strip()
        if not text:
            return
        agent = _get_agent()
        await asyncio.to_thread(agent.send, wrap_discovery_message(text))
    elif kind == "interrupt":
        agent = _get_agent()
        await asyncio.to_thread(agent.interrupt)
    elif kind == "restart":
        agent = _get_agent()
        await asyncio.to_thread(_restart_agent, agent)


def _shutdown_agent(*, clear_buffers: bool = True) -> None:
    global _agent
    if not _agent:
        return
    if _agent.pid or getattr(_agent, "_waiting_turn", False):
        _agent.interrupt()
    _agent.stop()
    if clear_buffers and hasattr(_agent, "clear_buffers"):
        _agent.clear_buffers()
    _agent = None


def _restart_agent(agent: HeadlessAgent | PtyAgent) -> None:
    trace.info("lifecycle", "restart requested")
    agent.stop()
    global _agent
    _agent = None
    a = _get_agent()
    a.start()


async def api_health(_request: web.Request) -> web.Response:
    agent = _get_agent() if _agent else None
    return web.json_response(
        {
            "ok": True,
            "port": PORT,
            "mock": MOCK,
            "agent_alive": bool(agent and agent.alive),
            "pid": agent.pid if agent else None,
            "mode": AGENT_MODE,
            "discovery_runner": os.environ.get("UPLIFT_DISCOVERY_RUNNER", "sdk").strip().lower(),
            "signals_runner": os.environ.get("UPLIFT_SIGNALS_RUNNER", "sdk").strip().lower(),
            "agent_sdk_url": os.environ.get("UPLIFT_AGENT_SDK_URL", "http://127.0.0.1:7778").rstrip("/"),
            "trace": trace.paths(),
            **sess.session_state(),
        }
    )


async def api_start(request: web.Request) -> web.Response:
    body = await request.json()
    pitch = (body.get("pitch") or "").strip()
    if not pitch:
        return web.json_response({"error": "pitch required"}, status=400)
    session_id = (body.get("session_id") or body.get("sessionId") or "").strip() or None
    bootstrap = body.get("bootstrap", True)
    if session_id and AGENT_MODE == "headless":
        try:
            result = await asyncio.to_thread(
                sync_turn.start_session,
                pitch,
                session_id=session_id,
                bootstrap=bool(bootstrap),
            )
            trace.info("session", "started (headless api)", session_id=result["session_id"], pitch=pitch)
            return web.json_response({**result, "trace": trace.paths()})
        except ValueError as exc:
            return web.json_response({"error": str(exc)}, status=400)
        except Exception as exc:
            trace.error("session start failed", exc, session_id=session_id)
            return web.json_response({"error": str(exc), "trace": trace.paths()}, status=500)

    try:
        path = sess.create_session(pitch, session_id=session_id)
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    trace.set_session_dir(path)
    trace.info("session", "created", session_id=path.name, pitch=pitch)
    agent = _get_agent()
    try:
        if agent.alive:
            trace.info(
                "lifecycle",
                "reusing live agent",
                pid=agent.pid,
                mode=AGENT_MODE,
                session_id=path.name,
            )
        else:
            await asyncio.to_thread(agent.start)
    except Exception as exc:
        trace.error("session start failed", exc, session_id=path.name)
        return web.json_response({"error": str(exc), "trace": trace.paths()}, status=500)
    if bootstrap:
        await asyncio.to_thread(agent.send, bootstrap_message(pitch=pitch, session_dir=str(path)))
    return web.json_response(
        {
            "session_id": path.name,
            "created": True,
            "trace": trace.paths(),
            **sess.session_state_for(path.name),
        }
    )


async def api_session_state(request: web.Request) -> web.Response:
    sid = request.match_info.get("session_id", "")
    return web.json_response(sess.session_state_for(sid))


async def api_session_delete(request: web.Request) -> web.Response:
    sid = request.match_info.get("session_id", "")
    try:
        ok = await asyncio.to_thread(sess.delete_session, sid)
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response({"ok": ok, "session_id": sid})


async def api_session_turn(request: web.Request) -> web.Response:
    sid = request.match_info.get("session_id", "")
    body = await request.json()
    text = (body.get("text") or "").strip()
    if not text:
        return web.json_response({"error": "text required"}, status=400)
    if not sess.session_exists(sid):
        return web.json_response({"error": f"session not found: {sid}"}, status=404)
    try:
        result = await asyncio.to_thread(sync_turn.run_turn, sid, text)
        return web.json_response(result)
    except Exception as exc:
        trace.error("turn failed", exc, session_id=sid)
        return web.json_response({"error": str(exc)}, status=502)


async def api_session_turn_stream(request: web.Request) -> web.Response:
    sid = request.match_info.get("session_id", "")
    body = await request.json()
    text = (body.get("text") or "").strip()
    if not text:
        return web.json_response({"error": "text required"}, status=400)
    if not sess.session_exists(sid):
        return web.json_response({"error": f"session not found: {sid}"}, status=404)

    resp = web.StreamResponse(
        status=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
    await resp.prepare(request)
    loop = asyncio.get_running_loop()
    q: asyncio.Queue[dict] = asyncio.Queue()

    def on_progress(msg: str) -> None:
        loop.call_soon_threadsafe(q.put_nowait, {"type": "progress", "message": msg})

    async def write_sse(item: dict) -> None:
        await resp.write(f"data: {json.dumps(item, ensure_ascii=False)}\n\n".encode())
        # Flush so ReqOps/Vite proxy delivers progress before the turn completes.
        if hasattr(resp, "flush"):
            await resp.flush()

    async def worker() -> None:
        try:
            result = await asyncio.to_thread(sync_turn.run_turn, sid, text, on_progress=on_progress)
            await q.put({"type": "result", **result})
        except Exception as exc:
            await q.put({"type": "error", "message": str(exc)})

    worker_task = asyncio.create_task(worker())

    try:
        while True:
            item = await q.get()
            await write_sse(item)
            if item.get("type") in ("result", "error"):
                break
    except (asyncio.CancelledError, ConnectionResetError, BrokenPipeError):
        worker_task.cancel()
    finally:
        if not worker_task.done():
            worker_task.cancel()
    return resp


async def api_session_board(request: web.Request) -> web.Response:
    sid = request.match_info.get("session_id", "")
    if not sess.session_exists(sid):
        return web.json_response({"error": "session not found"}, status=404)
    path = sess.session_path(sid)
    board = board_cards.load_board(path)
    if not board:
        return web.json_response({"error": "board not found"}, status=404)
    return web.json_response({"session_id": sid, **board})


async def api_session_board_extract(request: web.Request) -> web.Response:
    sid = request.match_info.get("session_id", "")
    if not sess.session_exists(sid):
        return web.json_response({"error": f"session not found: {sid}"}, status=404)
    body: dict = {}
    if request.content_length:
        try:
            parsed = await request.json()
            if isinstance(parsed, dict):
                body = parsed
        except json.JSONDecodeError:
            return web.json_response({"error": "invalid JSON body"}, status=400)
    column_ids = body.get("columns")
    if column_ids is not None and not isinstance(column_ids, list):
        return web.json_response({"error": "columns must be a list of column ids"}, status=400)
    try:
        result = await asyncio.to_thread(board_extract.extract_board, sid, column_ids=column_ids)
        return web.json_response(result)
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    except Exception as exc:
        trace.error("board extract failed", exc, session_id=sid)
        return web.json_response({"error": str(exc)}, status=502)


async def api_session_board_extract_stream(request: web.Request) -> web.Response:
    sid = request.match_info.get("session_id", "")
    if not sess.session_exists(sid):
        return web.json_response({"error": f"session not found: {sid}"}, status=404)
    body: dict = {}
    if request.content_length:
        try:
            parsed = await request.json()
            if isinstance(parsed, dict):
                body = parsed
        except json.JSONDecodeError:
            return web.json_response({"error": "invalid JSON body"}, status=400)
    column_ids = body.get("columns")
    if column_ids is not None and not isinstance(column_ids, list):
        return web.json_response({"error": "columns must be a list of column ids"}, status=400)

    resp = web.StreamResponse(
        status=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
    await resp.prepare(request)
    loop = asyncio.get_running_loop()
    q: asyncio.Queue[dict] = asyncio.Queue()

    def on_progress(msg: str) -> None:
        loop.call_soon_threadsafe(q.put_nowait, {"type": "progress", "message": msg})

    async def write_sse(item: dict) -> None:
        await resp.write(f"data: {json.dumps(item, ensure_ascii=False)}\n\n".encode())
        if hasattr(resp, "flush"):
            await resp.flush()

    async def worker() -> None:
        try:
            result = await asyncio.to_thread(
                board_extract.extract_board,
                sid,
                column_ids=column_ids,
                on_progress=on_progress,
            )
            await q.put({"type": "result", **result})
        except Exception as exc:
            await q.put({"type": "error", "message": str(exc)})

    worker_task = asyncio.create_task(worker())
    try:
        while True:
            item = await q.get()
            await write_sse(item)
            if item.get("type") in ("result", "error"):
                break
    except (asyncio.CancelledError, ConnectionResetError, BrokenPipeError):
        worker_task.cancel()
    finally:
        if not worker_task.done():
            worker_task.cancel()
    return resp


async def api_session_signals(request: web.Request) -> web.Response:
    sid = request.match_info.get("session_id", "")
    if not sess.session_exists(sid):
        return web.json_response({"error": "session not found"}, status=404)
    path = sess.session_path(sid)
    store = signals_v01_api.load_store(path)
    nodes = store.list_active_nodes()
    return web.json_response({"session_id": sid, "nodes": nodes, "store_path": str(store.store_path)})


async def api_session_signals_extract(request: web.Request) -> web.Response:
    sid = request.match_info.get("session_id", "")
    if not sess.session_exists(sid):
        return web.json_response({"error": f"session not found: {sid}"}, status=404)
    body: dict = {}
    if request.content_length:
        try:
            parsed = await request.json()
            if isinstance(parsed, dict):
                body = parsed
        except json.JSONDecodeError:
            return web.json_response({"error": "invalid JSON body"}, status=400)
    column_ids = body.get("columns")
    if column_ids is not None and not isinstance(column_ids, list):
        return web.json_response({"error": "columns must be a list of column ids"}, status=400)
    run_id = body.get("run_id")
    mutate_url = body.get("mutate_url")
    mutate_token = body.get("mutate_token")
    snapshot_url = body.get("snapshot_url")
    if mutate_url is not None and not isinstance(mutate_url, str):
        return web.json_response({"error": "mutate_url must be a string"}, status=400)
    if snapshot_url is not None and not isinstance(snapshot_url, str):
        return web.json_response({"error": "snapshot_url must be a string"}, status=400)
    try:
        result = await asyncio.to_thread(
            signals_v01_api.extract_signals,
            sid,
            column_ids=column_ids,
            run_id=run_id,
            mutate_url=mutate_url,
            snapshot_url=snapshot_url,
            mutate_token=str(mutate_token) if mutate_token else None,
        )
        return web.json_response(result)
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    except Exception as exc:
        trace.error("signals extract failed", exc, session_id=sid)
        return web.json_response({"error": str(exc)}, status=502)


async def api_session_signals_extract_stream(request: web.Request) -> web.Response:
    sid = request.match_info.get("session_id", "")
    if not sess.session_exists(sid):
        return web.json_response({"error": f"session not found: {sid}"}, status=404)
    body: dict = {}
    if request.content_length:
        try:
            parsed = await request.json()
            if isinstance(parsed, dict):
                body = parsed
        except json.JSONDecodeError:
            return web.json_response({"error": "invalid JSON body"}, status=400)
    column_ids = body.get("columns")
    if column_ids is not None and not isinstance(column_ids, list):
        return web.json_response({"error": "columns must be a list of column ids"}, status=400)
    run_id = body.get("run_id")
    mutate_url = body.get("mutate_url")
    mutate_token = body.get("mutate_token")
    snapshot_url = body.get("snapshot_url")

    resp = web.StreamResponse(
        status=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
    await resp.prepare(request)
    loop = asyncio.get_running_loop()
    q: asyncio.Queue[dict] = asyncio.Queue()

    def on_progress(msg: str) -> None:
        loop.call_soon_threadsafe(q.put_nowait, {"type": "progress", "message": msg})

    async def write_sse(item: dict) -> None:
        await resp.write(f"data: {json.dumps(item, ensure_ascii=False)}\n\n".encode())
        if hasattr(resp, "flush"):
            await resp.flush()

    async def worker() -> None:
        try:
            result = await asyncio.to_thread(
                signals_v01_api.extract_signals,
                sid,
                column_ids=column_ids,
                run_id=run_id,
                on_progress=on_progress,
                mutate_url=mutate_url if isinstance(mutate_url, str) else None,
                snapshot_url=snapshot_url if isinstance(snapshot_url, str) else None,
                mutate_token=str(mutate_token) if mutate_token else None,
            )
            await q.put({"type": "result", **result})
        except Exception as exc:
            await q.put({"type": "error", "message": str(exc)})

    worker_task = asyncio.create_task(worker())
    try:
        while True:
            item = await q.get()
            await write_sse(item)
            if item.get("type") in ("result", "error"):
                break
    except (asyncio.CancelledError, ConnectionResetError, BrokenPipeError):
        worker_task.cancel()
    finally:
        if not worker_task.done():
            worker_task.cancel()
    return resp


async def api_session_signals_mutate(request: web.Request) -> web.Response:
    sid = request.match_info.get("session_id", "")
    if not sess.session_exists(sid):
        return web.json_response({"error": f"session not found: {sid}"}, status=404)
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "invalid JSON body"}, status=400)
    if not isinstance(body, dict) or not body.get("action"):
        return web.json_response({"error": "action required"}, status=400)
    run_id = str(body.get("run_id") or "manual")
    path = sess.session_path(sid)
    try:
        result = await asyncio.to_thread(signals_v01_api.apply_mutation, path, body, run_id=run_id)
        status = 200 if result.get("ok") else 422
        return web.json_response(result, status=status)
    except Exception as exc:
        trace.error("signals mutate failed", exc, session_id=sid)
        return web.json_response({"error": str(exc)}, status=502)


async def api_session_signals_cancel(request: web.Request) -> web.Response:
    sid = request.match_info.get("session_id", "")
    if not sess.session_exists(sid):
        return web.json_response({"error": f"session not found: {sid}"}, status=404)
    body: dict = {}
    if request.content_length:
        try:
            parsed = await request.json()
            if isinstance(parsed, dict):
                body = parsed
        except json.JSONDecodeError:
            return web.json_response({"error": "invalid JSON body"}, status=400)
    column = body.get("column")
    if column is not None and not isinstance(column, str):
        return web.json_response({"error": "column must be a string or null"}, status=400)
    signals_v01_api.cancel_signals(sid, column_id=column)
    return web.json_response({"ok": True, "session_id": sid, "column": column})


async def api_session_turn_json(request: web.Request) -> web.Response:
    sid = request.match_info.get("session_id", "")
    turn_s = request.match_info.get("turn", "0")
    try:
        turn_n = int(turn_s)
    except ValueError:
        return web.json_response({"error": "invalid turn"}, status=400)
    if not sess.session_exists(sid):
        return web.json_response({"error": "session not found"}, status=404)
    path = sess.session_path(sid)
    data = sess.load_turn_json(path, turn_n)
    if not data:
        return web.json_response({"error": "turn not found"}, status=404)
    return web.json_response(data)


async def api_state(_request: web.Request) -> web.Response:
    return web.json_response({**sess.session_state(), "trace": trace.paths()})


async def api_reset(_request: web.Request) -> web.Response:
    return await api_new_session(_request)


async def api_new_session(_request: web.Request) -> web.Response:
    global _agent
    trace.info("session", "new session — shutdown agent and clear runtime")
    await asyncio.to_thread(_shutdown_agent)
    marker = sess.SESSIONS_DIR / ".active"
    if marker.exists():
        marker.unlink()
    trace.clear()
    trace.set_session_dir(None)
    _broadcast_event({"type": "session_reset"})
    return web.json_response({"ok": True, "session_id": None, "turn": 0})


async def api_diagnostics(_request: web.Request) -> web.Response:
    entries = trace.history(limit=1000)
    turn_rows = [
        {
            "turn": e["data"]["turn"],
            "elapsed_s": e["data"].get("elapsed_s"),
            "idle": e["data"].get("idle"),
        }
        for e in entries
        if e.get("kind") == "turn" and (e.get("data") or {}).get("action") == "complete"
    ]
    errors = [
        {"kind": e.get("kind"), "msg": e.get("msg"), "level": e.get("level"), "data": e.get("data")}
        for e in entries
        if e.get("level") == "error" or e.get("kind") == "error"
    ]
    compute_s = sum(float(t["elapsed_s"] or 0) for t in turn_rows)
    return web.json_response(
        {
            **sess.session_state(),
            "mode": AGENT_MODE,
            "mock": MOCK,
            "turn_latencies": turn_rows,
            "total_compute_s": round(compute_s, 2),
            "trace_errors": errors,
            "agent_alive": bool(_agent and _agent.alive),
            "agent_pid": _agent.pid if _agent else None,
        }
    )


async def api_trace(request: web.Request) -> web.Response:
    limit = int(request.rel_url.query.get("limit", "200"))
    kind = request.rel_url.query.get("kind")
    return web.json_response({"entries": trace.history(limit=limit, kind=kind), "paths": trace.paths()})


async def api_trace_clear(_request: web.Request) -> web.Response:
    trace.clear()
    return web.json_response({"ok": True})


async def index_page(_request: web.Request) -> web.FileResponse:
    return web.FileResponse(UI_DIR / "index.html")


async def api_trace_stream(request: web.Request) -> web.StreamResponse:
    """SSE stream of structured trace entries."""
    resp = web.StreamResponse(
        status=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
    await resp.prepare(request)
    q = trace.subscribe()
    try:
        for entry in trace.history(limit=100):
            await resp.write(f"data: {json.dumps(entry, ensure_ascii=False)}\n\n".encode())
        while True:
            try:
                entry = await asyncio.to_thread(q.get, True, 30.0)
            except queue.Empty:
                await resp.write(b": keepalive\n\n")
                continue
            await resp.write(f"data: {json.dumps(entry, ensure_ascii=False)}\n\n".encode())
    except (asyncio.CancelledError, ConnectionResetError, BrokenPipeError):
        pass
    finally:
        trace.unsubscribe(q)
    return resp


def _kill_port() -> None:
    import subprocess

    try:
        out = subprocess.check_output(["lsof", "-ti", f":{PORT}"], text=True).strip()
        for pid in out.splitlines():
            if pid:
                os.kill(int(pid), 9)
    except (subprocess.CalledProcessError, ProcessLookupError, ValueError):
        pass


async def _on_startup(_app: web.Application) -> None:
    global _broadcast_queue, _broadcast_task, _loop
    _loop = asyncio.get_running_loop()
    _broadcast_queue = asyncio.Queue(maxsize=4096)
    _broadcast_task = asyncio.create_task(_broadcast_worker())


async def _on_cleanup(_app: web.Application) -> None:
    global _broadcast_task
    if _broadcast_task:
        _broadcast_task.cancel()
        try:
            await _broadcast_task
        except asyncio.CancelledError:
            pass
        _broadcast_task = None
    trace.info("sys", "bridge shutdown (graceful)", port=PORT, pid=os.getpid())


def main() -> None:
    global _loop
    if "--kill-port" in sys.argv:
        _kill_port()
    trace.set_session_dir(sess.active_session())
    trace.info("sys", "Uplift v6 bridge starting", port=PORT, pid=os.getpid())

    app = web.Application(middlewares=[trace_middleware])
    app.on_startup.append(_on_startup)
    app.on_cleanup.append(_on_cleanup)
    app.router.add_get("/ws", websocket_handler)
    app.router.add_get("/api/health", api_health)
    app.router.add_get("/api/state", api_state)
    app.router.add_get("/api/diagnostics", api_diagnostics)
    app.router.add_get("/api/trace", api_trace)
    app.router.add_get("/api/trace/stream", api_trace_stream)
    app.router.add_post("/api/trace/clear", api_trace_clear)
    app.router.add_post("/api/start", api_start)
    app.router.add_get("/api/sessions/{session_id}/state", api_session_state)
    app.router.add_delete("/api/sessions/{session_id}", api_session_delete)
    app.router.add_post("/api/sessions/{session_id}/turn", api_session_turn)
    app.router.add_post("/api/sessions/{session_id}/turn/stream", api_session_turn_stream)
    app.router.add_get("/api/sessions/{session_id}/turns/{turn}", api_session_turn_json)
    app.router.add_get("/api/sessions/{session_id}/board", api_session_board)
    app.router.add_post("/api/sessions/{session_id}/board/extract", api_session_board_extract)
    app.router.add_post("/api/sessions/{session_id}/board/extract/stream", api_session_board_extract_stream)
    app.router.add_get("/api/sessions/{session_id}/signals", api_session_signals)
    app.router.add_post("/api/sessions/{session_id}/signals/extract", api_session_signals_extract)
    app.router.add_post("/api/sessions/{session_id}/signals/extract/stream", api_session_signals_extract_stream)
    app.router.add_post("/api/sessions/{session_id}/signals/mutate", api_session_signals_mutate)
    app.router.add_post("/api/sessions/{session_id}/signals/cancel", api_session_signals_cancel)
    app.router.add_post("/api/reset", api_reset)
    app.router.add_post("/api/new-session", api_new_session)
    app.router.add_get("/", index_page)
    app.router.add_get("/index.html", index_page)
    app.router.add_static("/", UI_DIR, show_index=False)

    if MOCK:
        trace.warn("sys", "Mock agent mode (UPLIFT_MOCK_AGENT=1) — no Cursor CLI calls")
    elif AGENT_MODE == "pty":
        threading.Thread(target=_warm_pty_agent, daemon=True, name="pty-warm").start()
    else:
        trace.warn("sys", "Headless agent mode — per-turn spawn; set UPLIFT_AGENT_MODE=pty for local PTY")

    paths = trace.paths()
    mode_label = "PTY (persistent)" if AGENT_MODE == "pty" else AGENT_MODE
    print(f"Uplift v6 → http://127.0.0.1:{PORT}/  ({mode_label} agent)")
    print(f"Trace log: {paths.get('jsonl')}")
    web.run_app(app, host="127.0.0.1", port=PORT, print=None)


if __name__ == "__main__":
    main()
