"""Heuristic per-gap classifier from user answer history."""

from __future__ import annotations

import re

from gatekeeper.detect import detect_changes
from gatekeeper.legend import CANONICAL_GAPS, GAP_INTENT, RISK_CLASS
from gatekeeper.models import AnswerHistory, DetectHint, Exposure, GapRow, StateGrid

# Keyword signals per gap (lowercase match).
GAP_SIGNALS: dict[str, tuple[str, ...]] = {
    "G1": (
        "user", "users", "target", "seller", "buyer", "primary users",
        "who ", "audience", "customer", "dealership",
    ),
    "G2": (
        "outcome", "job to be done", "goal", "purpose", "problem",
        "marketplace", "connecting",
    ),
    "G3": (
        "entry", "first action", "start", "create a listing", "browse",
        "onboard", "sign up", "landing",
    ),
    "G4": (
        "workflow", "core path", "contact", "chat", "handoff", "search listings",
        "negotiation", "transaction flow", "deal is done",
    ),
    "G5": (
        "success", "metric", "proves", "completed sale", "marks sold",
        "relist", "within 30 days", "kpi",
    ),
    "G6": (
        "scope", "v1", "mvp", "out of scope", "in scope", "include",
        "financing", "shipping", "inspection", "dealer",
    ),
    "G7": (
        "rule", "constraint", "verification", "policy", "regulation",
        "domain", "compliance", "report listing",
    ),
    "G8": (
        "failure", "broken", "edge case", "what happens if", "scam",
        "fraud", "unsafe", "risk to avoid",
    ),
    "G9": (
        "tradeoff", " vs ", "instead", "option", "competing", "manual negotiation",
        "auction", "automated",
    ),
    "GA": (
        "assume", "believe", "probably", "likely", "think that",
    ),
    "GB": (
        "runtime", "operates live", "production", "moderation queue",
    ),
    "GC": (
        "human review", "intervene", "manual review", "support team",
    ),
    "GD": (
        "trust", "safety", "fraud prevention", "unsafe meetup", "protect",
        "bad actor", "scam", "verify seller",
    ),
}

X5_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bsuccess means\b", re.I),
    re.compile(r"\bout of scope for v1\b", re.I),
    re.compile(r"\b(never|only|must not|will not)\b", re.I),
    re.compile(r"\bprimary users:\b", re.I),
    re.compile(r"\bbiggest risk to avoid:\b", re.I),
    re.compile(r"\boptimise for .+ over\b", re.I),
)

X2_HEDGE = re.compile(
    r"\b(maybe|probably|light|some|might|could|roughly|basic)\b", re.I
)

# UI / harness submit picks as `Gx: <chosen option text>` — treat as direct gap closure.
_GAP_ANSWER_LINE = re.compile(
    r"^(?P<gap>G[1-9]|GA|GB|GC|GD)\s*:\s*(?P<body>.+)$",
    re.I | re.M,
)


def _structured_gap_answers(
    history: AnswerHistory,
) -> dict[str, list[tuple[int, str]]]:
    by_gap: dict[str, list[tuple[int, str]]] = {g: [] for g in CANONICAL_GAPS}
    for t in history.turns:
        for m in _GAP_ANSWER_LINE.finditer(t.raw_text):
            gap = m.group("gap").upper()
            if gap not in CANONICAL_GAPS:
                continue
            body = m.group("body").strip()
            if body:
                by_gap[gap].append((t.turn, body))
    return by_gap


def _text_for_turns(history: AnswerHistory, turn_nums: list[int]) -> str:
    parts = [history.pitch] if 1 in turn_nums or not turn_nums else []
    for t in history.turns:
        if not turn_nums or t.turn in turn_nums:
            parts.append(t.raw_text)
    return "\n".join(parts).lower()


