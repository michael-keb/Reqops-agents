"""Discovery turn prompt suffix — keeps agent output parseable as five MCQs."""

from __future__ import annotations

MCQ_FORMAT_BLOCK = """
---
Uplift output contract (mandatory — copy this shape exactly):

## Reflection
(1–2 sentences)

## Questions

### 1. Short human title
One stem sentence grounded in the user's words.

- A) First specific choice
- B) Second specific choice
- C) Third specific choice

### 2. …
### 3. …
### 4. …
### 5. …

Forbidden: "Something else", "Other", "None of the above", or any open-text / catch-all option.
Forbidden: numbered lists "1. **Question**" without - A) - B) - C) under each question.
""".strip()

MCQ_RETRY_MESSAGE = (
    "Your last reply was rejected: Questions must use ### 1.–5. headings and exactly three bullets "
    "- A) - B) - C) under each — all concrete choices, no 'Something else'. "
    "Re-output ONLY ## Reflection and ## Questions in that format. "
    "Keep the same five topics; do not add preamble or file reads."
)


def wrap_discovery_message(text: str) -> str:
    """Append format contract so every turn is MCQ-parseable."""
    body = text.strip()
    if not body:
        return body
    if MCQ_FORMAT_BLOCK in body:
        return body
    return f"{body}\n\n{MCQ_FORMAT_BLOCK}"


def bootstrap_message(*, pitch: str, session_dir: str) -> str:
    return wrap_discovery_message(
        f"Start uplift discovery for: {pitch}\n"
        f"Session dir: {session_dir}\n"
        f"Follow .cursor/skills/uplift-discovery/SKILL.md.\n"
        f"Output Reflection + 5 ranked Questions in markdown only. Respond immediately — no file reads, no scoring narration.\n"
        f"Do NOT use edit/write/read on session files — the bridge saves your stdout."
    )
