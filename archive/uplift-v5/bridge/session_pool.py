"""Persistent agent session pool — one Cursor `agent` CLI process per uplift session."""

from __future__ import annotations

import json
import os
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from shutil import which

from bridge.cli_agent import CliAgentSession
from bridge.logging_util import ROOT, log, log_turn_start, log_turn_summary
from bridge.mock_agent import run_mock_turn
from bridge.terminal_log import clear as clear_terminal

SESSIONS_DIR = Path(os.environ.get("UPLIFT_SESSIONS_DIR", str(ROOT / "sessions"))).resolve()
ACTIVE_FILE = SESSIONS_DIR / ".active"
MOCK = os.environ.get("UPLIFT_MOCK_AGENT", "").strip() in ("1", "true", "yes")
MODE = "mock" if MOCK else "cli"


def slugify(text: str, max_len: int = 48) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower().strip())
    s = s.strip("-") or "session"
    return s[:max_len].rstrip("-")


def next_turn(session_dir: Path) -> int:
    turns = session_dir / "turns"
    if not turns.is_dir():
        return 1
    nums = [
        int(p.name)
        for p in turns.iterdir()
        if p.is_dir() and re.fullmatch(r"\d{2}", p.name)
    ]
    return (max(nums) if nums else 0) + 1


def load_turn_json(session_dir: Path, turn: int) -> dict | None:
    path = session_dir / "turns" / f"{turn:02d}" / "turn.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def read_response_file(session_dir: Path, turn: int) -> str | None:
    td = session_dir / "turns" / f"{turn:02d}"
    for name in ("response.md", "llm-response.txt"):
        p = td / name
        if p.is_file():
            return p.read_text(encoding="utf-8").strip()
    return None


