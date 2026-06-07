# Run the full stack

One-command startup for **ReqOps `/thoughts/:id` + Uplift v6 + agent-sdk**.

Prerequisites: **Docker**, **Node 20+**, **Python 3.11+**, **`agent login`** (once), and first-time setup in [cases/TEST-CASES.md](cases/TEST-CASES.md#first-time-only).

---

## Start everything

```bash
cd Call-backup/uplift-reqops-e2e

# first time only
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

./scripts/run_stack.sh
```

This starts (or skips if already running):

| Service | Port |
|---------|------|
| PostgreSQL (Docker) | 5432 |
| agent-sdk | 7778 |
| Uplift v6 bridge | 8786 |
| ReqOps backend | 3000 |
| ReqOps frontend | 8080 |

Logs: `.stack/logs/` · PIDs: `.stack/pids.env`

---

## Verify

```bash
./scripts/check_stack.sh
```

All `[OK]` → open **http://127.0.0.1:8080/thoughts/:sessionId**

---

## Stop

```bash
./scripts/stop_stack.sh
```

Stops background processes started by `run_stack.sh`. If this script started Postgres in Docker, it stops that container too.

## Cancel in-flight agent work

Stops signal extracts and agent turns **without** shutting down the stack:

```bash
./scripts/cancel_agents.sh
```

Cancels uplift signal extract on all `reqops-*` sessions, agent-sdk active sessions, and any `agent --resume` CLI subprocesses.

---

## Path overrides

If ReqOps lives somewhere else:

```bash
export REQOPS_ROOT="/path/to/Thinkfast book/ReqOps"
./scripts/run_stack.sh
```

| Variable | Default |
|----------|---------|
| `REQOPS_ROOT` | `../Thinkfast book/ReqOps` (relative to `Call-backup`) |
| `UPLIFT_ROOT` | `Call-backup/uplift-v6` |
| `AGENT_SDK_ROOT` | `Call-backup/agent-sdk` |
| `POSTGRES_CONTAINER` | `uplift-reqops-pg` |

---

## Live agent smoke (optional)

After the stack is up:

```bash
UPLIFT_E2E_LIVE=1 ./scripts/run_live_smoke.sh
```

---

## Manual terminals

If you prefer six separate terminals instead of `run_stack.sh`, see [cases/TEST-CASES.md](cases/TEST-CASES.md).
