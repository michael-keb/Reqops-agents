#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Missing .env — copy .env.docker.example and set CURSOR_API_KEY:" >&2
  echo "  cp .env.docker.example .env" >&2
  exit 1
fi

# shellcheck disable=SC1091
set -a && source .env && set +a

REQOPS_ROOT="${REQOPS_ROOT:-../Thinkfast book/ReqOps}"
REQOPS_ROOT="$(cd "$ROOT" && cd "$REQOPS_ROOT" 2>/dev/null && pwd)" || {
  echo "ReqOps not found at ${REQOPS_ROOT} (set REQOPS_ROOT in .env)" >&2
  exit 1
}

[[ -d "${REQOPS_ROOT}/Reqops_backend" ]] || {
  echo "ReqOps backend not found at ${REQOPS_ROOT}/Reqops_backend" >&2
  exit 1
}

# Docker build context is the repo root — copy ReqOps in (symlinks outside context are ignored by Docker).
BUILD_ROOT="${ROOT}/ReqOps"
rm -rf "$BUILD_ROOT"
mkdir -p "$BUILD_ROOT"
rsync -a --delete \
  --exclude node_modules --exclude dist --exclude .env --exclude .env.local \
  "${REQOPS_ROOT}/" "${BUILD_ROOT}/"
echo "[up] staged ReqOps for docker build from ${REQOPS_ROOT}"

export REQOPS_BUILD_ROOT=ReqOps

docker compose up -d --build "$@"

echo ""
echo "Stack starting. Public UI: http://localhost:${HTTP_PORT:-80}/thoughts/:sessionId"
echo "Health: curl -s http://localhost:${HTTP_PORT:-80}/api/v1/discovery/config"
