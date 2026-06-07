"""Build question plan from assessment — up to MAX_BATCH_SIZE probes per turn."""

from __future__ import annotations

import os

from gatekeeper.assess import DiscoveryAssessment, WeaknessItem, assess_discovery
from gatekeeper.legend import CLOSED_EXPOSURES, GAP_INTENT
from gatekeeper.models import AnswerHistory, GapRow, QuestionPlan, QuestionSlot, StateGrid
from gatekeeper.phrasing_brief import build_probe_brief

from gatekeeper.derive import derive_coaching, open_gaps
from gatekeeper.rank import rank_open_gaps

DEFAULT_MAX_BATCH = 1


def max_batch_size() -> int:
    raw = os.environ.get("MAX_BATCH_SIZE", "1")
    try:
        return max(1, min(13, int(raw)))
    except ValueError:
        return DEFAULT_MAX_BATCH


def _off_angle_primary(grid: StateGrid) -> GapRow | None:
    for row in grid.all_rows():
        if row.exposure == "X8":
            return row
    if grid.extras:
        return grid.extras[0]
    return None


def _slot_candidates(
    grid: StateGrid,
    assessment: DiscoveryAssessment,
) -> list[tuple[WeaknessItem | None, GapRow, str, str]]:
    """(weakness, row, role, concern_label) in probe order, deduped by gap."""
    out: list[tuple[WeaknessItem | None, GapRow, str, str]] = []
    seen: set[str] = set()

    off = _off_angle_primary(grid)
    if off and off.exposure == "X8":
        out.append(
            (
                None,
                off,
                "off_angle",
                f"Off-angle: {GAP_INTENT.get(off.gap, off.gap)}",
            )
        )
        seen.add(off.gap)

    for i, w in enumerate(assessment.weaknesses):
        row = grid.rows.get(w.primary_gap)
        if not row or w.primary_gap in seen:
            continue
        role = "primary" if not out else "support"
        out.append((w, row, role, w.label))
        seen.update(w.related_gaps)
        seen.add(w.primary_gap)

    for row in rank_open_gaps(grid):
        if row.gap in seen or row.exposure in CLOSED_EXPOSURES:
            continue
        label = f"{GAP_INTENT.get(row.gap, row.gap)} ({row.gap})"
        out.append((None, row, "support", label))
        seen.add(row.gap)

    return out


def build_question_plan(
    grid: StateGrid,
    *,
    history: AnswerHistory | None = None,
) -> QuestionPlan:
    coaching = derive_coaching(grid)
    history = history or AnswerHistory(pitch="", turns=[])
    assessment = assess_discovery(grid, history)

    if grid.phase in ("P1", "P2", "P4"):
        return QuestionPlan(
            phase=grid.phase,
            slots=[],
            coaching=coaching,
            constraints={
                "mcq_count": 0,
                "message": f"Phase {grid.phase}: no MCQs this turn",
                "assessment": assessment.to_dict(),
            },
        )

    cap = max_batch_size()
    candidates = _slot_candidates(grid, assessment)[:cap]
    slots: list[QuestionSlot] = []

    for i, (weakness, row, role, label) in enumerate(candidates, start=1):
        slot_assessment = assessment
        if role == "support" and weakness:
            slot_assessment = DiscoveryAssessment(
                synthesis=assessment.synthesis,
                weaknesses=assessment.weaknesses,
                primary_gap=row.gap,
                primary_label=label,
                related_gaps=weakness.related_gaps if weakness else [row.gap],
                probe_angle=assessment.probe_angle,
                steering=assessment.steering,
            )
        elif role == "support":
            from gatekeeper.assess import _probe_angle

            slot_assessment = DiscoveryAssessment(
                synthesis=assessment.synthesis,
                weaknesses=assessment.weaknesses,
                primary_gap=row.gap,
                primary_label=label,
                related_gaps=[row.gap],
                probe_angle=_probe_angle(
                    row,
                    history.latest().raw_text if history.latest() else "",
                    history,
                ),
                steering=assessment.steering,
            )

        slots.append(
            QuestionSlot(
                gap=row.gap,
                exposure=row.exposure,
                intent=GAP_INTENT.get(row.gap, ""),
                risk_class=row.risk_class,
                rank=i,
                role=role,
                concern_label=label,
                related_gaps=list(slot_assessment.related_gaps),
                brief=build_probe_brief(
                    row,
                    assessment=slot_assessment,
                    role=role,
                    grid=grid,
                    history=history,
                ),
            )
        )

    open_count = len(open_gaps(grid))
    return QuestionPlan(
        phase=grid.phase,
        slots=slots,
        coaching=coaching,
        constraints={
            "S1": True,
            "S2": True,
            "S3": True,
            "S4": True,
            "Q1": len(slots) <= 1,
            "Q6": open_count < 5,
            "mcq_count": len(slots),
            "gap_slots": len(slots),
            "assessment": assessment.to_dict(),
        },
    )
