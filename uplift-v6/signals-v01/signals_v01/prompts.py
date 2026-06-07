"""Prompt assembly for signals-v01 column agents."""

from __future__ import annotations

import json
from typing import Any

from .columns import SignalColumn

SKILL_PATH = ".cursor/skills/uplift-signals-v01/SKILL.md"


def _format_snapshot(cards: list[dict[str, Any]]) -> str:
    if not cards:
        return "(empty column — no existing cards)"
    return json.dumps(cards, indent=2, ensure_ascii=False)


def repair_prompt(*, column: SignalColumn) -> str:
    return f"""Your previous response did NOT include a valid `## Action` JSON block.

Reply with **ONLY** this shape — no preamble, no tools, no planning text:

## Action

```json
{{
  "action": "add",
  "column": "{column.id}",
  "card": {{
    "title": "...",
    "body": "...",
    "evidence": ["quote from transcript"],
    "confidence": "high"
  }}
}}
```

Or emit `edit` / `remove` / `complete` for the **{column.title}** column.
"""


def column_prompt(
    *,
    column: SignalColumn,
    transcript: str,
    snapshot: list[dict[str, Any]],
) -> str:
    return f"""You are the **{column.title}** column agent for signal-board extraction.

Column id: `{column.id}`
Definition: {column.definition}
Question: {column.question}

You are **editor of record** for this column only. You may add, edit, or remove any card in this lane — including human-created cards. Prefer **edit** over duplicate **add** when a card is nearly the same.

Rules:
- **Your entire response is one `## Action` block** — first line MUST be `## Action`, then a ```json fence with one action object.
- **Do NOT read files or use tools** — the protocol is fully specified below; never open `.cursor/skills/`.
- **Forbidden:** preamble, planning, skill reads, file tools, shell, grep, or any tool use.
- Read the conversation transcript and the existing column snapshot below.
- Output markdown only — **no file tools**, no discovery MCQs.
- Emit **one** action per turn under `## Action` (add | edit | remove | complete).
- For edit/remove: echo the exact `id` and `updatedAt` from the snapshot — never invent ids.
- Ground high/medium adds in transcript evidence; use inferred + rationale when thin.

Existing cards in `{column.id}` (use these ids for edit/remove):

```json
{_format_snapshot(snapshot)}
```

Required first action shape (example):

## Action

```json
{{
  "action": "add",
  "column": "{column.id}",
  "card": {{
    "title": "...",
    "body": "...",
    "evidence": ["verbatim quote"],
    "confidence": "high",
    "source_turn": "01",
    "source_message_id": "user-turn-01"
  }}
}}
```

When finished:

```json
{{ "action": "complete", "column": "{column.id}", "summary": "added N, edited M, removed K" }}
```

---

## Conversation transcript

{transcript}
"""


def continuation_prompt(
    *,
    column: SignalColumn,
    snapshot: list[dict[str, Any]],
    run_memory: list[dict[str, Any]],
) -> str:
    mem = json.dumps(run_memory, indent=2, ensure_ascii=False) if run_memory else "[]"
    return f"""Memory (mutations applied this run):

```json
{mem}
```

Current column snapshot for `{column.id}`:

```json
{_format_snapshot(snapshot)}
```

Continue for the **{column.title}** column. Prefer edit over duplicate add.
Emit the next `## Action` block, or `complete` if finished.
"""
