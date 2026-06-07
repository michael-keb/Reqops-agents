"""Persist discovery turn artifacts from agent stdout — not from agent file tools."""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import session as sess
from . import trace

RUBRIC_READ_OK = "rubric/llm_rubric_multiplier.md"
FORBIDDEN_TOOL_NAMES = frozenset({"edit", "write", "shell", "delete", "apply_patch"})
FORBIDDEN_READ_MARKERS = (
    "/Memory.md",
    "/turns/",
    "sessions/",
    "turn.json",
    "response.md",
    "multiplier-audit",
)

_CATCHALL_OPTION_RE = re.compile(
    r"^(something else|other|something different|none of the above|not sure|not listed|"
    r"describe\b|type your\b|spell out\b|explain\b|specify\b|your own words)",
    re.IGNORECASE,
)


def _option_body(text: str) -> str:
    return re.sub(r"^[A-D]\)\s*", "", text.strip(), flags=re.IGNORECASE).strip()


def _is_catchall_option(text: str) -> bool:
    body = _option_body(text)
    if not body:
        return True
    if "something else" in body.lower():
        return True
    if body.lower().startswith("other —") or body.lower().startswith("other -"):
        return True
    return bool(_CATCHALL_OPTION_RE.match(body))


def _filter_concrete_options(options: list[str]) -> list[str]:
    out: list[str] = []
    for o in options:
        if _is_catchall_option(o):
            continue
        out.append(o.strip())
    return out


def _relabel_options(options: list[str]) -> list[str]:
    bodies = [_option_body(o) for o in options if not _is_catchall_option(o)]
    bodies = [b for b in bodies if b]
    if len(bodies) < 3:
        return []
    labels = "ABC" if len(bodies) == 3 else "ABCD"
    limited = bodies[: len(labels)]
    return [f"{labels[i]}) {limited[i]}" for i in range(len(limited))]


def _sanitize_question_options(questions: list[dict]) -> list[dict]:
    """Drop catch-all options; keep only questions with 3–4 concrete MCQ choices."""
    out: list[dict] = []
    for q in questions:
        relabeled = _relabel_options(q.get("options") or [])
        if len(relabeled) < 3:
            continue
        out.append({**q, "options": relabeled[:4]})
    return out


