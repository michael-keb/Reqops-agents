"""End-to-end turn pipeline — deterministic + LLM scoring + selection."""

from __future__ import annotations

import json
from pathlib import Path

from analyst.candidates import build_candidates
from analyst.grid.classify import classify_gaps
from analyst.grid.detect import detect_changes
from analyst.grid.merge import merge_grid
from analyst.history import build_history_from_session
from analyst.models import (
    AnswerHistory,
    DriverScores,
    ScoredCandidate,
    StateGrid,
    TurnPipelineResult,
    TurnSelection,
)
from analyst.recency import build_asked_history
from analyst.score import build_suppressed, compute_score, rank_candidates
from analyst.scorer_prompt import parse_score_response
from analyst.tables import VALID_C, VALID_E, VALID_I

INTAKE_MIN_CHARS = 80


def _default_drivers(gap: str) -> DriverScores:
    return DriverScores(I="I0", C="C0", E="E0", why_now=f"No LLM score for {gap}")


def _sanitize_driver(code: str, valid: frozenset[str], default: str) -> str:
    c = code.upper().strip()
    return c if c in valid else default


def load_prior_grid(session, turn: int) -> StateGrid | None:
    if turn <= 1:
        return None
    path = session.turn_dir(turn - 1) / "grid.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    from analyst.models import GapRow

    rows = {
        g: GapRow(
            gap=g,
            exposure=r["exposure"],
            evidence_turns=r.get("evidence_turns", []),
            evidence_snippets=r.get("evidence_snippets", []),
            risk_class=r.get("risk_class", ""),
            locked_by=r.get("locked_by"),
            locked_turn=r.get("locked_turn"),
        )
        for g, r in data["rows"].items()
    }
    return StateGrid(turn=data["turn"], rows=rows, extras=[])


def _locked_facts(grid: StateGrid) -> list[str]:
    facts: list[str] = []
    for gap, row in grid.rows.items():
        if row.locked_by and row.exposure in ("X3", "X5"):
            facts.append(f"- {gap}: {row.locked_by[:200]}")
    return facts


def _needs_intake(history: AnswerHistory) -> bool:
    latest = history.latest()
    if not latest:
        return True
    if len(history.turns) == 1 and len(latest.raw_text.strip()) < INTAKE_MIN_CHARS:
        return True
    return False


def run_deterministic_pipeline(
    session,
    turn: int,
    *,
    prior_grid: StateGrid | None = None,
    current_user_text: str | None = None,
) -> tuple[AnswerHistory, StateGrid, list, list[dict[str, str]], dict[str, list[int]]]:
    history = build_history_from_session(session, through_turn=turn)
    if current_user_text is not None:
        if not history.turns or history.turns[-1].turn != turn:
            from analyst.models import UserTurn

            history.turns.append(UserTurn(turn=turn, raw_text=current_user_text.strip()))
        else:
            from analyst.models import UserTurn

            history.turns[-1] = UserTurn(turn=turn, raw_text=current_user_text.strip())

    hints = detect_changes(history, prior_grid)
    fresh = classify_gaps(history, turn, prior_grid=prior_grid, hints=hints)
    grid = merge_grid(prior_grid, fresh, history)
    asked = build_asked_history(session.turns_dir, through_turn=turn)
    candidates, vetoed = build_candidates(
        grid, history, asked_history=asked, current_turn=turn
    )
    return history, grid, candidates, vetoed, asked


def apply_llm_scores(
    candidates: list,
    llm_scores: dict[str, dict],
    *,
    asked_history: dict[str, list[int]],
    current_turn: int,
) -> list[ScoredCandidate]:
    scored: list[ScoredCandidate] = []
    for cand in candidates:
        raw = llm_scores.get(cand.gap, {})
        drivers = DriverScores(
            I=_sanitize_driver(raw.get("I", "I0"), VALID_I, "I0"),  # type: ignore[arg-type]
            C=_sanitize_driver(raw.get("C", "C0"), VALID_C, "C0"),  # type: ignore[arg-type]
            E=_sanitize_driver(raw.get("E", "E0"), VALID_E, "E0"),  # type: ignore[arg-type]
            why_now=raw.get("why_now", ""),
        )
        scored.append(
            compute_score(
                cand,
                drivers,
                asked_history=asked_history,
                current_turn=current_turn,
            )
        )
    return scored


def build_selection(
    turn: int,
    scored: list[ScoredCandidate],
    vetoed: list[dict[str, str]],
    *,
    intake: bool = False,
    intake_message: str = "",
) -> TurnSelection:
    if intake or not scored:
        return TurnSelection(
            turn=turn,
            primary=None,
            support=None,
            ranked=[],
            vetoed=vetoed,
            suppressed=[],
            intake=True,
            intake_message=intake_message or (
                "Share a bit more about who this is for and what problem you're solving — "
                "a short paragraph or two pasted artifacts helps."
            ),
        )

    ranked_list = rank_candidates(scored)
    primary = ranked_list[0]
    ranked = [{"gap": s.gap, "score": round(s.score, 4)} for s in ranked_list]
    suppressed = build_suppressed(ranked_list, primary_gap=primary.gap)

    return TurnSelection(
        turn=turn,
        primary=primary,
        support=None,
        ranked=ranked,
        vetoed=vetoed,
        suppressed=suppressed,
        intake=False,
    )


def run_pipeline(
    session,
    turn: int,
    *,
    prior_grid: StateGrid | None = None,
    current_user_text: str | None = None,
    llm_scores: dict[str, dict] | None = None,
) -> TurnPipelineResult:
    history, grid, candidates, vetoed, asked = run_deterministic_pipeline(
        session,
        turn,
        prior_grid=prior_grid,
        current_user_text=current_user_text,
    )

    if _needs_intake(history):
        selection = build_selection(turn, [], vetoed, intake=True)
        return TurnPipelineResult(
            history=history,
            grid=grid,
            selection=selection,
            candidates_scored=[],
        )

    if llm_scores is None:
        llm_scores = {c.gap: {"I": "I0", "C": "C0", "E": "E0", "why_now": ""} for c in candidates}

    scored = apply_llm_scores(
        candidates,
        llm_scores,
        asked_history=asked,
        current_turn=turn,
    )
    selection = build_selection(turn, scored, vetoed)
    return TurnPipelineResult(
        history=history,
        grid=grid,
        selection=selection,
        candidates_scored=scored,
    )
