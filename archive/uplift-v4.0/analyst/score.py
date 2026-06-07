"""Multiply driver × guard codes and rank — steps 4–5."""

from __future__ import annotations

from analyst.guards import killer_code, recency_code
from analyst.models import Candidate, DriverScores, ScoredCandidate
from analyst.routing import dominant_term_and_mode
from analyst.tables import (
    C_MULT,
    COVERAGE_FLOOR_BONUS,
    E_MULT,
    I_MULT,
    K_MULT,
    R_MULT,
)


def compute_score(
    candidate: Candidate,
    drivers: DriverScores,
    *,
    asked_history: dict[str, list[int]],
    current_turn: int,
) -> ScoredCandidate:
    r_code = recency_code(candidate.gap, asked_history, current_turn)
    k_code = killer_code(candidate.gap, candidate.risk_class)

    i_term = I_MULT[drivers.I]
    c_term = C_MULT[drivers.C]
    e_term = E_MULT[drivers.E]
    r_term = R_MULT[r_code]
    k_term = K_MULT[k_code]

    score = i_term * c_term * e_term * r_term * k_term
    if candidate.floor_flag:
        score += COVERAGE_FLOOR_BONUS

    terms = {
        "I": i_term,
        "C": c_term,
        "E": e_term,
        "R": r_term,
        "K": k_term,
    }
    dominant, mode = dominant_term_and_mode(drivers, terms, k_term=k_term)

    return ScoredCandidate(
        gap=candidate.gap,
        intent=candidate.intent,
        score=score,
        drivers=drivers,
        guards={"R": r_code, "K": k_code},
        lock="L0",
        terms=terms,
        dominant_term=dominant,
        mode=mode,
        floor_flag=candidate.floor_flag,
    )


def rank_candidates(scored: list[ScoredCandidate]) -> list[ScoredCandidate]:
    return sorted(scored, key=lambda s: s.score, reverse=True)


def build_suppressed(
    ranked: list[ScoredCandidate],
    *,
    primary_gap: str,
) -> list[dict[str, str]]:
    suppressed: list[dict[str, str]] = []
    for item in ranked:
        if item.gap == primary_gap:
            continue
        reason_parts: list[str] = []
        if item.guards["R"] == "R3":
            reason_parts.append("R3 — asked last turn — score annihilated")
        elif item.guards["R"] == "R2":
            reason_parts.append("R2 — asked recently")
        if item.score < 1.0:
            reason_parts.append(f"score {item.score:.3f}")
        if not reason_parts:
            reason_parts.append(f"below primary threshold (score {item.score:.3f})")
        suppressed.append({"gap": item.gap, "reason": "; ".join(reason_parts)})
    return suppressed
