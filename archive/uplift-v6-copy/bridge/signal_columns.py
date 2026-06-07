"""Fixed signal-board columns — mirrors ReqOps SignalColumnId wire enum."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SignalColumn:
    id: str
    title: str
    purpose: str
    question: str
    node_type: str
    slug: str

    @property
    def definition(self) -> str:
        return self.purpose


SIGNAL_COLUMNS: tuple[SignalColumn, ...] = (
    SignalColumn(
        id="goal",
        title="Goal",
        purpose="What we want to be true (outcomes, targets, north stars).",
        question="What do we want to become true?",
        node_type="goal",
        slug="goal",
    ),
    SignalColumn(
        id="actor",
        title="Actor",
        purpose="People, roles, or systems involved or affected.",
        question="Who is involved, impacted, responsible, or affected?",
        node_type="actor",
        slug="actor",
    ),
    SignalColumn(
        id="solution",
        title="Solution",
        purpose="Candidate solutions, paths, or moves.",
        question="What possible solutions or moves could address this?",
        node_type="solution",
        slug="solution",
    ),
    SignalColumn(
        id="mechanism",
        title="Mechanism",
        purpose="How the work delivers — moving parts under the hood.",
        question="What is happening under the hood?",
        node_type="mechanism",
        slug="mechanism",
    ),
    SignalColumn(
        id="inputs",
        title="Inputs",
        purpose="Data, signals, content, triggers — what feeds the work.",
        question="What data, signals, triggers, or resources are required?",
        node_type="input",
        slug="inputs",
    ),
    SignalColumn(
        id="outputs",
        title="Outputs",
        purpose="Concrete artefacts or results the work produces.",
        question="What artefacts, decisions, or results come out?",
        node_type="output",
        slug="outputs",
    ),
    SignalColumn(
        id="risk",
        title="Risk",
        purpose="Ways the plan could fail or side-effects to guard against.",
        question="What could fail, break, slow down, or create risk?",
        node_type="risk",
        slug="risk",
    ),
    SignalColumn(
        id="constraint",
        title="Constraint",
        purpose="Hard limits (time, money, policy, capability) we cannot move.",
        question="What hard limits or non-negotiable conditions exist?",
        node_type="constraint",
        slug="constraint",
    ),
    SignalColumn(
        id="unknown",
        title="Unknown / Tradeoff",
        purpose="Open unknowns or trade-offs we still need to resolve.",
        question="What is still unknown, unresolved, or requires compromise?",
        node_type="unknown",
        slug="unknown",
    ),
)


COLUMN_BY_ID = {c.id: c for c in SIGNAL_COLUMNS}
