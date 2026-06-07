"""Build candidate list — step 1 of the v4 pipeline."""

from __future__ import annotations

from analyst.coverage import apply_coverage_floor
from analyst.grid.merge import directly_negates
from analyst.legend import CANONICAL_GAPS, GAP_INTENT, LOCKED_EXPOSURES
from analyst.models import AnswerHistory, Candidate, GapRow, StateGrid


def lock_code(
    row: GapRow,
    *,
    latest_message: str,
) -> tuple[str, str | None]:
    """Return (L0|L2|L3, veto_reason). L2 = veto unless negated."""
    if row.exposure not in LOCKED_EXPOSURES:
        return "L0", None

    if directly_negates(latest_message, row.locked_by, row.gap):
        return "L3", None

    locked = (row.locked_by or row.evidence_snippets[-1] if row.evidence_snippets else "")
    reason = (
        f"L2 locked by turn-{row.locked_turn or '?'} statement; "
        f"new message does not negate it"
    )
    return "L2", reason


def build_candidates(
    grid: StateGrid,
    history: AnswerHistory,
    *,
    asked_history: dict[str, list[int]],
    current_turn: int,
) -> tuple[list[Candidate], list[dict[str, str]]]:
    """Eligible candidates + vetoed gaps (L2)."""
    latest = history.latest()
    latest_message = latest.raw_text if latest else ""
    eligible: list[Candidate] = []
    vetoed: list[dict[str, str]] = []

    floor_flags = apply_coverage_floor(
        grid, asked_history=asked_history, current_turn=current_turn
    )

    for gap in CANONICAL_GAPS:
        row = grid.rows[gap]
        code, veto_reason = lock_code(row, latest_message=latest_message)
        if code == "L2":
            vetoed.append({"gap": gap, "reason": veto_reason or "L2 locked"})
            continue

        eligible.append(
            Candidate(
                gap=gap,
                intent=GAP_INTENT.get(gap, gap),
                exposure=row.exposure,
                risk_class=row.risk_class,
                evidence_snippets=list(row.evidence_snippets),
                locked_by=row.locked_by,
                floor_flag=floor_flags.get(gap, False),
            )
        )

    return eligible, vetoed
