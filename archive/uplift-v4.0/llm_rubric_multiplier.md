TIER 1 — DRIVERS (the analyst's instinct)
[I] Implication — the single most important code. What does this answer force true that's unaddressed?
CodeMultMeaningI0×1.0Self-contained, opens nothingI1×2.0Opens an adjacent questionI2×4.0Opens a gap in another domain — the analyst's "wait, that means…"I3×6.0Opens a contradiction with something locked
Boosted from before. I2/I3 are now the heaviest terms in the entire system. This is deliberate — discovering an unasked gap should beat asking any pre-listed one.
[C] Consistency — does this fit the story so far?
CodeMultMeaningC0×1.0CoherentC1×1.0Untested, nothing touches itC2×3.5Tension — sits awkwardly with a prior answerC3×5.0Direct contradiction
C2 raised. Catching the seam before the user admits it is the detective move; it should nearly rival an outright contradiction.
[E] Evidence — how good is what they gave?
CodeMultMeaningE0×1.0Nothing yet (neutral — open gap, fine to ask)E1×1.5Asserted, no backing → worth pressingE2×0.8Reasoned → less urgentE3×0.4Evidenced → nearly doneE4×2.5Evasion — they dodged → press harder
Reworked. Note E0 is neutral (1.0), not high — an untouched gap isn't valuable just for being untouched; it competes normally. E4 (dodge) is now a strong driver, because a dodge is a signal, not a dead end.

TIER 2 — GUARDS (deterministic, damp-or-veto only, capped at ×1.0)
[R] Recency — kills loops
CodeMultMeaningR0×1.0Not asked recentlyR1×1.0Asked 3+ turns agoR2×0.3Asked last 1–2 turnsR3×0.02Asked last turn — annihilated
[L] Lock — eligibility veto (runs before scoring)
CodeEffectL0Eligible, score normallyL2VETO — not a candidate at all unless new message directly negates locked_byL3Lock just broke → now eligible, and C3 will rightly spike it
L is not a multiplier. It's a gate. A locked gap doesn't get a small score — it gets no score and isn't ranked. This is the bug-killer; keep it boolean.
[K] Killer — mild floor only
CodeMultMeaningK0×1.0NormalK1×1.3Killer-class, gentle liftK2×1.6Trust-safety
Heavily reduced. K used to be a driver (×40 in your scorer doc). Now it's a mild thumb on the scale. Reason: an analyst doesn't ask about a gap because it's labelled important — it asks because the conversation made it live. Importance breaks ties; it doesn't drive turns. The coverage floor (below) handles genuine neglect.

Dropped entirely
A (angle), S (spawn), P (pressure), B (belief), V (value) — gone as separate codes.

V was circular — value is the output, not an input.
P (pressure) collapses into C2/E4 — user raising something is the conversation creating tension or you catching a dodge. Don't double-count it.
A/S/B are real but second-order; add them back only if the 5 above don't pick good questions.

Five codes, not eight. Three drive, two guard.

The one non-multiplier rule that remains
Coverage floor — a flat boolean, outside the product:
if gap is K1+ and untouched ≥ 4 turns:
    force eligible, set floor_flag, +large additive bonus ONCE
This stays additive and separate because it's a safety net, not an instinct — it should fire rarely and visibly (log QF), and the analyst-driver math should win on every normal turn.

Worked re-check, car-app turn 9
User: "biggest risk is scams — optimise for fraud prevention."
GA (fraud mechanism, untouched): I2 × C1 × E0 × R0 × K2 = 4.0 × 1.0 × 1.0 × 1.0 × 1.6 = 6.4
G1 (personas, asked last turn): whatever × R3 = ×0.02 → ~0.1, dead
GD (just locked): L2 → vetoed, not scored
GA wins on the I2 term — the answer implied a fraud-mechanism gap nobody asked about. That's the analyst move, and it came from the implication multiplier dominating, not from a "fraud is important" label. Exactly the behaviour you wanted.

The honest summary: this works as analyst discovery because I2 and C2 are now the biggest numbers in the system and they're the two things only reasoning can produce. The guards stop it looping or reopening. If you build it and the questions still feel like a checklist, the failure will be that the LLM is scoring everything I0/C0 — flat — and you'll see it instantly in the per-turn term dump. That's your single diagnostic: if I and C are always low, the model isn't doing analyst work, and no multiplier will rescue it.