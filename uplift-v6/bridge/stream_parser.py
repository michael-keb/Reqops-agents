"""Parse Cursor agent `--output-format stream-json` NDJSON lines."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class StreamEvent:
    """One parsed stream-json line for trace + optional terminal display."""

    kind: str  # agent | tool | thinking | assistant | result | user | system
    msg: str
    data: dict[str, Any]
    terminal: str | None = None  # human-readable line(s) for xterm panel


def _short_path(path: str | None, root_hint: str = "") -> str:
    if not path:
        return "?"
    p = Path(path)
    try:
        if root_hint:
            return str(p.relative_to(root_hint))
    except ValueError:
        pass
    parts = p.parts
    if len(parts) >= 2:
        return "/".join(parts[-2:])
    return p.name


def _tool_label(tool_call: dict[str, Any], *, root: str = "") -> tuple[str, dict[str, Any]]:
    for key, body in tool_call.items():
        if not key.endswith("ToolCall"):
            continue
        name = key[: -len("ToolCall")]
        args = body.get("args") or {}
        detail: dict[str, Any] = {"tool": name, "args": args}

        if name == "read":
            path = _short_path(args.get("path"), root)
            limit = args.get("limit")
            msg = f"read {path}" + (f" (limit {limit})" if limit else "")
            detail["path"] = path
            return msg, detail
        if name == "write":
            path = _short_path(args.get("path"), root)
            msg = f"write {path}"
            detail["path"] = path
            return msg, detail
        if name == "shell" or name == "runTerminal":
            cmd = (args.get("command") or args.get("cmd") or "")[:120]
            msg = f"shell {cmd}"
            detail["command"] = cmd
            return msg, detail
        if name == "grep" or name == "search":
            pattern = (args.get("pattern") or args.get("query") or "")[:80]
            msg = f"{name} {pattern!r}"
            return msg, detail
        if name == "list":
            path = _short_path(args.get("path") or args.get("targetDirectory"), root)
            msg = f"list {path}"
            return msg, detail
        msg = f"{name} {args}"
        return msg[:160], detail
    return "tool", {"tool_call": tool_call}


def _tool_result_summary(tool_call: dict[str, Any]) -> str:
    for key, body in tool_call.items():
        if not key.endswith("ToolCall"):
            continue
        result = body.get("result") or {}
        if "success" in result:
            succ = result["success"]
            if isinstance(succ, dict):
                if "content" in succ:
                    text = str(succ["content"]).replace("\n", " ")[:100]
                    return f"ok · {text}…" if len(str(succ["content"])) > 100 else f"ok · {text}"
                if "linesCreated" in succ:
                    return f"ok · {succ.get('linesCreated')} lines"
                return "ok"
            return "ok"
        if "error" in result:
            return f"error · {result['error']}"
    return "done"


def _extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text") or ""))
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    if isinstance(content, dict):
        return _extract_text(content.get("content") or content.get("text") or "")
    return ""


def parse_stream_line(line: str, *, cwd: str = "", turn: int | None = None) -> StreamEvent | None:
    line = line.strip()
    if not line:
        return None
    try:
        import json

        obj = json.loads(line)
    except json.JSONDecodeError:
        return StreamEvent(
            kind="agent",
            msg=line[:200],
            data={"parse_error": True, "raw_line": line[:500], "turn": turn},
            terminal=line + "\n",
        )

    etype = obj.get("type") or "unknown"
    subtype = obj.get("subtype")
    base = {
        "event_type": etype,
        "subtype": subtype,
        "turn": turn,
        "call_id": obj.get("call_id"),
        "timestamp_ms": obj.get("timestamp_ms"),
    }

    if etype == "system" and subtype == "init":
        return StreamEvent(
            kind="agent",
            msg=f"init · model {obj.get('model', '?')}",
            data={**base, "model": obj.get("model"), "cwd": obj.get("cwd"), "session_id": obj.get("session_id")},
        )

    if etype == "user":
        text = _extract_text(obj.get("message"))
        preview = text.replace("\n", " ")[:120]
        return StreamEvent(
            kind="agent",
            msg=f"user → {preview}",
            data={**base, "text": text},
        )

    if etype == "thinking":
        if subtype == "delta" and not _thinking_verbose():
            return None
        if subtype == "delta":
            text = obj.get("text") or ""
            return StreamEvent(
                kind="thinking",
                msg=text[:200],
                data={**base, "text": text},
            )
        if subtype == "completed":
            return StreamEvent(
                kind="thinking",
                msg="thinking done",
                data=base,
            )
        return StreamEvent(kind="thinking", msg=str(subtype or etype), data={**base, "raw": obj})

    if etype == "tool_call":
        tc = obj.get("tool_call") or {}
        label, detail = _tool_label(tc, root=cwd)
        if subtype == "started":
            prefix = "▶"
            terminal = f"[tool] {label}\n"
        else:
            prefix = "✓" if "error" not in _tool_result_summary(tc).lower() else "✗"
            summary = _tool_result_summary(tc)
            label = f"{label} — {summary}"
            terminal = f"{prefix} {label}\n"
        return StreamEvent(
            kind="tool",
            msg=f"{prefix} {label}",
            data={**base, **detail, "tool_call": tc},
            terminal=terminal,
        )

    if etype == "assistant":
        text = _extract_text(obj.get("message"))
        if subtype == "delta" and text:
            return StreamEvent(
                kind="assistant",
                msg=text[:200],
                data={**base, "text": text, "partial": True},
                terminal=text,
            )
        if text:
            return StreamEvent(
                kind="assistant",
                msg=text[:200] + ("…" if len(text) > 200 else ""),
                data={**base, "text": text},
                terminal=text + "\n" if not text.endswith("\n") else text,
            )
        return StreamEvent(kind="assistant", msg="(assistant)", data={**base, "raw": obj})

    if etype == "result":
        text = obj.get("result") or obj.get("text") or _extract_text(obj.get("message"))
        if isinstance(text, dict):
            text = text.get("text") or str(text)
        text = str(text or "")
        ok = subtype == "success"
        term = None
        if text and len(text) > 1:
            term = text if text.endswith("\n") else text + "\n"
        return StreamEvent(
            kind="result",
            msg=f"{'done' if ok else 'failed'} · {text[:120]}{'…' if len(text) > 120 else ''}",
            data={**base, "text": text, "success": ok},
            terminal=term,
        )

    return StreamEvent(
        kind="agent",
        msg=f"{etype}/{subtype or '-'}",
        data={**base, "raw": obj},
    )


def _thinking_verbose() -> bool:
    import os

    return os.environ.get("UPLIFT_TRACE_THINKING", "").strip() in ("1", "true", "yes", "delta")