def _find_evidence(
    history: AnswerHistory, gap: str
) -> tuple[list[int], list[str], bool]:
    structured = _structured_gap_answers(history)
    if structured[gap]:
        return (
            [turn for turn, _ in structured[gap]],
            [body[:160] for _, body in structured[gap]],
            True,
        )

    signals = GAP_SIGNALS.get(gap, ())
    turns_hit: list[int] = []
    snippets: list[str] = []
    for t in history.turns:
        lower = t.raw_text.lower()
        if any(sig in lower for sig in signals):
            turns_hit.append(t.turn)
            snippets.append(t.raw_text[:160].strip())
    if not turns_hit and gap in ("G1", "G2") and history.pitch:
        pl = history.pitch.lower()
        if any(sig in pl for sig in signals):
            turns_hit.append(0)
            snippets.append(history.pitch[:160])
    return turns_hit, snippets, False


def _score_exposure(
    gap: str,
    history: AnswerHistory,
    evidence_turns: list[int],
    snippets: list[str],
    hints: list[DetectHint],
    *,
    structured: bool = False,
) -> Exposure:
    for h in hints:
        if h.gap == gap and h.kind == "contradiction":
            return "X6"
        if h.gap == gap and h.kind == "off_angle":
            return "X8"

    if not evidence_turns:
        return "X1"

    combined = " ".join(snippets)

    if structured:
        if any(p.search(combined) for p in X5_PATTERNS):
            if gap == "G5" and "success means" in combined.lower():
                return "X5"
            if gap == "G6" and "out of scope" in combined.lower():
                return "X5"
            if gap == "GD" and re.search(
                r"biggest risk|optimi[sz]e for", combined, re.I
            ):
                return "X5"
        if X2_HEDGE.search(combined):
            return "X2"
        # MCQ pick recorded — await qualifying depth on next turn (not instant close).
        return "X9"

    if any(p.search(combined) for p in X5_PATTERNS):
        if gap == "G5" and "success means" in combined.lower():
            return "X5"
        if gap == "G6" and "out of scope" in combined.lower():
            return "X5"
        if gap == "GD" and re.search(r"scam|fraud|unsafe", combined, re.I):
            if re.search(r"biggest risk|optimi[sz]e for", combined, re.I):
                return "X5"

    if gap == "G5" and re.search(r"success means", combined, re.I):
        if not X2_HEDGE.search(combined):
            return "X3"

    if gap == "G6" and re.search(r"out of scope for v1", combined, re.I):
        if not X2_HEDGE.search(combined):
            return "X3"

    if gap == "G1" and re.search(
        r"primary users:|individuals selling", combined, re.I
    ):
        if not X2_HEDGE.search(combined):
            return "X3"

    if evidence_turns and X2_HEDGE.search(combined):
        return "X2"

    if evidence_turns:
        return "X2"

    return "X1"


def classify_gaps(
    history: AnswerHistory,
    turn: int,
    *,
    prior_grid: StateGrid | None = None,
    hints: list[DetectHint] | None = None,
) -> StateGrid:
    hints = hints if hints is not None else detect_changes(history, prior_grid)
    rows: dict[str, GapRow] = {}

    for gap in CANONICAL_GAPS:
        evidence_turns, snippets, structured = _find_evidence(history, gap)
        exposure = _score_exposure(
            gap,
            history,
            evidence_turns,
            snippets,
            hints,
            structured=structured,
        )
        rows[gap] = GapRow(
            gap=gap,
            exposure=exposure,
            evidence_turns=evidence_turns,
            evidence_snippets=snippets[:3],
            risk_class=RISK_CLASS[gap],
        )

    extras: list[GapRow] = []
    for h in hints:
        if h.gap == "G0" and h.kind == "off_angle":
            extras.append(
                GapRow(
                    gap="G0",
                    exposure="X8",
                    evidence_turns=[history.latest().turn] if history.latest() else [],
                    evidence_snippets=[history.latest().raw_text[:160]] if history.latest() else [],
                    risk_class="UNKNOWN",
                )
            )

    return StateGrid(turn=turn, rows=rows, extras=extras)
