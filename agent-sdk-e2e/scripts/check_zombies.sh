#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

.venv/bin/python - <<'PY'
from lib.client import list_orphan_cursor_agents

orphans = list_orphan_cursor_agents()
if not orphans:
    print("OK: no orphan agent acp processes without --api-key")
else:
    print("WARN: orphan cursor agent processes (cause keychain login prompts):")
    for pid, cmd in orphans:
        print(f"  pid={pid}  {cmd[:120]}")
    raise SystemExit(1)
PY
