"""Per-session folders for Uplift 4.0."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

SESSIONS_DIR_NAME = "sessions"
MEMORY_FILE = "Memory.md"
LOG_HISTORY_FILE = "log-history.md"
META_FILE = "session.meta.json"
ACTIVE_FILE = ".active"
TURNS_DIR = "turns"
TURNS_INDEX_FILE = "README.md"
TURN_META_FILE = "meta.json"
MAX_COMPRESSED_CHARS = 2400


def slugify(text: str, max_len: int = 48) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower().strip())
    s = s.strip("-") or "session"
    return s[:max_len].rstrip("-")


MEMORY_TEMPLATE = """# Discovery memory (Uplift 4.0)

> Patched after each turn. User messages are source of truth.

## Pitch
{pitch}

## Settled facts (user-confirmed only)
{facts}

## Compressed conversation
{compressed}
"""


@dataclass
class MemoryPatch:
    pitch: str | None = None
    facts: list[str] = field(default_factory=list)
    turn_summary: str | None = None


@dataclass
class Session:
    root: Path
    meta: dict

    @property
    def memory_path(self) -> Path:
        return self.root / MEMORY_FILE

    @property
    def log_history_path(self) -> Path:
        return self.root / LOG_HISTORY_FILE

    @property
    def turns_dir(self) -> Path:
        return self.root / TURNS_DIR

    @property
    def turn_count(self) -> int:
        return int(self.meta.get("turn_count", 0))

    def read_memory(self) -> str:
        return self.memory_path.read_text(encoding="utf-8")

    def read_memory_for_llm(self) -> str:
        return self.read_memory()

    def read_compressed_history(self) -> str:
        text = self.read_memory()
        m = re.search(
            r"## Compressed conversation\s*\n(.*?)(?=\n## |\Z)",
            text,
            re.DOTALL,
        )
        block = (m.group(1).strip() if m else "") or "_(empty)_"
        return block if block != "_(empty)_" else ""

    def read_pitch(self) -> str:
        text = self.read_memory()
        m = re.search(r"## Pitch\s*\n(.*?)(?=\n## )", text, re.DOTALL)
        if not m:
            return self.meta.get("initial_intent", "")
        pitch = m.group(1).strip()
        if not pitch or pitch in ("_(not set)_", "_(none)_"):
            return self.meta.get("initial_intent", "")
        return pitch

    def read_facts(self) -> list[str]:
        text = self.read_memory()
        m = re.search(
            r"## Settled facts \(user-confirmed only\)\s*\n(.*?)(?=\n## )",
            text,
            re.DOTALL,
        )
        if not m:
            return []
        return [
            ln.strip().lstrip("-").strip()
            for ln in m.group(1).splitlines()
            if ln.strip().startswith("-")
        ]

    def apply_patch(self, patch: MemoryPatch, *, turn: int) -> None:
        pitch = patch.pitch or self.read_pitch() or "_(not set)_"
        facts = list(self.read_facts())
        for f in patch.facts:
            if f and f not in facts:
                facts.append(f)
        facts_block = "\n".join(f"- {f}" for f in facts) if facts else "_(none)_"
        compressed = self.read_compressed_history()
        if patch.turn_summary:
            summary = patch.turn_summary.strip()
            if not re.match(rf"^T{turn}\b", summary, re.I):
                summary = f"T{turn} — {summary}"
            compressed = f"{compressed}\n{summary}".strip() if compressed else summary
        compressed = trim_compressed(compressed) or "_(empty)_"
        body = MEMORY_TEMPLATE.format(pitch=pitch, facts=facts_block, compressed=compressed)
        self.memory_path.write_text(body, encoding="utf-8")

    def next_turn_number(self) -> int:
        return self.turn_count + 1

    def record_turn_completed(self) -> int:
        n = self.next_turn_number()
        self.meta["turn_count"] = n
        self.meta["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._write_meta()
        return n

    def turn_dir(self, turn: int) -> Path:
        d = self.turns_dir / f"{turn:02d}"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def list_turn_dirs(self) -> list[int]:
        if not self.turns_dir.is_dir():
            return []
        return sorted(
            int(p.name)
            for p in self.turns_dir.iterdir()
            if p.is_dir() and re.fullmatch(r"\d{2}", p.name)
        )

    def _write_meta(self) -> None:
        (self.root / META_FILE).write_text(
            json.dumps(self.meta, indent=2), encoding="utf-8"
        )


class SessionStore:
    def __init__(self, project_root: Path) -> None:
        self.sessions_dir = project_root / SESSIONS_DIR_NAME
        self.sessions_dir.mkdir(exist_ok=True)
        self.active_path = self.sessions_dir / ACTIVE_FILE

    def create(self, initial_intent: str) -> Session:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        folder = self.sessions_dir / f"{stamp}-{slugify(initial_intent)}"
        folder.mkdir(parents=True, exist_ok=False)
        (folder / TURNS_DIR).mkdir(exist_ok=True)
        meta = {
            "id": folder.name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "initial_intent": initial_intent,
            "turn_count": 0,
            "version": "4.0",
        }
        (folder / META_FILE).write_text(json.dumps(meta, indent=2), encoding="utf-8")
        session = Session(root=folder, meta=meta)
        session.memory_path.write_text(
            MEMORY_TEMPLATE.format(
                pitch=initial_intent,
                facts="_(none)_",
                compressed="_(empty)_",
            ),
            encoding="utf-8",
        )
        init_log_history(session)
        self.set_active(session)
        return session

    def set_active(self, session: Session) -> None:
        self.active_path.write_text(session.root.name, encoding="utf-8")

    def load_active(self) -> Session:
        if not self.active_path.is_file():
            sys.exit(
                'No active session. Start: python run_turn.py --new "your intent"'
            )
        return self.load(self.active_path.read_text(encoding="utf-8").strip())

    def load(self, session_id: str) -> Session:
        path = self.sessions_dir / session_id
        if not path.is_dir():
            sys.exit(f"Session not found: {path}")
        meta = json.loads((path / META_FILE).read_text(encoding="utf-8"))
        return Session(root=path, meta=meta)

    def list_sessions(self) -> list[str]:
        return sorted(
            p.name
            for p in self.sessions_dir.iterdir()
            if p.is_dir() and (p / META_FILE).is_file()
        )


def trim_compressed(text: str) -> str:
    text = text.strip()
    if len(text) <= MAX_COMPRESSED_CHARS:
        return text
    lines = text.splitlines()
    while lines and len("\n".join(lines)) > MAX_COMPRESSED_CHARS:
        lines.pop(0)
    return f"[…earlier turns dropped…]\n" + "\n".join(lines)


def write_analyst_artifacts(
    session: Session,
    turn: int,
    *,
    grid_json: str,
    selection_json: str,
    scored_json: str,
    history_json: str,
    multiplier_state: str = "",
) -> Path:
    d = session.turn_dir(turn)
    (d / "grid.json").write_text(grid_json, encoding="utf-8")
    (d / "selection.json").write_text(selection_json, encoding="utf-8")
    (d / "scored-candidates.json").write_text(scored_json, encoding="utf-8")
    (d / "history.json").write_text(history_json, encoding="utf-8")
    if multiplier_state:
        (d / "multiplier-state.txt").write_text(multiplier_state, encoding="utf-8")
    return d


def write_turn_artifacts(
    session: Session,
    turn: int,
    *,
    user_text: str,
    score_system: str,
    score_user: str,
    score_response: str,
    phrase_system: str,
    phrase_user: str,
    llm_response: str,
    model: str,
    score_wait_ms: float,
    phrase_wait_ms: float,
    input_prep_ms: float,
) -> Path:
    d = session.turn_dir(turn)
    (d / "user-input.txt").write_text(user_text.strip(), encoding="utf-8")
    (d / "score-system.txt").write_text(score_system, encoding="utf-8")
    (d / "score-user.txt").write_text(score_user, encoding="utf-8")
    (d / "score-response.json").write_text(score_response, encoding="utf-8")
    (d / "phrase-system.txt").write_text(phrase_system, encoding="utf-8")
    (d / "phrase-user.txt").write_text(phrase_user, encoding="utf-8")
    (d / "llm-response.txt").write_text(llm_response.strip(), encoding="utf-8")
    (d / "prompt-sent.txt").write_text(
        f"=== SCORE SYSTEM ===\n{score_system}\n\n"
        f"=== SCORE USER ===\n{score_user}\n\n"
        f"=== PHRASE SYSTEM ===\n{phrase_system}\n\n"
        f"=== PHRASE USER ===\n{phrase_user}",
        encoding="utf-8",
    )
    meta = {
        "turn": turn,
        "status": "ok",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "score_wait_ms": round(score_wait_ms, 1),
        "phrase_wait_ms": round(phrase_wait_ms, 1),
        "input_prep_ms": round(input_prep_ms, 1),
        "total_response_ms": round(input_prep_ms + score_wait_ms + phrase_wait_ms, 1),
    }
    (d / TURN_META_FILE).write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return d


LOG_HISTORY_HEADER = """# LLM log history (Uplift 4.0)

