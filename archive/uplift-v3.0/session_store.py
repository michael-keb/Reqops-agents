"""Per-session folders: Memory.md, compressed history, turn logs."""

from __future__ import annotations

import json
import re
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


MEMORY_TEMPLATE = """# Discovery memory (Uplift 2.0 — gatekeeper)

> Patched after each LLM turn. **User messages are source of truth.** State codes below
> are the gatekeeper's last declared read (audit only). Next turn re-derives from user
> history via `grid.json`, not from this line.

## Pitch
{pitch}

## Latest state codes (gatekeeper authoritative)
{state_codes}

## Settled facts (user-confirmed only)
{facts}

## Compressed conversation
{compressed}
"""


@dataclass
class MemoryPatch:
    pitch: str | None = None
    state_codes: str | None = None
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
        """Session memory for LLM prompts — omits sections duplicated elsewhere in the turn message."""
        text = self.read_memory()
        text = re.sub(
            r"## Latest state codes \(gatekeeper authoritative\)\s*\n.*?(?=\n## |\Z)",
            "",
            text,
            flags=re.DOTALL,
        )
        text = re.sub(
            r"## Settled facts \(user-confirmed only\)\s*\n.*?(?=\n## |\Z)",
            "",
            text,
            flags=re.DOTALL,
        )
        return re.sub(r"\n{3,}", "\n\n", text).strip()

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
        if not pitch or pitch.startswith("##") or pitch in ("_(not set)_", "_(none)_"):
            return self.meta.get("initial_intent", "")
        return pitch

    def read_state_codes(self) -> str:
        text = self.read_memory()
        m = re.search(r"## Latest state codes\s*\n(.*?)(?=\n## )", text, re.DOTALL)
        if not m:
            return ""
        codes = m.group(1).strip()
        return "" if codes in ("_(none)_", "_(not set)_") else codes

    def read_facts(self) -> list[str]:
        text = self.read_memory()
        m = re.search(
            r"## Settled facts \(user-confirmed only\)\s*\n(.*?)(?=\n## )",
            text,
            re.DOTALL,
        )
        if not m:
            return []
        lines = [
            ln.strip().lstrip("-").strip()
            for ln in m.group(1).splitlines()
            if ln.strip().startswith("-")
        ]
        return [ln for ln in lines if ln and not ln.startswith("_")]

    def apply_patch(self, patch: MemoryPatch, *, turn: int) -> None:
        pitch = patch.pitch or self.read_pitch() or "_(not set)_"
        codes = patch.state_codes or self.read_state_codes() or "_(none)_"
        facts = list(self.read_facts())
        skip = {"none", "n/a", "_(none)_"}
        for f in patch.facts:
            if f and f.lower() not in skip and f not in facts:
                facts.append(f)
        facts_block = "\n".join(f"- {f}" for f in facts) if facts else "_(none)_"

        compressed = self.read_compressed_history()
        if patch.turn_summary:
            summary = patch.turn_summary.strip()
            if not re.match(rf"^T{turn}\b", summary, re.I):
                summary = f"T{turn} — {summary}"
            compressed = f"{compressed}\n{summary}".strip() if compressed else summary
        compressed = trim_compressed(compressed)
        if not compressed:
            compressed = "_(empty)_"

        body = MEMORY_TEMPLATE.format(
            pitch=pitch,
            state_codes=codes,
            facts=facts_block,
            compressed=compressed,
        )
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
        nums: list[int] = []
        for p in self.turns_dir.iterdir():
            if p.is_dir() and re.fullmatch(r"\d{2}", p.name):
                nums.append(int(p.name))
        return sorted(nums)

    def sync_turn_count_from_disk(self) -> None:
        """Align meta turn_count with completed turn folders (meta.json status=ok)."""
        ok = 0
        for n in self.list_turn_dirs():
            meta_path = self.turn_dir(n) / TURN_META_FILE
            if meta_path.is_file():
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                if meta.get("status") == "ok":
                    ok = max(ok, n)
        if ok != self.turn_count:
            self.meta["turn_count"] = ok
            self._write_meta()

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
        }
        (folder / META_FILE).write_text(json.dumps(meta, indent=2), encoding="utf-8")

        session = Session(root=folder, meta=meta)
        session.memory_path.write_text(
            MEMORY_TEMPLATE.format(
                pitch=initial_intent,
                state_codes="_(none)_",
                facts="_(none)_",
                compressed="_(empty)_",
            ),
            encoding="utf-8",
        )
        init_log_history(session, initial_intent)
        init_turns_index(session)
        self.set_active(session)
        return session

    def set_active(self, session: Session) -> None:
        self.active_path.write_text(session.root.name, encoding="utf-8")

    def load_active(self) -> Session:
        if not self.active_path.is_file():
            sys_exit_no_active()
        sid = self.active_path.read_text(encoding="utf-8").strip()
        return self.load(sid)

    def load(self, session_id: str) -> Session:
        path = self.sessions_dir / session_id
        if not path.is_dir():
            sys.exit(f"Session not found: {path}")
        meta = json.loads((path / META_FILE).read_text(encoding="utf-8"))
        return Session(root=path, meta=meta)

    def list_sessions(self) -> list[str]:
        skip = {"_dry_run_preview"}
        return sorted(
            p.name
            for p in self.sessions_dir.iterdir()
            if p.is_dir()
            and p.name not in skip
            and (p / META_FILE).is_file()
        )


