#!/usr/bin/env python3
"""
Session-based harness for Discovery State Codes (system prompt = rubric file only).

Each test run lives in sessions/<id>/:
  Memory.md              — patched each turn (testing memory)
  log-history.md         — table: sent, output, tokens, time (all turns)
  turns/README.md        — index of all turns
  turns/01/              — user-input, prompts, llm-response, state-codes, meta.json, run.md
  session.meta.json      — turn count, timestamps

Usage:
  # New session (turn 1)
  python test-rubric.py --new "Construction app"

  # Continue active session (turn 2+)
  python test-rubric.py --continue "Field supervisors; v1 = daily photos"

  # Target a session by id
  python test-rubric.py --session 20260524-045316-consturciton-app "follow-up text"

  python test-rubric.py --list-sessions
  python test-rubric.py --dry-run --new "intent"

Loads OPENAI_API_KEY and LLM_MODEL from .env (see .env.example).

RUBRIC_FILE in .env (default llm-rubric.md) — sent as the API system message.

Output flags: OUTPUT_REFLECTION, OUTPUT_STATE_CODES, OUTPUT_NARRATIVE,
OUTPUT_QUESTIONS, OUTPUT_MEMORY_PATCH (1/on = include, 0/off = omit).
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

from env_config import get_openai_api_key, load_project_env, mask_api_key
from session_store import (
    MEMORY_FILE,
    MemoryPatch,
    Session,
    SessionStore,
    append_llm_log_history,
    extract_state_codes,
    init_turns_index,
    parse_memory_patch,
    rebuild_turns_index,
    preview_session,
    strip_memory_patch_section,
    write_turn_artifacts,
    write_turn_failed,
    write_turn_pending,
)

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"
DEFAULT_RUBRIC_FILE = "llm-rubric.md"


def rubric_path() -> Path:
    """Rubric file sent as the API system message (default: llm-rubric.md)."""
    name = os.environ.get("RUBRIC_FILE", DEFAULT_RUBRIC_FILE).strip()
    path = ROOT / name
    if not path.is_file():
        sys.exit(f"Missing rubric file: {path}")
    return path


def rubric_filename() -> str:
    return rubric_path().name

class OutputFlags(NamedTuple):
    reflection: bool
    state_codes: bool
    narrative: bool
    questions: bool
    memory_patch: bool


def _env_bool(name: str, default: bool = True) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def load_output_flags() -> OutputFlags:
    return OutputFlags(
        reflection=_env_bool("OUTPUT_REFLECTION", True),
        state_codes=_env_bool("OUTPUT_STATE_CODES", True),
        narrative=_env_bool("OUTPUT_NARRATIVE", True),
        questions=_env_bool("OUTPUT_QUESTIONS", True),
        memory_patch=_env_bool("OUTPUT_MEMORY_PATCH", True),
    )


def build_output_contract(flags: OutputFlags) -> str:
    if not any(flags):
        sys.exit(
            "At least one OUTPUT_* flag must be enabled. "
            "Set OUTPUT_STATE_CODES=1 for codes-only mode."
        )
    if not flags.state_codes:
        sys.exit("OUTPUT_STATE_CODES=0 is not supported — codes are required.")

    codes_only = flags.state_codes and not (
        flags.reflection or flags.narrative or flags.questions or flags.memory_patch
    )

    if codes_only:
        return """Output ONLY one line of state codes — no markdown headers, no prose.
Example: P3 G1:X1 G4:X2 G6:X1 L1 L4 R3 S2 Q1 Q7
Reason against the rubric internally; emit codes only.
"""

    parts = ["Respond using only the section(s) enabled below — omit disabled sections entirely.\n"]

    if flags.reflection:
        parts.append("""
## Reflection
1–2 sentences: warm ack (C1) + what you understood from the user only.
""")

    parts.append("""
## State codes
A single fenced-less line of codes, e.g.:
P3 G1:X1 G4:X2 G6:X1 G8:X1 L1 L4 R3 S2 Q1 Q7
""")

    if flags.narrative:
        parts.append("""
## Code narrative
3–5 sentences decoding the emitted codes (gaps, exposure, leverage, readiness).
""")

    if flags.questions:
        parts.append("""
