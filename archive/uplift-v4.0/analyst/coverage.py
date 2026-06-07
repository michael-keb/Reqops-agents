"""Coverage floor — additive safety net outside the product (QF)."""

from __future__ import annotations

from analyst.legend import CANONICAL_GAPS, KILLER_CLASSES, LOCKED_EXPOSURES, OPEN_EXPOSURES
from analyst.models import StateGrid
from analyst.tables import COVERAGE_FLOOR_TURNS


def apply_coverage_floor(
    grid: StateGrid,
    *,
    asked_history: dict[str, list[int]],
    current_turn: int,
) -> dict[str, bool]:
    """Return gap → floor_flag for killer-class gaps untouched ≥ N turns."""
    flags: dict[str, bool] = {}
    for gap in CANONICAL_GAPS:
        row = grid.rows[gap]
        if row.risk_class not in KILLER_CLASSES:
            continue
        if row.exposure in LOCKED_EXPOSURES:
            continue
        if row.exposure not in OPEN_EXPOSURES:
            continue
        asked = asked_history.get(gap, [])
        if asked:
            continue
        if current_turn >= COVERAGE_FLOOR_TURNS:
            flags[gap] = True
    return flags