def preview_session(sessions_dir: Path, intent: str) -> Session:
    """In-memory-ish session for dry-run (writes under _dry_run_preview only)."""
    root = sessions_dir / "_dry_run_preview"
    root.mkdir(parents=True, exist_ok=True)
    meta = {"turn_count": 0, "initial_intent": intent, "id": "_dry_run_preview"}
    session = Session(root=root, meta=meta)
    session.memory_path.write_text(
        MEMORY_TEMPLATE.format(
            pitch=intent,
            state_codes="_(none)_",
            facts="_(none)_",
            compressed="_(empty)_",
        ),
        encoding="utf-8",
    )
    return session


def sys_exit_no_active() -> None:
    import sys

    sys.exit(
        "No active session. Start one with:\n"
        '  python test-rubric.py "your intent"\n'
        "Or pass --session <id> to continue a specific session."
    )


def memory_for_phrasing_prompt(memory: str) -> str:
    """Drop Memory.md sections already sent elsewhere in the phrasing user message."""
    text = re.sub(
        r"## Latest state codes \(gatekeeper authoritative\)\s*\n.*?(?=\n## |\Z)",
        "",
        memory,
        count=1,
        flags=re.DOTALL,
    )
    return re.sub(r"\n{3,}", "\n\n", text.strip())


def trim_compressed(text: str) -> str:
    text = text.strip()
    if len(text) <= MAX_COMPRESSED_CHARS:
        return text
    lines = text.splitlines()
    while lines and len("\n".join(lines)) > MAX_COMPRESSED_CHARS:
        lines.pop(0)
    trimmed = "\n".join(lines)
    return f"[…earlier turns dropped…]\n{trimmed}"


def parse_memory_patch(reply: str) -> MemoryPatch:
    """Extract ## Memory patch section from LLM reply."""
    patch = MemoryPatch()
    m = re.search(
        r"## Memory patch\s*\n(.*?)(?=\n## |\Z)",
        reply,
        re.DOTALL | re.IGNORECASE,
    )
    if not m:
        return patch

    block = m.group(1).strip()
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- "):
            patch.facts.append(line[2:].strip())
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip().lower(), val.strip()
        if key == "pitch" and val:
            patch.pitch = val
        elif key in ("state_codes", "state codes", "codes") and val:
            patch.state_codes = val
        elif key in ("turn_summary", "turn summary", "summary") and val:
            patch.turn_summary = val
        elif key == "facts" and val:
            patch.facts.append(val)

    return patch


