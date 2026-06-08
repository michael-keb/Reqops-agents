#!/usr/bin/env bash
# Patch Auth0 SPA application URLs for a deployed origin (Management API).
# Requires a Machine-to-Machine app authorized for Auth0 Management API.
#
# Usage:
#   export AUTH0_DOMAIN=reqops.au.auth0.com
#   export AUTH0_SPA_CLIENT_ID=kP5WPBHJmk97JQEYOtN2ToMsoMC8dP90
#   export AUTH0_MGMT_CLIENT_ID=...
#   export AUTH0_MGMT_CLIENT_SECRET=...
#   export PUBLIC_ORIGIN=http://170.64.224.128
#   ./deploy/configure-auth0-app.sh
set -euo pipefail

: "${AUTH0_DOMAIN:?}"
: "${AUTH0_SPA_CLIENT_ID:?}"
: "${AUTH0_MGMT_CLIENT_ID:?}"
: "${AUTH0_MGMT_CLIENT_SECRET:?}"
: "${PUBLIC_ORIGIN:?}"

TOKEN=$(curl -sf -X POST "https://${AUTH0_DOMAIN}/oauth/token" \
  -H 'content-type: application/json' \
  -d "$(jq -n \
    --arg cid "$AUTH0_MGMT_CLIENT_ID" \
    --arg secret "$AUTH0_MGMT_CLIENT_SECRET" \
    --arg aud "https://${AUTH0_DOMAIN}/api/v2/" \
    '{client_id:$cid,client_secret:$secret,audience:$aud,grant_type:"client_credentials"}')" \
  | jq -r '.access_token')

[[ -n "$TOKEN" && "$TOKEN" != "null" ]] || { echo "Failed to get Management API token" >&2; exit 1; }

APP=$(curl -sf "https://${AUTH0_DOMAIN}/api/v2/clients/${AUTH0_SPA_CLIENT_ID}" \
  -H "Authorization: Bearer ${TOKEN}")

merge_csv() {
  local existing="$1"
  local add="$2"
  python3 - <<'PY' "$existing" "$add"
import sys
existing, add = sys.argv[1], sys.argv[2]
items = [x.strip() for x in existing.split(",") if x.strip()]
if add not in items:
    items.append(add)
print(",".join(items))
PY
}

callbacks=$(merge_csv "$(echo "$APP" | jq -r '.callbacks | join(",")')" "${PUBLIC_ORIGIN}")
logout=$(merge_csv "$(echo "$APP" | jq -r '.allowed_logout_urls | join(",")')" "${PUBLIC_ORIGIN}")
origins=$(merge_csv "$(echo "$APP" | jq -r '.web_origins | join(",")')" "${PUBLIC_ORIGIN}")
allowed=$(merge_csv "$(echo "$APP" | jq -r '.allowed_origins | join(",")')" "${PUBLIC_ORIGIN}")

curl -sf -X PATCH "https://${AUTH0_DOMAIN}/api/v2/clients/${AUTH0_SPA_CLIENT_ID}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H 'content-type: application/json' \
  -d "$(jq -n \
    --arg cb "$callbacks" \
    --arg lo "$logout" \
    --arg wo "$origins" \
    --arg ao "$allowed" \
    '{
      callbacks: ($cb | split(",") | map(select(length>0))),
      allowed_logout_urls: ($lo | split(",") | map(select(length>0))),
      web_origins: ($wo | split(",") | map(select(length>0))),
      allowed_origins: ($ao | split(",") | map(select(length>0))),
      grant_types: ["authorization_code","refresh_token","implicit"],
      oidc_conformant: true
    }')" >/dev/null

echo "Auth0 SPA ${AUTH0_SPA_CLIENT_ID} updated for ${PUBLIC_ORIGIN}"
