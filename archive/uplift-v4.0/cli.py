#!/usr/bin/env python3
"""
Uplift 4.0 — interactive CLI (primary interface).

  python cli.py              # REPL: continue active session or start new
  python cli.py --new "…"    # one-shot new session
  python cli.py --list       # list sessions

Commands inside the REPL:
  /quit, /exit     leave
  /new             start a new session (pitch prompt)
  /sessions        list saved sessions
  /audit           show last turn multiplier-state.txt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
ENV_PATH = ROOT / ".env" if (ROOT / ".env").is_file() else REPO_ROOT / ".env"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env_config import get_openai_api_key
from run_turn import run_one_turn
from session_store import SessionStore


def read_multiline(prompt: str = "> ") -> str | None:
    """Read until empty line. Returns None on EOF."""
    print("  (empty line to send · /cancel to discard)")
    lines: list[str] = []
    try:
        while True:
            line = input(prompt if not lines else "... ")
            if line.strip() in ("/cancel", "/c"):
                return None
            if line == "" and lines:
                break
            lines.append(line)
    except (EOFError, KeyboardInterrupt):
        print()
        return None
    text = "\n".join(lines).strip()
    return text or None


def show_last_question(session) -> None:
    turns = session.list_turn_dirs()
    if not turns:
        return
    path = session.turn_dir(turns[-1]) / "llm-response.txt"
    if path.is_file():
        print("\n--- Last question ---\n")
        print(path.read_text(encoding="utf-8").strip())
        print()


def run_repl(*, dry_run: bool = False) -> None:
    store = SessionStore(ROOT)
    api_key = None if dry_run else get_openai_api_key(ENV_PATH)

    if store.active_path.is_file():
        session = store.load_active()
        print(f"\nContinuing session: {session.root.name}")
        print(f"Turns so far: {session.turn_count}")
        show_last_question(session)
    else:
        pitch = input("\nPitch (one line): ").strip()
        if not pitch:
            print("No pitch — exiting.")
            return
        session = store.create(pitch)
        print(f"\nSession: {session.root.name}\n")
        print("Thinking…")
        run_one_turn(session, pitch, dry_run=dry_run, api_key=api_key, verbose=False)

    print("\nType /help for commands.\n")

    while True:
        try:
            cmd = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not cmd:
            continue
        lower = cmd.lower()
        if lower in ("/quit", "/exit", "quit", "exit"):
            print("Bye.")
            break
        if lower == "/help":
            print(__doc__)
            continue
        if lower == "/new":
            pitch = input("Pitch (one line): ").strip()
            if not pitch:
                continue
            session = store.create(pitch)
            print(f"\nSession: {session.root.name}\nThinking…")
            run_one_turn(session, pitch, dry_run=dry_run, api_key=api_key, verbose=False)
            continue
        if lower == "/sessions":
            for sid in store.list_sessions():
                mark = " ← active" if store.active_path.is_file() and store.active_path.read_text().strip() == sid else ""
                print(f"  {sid}{mark}")
            continue
        if lower == "/audit":
            turns = session.list_turn_dirs()
            if not turns:
                print("No turns yet.")
                continue
            audit = session.turn_dir(turns[-1]) / "multiplier-state.txt"
            if audit.is_file():
                print(audit.read_text(encoding="utf-8"))
            else:
                print("(no multiplier-state.txt for last turn)")
            continue
        if lower in ("/multi", "/m"):
            print("Enter your message (multiple lines OK):")
            text = read_multiline()
            if not text:
                continue
        else:
            text = cmd

        print("\nThinking… (30–60s)\n")
        run_one_turn(session, text, dry_run=dry_run, api_key=api_key, verbose=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Uplift 4.0 interactive CLI")
    parser.add_argument("--new", metavar="PITCH", help="Start one turn on a new session")
    parser.add_argument("--continue", dest="cont", metavar="MSG", help="One continue turn")
    parser.add_argument("--list", action="store_true", help="List sessions")
    parser.add_argument("--dry-run", action="store_true", help="No API calls")
    parser.add_argument("--json", action="store_true", help="Print selection JSON (audit)")
    args = parser.parse_args()

    store = SessionStore(ROOT)

    if args.list:
        active = store.active_path.read_text(encoding="utf-8").strip() if store.active_path.is_file() else None
        for sid in store.list_sessions():
            mark = " ← active" if sid == active else ""
            print(f"{sid}{mark}")
        return

    api_key = None if args.dry_run else get_openai_api_key(ENV_PATH)

    if args.new:
        session = store.create(args.new)
        run_one_turn(session, args.new, dry_run=args.dry_run, api_key=api_key, verbose=args.json)
        return
    if args.cont:
        session = store.load_active()
        run_one_turn(session, args.cont, dry_run=args.dry_run, api_key=api_key, verbose=args.json)
        return

    run_repl(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
