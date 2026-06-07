#!/usr/bin/env bash
# Stop processes started by run_stack.sh (and optional postgres container).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
E2E_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PID_FILE="${E2E_ROOT}/.stack/pids.env"

log() { printf '[stop_stack] %s\n' "$*"; }

if [[ ! -f "${PID_FILE}" ]]; then
  log "no pid file at ${PID_FILE} — nothing to stop"
  exit 0
fi

# shellcheck disable=SC1090
source "${PID_FILE}"

for key in reqops_frontend reqops_backend uplift agent_sdk; do
  pid_var="${key}"
  pid="${!pid_var:-}"
  if [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null; then
    log "stopping ${key} (pid ${pid})"
    kill "${pid}" 2>/dev/null || true
    sleep 1
    kill -9 "${pid}" 2>/dev/null || true
  fi
done

if [[ "${STARTED_PG:-0}" == "1" && -n "${POSTGRES_CONTAINER:-}" ]]; then
  if command -v docker >/dev/null 2>&1; then
    log "stopping postgres container ${POSTGRES_CONTAINER}"
    docker stop "${POSTGRES_CONTAINER}" >/dev/null 2>&1 || true
  fi
fi

rm -f "${PID_FILE}"
log "done"
