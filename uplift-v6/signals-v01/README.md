# signals-v01

Phase 02 signal-board column agents for Uplift v6.

One headless CLI agent processes all nine columns **sequentially** (one column at a time). It reads a reflection-only discovery transcript and mutates signal cards via **`add` / `edit` / `remove` / `complete`** actions. Spec: [`../docs/CLI-COLUMN-AGENTS.md`](../docs/CLI-COLUMN-AGENTS.md).

## Layout

```
signals-v01/signals_v01/     # Python package (import as signals_v01)
  columns.py                 # 9 column defs (ReqOps wire ids)
  transcript.py              # reflection-only transcript builder
  actions.py                 # ## Action parser + validation
  prompts.py                 # column + continuation prompts
  store.py                   # local card store (CRUD + soft-delete + concurrency)
  column_runner.py           # one column loop (reuses shared agent)
  extract.py                 # sequential orchestrator (one agent, 9 columns)
  cancel_registry.py         # cancel one / all columns

sessions/<upliftSessionId>/
  signals-v01/store.json     # local nodes (ReqOps BFF replaces in prod)
  signals-v01/<run_id>/agent/  # shared CLI workspace (.chat-id, turns)
  signals/<slug>/            # per-column audit (column_run_memory.json, response.raw.md)
```

Skill: `.cursor/skills/uplift-signals-v01/SKILL.md` (one skill, column context in prompt).

## Run (mock)

```bash
cd uplift-v6
UPLIFT_MOCK_AGENT=1 PYTHONPATH=signals-v01 python -m signals_v01 test-session goal risk
```

## Bridge API

- `GET  /api/sessions/{id}/signals`
- `POST /api/sessions/{id}/signals/extract`
- `POST /api/sessions/{id}/signals/extract/stream`
- `POST /api/sessions/{id}/signals/mutate`
- `POST /api/sessions/{id}/signals/cancel`

## Tests

```bash
cd uplift-v6
PYTHONPATH=signals-v01 python -m unittest tests.test_signals_v01 -v
```
