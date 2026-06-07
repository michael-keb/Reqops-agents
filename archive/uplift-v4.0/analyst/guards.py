"""Deterministic guard codes — R and K (step 3)."""

from __future__ import annotations

from analyst.legend import KILLER_CLASSES, TRUST_SAFETY_GAPS
from analyst.models import GuardKiller, GuardRecency


def killer_code(gap: str, risk_class: str) -> GuardKiller:
    if gap in TRUST_SAFETY_GAPS or risk_class == "TRUST_SAFETY":
        return "K2"
    if risk_class in KILLER_CLASSES:
        return "K1"
    return "K0"


def recency_code(gap: str, asked_history: dict[str, list[int]], current_turn: int) -> GuardRecency:
    turns = asked_history.get(gap, [])
    if not turns:
        return "R0"
    last = max(turns)
    delta = current_turn - last
    if delta <= 1:
        return "R3"
    if delta <= 2:
        return "R2"
    if delta >= 3:
        return "R1"
    return "R0"
