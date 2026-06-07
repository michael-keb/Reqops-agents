"""Parse and validate streaming ## Action blocks from column agent stdout."""

from __future__ import annotations

import json
import re
from typing import Any

ACTION_BLOCK_RE = re.compile(
    r"## Action\s*\n+```(?:json)?\s*\n([\s\S]*?)\n```",
    re.IGNORECASE,
)
ACTION_TAIL_RE = re.compile(r"## Action\s*\n+(\{[\s\S]+\})\s*$", re.IGNORECASE)
ACTION_OPEN_FENCE_RE = re.compile(
    r"## Action\s*\n+```(?:json)?\s*\n([\s\S]+)$",
    re.IGNORECASE,
)


def _load_action_json(raw: str) -> dict[str, Any] | None:
    text = raw.strip()
    if not text:
        return None
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        # Unclosed fence — try to recover a single top-level object.
        depth = 0
        end = -1
        for i, ch in enumerate(text):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if end >= 0:
            try:
                obj = json.loads(text[: end + 1])
            except json.JSONDecodeError:
                return None
        else:
            return None
    if isinstance(obj, dict) and obj.get("action"):
        return obj
    return None


def parse_action_blocks(text: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for m in ACTION_BLOCK_RE.finditer(text):
        obj = _load_action_json(m.group(1))
        if obj:
            out.append(obj)
    if out:
        return out

    # Prefer the last ## Action block when the model added preamble text.
    tail = text
    idx = text.lower().rfind("## action")
    if idx >= 0:
        tail = text[idx:]

    m = ACTION_OPEN_FENCE_RE.search(tail)
    if m:
        obj = _load_action_json(m.group(1))
        if obj:
            return [obj]

    m = ACTION_TAIL_RE.search(tail)
    if m:
        obj = _load_action_json(m.group(1))
        if obj:
            return [obj]

    return out


def parse_new_actions(text: str, *, seen: int) -> list[dict[str, Any]]:
    blocks = parse_action_blocks(text)
    return blocks[seen:]


def _non_empty_str(v: Any) -> str:
    return str(v or "").strip()


def validate_add(action: dict[str, Any], *, expected_column: str) -> str | None:
    if _non_empty_str(action.get("column")) != expected_column:
        return f"column must be {expected_column}"
    card = action.get("card")
    if not isinstance(card, dict):
        return "add requires card object"
    title = _non_empty_str(card.get("title"))
    body = _non_empty_str(card.get("body"))
    if not title or not body:
        return "add requires title and body"
    confidence = _non_empty_str(card.get("confidence")).lower() or "medium"
    if confidence == "inferred":
        rationale = card.get("rationale")
        if not isinstance(rationale, dict):
            return "inferred add requires rationale object"
        for key in ("gap", "paraphrase"):
            if not _non_empty_str(rationale.get(key)):
                return f"inferred add requires rationale.{key}"
        return None
    if confidence not in ("high", "medium", "low"):
        return "confidence must be high, medium, low, or inferred"
    evidence = card.get("evidence")
    if isinstance(evidence, str):
        evidence = [evidence]
    if not isinstance(evidence, list) or not any(_non_empty_str(e) for e in evidence):
        return "grounded add requires at least one evidence quote"
    return None


def validate_edit(action: dict[str, Any], *, expected_column: str, known_ids: set[str]) -> str | None:
    if _non_empty_str(action.get("column")) != expected_column:
        return f"column must be {expected_column}"
    node_id = _non_empty_str(action.get("id"))
    if not node_id:
        return "edit requires id"
    if node_id not in known_ids:
        return f"unknown id {node_id}"
    if not _non_empty_str(action.get("updatedAt")):
        return "edit requires updatedAt"
    patch = action.get("patch")
    if not isinstance(patch, dict) or not patch:
        return "edit requires non-empty patch"
    return None


def validate_remove(action: dict[str, Any], *, expected_column: str, known_ids: set[str]) -> str | None:
    if _non_empty_str(action.get("column")) != expected_column:
        return f"column must be {expected_column}"
    node_id = _non_empty_str(action.get("id"))
    if not node_id:
        return "remove requires id"
    if node_id not in known_ids:
        return f"unknown id {node_id}"
    if not _non_empty_str(action.get("updatedAt")):
        return "remove requires updatedAt"
    if not _non_empty_str(action.get("reason")):
        return "remove requires reason"
    return None
