"""Discovery session dirs + artifact loading for the chat UI."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SESSIONS_DIR = Path(
    __import__("os").environ.get("UPLIFT_SESSIONS_DIR", str(ROOT / "sessions"))
).resolve()

_SESSION_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}$")


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (s[:40] or "session").rstrip("-")


def new_session_id(pitch: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{ts}-{slugify(pitch)}"


def validate_session_id(session_id: str) -> str:
    sid = (session_id or "").strip()
    if not sid or not _SESSION_ID_RE.match(sid):
        raise ValueError(f"invalid session_id: {session_id!r}")
    return sid


def session_path(session_id: str) -> Path:
    return SESSIONS_DIR / validate_session_id(session_id)


def session_exists(session_id: str) -> bool:
    try:
        return session_path(session_id).is_dir()
    except ValueError:
        return False


def activate_session(session_id: str) -> Path:
    """Set global active marker + return session dir."""
    path = session_path(session_id)
    if not path.is_dir():
        raise FileNotFoundError(f"session not found: {session_id}")
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    (SESSIONS_DIR / ".active").write_text(path.name, encoding="utf-8")
    return path


def create_session(pitch: str, *, session_id: str | None = None) -> Path:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    sid = validate_session_id(session_id) if session_id else new_session_id(pitch)
    path = SESSIONS_DIR / sid
    if path.exists():
        activate_session(sid)
        return path
    path.mkdir(parents=True, exist_ok=False)
    (path / "Memory.md").write_text(
        f"# Discovery memory\n\n## Pitch\n{pitch}\n\n## Settled facts\n\n## Turn log\n",
        encoding="utf-8",
    )
    activate_session(sid)
    return path


def delete_session(session_id: str) -> bool:
    try:
        path = session_path(session_id)
    except ValueError:
        return False
    if not path.is_dir():
        return False
    shutil.rmtree(path)
    marker = SESSIONS_DIR / ".active"
    if marker.exists() and marker.read_text(encoding="utf-8").strip() == session_id:
        marker.unlink()
    return True


def active_session() -> Path | None:
    marker = SESSIONS_DIR / ".active"
    if not marker.exists():
        return None
    sid = marker.read_text(encoding="utf-8").strip()
    path = SESSIONS_DIR / sid
    return path if path.is_dir() else None


def turn_count(session: Path) -> int:
    turns = session / "turns"
    if not turns.is_dir():
        return 0
    return sum(1 for d in turns.iterdir() if d.is_dir() and d.name.isdigit())


def latest_turn_dir(session: Path) -> Path | None:
    turns = session / "turns"
    if not turns.is_dir():
        return None
    nums = sorted(int(d.name) for d in turns.iterdir() if d.is_dir() and d.name.isdigit())
    if not nums:
        return None
    return turns / f"{nums[-1]:02d}"


def turn_dir(session: Path, turn_n: int) -> Path | None:
    td = session / "turns" / f"{turn_n:02d}"
    return td if td.is_dir() else None


def load_turn_json(session: Path, turn_n: int) -> dict | None:
    td = turn_dir(session, turn_n)
    if not td:
        return None
    tj = td / "turn.json"
    if not tj.is_file():
        return None
    try:
        data = json.loads(tj.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def latest_response(session: Path) -> str | None:
    td = latest_turn_dir(session)
    if not td:
        return None
    resp = td / "response.md"
    return resp.read_text(encoding="utf-8") if resp.exists() else None


def latest_questions(session: Path) -> list[dict]:
    td = latest_turn_dir(session)
    if not td:
        return []
    turn_json = td / "turn.json"
    if not turn_json.is_file():
        return []
    try:
        data = json.loads(turn_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if isinstance(data.get("questions"), list) and data["questions"]:
        return data["questions"]
    if data.get("question"):
        return [
            {
                "rank": 1,
                "title": data.get("question", ""),
                "stem": data.get("question", ""),
                "options": data.get("options") or [],
                "primary_gap": data.get("primary_gap"),
                "score": data.get("score"),
            }
        ]
    return []


def session_state_for(session_id: str | None = None) -> dict:
    if session_id:
        try:
            session = session_path(session_id)
        except ValueError:
            return {"session_id": None, "turn": 0, "response": None, "questions": [], "exists": False}
        if not session.is_dir():
            return {
                "session_id": session_id,
                "turn": 0,
                "response": None,
                "questions": [],
                "exists": False,
            }
        return {
            "session_id": session.name,
            "turn": turn_count(session),
            "response": latest_response(session),
            "questions": latest_questions(session),
            "exists": True,
        }
    session = active_session()
    if not session:
        return {"session_id": None, "turn": 0, "response": None, "questions": [], "exists": False}
    return {
        "session_id": session.name,
        "turn": turn_count(session),
        "response": latest_response(session),
        "questions": latest_questions(session),
        "exists": True,
    }


def session_state() -> dict:
    return session_state_for(None)
