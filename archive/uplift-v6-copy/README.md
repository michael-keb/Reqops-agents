# Uplift v6

Chat UI wrapping a **persistent Cursor `agent` CLI** on a pseudo-terminal (PTY).

## Architecture

```
Browser (chat + xterm.js)  ←WebSocket→  bridge/server.py  ←PTY→  agent (long-lived)
                                              ↓
                                        sessions/ artifacts
```

| Layer | Role |
|-------|------|
| **UI shell** | Chat message list + composer; xterm.js panel for raw terminal output |
| **PTY wrapper** | `bridge/pty_agent.py` — spawns `agent` once, writes stdin, reads merged stdout/stderr |
| **WebSocket** | Binary chunks → xterm; JSON events → chat (turn complete, exit, etc.) |
| **Completion** | Prompt `→` reappears, or idle timeout (`UPLIFT_IDLE_DONE_S`, default 2.5s) |
| **Session** | `UPLIFT_SESSION` env set per discovery session; cwd/env persist in the shell |
| **Lifecycle** | Stop → SIGINT; Restart → kill + respawn; cleanup on server exit |

## Run

```bash
cd uplift-v6
./serve --open          # http://127.0.0.1:8786/
```

Requires `agent` on PATH and `agent login` completed.

First message starts a discovery session (creates `sessions/<id>/`) and sends a bootstrap prompt to the agent. Later messages go straight to stdin.

## Benchmark harness

Scripted replies via WebSocket — measures agent compute time without human think gaps:

```bash
./serve   # terminal 1
python bench/auto_reply.py --pitch "dog walking app" \
  --replies "A) busy professionals" "B) elderly owners" --json
```

Use `--continue` to append replies to an active session. Turn durations come from `turn_complete.elapsed_s`; use `session_turn` in output (from disk) when bridge restarts reset the in-memory counter.

## Env

| Variable | Default | Purpose |
|----------|---------|---------|
| `UPLIFT_AGENT_MODE` | `pty` | `pty` (one long-lived process) · `headless` (spawn per turn, stream-json tool trace) |
| `UPLIFT_PORT` | `8786` | HTTP + WebSocket port |
| `UPLIFT_LOGS_DIR` | `./logs` | Global trace JSONL when no session |
| `UPLIFT_TRACE_STDOUT` | `lines` | `lines` · `chunks` · `off` — stdout trace granularity |
| `UPLIFT_TRACE_MAX` | `5000` | In-memory trace ring buffer size |
| `UPLIFT_QUIET` | — | Set `1` to suppress stderr trace mirror |
| `UPLIFT_IDLE_DONE_S` | `2.5` | Idle seconds before marking turn complete |
| `UPLIFT_STARTUP_TIMEOUT_S` | `120` | Wait for first prompt on spawn |
| `UPLIFT_TURN_TIMEOUT_S` | `600` | Max seconds per turn |
| `UPLIFT_SESSIONS_DIR` | `./sessions` | Session artifact root |

## Trace / logging

Every agent action is recorded:

| Sink | Contents |
|------|----------|
| **UI trace panel** | Live SSE stream — stdin, stdout (ANSI stripped), events, turns, errors |
| **`sessions/<id>/agent.trace.jsonl`** | Structured JSON lines per session |
| **`sessions/<id>/agent-pty.txt`** | Raw PTY transcript (exact bytes) |
| **stderr** | Timestamped mirror (unless `UPLIFT_QUIET=1`) |

| **`sessions/<id>/agent.stream.jsonl`** | Raw NDJSON from `agent --output-format stream-json` |
| **Trace kinds `tool`, `thinking`, `assistant`, `result`** | Parsed internal agent events (reads, writes, shell, etc.) |

API: `GET /api/trace`, `GET /api/trace/stream`, `POST /api/trace/clear`

### Agent output env

| Variable | Default | Purpose |
|----------|---------|---------|
| `UPLIFT_AGENT_OUTPUT` | `stream-json` | `stream-json` (internal trace) · `text` (legacy, blind gap) |
| `UPLIFT_TRACE_THINKING` | off | Set `1` to log thinking deltas (noisy) |
| `UPLIFT_STREAM_PARTIAL` | off | Set `1` for `--stream-partial-output` |

## vs v5

v5 respawns headless `agent -p` per HTTP turn. v6 keeps one interactive PTY process — session state (cwd, env) persists and output streams live through xterm.js.
