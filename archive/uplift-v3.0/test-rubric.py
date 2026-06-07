#!/usr/bin/env python3
"""
Uplift 2.0 — gatekeeper-first discovery harness.

Separate from legacy `test-rubric.py` at repo root. Does not modify the existing system.

Flow each turn:
  1. Gatekeeper: history → classify → grid → plan → authoritative code line
  2. LLM: phrase MCQs from question plan (full llm-rubric_v2.md system prompt)
  3. Gatekeeper: validate MCQ count; patch memory with gatekeeper codes

Usage (from repo root or uplift-2.0/):
  python uplift-2.0/test-rubric.py --new "Car selling app"
  python uplift-2.0/test-rubric.py --continue "follow-up"
  python uplift-2.0/test-rubric.py --replay ../sessions/20260524-202455-car-selling-app --write
  python uplift-2.0/test-rubric.py --dry-run --new "intent"

Loads OPENAI_API_KEY from parent `.env`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
ENV_PATH = REPO_ROOT / ".env"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env_config import get_openai_api_key, load_project_env, mask_api_key
from gatekeeper.history import history_to_json
from gatekeeper.pipeline import load_prior_grid, run_pipeline
from gatekeeper.validate import count_mcq_headers, validate_mcq_count
from session_store import (
    MEMORY_FILE,
    MemoryPatch,
    Session,
    SessionStore,
    append_llm_log_history,
    init_turns_index,
    parse_memory_patch,
    rebuild_turns_index,
    preview_session,
    strip_memory_patch_section,
    write_gatekeeper_artifacts,
    write_turn_artifacts,
    write_turn_failed,
    write_turn_pending,
)

from rubric import RUBRIC_V2_FILENAME, load_phrasing_system_prompt


class OutputFlags(NamedTuple):
    reflection: bool
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
        questions=_env_bool("OUTPUT_QUESTIONS", True),
        memory_patch=_env_bool("OUTPUT_MEMORY_PATCH", True),
    )

DEFAULT_MAX_BATCH = 1


def build_output_contract(flags: OutputFlags, plan) -> str:
    """Turn-specific output gate only — format rules live in llm-rubric_v2.md."""
    mcq_count = plan.constraints.get("mcq_count", 0)
    assessment = plan.constraints.get("assessment") or {}
    enabled = [n for n, on in flags._asdict().items() if on]
    parts = [
        "Respond using only the sections enabled for this turn.\n",
        f"Enabled sections: {', '.join(enabled) or 'none'}\n",
        "**Do not emit state codes** — the gatekeeper attaches them.\n",
        "All phrasing, shaping (S*), batch (Q*), coaching (C*), and output format rules "
        f"are in the system prompt ({RUBRIC_V2_FILENAME}). Follow that document.\n",
    ]
    if flags.reflection and assessment:
        parts.append(
            f"\nThis turn's diagnosed primary weakness: "
            f"{assessment.get('primary_label', 'see DISCOVERY ASSESSMENT')}\n"
        )
    if flags.questions:
        if mcq_count == 0:
            parts.append(
                f"\nEmit ## Questions only. Phase {plan.phase}: "
                "`_(no MCQs this turn — phase gate)_` plus next step (see rubric P phase).\n"
            )
        else:
            parts.append(
                f"\nEmit ## Reflection (if enabled) then ## Questions.\n"
                f"Exactly **{mcq_count}** MCQ(s) — one per QUESTION PLAN slot, numbered "
                f"### 1. through ### {mcq_count}. "
                "Do not stop after the first question.\n"
                "Follow DISCOVERY ASSESSMENT + each slot's `brief` + rubric Phrasing layer.\n"
            )
    if flags.memory_patch:
        parts.append("""
Emit ## Memory patch — from user input only:
pitch: ...
turn_summary: ...
facts:
- ...
(Do not set state_codes.)
""")
    return "\n".join(parts)


def build_user_message(
    *,
    turn: int,
    user_text: str,
    session: Session,
    flags: OutputFlags,
    pipeline_result,
) -> str:
    memory = session.read_memory_for_llm()
    plan = pipeline_result.plan
    contract = build_output_contract(flags, plan)
    enabled = ", ".join(n for n, on in flags._asdict().items() if on)

    locked_facts = []
    for gap, row in pipeline_result.grid.rows.items():
        if row.locked_by and row.exposure in ("X3", "X5"):
            locked_facts.append(f"- {gap}: {row.locked_by[:200]}")

    locked_block = (
        "\n".join(locked_facts)
        if locked_facts
        else "_(no hard locks yet)_"
    )

    return f"""TURN {turn} — UPLIFT 3.0 (gatekeeper + grounded phrasing)