def extract_state_codes(reply: str) -> str:
    for line in reply.splitlines():
        stripped = line.strip().strip("`")
        if stripped.startswith("P") and ("G" in stripped or "G0" in stripped):
            return stripped
        if re.match(r"^P[1-4]\s", stripped):
            return stripped
    return ""


def strip_memory_patch_section(reply: str) -> str:
    return re.sub(
        r"\n## Memory patch\s*\n.*",
        "",
        reply,
        flags=re.DOTALL | re.IGNORECASE,
    ).strip()


LOG_HISTORY_HEADER = """# LLM log history

Session: `{session_id}`  
Created: {created}

Rolling log of every API call in this session.

## Summary

| Turn | Input tokens | Output tokens | Total tokens | Response time |
|------|-------------:|--------------:|-------------:|--------------:|
"""


def init_log_history(session: Session, initial_intent: str) -> None:
    created = session.meta.get("created_at", datetime.now(timezone.utc).isoformat())
    session.log_history_path.write_text(
        LOG_HISTORY_HEADER.format(session_id=session.root.name, created=created),
        encoding="utf-8",
    )


def _fmt_tokens(n: int | None) -> str:
    return f"{n:,}" if n is not None else "—"


def _fence(body: str) -> str:
    """Fenced block; escape inner backticks."""
    safe = body.replace("```", "``\\`")
    return f"```text\n{safe}\n```"


def append_llm_log_history(
    session: Session,
    *,
    turn: int,
    model: str,
    system_prompt: str,
    user_prompt: str,
    output: str,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    total_tokens: int | None,
    total_response_ms: float,
    llm_wait_ms: float,
    input_prep_ms: float,
    rubric_filename: str = "llm-rubric_v2.md",
) -> Path:
    """Append summary row + per-turn 4-field table with full payloads below."""
    path = session.log_history_path
    if not path.is_file():
        init_log_history(session, session.meta.get("initial_intent", ""))

    sent_full = (
        f"=== SYSTEM — {rubric_filename} only ({len(system_prompt):,} chars) ===\n\n"
        f"{system_prompt}\n\n"
        f"=== USER — turn context ({len(user_prompt):,} chars) ===\n\n"
        f"{user_prompt}"
    )
    output_full = output.strip()
    total_s = total_response_ms / 1000
    recorded = datetime.now(timezone.utc).isoformat()
    in_tok = _fmt_tokens(prompt_tokens)
    out_tok = _fmt_tokens(completion_tokens)
    tot_tok = _fmt_tokens(total_tokens)
    tok_cell = f"{in_tok} / {out_tok}"
    sent_anchor = f"turn-{turn:02d}-sent"
    out_anchor = f"turn-{turn:02d}-output"

    summary_row = (
        f"| {turn:02d} | {in_tok} | {out_tok} | {tot_tok} | {total_s:.3f} s |"
    )

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    insert_at = None
    for i, line in enumerate(lines):
        if line.startswith("|------|") and "Turn" in (lines[i - 1] if i else ""):
            insert_at = i + 1
            break
    if insert_at is not None:
        lines.insert(insert_at, summary_row)
        text = "\n".join(lines) + "\n"
    else:
        text = text.rstrip() + "\n" + summary_row + "\n"

    turn_section = f"""
---

## Turn {turn:02d} — {recorded}

**Model:** `{model}` · prep {input_prep_ms:.0f} ms · API wait {llm_wait_ms:.0f} ms

| # | What was sent to the LLM | Output | Token spend (input / output) | Total response time |
|---|--------------------------|--------|------------------------------|---------------------|
| **{turn:02d}** | [{len(sent_full):,} chars — expand](#{sent_anchor}) | [{len(output_full):,} chars — expand](#{out_anchor}) | **{tok_cell}** (Σ {tot_tok}) | **{total_response_ms:.1f} ms** ({total_s:.3f} s) |

#### <a id="{sent_anchor}"></a> 1 — What was sent to the LLM

{_fence(sent_full)}

#### <a id="{out_anchor}"></a> 2 — Output

{_fence(output_full)}
"""
    path.write_text(text.rstrip() + "\n" + turn_section, encoding="utf-8")
    return path


