# Uplift 2.0 — Deterministic Gatekeeper

Self-contained implementation of the turn-loop from `deterministic-gatekeeper-plan.md`.
**Does not modify** the legacy harness at repo root (`test-rubric.py`, `session_store.py`).

## What this is

| Layer | Role |
|-------|------|
| **Gatekeeper** (`gatekeeper/`) | User history → full gap grid → L/R/P → question plan → authoritative code line |
| **LLM** (`prompts/phrasing-rubric.md`) | MCQ wording + coaching voice only |
| **Harness** (`test-rubric.py`) | Orchestrates gatekeeper then phrasing LLM |

## Quick start

```bash
# From repo root — unit tests (no API)
python uplift-2.0/test_gatekeeper.py

# Replay legacy car-selling session (read-only on ../sessions/)
python uplift-2.0/test-rubric.py --replay 20260524-202455-car-selling-app

# Write grid.json into that session's turn folders
python uplift-2.0/test-rubric.py --replay 20260524-202455-car-selling-app --write

# Gatekeeper only (no OpenAI)
python uplift-2.0/test-rubric.py --gatekeeper-only --new "Car selling app"

# Full turn (uses parent .env OPENAI_API_KEY)
python uplift-2.0/test-rubric.py --new "Car selling app"
python uplift-2.0/test-rubric.py --continue "Peer-to-peer marketplace..."
```

Sessions for uplift live under **`uplift-2.0/sessions/`** (separate from legacy `sessions/`).

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
user input → history → detect → classify → derive → rank → batch plan
                → code line (validated) → LLM phrasing → memory patch
```

Classifier v1 uses **heuristic keyword signals** (no extra LLM call). Optional LLM extraction can be added in `classify_llm.py` later.

## Env vars

Uses parent `Call-backup/.env`:

- `OPENAI_API_KEY` — required for live LLM turns
- `PHRASING_MODEL` / `LLM_MODEL` — phrasing model (default `gpt-4o`)
- `MAX_BATCH_SIZE` — Q6 cap (default `4`)

## Copied from legacy (unchanged at source)

- `session_store.py` — extended with `write_gatekeeper_artifacts` + uplift memory template
- `env_config.py`
- `llm-rubric_v2.md` — legend reference

## Success vs legacy run

| Check | Legacy | Uplift 2.0 |
|-------|--------|------------|
| All 13 gaps every turn | ❌ sparse | ✅ full grid |
| Invalid `GCh` | ❌ shipped | ✅ rejected by validator |
| L/R re-derived | ❌ copied | ✅ computed from grid |
| MCQ count | fixed 3 | `min(open, MAX_BATCH)+Q7` |
| P4 when closed | ❌ | ✅ when open set empty |

See `deterministic-gatekeeper-plan.md` for the full design spec.
