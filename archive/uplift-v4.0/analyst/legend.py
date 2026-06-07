"""Gap taxonomy for discovery — structural labels only (not the multiplier rubric)."""

from __future__ import annotations

CANONICAL_GAPS: tuple[str, ...] = (
    "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9",
    "GA", "GB", "GC", "GD",
)

LOCKED_EXPOSURES: frozenset[str] = frozenset({"X3", "X5"})
OPEN_EXPOSURES: frozenset[str] = frozenset(
    {"X1", "X2", "X4", "X6", "X7", "X8", "X9"}
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

TRUST_SAFETY_GAPS: frozenset[str] = frozenset({"G7", "G8", "GA", "GB", "GC", "GD"})

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
}
