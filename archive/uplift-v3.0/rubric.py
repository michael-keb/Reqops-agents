"""Load discovery rubric from llm-rubric_v2.md (single source of truth)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUBRIC_V2_PATH = ROOT / "llm-rubric_v2.md"
RUBRIC_V2_FILENAME = RUBRIC_V2_PATH.name


def load_rubric_v2() -> str:
    if not RUBRIC_V2_PATH.is_file():
        sys.exit(f"Missing rubric: {RUBRIC_V2_PATH}")
    return RUBRIC_V2_PATH.read_text(encoding="utf-8").strip()


def load_phrasing_system_prompt() -> str:
    """Full llm-rubric_v2.md as the phrasing LLM system prompt — no excerpting."""
    return load_rubric_v2()
