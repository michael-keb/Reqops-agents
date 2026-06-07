# Agent-SDK E2E Test Cases

Manual and automated coverage for Cursor + agent-sdk integration.
Automated tests live in `tests/`; this document is the source-of-truth checklist.

## Prerequisites

| ID | Case | Automated |
|----|------|-----------|
| P-01 | agent-sdk server running on `AGENT_SDK_URL` (default `http://localhost:7778`) | `test_preflight.py::test_server_health` |
| P-02 | `GET /health` returns `cursor_api_key_configured: true` | `test_preflight.py::test_cursor_api_key_configured_on_server` |
| P-03 | No `agent acp` processes without `--api-key` on host | `test_preflight.py::test_no_orphan_cursor_agent_processes`, `scripts/check_zombies.sh` |
| P-04 | UI page loads at `/ui/` | `test_preflight.py::test_ui_reachable` |
| P-05 | `CURSOR_API_KEY` set in `Call-backup/.env` | `conftest.cursor_key` fixture |

## Cursor session creation

| ID | Case | Expected | Automated |
|----|------|----------|-----------|
| C-01 | `POST /sessions` with `agent_type: cursor`, no body secrets | `connected: true`, `agent_type: cursor`, server injects key | `test_cursor_session.py::test_create_without_body_secrets_uses_server_env` |
| C-02 | `POST /sessions` with explicit `CURSOR_API_KEY` in secrets | `connected: true` | `test_cursor_session.py::test_create_with_explicit_api_key` |
| C-03 | Invalid `CURSOR_API_KEY` on message | Auth error, no successful reply | `test_cursor_session.py::test_invalid_api_key_fails_on_message` |
| C-04 | UI: Agent = Cursor, Auth empty, Connect | Banner shows `(cursor)` | Manual |
| C-05 | UI: Agent = Claude (default before fix) | Uses Claude, not Cursor | Manual regression |

## Cursor messaging

| ID | Case | Expected | Automated |
|----|------|----------|-----------|
| M-01 | Single turn: "Reply exactly: HELLO" | Response contains HELLO | `test_cursor_messaging.py::test_single_turn_exact_reply` |
| M-02 | Follow-up turn in same session | Second reply correct | `test_cursor_messaging.py::test_follow_up_turn` |
| M-03 | No 401 / invalid bearer in stream | Clean stream | `test_cursor_messaging.py::test_no_auth_error_in_stream` |
| M-04 | UI: send message while idle | Agent responds in thread | Manual |
| M-05 | UI: queue message while generating | Queued message runs after turn | Manual |

## Session lifecycle

| ID | Case | Expected | Automated |
|----|------|----------|-----------|
| L-01 | Delete session + create new | New session_id, message works | `test_session_lifecycle.py::test_disconnect_and_new_session` |
| L-02 | `GET /sessions/{id}` metadata | `agent_type`, `sandbox_ref` present | `test_session_lifecycle.py::test_get_session_metadata` |
| L-03 | UI: Disconnect → Connect | Fresh session | Manual |
| L-04 | UI: hard refresh → Connect | Cursor default, works | Manual |

## Negative / regression

| ID | Case | Expected | Automated |
|----|------|----------|-----------|
| N-01 | Claude without OAuth token | Auth failure on message, not keychain loop | `test_negative_auth.py::test_claude_without_token_fails_or_errors_on_message` |
| N-02 | Claude with invalid token | 401 / authentication error | `test_negative_auth.py::test_claude_with_invalid_token_errors` |
| N-03 | Cursor session secrets are Cursor-only | No `CLAUDE_CODE_OAUTH_TOKEN` | `test_negative_auth.py::test_cursor_agent_type_not_claude` |
| N-04 | macOS keychain "cursor-user" dialog | Must NOT appear for API-key cursor sessions | Manual (watch during C-04, M-04) |

## Running tests

```bash
# From Call-backup/agent-sdk-e2e
./scripts/run_all.sh          # full suite
./scripts/smoke_cursor.sh     # fast smoke (preflight + one message)
./scripts/check_zombies.sh    # orphan process check only
```

Requires agent-sdk server:

```bash
cd ../agent-sdk
export DATABASE_URL="postgresql://$(whoami)@localhost:5432/agent_sdk_server"
export PYTHONPATH=src
.venv/bin/python -m uvicorn api.server:app --host 0.0.0.0 --port 7778
```
