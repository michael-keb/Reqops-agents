# Uplift 4.0

Analyst-first discovery harness. **CLI only** — no web server, no HTTP API between you and the tool.

## How you run it

From repo root:

```bash
chmod +x uplift    # once
./uplift           # interactive REPL
./uplift --new "Extract goals from conversation history"
./uplift --list
```

Or from this directory:

```bash
../uplift-v3.0/.venv/bin/python cli.py
```

Flow: **terminal → cli.py → run_turn.py → session files**. Nothing listens on a port; nothing parses MCQs for a browser.

## Architecture

See `instrucitons.md` for the full pipeline. Summary:

1. **Deterministic** — build candidates, apply L2 lock veto, track recency
2. **LLM** — score each candidate with **I / C / E** driver codes (reads `llm_rubric_multiplier.md`)
3. **Deterministic** — attach **R / K**, multiply, rank, pick mode (FOLLOW, CONFRONT, …)
4. **LLM** — phrase **one MCQ** from the selection object

The multiplier rubric lives in **`llm_rubric_multiplier.md`** — loaded at runtime, never embedded in Python.

## Quick start (CLI — recommended)

```bash
cd uplift-v4.0
../uplift-v3.0/.venv/bin/python cli.py          # interactive REPL
../uplift-v3.0/.venv/bin/python cli.py --new "Car selling app"
../uplift-v3.0/.venv/bin/python cli.py --list
```

One-shot turns: see **Scripting** below.

REPL commands: `/new` `/sessions` `/audit` `/quit` · multi-line: `/multi`

## vs web UI (deprecated)

The old path was **browser → HTTP `/api/turn` → subprocess**. That added a parser and broke when LLM output format changed. Do not use `http://127.0.0.1:8765` for new work. Legacy v3 web only if needed:

```bash
UPLIFT_WEB_LEGACY=1 python uplift-v3.0/web/server.py
```

## Scripting (one shot per invocation)

```bash
../uplift-v3.0/.venv/bin/python run_turn.py --new "Car selling app"
../uplift-v3.0/.venv/bin/python run_turn.py --continue "follow-up"
../uplift-v3.0/.venv/bin/python run_turn.py --continue "…" --json   # audit selection
```

## Tests

```bash
python test_analyst.py
```

## Turn artifacts

Each turn folder under `sessions/<id>/turns/NN/`:

| File | Contents |
|------|----------|
| `grid.json` | Gap exposure snapshot |
| `selection.json` | Primary gap, score, mode, ranked, vetoed, suppressed |
| `scored-candidates.json` | Full term dump for audit |
| `score-response.json` | Raw LLM I/C/E scores |
| `llm-response.txt` | Phrased MCQ |
| `../log-history.md` | Rolling session log (score + phrase + selection per turn) |

## Diagnostic

If every turn's `scored-candidates.json` shows I0/C0/E0 flat scores, the scoring LLM isn't doing analyst work — fix the scoring prompt, not the multipliers.

## vs v3

| v3 | v4 |
|----|-----|
| Gap-rank + L/R/P codes as labels | I×C×E drivers + R/K guards |
| Multi-slot batch plans | One primary question per turn |
| Full llm-rubric_v2.md phrasing | Multiplier rubric + selection object |
| assess.py heuristic weakness | LLM implication/consistency/evidence scoring |