TURNS_INDEX_TEMPLATE = """# Turns

Session: `{session_id}`

| Turn | Status | State codes | Tokens (in/out) | Time | Folder |
|------|--------|-------------|-------------------|------|--------|
"""


def init_turns_index(session: Session) -> None:
    session.turns_dir.mkdir(parents=True, exist_ok=True)
    path = session.turns_dir / TURNS_INDEX_FILE
    if not path.is_file():
        path.write_text(
            TURNS_INDEX_TEMPLATE.format(session_id=session.root.name),
            encoding="utf-8",
        )


def _legacy_turn_codes(turn_dir: Path) -> str:
    codes_file = turn_dir / "state-codes.txt"
    if codes_file.is_file():
        return codes_file.read_text(encoding="utf-8").strip()
    run_md = turn_dir / "run.md"
    if run_md.is_file():
        for line in run_md.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s.startswith("P") and ("G" in s or re.match(r"^P[1-4]\s", s)):
                return s
    return "—"


def rebuild_turns_index(session: Session) -> None:
    """Rebuild turns/README.md from each turn's meta.json (or legacy run.md)."""
    init_turns_index(session)
    rows: list[str] = []
    for n in session.list_turn_dirs():
        d = session.turn_dir(n)
        meta_path = d / TURN_META_FILE
        if meta_path.is_file():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        else:
            codes = _legacy_turn_codes(d)
            meta = {"turn": n, "status": "ok (legacy)", "state_codes": codes}
            run_md = d / "run.md"
            if run_md.is_file():
                body = run_md.read_text(encoding="utf-8")
                m = re.search(r"LLM wait time \(processing\)\s*\|\s*([\d.]+)", body)
                if m:
                    meta["total_response_ms"] = float(m.group(1))
                m2 = re.search(r"Input \(prompt\)\s*\|\s*(\d+)", body)
                m3 = re.search(r"Output \(completion\)\s*\|\s*(\d+)", body)
                if m2:
                    meta["prompt_tokens"] = int(m2.group(1))
                if m3:
                    meta["completion_tokens"] = int(m3.group(1))
        codes = meta.get("state_codes") or "—"
        tok = f"{meta.get('prompt_tokens', '—')} / {meta.get('completion_tokens', '—')}"
        t_ms = meta.get("total_response_ms")
        time_s = f"{t_ms / 1000:.3f} s" if isinstance(t_ms, (int, float)) else "—"
        status = meta.get("status", "?")
        rows.append(
            f"| {n:02d} | {status} | `{codes}` | {tok} | {time_s} | `{n:02d}/` |"
        )
    body = TURNS_INDEX_TEMPLATE.format(session_id=session.root.name)
    if rows:
        body += "\n".join(rows) + "\n"
    (session.turns_dir / TURNS_INDEX_FILE).write_text(body, encoding="utf-8")


def _append_turns_index_row(session: Session, turn_meta: dict) -> None:
    init_turns_index(session)
    path = session.turns_dir / TURNS_INDEX_FILE
    codes = turn_meta.get("state_codes") or "—"
    tok = f"{turn_meta.get('prompt_tokens', '—')} / {turn_meta.get('completion_tokens', '—')}"
    t_ms = turn_meta.get("total_response_ms")
    time_s = f"{t_ms / 1000:.3f} s" if isinstance(t_ms, (int, float)) else "—"
    status = turn_meta.get("status", "?")
    row = (
        f"| {turn_meta['turn']:02d} | {status} | `{codes}` | {tok} | {time_s} | "
        f"`{turn_meta['turn']:02d}/` |"
    )
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("|------|"):
            lines.insert(i + 1, row)
            break
    else:
        lines.append(row)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_turn_pending(
    session: Session,
    turn: int,
    *,
    user_text: str,
    output_flags: dict,
) -> Path:
    """Create turn folder before API call."""
    d = session.turn_dir(turn)
    (d / "user-input.txt").write_text(user_text.strip(), encoding="utf-8")
    meta = {
        "turn": turn,
        "status": "pending",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "user_input": user_text.strip(),
        "output_flags": output_flags,
    }
    (d / TURN_META_FILE).write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return d


