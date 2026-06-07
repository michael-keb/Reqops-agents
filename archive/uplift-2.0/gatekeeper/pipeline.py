"""End-to-end gatekeeper turn pipeline."""

from __future__ import annotations

from gatekeeper.batch import build_question_plan
from gatekeeper.classify import classify_gaps
from gatekeeper.detect import detect_changes
from gatekeeper.derive import enrich_grid
from gatekeeper.emit import grid_to_code_line
from gatekeeper.history import build_history_from_session
from gatekeeper.models import StateGrid, TurnPipelineResult, UserTurn
from gatekeeper.validate import validate_code_line, validate_grid_matches_line


def run_pipeline(
    session,
    turn: int,
    *,
    prior_grid: StateGrid | None = None,
    current_user_text: str | None = None,
) -> TurnPipelineResult:
    history = build_history_from_session(session, through_turn=turn)
    if current_user_text is not None:
        # Live turn: user message may not be on disk yet
        if not history.turns or history.turns[-1].turn != turn:
            history.turns.append(UserTurn(turn=turn, raw_text=current_user_text.strip()))
        else:
            history.turns[-1] = UserTurn(turn=turn, raw_text=current_user_text.strip())
    hints = detect_changes(history, prior_grid)
    grid = classify_gaps(history, turn, prior_grid=prior_grid, hints=hints)
    grid = enrich_grid(grid, history)
    plan = build_question_plan(grid)
    code_line = grid_to_code_line(grid)

    vr = validate_code_line(code_line, require_all_gaps=True)
    if not vr.ok:
        raise ValueError(f"gatekeeper produced invalid code line: {vr.errors}")

    gvr = validate_grid_matches_line(grid, code_line)
    if not gvr.ok:
        raise ValueError(f"grid/emit mismatch: {gvr.errors}")

    from gatekeeper.derive import open_gaps

    return TurnPipelineResult(
        history=history,
        grid=grid,
        plan=plan,
        code_line=code_line,
        open_gaps=open_gaps(grid),
    )


def load_prior_grid(session, turn: int) -> StateGrid | None:
    if turn <= 1:
        return None
    path = session.turn_dir(turn - 1) / "grid.json"
    if not path.is_file():
        return None
    import json
    from gatekeeper.models import GapRow

    data = json.loads(path.read_text(encoding="utf-8"))
    rows = {
        k: GapRow(
            gap=k,
            exposure=v["exposure"],
            evidence_turns=v.get("evidence_turns", []),
            evidence_snippets=v.get("evidence_snippets", []),
            risk_class=v.get("risk_class", ""),
            sub_gap=v.get("sub_gap"),
        )
        for k, v in data.get("rows", {}).items()
    }
    return StateGrid(
        turn=data.get("turn", turn - 1),
        rows=rows,
        phase=data.get("phase", "P3"),
        leverage=data.get("leverage", []),
        readiness=data.get("readiness", []),
        shaping=data.get("shaping", []),
        batch=data.get("batch", []),
    )