def extract_pitch(text: str) -> str | None:
    m = re.search(r"Start uplift discovery for:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
    return m.group(1).strip() if m else None


def user_input_for_turn(raw: str) -> str:
    """Normalize stored user-input: bootstrap → pitch only."""
    pitch = extract_pitch(raw)
    return pitch if pitch else raw.strip()


def extract_json_block(text: str) -> dict | None:
    for m in re.finditer(r"```(?:json)?\s*\n([\s\S]*?)\n```", text):
        try:
            obj = json.loads(m.group(1))
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    return None


def strip_json_fence_blocks(text: str) -> str:
    """Remove ```json fenced blocks — for user-facing markdown only."""
    cleaned = re.sub(r"```(?:json)?\s*\n[\s\S]*?\n```", "", text, flags=re.IGNORECASE)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def display_response_text(response_text: str) -> str:
    """User-facing turn markdown — keep ## Action JSON intact for signal column agents."""
    text = (response_text or "").strip()
    if re.search(r"## Action\b", text, re.IGNORECASE):
        return text
    return strip_json_fence_blocks(text)


def _parse_reflection(text: str) -> str:
    m = re.search(r"## Reflection\s*\n([\s\S]*?)(?=\n## |\Z)", text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _parse_questions_markdown(text: str) -> list[dict]:
    """Best-effort parse of ### N. title blocks with A-D options."""
    questions: list[dict] = []
    body = text
    if "## Questions" in body:
        body = body.split("## Questions", 1)[1]
    elif "## Question" in body:
        # legacy single-question format
        body = body.split("## Question", 1)[1]
        m = re.search(r"\*\*(.+?)\*\*", body)
        stem_m = re.search(r"\*\*.+?\*\*\s*\n([\s\S]*?)(?=\n-\s*[A-D]\)|\Z)", body)
        opts = re.findall(r"^-\s*([A-D])\)\s*(.+)$", body, re.MULTILINE)
        if m:
            questions.append(
                {
                    "rank": 1,
                    "title": m.group(1).strip(),
                    "stem": (stem_m.group(1).strip() if stem_m else ""),
                    "options": _relabel_options([f"{k}) {v.strip()}" for k, v in opts]),
                }
            )
        return questions

    blocks = re.split(r"(?=^###\s+\d+\.\s)", body, flags=re.MULTILINE)
    if len(blocks) <= 1:
        blocks = re.split(r"(?=^\d+\.\s+\*\*)", body, flags=re.MULTILINE)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        hdr = re.match(r"^###\s+(\d+)\.\s*(.+?)\s*$", block, re.MULTILINE)
        if not hdr:
            hdr = re.match(r"^(\d+)\.\s+\*\*(.+?)\*\*", block, re.MULTILINE)
        if not hdr:
            continue
        rank = int(hdr.group(1))
        title = hdr.group(2).strip().rstrip("*").strip()
        rest = block[hdr.end() :].strip()
        stem_m = re.match(r"^([\s\S]*?)(?=\n-\s*[A-D]\)|\Z)", rest)
        stem = stem_m.group(1).strip() if stem_m else ""
        opts = re.findall(r"^-\s*([A-D])\)\s*(.+)$", rest, re.MULTILINE)
        questions.append(
            {
                "rank": rank,
                "title": title,
                "stem": stem,
                "options": _relabel_options([f"{k}) {v.strip()}" for k, v in opts]),
            }
        )
    return sorted(questions, key=lambda q: q.get("rank", 0))


def _split_choice_clauses(chunk: str) -> list[str]:
    chunk = chunk.strip().rstrip(".")
    if not chunk:
        return []
    parts: list[str]
    if "," in chunk:
        parts = [p.strip().rstrip(",").strip() for p in chunk.split(",")]
        parts = [re.sub(r"^or\s+", "", p, flags=re.IGNORECASE) for p in parts if p.strip()]
    elif re.search(r"\s+or\s+", chunk, re.IGNORECASE):
        parts = [p.strip() for p in re.split(r"\s+or\s+", chunk, flags=re.IGNORECASE) if p.strip()]
    elif re.search(r"\s+vs\.?\s+", chunk, re.IGNORECASE):
        parts = [p.strip() for p in re.split(r"\s+vs\.?\s+", chunk, flags=re.IGNORECASE) if p.strip()]
    else:
        parts = [chunk]
    out: list[str] = []
    for p in parts:
        p = p.strip().rstrip(".")
        if not p or p.lower() in ("etc", "etc."):
            continue
        out.append(p)
    return out


def _extract_body_options(body: str) -> list[str]:
    """Pull real choices from the follow-up paragraph under a numbered question."""
    body = body.strip()
    if not body:
        return []
    m = re.search(
        r"for\s+(.+?),\s*for\s+(?:a\s+)?(.+?),\s*or\s+for\s+(.+?)\?",
        body,
        re.IGNORECASE | re.DOTALL,
    )
    if m:
        return [m.group(1).strip(), m.group(2).strip(), m.group(3).strip()]
    qm = re.search(r"^([\s\S]+?)\?", body)
    if not qm:
        return []
    clause = qm.group(1).strip()
    clause = re.sub(
        r"^(?:Is this|Are|Do you want|Which|What|How much|How|Where should this live in your existing stack)\s*",
        "",
        clause,
        flags=re.IGNORECASE,
    ).strip()
    clause = re.sub(r'^Are\s+[“"].*?[”"]\s*', "", clause).strip()
    parts: list[str] = []
    for pm in re.finditer(r"\(([^)]+)\)", clause):
        inner = pm.group(1).strip()
        inner = re.sub(r"^(e\.g\.|eg\.|such as|like)\s*", "", inner, flags=re.IGNORECASE)
        if "," in inner or " or " in inner.lower():
            parts.extend(_split_choice_clauses(inner))
    tail = re.sub(r"\([^)]*\)", "", clause).strip(" ,;")
    tail = re.sub(r"^.*?\bhard limits\s*", "", tail, flags=re.IGNORECASE).strip(" ,;")
    if tail:
        parts.extend(_split_choice_clauses(tail))
    if len(parts) < 2:
        parts = _split_choice_clauses(clause)
    deduped: list[str] = []
    seen: set[str] = set()
    for p in parts:
        p = p.strip().rstrip(".")
        if len(p) < 3 or len(p) > 100:
            continue
        key = p.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(p)
    return deduped


def _choices_from_narrative(rest: str) -> list[str]:
    """Pull one clean A–D set from em-dash or (e.g. …) lists — prefer em-dash clause first."""
    pools: list[list[str]] = []
    em = re.search(
        r"^—\s*([^—]+?)(?:\s+and\s+(?:who|what)|—|\?|$)",
        rest.strip(),
        flags=re.IGNORECASE,
    )
    em_lead: str | None = None
    if em:
        parts = _split_choice_clauses(em.group(1))
        if len(parts) >= 2:
            pools.append(parts)
        elif parts:
            em_lead = parts[0]
    vs_parts: list[str] = []
    if re.search(r"\s+vs\.?\s+", rest, re.IGNORECASE):
        vs_parts = [
            p.strip().rstrip(".")
            for p in re.split(r"\s+vs\.?\s+", rest, flags=re.IGNORECASE)
            if p.strip() and len(p) < 80
        ]
        if len(vs_parts) >= 2:
            pools.append(vs_parts)
    if em_lead and len(vs_parts) >= 2:
        pools.insert(0, [em_lead, vs_parts[0], vs_parts[1]])
    for m in re.finditer(r"\*\(([^)]+)\)\*|\(([^)]+)\)", rest):
        inner = (m.group(1) or m.group(2) or "").strip()
        inner = re.sub(r"^(e\.g\.|eg\.|such as|like)\s*", "", inner, flags=re.IGNORECASE)
        inner = re.sub(r"\s+—\s+.+$", "", inner).strip()
        parts = _split_choice_clauses(inner)
        if len(parts) >= 2:
            pools.append(parts)
    if not pools:
        return []
    best = pools[0][:4]
    deduped: list[str] = []
    seen: set[str] = set()
    for c in best:
        key = c.lower()[:120]
        if key not in seen:
            seen.add(key)
            deduped.append(c)
    return deduped


def _pad_options(choices: list[str]) -> list[str]:
    """Build A–C (or A–D when four real choices exist) — never invent catch-all options."""
    cleaned: list[str] = []
    for c in choices:
        c = c.strip().rstrip(",").strip()
        if not c or _is_catchall_option(c):
            continue
        cleaned.append(_option_body(c) if re.match(r"^[A-D]\)", c, re.IGNORECASE) else c)
    if len(cleaned) < 3:
        return []
    labels = "ABC" if len(cleaned) == 3 else "ABCD"
    limited = cleaned[: len(labels)]
    return [f"{labels[i]}) {limited[i]}" for i in range(len(limited))]


def _parse_narrative_questions(text: str) -> list[dict]:
    """Turn open-ended '1. **Title**—a, b, or c' blocks into MCQ-shaped dicts."""
    body = text
    if re.search(r"##\s*Questions", body, re.IGNORECASE):
        body = re.split(r"##\s*Questions", body, flags=re.IGNORECASE, maxsplit=1)[1]
    body = re.sub(r"^\([^)]*ranked[^)]*\)\s*$", "", body, flags=re.IGNORECASE | re.MULTILINE)
    blocks = re.split(r"(?=^\d+\.\s+\*\*)", body, flags=re.MULTILINE)
    questions: list[dict] = []
    for block in blocks:
        block = block.strip()
        m = re.match(r"^(\d+)\.\s+\*\*(.+?)\*\*(.*)$", block, re.DOTALL)
        if not m:
            continue
        rank = int(m.group(1))
        title = m.group(2).strip()
        rest = m.group(3).strip()
        body_text = re.sub(r"^\s+", "", rest).replace("\n", " ").strip()
        stem = body_text if body_text else title
        if stem and not stem.endswith("?"):
            stem = stem.rstrip(".") + "?"
        choices = _extract_body_options(rest) or _choices_from_narrative(rest)
        opts = _pad_options(choices)
        if not opts:
            continue
        questions.append(
            {
                "rank": rank,
                "title": title,
                "stem": stem,
                "options": opts,
            }
        )
    return sorted(questions, key=lambda q: q.get("rank", 0))


def _options_valid(options: list[str]) -> bool:
    relabeled = _relabel_options(options)
    if len(relabeled) < 3 or len(relabeled) > 4:
        return False
    labels = "ABCD"[: len(relabeled)]
    for i, o in enumerate(relabeled):
        if not re.match(rf"^{labels[i]}\)\s+\S", o.strip(), re.IGNORECASE):
            return False
        if _is_catchall_option(o):
            return False
    return True


def _questions_have_mcq(questions: list[dict]) -> bool:
    return bool(questions) and all(_options_valid(q.get("options") or []) for q in questions)


def ensure_mcq_questions(response_text: str, questions: list[dict]) -> list[dict]:
    """Fill or replace questions so every item has concrete A–C (or A–D) options."""
    narrative = _parse_narrative_questions(response_text)
    if _questions_have_mcq(narrative):
        return _sanitize_question_options(narrative)
    if _questions_have_mcq(questions):
        return _sanitize_question_options(questions)
    if not narrative:
        return _sanitize_question_options(questions)
    if not questions:
        return _sanitize_question_options(narrative)
    by_rank = {int(q.get("rank", 0)): q for q in narrative}
    merged: list[dict] = []
    for q in questions:
        rank = int(q.get("rank", 0))
        opts = q.get("options") or []
        if _options_valid(opts):
            merged.append(q)
            continue
        fill = by_rank.get(rank) or {}
        merged.append(
            {
                **q,
                "options": fill.get("options")
                or _pad_options(_choices_from_narrative(q.get("stem", ""))),
            }
        )
    return _sanitize_question_options(merged)


def format_mcq_markdown(reflection: str, questions: list[dict]) -> str:
    lines = ["## Reflection", "", reflection.strip(), "", "## Questions", ""]
    for q in sorted(questions, key=lambda x: int(x.get("rank", 0))):
        rank = q.get("rank", "?")
        title = q.get("title", "Question")
        lines.append(f"### {rank}. {title}")
        if q.get("stem"):
            lines.append(str(q["stem"]))
            lines.append("")
        for opt in q.get("options") or []:
            lines.append(f"- {opt}" if opt.startswith(("A)", "B)", "C)", "D)")) else f"- {opt}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def build_turn_json(turn_num: int, response_text: str, parsed: dict | None) -> dict:
    if parsed and isinstance(parsed.get("questions"), list) and parsed["questions"]:
        out = dict(parsed)
        out["turn"] = turn_num
        return out
    reflection = (parsed or {}).get("reflection") or _parse_reflection(response_text)
    questions = _parse_questions_markdown(response_text)
    if not questions and parsed:
        # legacy single question in json
        if parsed.get("question"):
            questions = [
                {
                    "rank": 1,
                    "title": parsed.get("question", ""),
                    "stem": parsed.get("question", ""),
                    "options": parsed.get("options") or [],
                    **{k: parsed[k] for k in ("primary_gap", "mode", "score", "dominant_term", "why_now") if k in parsed},
                }
            ]
    questions = ensure_mcq_questions(response_text, questions)
    out: dict = {"turn": turn_num, "reflection": reflection, "questions": questions}
    if parsed:
        for k in ("primary_gap", "mode", "score", "dominant_term", "why_now"):
            if k in parsed and k not in out:
                out[k] = parsed[k]
    return out


def _update_memory(session_dir: Path, turn_num: int, response_text: str, questions: list[dict]) -> None:
    mem = session_dir / "Memory.md"
    if not mem.is_file():
        return
    text = mem.read_text(encoding="utf-8")
    titles = ", ".join(q.get("title", "?")[:40] for q in questions[:3])
    line = f"T{turn_num} — asked {len(questions) or '?'} questions (top: {titles})"
    if "## Turn log" in text:
        text = text.rstrip() + f"\n{line}\n"
    else:
        text = text.rstrip() + f"\n\n## Turn log\n{line}\n"
    mem.write_text(text, encoding="utf-8")


def persist_turn(session_dir: Path, *, user_input: str, response_text: str) -> int:
    """Write turns/NN/* from captured agent output. Returns disk turn number."""
    response_text = (response_text or "").strip()
    if not response_text:
        trace.warn("validation", "no response text to persist", session_id=session_dir.name)
        return sess.turn_count(session_dir)

    turn_num = sess.turn_count(session_dir) + 1
    turn_dir = session_dir / "turns" / f"{turn_num:02d}"
    turn_dir.mkdir(parents=True, exist_ok=True)

    stored_input = user_input_for_turn(user_input)
    (turn_dir / "user-input.txt").write_text(stored_input + "\n", encoding="utf-8")

    (turn_dir / "response.full.md").write_text(response_text + "\n", encoding="utf-8")
    parsed = extract_json_block(response_text)
    display_text = display_response_text(response_text)
    (turn_dir / "response.raw.md").write_text(display_text + "\n", encoding="utf-8")
    turn_json = build_turn_json(turn_num, response_text, parsed)
    qs = turn_json.get("questions") or []
    if _questions_have_mcq(qs):
        display_text = format_mcq_markdown(turn_json.get("reflection") or _parse_reflection(display_text), qs)
    (turn_dir / "response.md").write_text(display_text + "\n", encoding="utf-8")
    (turn_dir / "turn.json").write_text(json.dumps(turn_json, indent=2) + "\n", encoding="utf-8")

    audit_lines = [f"T{turn_num} multiplier audit (bridge-captured)\n"]
    for q in turn_json.get("questions") or []:
        audit_lines.append(
            f"#{q.get('rank', '?')} {q.get('primary_gap', '—')} "
            f"{q.get('mode', '—')} score={q.get('score', '—')} — {q.get('title', '')[:60]}"
        )
    (turn_dir / "multiplier-audit.txt").write_text("\n".join(audit_lines) + "\n", encoding="utf-8")

    _update_memory(session_dir, turn_num, response_text, turn_json.get("questions") or [])

    qn = len(turn_json.get("questions") or [])
    trace.info(
        "validation",
        "turn artifacts persisted",
        session_id=session_dir.name,
        turn=turn_num,
        questions=qn,
    )
    if qn == 0 and re.search(r"##\s*Questions\b", display_text, re.IGNORECASE):
        trace.warn(
            "validation",
            "questions present in markdown but no A–D options parsed — agent skipped MCQ format",
            session_id=session_dir.name,
            turn=turn_num,
        )
    elif qn and _questions_have_mcq(turn_json.get("questions") or []):
        trace.info(
            "validation",
            "MCQ options normalized for UI",
            session_id=session_dir.name,
            turn=turn_num,
            questions=qn,
        )
    return turn_num


def verify_turn_tools(*, turn: int, is_first_turn: bool) -> None:
    """Warn if agent used forbidden file tools (skill: chat-only, rubric read turn 1 only)."""
    edits = 0
    bad_reads: list[str] = []
    ok_reads: list[str] = []
    other_tools: list[str] = []

    for entry in trace.history(limit=2000, kind="tool"):
        data = entry.get("data") or {}
        if data.get("turn") != turn:
            continue
        tool = (data.get("tool") or "").lower()
        path = str(data.get("path") or data.get("args", {}).get("path") or "")

        if tool in FORBIDDEN_TOOL_NAMES:
            edits += 1
            trace.warn("validation", f"forbidden tool {tool}", turn=turn, path=path[:120])
            continue

        if tool == "read":
            rel = path.replace("\\", "/")
            if any(m in rel for m in FORBIDDEN_READ_MARKERS):
                bad_reads.append(rel)
                trace.warn("validation", "forbidden read (use chat context)", turn=turn, path=rel[:120])
            elif ".cursor/skills/" in rel or rel.startswith("rubric/"):
                trace.warn("validation", "unnecessary file read — respond from chat context", turn=turn, path=rel[:120])
            else:
                other_tools.append(f"read {rel[:80]}")
        elif tool in ("glob", "grep", "list", "search"):
            trace.warn("validation", f"unnecessary {tool} tool", turn=turn, path=path[:120])
        elif tool:
            other_tools.append(tool)

    if edits == 0 and not bad_reads:
        trace.info(
            "validation",
            "tool policy ok",
            turn=turn,
            rubric_reads=len(ok_reads),
            other=len(other_tools),
        )
    elif edits > 0:
        trace.warn("validation", f"turn used {edits} forbidden write/edit tools", turn=turn)
