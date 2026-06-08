"""Discovery workshop context — skill text + session transcript (no repo reads)."""

from __future__ import annotations

import re
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_FILE = ROOT / ".cursor/skills/uplift-discovery/SKILL.md"

_SIG_PKG = ROOT / "signals-v01"
if str(_SIG_PKG) not in sys.path:
    sys.path.insert(0, str(_SIG_PKG))

from signals_v01.transcript import build_transcript  # noqa: E402

# Structural signals of a coding-agent reply — not product words like "description agent".
_CODE_OUTPUT_MARKERS = (
    "## action",
    "column_runner",
    "signals-v01",
    "signals_v01",
    "extract.py",
    "add_draft",
    '"action":',
    "parse_action",
    "```mermaid",
    "sequencediagram",
    "## pipeline",
    "## key files",
    "/signals/extract/stream",
    "want me to trace",
    "unit tests pass",
)


@lru_cache(maxsize=1)
def load_discovery_skill_text() -> str:
    """Embedded uplift-discovery skill — agent must not open this file itself."""
    if not SKILL_FILE.is_file():
        return ""
    raw = SKILL_FILE.read_text(encoding="utf-8")
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            raw = parts[2].strip()
    # Drop mermaid "thinking brain" — huge, slows turns, confuses output shape.
    raw = re.sub(r"### Thinking brain[\s\S]*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"```mermaid[\s\S]*?```", "", raw)
    return raw.strip()


def build_workshop_transcript(session_dir: Path) -> str:
    """Reflection-only workshop history from session artifacts."""
    try:
        return build_transcript(session_dir, reflection_only=True).strip()
    except Exception:
        return ""


def looks_like_code_output(text: str) -> bool:
    """True when the model replied like a coding agent, not discovery MCQs."""
    body = (text or "").strip()
    if not body:
        return False
    lower = body.lower()
    if any(m in lower for m in _CODE_OUTPUT_MARKERS):
        return True
    if "i'll explore" in lower or "i'll check" in lower or "fixing " in lower:
        return True
    return False


def valid_discovery_response(text: str) -> bool:
    """Strict: Reflection + exactly five MCQs with three options each."""
    from . import artifacts

    body = (text or "").strip()
    if not body:
        return False
    if not re.search(r"##\s*Reflection\b", body, re.I):
        return False
    if not re.search(r"##\s*Questions\b", body, re.I):
        return False

    reflection = artifacts._parse_reflection(body)
    if not reflection or len(reflection.strip()) < 8:
        return False

    parsed = artifacts._parse_questions_markdown(body)
    questions = artifacts.ensure_mcq_questions(body, parsed)
    if len(questions) != 5:
        return False

    for q in questions:
        opts = q.get("options") or []
        if len(opts) != 3:
            return False
        if not artifacts._options_valid(opts):
            return False
        title = str(q.get("title") or "")
        if len(title) > 120:
            return False

    # Parsed workshop shape wins — product copy may mention agents, extract, etc.
    return True
