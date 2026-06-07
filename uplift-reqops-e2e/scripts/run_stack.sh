#!/usr/bin/env bash
# Start the full ReqOps + Uplift + agent-sdk stack (background processes).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
E2E_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CALL_BACKUP="$(cd "${E2E_ROOT}/.." && pwd)"
STACK_DIR="${E2E_ROOT}/.stack"
LOG_DIR="${STACK_DIR}/logs"
PID_FILE="${STACK_DIR}/pids.env"

REQOPS_ROOT="${REQOPS_ROOT:-${CALL_BACKUP}/../Thinkfast book/ReqOps}"
UPLIFT_ROOT="${UPLIFT_ROOT:-${CALL_BACKUP}/uplift-v6}"
AGENT_SDK_ROOT="${AGENT_SDK_ROOT:-${CALL_BACKUP}/agent-sdk}"

POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-uplift-reqops-pg}"
POSTGRES_IMAGE="${POSTGRES_IMAGE:-postgres:15}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-thoughtweaver}"

mkdir -p "${LOG_DIR}"
: > "${PID_FILE}"

log() { printf '[run_stack] %s\n' "$*"; }
die() { log "ERROR: $*"; exit 1; }

port_open() {
  local port="$1"
  (echo >/dev/tcp/127.0.0.1/"${port}") >/dev/null 2>&1
}

wait_url() {
  local url="$1" label="$2" tries="${3:-60}"
  local i=0
  while (( i < tries )); do
    if curl -sf "${url}" >/dev/null 2>&1; then
      log "ready: ${label}"
      return 0
    fi
    sleep 1
    (( i++ )) || true
  done
  die "${label} not ready at ${url} (see ${LOG_DIR})"
}

start_bg() {
  local name="$1" logfile="$2"
  shift 2
  log "starting ${name}…"
  nohup "$@" >"${logfile}" 2>&1 &
  local pid=$!
  echo "${name}=${pid}" >> "${PID_FILE}"
  log "${name} pid ${pid} → ${logfile}"
}

