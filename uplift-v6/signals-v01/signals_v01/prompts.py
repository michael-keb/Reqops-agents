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


def title_column_prompt(
    *,
    column: SignalColumn,
    transcript: str,
    snapshot: list[dict[str, Any]],
) -> str:
    return f"""You are the **title agent** for the **{column.title}** column.

Column id: `{column.id}`
Definition: {column.definition}
Question: {column.question}

**Phase 1 — titles only.** Emit one `add_draft` per turn with a short card title. Do **not** write body text yet — a description agent fills that in after each title lands.

Rules:
- **Your entire response is one `## Action` block** — first line MUST be `## Action`, then a ```json fence with one action object.
- **Do NOT read files or use tools.**
- **Forbidden:** preamble, planning, skill reads, file tools, shell, grep, or any tool use.
- Emit **one** `add_draft` per turn, or `complete` when all titles for this column are done.
- Titles must be grounded in the transcript — short labels (3–8 words).

Existing cards in `{column.id}`:

```json
{_format_snapshot(snapshot)}
```

Required action shape:

## Action

```json
{{
  "action": "add_draft",
  "column": "{column.id}",
  "card": {{
    "title": "Short label from transcript"
  }}
}}
```

When all titles are added:

```json
{{ "action": "complete", "column": "{column.id}", "summary": "added N draft titles" }}
```

---

## Conversation transcript

{transcript}
"""


def title_continuation_prompt(
    *,
    column: SignalColumn,
    snapshot: list[dict[str, Any]],
    run_memory: list[dict[str, Any]],
) -> str:
    mem = json.dumps(run_memory, indent=2, ensure_ascii=False) if run_memory else "[]"
    return f"""Titles added this run:

```json
{mem}
```

Current column snapshot for `{column.id}`:

```json
{_format_snapshot(snapshot)}
```

Continue for **{column.title}**. Emit the next `add_draft` title, or `complete` if finished.
"""


def description_card_prompt(
    *,
    column: SignalColumn,
    transcript: str,
    card: dict[str, Any],
    snapshot: list[dict[str, Any]],
) -> str:
    card_json = json.dumps(card, indent=2, ensure_ascii=False)
    return f"""You are the **description agent** for signal-board extraction.

Fill in the body and evidence for **one draft card** in the **{column.title}** column.

Column id: `{column.id}`
Definition: {column.definition}

Draft card to complete (use exact `id` and `updatedAt` in your edit):

```json
{card_json}
```

Rules:
- **Your entire response is one `## Action` block** with a single `edit`.
- **Do NOT read files or use tools.**
- Write 1–3 concrete sentences for `body`.
- Include at least one verbatim `evidence` quote from the transcript.
- Set `confidence` to high, medium, low, or inferred (with rationale if inferred).
- After this edit the card leaves draft state.

Required action shape:

## Action

```json
{{
  "action": "edit",
  "column": "{column.id}",
  "id": "{card.get('id', '')}",
  "updatedAt": "{card.get('updatedAt', '')}",
  "patch": {{
    "body": "1–3 concrete sentences grounded in transcript.",
    "evidence": ["verbatim quote"],
    "confidence": "high"
  }}
}}
```

Column snapshot for context:

```json
{_format_snapshot(snapshot)}
```

---

## Conversation transcript

{transcript}
"""


def description_continuation_prompt(
    *,
    column: SignalColumn,
    card: dict[str, Any],
    snapshot: list[dict[str, Any]],
) -> str:
    card_json = json.dumps(card, indent=2, ensure_ascii=False)
    return f"""Next draft card in **{column.title}** (`{column.id}`).

Use the conversation transcript from earlier in this session. Fill body + evidence for this card only.

```json
{card_json}
```

Column snapshot:

```json
{_format_snapshot(snapshot)}
```

Emit one `edit` ## Action (exact `id` and `updatedAt` from the card above).
"""


def description_repair_prompt(*, column: SignalColumn, card: dict[str, Any]) -> str:
    return f"""Your previous response did NOT include a valid `## Action` edit block.

Reply with **ONLY** this shape — edit the draft card `{card.get('id', '')}` in **{column.title}**:

## Action

```json
{{
  "action": "edit",
  "column": "{column.id}",
  "id": "{card.get('id', '')}",
  "updatedAt": "{card.get('updatedAt', '')}",
  "patch": {{
    "body": "...",
    "evidence": ["quote from transcript"],
    "confidence": "high"
  }}
}}
```
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
