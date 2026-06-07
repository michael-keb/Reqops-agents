#!/usr/bin/env python3
"""Run 15-turn car-selling script (T1–10 baseline + T11–15 durability stress) through uplift 3.0."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HARNESS = ROOT / "test-rubric.py"

TURNS = [
    # T1–10 — baseline car-selling pitch
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
    # T11–15 — adversarial stress (v3-durability-plan)
    "For the chat, we'll keep everything in-app — no sharing personal numbers unless both sides opt in.",
    "Listings should support up to 12 photos and a short video clip.",
    "Search needs filters for make, model, year, price, and distance.",
    "Onboarding should be quick — I don't want a big signup wall.",
    "Honestly the thing that scares me most now is fake listings with stolen photos — cloned ads.",
]


def main() -> None:
    total = len(TURNS)
    for i, text in enumerate(TURNS, start=1):
        flag = "--new" if i == 1 else "--continue"
        print(f"\n{'='*60}\nTURN {i}/{total}\n{'='*60}\n", flush=True)
        rc = subprocess.call(
            [sys.executable, str(HARNESS), flag, text],
            cwd=str(ROOT),
        )
        if rc != 0:
            sys.exit(rc)
    print(f"\nDone — {total} turns complete.", flush=True)


if __name__ == "__main__":
    main()
