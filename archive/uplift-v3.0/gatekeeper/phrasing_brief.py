"""Per-slot briefs — one pointed probe from assessment, not a gap checklist."""

from __future__ import annotations

from gatekeeper.assess import DiscoveryAssessment
from gatekeeper.legend import GAP_INTENT
from gatekeeper.models import AnswerHistory, GapRow, StateGrid

_EXPOSURE_NOTE: dict[str, str] = {
    "X1": "unknown — first concrete fork on this concern",
    "X2": "thin — stress-test; do not accept the mention as settled",
    "X4": "inferred — confirm the fork explicitly",
    "X6": "contradiction — ask what the new rule is",
    "X7": "urgent — reference their latest concern",
    "X9": "awaiting depth on a prior answer — sharpen, do not re-paraphrase",
    "X8": "off-angle — follow what they raised",
}


def build_probe_brief(
    row: GapRow,
    *,
    assessment: DiscoveryAssessment,
    role: str,
    grid: StateGrid,
    history: AnswerHistory,
) -> str:
    intent = GAP_INTENT.get(row.gap, row.gap)
    exposure_note = _EXPOSURE_NOTE.get(row.exposure, f"exposure {row.exposure}")
    related = ", ".join(assessment.related_gaps) if assessment.related_gaps else row.gap

    if role == "primary":
        head = (
            f"PRIMARY probe this turn — weakness: {assessment.primary_label}. "
            f"Steering: {', '.join(assessment.steering[:4]) or 'Q1'}."
        )
    elif role == "confirm":
        head = "CONFIRMING probe — user implied but has not locked this fork."
    elif role == "support":
        head = f"SUPPORT probe — secondary weakness: {assessment.primary_label}."
    else:
        head = "OFF-ANGLE probe — user raised something outside the main batch."

    lines = [
        head,
        f"Concern domain {row.gap} ({intent}) · heat: {exposure_note}.",
        f"Related codes for context (do not ask separate menus for each): {related}.",
        f"Probe angle: {assessment.probe_angle}",
        "Ground the stem in NEW USER INPUT above — quote or paraphrase their words.",
        "Use the gap Probe (rubric G section) for depth — apply S6/S8; C2 if thin.",
        "Options A–C are plausible resolutions to test thinking — specific policies, "
        "not generic best practices. Picking one advances evidence; closure is judged "
        "on the user's next answer, not instant.",
        "Respect LOCKED FACTS above — do not re-litigate settled decisions.",
    ]
    if row.evidence_snippets and row.exposure not in ("X1",):
        lines.append(f"Prior evidence: {row.evidence_snippets[-1][:160]}")

    return " ".join(lines)


def build_slot_brief(
    row: GapRow,
    *,
    grid: StateGrid,
    history: AnswerHistory,
    assessment: DiscoveryAssessment | None = None,
    role: str = "primary",
) -> str:
    if assessment is None:
        from gatekeeper.assess import assess_discovery

        assessment = assess_discovery(grid, history)
    return build_probe_brief(
        row, assessment=assessment, role=role, grid=grid, history=history
    )