def create_session(pitch: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    session_dir = SESSIONS_DIR / f"{ts}-{slugify(pitch)}"
    (session_dir / "turns").mkdir(parents=True, exist_ok=True)
    (session_dir / "Memory.md").write_text(
        f"# Discovery memory\n\n## Pitch\n{pitch}\n\n## Settled facts\n_(none yet)_\n\n## Turn log\n",
        encoding="utf-8",
    )
    ACTIVE_FILE.write_text(session_dir.name, encoding="utf-8")
    return session_dir


def load_active_session() -> Path | None:
    if not ACTIVE_FILE.is_file():
        return None
    sid = ACTIVE_FILE.read_text(encoding="utf-8").strip()
    path = SESSIONS_DIR / sid
    return path if path.is_dir() else None


def agent_available() -> bool:
    return MOCK or which("agent") is not None


def bootstrap_prompt(session_dir: Path, pitch: str) -> str:
    return f"""Uplift v5 discovery — turn 01 (new session).

Read .cursor/skills/uplift-discovery/SKILL.md and rubric/llm_rubric_multiplier.md once.
Session: {session_dir}
Pitch: {pitch}

Write turn 01 artifacts (user-input.txt, turn.json, multiplier-audit.txt, response.md, update Memory.md).
Ask exactly one discovery question in the skill's user-facing format."""


def continue_prompt(turn: int, user_text: str) -> str:
    return f"""Turn {turn:02d}. User message:
{user_text}

Same agent session — rubric already loaded. Write turn {turn:02d} artifacts, ask one question."""


@dataclass
class SessionRuntime:
    session_dir: Path
    cli: CliAgentSession | None = None
    lock: threading.Lock = field(default_factory=threading.Lock)

    def get_cli(self) -> CliAgentSession:
        if self.cli is None:
            self.cli = CliAgentSession(self.session_dir)
        return self.cli

    def close_cli(self) -> None:
        if self.cli is not None:
            self.cli.close()
            self.cli = None

    def run_agent(self, prompt: str) -> int:
        return self.get_cli().send(prompt)


class SessionPool:
    def __init__(self) -> None:
        self._runtimes: dict[str, SessionRuntime] = {}
        self._global_lock = threading.Lock()

    def get(self, session_dir: Path) -> SessionRuntime:
        sid = session_dir.name
        with self._global_lock:
            rt = self._runtimes.get(sid)
            if rt is None:
                rt = SessionRuntime(session_dir=session_dir)
                self._runtimes[sid] = rt
            return rt

    def activate(self, session_dir: Path) -> SessionRuntime:
        with self._global_lock:
            for rt in self._runtimes.values():
                rt.close_cli()
            self._runtimes = {session_dir.name: SessionRuntime(session_dir=session_dir)}
        return self._runtimes[session_dir.name]

    def close_all(self) -> None:
        with self._global_lock:
            for rt in self._runtimes.values():
                rt.close_cli()
            self._runtimes.clear()

    def status(self) -> dict:
        session_dir = load_active_session()
        rt = self._runtimes.get(session_dir.name) if session_dir else None
        alive = bool(rt and rt.cli and rt.cli.is_alive)
        chat = None
        if session_dir and (session_dir / ".chat-id").is_file():
            chat = (session_dir / ".chat-id").read_text(encoding="utf-8").strip()[:8]
        return {
            "mock": MOCK,
            "cli_live": alive,
            "persistent": alive or bool(session_dir),
            "mode": MODE,
            "chat_id_prefix": chat,
            "pooled_sessions": len(self._runtimes),
        }


POOL = SessionPool()


def reset_for_tests() -> None:
    global POOL
    POOL.close_all()
    POOL = SessionPool()
    clear_terminal()
    if ACTIVE_FILE.is_file():
        ACTIVE_FILE.unlink()


def prepare_test_sessions_dir() -> None:
    import shutil

    if SESSIONS_DIR.is_dir():
        shutil.rmtree(SESSIONS_DIR)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def run_turn(user_text: str, *, new_pitch: str | None = None) -> dict:
    if not agent_available():
        raise RuntimeError(
            "Cursor agent CLI not found. Install: curl https://cursor.com/install -fsS | bash && agent login"
        )

    if new_pitch:
        session_dir = create_session(new_pitch)
        runtime = POOL.activate(session_dir)
        turn = 1
        prompt = bootstrap_prompt(session_dir, new_pitch)
        is_new = True
    else:
        session_dir = load_active_session()
        if not session_dir:
            raise RuntimeError("No active session — start with a pitch.")
        runtime = POOL.get(session_dir)
        turn = next_turn(session_dir)
        prompt = continue_prompt(turn, user_text)
        is_new = False

    turn_dir = session_dir / "turns" / f"{turn:02d}"
    turn_dir.mkdir(parents=True, exist_ok=True)
    (turn_dir / "user-input.txt").write_text(user_text.strip(), encoding="utf-8")

    log_turn_start(
        turn=turn,
        session_dir=session_dir,
        user_text=user_text,
        new_session=is_new,
        chat_id="cli-live",
        persistent=True,
    )

    t0 = time.monotonic()
    with runtime.lock:
        if MOCK:
            run_mock_turn(session_dir, turn, user_text, pitch=new_pitch)
            proc_rc = 0
        else:
            proc_rc = runtime.run_agent(prompt)
    elapsed = time.monotonic() - t0

    if proc_rc != 0:
        raise RuntimeError(f"agent run failed after {elapsed:.1f}s — see terminal")

    turn_data = load_turn_json(session_dir, turn)
    log_turn_summary(session_dir, turn, elapsed, turn_data)

    response_text = read_response_file(session_dir, turn)
    if not response_text:
        raise RuntimeError(
            f"agent finished but no response.md in turn {turn:02d} — check terminal output"
        )

    st = POOL.status()
    return {
        "session_id": session_dir.name,
        "session_path": str(session_dir),
        "turn": turn,
        "response": response_text,
        "turn_json": turn_data,
        "elapsed_s": round(elapsed, 2),
        "persistent": True,
        "cli_live": st.get("cli_live", False),
        "mode": MODE,
    }


def session_state() -> dict:
    session_dir = load_active_session()
    pool_status = POOL.status()
    if not session_dir:
        return {"session_id": None, **pool_status}

    turn = next_turn(session_dir) - 1
    if turn < 1:
        pitch = ""
        mem = session_dir / "Memory.md"
        if mem.is_file():
            m = re.search(r"## Pitch\s*\n(.*?)(?=\n## )", mem.read_text(encoding="utf-8"), re.DOTALL)
            if m:
                pitch = m.group(1).strip()
        return {
            "session_id": session_dir.name,
            "turn": 0,
            "pitch": pitch,
            "response": None,
            "turn_json": None,
            **pool_status,
        }

    return {
        "session_id": session_dir.name,
        "turn": turn,
        "response": read_response_file(session_dir, turn),
        "turn_json": load_turn_json(session_dir, turn),
        "last_user_input": (
            (session_dir / "turns" / f"{turn:02d}" / "user-input.txt").read_text(encoding="utf-8").strip()
            if (session_dir / "turns" / f"{turn:02d}" / "user-input.txt").is_file()
            else None
        ),
        **pool_status,
    }
