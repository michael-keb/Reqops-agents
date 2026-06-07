"""Build LLM prompt for candidate scoring — references rubric file, does not embed it."""

from __future__ import annotations

import json
import re

from analyst.models import AnswerHistory, Candidate, StateGrid

_LINE = re.compile(
    r"^(?P<gap>G[1-9A-D])\s+I(?P<i>[0-3])\s+C(?P<c>[0-3])\s+E(?P<e>[0-4])\s*$",
    re.I | re.M,
)
_WHY = re.compile(r"^why:\s*(.+)$", re.I | re.M)


def build_score_user_message(
    *,
    turn: int,
    history: AnswerHistory,
    grid: StateGrid,
    candidates: list[Candidate],
    locked_facts: list[str],
) -> str:
    cand_payload = [
        {
            "gap": c.gap,
            "exposure": c.exposure,
            "risk_class": c.risk_class,
            "evidence_snippets": c.evidence_snippets[:2],
            "floor_flag": c.floor_flag,
        }
        for c in candidates
    ]
    latest = history.latest()
    latest_text = latest.raw_text if latest else ""
    locked_block = "\n".join(locked_facts) if locked_facts else "_(none)_"

    return f"""TURN {turn} — SCORE CANDIDATES (I, C, E drivers only)

--- NEW USER INPUT (read first) ---
{latest_text.strip()}

--- PITCH ---
{history.pitch.strip()}

--- PRIOR TURNS ---
{history.full_text()[:4000]}

--- LOCKED FACTS ---
{locked_block}

--- GRID (exposure — context only) ---
{json.dumps({g: grid.rows[g].exposure for g in grid.rows}, indent=2)}

--- CANDIDATES (score each — gap code is audit label only) ---
{json.dumps(cand_payload, indent=2)}

Respond with driver lines + why (see system prompt). Example:

GA  I2 C1 E0
GB  I1 C1 E0
G1  I0 C0 E1

why: answer named fraud priority but not the mechanism — who acts on a report, how fast, what seller sees
"""


def parse_score_response(raw: str) -> dict[str, dict]:
    """Parse compact driver lines or fallback JSON."""
    text = raw.strip()
    out: dict[str, dict] = {}

    for m in _LINE.finditer(text):
        gap = m.group("gap").upper()
        out[gap] = {
            "I": f"I{m.group('i')}",
            "C": f"C{m.group('c')}",
            "E": f"E{m.group('e')}",
            "why_now": "",
        }

    why_m = _WHY.search(text)
    global_why = why_m.group(1).strip() if why_m else ""

    if out:
        if global_why:
            best_gap = _pick_why_gap(out, global_why)
            if best_gap:
                out[best_gap]["why_now"] = global_why
        return out

    # Fallback: JSON
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    data = json.loads(text)
    for item in data.get("scores", []):
        gap = str(item["gap"]).upper()
        out[gap] = {
            "I": str(item.get("I", "I0")).upper(),
            "C": str(item.get("C", "C0")).upper(),
            "E": str(item.get("E", "E0")).upper(),
            "why_now": str(item.get("why_now", "")).strip(),
        }
    return out


def _pick_why_gap(scores: dict[str, dict], why: str) -> str | None:
    """Attach global why to highest-I driver gap."""
    ranked = sorted(
        scores.items(),
        key=lambda kv: int(kv[1]["I"][1]) if kv[1]["I"][1].isdigit() else 0,
        reverse=True,
    )
    for gap, d in ranked:
        if d["I"] not in ("I0",):
            return gap
    return ranked[0][0] if ranked else None
