# Call-backup

Praxis workshop stack: **ReqOps + Uplift v6 + agent-sdk**.

## Active projects

| Folder | Purpose |
|--------|---------|
| [`agent-sdk/`](agent-sdk/) | Agent orchestration server (Cursor/Claude/Codex). Deploy target: Railway. |
| [`agent-sdk-e2e/`](agent-sdk-e2e/) | E2E tests for agent-sdk. |
| [`uplift-v6/`](uplift-v6/) | Discovery + signal bridge (ReqOps sidecar on `:8786`). |
| [`uplift-reqops-e2e/`](uplift-reqops-e2e/) | Full-stack local orchestration + smoke tests. |

ReqOps (backend + frontend) lives outside this repo:

`../Thinkfast book/ReqOps/`

## Deploy (single server)

Docker Compose bundles Postgres, agent-sdk, uplift-v6, ReqOps backend/frontend, and nginx on one machine.

```bash
cp .env.docker.example .env   # set CURSOR_API_KEY
./deploy/up.sh
```

See [deploy/README.md](deploy/README.md). Systemd units for bare-metal VPS are in [deploy/systemd/](deploy/systemd/).

## Quick start (local full stack)

```bash
cd uplift-reqops-e2e
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./scripts/run_stack.sh
./scripts/check_stack.sh
```

See [`uplift-reqops-e2e/RUN.md`](uplift-reqops-e2e/RUN.md).

## Shared config

Root [`.env`](.env) is loaded by `run_stack.sh`, uplift-v6 (`./serve`), and agent-sdk.

## Uplift shortcut

```bash
./uplift              # start uplift-v6 bridge (same as uplift-v6/start)
./uplift --open       # open browser
```

## Archive

Older uplift versions (v2–v5), legacy root scripts, and old session data are in [`archive/`](archive/). Not used by the active stack.
