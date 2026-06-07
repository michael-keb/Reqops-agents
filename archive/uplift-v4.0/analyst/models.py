"""Data models for Uplift 4.0."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Exposure = Literal["X1", "X2", "X3", "X4", "X5", "X6", "X7", "X8", "X9"]

DriverCode = Literal["I0", "I1", "I2", "I3", "C0", "C1", "C2", "C3", "E0", "E1", "E2", "E3", "E4"]
GuardRecency = Literal["R0", "R1", "R2", "R3"]
GuardKiller = Literal["K0", "K1", "K2"]
LockCode = Literal["L0", "L2", "L3"]
QuestionMode = Literal[
    "FOLLOW",
    "CONFRONT",
    "PROBE_SEAM",
    "REASK_NARROWER",
    "CHALLENGE_GROUNDS",
    "COVERAGE",
    "INTAKE",
]


@dataclass
class UserTurn:
    turn: int
    raw_text: str


@dataclass
class AnswerHistory:
    pitch: str
    turns: list[UserTurn]

    def latest(self) -> UserTurn | None:
        return self.turns[-1] if self.turns else None

    def full_text(self) -> str:
        parts = [f"PITCH: {self.pitch}"]
        for t in self.turns:
            parts.append(f"T{t.turn}: {t.raw_text}")
        return "\n\n".join(parts)


@dataclass
class DetectHint:
    gap: str
    kind: Literal["contradiction", "off_angle"]
    reason: str
    suggested_exposure: Exposure = "X6"


@dataclass
class GapRow:
    gap: str
    exposure: Exposure
    evidence_turns: list[int] = field(default_factory=list)
    evidence_snippets: list[str] = field(default_factory=list)
    risk_class: str = ""
    locked_by: str | None = None
    locked_turn: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StateGrid:
    turn: int
    rows: dict[str, GapRow]
    extras: list[GapRow] = field(default_factory=list)

    def all_rows(self) -> list[GapRow]:
        return list(self.rows.values()) + self.extras

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn": self.turn,
            "rows": {k: v.to_dict() for k, v in self.rows.items()},
            "extras": [e.to_dict() for e in self.extras],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


@dataclass
class Candidate:
    gap: str
    intent: str
    exposure: Exposure
    risk_class: str
    evidence_snippets: list[str] = field(default_factory=list)
    locked_by: str | None = None
    floor_flag: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DriverScores:
    I: DriverCode
    C: DriverCode
    E: DriverCode
    why_now: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"I": self.I, "C": self.C, "E": self.E, "why_now": self.why_now}


@dataclass
class ScoredCandidate:
    gap: str
    intent: str
    score: float
    drivers: DriverScores
    guards: dict[str, str]
    lock: LockCode
    terms: dict[str, float]
    dominant_term: str
    mode: QuestionMode
    floor_flag: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "gap": self.gap,
            "intent": self.intent,
            "score": round(self.score, 4),
            "codes": {
                **self.drivers.to_dict(),
                "R": self.guards["R"],
                "K": self.guards["K"],
                "L": self.lock,
            },
            "terms": {k: round(v, 4) for k, v in self.terms.items()},
            "dominant_term": self.dominant_term,
            "mode": self.mode,
            "floor_flag": self.floor_flag,
        }


@dataclass
class TurnSelection:
    turn: int
    primary: ScoredCandidate | None
    support: ScoredCandidate | None
    ranked: list[dict[str, Any]]
    vetoed: list[dict[str, str]]
    suppressed: list[dict[str, str]]
    intake: bool = False
    intake_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        primary = None
        if self.primary:
            primary = {
                "gap": self.primary.gap,
                "score": round(self.primary.score, 4),
                "mode": self.primary.mode,
                "dominant_term": self.primary.dominant_term,
                "codes": {
                    "I": self.primary.drivers.I,
                    "C": self.primary.drivers.C,
                    "E": self.primary.drivers.E,
                    "R": self.primary.guards["R"],
                    "K": self.primary.guards["K"],
                    "L": self.primary.lock,
                },
                "why_now": self.primary.drivers.why_now,
                "question_intent": (
                    self.primary.drivers.why_now.strip()
                    or f"{self.primary.mode} probe on {self.primary.gap}"
                ),
            }
        return {
            "turn": self.turn,
            "primary": primary,
            "support": None,
            "ranked": self.ranked,
            "vetoed": self.vetoed,
            "suppressed": self.suppressed,
            "intake": self.intake,
            "intake_message": self.intake_message,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


@dataclass
class TurnPipelineResult:
    history: AnswerHistory
    grid: StateGrid
    selection: TurnSelection
    candidates_scored: list[ScoredCandidate]
