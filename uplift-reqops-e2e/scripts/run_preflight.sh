#!/usr/bin/env bash
# Pytest preflight — same checks as check_stack.sh but via test suite.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi

.venv/bin/pytest tests/test_stack_preflight.py -v -s "$@"
