#!/usr/bin/env python3
"""20-turn scripted car-selling dialogue through uplift 3.0 test-rubric harness.

Turns 1–10 mirror run_10_turns.py.
Turns 11–20 continue the narrative (media, onboarding, fraud, ops) for stress-testing.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HARNESS = ROOT / "test-rubric.py"

TURNS_FIRST_10: list[str] = [
    "Car selling app",
    "Peer-to-peer marketplace connecting private car sellers with buyers — mobile-first, like classifieds for used cars.",
    "MVP: create a listing with photos, browse and search listings, contact the seller, arrange a meetup. No in-app payments in v1.",
    "Trust is critical: light seller verification, report listing, and safety guidance for in-person meetups.",
    "Price is manual negotiation only — no automated pricing, auctions, or instant offers in v1.",
    "Out of scope for v1: financing, shipping, professional inspections, and dealer fleet tools. Consumer P2P only.",
    "Success means a completed sale handoff (buyer marks sold) and sellers who relist or sell again within 30 days.",
    "Primary users: individuals selling one personal vehicle; buyers searching locally within about 50km.",
    "Biggest risk to avoid: scams and unsafe meetups — optimise for fraud prevention over user growth.",
    "After contact, buyers and sellers use in-app chat until the deal is done; sharing phone numbers is optional, not required.",
]

TURNS_11_TO_20: list[str] = [
    "Listings should support up to 12 photos and a single short walk-around video.",
    "Onboarding wants to be fast — ideally browse as guest, minimal friction before contacting a seller.",
    "The nightmare is fake listings with stolen photos — cloned ads from Marketplace. We’d rather slow publishing than ship that.",
    "For clones: publish only after image fingerprint + VIN-photo match when we have the data; otherwise cap new sellers at lower daily listing volume until verified.",
    "Dispute path: escalate to ops within 48 hours via in-app ticket; abusive users get progressively longer shadow bans.",
    "We’ll run a moderation queue staffed European business hours first — no 24/7 human coverage until we have traction.",
    "Biggest UX risk is sellers abandoning if we require too much proof upfront — willing to soften checks for sellers with verified phone + three sale completions.",
    "Meetups stay off-platform coordination after chat handoff — we publish meet-in-public guidance but no insured pickup program in v1.",
    "Instrumentation: funnel from contact request → chat replied within 24h → meetup flagged → buyer marks sold; alert if cloned-ad reports spike.",
    "If cloned ads spike in week two, fallback is pause new publishes from sellers under 90 days tenure until manual review clears the backlog.",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run car-selling benchmark turns")
    parser.add_argument(
        "--start-turn",
        type=int,
        default=1,
        metavar="N",
        help="1 = fresh session (--new); 11 = continue-only using turns 11–20 (needs active session)",
    )
    args = parser.parse_args()

    if args.start_turn == 1:
        messages = TURNS_FIRST_10 + TURNS_11_TO_20
        rel_turn_start = 1
    elif args.start_turn == 11:
        messages = TURNS_11_TO_20
        rel_turn_start = 11
    else:
        sys.exit("--start-turn must be 1 or 11")

    for i, msg in enumerate(messages):
        rel_turn = rel_turn_start + i
        flag = "--new" if (args.start_turn == 1 and i == 0) else "--continue"

        print(f"\n{'=' * 60}\nTURN {rel_turn}/20\n{'=' * 60}\n", flush=True)
        rc = subprocess.call([sys.executable, str(HARNESS), flag, msg], cwd=str(ROOT))
        if rc != 0:
            sys.exit(rc)
    done = (
        "20-turn car benchmark complete (--new)."
        if args.start_turn == 1
        else "10-turn continuation complete (--continue)."
    )
    print(f"\nDone — {done}", flush=True)


if __name__ == "__main__":
    main()
