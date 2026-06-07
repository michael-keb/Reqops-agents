"""Canonical discovery state codes (v0.3 — aligns with llm-rubric_v2.md)."""

from __future__ import annotations

CANONICAL_GAPS: tuple[str, ...] = (
    "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9",
    "GA", "GB", "GC", "GD",
)

GAP_ORDER: tuple[str, ...] = CANONICAL_GAPS

EXPOSURES: frozenset[str] = frozenset(
    {"X1", "X2", "X3", "X4", "X5", "X6", "X7", "X8", "X9"}
)

OPEN_EXPOSURES: frozenset[str] = frozenset(
    {"X1", "X2", "X4", "X6", "X7", "X8", "X9"}
)

CLOSED_EXPOSURES: frozenset[str] = frozenset({"X3", "X5"})

PHASES: frozenset[str] = frozenset({"P1", "P2", "P3", "P4"})

LEVERAGE: frozenset[str] = frozenset(
    {"L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8"}
)

READINESS: frozenset[str] = frozenset({"R1", "R2", "R3", "R4", "R5", "R6"})

SHAPING: frozenset[str] = frozenset({"S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"})

BATCH: frozenset[str] = frozenset({"Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"})

COACHING: frozenset[str] = frozenset({"C1", "C2", "C3", "C4", "C5", "C6", "C7"})

GAP_CODES: frozenset[str] = frozenset(CANONICAL_GAPS) | {"G0"}

ALL_BEHAVIOURAL: frozenset[str] = (
    GAP_CODES | PHASES | LEVERAGE | READINESS | SHAPING | BATCH | COACHING
)

RISK_CLASS: dict[str, str] = {
    "G1": "WRONG_THING",
    "G2": "WRONG_THING",
    "G3": "BOUNDLESS",
    "G4": "BOUNDLESS",
    "G5": "UNMEASURABLE",
    "G6": "BOUNDLESS",
    "G7": "UNGOVERNED",
    "G8": "FRAGILE",
    "G9": "BOUNDLESS",
    "GA": "BUILT_ON_SAND",
    "GB": "UNGOVERNED",
    "GC": "UNGOVERNED",
    "GD": "TRUST_SAFETY",
    "G0": "UNKNOWN",
}

KILLER_CLASSES: frozenset[str] = frozenset(
    {
        "WRONG_THING",
        "BOUNDLESS",
        "UNMEASURABLE",
        "FRAGILE",
        "BUILT_ON_SAND",
        "UNGOVERNED",
        "TRUST_SAFETY",
    }
)

HIGH_PRIORITY_KILLERS: frozenset[str] = frozenset(
    {"WRONG_THING", "BOUNDLESS", "TRUST_SAFETY"}
)

GAP_INTENT: dict[str, str] = {
    "G1": "who exactly, concretely",
    "G2": "what job, measurably",
    "G3": "how use begins",
    "G4": "the one core path",
    "G5": "what proves it worked",
    "G6": "in vs out, v1",
    "G7": "what constraint binds",
    "G8": "what happens broken",
    "G9": "which competing option",
    "GA": "believe vs proven",
    "GB": "how it operates live",
    "GC": "where humans intervene",
    "GD": "how participants are protected",
    "G0": "unnamed risk — name it",
}

# Gaps that unlock several dimensions when closed (L2 heuristic).
UNLOCK_WEIGHT: dict[str, int] = {
    "G1": 3,
    "G4": 3,
    "G6": 3,
    "G2": 2,
    "G5": 2,
    "G8": 2,
    "GD": 2,
    "G3": 1,
    "G7": 1,
    "G9": 1,
    "GA": 1,
    "GB": 1,
    "GC": 1,
    "G0": 1,
}

EXPOSURE_RANK: dict[str, int] = {
    "X6": 0,
    "X4": 1,
    "X1": 2,
    "X8": 3,
    "X2": 4,
    "X7": 5,
    "X9": 5,
    "X3": 6,
    "X5": 7,
}

KILLER_RANK: dict[str, int] = {
    "WRONG_THING": 0,
    "TRUST_SAFETY": 1,
    "BOUNDLESS": 2,
    "FRAGILE": 3,
    "BUILT_ON_SAND": 4,
    "UNGOVERNED": 5,
    "UNMEASURABLE": 6,
    "UNKNOWN": 7,
}
