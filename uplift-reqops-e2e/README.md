# uplift-reqops E2E

Preflight and smoke tests for the **ReqOps `/thoughts/:id` + Uplift v6 + agent-sdk** stack.

## Run the full stack

```bash
cd uplift-reqops-e2e
./scripts/run_stack.sh    # start all services
./scripts/stop_stack.sh   # stop
```

See **[RUN.md](RUN.md)** for details.

## Quick check (is everything running?)

```bash
cd uplift-reqops-e2e
./scripts/check_stack.sh
```

Example output:

```
[OK] PostgreSQL (5432) — reachable via ReqOps /healthz
[OK] ReqOps backend (3000) — HTTP 200
[OK] ReqOps frontend (8080) — HTTP 200
[OK] Uplift v6 bridge (8786) — HTTP 200
[OK] agent-sdk server (7778) — HTTP 200
[OK] Cursor agent CLI (PATH) — ...
CURSOR_API_KEY: set
```

Exit code `1` if any service is down — see `cases/TEST-CASES.md` for start commands.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Config loads from:

1. `Call-backup/.env` ( `CURSOR_API_KEY`, `UPLIFT_SIGNALS_RUNNER`, … )
2. `uplift-reqops-e2e/.env` (optional URL overrides)

## Run tests

```bash
./scripts/run_preflight.sh              # fast — no LLM calls
UPLIFT_E2E_LIVE=1 ./scripts/run_live_smoke.sh   # slow — real agent turn + SDK extract
```

## What must be active

See **[cases/TEST-CASES.md](cases/TEST-CASES.md)** for the full diagram, six terminals, env vars, and manual UI checklist.

| Service | Port | Start |
|---------|------|-------|
| PostgreSQL | 5432 | `docker run … postgres:15` |
| ReqOps backend | 3000 | `Reqops_backend && npm run dev` |
| ReqOps frontend | 8080 | `Reqops_Frontend && npm run dev` |
| agent-sdk | 7778 | `agent-sdk && uvicorn … --port 7778` |
| Uplift v6 bridge | 8786 | `uplift-v6 && ./serve` |
| Cursor CLI | PATH | `agent login` |

## Env overrides

| Variable | Default |
|----------|---------|
| `REQOPS_BACKEND_URL` | `http://127.0.0.1:3000` |
| `REQOPS_FRONTEND_URL` | `http://127.0.0.1:8080` |
| `UPLIFT_BRIDGE_URL` | `http://127.0.0.1:8786` |
| `AGENT_SDK_URL` | `http://127.0.0.1:7778` |
| `UPLIFT_E2E_LIVE` | unset (skip live agent tests) |
