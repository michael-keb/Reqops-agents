#!/usr/bin/env python3
"""Re-build turn.json + response.md with A–D MCQs from agent markdown."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bridge import artifacts  # noqa: E402


def _source_text(turn_dir: Path) -> str:
    raw = turn_dir / "response.raw.md"
    if raw.is_file():
        return raw.read_text(encoding="utf-8")
    resp = turn_dir / "response.md"
    if resp.is_file():
        return resp.read_text(encoding="utf-8")
    return ""


def reparse_turn(turn_dir: Path) -> None:
    text = _source_text(turn_dir)
    if not text:
        print(f"skip {turn_dir}: no response markdown")
        return
    turn_num = int(turn_dir.name)
    turn_json = artifacts.build_turn_json(turn_num, text, artifacts.extract_json_block(text))
    qs = turn_json.get("questions") or []
    if artifacts._questions_have_mcq(qs):
        text = artifacts.format_mcq_markdown(turn_json.get("reflection") or "", qs)
        (turn_dir / "response.md").write_text(text, encoding="utf-8")
    (turn_dir / "turn.json").write_text(json.dumps(turn_json, indent=2) + "\n", encoding="utf-8")
    print(f"{turn_dir.name}: {len(qs)} questions, MCQ ok={artifacts._questions_have_mcq(qs)}")


def restore_raw_from_stream(session: Path) -> None:
    stream = session / "agent.stream.jsonl"
    if not stream.is_file():
        return
    results: list[str] = []
    for line in stream.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("type") == "result" and row.get("subtype") == "success" and row.get("result"):
            results.append(str(row["result"]))
    turns = sorted(d for d in (session / "turns").iterdir() if d.is_dir() and d.name.isdigit())
    for td, raw in zip(turns, results):
        (td / "response.raw.md").write_text(raw.strip() + "\n", encoding="utf-8")
        print(f"restored raw → {td.name}")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: reparse-session.py sessions/<session-id> [--from-stream]")
        return 1
    session = Path(sys.argv[1])
    if not session.is_dir():
        session = ROOT / "sessions" / sys.argv[1]
    if "--from-stream" in sys.argv:
        restore_raw_from_stream(session)
    turns = session / "turns"
    if not turns.is_dir():
        print(f"No turns/ in {session}")
        return 1
    for td in sorted(turns.iterdir()):
        if td.is_dir() and td.name.isdigit():
            reparse_turn(td)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
