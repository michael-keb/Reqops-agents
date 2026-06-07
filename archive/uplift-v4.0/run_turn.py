#!/usr/bin/env python3
"""
Uplift 4.0 — analyst discovery harness.

Pipeline (see instrucitons.md):
  1. Deterministic: candidates (L2 veto), grid
  2. LLM: score I/C/E per candidate (multiplier rubric as system prompt — referenced, not coded)
  3. Deterministic: attach R/K, multiply, rank, route mode
  4. LLM: phrase one MCQ from selection

Usage:
  python run_turn.py --new "Car selling app"
  python run_turn.py --continue "follow-up message"
  python run_turn.py --dry-run --new "..."   # pipeline only — NO phrasing LLM (see llm-response stub)
  python run_turn.py --new "Car selling app" # LIVE: score LLM + phrase LLM
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
ENV_PATH = ROOT / ".env" if (ROOT / ".env").is_file() else REPO_ROOT / ".env"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analyst.emit import format_multiplier_audit
from analyst.history import history_to_json
from analyst.llm_client import call_llm
from analyst.pipeline import (
    _locked_facts,
    load_prior_grid,
    run_deterministic_pipeline,
    run_pipeline,
)
from analyst.phrasing_prompt import build_phrase_user_message
from analyst.scorer_prompt import build_score_user_message, parse_score_response
from env_config import get_openai_api_key, mask_api_key
from rubric import RUBRIC_FILENAME, load_phrasing_system_prompt, load_scorer_system_prompt
from analyst.fixtures import CAR_APP_TURNS, TURN9_LLM_SCORES, TURN9_USER
from session_store import (
    MemoryPatch,
    SessionStore,
    append_turn_log_history,
    write_analyst_artifacts,
    write_turn_artifacts,
)


def _score_system_prompt() -> str:
    preamble = (ROOT / "prompts" / "score-candidates.md").read_text(encoding="utf-8")
    rubric = load_scorer_system_prompt()
    return f"{preamble}\n\n---\n\n# Multiplier rubric (authoritative)\n\n{rubric}"


def run_one_turn(
    session,
    user_text: str,
    *,
    dry_run: bool = False,
    fixture: str | None = None,
    api_key: str | None = None,
    verbose: bool = False,
) -> str:
    turn = session.next_turn_number()
    prior = load_prior_grid(session, turn)
    prep_t0 = time.perf_counter()

    history, grid, candidates, vetoed, asked = run_deterministic_pipeline(
        session,
        turn,
        prior_grid=prior,
        current_user_text=user_text,
    )
    locked = _locked_facts(grid)

    score_user = build_score_user_message(
        turn=turn,
        history=history,
        grid=grid,
        candidates=candidates,
        locked_facts=locked,
    )
    score_system = _score_system_prompt()

    score_prompt_tokens: int | None = None
    score_completion_tokens: int | None = None
    phrase_prompt_tokens: int | None = None
    phrase_completion_tokens: int | None = None

    if fixture == "turn9":
        llm_scores = {
            c.gap: TURN9_LLM_SCORES.get(
                c.gap, {"I": "I0", "C": "C0", "E": "E0", "why_now": ""}
            )
            for c in candidates
        }
        score_response_text = json.dumps(
            {"scores": [{"gap": g, **v} for g, v in llm_scores.items()]}, indent=2
        )
        score_wait = 0.0
    elif dry_run:
        llm_scores = {c.gap: {"I": "I0", "C": "C0", "E": "E0", "why_now": ""} for c in candidates}
        score_response_text = json.dumps({"scores": [{"gap": c.gap, "I": "I0", "C": "C0", "E": "E0", "why_now": ""} for c in candidates]}, indent=2)
        score_wait = 0.0
    else:
        if not api_key:
            sys.exit("API key required unless --dry-run or --fixture")
        score_result = call_llm(
            api_key=api_key,
            system_prompt=score_system,
            user_message=score_user,
            role="score",
            temperature=0.2,
        )
        score_wait = score_result.wait_ms
        score_response_text = score_result.text
        score_prompt_tokens = score_result.prompt_tokens
        score_completion_tokens = score_result.completion_tokens
        llm_scores = parse_score_response(score_result.text)

    result = run_pipeline(
        session,
        turn,
        prior_grid=prior,
        current_user_text=user_text,
        llm_scores=llm_scores,
    )

    scored_json = json.dumps(
        [s.to_dict() for s in result.candidates_scored], indent=2
    )
    why = result.selection.primary.drivers.why_now if result.selection.primary else ""
    multiplier_state = format_multiplier_audit(
        turn=turn,
        scored=result.candidates_scored,
        vetoed=result.selection.vetoed,
        primary=result.selection.primary,
        why=why,
    )
    write_analyst_artifacts(
        session,
        turn,
        grid_json=result.grid.to_json(),
        selection_json=result.selection.to_json(),
        scored_json=scored_json,
        history_json=history_to_json(result.history),
        multiplier_state=multiplier_state,
    )

    phrase_system = load_phrasing_system_prompt()
    phrase_user = build_phrase_user_message(
        turn=turn,
        user_text=user_text,
        selection=result.selection,
        locked_facts=locked,
        memory=session.read_memory_for_llm(),
        multiplier_audit=multiplier_state,
    )

    if dry_run:
        llm_response = _dry_run_phrase_stub(result)
        phrase_wait = 0.0
        model = "dry-run"
    else:
        phrase_result = call_llm(
            api_key=api_key,
            system_prompt=phrase_system,
            user_message=phrase_user,
            role="phrase",
            temperature=0.5,
        )
        llm_response = phrase_result.text
        phrase_wait = phrase_result.wait_ms
        phrase_prompt_tokens = phrase_result.prompt_tokens
        phrase_completion_tokens = phrase_result.completion_tokens
        model = phrase_result.model
        llm_response = _reject_template_output(llm_response, phrase_user, api_key, phrase_system)

    prep_ms = (time.perf_counter() - prep_t0) * 1000 - score_wait - phrase_wait

    write_turn_artifacts(
        session,
        turn,
        user_text=user_text,
        score_system=score_system,
        score_user=score_user,
        score_response=score_response_text,
        phrase_system=phrase_system,
        phrase_user=phrase_user,
        llm_response=llm_response,
        model=model,
        score_wait_ms=score_wait,
        phrase_wait_ms=phrase_wait,
        input_prep_ms=max(0.0, prep_ms),
    )

    append_turn_log_history(
        session,
        turn=turn,
        user_text=user_text,
        score_system=score_system,
        score_user=score_user,
        score_output=score_response_text,
        phrase_system=phrase_system,
        phrase_user=phrase_user,
        phrase_output=llm_response,
        selection_json=result.selection.to_json(),
        model=model,
        score_prompt_tokens=score_prompt_tokens,
        score_completion_tokens=score_completion_tokens,
        phrase_prompt_tokens=phrase_prompt_tokens,
        phrase_completion_tokens=phrase_completion_tokens,
        score_wait_ms=score_wait,
        phrase_wait_ms=phrase_wait,
        input_prep_ms=max(0.0, prep_ms),
        rubric_filename=RUBRIC_FILENAME,
    )

    session.apply_patch(
        MemoryPatch(turn_summary=f"Asked {result.selection.primary.gap if result.selection.primary else 'intake'}"),
        turn=turn,
    )
    session.record_turn_completed()

    sel = result.selection.to_dict()
    primary = result.selection.primary
    if verbose:
        print(json.dumps(sel, indent=2))
        print("\n--- LLM response ---\n")
    else:
        sid = session.root.name
        gap = primary.gap if primary else "intake"
        mode = primary.mode if primary else "—"
        print(f"--- {sid} · turn {turn:02d} · {gap} · {mode} ---\n")
    print(llm_response)
    return llm_response


def _looks_templated(text: str) -> bool:
    lower = text.lower()
    markers = (
        "option a",
        "option b",
        "option c",
        "under your latest input",
        "[coverage]",
        "[follow]",
        "[confront]",
        "[probe_seam]",
        "what specifically happens for",
    )
    return any(m in lower for m in markers)


def _reject_template_output(
    text: str,
    phrase_user: str,
    api_key: str,
    phrase_system: str,
) -> str:
    """One retry if phrasing LLM returned placeholder/template output."""
    if not _looks_templated(text):
        return text
    retry_user = (
        phrase_user
        + "\n\n--- RETRY ---\n"
        "Your previous output used banned templates or placeholders. "
        "Rewrite from scratch: specific stem, specific policies in A–C, no mode tags."
    )
    retry = call_llm(
        api_key=api_key,
        system_prompt=phrase_system,
        user_message=retry_user,
        role="phrase",
        temperature=0.6,
    )
    return retry.text


def _dry_run_phrase_stub(result) -> str:
    """Explicit stub — dry-run never calls the phrasing LLM."""
    p = result.selection.primary
    if not p:
        return (
            "## Reflection\n"
            "_(DRY-RUN — phrasing LLM not called. See `phrase-user.txt`.)_\n\n"
            "## Questions\n\n"
            "_(intake turn — run without --dry-run for real output)_\n"
        )
    return (
        "## Reflection\n"
        "_(DRY-RUN — phrasing LLM not called. "
        f"Selection: `{p.gap}` mode={p.mode}. See `phrase-user.txt` for full prompt.)_\n\n"
        "## Questions\n\n"
        "_(no LLM MCQ — run without --dry-run)_\n"
    )


def replay_car_turn9(store: SessionStore, *, dry_run: bool = True) -> None:
    """Replay car-app turns 1–8 then run turn 9 with fixture scores."""
    session = store.create("car-selling-app-replay")
    for msg in CAR_APP_TURNS[:-1]:
        run_one_turn(session, msg, dry_run=True)
    # Ensure turn 8 recorded G1 as asked (for R3 on turn 9)
    _mark_primary_gap(session, 8, "G1")
    run_one_turn(session, TURN9_USER, dry_run=dry_run, fixture="turn9")


def _mark_primary_gap(session, turn: int, gap: str) -> None:
    d = session.turn_dir(turn)
    sel_path = d / "selection.json"
    if sel_path.is_file():
        data = json.loads(sel_path.read_text(encoding="utf-8"))
    else:
        data = {"turn": turn, "ranked": []}
    data["primary"] = {
        "gap": gap,
        "score": 1.0,
        "mode": "FOLLOW",
        "dominant_term": "I=1.0",
        "codes": {"I": "I0", "C": "C0", "E": "E0", "R": "R0", "K": "K1"},
        "why_now": "replay seed",
        "question_intent": gap,
    }
    sel_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Uplift 4.0 discovery turn")
    parser.add_argument("message", nargs="?", help="User message for this turn")
    parser.add_argument("--new", metavar="INTENT", help="Start new session with pitch")
    parser.add_argument("--continue", dest="cont", metavar="MSG", help="Continue active session")
    parser.add_argument("--session", metavar="ID", help="Session id")
    parser.add_argument("--dry-run", action="store_true", help="No API calls")
    parser.add_argument("--fixture", choices=["turn9"], help="Use built-in score fixture")
    parser.add_argument(
        "--replay-car-turn9",
        action="store_true",
        help="Replay car-app script through turn 9 with fixture scores",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full selection JSON (audit)",
    )
    args = parser.parse_args()

    store = SessionStore(ROOT)
    api_key = None
    if not args.dry_run:
        api_key = get_openai_api_key(ENV_PATH)

    if args.replay_car_turn9:
        replay_car_turn9(store, dry_run=args.dry_run)
        return

    if args.new:
        session = store.create(args.new)
        user_text = args.new
    elif args.cont:
        session = store.load_active()
        user_text = args.cont
    elif args.session and args.message:
        session = store.load(args.session)
        user_text = args.message
    elif args.message:
        session = store.load_active()
        user_text = args.message
    else:
        parser.print_help()
        sys.exit(1)

    run_one_turn(
        session,
        user_text,
        dry_run=args.dry_run,
        fixture=args.fixture,
        api_key=api_key,
        verbose=args.json,
    )


if __name__ == "__main__":
    main()
