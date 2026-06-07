"""Derive phase, leverage, readiness, and shaping from grid."""

from __future__ import annotations

from gatekeeper.legend import CANONICAL_GAPS, HIGH_PRIORITY_KILLERS, OPEN_EXPOSURES, RISK_CLASS
from gatekeeper.models import AnswerHistory, GapRow, Phase, StateGrid


def open_gaps(grid: StateGrid) -> list[GapRow]:
    return [r for r in grid.all_rows() if r.exposure in OPEN_EXPOSURES]


def _killer_open(grid: StateGrid) -> bool:
    return any(
        r.risk_class in HIGH_PRIORITY_KILLERS and r.exposure in OPEN_EXPOSURES
        for r in grid.all_rows()
    )


def _any_exposure(grid: StateGrid, exp: str) -> bool:
    return any(r.exposure == exp for r in grid.all_rows())


def derive_phase(grid: StateGrid, history: AnswerHistory) -> Phase:
    if not open_gaps(grid):
        return "P4"
    if len(history.turns) == 1 and len(history.turns[0].raw_text) < 80:
        return "P1"
    return "P3"


def derive_leverage(grid: StateGrid) -> list[str]:
    codes: list[str] = []
    opens = open_gaps(grid)
    if not opens:
        codes.append("L6")
        return codes
    if _killer_open(grid):
        codes.append("L1")
    if _any_exposure(grid, "X4"):
        codes.append("L3")
    if _any_exposure(grid, "X6"):
        codes.append("L4")
    if _any_exposure(grid, "X2"):
        codes.append("L5")
    return codes


def derive_readiness(grid: StateGrid) -> list[str]:
    codes: list[str] = []
    opens = open_gaps(grid)
    if opens:
        codes.append("R1")
    if _any_exposure(grid, "X4") or _any_exposure(grid, "X6"):
        codes.append("R3")
    if _killer_open(grid):
        codes.append("R4")

    settled = sum(
        1 for g in CANONICAL_GAPS
        if grid.rows[g].exposure in ("X3", "X5")
    )
    killers_ok = all(
        grid.rows[g].exposure in ("X3", "X5")
        for g in CANONICAL_GAPS
        if RISK_CLASS[g] in HIGH_PRIORITY_KILLERS
    )
    if settled >= 12 and killers_ok and not opens:
        codes.append("R5")

    return codes


def derive_shaping(grid: StateGrid) -> list[str]:
    codes = ["S1", "S3"]
    if _any_exposure(grid, "X2"):
        codes.append("S2")
    if _any_exposure(grid, "X2"):
        pass  # C2 is coaching hint, not S
    if any(r.exposure in OPEN_EXPOSURES for r in grid.all_rows()):
        codes.append("S2")
    return sorted(set(codes), key=codes.index)


def derive_coaching(grid: StateGrid) -> list[str]:
    if grid.phase == "P1":
        return ["C1", "C4"]
    if grid.phase == "P2":
        return ["C1", "C5"]
    coaching = ["C1"]
    if _any_exposure(grid, "X2"):
        coaching.append("C2")
    if any(r.exposure == "X5" for r in grid.all_rows()):
        coaching.append("C3")
    return coaching


def derive_batch_flags(grid: StateGrid, open_count: int) -> list[str]:
    flags: list[str] = []
    if grid.phase == "P3":
        if open_count < 5:
            flags.append("Q6")
        flags.append("Q7")
        flags.append("Q5")
        flags.append("Q3")
        flags.append("Q2")
    return flags


def enrich_grid(grid: StateGrid, history: AnswerHistory) -> StateGrid:
    grid.phase = derive_phase(grid, history)
    grid.leverage = derive_leverage(grid)
    grid.readiness = derive_readiness(grid)
    grid.shaping = derive_shaping(grid)
    grid.batch = derive_batch_flags(grid, len(open_gaps(grid)))
    return grid