def write_turn_failed(
    session: Session,
    turn: int,
    *,
    error: str,
    api_key_mask: str,
) -> Path:
    d = session.turn_dir(turn)
    meta_path = d / TURN_META_FILE
    meta = {}
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta.update(
        {
            "turn": turn,
            "status": "failed",
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "error": error,
            "api_key": api_key_mask,
        }
    )
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (d / "error.md").write_text(
        f"# Turn {turn:02d} — failed\n\n**API key:** `{api_key_mask}`\n\n```\n{error}\n```\n",
        encoding="utf-8",
    )
    _append_turns_index_row(session, meta)
    return d


def write_turn_artifacts(
    session: Session,
    turn: int,
    *,
    user_text: str,
    system_prompt: str,
    user_prompt: str,
    llm_response: str,
    state_codes: str,
    model: str,
    output_flags: dict,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    total_tokens: int | None,
    input_prep_ms: float,
    llm_wait_ms: float,
    api_key_mask: str,
    memory_after: str,
    run_md_body: str,
    rubric_filename: str = "llm-rubric_v2.md",
) -> Path:
    """Write standard turn folder layout after a successful API call."""
    d = session.turn_dir(turn)
    total_ms = input_prep_ms + llm_wait_ms
    rubric_copy = d / rubric_filename

    (d / "user-input.txt").write_text(user_text.strip(), encoding="utf-8")
    (d / "system-prompt.txt").write_text(system_prompt, encoding="utf-8")
    rubric_copy.write_text(system_prompt, encoding="utf-8")
    (d / "user-prompt.txt").write_text(user_prompt, encoding="utf-8")
    (d / "llm-response.txt").write_text(llm_response.strip(), encoding="utf-8")
    (d / "state-codes.txt").write_text(state_codes.strip() + "\n", encoding="utf-8")
    (d / "prompt-sent.txt").write_text(
        f"=== SYSTEM ({rubric_filename} only) ===\n\n{system_prompt}\n\n"
        f"=== USER (turn context + output format) ===\n\n{user_prompt}",
        encoding="utf-8",
    )
    (d / "run.md").write_text(run_md_body, encoding="utf-8")

    meta = {
        "turn": turn,
        "status": "ok",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "api_key": api_key_mask,
        "state_codes": state_codes,
        "output_flags": output_flags,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "input_prep_ms": round(input_prep_ms, 1),
        "llm_wait_ms": round(llm_wait_ms, 1),
        "total_response_ms": round(total_ms, 1),
    }
    (d / TURN_META_FILE).write_text(json.dumps(meta, indent=2), encoding="utf-8")
    _append_turns_index_row(session, meta)
    return d


def write_gatekeeper_artifacts(
    session: Session,
    turn: int,
    *,
    grid_json: str,
    plan_json: str,
    history_json: str,
    code_line: str,
) -> Path:
    """Write gatekeeper outputs before/after LLM call."""
    d = session.turn_dir(turn)
    (d / "grid.json").write_text(grid_json, encoding="utf-8")
    (d / "question-plan.json").write_text(plan_json, encoding="utf-8")
    (d / "history.json").write_text(history_json, encoding="utf-8")
    (d / "state-codes.txt").write_text(code_line.strip() + "\n", encoding="utf-8")
    return d
