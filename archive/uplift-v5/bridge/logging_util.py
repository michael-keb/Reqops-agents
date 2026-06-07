"""Terminal logging for bridge + agent runs."""

from __future__ import annotations

import os
import shlex
import sys
from pathlib import Path

from bridge.terminal_log import emit

ROOT = Path(__file__).resolve().parent.parent
QUIET = os.environ.get("UPLIFT_QUIET", "").strip() in ("1", "true", "yes")


def log(msg: str = "", *, kind: str = "sys") -> None:
    emit(msg, kind=kind)
    if QUIET:
        return
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()


def fmt_cmd(cmd: list[str]) -> str:
    parts: list[str] = []
    skip_next = False
    for i, arg in enumerate(cmd):
        if skip_next:
            skip_next = False
            continue
        if arg in ("-p", "--resume") and i + 1 < len(cmd):
            if arg == "-p":
                parts.extend(["-p", "<prompt>"])
            else:
                parts.extend(["--resume", cmd[i + 1][:8] + "…" if len(cmd[i + 1]) > 8 else cmd[i + 1]])
            skip_next = True
        else:
            parts.append(shlex.quote(arg))
    return " ".join(parts)


def log_turn_start(
    *,
    turn: int,
    session_dir: Path,
    user_text: str,
    new_session: bool,
    chat_id: str | None,
    persistent: bool,
) -> None:
    kind = "new session" if new_session else "continue"
    preview = user_text.strip().replace("\n", " ")
    if len(preview) > 100:
        preview = preview[:97] + "…"
    chat = f" · chat {chat_id[:8]}…" if chat_id else ""
    mode = "persistent" if persistent else "one-shot"
    log("")
    log(f"{'─' * 60}")
    log(f"turn {turn:02d} · {session_dir.name} · {kind} · {mode}{chat}")
    log(f"input: {preview or '(empty)'}")
    log(f"{'─' * 60}")


def log_turn_summary(session_dir: Path, turn: int, elapsed_s: float, turn_data: dict | None) -> None:
    log(f"done in {elapsed_s:.1f}s")
    if turn_data:
        gap = turn_data.get("primary_gap", "?")
        mode = turn_data.get("mode", "?")
        score = turn_data.get("score", "?")
        dom = turn_data.get("dominant_term", "?")
        log(f"  → {gap} · {mode} · score {score} · {dom}")
        why = (turn_data.get("why_now") or "").strip()
        if why:
            short = why if len(why) <= 120 else why[:117] + "…"
            log(f"  why: {short}")
    audit = session_dir / "turns" / f"{turn:02d}" / "multiplier-audit.txt"
    if audit.is_file():
        try:
            log(f"  audit: {audit.resolve().relative_to(ROOT.resolve())}")
        except ValueError:
            log(f"  audit: {audit}")
    resp = session_dir / "turns" / f"{turn:02d}" / "response.md"
    if resp.is_file():
        try:
            log(f"  response: {resp.resolve().relative_to(ROOT.resolve())}")
        except ValueError:
            log(f"  response: {resp}")
    log(f"{'─' * 60}")
    log("")
