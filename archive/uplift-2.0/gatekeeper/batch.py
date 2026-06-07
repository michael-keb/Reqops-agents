"""Build question plan from ranked open gaps."""

from __future__ import annotations

import os

from gatekeeper.legend import GAP_INTENT
from gatekeeper.models import QuestionPlan, QuestionSlot, StateGrid

from gatekeeper.derive import derive_coaching, open_gaps
from gatekeeper.rank import rank_open_gaps

DEFAULT_MAX_BATCH = 4


def max_batch_size() -> int:
    raw = os.environ.get("MAX_BATCH_SIZE", "4")
    try:
        return max(1, int(raw))
    except ValueError:
        return DEFAULT_MAX_BATCH


def build_question_plan(grid: StateGrid) -> QuestionPlan:
    coaching = derive_coaching(grid)

    if grid.phase in ("P1", "P2", "P4"):
        return QuestionPlan(
            phase=grid.phase,
            slots=[],
            coaching=coaching,
            constraints={
                "mcq_count": 0,
                "message": f"Phase {grid.phase}: no MCQs this turn",
            },
        )

    ranked = rank_open_gaps(grid)
    cap = min(len(ranked), max_batch_size())
    slots: list[QuestionSlot] = []

    for i, row in enumerate(ranked[:cap]):
        slots.append(
            QuestionSlot(
                gap=row.gap,
                exposure=row.exposure,
                intent=GAP_INTENT.get(row.gap, ""),
                risk_class=row.risk_class,
                rank=i + 1,
            )
        )

    slots.append(
        QuestionSlot(
            gap="Q7",
            exposure="X1",
            intent="open probe — valuable question not driven by gap list",
            risk_class="UNKNOWN",
            rank=len(slots) + 1,
            is_q7_probe=True,
        )
    )

    return QuestionPlan(
        phase=grid.phase,
        slots=slots,
        coaching=coaching,
        constraints={
            "S1": True,
            "S2": True,
            "S3": True,
            "S4": True,
            "Q6": len(open_gaps(grid)) < 5,
            "Q7": True,
            "mcq_count": len(slots),
            "gap_slots": cap,
        },
    )
