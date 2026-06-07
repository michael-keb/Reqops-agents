#!/usr/bin/env python3
"""RunMe-shot: run 10-turn car-selling script through uplift 2.0 harness."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HARNESS = ROOT / "test-rubric.py"

TURNS = [
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


def main() -> None:
    for i, text in enumerate(TURNS, start=1):
        flag = "--new" if i == 1 else "--continue"
        print(f"\n{'='*60}\nTURN {i}/10\n{'='*60}\n", flush=True)
        rc = subprocess.call(
            [sys.executable, str(HARNESS), flag, text],
            cwd=str(ROOT),
        )
        if rc != 0:
            sys.exit(rc)
    print("\nDone — 10 turns complete.", flush=True)


if __name__ == "__main__":
    main()
