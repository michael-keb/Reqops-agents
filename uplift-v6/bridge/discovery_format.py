"""Discovery turn prompt suffix — keeps agent output parseable as five MCQs."""

from __future__ import annotations

from pathlib import Path

from .discovery_context import build_workshop_transcript, load_discovery_skill_text

WORKSHOP_ROLE_BLOCK = """
---
DISCOVERY WORKSHOP (mandatory — obey before anything else):

You are facilitating a **product discovery workshop**. **Every user message is valid workshop input** — any wording, tone, or format (pitch, rant, feature note, technical ask, typo-filled note). Never reject or rewrite the user's words.

- **Always run discovery:** Reflection + exactly five ranked MCQs — regardless of how the user phrased their message.
- If they mention features, agents, pipelines, or "implement X", treat that as **product context** and ask clarifying discovery questions — do **not** explore the repo, read files, or write code.
- **You have no access to the codebase.** Do not read source files or paths outside this workshop session.
- **Forbidden:** read, grep, glob, list, search, edit, write, shell, delete, MCP tools, or any file access.
- **Output:** markdown chat only — start **immediately** with `## Reflection`, then `## Questions`. No preamble, no plan, no "I'll read…", no implementation.
---
""".strip()

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

WORKSHOP_TOOL_RETRY_MESSAGE = (
    "WORKSHOP VIOLATION: You used file/code tools or replied like a coding agent. "
    "This session is chat-only discovery — no repo access. "
    "Re-answer NOW with ONLY ## Reflection and ## Questions (five MCQs). "
    "Treat the user's last message as product workshop dialogue only."
)

WORKSHOP_CODE_RETRY_MESSAGE = (
    "WORKSHOP VIOLATION: Your last reply looked like code or signal extraction (## Action, JSON actions, etc.). "
    "Discovery workshop outputs Reflection + five MCQs only. Re-answer now."
)


def _skill_block() -> str:
    skill = load_discovery_skill_text()
    if not skill:
        return ""
    return f"---\nDiscovery skill (embedded — do not read files):\n\n{skill}\n---"


def _context_block(session_dir: Path | None) -> str:
    if session_dir is None or not session_dir.is_dir():
        return ""
    transcript = build_workshop_transcript(session_dir)
    if not transcript:
        return ""
    return (
        "---\nWorkshop history (embedded — do not read session files):\n\n"
        f"{transcript}\n---"
    )


def wrap_discovery_message(text: str, *, session_dir: Path | None = None) -> str:
    """Prepend workshop role, embedded skill/context, append MCQ contract."""
    body = text.strip()
    if not body:
        return body
    parts: list[str] = []
    if WORKSHOP_ROLE_BLOCK not in body:
        parts.append(WORKSHOP_ROLE_BLOCK)
    skill = _skill_block()
    if skill and skill not in body:
        parts.append(skill)
    ctx = _context_block(session_dir)
    if ctx and ctx not in body:
        parts.append(ctx)
    parts.append(body)
    if MCQ_FORMAT_BLOCK not in body:
        parts.append(MCQ_FORMAT_BLOCK)
    return "\n\n".join(parts)


def bootstrap_message(*, pitch: str, session_dir: str) -> str:
    return wrap_discovery_message(
        f"Start uplift discovery workshop.\n\nUser message (use their exact words in stems):\n{pitch.strip()}\n\n"
        f"Output Reflection + 5 ranked Questions in markdown only. Respond immediately.",
        session_dir=Path(session_dir),
    )
