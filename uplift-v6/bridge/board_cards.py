"""Build transcripts, prompts, and parse column-agent card output."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import artifacts
from .board_columns import BOARD_COLUMNS, BoardColumn

SKILL_PATH = ".cursor/skills/uplift-board-column/SKILL.md"


def build_transcript(session_dir: Path) -> str:
    """Assemble discovery conversation from Memory.md and turn artifacts."""
    parts: list[str] = []
    memory = session_dir / "Memory.md"
    if memory.is_file():
        parts.append(memory.read_text(encoding="utf-8").strip())

    turns_root = session_dir / "turns"
    if turns_root.is_dir():
        for turn_dir in sorted(turns_root.iterdir()):
            if not turn_dir.is_dir():
                continue
            label = turn_dir.name
            user_path = turn_dir / "user-input.txt"
            response_path = turn_dir / "response.md"
            if user_path.is_file():
                parts.append(f"### User (turn {label})\n{user_path.read_text(encoding='utf-8').strip()}")
            if response_path.is_file():
                parts.append(f"### Agent (turn {label})\n{response_path.read_text(encoding='utf-8').strip()}")

    return "\n\n---\n\n".join(p for p in parts if p.strip())


def column_prompt(*, column: BoardColumn, transcript: str) -> str:
    return f"""You are the **{column.title}** column agent.

Purpose: {column.purpose}
Question: {column.question}

Rules:
- Read the conversation transcript below.
- Create up to {column.target_cards} cards supported by the transcript only.
- Do not invent facts not grounded in the transcript.
- Each card: short title, 1–3 sentence body, at least one evidence quote, confidence (high|medium|low).
- Output markdown only — no file tools, no preamble.

Required shape:

## Reflection
(1–2 sentences on what you extracted for {column.title}.)

## Cards

```json
{{
  "column": "{column.id}",
  "cards": [
    {{
      "title": "...",
      "body": "...",
      "evidence": ["verbatim quote from transcript"],
      "confidence": "high"
    }}
  ]
}}
```

---

## Conversation transcript

{transcript}
"""


def _parse_reflection(text: str) -> str:
    m = re.search(r"## Reflection\s*\n([\s\S]*?)(?=\n## |\Z)", text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def parse_column_response(text: str, *, column: BoardColumn) -> dict[str, Any]:
    """Parse agent stdout into column payload with cards."""
    reflection = _parse_reflection(text)
    parsed = artifacts.extract_json_block(text)
    cards: list[dict[str, Any]] = []
    if parsed and isinstance(parsed.get("cards"), list):
        for raw in parsed["cards"]:
            if not isinstance(raw, dict):
                continue
            title = str(raw.get("title") or "").strip()
            body = str(raw.get("body") or "").strip()
            if not title and not body:
                continue
            evidence = raw.get("evidence")
            if isinstance(evidence, str):
                evidence = [evidence]
            elif not isinstance(evidence, list):
                evidence = []
            confidence = str(raw.get("confidence") or "medium").strip().lower()
            if confidence not in ("high", "medium", "low"):
                confidence = "medium"
            cards.append(
                {
                    "title": title or body[:80],
                    "body": body,
                    "evidence": [str(e).strip() for e in evidence if str(e).strip()],
                    "confidence": confidence,
                }
            )
    return {
        "id": column.id,
        "title": column.title,
        "description": column.description,
        "reflection": reflection,
        "cards": cards,
    }


def mock_column_payload(*, column: BoardColumn, transcript: str) -> dict[str, Any]:
    snippet = transcript.strip().splitlines()[0][:120] if transcript.strip() else column.title
    cards = [
        {
            "title": f"{column.title} item {i + 1}",
            "body": f"Mock card derived from conversation context for {column.title.lower()}.",
            "evidence": [snippet] if snippet else [],
            "confidence": "medium",
        }
        for i in range(min(column.target_cards, 2))
    ]
    return {
        "id": column.id,
        "title": column.title,
        "description": column.description,
        "reflection": f"Mock extraction for {column.title} (UPLIFT_MOCK_AGENT=1).",
        "cards": cards,
    }


def board_dir(session_dir: Path) -> Path:
    return session_dir / "board"


def board_json_path(session_dir: Path) -> Path:
    return board_dir(session_dir) / "board.json"


def load_board(session_dir: Path) -> dict[str, Any] | None:
    path = board_json_path(session_dir)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def save_board(session_dir: Path, columns: list[dict[str, Any]], *, elapsed_s: float | None = None) -> Path:
    out_dir = board_dir(session_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_s": elapsed_s,
        "columns": columns,
    }
    path = board_json_path(session_dir)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def persist_column_run(
    session_dir: Path,
    *,
    column: BoardColumn,
    response_text: str,
    elapsed_s: float | None = None,
) -> dict[str, Any]:
    """Write per-column raw response + parsed cards under board/{slug}/."""
    col_dir = board_dir(session_dir) / column.slug
    col_dir.mkdir(parents=True, exist_ok=True)
    (col_dir / "response.raw.md").write_text(response_text, encoding="utf-8")
    payload = parse_column_response(response_text, column=column)
    if elapsed_s is not None:
        payload["elapsed_s"] = elapsed_s
    (col_dir / "column.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload
