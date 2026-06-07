"""Reflection-only discovery transcript for column agents."""

from __future__ import annotations

import re
from pathlib import Path

_MCQ_LINE = re.compile(r"^\s*-\s*[A-D]\)\s", re.IGNORECASE | re.MULTILINE)
_DISCOVERY_CONTRACT_RE = re.compile(
    r"\n---\s*\nUplift output contract[\s\S]*?(?=\n---\s*\n|\Z)",
    re.IGNORECASE,
)


def _clean_user_turn_text(text: str) -> str:
    cleaned = _DISCOVERY_CONTRACT_RE.sub("", text).strip()
    cleaned = re.sub(r"\n---\s*$", "", cleaned).strip()
    return cleaned or text.strip()


def _extract_pitch(memory_text: str) -> str:
    text = memory_text.strip()
    if not text:
        return ""
    m = re.search(r"##\s*Pitch\s*\n([\s\S]*?)(?=\n## |\Z)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    if text.startswith("# Discovery memory"):
        lines = text.splitlines()
        body: list[str] = []
        for line in lines[1:]:
            if line.startswith("## "):
                break
            body.append(line)
        joined = "\n".join(body).strip()
        if joined:
            return joined
    return text.split("\n\n")[0].strip()


def _extract_reflection(response_text: str) -> str:
    m = re.search(r"## Reflection\s*\n([\s\S]*?)(?=\n## |\Z)", response_text, re.IGNORECASE)
    if not m:
        return ""
    block = m.group(1)
    lines = [ln for ln in block.splitlines() if not _MCQ_LINE.match(ln)]
    return "\n".join(lines).strip()


def build_transcript(session_dir: Path, *, reflection_only: bool = True) -> str:
    """Assemble discovery conversation; default excludes MCQs and full agent responses."""
    parts: list[str] = []
    memory = session_dir / "Memory.md"
    if memory.is_file():
        raw = memory.read_text(encoding="utf-8").strip()
        pitch = _extract_pitch(raw) if reflection_only else raw
        if pitch:
            parts.append(f"### Pitch\n{pitch}")

    turns_root = session_dir / "turns"
    if turns_root.is_dir():
        for turn_dir in sorted(turns_root.iterdir()):
            if not turn_dir.is_dir():
                continue
            label = turn_dir.name
            user_path = turn_dir / "user-input.txt"
            if user_path.is_file():
                user_text = _clean_user_turn_text(user_path.read_text(encoding="utf-8").strip())
                parts.append(f"### User (id: user-turn-{label}, turn {label})\n{user_text}")
            response_path = turn_dir / "response.md"
            if not response_path.is_file():
                continue
            response_text = response_path.read_text(encoding="utf-8")
            if reflection_only:
                reflection = _extract_reflection(response_text)
                if reflection:
                    parts.append(f"### Agent reflection (turn {label})\n{reflection}")
            else:
                parts.append(f"### Agent (turn {label})\n{response_text.strip()}")

    return "\n\n---\n\n".join(p for p in parts if p.strip())
