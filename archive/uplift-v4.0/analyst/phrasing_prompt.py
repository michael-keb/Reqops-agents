"""Build phrasing LLM prompt from multiplier selection — not gap taxonomy labels."""

from __future__ import annotations

from analyst.models import TurnSelection

_MODE_HINT: dict[str, str] = {
    "FOLLOW": "The answer opened a door — follow that thread in their words.",
    "CONFRONT": "Name the contradiction; force one explicit pick.",
    "PROBE_SEAM": "Two answers don't fit — help them square it.",
    "REASK_NARROWER": "They dodged — tighten; no escape hatch.",
    "CHALLENGE_GROUNDS": "They asserted without backing — ask for evidence.",
    "COVERAGE": "Nothing scored live — still ask one concrete policy fork tied to their app.",
}


def build_phrase_user_message(
    *,
    turn: int,
    user_text: str,
    selection: TurnSelection,
    locked_facts: list[str],
    memory: str,
    multiplier_audit: str = "",
) -> str:
    primary = selection.primary
    if not primary:
        return f"""TURN {turn} — INTAKE (no MCQ)

--- NEW USER INPUT ---
{user_text.strip()}

--- INSTRUCTION ---
{selection.intake_message or "Reflect what you heard and invite concrete detail or artifacts."}

--- SESSION MEMORY ---
{memory}
"""

    locked_block = "\n".join(locked_facts) if locked_facts else "_(none)_"
    why = primary.drivers.why_now.strip() or "Infer from NEW USER INPUT — plain language only"
    mode_hint = _MODE_HINT.get(primary.mode, "")
    audit_block = multiplier_audit.strip() or "(see selection below)"

    return f"""TURN {turn} — PHRASE ONE MCQ (from multiplier outcome, not gap checklist)

--- NEW USER INPUT (source of truth) ---
{user_text.strip()}

--- LOCKED FACTS ---
{locked_block}

--- MULTIPLIER OUTCOME (fixed — this turn's move) ---
{audit_block}

PRIMARY gap (audit tag only — do NOT use as the question title): {primary.gap}
MODE: {primary.mode} — {mode_hint}
Dominant term: {primary.dominant_term}
why: {why}

--- PHRASING RULES ---
- Title and stem come from **why** + user input — not from gap taxonomy ("how participants are protected", "who exactly concretely", etc.).
- Do not print gap codes or mode names in the MCQ header visible to the user.
- One atomic MCQ; options A–C are specific adoptable policies for THIS app turn.

--- SESSION MEMORY ---
{memory}
"""
