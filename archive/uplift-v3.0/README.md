# Uplift 3.0 — Deterministic Gatekeeper

Self-contained implementation of the turn-loop from `deterministic-gatekeeper-plan.md`.
**Does not modify** the legacy harness at repo root (`test-rubric.py`, `session_store.py`).

## What this is

| Layer | Role |
|-------|------|
| **Gatekeeper** (`gatekeeper/`) | User history → assessment → grid → **one primary probe** → code line |
| **LLM** (`llm-rubric_v2.md`, full file) | MCQ wording — entire rubric as system prompt |
| **Harness** (`test-rubric.py`) | Orchestrates gatekeeper then phrasing LLM |

## Quick start

```bash
# From repo root — unit tests (no API)
python uplift-v3.0/test_gatekeeper.py

# Replay legacy car-selling session (read-only on ../sessions/)
python uplift-v3.0/test-rubric.py --replay 20260524-202455-car-selling-app

# Write grid.json into that session's turn folders
python uplift-v3.0/test-rubric.py --replay 20260524-202455-car-selling-app --write

# Gatekeeper only (no OpenAI)
python uplift-v3.0/test-rubric.py --gatekeeper-only --new "Car selling app"

# Full turn (uses parent .env OPENAI_API_KEY)
python uplift-v3.0/test-rubric.py --new "Car selling app"
python uplift-v3.0/test-rubric.py --continue "Peer-to-peer marketplace..."
```

Sessions for uplift live under **`uplift-v3.0/sessions/`** (separate from legacy `sessions/`).

## Artifacts per turn

| File | Owner |
|------|-------|
| `grid.json` | Gatekeeper — full G1–GD exposure grid |
| `question-plan.json` | Gatekeeper — ranked MCQ slots + Q7 |
| `history.json` | Gatekeeper — user-only answer history |
| `state-codes.txt` | Gatekeeper — authoritative code line |
| `llm-response.txt` | LLM phrasing + appended codes |

## Architecture

```
user input → history → assess weaknesses → classify → merge → derive → one primary probe (Q1)
                → code line (validated) → LLM phrasing → memory patch
```

**v3:** `merge` enforces X3/X5 durability (`locked_by` on `grid.json`). See `v3-durability-plan.md`.

Classifier v1 uses **heuristic keyword signals** (no extra LLM call). Optional LLM extraction can be added in `classify_llm.py` later.

## Env vars

Uses parent `Call-backup/.env`:

- `OPENAI_API_KEY` — required for live LLM turns
- `PHRASING_MODEL` / `LLM_MODEL` — phrasing model (default `gpt-4o`)
- `MAX_BATCH_SIZE` — max MCQs per turn (default `1`; set `2` to allow optional X4 confirm slot)

## Copied from legacy (unchanged at source)

- `session_store.py` — extended with `write_gatekeeper_artifacts` + uplift memory template
- `env_config.py`
- `llm-rubric_v2.md` — **source of truth**; full file sent as phrasing LLM system prompt

## Success vs legacy run

| Check | Legacy | Uplift 2.0 |
|-------|--------|------------|
| All 13 gaps every turn | ❌ sparse | ✅ full grid |
| Invalid `GCh` | ❌ shipped | ✅ rejected by validator |
| L/R re-derived | ❌ copied | ✅ computed from grid |
| MCQ count | fixed 3 | `min(open, MAX_BATCH)+Q7` |
| P4 when closed | ❌ | ✅ when open set empty |

See `deterministic-gatekeeper-plan.md` for the full design spec.
