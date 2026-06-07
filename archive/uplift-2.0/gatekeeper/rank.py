"""Rank open gaps by leverage."""

from __future__ import annotations

from gatekeeper.legend import EXPOSURE_RANK, GAP_INTENT, KILLER_RANK, UNLOCK_WEIGHT
from gatekeeper.models import GapRow, StateGrid

from gatekeeper.derive import open_gaps


def rank_key(row: GapRow) -> tuple[int, int, int, str]:
    return (
        EXPOSURE_RANK.get(row.exposure, 99),
        KILLER_RANK.get(row.risk_class, 99),
        -UNLOCK_WEIGHT.get(row.gap, 0),
        row.gap,
    )


def rank_open_gaps(grid: StateGrid) -> list[GapRow]:
    opens = open_gaps(grid)
    return sorted(opens, key=rank_key)
