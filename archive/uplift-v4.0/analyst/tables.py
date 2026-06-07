"""Multiplier lookup tables — numeric only. See llm_rubric_multiplier.md for semantics."""

from __future__ import annotations

from analyst.models import DriverCode, GuardKiller, GuardRecency

I_MULT: dict[str, float] = {"I0": 1.0, "I1": 2.0, "I2": 4.0, "I3": 6.0}
C_MULT: dict[str, float] = {"C0": 1.0, "C1": 1.0, "C2": 3.5, "C3": 5.0}
E_MULT: dict[str, float] = {"E0": 1.0, "E1": 1.5, "E2": 0.8, "E3": 0.4, "E4": 2.5}
R_MULT: dict[str, float] = {"R0": 1.0, "R1": 1.0, "R2": 0.3, "R3": 0.02}
K_MULT: dict[str, float] = {"K0": 1.0, "K1": 1.3, "K2": 1.6}

COVERAGE_FLOOR_BONUS: float = 5.0
COVERAGE_FLOOR_TURNS: int = 4

VALID_I: frozenset[str] = frozenset(I_MULT)
VALID_C: frozenset[str] = frozenset(C_MULT)
VALID_E: frozenset[str] = frozenset(E_MULT)


def driver_multiplier(code: DriverCode) -> float:
    prefix = code[0]
    if prefix == "I":
        return I_MULT[code]
    if prefix == "C":
        return C_MULT[code]
    return E_MULT[code]


def guard_multiplier(r: GuardRecency, k: GuardKiller) -> float:
    return R_MULT[r] * K_MULT[k]
