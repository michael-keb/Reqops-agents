#!/usr/bin/env bash
# Run full agent-sdk E2E suite.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi

export AGENT_SDK_URL="${AGENT_SDK_URL:-http://localhost:7778}"
echo "Running E2E against $AGENT_SDK_URL"
.venv/bin/pytest tests/ -v "$@"
