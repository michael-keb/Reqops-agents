#!/usr/bin/env bash
# Cancel all in-flight agent work: uplift signal extracts, agent-sdk sessions, CLI subprocesses.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
E2E_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CALL_BACKUP="$(cd "${E2E_ROOT}/.." && pwd)"
UPLIFT_ROOT="${UPLIFT_ROOT:-${CALL_BACKUP}/uplift-v6}"
UPLIFT_URL="${UPLIFT_BRIDGE_URL:-http://127.0.0.1:8786}"
SDK_URL="${AGENT_SDK_URL:-http://127.0.0.1:7778}"

log() { printf '[cancel_agents] %s\n' "$*"; }

# ── 1 uplift: cancel signal extract for every reqops session ────────────────
if curl -sf "${UPLIFT_URL}/api/health" >/dev/null 2>&1; then
  sessions_dir="${UPLIFT_ROOT}/sessions"
  if [[ -d "${sessions_dir}" ]]; then
    while IFS= read -r -d '' dir; do
      sid="$(basename "${dir}")"
      [[ "${sid}" == reqops-* ]] || continue
      if curl -sf -X POST "${UPLIFT_URL}/api/sessions/${sid}/signals/cancel" \
        -H "Content-Type: application/json" -d '{}' >/dev/null 2>&1; then
        log "uplift cancel signals: ${sid}"
      fi
    done < <(find "${sessions_dir}" -mindepth 1 -maxdepth 1 -type d -print0 2>/dev/null)
  fi
  active="${sessions_dir}/.active"
  if [[ -f "${active}" ]]; then
    sid="$(tr -d '[:space:]' < "${active}")"
    if [[ -n "${sid}" ]]; then
      curl -sf -X POST "${UPLIFT_URL}/api/sessions/${sid}/signals/cancel" \
        -H "Content-Type: application/json" -d '{}' >/dev/null 2>&1 \
        && log "uplift cancel signals (active): ${sid}" || true
    fi
  fi
else
  log "uplift bridge not reachable — skip"
fi

# ── 2 agent-sdk: cancel + delete active sessions ────────────────────────────
if curl -sf "${SDK_URL}/health" >/dev/null 2>&1; then
  sdk_count=0
  while IFS= read -r sid; do
    [[ -z "${sid}" ]] && continue
    sdk_count=$((sdk_count + 1))
    curl -sf -X POST "${SDK_URL}/sessions/${sid}/cancel" >/dev/null 2>&1 \
      && log "agent-sdk cancel: ${sid}" || true
    curl -sf -X DELETE "${SDK_URL}/sessions/${sid}" >/dev/null 2>&1 \
      && log "agent-sdk delete: ${sid}" || true
  done < <(curl -sf "${SDK_URL}/sessions" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
for row in data if isinstance(data, list) else []:
    sid = row.get('session_id')
    if sid:
        print(sid)
" 2>/dev/null || true)
  if [[ "${sdk_count}" -eq 0 ]]; then
    log "agent-sdk: no active sessions"
  fi
else
  log "agent-sdk not reachable — skip"
fi

# ── 3 headless CLI subprocesses (discovery turns) ───────────────────────────
if pgrep -f "agent --resume" >/dev/null 2>&1; then
  log "killing agent --resume subprocesses…"
  pkill -f "agent --resume" 2>/dev/null || true
  sleep 1
  pkill -9 -f "agent --resume" 2>/dev/null || true
else
  log "no agent --resume subprocesses"
fi

log "done"
