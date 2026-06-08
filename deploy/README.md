# Single-server deployment

Run the full **ReqOps + Uplift v6 + agent-sdk** stack on one machine with Docker Compose.

## What runs

| Container | Role | Exposed |
|-----------|------|---------|
| `postgres` | `thoughtweaver` + `agent_sdk_server` databases | internal |
| `agent-sdk` | Cursor agent sessions (signal board) | internal |
| `uplift` | Discovery + signal bridge | internal |
| `reqops-backend` | Fastify API | internal |
| `reqops-frontend` | Vite SPA (static) | internal |
| `nginx` | Public entry point | `:80` (configurable) |

Only **nginx** is public. The backend talks to uplift and agent-sdk over the Docker network.

## How agents run (CLI-as-a-service)

Uplift does **not** spawn the Cursor CLI directly in production. With the default SDK runners:

```
ReqOps backend → uplift bridge → agent-sdk (:7778) → Cursor CLI (inside agent-sdk)
```

| Component | Runs CLI? | Notes |
|-----------|-----------|-------|
| **uplift** | No | Orchestrator only (`UPLIFT_*_RUNNER=sdk`) |
| **agent-sdk** | Yes | REST API + ACP supervisor; this is CLI-as-a-service |
| **Direct CLI** (`HeadlessAgent`) | uplift subprocess | Not used in compose; needs `agent` on uplift host |

**Auth:** `CURSOR_API_KEY` only — no `agent login` in Docker.

**Provider** (`UPLIFT_SDK_PROVIDER`):

| Value | When to use |
|-------|-------------|
| `unix_local` (default) | Single server — CLI runs inside agent-sdk container |
| `daytona` | Isolated cloud sandboxes; set `DAYTONA_API_KEY` on agent-sdk |

agent-sdk persists agent workspaces at `AGENT_SDK_LOCAL_VOL_ROOT` (mounted volume in compose).

## Prerequisites

- Docker 24+ with Compose v2
- ReqOps repo at `../Thinkfast book/ReqOps` (or set `REQOPS_ROOT` in `.env`)
- `CURSOR_API_KEY`
- `DAYTONA_API_KEY` only if `UPLIFT_SDK_PROVIDER=daytona`

**Server sizing:** 4 GB RAM minimum, 8 GB recommended.

## Quick start

```bash
cp .env.docker.example .env
# Edit .env — at minimum set CURSOR_API_KEY and POSTGRES_PASSWORD

./deploy/up.sh
```

Open **http://localhost/thoughts/:sessionId**

Verify:

```bash
curl -s http://localhost/api/v1/discovery/config | jq .data.engine
# → "uplift"

curl -s http://localhost/healthz  # may 404 at edge — use API path:
curl -s http://localhost/api/v1/discovery/config
```

## Production checklist (Auth0)

1. Set strong `POSTGRES_PASSWORD`
2. Copy `deploy/production.env.example` → `.env` (Auth0 vars, **no** `DEV_USER_SUB` / `VITE_DEV_AUTH_BYPASS`)
3. Set `CORS_ORIGINS` and `VITE_WS_BASE_URL` to your public origin
4. **Auth0 dashboard** (Applications → Staging-Reqops SPA) — add your origin to:
   - Allowed Callback URLs: `http://YOUR_IP`
   - Allowed Logout URLs: `http://YOUR_IP`
   - Allowed Web Origins: `http://YOUR_IP`
   - Enable **Refresh Token Rotation** (SPA uses `useRefreshTokens`)
5. Rebuild: `./deploy/up.sh` (frontend bakes `VITE_AUTH0_*` at build time)
6. Optional: `./deploy/configure-auth0-app.sh` if you have a Management API M2M app
7. Put TLS in front for production (then update Auth0 URLs to `https://...`)

**ReqOps tenant (existing):** `reqops.au.auth0.com` · SPA client `kP5WPBHJmk97JQEYOtN2ToMsoMC8dP90` · backend verifies **ID tokens** (`AUTH0_AUDIENCE` = client id).

## Commands

```bash
docker compose up -d --build    # start / rebuild
docker compose ps
docker compose logs -f uplift agent-sdk reqops-backend
docker compose down             # stop (keeps volumes)
docker compose down -v          # stop + wipe DB/sessions
```

## VPS without Docker (systemd)

If you prefer native processes on a VPS, use the unit files in `deploy/systemd/`:

```bash
# Edit paths and env in deploy/systemd/reqops-stack.env.example, copy to /etc/reqops-stack.env
sudo cp deploy/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now reqops-stack.target
```

This mirrors `uplift-reqops-e2e/scripts/run_stack.sh` — Postgres, agent-sdk, uplift, ReqOps backend, ReqOps frontend, plus optional nginx on the host.

## Troubleshooting

| Symptom | Check |
|---------|-------|
| Frontend loads, API 502 | `docker compose logs reqops-backend` — migrations, `DATABASE_URL` |
| Discovery hangs | `docker compose logs uplift agent-sdk` — `CURSOR_API_KEY`; if `UPLIFT_SDK_PROVIDER=daytona`, also `DAYTONA_API_KEY` |
| Agent sessions lost on restart | Ensure `agent_sdk_volumes` volume exists (`docker volume ls`) |
| WebSocket fails | Rebuild frontend with correct `VITE_WS_BASE_URL` for your host |
| ReqOps build fails | `REQOPS_ROOT` path, Node 20 lockfiles present |
