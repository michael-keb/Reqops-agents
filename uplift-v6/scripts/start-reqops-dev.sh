#!/usr/bin/env bash
# Start Uplift v6 bridge for ReqOps local dev (mock agent = no Cursor CLI).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export UPLIFT_PORT="${UPLIFT_PORT:-8786}"
export UPLIFT_MOCK_AGENT="${UPLIFT_MOCK_AGENT:-1}"
export UPLIFT_MOCK_DELAY_MS="${UPLIFT_MOCK_DELAY_MS:-80}"
export UPLIFT_AGENT_MODE="${UPLIFT_AGENT_MODE:-headless}"
exec ./serve
