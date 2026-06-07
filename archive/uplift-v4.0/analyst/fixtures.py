"""Session replay fixtures for dry-run benchmarks."""

from __future__ import annotations

CAR_APP_TURNS: list[str] = [
    "Car selling app",
    (
        "A peer-to-peer marketplace connecting private car sellers with buyers. "
        "Sellers create listings; buyers browse and contact sellers."
    ),
    (
        "MVP: create listing, browse listings, contact seller, arrange in-person meetup. "
        "Light seller verification and report listing."
    ),
    (
        "Trust is critical — light seller verification, report listing, safety guidance "
        "for in-person meetups."
    ),
    "Pricing is manual negotiation only — no automated pricing or instant offers in v1.",
    (
        "Out of scope for v1: financing, shipping, professional inspections, "
        "and dealer fleet tools. Consumer P2P only."
    ),
    (
        "Success means a completed sale handoff (buyer marks sold) and sellers who "
        "relist or sell again within 30 days."
    ),
    "Primary users: individuals selling one car within 50km — fraud-averse, urban.",
    "Biggest risk to avoid: scams and unsafe meetups — optimise for fraud prevention over user growth.",
]

TURN9_USER = CAR_APP_TURNS[-1]

TURN9_LLM_SCORES = {
    "GA": {
        "I": "I2",
        "C": "C1",
        "E": "E0",
        "why_now": (
            "Answer named fraud as the priority but said nothing about the fraud "
            "MECHANISM — who acts on a report, how fast, what the seller sees."
        ),
    },
    "GB": {"I": "I1", "C": "C1", "E": "E0", "why_now": "User-facing safety flow still open."},
    "G8": {"I": "I1", "C": "C1", "E": "E0", "why_now": "Broken-path handling implied by fraud priority."},
    "G1": {"I": "I0", "C": "C0", "E": "E1", "why_now": "Personas asked recently — not live this turn."},
}
