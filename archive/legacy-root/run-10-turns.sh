#!/usr/bin/env bash
# Run N turns; bash/zsh safe (no array index 0 under zsh).
set -euo pipefail
cd "$(dirname "$0")"
PY=".venv/bin/python"

msgs=(
  "Car selling app"
  "Peer-to-peer marketplace connecting private car sellers with buyers — mobile-first, like classifieds for used cars."
  "MVP: create a listing with photos, browse and search listings, contact the seller, arrange a meetup. No in-app payments in v1."
  "Trust is critical: light seller verification, report listing, and safety guidance for in-person meetups."
  "Price is manual negotiation only — no automated pricing, auctions, or instant offers in v1."
  "Out of scope for v1: financing, shipping, professional inspections, and dealer fleet tools. Consumer P2P only."
  "Success means a completed sale handoff (buyer marks sold) and sellers who relist or sell again within 30 days."
  "Primary users: individuals selling one personal vehicle; buyers searching locally within about 50km."
  "Biggest risk to avoid: scams and unsafe meetups — optimise for fraud prevention over user growth."
  "After contact, buyers and sellers use in-app chat until the deal is done; sharing phone numbers is optional, not required."
)

$PY test-rubric.py --new "${msgs[@]:0:1}"
for ((i=1; i<${#msgs[@]}; i++)); do
  echo ""
  echo "========== TURN $((i+1)) / ${#msgs[@]} =========="
  $PY test-rubric.py --continue "${msgs[$i]}"
done
