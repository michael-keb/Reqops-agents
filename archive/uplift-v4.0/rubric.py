"""Load multiplier rubric from file — reference only, never embed in code."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUBRIC_PATH = ROOT / "llm_rubric_multiplier.md"
RUBRIC_FILENAME = RUBRIC_PATH.name
INSTRUCTIONS_PATH = ROOT / "instrucitons.md"


def load_multiplier_rubric() -> str:
    if not RUBRIC_PATH.is_file():
        sys.exit(f"Missing rubric: {RUBRIC_PATH}")
    return RUBRIC_PATH.read_text(encoding="utf-8").strip()


def load_instructions() -> str:
    if not INSTRUCTIONS_PATH.is_file():
        return ""
    return INSTRUCTIONS_PATH.read_text(encoding="utf-8").strip()


def load_scorer_system_prompt() -> str:
    """Full multiplier rubric as system prompt for the scoring LLM."""
    return load_multiplier_rubric()


def load_phrasing_system_prompt() -> str:
    """Phrasing uses a short contract; full rubric referenced for analyst voice."""
    from pathlib import Path

    prompt_path = ROOT / "prompts" / "phrase-question.md"
    if prompt_path.is_file():
        body = prompt_path.read_text(encoding="utf-8").strip()
    else:
        body = "Phrase one MCQ from the SELECTION block. Ground in user words."
    return (
        f"{body}\n\n"
        f"Analyst multiplier reference (for voice, not re-scoring): see {RUBRIC_FILENAME}."
    )
