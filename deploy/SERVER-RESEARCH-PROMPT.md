# Server research prompt

Copy everything below the line into ChatGPT, Claude, Perplexity, or a colleague.

---

## Prompt (copy from here)

I'm deploying a **single-server** workshop stack on one VPS using **Docker Compose**. Help me choose the right provider, instance size, and region.

### What runs on the box (all containers on one machine)

| Service | Role | Notes |
|---------|------|-------|
| **PostgreSQL 16** | 2 databases (`thoughtweaver`, `agent_sdk_server`) | Persistent volume |
| **agent-sdk** | REST API that runs **Cursor agent CLI** via ACP supervisor (`unix_local` provider) | Needs persistent disk for agent workspaces; `CURSOR_API_KEY` auth |
| **uplift-v6** | Python bridge — discovery + signal orchestration | Calls agent-sdk over HTTP; persistent `sessions/` disk |
| **ReqOps backend** | Node 20 / Fastify / Prisma API | Talks to Postgres + uplift |
| **ReqOps frontend** | Static Vite/React SPA behind nginx | Built at deploy time |
| **nginx** | Reverse proxy :80/:443 | Only public entry point |

**Architecture:** Browser → nginx → ReqOps backend → uplift → **agent-sdk (CLI-as-a-service)** → Cursor cloud API.

Uplift does **not** run the Cursor CLI directly. agent-sdk spawns supervisor + `agent` subprocesses inside its container.

### Workload profile

- **Users:** Small team / workshop (roughly 1–10 concurrent users, not thousands)
- **Agent pattern:** SDK runners — one persistent agent-sdk session per discovery workshop / signal extract; LLM calls can run 1–3 minutes per turn
- **Concurrency:** Occasional parallel signal work; not 9 separate CLI processes by default
- **Disk:** Postgres + uplift sessions + agent-sdk volumes — estimate **20–50 GB** comfortable headroom
- **Network:** Outbound HTTPS to Cursor API (`api2.cursor.sh`); no inbound except 80/443
- **Auth:** API keys only (`CURSOR_API_KEY`) — no browser `agent login`

### What I need from you

1. **Minimum vs recommended specs** (vCPU, RAM, disk type/size) for this stack with brief justification
2. **Provider comparison** for this use case (e.g. Hetzner, DigitalOcean, Linode, Vultr, AWS Lightsail, OVH) — cost, reliability, EU/US regions if relevant
3. **Docker-friendly** — Ubuntu 24.04 LTS, root or sudo, single public IPv4 fine
4. **When I'd need to upgrade** — signals that we're outgrowing one box (RAM, CPU, disk I/O)
5. **Daytona vs unix_local** — confirm whether `unix_local` inside agent-sdk on a dedicated VPS is sufficient, or when isolated sandboxes (Daytona) become necessary
6. **Backup strategy** — what to snapshot (Postgres volume, `agent_sdk_volumes`, `uplift_sessions`)
7. **TLS** — simplest path (Caddy vs Certbot + nginx) for one domain pointing at the VPS
8. **Red flags** — providers/plans to avoid for long-running agent subprocesses and WebSocket/SSE through nginx

### Constraints

- **Budget:** Prefer **$20–60/month** all-in if realistic; call out if that's too low
- **Region:** [FILL IN: e.g. Australia / EU / US East — closest to users]
- **Ops skill:** Comfortable with SSH, Docker Compose, `.env` files — not fully managed PaaS
- **Not using:** Render/Railway multi-service split — this must be **one VPS, one `docker compose up`**

### Deliverable format

- **Top 3 provider + plan recommendations** with monthly cost estimate
- **One "start here" pick** if you had to choose today
- **Pre-flight checklist** before I run `./deploy/up.sh`
- **Optional:** Hetzner vs DigitalOcean vs Linene for this specific agent-heavy workload

### Reference deploy command (after server is provisioned)

```bash
git clone https://github.com/michael-keb/Reqops-agents.git
# clone ReqOps repo alongside, set REQOPS_ROOT in .env
cp .env.docker.example .env   # CURSOR_API_KEY, POSTGRES_PASSWORD, REQOPS_ROOT
./deploy/up.sh
```

---

## Optional context to paste after the prompt

- Repo: https://github.com/michael-keb/Reqops-agents
- Deploy docs: `deploy/README.md` in that repo
- Default env: `UPLIFT_SDK_PROVIDER=unix_local`, `UPLIFT_*_RUNNER=sdk`
