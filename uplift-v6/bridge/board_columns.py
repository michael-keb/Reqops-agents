"""Fixed board columns for conversation → card extraction."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BoardColumn:
    id: str
    title: str
    purpose: str
    question: str
    target_cards: int
    slug: str

    @property
    def description(self) -> str:
        return f"{self.purpose} {self.question}"


BOARD_COLUMNS: tuple[BoardColumn, ...] = (
    BoardColumn(
        id="goal",
        title="Goal",
        purpose="Define what success looks like.",
        question="What do we want to become true?",
        target_cards=2,
        slug="goal",
    ),
    BoardColumn(
        id="actor",
        title="Actor",
        purpose="Identify people, systems, or groups involved.",
        question="Who is involved, impacted, responsible, or affected?",
        target_cards=2,
        slug="actor",
    ),
    BoardColumn(
        id="solution",
        title="Solution",
        purpose="Capture candidate actions, ideas, or interventions.",
        question="What possible solutions or moves could address this?",
        target_cards=3,
        slug="solution",
    ),
    BoardColumn(
        id="mechanism",
        title="Mechanism",
        purpose="Explain how the solution actually works.",
        question="What is happening under the hood?",
        target_cards=3,
        slug="mechanism",
    ),
    BoardColumn(
        id="inputs",
        title="Inputs",
        purpose="Identify what flows into the system.",
        question="What data, signals, triggers, or resources are required?",
        target_cards=2,
        slug="inputs",
    ),
    BoardColumn(
        id="outputs",
        title="Outputs",
        purpose="Define what the system produces.",
        question="What artefacts, decisions, or results come out?",
        target_cards=2,
        slug="outputs",
    ),
    BoardColumn(
        id="risk",
        title="Risk",
        purpose="Identify failure points or blockers.",
        question="What could fail, break, slow down, or create risk?",
        target_cards=2,
        slug="risk",
    ),
    BoardColumn(
        id="constraint",
        title="Constraint",
        purpose="Capture immovable boundaries.",
        question="What hard limits or non-negotiable conditions exist?",
        target_cards=2,
        slug="constraint",
    ),
    BoardColumn(
        id="unknown_tradeoff",
        title="Unknown / Tradeoff",
        purpose="Surface uncertainty and competing priorities.",
        question="What is still unknown, unresolved, or requires compromise?",
        target_cards=2,
        slug="unknown-tradeoff",
    ),
)


COLUMN_BY_ID = {c.id: c for c in BOARD_COLUMNS}
