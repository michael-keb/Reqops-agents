# Uplift v5

Discovery runs through **Cursor Agent CLI** (`agent`). No Python harness.

## On session start

1. Load skill: `.cursor/skills/uplift-discovery/SKILL.md`
2. Read rubric: `rubric/llm_rubric_multiplier.md` and `rubric/gap-legend.md`
3. If `UPLIFT_SESSION` is set, use that folder under `sessions/`

## You are the engine

All scoring, routing, and phrasing happens in your reasoning. Write `turn.json` and `Memory.md` each turn.
