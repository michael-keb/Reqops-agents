"""Gatekeeper data models."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Exposure = Literal["X1", "X2", "X3", "X4", "X5", "X6", "X7", "X8", "X9"]
Phase = Literal["P1", "P2", "P3", "P4"]


@dataclass
class UserTurn:
    turn: int
    raw_text: str


@dataclass
class AnswerHistory:
    pitch: str
    turns: list[UserTurn]

    def full_text(self) -> str:
        parts = [f"PITCH: {self.pitch}"]
        for t in self.turns:
            parts.append(f"T{t.turn}: {t.raw_text}")
        return "\n\n".join(parts)

    def latest(self) -> UserTurn | None:
        return self.turns[-1] if self.turns else None


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
    sub_gap: str | None = None
    locked_by: str | None = None
    locked_turn: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StateGrid:
    turn: int
    rows: dict[str, GapRow]
    extras: list[GapRow] = field(default_factory=list)
    phase: Phase = "P3"
    leverage: list[str] = field(default_factory=list)
    readiness: list[str] = field(default_factory=list)
    shaping: list[str] = field(default_factory=list)
    batch: list[str] = field(default_factory=list)

    def all_rows(self) -> list[GapRow]:
        return list(self.rows.values()) + self.extras

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn": self.turn,
            "phase": self.phase,
            "rows": {k: v.to_dict() for k, v in self.rows.items()},
            "extras": [e.to_dict() for e in self.extras],
            "leverage": self.leverage,
            "readiness": self.readiness,
            "shaping": self.shaping,
            "batch": self.batch,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


@dataclass
class QuestionSlot:
    gap: str
    exposure: Exposure
    intent: str
    risk_class: str
    rank: int
    role: str = "primary"
    concern_label: str = ""
    related_gaps: list[str] = field(default_factory=list)
    is_q7_probe: bool = False
    brief: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QuestionPlan:
    phase: str
    slots: list[QuestionSlot]
    coaching: list[str] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "slots": [s.to_dict() for s in self.slots],
            "coaching": self.coaching,
            "constraints": self.constraints,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @classmethod
    def success(cls, warnings: list[str] | None = None) -> ValidationResult:
        return cls(ok=True, warnings=warnings or [])

    @classmethod
    def failure(cls, *errors: str) -> ValidationResult:
        return cls(ok=False, errors=list(errors))


@dataclass
class TurnPipelineResult:
    history: AnswerHistory
    grid: StateGrid
    plan: QuestionPlan
    code_line: str
    open_gaps: list[GapRow]
