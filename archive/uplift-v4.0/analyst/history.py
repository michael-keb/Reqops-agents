"""Build user-only answer history from session turns."""

from __future__ import annotations

import json
from pathlib import Path

from analyst.models import AnswerHistory, UserTurn


def build_history_from_turn_files(
    pitch: str,
    turns_dir: Path,
    *,
    through_turn: int | None = None,
) -> AnswerHistory:
    turns: list[UserTurn] = []
    if not turns_dir.is_dir():
        return AnswerHistory(pitch=pitch, turns=turns)

    nums = sorted(
        int(p.name)
        for p in turns_dir.iterdir()
        if p.is_dir() and p.name.isdigit() and len(p.name) == 2
    )
    for n in nums:
        if through_turn is not None and n > through_turn:
            break
        user_file = turns_dir / f"{n:02d}" / "user-input.txt"
        if user_file.is_file():
            turns.append(
                UserTurn(turn=n, raw_text=user_file.read_text(encoding="utf-8").strip())
            )

    return AnswerHistory(pitch=pitch, turns=turns)


def build_history_from_session(session, *, through_turn: int | None = None) -> AnswerHistory:
    pitch = session.read_pitch() or session.meta.get("initial_intent", "")
    return build_history_from_turn_files(
        pitch, session.turns_dir, through_turn=through_turn
    )


def history_to_json(history: AnswerHistory) -> str:
    data = {
        "pitch": history.pitch,
        "turns": [{"turn": t.turn, "raw_text": t.raw_text} for t in history.turns],
    }
    return json.dumps(data, indent=2)
