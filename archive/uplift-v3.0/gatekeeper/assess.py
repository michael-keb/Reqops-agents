"""Assess discovery weaknesses from user history — steer probes, not gap checklists."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from gatekeeper.classify import GAP_SIGNALS
from gatekeeper.legend import CLOSED_EXPOSURES, GAP_INTENT, KILLER_RANK
from gatekeeper.models import AnswerHistory, GapRow, StateGrid

from gatekeeper.derive import open_gaps
from gatekeeper.rank import rank_open_gaps

OPS_CLUSTER = frozenset({"G7", "GA", "GB", "GC", "GD"})
FEAR_SPIKE = re.compile(
    r"\b("
    r"biggest risk|nightmare|won't ship|wor't ship|existential|"
    r"worst case|optimi[sz]e for .+ over|fraud prevention over"
    r")\b",
    re.I,
)
EXPOSURE_URGENCY: dict[str, int] = {
    "X6": 100,
    "X4": 85,
    "X8": 80,
    "X7": 70,
    "X2": 65,
    "X9": 60,
    "X1": 50,
}


@dataclass
class WeaknessItem:
    label: str
    primary_gap: str
    related_gaps: list[str]
    reason: str
    killer: str
    exposure: str
    score: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DiscoveryAssessment:
    synthesis: list[str]
    weaknesses: list[WeaknessItem]
    primary_gap: str
    primary_label: str
    related_gaps: list[str]
    probe_angle: str
    steering: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "synthesis": self.synthesis,
            "weaknesses": [w.to_dict() for w in self.weaknesses],
            "primary_gap": self.primary_gap,
            "primary_label": self.primary_label,
            "related_gaps": self.related_gaps,
            "probe_angle": self.probe_angle,
            "steering": self.steering,
        }


def _ops_cluster_open(opens: list[GapRow]) -> list[GapRow]:
    return [r for r in opens if r.gap in OPS_CLUSTER]


def _weakness_reason(row: GapRow, latest_text: str) -> str:
    exposure_notes = {
        "X1": "Never materially resolved — still unknown.",
        "X2": "Mentioned but thin — needs stress-test, not acceptance.",
        "X4": "Inferred, not user-committed — needs confirming fork.",
        "X6": "Contradiction — needs reconciliation.",
        "X7": "New risk surfaced — urgent.",
        "X8": "Off-angle concern user raised — prioritize over generic gaps.",
        "X9": "Prior question outstanding — answer may not have qualified yet.",
    }
    base = exposure_notes.get(row.exposure, f"Exposure {row.exposure}.")
    if latest_text and row.evidence_snippets:
        snippet = row.evidence_snippets[-1][:100]
        if snippet.lower() in latest_text.lower()[:200]:
            base += " User touched this in their latest message."
    return base


def _score_weakness(row: GapRow, latest_text: str) -> int:
    score = EXPOSURE_URGENCY.get(row.exposure, 40)
    score += max(0, (8 - KILLER_RANK.get(row.risk_class, 8)) * 6)
    if row.exposure == "X2":
        score += 12
    lower = latest_text.lower()
    if lower and any(sig in lower for sig in GAP_SIGNALS.get(row.gap, ())):
        score += 18
    if row.gap == "GD" and FEAR_SPIKE.search(latest_text):
        score += 25
    return score


def _probe_angle(row: GapRow, latest_text: str, history: AnswerHistory) -> str:
    intent = GAP_INTENT.get(row.gap, row.gap)
    if row.exposure == "X2":
        return (
            f"Pin down what they implied about {intent} — use a counterfactual or "
            f"scenario tied to their latest message; do not accept category nouns alone."
        )
    if row.exposure == "X4":
        return (
            f"Confirm the fork they have not explicitly locked for {intent} — "
            f"one atomic decision, not exploration."
        )
    if row.exposure == "X8":
        return (
            "Follow the concern they volunteered that other gaps did not cover — "
            "name it in their words."
        )
    if row.gap in OPS_CLUSTER:
        return (
            "Under their stated harm/fraud concern: who acts, how fast, what the user sees "
            "when something goes wrong — mechanism not 'trust features'."
        )
    if row.gap == "G5":
        return (
            "Extract a falsifiable success or kill signal with threshold and consequence — "
            "not a vanity metric."
        )
    if row.gap == "G4":
        return (
            "Walk the core path in verbs — include silent-failure detection without surveying."
        )
    return (
        f"Attack the greatest weakness in {intent} for this product — "
        f"ground in: \"{latest_text[:120]}{'…' if len(latest_text) > 120 else ''}\""
        if latest_text
        else f"Open first concrete fork on {intent}."
    )


def _build_ops_cluster_weakness(
    ops_rows: list[GapRow], latest_text: str
) -> WeaknessItem:
    priority = ("GD", "G8", "GB", "GC", "G7", "GA")
    primary = ops_rows[0]
    for g in priority:
        for row in ops_rows:
            if row.gap == g:
                primary = row
                break
    related = sorted({r.gap for r in ops_rows})
    score = max(_score_weakness(r, latest_text) for r in ops_rows) + 10
    return WeaknessItem(
        label="Live ops / participant harm — binding rules still thin",
        primary_gap=primary.gap,
        related_gaps=related,
        reason=(
            f"Overlapping governance/trust gaps ({', '.join(related)}) share one user concern — "
            "probe once with Q8 collapse, not parallel menus."
        ),
        killer=primary.risk_class or "TRUST_SAFETY",
        exposure=primary.exposure,
        score=score,
    )


def assess_discovery(grid: StateGrid, history: AnswerHistory) -> DiscoveryAssessment:
    latest = history.latest()
    latest_text = (latest.raw_text if latest else "").strip()
    opens = open_gaps(grid)

    settled = sum(
        1 for row in grid.rows.values() if row.exposure in CLOSED_EXPOSURES
    )
    synthesis = [
        f"Pitch: {history.pitch[:160]}",
        f"Conversation turns: {len(history.turns)} · substantively settled: {settled}/13",
    ]
    if latest_text:
        synthesis.append(
            f"Latest input ({len(latest_text)} chars): review for assumptions vs locked facts."
        )

    weaknesses: list[WeaknessItem] = []
    skip: set[str] = set()

    ops = _ops_cluster_open(opens)
    if len(ops) >= 2:
        cluster = _build_ops_cluster_weakness(ops, latest_text)
        weaknesses.append(cluster)
        skip = OPS_CLUSTER - {cluster.primary_gap}

    for row in rank_open_gaps(grid):
        if row.gap in skip:
            continue
        if row.exposure in CLOSED_EXPOSURES:
            continue
        weaknesses.append(
            WeaknessItem(
                label=f"{GAP_INTENT.get(row.gap, row.gap)} ({row.gap})",
                primary_gap=row.gap,
                related_gaps=[row.gap],
                reason=_weakness_reason(row, latest_text),
                killer=row.risk_class,
                exposure=row.exposure,
                score=_score_weakness(row, latest_text),
            )
        )

    weaknesses.sort(key=lambda w: w.score, reverse=True)
    weaknesses = weaknesses[:3]

    steering = list(grid.leverage)
    if FEAR_SPIKE.search(latest_text) and "L4" not in steering:
        steering.insert(0, "L4")
    if len(ops) >= 2 and "Q8" not in steering:
        steering.append("Q8")
    if "Q1" not in steering and grid.phase == "P3":
        steering.append("Q1")

    if not weaknesses:
        primary_gap = "G1"
        primary_label = "Discovery just starting"
        related = ["G1"]
        probe = "Invite concrete user segment and excluded segment before feature talk."
    else:
        top = weaknesses[0]
        primary_gap = top.primary_gap
        primary_label = top.label
        related = top.related_gaps
        probe = _probe_angle(grid.rows[primary_gap], latest_text, history)

    return DiscoveryAssessment(
        synthesis=synthesis,
        weaknesses=weaknesses,
        primary_gap=primary_gap,
        primary_label=primary_label,
        related_gaps=related,
        probe_angle=probe,
        steering=steering,
    )
