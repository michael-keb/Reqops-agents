#!/usr/bin/env python3
"""Run 20 uplift-2.0 turns; user replies grounded in Interview-profile.md."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
HARNESS = ROOT / "test-rubric.py"
PROFILE_PATH = REPO_ROOT / "Interview-profile.md"
ENV_PATH = REPO_ROOT / ".env"
TURN_COUNT = 20

TURN_ONE_INTENT = (
    "I need to cancel my Strive Fitness Parramatta gym membership. "
    "I cannot get to the club in person. They keep billing me and will not "
    "send my signed contract or process remote cancellation without proof of relocation."
)

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env_config import get_openai_api_key, load_project_env


def load_profile() -> str:
    if not PROFILE_PATH.is_file():
        sys.exit(f"Missing interview profile: {PROFILE_PATH}")
    return PROFILE_PATH.read_text(encoding="utf-8").strip()


def latest_turn_dir(session_root: Path) -> Path | None:
    turns = session_root / "turns"
    if not turns.is_dir():
        return None
    nums = []
    for p in turns.iterdir():
        if p.is_dir() and p.name.isdigit():
            nums.append(int(p.name))
    if not nums:
        return None
    return turns / f"{max(nums):02d}"


def active_session_root() -> Path:
    active = ROOT / "sessions" / ".active"
    if not active.is_file():
        sys.exit("No active session after harness run")
    sid = active.read_text(encoding="utf-8").strip()
    return ROOT / "sessions" / sid


def respond_from_profile(
    *,
    profile: str,
    prior_questions: str,
    memory: str,
    turn: int,
    api_key: str,
) -> str:
    from openai import OpenAI

    model = (
        __import__("os").environ.get("RESPONDER_MODEL")
        or __import__("os").environ.get("LLM_MODEL")
        or "gpt-4o-mini"
    )
    client = OpenAI(api_key=api_key)
    system = f"""You are Michael Keb, the interviewee in a product-discovery session.

Answer ONLY from facts in the interview profile below. Do not invent details.
If a question does not map to the profile, say what is unknown and pick the closest
honest option or "Something else" with a short sub-angle that matches the emails.

When MCQs are present, reply with **one line per question** in the form `Gx: <chosen option text>`
(copy the option you pick, or your D sub-angle). Example:
`GA: We will validate trust via user reviews and completed-sale counts only.`
Do not skip numbered questions. Plain text only — no markdown headers.

--- INTERVIEW PROFILE (source of truth) ---
{profile}
"""

    user = f"""TURN {turn} — reply to the facilitator's last message.

--- SESSION MEMORY ---
{memory or "_(empty)_"}

--- FACILITATOR MESSAGE (questions / reflection) ---
{prior_questions or "_(turn 1 — no prior questions)_"}

Write your next user message. Cover every numbered MCQ as `Gx: <option text>` (one line each).
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
    )
    return (response.choices[0].message.content or "").strip()


def run_harness(flag: str, text: str) -> int:
    return subprocess.call(
        [sys.executable, str(HARNESS), flag, text],
        cwd=str(ROOT),
    )


def main() -> None:
    load_project_env(ENV_PATH)
    api_key = get_openai_api_key(ENV_PATH)
    profile = load_profile()

    print(f"Profile: {PROFILE_PATH.name} ({len(profile)} chars)", flush=True)
    print(f"Running {TURN_COUNT} turns via uplift-2.0\n", flush=True)

    user_text = TURN_ONE_INTENT
    for turn in range(1, TURN_COUNT + 1):
        flag = "--new" if turn == 1 else "--continue"
        print(f"\n{'='*60}\nTURN {turn}/{TURN_COUNT}\n{'='*60}\n", flush=True)
        print(f"User input preview: {user_text[:120]}…\n", flush=True)

        rc = run_harness(flag, user_text)
        if rc != 0:
            sys.exit(rc)

        if turn >= TURN_COUNT:
            break

        session = active_session_root()
        td = latest_turn_dir(session)
        if td is None:
            sys.exit(f"No turn artifacts in {session}")
        prior = (td / "llm-response.txt").read_text(encoding="utf-8")
        memory = ""
        mem_path = session / "Memory.md"
        if mem_path.is_file():
            memory = mem_path.read_text(encoding="utf-8")

        user_text = respond_from_profile(
            profile=profile,
            prior_questions=prior,
            memory=memory,
            turn=turn + 1,
            api_key=api_key,
        )
        time.sleep(0.5)

    print(f"\nDone — {TURN_COUNT} turns complete.", flush=True)
    print(f"Session: {active_session_root().name}", flush=True)


if __name__ == "__main__":
    main()
