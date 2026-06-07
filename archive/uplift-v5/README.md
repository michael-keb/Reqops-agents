# Uplift v5

**Rubric + skill + Cursor CLI.** No Python discovery pipeline. Optional **UI** (`./serve`) bridges the browser to `agent` on your terminal.

The agent reads the multiplier rubric, does all I×C×E×R×K reasoning internally, asks one question per turn, and writes session files.

## Prerequisites

```bash
curl https://cursor.com/install -fsS | bash
agent login
```

## UI (`./serve`)

One **`agent` CLI process** per discovery session — same binary as your terminal, not respawned each turn.

```bash
cd uplift-v5
chmod +x serve
./serve --open    # http://127.0.0.1:8785
```

## Run

```bash
cd uplift-v5
chmod +x start serve    # once

./start                           # interactive CLI
./start "Extract goals from chat" # new session + pitch
./serve --open                    # web UI → same agent CLI
```

From repo root:

```bash
./uplift                          # points here (v5)
./uplift "Car selling app"
```

## What's in the box

```
uplift-v5/
  serve                           # UI server → agent CLI
  start                           # CLI only
  bridge/server.py                # thin HTTP bridge (no discovery logic)
  ui/                             # browser UI
  AGENTS.md
  rubric/
    llm_rubric_multiplier.md      # authoritative multiplier tables
    gap-legend.md                 # G1–GD (audit only)
  .cursor/skills/uplift-discovery/
    SKILL.md                      # discovery workflow + file schema
  sessions/                       # agent-written artifacts
  PLAN.md                         # future UI + Docker notes
```

## Session artifacts (agent writes these)

```
sessions/<id>/
  Memory.md
  turns/01/
    user-input.txt
    turn.json
    multiplier-audit.txt
    response.md
```

## vs v4

| v4 | v5 |
|----|-----|
| Python pipeline + 2 LLM calls | One agent, one conversation |
| `run_turn.py`, `cli.py` | `start` → `agent` |
| Code multiplies I×C×E×R×K | Agent multiplies in reasoning |
| Rubric in prompts via code | Rubric files agent reads directly |

v4 remains in `uplift-v4.0/` for benchmarks and regression.

## Environment

Optional: `export UPLIFT_SESSION=/path/to/sessions/foo` before `agent` so the skill knows where to write.

Terminal output: agent streams live to the terminal running `./serve` or `./start`. Set `UPLIFT_QUIET=1` to hide turn banners.

**Persistent sessions:** `./serve` starts one `agent` process when you begin a session; all turns reuse it. Terminal panel shows `$ agent <<< …` (not `$ agent --resume …`).

## E2E tests (Playwright, mock agent)

```bash
cd uplift-v5
npm install
npx playwright install chromium
npm run test:e2e
```

Uses `UPLIFT_MOCK_AGENT=1` — no Cursor API calls during tests.

Auth: `agent login` or `export CURSOR_API_KEY=...`