## Questions
Exactly 3 multiple-choice questions when phase is P3 (elicitation).
For P1/P2/P4: write "_(no MCQs this turn — phase gate)_" and explain the next step instead.

Each MCQ must include:
- A short title with the driving gap code, e.g. **G6 — scope boundary**
- The question (S3: one decision each)
- Options A–D where D is always "Something else" (S4)
- At least one safe/conservative option (S2)
- One question must be your Q7 open probe (not purely G-derived)

Format each MCQ like:

### 1. G6 — scope boundary
[question]
- A) ...
- B) ...
- C) ...
- D) Something else — [hint for sub-angle]
""")

    if flags.memory_patch:
        parts.append("""
## Memory patch
Update session memory from **user input only** (not from prior assistant text as fact).
Use this exact key format:

pitch: <earliest product pitch, locked>
state_codes: <your emitted code line this turn>
turn_summary: <one line: Tn user did X → phase/codes effect>
facts:
- <new user-confirmed fact, if any this turn>
""")

    return "\n".join(parts)


def model_name() -> str:
    return (
        os.environ.get("RUBRIC_MODEL")
        or os.environ.get("LLM_MODEL")
        or "gpt-4o"
    )


def load_rubric() -> str:
    return rubric_path().read_text(encoding="utf-8")


def build_system_prompt(rubric: str) -> str:
    """System message is strictly the rubric file — no wrapper text."""
    return rubric.strip()


def build_user_message(
    *,
    turn: int,
    user_text: str,
    session: Session,
    flags: OutputFlags,
) -> str:
    memory = session.read_memory()
    contract = build_output_contract(flags)
    enabled = ", ".join(n for n, on in flags._asdict().items() if on)

    return f"""TURN {turn}

Apply the rubric in the system message. User input is source of truth; recompute codes each turn.
Enabled output sections: {enabled}

--- OUTPUT FORMAT (this turn) ---
{contract}

--- SESSION MEMORY (includes compressed conversation; recompute codes from user truth) ---
{memory}

--- NEW USER INPUT (SOURCE OF TRUTH THIS TURN) ---
{user_text.strip()}
"""


@dataclass
class LlmCallResult:
    reply: str
    model: str
    llm_wait_ms: float
    client_init_ms: float
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


def call_llm(system: str, user: str, *, api_key: str) -> LlmCallResult:
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("Install dependencies: pip install -r requirements.txt")

    model = model_name()
    t0 = time.perf_counter()
    client = OpenAI(
        api_key=api_key,
        base_url=os.environ.get("OPENAI_BASE_URL") or None,
    )
    client_init_ms = (time.perf_counter() - t0) * 1000

    t_llm = time.perf_counter()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.4,
    )
    llm_wait_ms = (time.perf_counter() - t_llm) * 1000
    reply = (response.choices[0].message.content or "").strip()

    usage = getattr(response, "usage", None)
    prompt_tokens = getattr(usage, "prompt_tokens", None) if usage else None
    completion_tokens = getattr(usage, "completion_tokens", None) if usage else None
    total_tokens = getattr(usage, "total_tokens", None) if usage else None

    return LlmCallResult(
        reply=reply,
        model=model,
        llm_wait_ms=llm_wait_ms,
        client_init_ms=client_init_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )


def build_run_markdown(
    session: Session,
    turn: int,
    *,
    user_text: str,
    user_msg: str,
    result: LlmCallResult,
    input_wall_ms: float,
    memory_after: str,
    api_key_mask: str,
    flags: OutputFlags,
    rubric_name: str,
) -> str:
    total_ms = input_wall_ms + result.llm_wait_ms
    visible_reply = (
        strip_memory_patch_section(result.reply)
        if flags.memory_patch
        else result.reply.strip()
    )
    state_codes = extract_state_codes(result.reply) or visible_reply.strip()

    return f"""# Turn {turn:02d} — LLM call

**Session:** `{session.root.name}`  
**Recorded:** {datetime.now(timezone.utc).isoformat()}  
**Model:** `{result.model}`  
**API key:** `{api_key_mask}` (from `{ENV_PATH.name}`)  
**Memory:** `{MEMORY_FILE}` (in session folder)

