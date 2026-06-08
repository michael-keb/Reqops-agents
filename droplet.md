# ReqOps stack droplet (DigitalOcean)

| Field | Value |
|-------|-------|
| **Name** | `reqops-stack` |
| **ID** | `575922930` |
| **IP** | `170.64.224.128` |
| **Region** | `syd1` (Sydney) |
| **Size** | `s-2vcpu-4gb` (2 vCPU, 4 GB RAM, 80 GB disk) — **~$24/mo** |
| **Image** | Ubuntu 24.04 |

## URLs

| What | URL |
|------|-----|
| **App (Auth0 login)** | https://app.reqops.com/ |
| **Workshop UI** | https://app.reqops.com/thoughts/:sessionId (after login) |
| **Discovery config** | https://app.reqops.com/api/v1/discovery/config (public) |
| **Droplet IP (no Auth0)** | http://170.64.224.128/ — use domain only for login |

## DNS (required)

`app.reqops.com` is on **Cloudflare**. Add or update:

| Type | Name | Value | Proxy |
|------|------|-------|-------|
| A | `app` | `170.64.224.128` | Proxied (orange) or DNS only (grey) |

- **Proxied + Flexible SSL** (recommended): Cloudflare terminates HTTPS; Caddy serves HTTP on :80.
- **DNS only (grey cloud)**: Change `deploy/caddy/Caddyfile` to `{$PUBLIC_HOST}` (no `http://` prefix) for Let's Encrypt on :443.

## Auth0 (production)

| Setting | Value |
|---------|-------|
| Tenant | `reqops.au.auth0.com` |
| SPA | Staging-Reqops · `kP5WPBHJmk97JQEYOtN2ToMsoMC8dP90` |
| Backend | `AUTH0_AUDIENCE` = SPA client id (ID token flow) |
| Dev bypass | **Off** (`DEV_USER_SUB` and `VITE_DEV_AUTH_BYPASS` empty) |

**Add in [Auth0 Application Settings](https://manage.auth0.com/)** (SPA `Staging-Reqops`):

```
Allowed Callback URLs:  https://app.reqops.com
Allowed Logout URLs:    https://app.reqops.com
Allowed Web Origins:    https://app.reqops.com
```

Or run `./deploy/configure-auth0-app.sh` with `PUBLIC_ORIGIN=https://app.reqops.com` and M2M credentials.

Enable **Refresh Token Rotation** on the SPA. Without these URLs, login redirects fail with `callback URL mismatch`.

## SSH

```bash
ssh -i deploy/.ssh-reqops/id_ed25519 root@170.64.224.128
```

Private key: `deploy/.ssh-reqops/id_ed25519` (gitignored — keep local).

## Manage stack (on droplet)

```bash
cd /opt/Reqops-agents
docker compose ps
docker compose logs -f reqops-backend agent-sdk uplift
./deploy/up.sh          # rebuild + restart after code changes
```

## Secrets

- `DIGITAL_OCEAN_API` — local `.env` only, **never commit**; rotate if exposed
- Deploy `.env` lives on droplet at `/opt/Reqops-agents/.env` (not in git)
- `CURSOR_API_KEY` required for agent-sdk

## Re-deploy from your Mac

```bash
rsync -az --exclude node_modules --exclude .git --exclude deploy/.ssh-reqops \
  -e "ssh -i deploy/.ssh-reqops/id_ed25519" \
  ./ root@170.64.224.128:/opt/Reqops-agents/
rsync -az --exclude node_modules -e "ssh -i deploy/.ssh-reqops/id_ed25519" \
  "../Thinkfast book/ReqOps/" root@170.64.224.128:/opt/ReqOps/
ssh -i deploy/.ssh-reqops/id_ed25519 root@170.64.224.128 \
  "cd /opt/Reqops-agents && ./deploy/up.sh"
```
