# agent-sdk E2E Tests

End-to-end tests for **Cursor** integration with [agent-sdk](../agent-sdk).
Lives outside `agent-sdk/` so the suite can validate a running server without coupling to its unit tests.

## Setup

```bash
cd agent-sdk-e2e
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Config is loaded from:

1. `Call-backup/.env` (parent — includes `CURSOR_API_KEY`)
2. `agent-sdk-e2e/.env` (optional overrides)

## Start the server (separate terminal)

```bash
cd agent-sdk
export DATABASE_URL="postgresql://$(whoami)@localhost:5432/agent_sdk_server"
export PYTHONPATH=src
.venv/bin/python -m uvicorn api.server:app --host 0.0.0.0 --port 7778
```

## Run tests

```bash
./scripts/smoke_cursor.sh     # fast: health + connect + one message
./scripts/check_zombies.sh    # detect orphan agent acp (keychain prompt cause)
./scripts/run_all.sh          # full pytest suite
```

Or directly:

```bash
.venv/bin/pytest tests/ -v
.venv/bin/pytest tests/test_cursor_messaging.py -v
```

## Layout

```
agent-sdk-e2e/
  cases/TEST-CASES.md    # human-readable checklist + automation mapping
  lib/
    client.py            # HTTP + SSE client
    env.py               # .env loading
  scripts/
    run_all.sh
    smoke_cursor.sh
    check_zombies.sh
  tests/
    test_preflight.py
    test_cursor_session.py
    test_cursor_messaging.py
    test_session_lifecycle.py
    test_negative_auth.py
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_SDK_URL` | `http://localhost:7778` | Server base URL |
| `CURSOR_API_KEY` | from `.env` | Cursor User API key |

## Notes

- Tests skip automatically if the server is not reachable.
- Cursor messaging tests can take 30–90s per turn (cold CLI boot).
- UI-specific cases (C-04, M-04, N-04) are documented in `cases/TEST-CASES.md` for manual runs.
