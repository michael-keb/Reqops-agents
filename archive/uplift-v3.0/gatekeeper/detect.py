"""Detect contradictions (X6) and off-angles (X8) from latest user message."""

from __future__ import annotations

import re

from gatekeeper.models import AnswerHistory, DetectHint, StateGrid

# Pairs of patterns: if prior text matched A and latest matches B → contradiction on gap.
CONTRADICTION_RULES: list[tuple[str, re.Pattern[str], re.Pattern[str], str]] = [
    (
        "G6",
        re.compile(r"\bout of scope\b", re.I),
        re.compile(r"\bin scope\b|\binclude\b.*\bv1\b", re.I),
        "scope boundary reversed",
    ),
    (
        "G5",
        re.compile(r"\bsuccess means\b", re.I),
        re.compile(r"\bsuccess (is|means) (not|never)\b", re.I),
        "success metric reversed",
    ),
    (
        "G9",
        re.compile(r"\bmanual negotiation only\b", re.I),
        re.compile(r"\bauction|instant offer|automated pric", re.I),
        "pricing model reversed",
    ),
    (
        "G1",
        re.compile(
            r"\b(consumer-only|private sellers?|individuals selling|primary users)\b",
            re.I,
        ),
        re.compile(
            r"\b(dealers?|dealer fleet|not just private|consumer-only was wrong)\b",
            re.I,
        ),
        "user base expanded to dealers",
    ),
]


def detect_changes(
    history: AnswerHistory,
    prior_grid: StateGrid | None = None,
) -> list[DetectHint]:
    hints: list[DetectHint] = []
    latest = history.latest()
    if not latest or len(history.turns) < 2:
        return hints

    prior_text = "\n".join(t.raw_text for t in history.turns[:-1])
    latest_text = latest.raw_text

    if prior_grid:
        for gap, row in prior_grid.rows.items():
            if row.exposure not in ("X3", "X5"):
                continue
            for gap_code, pat_a, pat_b, reason in CONTRADICTION_RULES:
                if gap_code != gap:
                    continue
                if pat_a.search(prior_text) and pat_b.search(latest_text):
                    hints.append(
                        DetectHint(
                            gap=gap,
                            kind="contradiction",
                            reason=reason,
                            suggested_exposure="X6",
                        )
                    )

    # Off-angle: long free-text on turn 1+ that doesn't match known gap keywords well
    off_angle_markers = (
        "by the way",
        "also important",
        "another thing",
        "forgot to mention",
    )
    lower = latest_text.lower()
    if any(m in lower for m in off_angle_markers):
        hints.append(
            DetectHint(
                gap="G0",
                kind="off_angle",
                reason="user volunteered tangential detail",
                suggested_exposure="X8",
            )
        )

    return hints
