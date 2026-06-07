#!/usr/bin/env bash
# Quick smoke test: health + cursor session + one message.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi

export AGENT_SDK_URL="${AGENT_SDK_URL:-http://localhost:7778}"
.venv/bin/pytest tests/test_preflight.py tests/test_cursor_session.py::TestCursorSessionCreate::test_create_without_body_secrets_uses_server_env tests/test_cursor_messaging.py::TestCursorMessaging::test_single_turn_exact_reply -v "$@"
