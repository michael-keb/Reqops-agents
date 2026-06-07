"""Recency tracking — which gaps were asked in prior turns."""

from __future__ import annotations

import json
import re
from pathlib import Path

from analyst.legend import CANONICAL_GAPS


def _gap_from_selection(data: dict) -> str | None:
    primary = data.get("primary")
    if isinstance(primary, dict) and primary.get("gap"):
        return str(primary["gap"]).upper()
    return None


def _gap_from_llm_response(text: str) -> str | None:
    m = re.search(r"###\s*1\.\s*`?(G[1-9A-D])`?", text, re.I)
    if m:
        return m.group(1).upper()
    return None


def build_asked_history(turns_dir: Path, *, through_turn: int | None = None) -> dict[str, list[int]]:
    """Scan prior turn folders for which gaps were primary questions."""
    history: dict[str, list[int]] = {g: [] for g in CANONICAL_GAPS}
    if not turns_dir.is_dir():
        return history

    nums = sorted(
        int(p.name)
        for p in turns_dir.iterdir()
        if p.is_dir() and p.name.isdigit() and len(p.name) == 2
    )
    for n in nums:
        if through_turn is not None and n >= through_turn:
            break
        d = turns_dir / f"{n:02d}"
        gap: str | None = None

        sel = d / "selection.json"
        if sel.is_file():
            try:
                gap = _gap_from_selection(json.loads(sel.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                gap = None

        if not gap:
            resp = d / "llm-response.txt"
            if resp.is_file():
                gap = _gap_from_llm_response(resp.read_text(encoding="utf-8"))

        if gap and gap in history:
            history[gap].append(n)

    return history