**Artifacts:** `{rubric_name}` · `user-prompt.txt` · `llm-response.txt` · `state-codes.txt` · `meta.json`

System message sent to the API is **only** `{rubric_name}` (see `turns/{turn:02d}/{rubric_name}`).

---

## Timing

| Metric | ms | seconds |
|--------|-----:|--------:|
| Input preparation time | {input_wall_ms:.1f} | {input_wall_ms / 1000:.3f} |
| LLM wait time (processing) | {result.llm_wait_ms:.1f} | {result.llm_wait_ms / 1000:.3f} |
| Total response time | {total_ms:.1f} | {total_ms / 1000:.3f} |

## Tokens

| | Count |
|--|------:|
| Input (prompt) | {result.prompt_tokens if result.prompt_tokens is not None else "—"} |
| Output (completion) | {result.completion_tokens if result.completion_tokens is not None else "—"} |
| Total | {result.total_tokens if result.total_tokens is not None else "—"} |

---

## User input

```
{user_text.strip()}
```

<details>
<summary>Full prompt sent to the model</summary>

```
{user_msg.strip()}
```

</details>

---

## State codes

```
{state_codes}
```

## LLM response

{visible_reply}

---

## Memory after patch

```
{memory_after.strip()[:8000]}
```
"""


def apply_reply_to_session(
    session: Session,
    turn: int,
    user_text: str,
    reply: str,
    *,
    flags: OutputFlags,
) -> str:
    patch = parse_memory_patch(reply) if flags.memory_patch else MemoryPatch()
    if not patch.state_codes:
        patch.state_codes = extract_state_codes(reply)
    if not patch.pitch:
        patch.pitch = (
            session.meta.get("initial_intent")
            or session.read_pitch()
            or user_text.splitlines()[0][:200]
        )
    if not patch.turn_summary:
        codes = patch.state_codes or "?"
        patch.turn_summary = f'user: "{user_text[:80]}{"…" if len(user_text) > 80 else ""}" → {codes}'

    session.apply_patch(patch, turn=turn)
    session.record_turn_completed()
    return session.read_memory()


def read_user_text(args: argparse.Namespace) -> str:
    if args.intent:
        return " ".join(args.intent).strip()
    if args.interactive:
        print("Your message (empty line to finish):")
        lines: list[str] = []
        try:
            while True:
                line = input()
                if line == "" and lines:
                    break
                lines.append(line)
        except EOFError:
            pass
        text = "\n".join(lines).strip()
        if text:
            return text
    sys.exit("Provide message text, or use -i for interactive input.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Session-based llm-rubric tester")
    parser.add_argument("intent", nargs="*", help="User message for this turn")
    parser.add_argument("--new", action="store_true", help="Start a new session")
    parser.add_argument(
        "--continue",
        dest="continue_",
        action="store_true",
        help="Continue the active session",
    )
    parser.add_argument("--session", metavar="ID", help="Use a specific session folder")
    parser.add_argument("--list-sessions", action="store_true", help="List sessions")
    parser.add_argument("-i", "--interactive", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_project_env(ENV_PATH)
    flags = load_output_flags()
    store = SessionStore(ROOT)

    if args.list_sessions:
        active = (
            store.active_path.read_text(encoding="utf-8").strip()
            if store.active_path.is_file()
            else None
        )
        for sid in store.list_sessions():
            mark = " ← active" if sid == active else ""
            print(f"  {sid}{mark}")
        return

    if args.new and args.continue_:
        sys.exit("Use either --new or --continue, not both.")

    text = read_user_text(args)

    if args.dry_run:
        if args.new or not store.active_path.is_file():
            print("(dry-run: no session created)")
            print(f"Would start new session for: {text!r}")
            turn = 1
            user_msg = build_user_message(
                turn=turn,
                user_text=text,
                session=preview_session(store.sessions_dir, text),
                flags=flags,
            )
        else:
            session = store.load_active()
            turn = session.next_turn_number()
            print(f"(dry-run) Session: {session.root.name} turn {turn}")
            user_msg = build_user_message(
                turn=turn, user_text=text, session=session, flags=flags
            )
        print(f"Output flags: {flags}")
        print("\n=== USER MESSAGE ===\n")
        print(user_msg)
        return

    if args.new:
        session = store.create(text)
        is_turn_one = True
    elif args.session:
        session = store.load(args.session)
        store.set_active(session)
        is_turn_one = False
    elif args.continue_:
        session = store.load_active()
        is_turn_one = False
    elif store.active_path.is_file():
        session = store.load_active()
        is_turn_one = False
    else:
        session = store.create(text)
        is_turn_one = True

    turn = 1 if is_turn_one else session.next_turn_number()

    t_input = time.perf_counter()
    rubric = load_rubric()
    system = build_system_prompt(rubric)
    user_msg = build_user_message(
        turn=turn, user_text=text, session=session, flags=flags
    )
    input_wall_ms = (time.perf_counter() - t_input) * 1000

    enabled = [n for n, on in flags._asdict().items() if on]
    rfile = rubric_filename()
    api_key = get_openai_api_key(ENV_PATH)
    key_mask = mask_api_key(api_key)
    flags_dict = flags._asdict()

    init_turns_index(session)
    rebuild_turns_index(session)
    write_turn_pending(session, turn, user_text=text, output_flags=flags_dict)

    print(f"\n--- Session `{session.root.name}` · turn {turn:02d} ---")
    print(f"Rubric: {rfile}")
    print(f"Output: {', '.join(enabled)}")
    print(f"OpenAI key: {key_mask}\n")

    try:
        result = call_llm(system, user_msg, api_key=api_key)
    except Exception as exc:
        write_turn_failed(session, turn, error=str(exc), api_key_mask=key_mask)
        print(f"API call failed. See turns/{turn:02d}/error.md", file=sys.stderr)
        raise SystemExit(1) from exc

    memory_after = apply_reply_to_session(
        session, turn, text, result.reply, flags=flags
    )
    total_ms = input_wall_ms + result.llm_wait_ms
    state_codes = extract_state_codes(result.reply) or result.reply.strip()

    run_md = build_run_markdown(
        session,
        turn,
        user_text=text,
        user_msg=user_msg,
        result=result,
        input_wall_ms=input_wall_ms,
        memory_after=memory_after,
        api_key_mask=key_mask,
        flags=flags,
        rubric_name=rfile,
    )
    log_path = write_turn_artifacts(
        session,
        turn,
        user_text=text,
        system_prompt=system,
        user_prompt=user_msg,
        llm_response=result.reply,
        state_codes=state_codes,
        model=result.model,
        output_flags=flags_dict,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        total_tokens=result.total_tokens,
        input_prep_ms=input_wall_ms,
        llm_wait_ms=result.llm_wait_ms,
        api_key_mask=key_mask,
        memory_after=memory_after,
        run_md_body=run_md,
        rubric_filename=rfile,
    )
    session.sync_turn_count_from_disk()

    history_path = append_llm_log_history(
        session,
        turn=turn,
        model=result.model,
        system_prompt=system,
        user_prompt=user_msg,
        output=result.reply,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        total_tokens=result.total_tokens,
        total_response_ms=total_ms,
        llm_wait_ms=result.llm_wait_ms,
        input_prep_ms=input_wall_ms,
        rubric_filename=rfile,
    )

    visible = (
        strip_memory_patch_section(result.reply)
        if flags.memory_patch
        else result.reply.strip()
    )

    print("## Timing")
    print(f"1. Input preparation time:  {input_wall_ms:.1f} ms")
    print(f"2. LLM wait (processing):    {result.llm_wait_ms:.1f} ms")
    print(f"3. Total response time:      {total_ms:.1f} ms")
    if result.prompt_tokens is not None:
        print(
            f"4. Tokens (in / out / total): "
            f"{result.prompt_tokens:,} / {result.completion_tokens:,} / {result.total_tokens:,}"
        )
    print(f"\n5. Turn log:      {log_path}")
    print(f"6. Log history:   {history_path}")
    print(f"7. Memory:        {session.memory_path}\n")
    print("## LLM response\n")
    print(visible)
    print(f"\n[continue] python test-rubric.py --continue \"your follow-up\"")


if __name__ == "__main__":
    main()
