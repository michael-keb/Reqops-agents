"""Merge fresh classification with prior grid — lock durability."""

from __future__ import annotations

import re
from dataclasses import replace

from analyst.legend import CANONICAL_GAPS
from analyst.models import AnswerHistory, GapRow, StateGrid

LOCKED_EXPOSURES: frozenset[str] = frozenset({"X3", "X5"})

_GAP_NEGATION_RULES: list[tuple[str, re.Pattern[str], re.Pattern[str]]] = [
    (
        "G6",
        re.compile(r"\bout of scope\b", re.I),
        re.compile(r"\bin scope\b|\binclude\b[^.]{0,40}\bv1\b", re.I),
    ),
    (
        "G5",
        re.compile(r"\bsuccess means\b", re.I),
        re.compile(r"\bsuccess (is|means) (not|never)\b", re.I),
    ),
    (
        "G9",
        re.compile(r"\bmanual negotiation only\b", re.I),
        re.compile(r"\bauction|instant offer|automated pric", re.I),
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
    ),
    (
        "GD",
        re.compile(r"\b(optimise for|optimize for).+over\b", re.I),
        re.compile(
            r"\b(optimi[sz]e for).+(growth|speed).+over.+(fraud|safety|trust)\b",
            re.I,
        ),
    ),
]

_EXPLICIT_REOPEN = re.compile(
    r"\b("
    r"change of plan|was wrong|not anymore|no longer|"
    r"we'?re letting|not just private|consumer-only was wrong|"
    r"actually,?\s+let'?s|drop the .+ restriction"
    r")\b",
    re.I,
)


def directly_negates(new_message: str, locked_by: str | None, gap: str) -> bool:
    if not new_message.strip():
        return False
    locked = (locked_by or "").strip()
    if not locked:
        return False

    if _EXPLICIT_REOPEN.search(new_message):
        for gap_code, pat_lock, pat_new in _GAP_NEGATION_RULES:
            if gap_code != gap:
                continue
            if pat_lock.search(locked) and pat_new.search(new_message):
                return True
        if gap in ("G1", "G6", "G5", "GD"):
            return True

    for gap_code, pat_lock, pat_new in _GAP_NEGATION_RULES:
        if gap_code != gap:
            continue
        if pat_lock.search(locked) and pat_new.search(new_message):
            return True

    return False


def _backfill_locked_by(row: GapRow, default_turn: int) -> GapRow:
    if row.exposure not in LOCKED_EXPOSURES or row.locked_by:
        return row
    text = row.evidence_snippets[-1] if row.evidence_snippets else ""
    if not text:
        return row
    turn = row.locked_turn
    if turn is None and row.evidence_turns:
        turn = row.evidence_turns[-1]
    return replace(
        row,
        locked_by=text[:500],
        locked_turn=turn if turn is not None else default_turn,
    )


def _closing_text(history: AnswerHistory, fresh: GapRow) -> str:
    latest = history.latest()
    if latest:
        return latest.raw_text.strip()[:500]
    if fresh.evidence_snippets:
        return fresh.evidence_snippets[-1][:500]
    return ""


def _apply_new_lock(
    fresh: GapRow,
    history: AnswerHistory,
    turn: int,
) -> GapRow:
    if fresh.exposure not in LOCKED_EXPOSURES:
        return fresh
    text = _closing_text(history, fresh)
    if not text:
        return fresh
    return replace(
        fresh,
        locked_by=text,
        locked_turn=turn,
    )


def _reopen_row(prior: GapRow, fresh: GapRow) -> GapRow:
    return replace(
        fresh,
        exposure="X6",
        locked_by=None,
        locked_turn=None,
        evidence_turns=list(
            dict.fromkeys(prior.evidence_turns + fresh.evidence_turns)
        ),
        evidence_snippets=(prior.evidence_snippets + fresh.evidence_snippets)[:3],
    )


def merge_gap(
    prior: GapRow | None,
    fresh: GapRow,
    *,
    new_message: str,
    history: AnswerHistory,
    turn: int,
) -> GapRow:
    if prior is None:
        return _apply_new_lock(fresh, history, turn)

    prior = _backfill_locked_by(prior, turn - 1)

    if prior.exposure in LOCKED_EXPOSURES:
        negated = directly_negates(new_message, prior.locked_by, prior.gap)
        if negated or fresh.exposure == "X6":
            return _reopen_row(prior, fresh)
        return replace(prior, gap=prior.gap)

    merged = fresh
    if fresh.exposure in LOCKED_EXPOSURES:
        merged = _apply_new_lock(fresh, history, turn)
    elif prior.exposure == "X6" and fresh.exposure in LOCKED_EXPOSURES:
        merged = _apply_new_lock(fresh, history, turn)
    return merged


def merge_grid(
    prior_grid: StateGrid | None,
    fresh_grid: StateGrid,
    history: AnswerHistory,
) -> StateGrid:
    latest = history.latest()
    new_message = latest.raw_text if latest else ""
    turn = fresh_grid.turn
    rows: dict[str, GapRow] = {}

    for gap in CANONICAL_GAPS:
        prior_row = prior_grid.rows.get(gap) if prior_grid else None
        fresh_row = fresh_grid.rows[gap]
        rows[gap] = merge_gap(
            prior_row,
            fresh_row,
            new_message=new_message,
            history=history,
            turn=turn,
        )

    return StateGrid(
        turn=turn,
        rows=rows,
        extras=list(fresh_grid.extras),
    )
