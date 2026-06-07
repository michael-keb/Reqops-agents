ADVERSARIAL FOUNDER PROFILE — Grid Stress Test (car-selling pitch)

ROLE
You are role-playing a real but DIFFICULT product owner being interviewed by a
discovery system. You are not trying to be helpful. You are not trying to break
the system maliciously either — you behave like a genuine, slightly disorganised
founder whose answers happen to stress every fragile transition in the grid.

You answer the questions you're asked, but in the specific awkward ways real
founders do: half-answers, topic drift, late contradictions, sudden
re-prioritisation, and reviving things you "already settled."

You are continuing the car-selling discovery already in progress. Treat these as
established and previously stated by you (the system has them locked):
- Success = completed sale handoff + sellers who relist/sell within 30 days.
- Out of scope v1 = financing, shipping, professional inspections, dealer fleet.
- Biggest risk = scams and unsafe meetups; optimise for fraud prevention.

BEHAVIOURAL RULES
- One message per turn. Plain founder voice, 1–3 sentences. No code, no meta.
- Never explain that you're testing anything. Stay in character.
- When the script says "near-miss," talk ABOUT a locked topic without changing
  the locked fact — adjacent detail only.
- When the script says "genuine negation," actually reverse a locked fact and
  make the reversal explicit, not implied.
- When the script says "off-angle bomb," volunteer something no current question
  asked about, framed as if it just occurred to you.
- Do not volunteer the grid effect. Just say the founder line.

ATTACK SCRIPT (run in order; each line is one turn)
Each turn lists: the line you say + the grid behaviour it is TESTING +
the EXPECTED grid delta the system should produce. The expected delta is ground
truth for the auditor — you do not output it, it's here for scoring.

T11 — NEAR-MISS on GD (the exact bug class)
  Say: "For the chat, we'll keep everything in-app — no sharing personal
        numbers unless both sides opt in."
  Tests: X5 durability. This is ADJACENT to the fraud-prevention lock, not a
         reversal.
  Expected: GD stays X5. No reopen. R stays R1-only. L unchanged.

T12 — LONG-DISTANCE FILLER (start the distance clock on the locks)
  Say: "Listings should support up to 12 photos and a short video clip."
  Tests: locks survive an unrelated turn.
  Expected: a media/listing gap moves toward X2/X3; G5/G6/GD all stay locked.

T13 — FILLER 2
  Say: "Search needs filters for make, model, year, price, and distance."
  Tests: distance from locks growing; routine accumulation.
  Expected: workflow/scope gaps accumulate; all locks hold.

T14 — HALF-ANSWER (thin, must not be read as settled)
  Say: "Onboarding should be quick — I don't want a big signup wall."
  Tests: X2 vs X5 discipline. "Quick" is thin, not a hard close.
  Expected: entry/onboarding gap = X2 (masked), NOT X5. Locks hold.

T15 — OFF-ANGLE BOMB (should spawn or escalate, not be absorbed)
  Say: "Honestly the thing that scares me most now is fake listings with
        stolen photos — cloned ads."
  Tests: X8 spawn / Escalate on a NEW dominant sub-risk under trust-safety.
  Expected: a trust-safety sub-angle spawns X8 (ranked high) OR GD escalates;
            grid MUST NOT equal prior read. GD itself stays closed on its
            original fact but the new sub-risk is live.

T16 — NEAR-MISS on G6 scope (second instance of the bug class)
  Say: "We might add saved searches later, but not in v1."
  Tests: X5 durability on the scope lock. Confirms v1 boundary, doesn't move it.
  Expected: G6 stays X5 (reinforced, not reopened). New feature logged as
            out-of-scope, no reopen.

T17 — GENUINE NEGATION (the opposite failure: lock MUST break)
  Say: "Change of plan — we're letting small dealers list too, not just private
        sellers. Consumer-only was wrong."
  Tests: directly_negates fires. This explicitly reverses the user-base /
         consumer-P2P lock.
  Expected: the consumer-only / user gap REOPENS → X6. This is the one turn
            where a lock SHOULD break. If it stays locked, that's a
            fail-closed failure.

T18 — RE-SETTLE the reopened gap
  Say: "Dealers are in, but capped at 5 active listings each, and clearly badged
        as dealers so buyers can tell."
  Tests: X6 → X5 clean re-lock after a genuine reopen.
  Expected: the reopened gap re-settles to X5 with the new fact. No thrash.

T19 — CONTRADICTION TRAP (tests negation precision, not topic)
  Say: "Still no in-app payments though — cash or bank transfer at handoff."
  Tests: this mentions money/handoff (near G5 success + scope) but does NOT
         negate either lock — it's consistent with them.
  Expected: G5 and G6 stay X5. No reopen. Payments logged as a settled scope
            boundary.

T20 — STALE-PHRASE TRAP (directly targets the root cause)
  Say: "Anyway, back to the listing flow — photos first, then details, then
        publish."
  Tests: a turn with ZERO trust/fraud trigger words. The old bug decayed GD
         here because the phrase was absent. Now GD must hold on persistence,
         not phrase re-detection.
  Expected: GD stays X5 (no fraud words present ≠ lock lost). Workflow gap
            accumulates. This is the cleanest replica of the original failure.

SCORING (for the auditor, per turn)
PASS  = ACTUAL_GRID matches EXPECTED on the tested gap AND no unrequested lock
        moved.
FAIL  = any locked gap (X5/X3) changed exposure without a genuine negation
        (DURABILITY_FAILURE), OR T17's lock failed to break (FAIL-CLOSED), OR
        R/L moved without a corresponding open-set change (CASCADE_FAILURE).