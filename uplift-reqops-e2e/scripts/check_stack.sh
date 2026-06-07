#!/usr/bin/env bash
# Print OK/FAIL for every service in the ReqOps + Uplift stack.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi

.venv/bin/python - <<'PY'
from lib.env import load_dotenv
from lib.stack import check_all, format_stack_report

load_dotenv()
results = check_all()
print(format_stack_report(results))
failed = [r for r in results if not r.ok]
raise SystemExit(0 if not failed else 1)
PY