# ── env ─────────────────────────────────────────────────────────────────────
if [[ -f "${CALL_BACKUP}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${CALL_BACKUP}/.env"
  set +a
fi
if [[ -f "${E2E_ROOT}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${E2E_ROOT}/.env"
  set +a
fi

[[ -d "${REQOPS_ROOT}/Reqops_backend" ]] || die "ReqOps not found at ${REQOPS_ROOT} (set REQOPS_ROOT)"
[[ -d "${UPLIFT_ROOT}" ]] || die "uplift-v6 not found at ${UPLIFT_ROOT}"
[[ -d "${AGENT_SDK_ROOT}" ]] || die "agent-sdk not found at ${AGENT_SDK_ROOT}"

# ── 1 PostgreSQL ─────────────────────────────────────────────────────────────
STARTED_PG=0
if port_open "${POSTGRES_PORT}"; then
  log "postgres already listening on :${POSTGRES_PORT}"
else
  command -v docker >/dev/null 2>&1 || die "docker required to start postgres (or start postgres yourself on :${POSTGRES_PORT})"
  if docker ps -a --format '{{.Names}}' | grep -qx "${POSTGRES_CONTAINER}"; then
    docker start "${POSTGRES_CONTAINER}" >/dev/null
  else
    docker run -d --name "${POSTGRES_CONTAINER}" \
      -p "${POSTGRES_PORT}:5432" \
      -e POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
      -e POSTGRES_DB="${POSTGRES_DB}" \
      "${POSTGRES_IMAGE}" >/dev/null
  fi
  STARTED_PG=1
  echo "POSTGRES_CONTAINER=${POSTGRES_CONTAINER}" >> "${PID_FILE}"
  echo "STARTED_PG=1" >> "${PID_FILE}"
  for _ in $(seq 1 30); do
    if port_open "${POSTGRES_PORT}"; then
      log "ready: postgres"
      break
    fi
    sleep 1
  done
  port_open "${POSTGRES_PORT}" || die "postgres not listening on :${POSTGRES_PORT}"
  sleep 2
  log "postgres docker container ${POSTGRES_CONTAINER}"
fi

# agent-sdk DB (best-effort)
if command -v psql >/dev/null 2>&1; then
  PGPASSWORD="${POSTGRES_PASSWORD}" psql -h 127.0.0.1 -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d postgres \
    -tc "SELECT 1 FROM pg_database WHERE datname='agent_sdk_server'" 2>/dev/null | grep -q 1 \
    || PGPASSWORD="${POSTGRES_PASSWORD}" psql -h 127.0.0.1 -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d postgres \
      -c "CREATE DATABASE agent_sdk_server;" 2>/dev/null \
    && log "database agent_sdk_server ok" \
    || log "warn: could not create agent_sdk_server (agent-sdk may use its own postgres)"
fi

# ── 2 agent-sdk ──────────────────────────────────────────────────────────────
if port_open 7778; then
  log "agent-sdk already on :7778"
else
  export DATABASE_URL="${AGENT_SDK_DATABASE_URL:-postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:${POSTGRES_PORT}/agent_sdk_server}"
  export PYTHONPATH="${AGENT_SDK_ROOT}/src"
  SDK_PY="${AGENT_SDK_ROOT}/.venv/bin/python"
  [[ -x "${SDK_PY}" ]] || die "agent-sdk venv missing — run: cd ${AGENT_SDK_ROOT} && python3 -m venv .venv && .venv/bin/pip install -e ."
  start_bg agent_sdk "${LOG_DIR}/agent-sdk.log" \
    "${SDK_PY}" -m uvicorn api.server:app --host 0.0.0.0 --port 7778
  wait_url "http://127.0.0.1:7778/health" "agent-sdk"
fi

# ── 3 uplift bridge ──────────────────────────────────────────────────────────
if port_open 8786; then
  log "uplift bridge already on :8786"
else
  export UPLIFT_PORT="${UPLIFT_PORT:-8786}"
  export UPLIFT_AGENT_MODE="${UPLIFT_AGENT_MODE:-headless}"
  export UPLIFT_DISCOVERY_RUNNER="${UPLIFT_DISCOVERY_RUNNER:-sdk}"
  export UPLIFT_SIGNALS_RUNNER="${UPLIFT_SIGNALS_RUNNER:-sdk}"
  export UPLIFT_AGENT_SDK_URL="${UPLIFT_AGENT_SDK_URL:-http://127.0.0.1:7778}"
  start_bg uplift "${LOG_DIR}/uplift-v6.log" \
    bash -lc "cd '${UPLIFT_ROOT}' && ./serve"
  wait_url "http://127.0.0.1:8786/api/health" "uplift bridge"
fi

# ── 4 ReqOps backend ─────────────────────────────────────────────────────────
if port_open 3000; then
  log "reqops backend already on :3000"
else
  start_bg reqops_backend "${LOG_DIR}/reqops-backend.log" \
    bash -lc "cd '${REQOPS_ROOT}/Reqops_backend' && npm run dev"
  wait_url "http://127.0.0.1:3000/healthz" "reqops backend"
fi

# ── 5 ReqOps frontend ────────────────────────────────────────────────────────
if port_open 8080; then
  log "reqops frontend already on :8080"
else
  start_bg reqops_frontend "${LOG_DIR}/reqops-frontend.log" \
    bash -lc "cd '${REQOPS_ROOT}/Reqops_Frontend' && npm run dev"
  wait_url "http://127.0.0.1:8080/" "reqops frontend"
fi

# ── verify ───────────────────────────────────────────────────────────────────
log "running preflight…"
if [[ -x "${E2E_ROOT}/scripts/check_stack.sh" ]]; then
  (cd "${E2E_ROOT}" && ./scripts/check_stack.sh) || log "warn: preflight reported failures — check ${LOG_DIR}"
else
  log "skip preflight (missing check_stack.sh)"
fi

cat <<EOF

Stack started.

  UI:        http://127.0.0.1:8080/thoughts/:sessionId
  Backend:   http://127.0.0.1:3000/healthz
  Uplift:    http://127.0.0.1:8786/api/health
  agent-sdk: http://127.0.0.1:7778/health

  Logs:      ${LOG_DIR}/
  PIDs:      ${PID_FILE}

  Stop:      ./scripts/stop_stack.sh
  Verify:    ./scripts/check_stack.sh

EOF
