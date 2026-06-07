"""Fast mock agent for Playwright / local e2e (no Cursor API)."""

from __future__ import annotations

import json
import time
from pathlib import Path

from bridge.logging_util import log

MOCK_DELAY_MS = int(__import__("os").environ.get("UPLIFT_MOCK_DELAY_MS", "200"))


def _mock_stream(turn: int, user_text: str) -> None:
    steps = [
        "Reading uplift-discovery skill…",
        "Scoring gaps (I×C×E×R×K)…",
        f"Writing turn {turn:02d} artifacts…",
    ]
    chunk = max(MOCK_DELAY_MS // max(len(steps), 1), 30)
    for step in steps:
        log(step, kind="agent")
        time.sleep(chunk / 1000.0)
    log(f"Mock turn {turn:02d} complete.", kind="agent")


def _response_md(turn: int, reflection: str, question: str, options: list[str]) -> str:
    opts = "\n".join(f"- {o}" for o in options)
    return f"## Reflection\n{reflection}\n\n## Question\n**{question}**\n\n{opts}\n"


def run_mock_turn(session_dir: Path, turn: int, user_text: str, *, pitch: str | None = None) -> None:
    _mock_stream(turn, user_text)
    turn_dir = session_dir / "turns" / f"{turn:02d}"
    turn_dir.mkdir(parents=True, exist_ok=True)
    (turn_dir / "user-input.txt").write_text(user_text.strip(), encoding="utf-8")

    if turn == 1:
        reflection = f"You described {user_text.strip()[:80]} — that sets the product frame."
        question = "Who is the primary user on day one?"
        options = [
            "A) Individual consumers booking directly",
            "B) Small businesses managing a roster",
            "C) Both, but one side leads supply",
            "D) Something else — describe your wedge",
        ]
        turn_json = {
            "turn": 1,
            "primary_gap": "G1",
            "mode": "PROBE",
            "score": 8.0,
            "dominant_term": "I2",
            "why_now": f"Pitch is thin on who actually uses this first: {user_text.strip()[:60]}",
            "reflection": reflection,
            "question": question,
            "options": options,
        }
    else:
        reflection = f"You answered: {user_text.strip()[:120]} — that narrows the wedge."
        question = "What must be true before someone trusts this with real money or access?"
        options = [
            "A) Reviews and identity verification on both sides",
            "B) Insurance or guarantee from the platform",
            "C) Starts inside existing social trust (friends/referrals)",
            "D) Something else — spell out the trust mechanism",
        ]
        turn_json = {
            "turn": turn,
            "primary_gap": "GA",
            "mode": "FOLLOW",
            "score": 12.8,
            "dominant_term": "I2",
            "why_now": f"Follow-up to prior answer: {user_text.strip()[:80]}",
            "reflection": reflection,
            "question": question,
            "options": options,
        }

    response = _response_md(turn, reflection, question, options)
    (turn_dir / "turn.json").write_text(json.dumps(turn_json, indent=2) + "\n", encoding="utf-8")
    (turn_dir / "response.md").write_text(response, encoding="utf-8")
    (turn_dir / "multiplier-audit.txt").write_text(
        f"T{turn} mock audit — {turn_json['primary_gap']} {turn_json['mode']} {turn_json['score']}\n",
        encoding="utf-8",
    )

    memory = session_dir / "Memory.md"
    pitch_line = pitch or user_text.strip()
    if turn == 1:
        memory.write_text(
            f"# Discovery memory\n\n## Pitch\n{pitch_line}\n\n## Settled facts\n_(none yet)_\n\n## Turn log\n"
            f"T1 — asked primary user\n",
            encoding="utf-8",
        )
    else:
        body = memory.read_text(encoding="utf-8") if memory.is_file() else ""
        if "## Turn log" not in body:
            body += "\n## Turn log\n"
        memory.write_text(body + f"T{turn} — trust mechanism follow-up\n", encoding="utf-8")

    chat_id = f"mock-{session_dir.name[-12:]}"
    (session_dir / ".chat-id").write_text(chat_id, encoding="utf-8")
