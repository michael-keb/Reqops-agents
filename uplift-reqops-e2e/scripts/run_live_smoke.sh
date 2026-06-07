#!/usr/bin/env bash
# Full uplift path smoke: bootstrap discovery turn + SDK goal extract (slow).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi

export UPLIFT_E2E_LIVE=1
./scripts/run_preflight.sh
.venv/bin/pytest tests/test_uplift_paths_smoke.py -v -s "$@"