Enabled output sections: {enabled}

--- NEW USER INPUT (SOURCE OF TRUTH — read first) ---
{user_text.strip()}

--- LOCKED FACTS (do not re-ask; you may reference) ---
{locked_block}

--- GATEKEEPER STATE (read-only; do not re-derive) ---
Phase: {pipeline_result.grid.phase}
Open gaps: {len(pipeline_result.open_gaps)}
Authoritative codes (for your awareness only — do not emit):
{pipeline_result.code_line}

--- DISCOVERY ASSESSMENT (gatekeeper — read before phrasing) ---
{json.dumps(plan.constraints.get("assessment") or {}, indent=2)}

--- QUESTION PLAN (one primary probe per slot; follow `brief` + assessment) ---
{plan.to_json()}

--- OUTPUT FORMAT (turn gate — full rules in system rubric) ---
{contract}

--- SESSION MEMORY (pitch + compressed history; state codes and settled facts omitted — see above) ---
{memory}
"""


def model_name() -> str:
    return (
        os.environ.get("PHRASING_MODEL")
        or os.environ.get("RUBRIC_MODEL")
        or os.environ.get("LLM_MODEL")
        or "gpt-4o"
    )


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
        temperature=0.55,
    )
    llm_wait_ms = (time.perf_counter() - t_llm) * 1000
    reply = (response.choices[0].message.content or "").strip()

    usage = getattr(response, "usage", None)
    return LlmCallResult(
        reply=reply,
        model=model,
        llm_wait_ms=llm_wait_ms,
        client_init_ms=client_init_ms,
        prompt_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
        completion_tokens=getattr(usage, "completion_tokens", None) if usage else None,
        total_tokens=getattr(usage, "total_tokens", None) if usage else None,
    )


def append_state_codes(reply: str, code_line: str) -> str:
    if "## State codes" in reply:
        return reply
    return f"{reply.rstrip()}\n\n## State codes\n{code_line}\n"


def apply_reply_to_session(
    session: Session,
    turn: int,
    user_text: str,
    reply: str,
    *,
    code_line: str,
    flags: OutputFlags,
) -> str:
    patch = parse_memory_patch(reply) if flags.memory_patch else MemoryPatch()
    patch.state_codes = code_line
    if not patch.pitch:
        patch.pitch = (
            session.meta.get("initial_intent")
            or session.read_pitch()
            or user_text.splitlines()[0][:200]
        )
    if not patch.turn_summary:
        patch.turn_summary = (
            f'user: "{user_text[:80]}{"…" if len(user_text) > 80 else ""}" → {code_line}'
        )
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
    parser = argparse.ArgumentParser(description="Uplift 2.0 gatekeeper harness")
    parser.add_argument("intent", nargs="*", help="User message for this turn")
    parser.add_argument("--new", action="store_true")
    parser.add_argument("--continue", dest="continue_", action="store_true")
    parser.add_argument("--session", metavar="ID")
    parser.add_argument("--list-sessions", action="store_true")
    parser.add_argument("--replay", metavar="PATH", help="Replay gatekeeper on session path")
    parser.add_argument("--write", action="store_true", help="With --replay, write grid.json")
    parser.add_argument("--gatekeeper-only", action="store_true", help="Skip LLM; run gatekeeper only")
    parser.add_argument("-i", "--interactive", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_project_env(ENV_PATH)
    flags = load_output_flags()
    store = SessionStore(ROOT)

    if args.replay:
        from gatekeeper.replay import replay_session

        path = Path(args.replay)
        if not path.is_dir():
            path = REPO_ROOT / "sessions" / args.replay
        replay_session(path, write=args.write)
        return

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
        session = (
            preview_session(store.sessions_dir, text)
            if args.new or not store.active_path.is_file()
            else store.load_active()
        )
        turn = 1 if args.new else session.next_turn_number()
        prior = load_prior_grid(session, turn)
        result = run_pipeline(session, turn, prior_grid=prior, current_user_text=text)
        user_msg = build_user_message(
            turn=turn,
            user_text=text,
            session=session,
            flags=flags,
            pipeline_result=result,
        )
        print(f"(dry-run) Turn {turn}")
        print(f"Gatekeeper codes: {result.code_line}")
        print(f"Plan slots: {len(result.plan.slots)}")
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
    prior = load_prior_grid(session, turn)
    # Ensure current user message is visible to gatekeeper
    td = session.turn_dir(turn)
    td.mkdir(parents=True, exist_ok=True)
    (td / "user-input.txt").write_text(text.strip(), encoding="utf-8")
    pipeline_result = run_pipeline(
        session, turn, prior_grid=prior, current_user_text=text
    )

    write_gatekeeper_artifacts(
        session,
        turn,
        grid_json=pipeline_result.grid.to_json(),
        plan_json=pipeline_result.plan.to_json(),
        history_json=history_to_json(pipeline_result.history),
        code_line=pipeline_result.code_line,
    )

    print(f"\n--- Uplift 3.0 · `{session.root.name}` · turn {turn:02d} ---")
    print(f"Gatekeeper: {pipeline_result.code_line}")
    print(f"Open gaps: {len(pipeline_result.open_gaps)} · Plan slots: {len(pipeline_result.plan.slots)}")

    if args.gatekeeper_only:
        print("\n(gatekeeper-only mode — no LLM call)")
        return

    t_input = time.perf_counter()
    system = load_phrasing_system_prompt()
    user_msg = build_user_message(
        turn=turn,
        user_text=text,
        session=session,
        flags=flags,
        pipeline_result=pipeline_result,
    )
    input_wall_ms = (time.perf_counter() - t_input) * 1000

    api_key = get_openai_api_key(ENV_PATH)
    key_mask = mask_api_key(api_key)
    flags_dict = flags._asdict()

    init_turns_index(session)
    rebuild_turns_index(session)
    write_turn_pending(session, turn, user_text=text, output_flags=flags_dict)

    try:
        result = call_llm(system, user_msg, api_key=api_key)
    except Exception as exc:
        write_turn_failed(session, turn, error=str(exc), api_key_mask=key_mask)
        raise SystemExit(1) from exc

    full_reply = append_state_codes(result.reply, pipeline_result.code_line)
    expected_mcqs = pipeline_result.plan.constraints.get("mcq_count", 0)
    if flags.questions and expected_mcqs > 0:
        mcq_count = count_mcq_headers(full_reply)
        vr = validate_mcq_count(expected_mcqs, mcq_count)
        if not vr.ok:
            print(f"WARNING: {vr.errors[0]}", file=sys.stderr)

    memory_after = apply_reply_to_session(
        session,
        turn,
        text,
        full_reply,
        code_line=pipeline_result.code_line,
        flags=flags,
    )

    total_ms = input_wall_ms + result.llm_wait_ms
    visible = (
        strip_memory_patch_section(full_reply)
        if flags.memory_patch
        else full_reply.strip()
    )

    write_turn_artifacts(
        session,
        turn,
        user_text=text,
        system_prompt=system,
        user_prompt=user_msg,
        llm_response=full_reply,
        state_codes=pipeline_result.code_line,
        model=result.model,
        output_flags=flags_dict,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        total_tokens=result.total_tokens,
        input_prep_ms=input_wall_ms,
        llm_wait_ms=result.llm_wait_ms,
        api_key_mask=key_mask,
        memory_after=memory_after,
        run_md_body=f"# Turn {turn:02d} — Uplift 2.0\n\nGatekeeper: `{pipeline_result.code_line}`\n",
        rubric_filename=RUBRIC_V2_FILENAME,
    )
    session.sync_turn_count_from_disk()

    append_llm_log_history(
        session,
        turn=turn,
        model=result.model,
        system_prompt=system,
        user_prompt=user_msg,
        output=full_reply,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        total_tokens=result.total_tokens,
        total_response_ms=total_ms,
        llm_wait_ms=result.llm_wait_ms,
        input_prep_ms=input_wall_ms,
        rubric_filename=RUBRIC_V2_FILENAME,
    )

    print(f"\nTiming: prep {input_wall_ms:.0f} ms · LLM {result.llm_wait_ms:.0f} ms")
    print(f"Memory: {session.memory_path}\n")
    print("## LLM response\n")
    print(visible)
    print(f"\n[continue] python uplift-2.0/test-rubric.py --continue \"follow-up\"")


if __name__ == "__main__":
    main()
