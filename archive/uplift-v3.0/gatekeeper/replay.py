"""Offline replay of gatekeeper pipeline against session folders."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gatekeeper.history import build_history_from_turn_files
from gatekeeper.pipeline import run_pipeline
from session_store import Session, SessionStore


def replay_session(session_path: Path, *, write: bool = False) -> None:
    meta = json.loads((session_path / "session.meta.json").read_text(encoding="utf-8"))
    session = Session(root=session_path, meta=meta)
    turn_nums = session.list_turn_dirs()
    if not turn_nums:
        print(f"No turns in {session_path}")
        return

    prior = None
    for n in turn_nums:
        # Build history through turn n (simulate live turn)
        result = run_pipeline(session, n, prior_grid=prior)
        print(f"\n=== Turn {n:02d} ===")
        print(f"Phase: {result.grid.phase}")
        print(f"Open gaps: {len(result.open_gaps)}")
        print(f"Codes: {result.code_line}")
        print(f"Plan slots: {len(result.plan.slots)} ({result.plan.constraints.get('gap_slots', 0)} gap + Q7)")

        if write:
            d = session.turn_dir(n)
            (d / "grid.json").write_text(result.grid.to_json(), encoding="utf-8")
            (d / "question-plan.json").write_text(result.plan.to_json(), encoding="utf-8")
            hist = build_history_from_turn_files(
                session.read_pitch(), session.turns_dir, through_turn=n
            )
            (d / "history.json").write_text(
                json.dumps(
                    {
                        "pitch": hist.pitch,
                        "turns": [{"turn": t.turn, "raw_text": t.raw_text} for t in hist.turns],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

        prior = result.grid


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay gatekeeper on a session")
    parser.add_argument("session", help="Session folder path or id under uplift-2.0/sessions")
    parser.add_argument("--write", action="store_true", help="Write grid.json artifacts")
    parser.add_argument(
        "--import-legacy",
        help="Import user turns from legacy sessions/<id> into uplift replay (read-only)",
    )
    args = parser.parse_args()

    path = Path(args.session)
    if not path.is_dir():
        store = SessionStore(ROOT)
        path = store.sessions_dir / args.session
    if args.import_legacy:
        legacy = ROOT.parent / "sessions" / args.import_legacy
        if not legacy.is_dir():
            sys.exit(f"Legacy session not found: {legacy}")
        path = legacy

    if not path.is_dir():
        sys.exit(f"Session not found: {path}")

    replay_session(path, write=args.write)


if __name__ == "__main__":
    main()