Session: `{session_id}`  
Created: {created}

Rolling log of every turn — score LLM + phrase LLM + selection.

## Summary

| Turn | Input tokens | Output tokens | Total tokens | Response time |
|------|-------------:|--------------:|-------------:|--------------:|
"""


def init_log_history(session: Session) -> None:
    created = session.meta.get("created_at", datetime.now(timezone.utc).isoformat())
    session.log_history_path.write_text(
        LOG_HISTORY_HEADER.format(session_id=session.root.name, created=created),
        encoding="utf-8",
    )


def _fmt_tokens(n: int | None) -> str:
    return f"{n:,}" if n is not None else "—"


def _fence(body: str) -> str:
    safe = body.replace("```", "``\\`")
    return f"```text\n{safe}\n```"


def append_turn_log_history(
    session: Session,
    *,
    turn: int,
    user_text: str,
    score_system: str,
    score_user: str,
    score_output: str,
    phrase_system: str,
    phrase_user: str,
    phrase_output: str,
    selection_json: str,
    model: str,
    score_prompt_tokens: int | None = None,
    score_completion_tokens: int | None = None,
    phrase_prompt_tokens: int | None = None,
    phrase_completion_tokens: int | None = None,
    score_wait_ms: float = 0.0,
    phrase_wait_ms: float = 0.0,
    input_prep_ms: float = 0.0,
    rubric_filename: str = "llm_rubric_multiplier.md",
) -> Path:
    """Append one turn block: score call, phrase call, selection audit."""
    path = session.log_history_path
    if not path.is_file():
        init_log_history(session)

    in_tok = (score_prompt_tokens or 0) + (phrase_prompt_tokens or 0)
    out_tok = (score_completion_tokens or 0) + (phrase_completion_tokens or 0)
    total_tok = in_tok + out_tok if in_tok or out_tok else None
    total_ms = input_prep_ms + score_wait_ms + phrase_wait_ms

    in_disp = _fmt_tokens(in_tok if in_tok else None)
    out_disp = _fmt_tokens(out_tok if out_tok else None)
    tot_disp = _fmt_tokens(total_tok)
    summary_row = (
        f"| {turn:02d} | {in_disp} | {out_disp} | {tot_disp} | {total_ms / 1000:.3f} s |"
    )

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("|------|") and i > 0 and "Turn" in lines[i - 1]:
            lines.insert(i + 1, summary_row)
            break
    else:
        lines.append(summary_row)
    text = "\n".join(lines) + "\n"

    recorded = datetime.now(timezone.utc).isoformat()
    score_sent = (
        f"=== SCORE SYSTEM — {rubric_filename} ({len(score_system):,} chars) ===\n\n"
        f"{score_system}\n\n"
        f"=== SCORE USER ({len(score_user):,} chars) ===\n\n"
        f"{score_user}"
    )
    phrase_sent = (
        f"=== PHRASE SYSTEM ({len(phrase_system):,} chars) ===\n\n"
        f"{phrase_system}\n\n"
        f"=== PHRASE USER ({len(phrase_user):,} chars) ===\n\n"
        f"{phrase_user}"
    )
    score_tok = (
        f"{_fmt_tokens(score_prompt_tokens)} / {_fmt_tokens(score_completion_tokens)}"
    )
    phrase_tok = (
        f"{_fmt_tokens(phrase_prompt_tokens)} / {_fmt_tokens(phrase_completion_tokens)}"
    )

    turn_section = f"""
---

## Turn {turn:02d} — {recorded}

**User input:** {_fence(user_text.strip())}

**Model:** `{model}` · prep {input_prep_ms:.0f} ms · score wait {score_wait_ms:.0f} ms · phrase wait {phrase_wait_ms:.0f} ms

### Selection (deterministic)

{_fence(selection_json)}

### 1 — Score LLM (I/C/E drivers)

| Sent | Output | Tokens (in/out) | Wait |
|------|--------|-----------------|------|
| {len(score_sent):,} chars | {len(score_output.strip()):,} chars | {score_tok} | {score_wait_ms:.0f} ms |

#### Score — sent

{_fence(score_sent)}

#### Score — output

{_fence(score_output.strip())}

### 2 — Phrase LLM (MCQ)

| Sent | Output | Tokens (in/out) | Wait |
|------|--------|-----------------|------|
| {len(phrase_sent):,} chars | {len(phrase_output.strip()):,} chars | {phrase_tok} | {phrase_wait_ms:.0f} ms |

#### Phrase — sent

{_fence(phrase_sent)}

#### Phrase — output

{_fence(phrase_output.strip())}
"""
    path.write_text(text.rstrip() + "\n" + turn_section, encoding="utf-8")
    return path
