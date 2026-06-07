#!/usr/bin/env bash
# Run Uplift from your Mac Terminal: persistent local PTY agent (not headless per-turn spawn).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export UPLIFT_AGENT_MODE=pty
echo "If a turn hangs, run: python3 scripts/trace-wait.py" >&2
exec ./serve --open "$@"
