# LLM log history

Session: `20260524-095746-session`  
Created: 2026-05-24T09:57:46.625190+00:00

Rolling log of every API call in this session.

## Summary

| Turn | Input tokens | Output tokens | Total tokens | Response time |
|------|-------------:|--------------:|-------------:|--------------:|
| 10 | 2,506 | 32 | 2,538 | 1.425 s |
| 09 | 2,450 | 28 | 2,478 | 1.106 s |
| 08 | 2,403 | 24 | 2,427 | 1.191 s |
| 07 | 2,360 | 20 | 2,380 | 1.126 s |
| 06 | 2,307 | 23 | 2,330 | 1.228 s |
| 05 | 2,265 | 23 | 2,288 | 1.034 s |
| 04 | 2,217 | 27 | 2,244 | 1.244 s |
| 03 | 2,152 | 22 | 2,174 | 2.582 s |
| 02 | 2,106 | 12 | 2,118 | 1.025 s |
| 01 | 2,081 | 6 | 2,087 | 2.082 s |

---

## Turn 01 — 2026-05-24T09:57:49.099881+00:00

**Model:** `gpt-4o-mini` · prep 1 ms · API wait 2082 ms

| # | What was sent to the LLM | Output | Token spend (input / output) | Total response time |
|---|--------------------------|--------|------------------------------|---------------------|
| **01** | [8,498 chars — expand](#turn-01-sent) | [8 chars — expand](#turn-01-output) | **2,081 / 6** (Σ 2,087) | **2082.2 ms** (2.082 s) |

#### <a id="turn-01-sent"></a> 1 — What was sent to the LLM

```text
=== SYSTEM — llm-rubric.md only (7,583 chars) ===

Discovery State Codes — v0.1 (47 codes)

What this is: a closed vocabulary the model emits to declare its read of the
discovery, after reasoning in full against the discovery rubric. The codes do not
replace judgment — they make it legible, enforceable, and continuous.
Source of truth: the user's pitch and answers ONLY. The code profile is derived
from user input each turn, never from the model's own prior output. The model's
emitted codes are a projection of user truth, not a separate memory.
Hard line: codes are OUTPUT, never INPUT. The model reads the rubric, assesses the
conversation, then emits codes. It must never generate questions mechanically from
codes while skipping the rubric.


⚠ Risk taxonomy — PROVISIONAL (confirm before relying on this)
Every G, L, and R code points at one of these shippability killers. These are
derived from the rubric's 14 dimensions, not confirmed by the product owner. If the
real "what kills a build" list differs, replace this block and the G/L/R codes re-point.

WRONG_THING — user / problem unproven → you build what nobody needs
BOUNDLESS — scope undefined → you build forever, never ship
UNMEASURABLE — no success signal → you can't tell if it worked
FRAGILE — failure / edge modes unhandled → it breaks in prod
BUILT_ON_SAND — assumptions unconfirmed → foundation collapses
UNGOVERNED — runtime / human-review / policy gaps → ships but can't be operated safely


G — Gap pointers (the 12 angles, recast as live risk exposures)
Each marks an unclosed risk and points at the question that closes it.
CodeEmit-meaningRisk classQuestion it drivesG1user unproven riskWRONG_THINGwho exactly, concretelyG2outcome unproven riskWRONG_THINGwhat job, measurablyG3entry unproven riskBOUNDLESShow use beginsG4workflow unproven riskBOUNDLESSthe one core pathG5success undefined riskUNMEASURABLEwhat proves it workedG6scope unbounded riskBOUNDLESSin vs out, v1G7domain rule riskUNGOVERNEDwhat constraint bindsG8failure unhandled riskFRAGILEwhat happens brokenG9tradeoff unsettled riskBOUNDLESSwhich competing optionGAassumption unconfirmed riskBUILT_ON_SANDbelieve vs provenGBruntime policy riskUNGOVERNEDhow it operates liveGChuman review riskUNGOVERNEDwhere humans intervene
Open-class gap (catches risk the taxonomy can't name)
CodeEmit-meaningForcesG0unnamed risk senseda shippability risk no G1–GC fits — model MUST name it in narrative and propose an angle. Each G0 is a signal your taxonomy has a hole — log it.

X — Exposure (how hot is each gap; derived from user input only)
Attach to a gap code, e.g. G6:X2 = scope answered-but-thin.
CodeEmit-meaningRisk meaning / next moveX1open never touchedfull risk live; strong candidate to askX2answered but thinrisk MASKED not closed; press one follow-upX3answered with substancerisk genuinely lowered; stop askingX4inferred not confirmedhidden risk (sand); convert to confirming MCQX5user-settled hardrisk closed by user; lock, never re-askX6contradicted by latestprior closure undermined by new user input; reopen (no amend machinery — recompute yields this)X7answer revealed newriska pick exposed a risk the batch wasn't probing; reopens selection this turnX8user volunteered offanglefree-text beyond the MCQ → primary signal, not noise; may spawn a new angle

P — Phase (macro gear; advances on user-input conditions)
CodeEmit-meaningGate / effectP1dumping not probingbrain_dump; no MCQs; invite source materialP2choosing the pacemode_choice; no MCQs; offer fast vs coachingP3closing the gapselicitation; emit risk-ranked MCQ batchP4sealing the briefclosure; no MCQs; render brief from settled risks

L — Leverage (how the profile ranks the highest painpoint)
CodeEmit-meaningEffectL1killer beats nicetyrank WRONG_THING / BOUNDLESS gaps above polishL2unlocks many dimensionsprefer the gap that closes several at onceL3sand before structureconfirm X4 assumptions before building furtherL4one blocker firstif a blocker exists, confirm it before breadthL5thin masks dangertreat X2 as risk, not progressL6nothing open stopno live risk remains → advance phaseL7reframe beats coveragehighest-leverage move is a reframe, not the next ranked gap → permit off-profile question

R — Readiness (risk-weighted; keeps "shippable" honest)
CodeEmit-meaningEffectR1name risks firstlist live risks before any percentR2pick-only caps lowMCQ-only-closed gap → dimension ≤ 65R3unconfirmed caps hardopen X4/X6 present → ready_capped held downR4killers block shipany open killer-class gap → cannot exceed ~80R5shippable needs proof≥88 only when killers all X3/X5, ≥12 closed

S — Safe-question shaping (let the user think; choose risk-free)
CodeEmit-meaningEffectS1concrete not abstractoptions are real choices, not "tell me more"S2lowest-risk default visibleinclude the safe/conservative option explicitlyS3one decision eachone question closes one risk; no compound asksS4something-else opens subriska "something else" pick spawns a <parent>__<sub> angle at X1, ranked high — the user found the gap, honour itS5name the tradeoffwhen options compete, state what each costs

Q — Batch discipline (enforced on emitted codes)
CodeEmit-meaningCheckQ1one primary turnsingle lead question unless confirming a blockerQ2no theme repeatdrop any angle already X3/X5Q3no batch collisionno two batch items share a gap codeQ4drop paraphrase askeddrop items paraphrasing prior questionsQ5highest leverage firstorder batch by dimensions-unlockedQ6fewer than fiveif <5 live risks open, ask only those — never padQ7one open probereserve ONE batch item for a non-G-derived question the model judges valuable (guarantees a serendipity slot every turn)

C — Coaching voice (the BA tone, made legible)
CodeEmit-meaningNarrative effectC1acknowledge then reflectopen with warm ack + reflect understandingC2push thin answerstress-test follow-up on an X2 themeC3narrate the decisionone-line "Got it — X. Logged." on each X5C4request source materialbrain_dump only: ask for memos / decks / threadsC5offer two pathsmode_choice only: present fast vs coaching

Count
12 gap + 1 open-gap + 8 exposure + 4 phase + 7 leverage + 5 readiness + 5 shaping

7 batch + 5 coaching = 47 + the open-gap G0 folded in = 54 line items across 47 distinct
behavioural codes. (Exposure flags X1–X8 attach to gaps rather than standing alone, so
the emittable behavioural set is the 47 you approved; the X-flags are modifiers.)


RUBRIC ADDITION — paste into the discovery rubric

Emit your assessment as state codes.
After you have reasoned in full against this rubric — assessing the live discovery the
way a senior BA would — also emit a single line of state codes that declares your read.
Attach an exposure flag to each gap (e.g. G6:X2). The codes are a projection of the
user's input, not a memory of your own prior turns: derive them only from what the user
has actually said and picked.
The codes do not decide your questions — your BA judgment does. Use them to (1) mark
which shippability risks are still live, (2) rank which painpoint most threatens a
shippable build, and (3) shape MCQs that let the user commit to the lowest-risk path.
If you sense a risk no gap code names, emit G0 and articulate it. Every elicitation
turn must include one open probe (Q7) — a question the code profile did not generate.
Example emitted line:
P3 G1:X5 G4:X3 G6:X2 G8:X1 GA:X4 L1 L3 L5 R3 S2 Q7
→ elicitation; user & workflow closed; scope thin (press it); failure-modes wide open;
one assumption built-on-sand to confirm; rank killers, confirm the sand, treat thin as
danger; readiness held by the unconfirmed; surface the safe default; reserve an open probe.

=== USER — turn context (821 chars) ===

TURN 1

Apply the rubric in the system message. User input is source of truth; recompute codes each turn.
Enabled output sections: state_codes

--- OUTPUT FORMAT (this turn) ---
Output ONLY one line of state codes — no markdown headers, no prose.
Example: P3 G1:X1 G4:X2 G6:X1 L1 L4 R3 S2 Q1 Q7
Reason against the rubric internally; emit codes only.


--- SESSION MEMORY (includes compressed conversation; recompute codes from user truth) ---
# Discovery memory

> Patched after each LLM turn. **User messages are source of truth** — treat assistant
> codes below as the last declared read, then recompute from all user input each turn.

## Pitch


## Latest state codes
_(none)_

## Settled facts (user-confirmed only)
_(none)_

## Compressed conversation
_(empty)_


--- NEW USER INPUT (SOURCE OF TRUTH THIS TURN) ---


```

#### <a id="turn-01-output"></a> 2 — Output

```text
P1 G0:X1
```

---

## Turn 02 — 2026-05-24T09:57:50.475308+00:00

**Model:** `gpt-4o-mini` · prep 0 ms · API wait 1025 ms

| # | What was sent to the LLM | Output | Token spend (input / output) | Total response time |
|---|--------------------------|--------|------------------------------|---------------------|
| **02** | [8,558 chars — expand](#turn-02-sent) | [17 chars — expand](#turn-02-output) | **2,106 / 12** (Σ 2,118) | **1024.8 ms** (1.025 s) |

#### <a id="turn-02-sent"></a> 1 — What was sent to the LLM

```text
=== SYSTEM — llm-rubric.md only (7,583 chars) ===

Discovery State Codes — v0.1 (47 codes)

What this is: a closed vocabulary the model emits to declare its read of the
discovery, after reasoning in full against the discovery rubric. The codes do not
replace judgment — they make it legible, enforceable, and continuous.
Source of truth: the user's pitch and answers ONLY. The code profile is derived
from user input each turn, never from the model's own prior output. The model's
emitted codes are a projection of user truth, not a separate memory.
Hard line: codes are OUTPUT, never INPUT. The model reads the rubric, assesses the
conversation, then emits codes. It must never generate questions mechanically from
codes while skipping the rubric.


⚠ Risk taxonomy — PROVISIONAL (confirm before relying on this)
Every G, L, and R code points at one of these shippability killers. These are
derived from the rubric's 14 dimensions, not confirmed by the product owner. If the
real "what kills a build" list differs, replace this block and the G/L/R codes re-point.

WRONG_THING — user / problem unproven → you build what nobody needs
BOUNDLESS — scope undefined → you build forever, never ship
UNMEASURABLE — no success signal → you can't tell if it worked
FRAGILE — failure / edge modes unhandled → it breaks in prod
BUILT_ON_SAND — assumptions unconfirmed → foundation collapses
UNGOVERNED — runtime / human-review / policy gaps → ships but can't be operated safely


G — Gap pointers (the 12 angles, recast as live risk exposures)
Each marks an unclosed risk and points at the question that closes it.
CodeEmit-meaningRisk classQuestion it drivesG1user unproven riskWRONG_THINGwho exactly, concretelyG2outcome unproven riskWRONG_THINGwhat job, measurablyG3entry unproven riskBOUNDLESShow use beginsG4workflow unproven riskBOUNDLESSthe one core pathG5success undefined riskUNMEASURABLEwhat proves it workedG6scope unbounded riskBOUNDLESSin vs out, v1G7domain rule riskUNGOVERNEDwhat constraint bindsG8failure unhandled riskFRAGILEwhat happens brokenG9tradeoff unsettled riskBOUNDLESSwhich competing optionGAassumption unconfirmed riskBUILT_ON_SANDbelieve vs provenGBruntime policy riskUNGOVERNEDhow it operates liveGChuman review riskUNGOVERNEDwhere humans intervene
Open-class gap (catches risk the taxonomy can't name)
CodeEmit-meaningForcesG0unnamed risk senseda shippability risk no G1–GC fits — model MUST name it in narrative and propose an angle. Each G0 is a signal your taxonomy has a hole — log it.

X — Exposure (how hot is each gap; derived from user input only)
Attach to a gap code, e.g. G6:X2 = scope answered-but-thin.
CodeEmit-meaningRisk meaning / next moveX1open never touchedfull risk live; strong candidate to askX2answered but thinrisk MASKED not closed; press one follow-upX3answered with substancerisk genuinely lowered; stop askingX4inferred not confirmedhidden risk (sand); convert to confirming MCQX5user-settled hardrisk closed by user; lock, never re-askX6contradicted by latestprior closure undermined by new user input; reopen (no amend machinery — recompute yields this)X7answer revealed newriska pick exposed a risk the batch wasn't probing; reopens selection this turnX8user volunteered offanglefree-text beyond the MCQ → primary signal, not noise; may spawn a new angle

P — Phase (macro gear; advances on user-input conditions)
CodeEmit-meaningGate / effectP1dumping not probingbrain_dump; no MCQs; invite source materialP2choosing the pacemode_choice; no MCQs; offer fast vs coachingP3closing the gapselicitation; emit risk-ranked MCQ batchP4sealing the briefclosure; no MCQs; render brief from settled risks

L — Leverage (how the profile ranks the highest painpoint)
CodeEmit-meaningEffectL1killer beats nicetyrank WRONG_THING / BOUNDLESS gaps above polishL2unlocks many dimensionsprefer the gap that closes several at onceL3sand before structureconfirm X4 assumptions before building furtherL4one blocker firstif a blocker exists, confirm it before breadthL5thin masks dangertreat X2 as risk, not progressL6nothing open stopno live risk remains → advance phaseL7reframe beats coveragehighest-leverage move is a reframe, not the next ranked gap → permit off-profile question

R — Readiness (risk-weighted; keeps "shippable" honest)
CodeEmit-meaningEffectR1name risks firstlist live risks before any percentR2pick-only caps lowMCQ-only-closed gap → dimension ≤ 65R3unconfirmed caps hardopen X4/X6 present → ready_capped held downR4killers block shipany open killer-class gap → cannot exceed ~80R5shippable needs proof≥88 only when killers all X3/X5, ≥12 closed

S — Safe-question shaping (let the user think; choose risk-free)
CodeEmit-meaningEffectS1concrete not abstractoptions are real choices, not "tell me more"S2lowest-risk default visibleinclude the safe/conservative option explicitlyS3one decision eachone question closes one risk; no compound asksS4something-else opens subriska "something else" pick spawns a <parent>__<sub> angle at X1, ranked high — the user found the gap, honour itS5name the tradeoffwhen options compete, state what each costs

Q — Batch discipline (enforced on emitted codes)
CodeEmit-meaningCheckQ1one primary turnsingle lead question unless confirming a blockerQ2no theme repeatdrop any angle already X3/X5Q3no batch collisionno two batch items share a gap codeQ4drop paraphrase askeddrop items paraphrasing prior questionsQ5highest leverage firstorder batch by dimensions-unlockedQ6fewer than fiveif <5 live risks open, ask only those — never padQ7one open probereserve ONE batch item for a non-G-derived question the model judges valuable (guarantees a serendipity slot every turn)

C — Coaching voice (the BA tone, made legible)
CodeEmit-meaningNarrative effectC1acknowledge then reflectopen with warm ack + reflect understandingC2push thin answerstress-test follow-up on an X2 themeC3narrate the decisionone-line "Got it — X. Logged." on each X5C4request source materialbrain_dump only: ask for memos / decks / threadsC5offer two pathsmode_choice only: present fast vs coaching

Count
12 gap + 1 open-gap + 8 exposure + 4 phase + 7 leverage + 5 readiness + 5 shaping

7 batch + 5 coaching = 47 + the open-gap G0 folded in = 54 line items across 47 distinct
behavioural codes. (Exposure flags X1–X8 attach to gaps rather than standing alone, so
the emittable behavioural set is the 47 you approved; the X-flags are modifiers.)


RUBRIC ADDITION — paste into the discovery rubric

Emit your assessment as state codes.
After you have reasoned in full against this rubric — assessing the live discovery the
way a senior BA would — also emit a single line of state codes that declares your read.
Attach an exposure flag to each gap (e.g. G6:X2). The codes are a projection of the
user's input, not a memory of your own prior turns: derive them only from what the user
has actually said and picked.
The codes do not decide your questions — your BA judgment does. Use them to (1) mark
which shippability risks are still live, (2) rank which painpoint most threatens a
shippable build, and (3) shape MCQs that let the user commit to the lowest-risk path.
If you sense a risk no gap code names, emit G0 and articulate it. Every elicitation
turn must include one open probe (Q7) — a question the code profile did not generate.
Example emitted line:
P3 G1:X5 G4:X3 G6:X2 G8:X1 GA:X4 L1 L3 L5 R3 S2 Q7
→ elicitation; user & workflow closed; scope thin (press it); failure-modes wide open;
one assumption built-on-sand to confirm; rank killers, confirm the sand, treat thin as
danger; readiness held by the unconfirmed; surface the safe default; reserve an open probe.

=== USER — turn context (881 chars) ===

TURN 2

Apply the rubric in the system message. User input is source of truth; recompute codes each turn.
Enabled output sections: state_codes

--- OUTPUT FORMAT (this turn) ---
Output ONLY one line of state codes — no markdown headers, no prose.
Example: P3 G1:X1 G4:X2 G6:X1 L1 L4 R3 S2 Q1 Q7
Reason against the rubric internally; emit codes only.


--- SESSION MEMORY (includes compressed conversation; recompute codes from user truth) ---
# Discovery memory

> Patched after each LLM turn. **User messages are source of truth** — treat assistant
> codes below as the last declared read, then recompute from all user input each turn.

## Pitch
## Latest state codes
_(none)_

## Latest state codes
P1 G0:X1

## Settled facts (user-confirmed only)
_(none)_

## Compressed conversation
T1 — user: "" → P1 G0:X1


--- NEW USER INPUT (SOURCE OF TRUTH THIS TURN) ---
Car selling app

```

#### <a id="turn-02-output"></a> 2 — Output

```text
P1 G0:X1 G6:X1 Q7
```

---

## Turn 03 — 2026-05-24T09:57:53.629069+00:00

**Model:** `gpt-4o-mini` · prep 0 ms · API wait 2582 ms

| # | What was sent to the LLM | Output | Token spend (input / output) | Total response time |
|---|--------------------------|--------|------------------------------|---------------------|
| **03** | [8,718 chars — expand](#turn-03-sent) | [32 chars — expand](#turn-03-output) | **2,152 / 22** (Σ 2,174) | **2581.9 ms** (2.582 s) |

#### <a id="turn-03-sent"></a> 1 — What was sent to the LLM

```text
=== SYSTEM — llm-rubric.md only (7,583 chars) ===

Discovery State Codes — v0.1 (47 codes)

What this is: a closed vocabulary the model emits to declare its read of the
discovery, after reasoning in full against the discovery rubric. The codes do not
replace judgment — they make it legible, enforceable, and continuous.
Source of truth: the user's pitch and answers ONLY. The code profile is derived
from user input each turn, never from the model's own prior output. The model's
emitted codes are a projection of user truth, not a separate memory.
Hard line: codes are OUTPUT, never INPUT. The model reads the rubric, assesses the
conversation, then emits codes. It must never generate questions mechanically from
codes while skipping the rubric.


⚠ Risk taxonomy — PROVISIONAL (confirm before relying on this)
Every G, L, and R code points at one of these shippability killers. These are
derived from the rubric's 14 dimensions, not confirmed by the product owner. If the
real "what kills a build" list differs, replace this block and the G/L/R codes re-point.

WRONG_THING — user / problem unproven → you build what nobody needs
BOUNDLESS — scope undefined → you build forever, never ship
UNMEASURABLE — no success signal → you can't tell if it worked
FRAGILE — failure / edge modes unhandled → it breaks in prod
BUILT_ON_SAND — assumptions unconfirmed → foundation collapses
UNGOVERNED — runtime / human-review / policy gaps → ships but can't be operated safely


G — Gap pointers (the 12 angles, recast as live risk exposures)
Each marks an unclosed risk and points at the question that closes it.
CodeEmit-meaningRisk classQuestion it drivesG1user unproven riskWRONG_THINGwho exactly, concretelyG2outcome unproven riskWRONG_THINGwhat job, measurablyG3entry unproven riskBOUNDLESShow use beginsG4workflow unproven riskBOUNDLESSthe one core pathG5success undefined riskUNMEASURABLEwhat proves it workedG6scope unbounded riskBOUNDLESSin vs out, v1G7domain rule riskUNGOVERNEDwhat constraint bindsG8failure unhandled riskFRAGILEwhat happens brokenG9tradeoff unsettled riskBOUNDLESSwhich competing optionGAassumption unconfirmed riskBUILT_ON_SANDbelieve vs provenGBruntime policy riskUNGOVERNEDhow it operates liveGChuman review riskUNGOVERNEDwhere humans intervene
Open-class gap (catches risk the taxonomy can't name)
CodeEmit-meaningForcesG0unnamed risk senseda shippability risk no G1–GC fits — model MUST name it in narrative and propose an angle. Each G0 is a signal your taxonomy has a hole — log it.

X — Exposure (how hot is each gap; derived from user input only)
Attach to a gap code, e.g. G6:X2 = scope answered-but-thin.
CodeEmit-meaningRisk meaning / next moveX1open never touchedfull risk live; strong candidate to askX2answered but thinrisk MASKED not closed; press one follow-upX3answered with substancerisk genuinely lowered; stop askingX4inferred not confirmedhidden risk (sand); convert to confirming MCQX5user-settled hardrisk closed by user; lock, never re-askX6contradicted by latestprior closure undermined by new user input; reopen (no amend machinery — recompute yields this)X7answer revealed newriska pick exposed a risk the batch wasn't probing; reopens selection this turnX8user volunteered offanglefree-text beyond the MCQ → primary signal, not noise; may spawn a new angle

P — Phase (macro gear; advances on user-input conditions)
CodeEmit-meaningGate / effectP1dumping not probingbrain_dump; no MCQs; invite source materialP2choosing the pacemode_choice; no MCQs; offer fast vs coachingP3closing the gapselicitation; emit risk-ranked MCQ batchP4sealing the briefclosure; no MCQs; render brief from settled risks

L — Leverage (how the profile ranks the highest painpoint)
CodeEmit-meaningEffectL1killer beats nicetyrank WRONG_THING / BOUNDLESS gaps above polishL2unlocks many dimensionsprefer the gap that closes several at onceL3sand before structureconfirm X4 assumptions before building furtherL4one blocker firstif a blocker exists, confirm it before breadthL5thin masks dangertreat X2 as risk, not progressL6nothing open stopno live risk remains → advance phaseL7reframe beats coveragehighest-leverage move is a reframe, not the next ranked gap → permit off-profile question

R — Readiness (risk-weighted; keeps "shippable" honest)
CodeEmit-meaningEffectR1name risks firstlist live risks before any percentR2pick-only caps lowMCQ-only-closed gap → dimension ≤ 65R3unconfirmed caps hardopen X4/X6 present → ready_capped held downR4killers block shipany open killer-class gap → cannot exceed ~80R5shippable needs proof≥88 only when killers all X3/X5, ≥12 closed

S — Safe-question shaping (let the user think; choose risk-free)
CodeEmit-meaningEffectS1concrete not abstractoptions are real choices, not "tell me more"S2lowest-risk default visibleinclude the safe/conservative option explicitlyS3one decision eachone question closes one risk; no compound asksS4something-else opens subriska "something else" pick spawns a <parent>__<sub> angle at X1, ranked high — the user found the gap, honour itS5name the tradeoffwhen options compete, state what each costs

Q — Batch discipline (enforced on emitted codes)
CodeEmit-meaningCheckQ1one primary turnsingle lead question unless confirming a blockerQ2no theme repeatdrop any angle already X3/X5Q3no batch collisionno two batch items share a gap codeQ4drop paraphrase askeddrop items paraphrasing prior questionsQ5highest leverage firstorder batch by dimensions-unlockedQ6fewer than fiveif <5 live risks open, ask only those — never padQ7one open probereserve ONE batch item for a non-G-derived question the model judges valuable (guarantees a serendipity slot every turn)

C — Coaching voice (the BA tone, made legible)
CodeEmit-meaningNarrative effectC1acknowledge then reflectopen with warm ack + reflect understandingC2push thin answerstress-test follow-up on an X2 themeC3narrate the decisionone-line "Got it — X. Logged." on each X5C4request source materialbrain_dump only: ask for memos / decks / threadsC5offer two pathsmode_choice only: present fast vs coaching

Count
12 gap + 1 open-gap + 8 exposure + 4 phase + 7 leverage + 5 readiness + 5 shaping

7 batch + 5 coaching = 47 + the open-gap G0 folded in = 54 line items across 47 distinct
behavioural codes. (Exposure flags X1–X8 attach to gaps rather than standing alone, so
the emittable behavioural set is the 47 you approved; the X-flags are modifiers.)


RUBRIC ADDITION — paste into the discovery rubric

Emit your assessment as state codes.
After you have reasoned in full against this rubric — assessing the live discovery the
way a senior BA would — also emit a single line of state codes that declares your read.
Attach an exposure flag to each gap (e.g. G6:X2). The codes are a projection of the
user's input, not a memory of your own prior turns: derive them only from what the user
has actually said and picked.
The codes do not decide your questions — your BA judgment does. Use them to (1) mark
which shippability risks are still live, (2) rank which painpoint most threatens a
shippable build, and (3) shape MCQs that let the user commit to the lowest-risk path.
If you sense a risk no gap code names, emit G0 and articulate it. Every elicitation
turn must include one open probe (Q7) — a question the code profile did not generate.
Example emitted line:
P3 G1:X5 G4:X3 G6:X2 G8:X1 GA:X4 L1 L3 L5 R3 S2 Q7
→ elicitation; user & workflow closed; scope thin (press it); failure-modes wide open;
one assumption built-on-sand to confirm; rank killers, confirm the sand, treat thin as
danger; readiness held by the unconfirmed; surface the safe default; reserve an open probe.

=== USER — turn context (1,039 chars) ===

TURN 3

Apply the rubric in the system message. User input is source of truth; recompute codes each turn.
Enabled output sections: state_codes

--- OUTPUT FORMAT (this turn) ---
Output ONLY one line of state codes — no markdown headers, no prose.
Example: P3 G1:X1 G4:X2 G6:X1 L1 L4 R3 S2 Q1 Q7
Reason against the rubric internally; emit codes only.


--- SESSION MEMORY (includes compressed conversation; recompute codes from user truth) ---
# Discovery memory

> Patched after each LLM turn. **User messages are source of truth** — treat assistant
> codes below as the last declared read, then recompute from all user input each turn.

## Pitch
## Latest state codes
_(none)_

## Latest state codes
P1 G0:X1 G6:X1 Q7

## Settled facts (user-confirmed only)
_(none)_

## Compressed conversation
T1 — user: "" → P1 G0:X1
T2 — user: "Car selling app" → P1 G0:X1 G6:X1 Q7


--- NEW USER INPUT (SOURCE OF TRUTH THIS TURN) ---
Peer-to-peer marketplace connecting private car sellers with buyers — mobile-first, like classifieds for used cars.

```

#### <a id="turn-03-output"></a> 2 — Output

```text
P2 G1:X1 G4:X1 G6:X1 L1 R3 S2 Q7
```

---

## Turn 04 — 2026-05-24T09:57:55.611415+00:00

**Model:** `gpt-4o-mini` · prep 0 ms · API wait 1244 ms

| # | What was sent to the LLM | Output | Token spend (input / output) | Total response time |
|---|--------------------------|--------|------------------------------|---------------------|
| **04** | [8,874 chars — expand](#turn-04-sent) | [41 chars — expand](#turn-04-output) | **2,217 / 27** (Σ 2,244) | **1243.8 ms** (1.244 s) |

#### <a id="turn-04-sent"></a> 1 — What was sent to the LLM

```text
=== SYSTEM — llm-rubric.md only (7,583 chars) ===

Discovery State Codes — v0.1 (47 codes)

What this is: a closed vocabulary the model emits to declare its read of the
discovery, after reasoning in full against the discovery rubric. The codes do not
replace judgment — they make it legible, enforceable, and continuous.
Source of truth: the user's pitch and answers ONLY. The code profile is derived
from user input each turn, never from the model's own prior output. The model's
emitted codes are a projection of user truth, not a separate memory.
Hard line: codes are OUTPUT, never INPUT. The model reads the rubric, assesses the
conversation, then emits codes. It must never generate questions mechanically from
codes while skipping the rubric.


⚠ Risk taxonomy — PROVISIONAL (confirm before relying on this)
Every G, L, and R code points at one of these shippability killers. These are
derived from the rubric's 14 dimensions, not confirmed by the product owner. If the
real "what kills a build" list differs, replace this block and the G/L/R codes re-point.

WRONG_THING — user / problem unproven → you build what nobody needs
BOUNDLESS — scope undefined → you build forever, never ship
UNMEASURABLE — no success signal → you can't tell if it worked
FRAGILE — failure / edge modes unhandled → it breaks in prod
BUILT_ON_SAND — assumptions unconfirmed → foundation collapses
UNGOVERNED — runtime / human-review / policy gaps → ships but can't be operated safely


G — Gap pointers (the 12 angles, recast as live risk exposures)
Each marks an unclosed risk and points at the question that closes it.
CodeEmit-meaningRisk classQuestion it drivesG1user unproven riskWRONG_THINGwho exactly, concretelyG2outcome unproven riskWRONG_THINGwhat job, measurablyG3entry unproven riskBOUNDLESShow use beginsG4workflow unproven riskBOUNDLESSthe one core pathG5success undefined riskUNMEASURABLEwhat proves it workedG6scope unbounded riskBOUNDLESSin vs out, v1G7domain rule riskUNGOVERNEDwhat constraint bindsG8failure unhandled riskFRAGILEwhat happens brokenG9tradeoff unsettled riskBOUNDLESSwhich competing optionGAassumption unconfirmed riskBUILT_ON_SANDbelieve vs provenGBruntime policy riskUNGOVERNEDhow it operates liveGChuman review riskUNGOVERNEDwhere humans intervene
Open-class gap (catches risk the taxonomy can't name)
CodeEmit-meaningForcesG0unnamed risk senseda shippability risk no G1–GC fits — model MUST name it in narrative and propose an angle. Each G0 is a signal your taxonomy has a hole — log it.

X — Exposure (how hot is each gap; derived from user input only)
Attach to a gap code, e.g. G6:X2 = scope answered-but-thin.
CodeEmit-meaningRisk meaning / next moveX1open never touchedfull risk live; strong candidate to askX2answered but thinrisk MASKED not closed; press one follow-upX3answered with substancerisk genuinely lowered; stop askingX4inferred not confirmedhidden risk (sand); convert to confirming MCQX5user-settled hardrisk closed by user; lock, never re-askX6contradicted by latestprior closure undermined by new user input; reopen (no amend machinery — recompute yields this)X7answer revealed newriska pick exposed a risk the batch wasn't probing; reopens selection this turnX8user volunteered offanglefree-text beyond the MCQ → primary signal, not noise; may spawn a new angle

P — Phase (macro gear; advances on user-input conditions)
CodeEmit-meaningGate / effectP1dumping not probingbrain_dump; no MCQs; invite source materialP2choosing the pacemode_choice; no MCQs; offer fast vs coachingP3closing the gapselicitation; emit risk-ranked MCQ batchP4sealing the briefclosure; no MCQs; render brief from settled risks

L — Leverage (how the profile ranks the highest painpoint)
CodeEmit-meaningEffectL1killer beats nicetyrank WRONG_THING / BOUNDLESS gaps above polishL2unlocks many dimensionsprefer the gap that closes several at onceL3sand before structureconfirm X4 assumptions before building furtherL4one blocker firstif a blocker exists, confirm it before breadthL5thin masks dangertreat X2 as risk, not progressL6nothing open stopno live risk remains → advance phaseL7reframe beats coveragehighest-leverage move is a reframe, not the next ranked gap → permit off-profile question

R — Readiness (risk-weighted; keeps "shippable" honest)
CodeEmit-meaningEffectR1name risks firstlist live risks before any percentR2pick-only caps lowMCQ-only-closed gap → dimension ≤ 65R3unconfirmed caps hardopen X4/X6 present → ready_capped held downR4killers block shipany open killer-class gap → cannot exceed ~80R5shippable needs proof≥88 only when killers all X3/X5, ≥12 closed

S — Safe-question shaping (let the user think; choose risk-free)
CodeEmit-meaningEffectS1concrete not abstractoptions are real choices, not "tell me more"S2lowest-risk default visibleinclude the safe/conservative option explicitlyS3one decision eachone question closes one risk; no compound asksS4something-else opens subriska "something else" pick spawns a <parent>__<sub> angle at X1, ranked high — the user found the gap, honour itS5name the tradeoffwhen options compete, state what each costs

Q — Batch discipline (enforced on emitted codes)
CodeEmit-meaningCheckQ1one primary turnsingle lead question unless confirming a blockerQ2no theme repeatdrop any angle already X3/X5Q3no batch collisionno two batch items share a gap codeQ4drop paraphrase askeddrop items paraphrasing prior questionsQ5highest leverage firstorder batch by dimensions-unlockedQ6fewer than fiveif <5 live risks open, ask only those — never padQ7one open probereserve ONE batch item for a non-G-derived question the model judges valuable (guarantees a serendipity slot every turn)

C — Coaching voice (the BA tone, made legible)
CodeEmit-meaningNarrative effectC1acknowledge then reflectopen with warm ack + reflect understandingC2push thin answerstress-test follow-up on an X2 themeC3narrate the decisionone-line "Got it — X. Logged." on each X5C4request source materialbrain_dump only: ask for memos / decks / threadsC5offer two pathsmode_choice only: present fast vs coaching

Count
12 gap + 1 open-gap + 8 exposure + 4 phase + 7 leverage + 5 readiness + 5 shaping

7 batch + 5 coaching = 47 + the open-gap G0 folded in = 54 line items across 47 distinct
behavioural codes. (Exposure flags X1–X8 attach to gaps rather than standing alone, so
the emittable behavioural set is the 47 you approved; the X-flags are modifiers.)


RUBRIC ADDITION — paste into the discovery rubric

Emit your assessment as state codes.
After you have reasoned in full against this rubric — assessing the live discovery the
way a senior BA would — also emit a single line of state codes that declares your read.
Attach an exposure flag to each gap (e.g. G6:X2). The codes are a projection of the
user's input, not a memory of your own prior turns: derive them only from what the user
has actually said and picked.
The codes do not decide your questions — your BA judgment does. Use them to (1) mark
which shippability risks are still live, (2) rank which painpoint most threatens a
shippable build, and (3) shape MCQs that let the user commit to the lowest-risk path.
If you sense a risk no gap code names, emit G0 and articulate it. Every elicitation
turn must include one open probe (Q7) — a question the code profile did not generate.
Example emitted line:
P3 G1:X5 G4:X3 G6:X2 G8:X1 GA:X4 L1 L3 L5 R3 S2 Q7
→ elicitation; user & workflow closed; scope thin (press it); failure-modes wide open;
one assumption built-on-sand to confirm; rank killers, confirm the sand, treat thin as
danger; readiness held by the unconfirmed; surface the safe default; reserve an open probe.

=== USER — turn context (1,195 chars) ===

TURN 4

Apply the rubric in the system message. User input is source of truth; recompute codes each turn.
Enabled output sections: state_codes

--- OUTPUT FORMAT (this turn) ---
Output ONLY one line of state codes — no markdown headers, no prose.
Example: P3 G1:X1 G4:X2 G6:X1 L1 L4 R3 S2 Q1 Q7
Reason against the rubric internally; emit codes only.


--- SESSION MEMORY (includes compressed conversation; recompute codes from user truth) ---
# Discovery memory

> Patched after each LLM turn. **User messages are source of truth** — treat assistant
> codes below as the last declared read, then recompute from all user input each turn.

## Pitch
## Latest state codes
_(none)_

## Latest state codes
P2 G1:X1 G4:X1 G6:X1 L1 R3 S2 Q7

## Settled facts (user-confirmed only)
_(none)_

## Compressed conversation
T1 — user: "" → P1 G0:X1
T2 — user: "Car selling app" → P1 G0:X1 G6:X1 Q7
T3 — user: "Peer-to-peer marketplace connecting private car sellers with buyers — mobile-fir…" → P2 G1:X1 G4:X1 G6:X1 L1 R3 S2 Q7


--- NEW USER INPUT (SOURCE OF TRUTH THIS TURN) ---
MVP: create a listing with photos, browse and search listings, contact the seller, arrange a meetup. No in-app payments in v1.

```

#### <a id="turn-04-output"></a> 2 — Output

```text
P3 G3:X1 G6:X2 G8:X1 GA:X4 L1 L4 R3 S2 Q7
```

---

## Turn 05 — 2026-05-24T09:57:56.992929+00:00

**Model:** `gpt-4o-mini` · prep 0 ms · API wait 1034 ms

| # | What was sent to the LLM | Output | Token spend (input / output) | Total response time |
|---|--------------------------|--------|------------------------------|---------------------|
| **05** | [9,000 chars — expand](#turn-05-sent) | [35 chars — expand](#turn-05-output) | **2,265 / 23** (Σ 2,288) | **1033.9 ms** (1.034 s) |

#### <a id="turn-05-sent"></a> 1 — What was sent to the LLM

```text
=== SYSTEM — llm-rubric.md only (7,583 chars) ===

Discovery State Codes — v0.1 (47 codes)

What this is: a closed vocabulary the model emits to declare its read of the
discovery, after reasoning in full against the discovery rubric. The codes do not
replace judgment — they make it legible, enforceable, and continuous.
Source of truth: the user's pitch and answers ONLY. The code profile is derived
from user input each turn, never from the model's own prior output. The model's
emitted codes are a projection of user truth, not a separate memory.
Hard line: codes are OUTPUT, never INPUT. The model reads the rubric, assesses the
conversation, then emits codes. It must never generate questions mechanically from
codes while skipping the rubric.


⚠ Risk taxonomy — PROVISIONAL (confirm before relying on this)
Every G, L, and R code points at one of these shippability killers. These are
derived from the rubric's 14 dimensions, not confirmed by the product owner. If the
real "what kills a build" list differs, replace this block and the G/L/R codes re-point.

WRONG_THING — user / problem unproven → you build what nobody needs
BOUNDLESS — scope undefined → you build forever, never ship
UNMEASURABLE — no success signal → you can't tell if it worked
FRAGILE — failure / edge modes unhandled → it breaks in prod
BUILT_ON_SAND — assumptions unconfirmed → foundation collapses
UNGOVERNED — runtime / human-review / policy gaps → ships but can't be operated safely


G — Gap pointers (the 12 angles, recast as live risk exposures)
Each marks an unclosed risk and points at the question that closes it.
CodeEmit-meaningRisk classQuestion it drivesG1user unproven riskWRONG_THINGwho exactly, concretelyG2outcome unproven riskWRONG_THINGwhat job, measurablyG3entry unproven riskBOUNDLESShow use beginsG4workflow unproven riskBOUNDLESSthe one core pathG5success undefined riskUNMEASURABLEwhat proves it workedG6scope unbounded riskBOUNDLESSin vs out, v1G7domain rule riskUNGOVERNEDwhat constraint bindsG8failure unhandled riskFRAGILEwhat happens brokenG9tradeoff unsettled riskBOUNDLESSwhich competing optionGAassumption unconfirmed riskBUILT_ON_SANDbelieve vs provenGBruntime policy riskUNGOVERNEDhow it operates liveGChuman review riskUNGOVERNEDwhere humans intervene
Open-class gap (catches risk the taxonomy can't name)
CodeEmit-meaningForcesG0unnamed risk senseda shippability risk no G1–GC fits — model MUST name it in narrative and propose an angle. Each G0 is a signal your taxonomy has a hole — log it.

X — Exposure (how hot is each gap; derived from user input only)
Attach to a gap code, e.g. G6:X2 = scope answered-but-thin.
CodeEmit-meaningRisk meaning / next moveX1open never touchedfull risk live; strong candidate to askX2answered but thinrisk MASKED not closed; press one follow-upX3answered with substancerisk genuinely lowered; stop askingX4inferred not confirmedhidden risk (sand); convert to confirming MCQX5user-settled hardrisk closed by user; lock, never re-askX6contradicted by latestprior closure undermined by new user input; reopen (no amend machinery — recompute yields this)X7answer revealed newriska pick exposed a risk the batch wasn't probing; reopens selection this turnX8user volunteered offanglefree-text beyond the MCQ → primary signal, not noise; may spawn a new angle

P — Phase (macro gear; advances on user-input conditions)
CodeEmit-meaningGate / effectP1dumping not probingbrain_dump; no MCQs; invite source materialP2choosing the pacemode_choice; no MCQs; offer fast vs coachingP3closing the gapselicitation; emit risk-ranked MCQ batchP4sealing the briefclosure; no MCQs; render brief from settled risks

L — Leverage (how the profile ranks the highest painpoint)
CodeEmit-meaningEffectL1killer beats nicetyrank WRONG_THING / BOUNDLESS gaps above polishL2unlocks many dimensionsprefer the gap that closes several at onceL3sand before structureconfirm X4 assumptions before building furtherL4one blocker firstif a blocker exists, confirm it before breadthL5thin masks dangertreat X2 as risk, not progressL6nothing open stopno live risk remains → advance phaseL7reframe beats coveragehighest-leverage move is a reframe, not the next ranked gap → permit off-profile question

R — Readiness (risk-weighted; keeps "shippable" honest)
CodeEmit-meaningEffectR1name risks firstlist live risks before any percentR2pick-only caps lowMCQ-only-closed gap → dimension ≤ 65R3unconfirmed caps hardopen X4/X6 present → ready_capped held downR4killers block shipany open killer-class gap → cannot exceed ~80R5shippable needs proof≥88 only when killers all X3/X5, ≥12 closed

S — Safe-question shaping (let the user think; choose risk-free)
CodeEmit-meaningEffectS1concrete not abstractoptions are real choices, not "tell me more"S2lowest-risk default visibleinclude the safe/conservative option explicitlyS3one decision eachone question closes one risk; no compound asksS4something-else opens subriska "something else" pick spawns a <parent>__<sub> angle at X1, ranked high — the user found the gap, honour itS5name the tradeoffwhen options compete, state what each costs

Q — Batch discipline (enforced on emitted codes)
CodeEmit-meaningCheckQ1one primary turnsingle lead question unless confirming a blockerQ2no theme repeatdrop any angle already X3/X5Q3no batch collisionno two batch items share a gap codeQ4drop paraphrase askeddrop items paraphrasing prior questionsQ5highest leverage firstorder batch by dimensions-unlockedQ6fewer than fiveif <5 live risks open, ask only those — never padQ7one open probereserve ONE batch item for a non-G-derived question the model judges valuable (guarantees a serendipity slot every turn)

C — Coaching voice (the BA tone, made legible)
CodeEmit-meaningNarrative effectC1acknowledge then reflectopen with warm ack + reflect understandingC2push thin answerstress-test follow-up on an X2 themeC3narrate the decisionone-line "Got it — X. Logged." on each X5C4request source materialbrain_dump only: ask for memos / decks / threadsC5offer two pathsmode_choice only: present fast vs coaching

Count
12 gap + 1 open-gap + 8 exposure + 4 phase + 7 leverage + 5 readiness + 5 shaping

7 batch + 5 coaching = 47 + the open-gap G0 folded in = 54 line items across 47 distinct
behavioural codes. (Exposure flags X1–X8 attach to gaps rather than standing alone, so
the emittable behavioural set is the 47 you approved; the X-flags are modifiers.)


RUBRIC ADDITION — paste into the discovery rubric

Emit your assessment as state codes.
After you have reasoned in full against this rubric — assessing the live discovery the
way a senior BA would — also emit a single line of state codes that declares your read.
Attach an exposure flag to each gap (e.g. G6:X2). The codes are a projection of the
user's input, not a memory of your own prior turns: derive them only from what the user
has actually said and picked.
The codes do not decide your questions — your BA judgment does. Use them to (1) mark
which shippability risks are still live, (2) rank which painpoint most threatens a
shippable build, and (3) shape MCQs that let the user commit to the lowest-risk path.
If you sense a risk no gap code names, emit G0 and articulate it. Every elicitation
turn must include one open probe (Q7) — a question the code profile did not generate.
Example emitted line:
P3 G1:X5 G4:X3 G6:X2 G8:X1 GA:X4 L1 L3 L5 R3 S2 Q7
→ elicitation; user & workflow closed; scope thin (press it); failure-modes wide open;
one assumption built-on-sand to confirm; rank killers, confirm the sand, treat thin as
danger; readiness held by the unconfirmed; surface the safe default; reserve an open probe.

=== USER — turn context (1,321 chars) ===

TURN 5

Apply the rubric in the system message. User input is source of truth; recompute codes each turn.
Enabled output sections: state_codes

--- OUTPUT FORMAT (this turn) ---
Output ONLY one line of state codes — no markdown headers, no prose.
Example: P3 G1:X1 G4:X2 G6:X1 L1 L4 R3 S2 Q1 Q7
Reason against the rubric internally; emit codes only.


--- SESSION MEMORY (includes compressed conversation; recompute codes from user truth) ---
# Discovery memory

> Patched after each LLM turn. **User messages are source of truth** — treat assistant
> codes below as the last declared read, then recompute from all user input each turn.

## Pitch
## Latest state codes
_(none)_

## Latest state codes
P3 G3:X1 G6:X2 G8:X1 GA:X4 L1 L4 R3 S2 Q7

## Settled facts (user-confirmed only)
_(none)_

## Compressed conversation
T1 — user: "" → P1 G0:X1
T2 — user: "Car selling app" → P1 G0:X1 G6:X1 Q7
T3 — user: "Peer-to-peer marketplace connecting private car sellers with buyers — mobile-fir…" → P2 G1:X1 G4:X1 G6:X1 L1 R3 S2 Q7
T4 — user: "MVP: create a listing with photos, browse and search listings, contact the selle…" → P3 G3:X1 G6:X2 G8:X1 GA:X4 L1 L4 R3 S2 Q7


--- NEW USER INPUT (SOURCE OF TRUTH THIS TURN) ---
Trust is critical: light seller verification, report listing, and safety guidance for in-person meetups.

```

#### <a id="turn-05-output"></a> 2 — Output

```text
P3 G1:X1 G8:X1 GA:X4 L1 L4 R3 S2 Q7
```

---

## Turn 06 — 2026-05-24T09:57:58.553371+00:00

**Model:** `gpt-4o-mini` · prep 0 ms · API wait 1228 ms

| # | What was sent to the LLM | Output | Token spend (input / output) | Total response time |
|---|--------------------------|--------|------------------------------|---------------------|
| **06** | [9,114 chars — expand](#turn-06-sent) | [35 chars — expand](#turn-06-output) | **2,307 / 23** (Σ 2,330) | **1227.8 ms** (1.228 s) |

#### <a id="turn-06-sent"></a> 1 — What was sent to the LLM

```text
=== SYSTEM — llm-rubric.md only (7,583 chars) ===

Discovery State Codes — v0.1 (47 codes)

What this is: a closed vocabulary the model emits to declare its read of the
discovery, after reasoning in full against the discovery rubric. The codes do not
replace judgment — they make it legible, enforceable, and continuous.
Source of truth: the user's pitch and answers ONLY. The code profile is derived
from user input each turn, never from the model's own prior output. The model's
emitted codes are a projection of user truth, not a separate memory.
Hard line: codes are OUTPUT, never INPUT. The model reads the rubric, assesses the
conversation, then emits codes. It must never generate questions mechanically from
codes while skipping the rubric.


⚠ Risk taxonomy — PROVISIONAL (confirm before relying on this)
Every G, L, and R code points at one of these shippability killers. These are
derived from the rubric's 14 dimensions, not confirmed by the product owner. If the
real "what kills a build" list differs, replace this block and the G/L/R codes re-point.

WRONG_THING — user / problem unproven → you build what nobody needs
BOUNDLESS — scope undefined → you build forever, never ship
UNMEASURABLE — no success signal → you can't tell if it worked
FRAGILE — failure / edge modes unhandled → it breaks in prod
BUILT_ON_SAND — assumptions unconfirmed → foundation collapses
UNGOVERNED — runtime / human-review / policy gaps → ships but can't be operated safely


G — Gap pointers (the 12 angles, recast as live risk exposures)
Each marks an unclosed risk and points at the question that closes it.
CodeEmit-meaningRisk classQuestion it drivesG1user unproven riskWRONG_THINGwho exactly, concretelyG2outcome unproven riskWRONG_THINGwhat job, measurablyG3entry unproven riskBOUNDLESShow use beginsG4workflow unproven riskBOUNDLESSthe one core pathG5success undefined riskUNMEASURABLEwhat proves it workedG6scope unbounded riskBOUNDLESSin vs out, v1G7domain rule riskUNGOVERNEDwhat constraint bindsG8failure unhandled riskFRAGILEwhat happens brokenG9tradeoff unsettled riskBOUNDLESSwhich competing optionGAassumption unconfirmed riskBUILT_ON_SANDbelieve vs provenGBruntime policy riskUNGOVERNEDhow it operates liveGChuman review riskUNGOVERNEDwhere humans intervene
Open-class gap (catches risk the taxonomy can't name)
CodeEmit-meaningForcesG0unnamed risk senseda shippability risk no G1–GC fits — model MUST name it in narrative and propose an angle. Each G0 is a signal your taxonomy has a hole — log it.

X — Exposure (how hot is each gap; derived from user input only)
Attach to a gap code, e.g. G6:X2 = scope answered-but-thin.
CodeEmit-meaningRisk meaning / next moveX1open never touchedfull risk live; strong candidate to askX2answered but thinrisk MASKED not closed; press one follow-upX3answered with substancerisk genuinely lowered; stop askingX4inferred not confirmedhidden risk (sand); convert to confirming MCQX5user-settled hardrisk closed by user; lock, never re-askX6contradicted by latestprior closure undermined by new user input; reopen (no amend machinery — recompute yields this)X7answer revealed newriska pick exposed a risk the batch wasn't probing; reopens selection this turnX8user volunteered offanglefree-text beyond the MCQ → primary signal, not noise; may spawn a new angle

P — Phase (macro gear; advances on user-input conditions)
CodeEmit-meaningGate / effectP1dumping not probingbrain_dump; no MCQs; invite source materialP2choosing the pacemode_choice; no MCQs; offer fast vs coachingP3closing the gapselicitation; emit risk-ranked MCQ batchP4sealing the briefclosure; no MCQs; render brief from settled risks

L — Leverage (how the profile ranks the highest painpoint)
CodeEmit-meaningEffectL1killer beats nicetyrank WRONG_THING / BOUNDLESS gaps above polishL2unlocks many dimensionsprefer the gap that closes several at onceL3sand before structureconfirm X4 assumptions before building furtherL4one blocker firstif a blocker exists, confirm it before breadthL5thin masks dangertreat X2 as risk, not progressL6nothing open stopno live risk remains → advance phaseL7reframe beats coveragehighest-leverage move is a reframe, not the next ranked gap → permit off-profile question

R — Readiness (risk-weighted; keeps "shippable" honest)
CodeEmit-meaningEffectR1name risks firstlist live risks before any percentR2pick-only caps lowMCQ-only-closed gap → dimension ≤ 65R3unconfirmed caps hardopen X4/X6 present → ready_capped held downR4killers block shipany open killer-class gap → cannot exceed ~80R5shippable needs proof≥88 only when killers all X3/X5, ≥12 closed

S — Safe-question shaping (let the user think; choose risk-free)
CodeEmit-meaningEffectS1concrete not abstractoptions are real choices, not "tell me more"S2lowest-risk default visibleinclude the safe/conservative option explicitlyS3one decision eachone question closes one risk; no compound asksS4something-else opens subriska "something else" pick spawns a <parent>__<sub> angle at X1, ranked high — the user found the gap, honour itS5name the tradeoffwhen options compete, state what each costs

Q — Batch discipline (enforced on emitted codes)
CodeEmit-meaningCheckQ1one primary turnsingle lead question unless confirming a blockerQ2no theme repeatdrop any angle already X3/X5Q3no batch collisionno two batch items share a gap codeQ4drop paraphrase askeddrop items paraphrasing prior questionsQ5highest leverage firstorder batch by dimensions-unlockedQ6fewer than fiveif <5 live risks open, ask only those — never padQ7one open probereserve ONE batch item for a non-G-derived question the model judges valuable (guarantees a serendipity slot every turn)

C — Coaching voice (the BA tone, made legible)
CodeEmit-meaningNarrative effectC1acknowledge then reflectopen with warm ack + reflect understandingC2push thin answerstress-test follow-up on an X2 themeC3narrate the decisionone-line "Got it — X. Logged." on each X5C4request source materialbrain_dump only: ask for memos / decks / threadsC5offer two pathsmode_choice only: present fast vs coaching

Count
12 gap + 1 open-gap + 8 exposure + 4 phase + 7 leverage + 5 readiness + 5 shaping

7 batch + 5 coaching = 47 + the open-gap G0 folded in = 54 line items across 47 distinct
behavioural codes. (Exposure flags X1–X8 attach to gaps rather than standing alone, so
the emittable behavioural set is the 47 you approved; the X-flags are modifiers.)


RUBRIC ADDITION — paste into the discovery rubric

Emit your assessment as state codes.
After you have reasoned in full against this rubric — assessing the live discovery the
way a senior BA would — also emit a single line of state codes that declares your read.
Attach an exposure flag to each gap (e.g. G6:X2). The codes are a projection of the
user's input, not a memory of your own prior turns: derive them only from what the user
has actually said and picked.
The codes do not decide your questions — your BA judgment does. Use them to (1) mark
which shippability risks are still live, (2) rank which painpoint most threatens a
shippable build, and (3) shape MCQs that let the user commit to the lowest-risk path.
If you sense a risk no gap code names, emit G0 and articulate it. Every elicitation
turn must include one open probe (Q7) — a question the code profile did not generate.
Example emitted line:
P3 G1:X5 G4:X3 G6:X2 G8:X1 GA:X4 L1 L3 L5 R3 S2 Q7
→ elicitation; user & workflow closed; scope thin (press it); failure-modes wide open;
one assumption built-on-sand to confirm; rank killers, confirm the sand, treat thin as
danger; readiness held by the unconfirmed; surface the safe default; reserve an open probe.

=== USER — turn context (1,435 chars) ===

TURN 6

Apply the rubric in the system message. User input is source of truth; recompute codes each turn.
Enabled output sections: state_codes

--- OUTPUT FORMAT (this turn) ---
Output ONLY one line of state codes — no markdown headers, no prose.
Example: P3 G1:X1 G4:X2 G6:X1 L1 L4 R3 S2 Q1 Q7
Reason against the rubric internally; emit codes only.


--- SESSION MEMORY (includes compressed conversation; recompute codes from user truth) ---
# Discovery memory

> Patched after each LLM turn. **User messages are source of truth** — treat assistant
> codes below as the last declared read, then recompute from all user input each turn.

## Pitch
## Latest state codes
_(none)_

## Latest state codes
P3 G1:X1 G8:X1 GA:X4 L1 L4 R3 S2 Q7

## Settled facts (user-confirmed only)
_(none)_

## Compressed conversation
T1 — user: "" → P1 G0:X1
T2 — user: "Car selling app" → P1 G0:X1 G6:X1 Q7
T3 — user: "Peer-to-peer marketplace connecting private car sellers with buyers — mobile-fir…" → P2 G1:X1 G4:X1 G6:X1 L1 R3 S2 Q7
T4 — user: "MVP: create a listing with photos, browse and search listings, contact the selle…" → P3 G3:X1 G6:X2 G8:X1 GA:X4 L1 L4 R3 S2 Q7
T5 — user: "Trust is critical: light seller verification, report listing, and safety guidanc…" → P3 G1:X1 G8:X1 GA:X4 L1 L4 R3 S2 Q7


--- NEW USER INPUT (SOURCE OF TRUTH THIS TURN) ---
Price is manual negotiation only — no automated pricing, auctions, or instant offers in v1.

```

#### <a id="turn-06-output"></a> 2 — Output

```text
P3 G6:X2 G8:X1 GA:X4 L1 L4 R3 S2 Q7
```

---

## Turn 07 — 2026-05-24T09:58:00.210523+00:00

**Model:** `gpt-4o-mini` · prep 0 ms · API wait 1126 ms

| # | What was sent to the LLM | Output | Token spend (input / output) | Total response time |
|---|--------------------------|--------|------------------------------|---------------------|
| **07** | [9,266 chars — expand](#turn-07-sent) | [29 chars — expand](#turn-07-output) | **2,360 / 20** (Σ 2,380) | **1125.9 ms** (1.126 s) |

#### <a id="turn-07-sent"></a> 1 — What was sent to the LLM

```text
=== SYSTEM — llm-rubric.md only (7,583 chars) ===

Discovery State Codes — v0.1 (47 codes)

What this is: a closed vocabulary the model emits to declare its read of the
discovery, after reasoning in full against the discovery rubric. The codes do not
replace judgment — they make it legible, enforceable, and continuous.
Source of truth: the user's pitch and answers ONLY. The code profile is derived
from user input each turn, never from the model's own prior output. The model's
emitted codes are a projection of user truth, not a separate memory.
Hard line: codes are OUTPUT, never INPUT. The model reads the rubric, assesses the
conversation, then emits codes. It must never generate questions mechanically from
codes while skipping the rubric.


⚠ Risk taxonomy — PROVISIONAL (confirm before relying on this)
Every G, L, and R code points at one of these shippability killers. These are
derived from the rubric's 14 dimensions, not confirmed by the product owner. If the
real "what kills a build" list differs, replace this block and the G/L/R codes re-point.

WRONG_THING — user / problem unproven → you build what nobody needs
BOUNDLESS — scope undefined → you build forever, never ship
UNMEASURABLE — no success signal → you can't tell if it worked
FRAGILE — failure / edge modes unhandled → it breaks in prod
BUILT_ON_SAND — assumptions unconfirmed → foundation collapses
UNGOVERNED — runtime / human-review / policy gaps → ships but can't be operated safely


G — Gap pointers (the 12 angles, recast as live risk exposures)
Each marks an unclosed risk and points at the question that closes it.
CodeEmit-meaningRisk classQuestion it drivesG1user unproven riskWRONG_THINGwho exactly, concretelyG2outcome unproven riskWRONG_THINGwhat job, measurablyG3entry unproven riskBOUNDLESShow use beginsG4workflow unproven riskBOUNDLESSthe one core pathG5success undefined riskUNMEASURABLEwhat proves it workedG6scope unbounded riskBOUNDLESSin vs out, v1G7domain rule riskUNGOVERNEDwhat constraint bindsG8failure unhandled riskFRAGILEwhat happens brokenG9tradeoff unsettled riskBOUNDLESSwhich competing optionGAassumption unconfirmed riskBUILT_ON_SANDbelieve vs provenGBruntime policy riskUNGOVERNEDhow it operates liveGChuman review riskUNGOVERNEDwhere humans intervene
Open-class gap (catches risk the taxonomy can't name)
CodeEmit-meaningForcesG0unnamed risk senseda shippability risk no G1–GC fits — model MUST name it in narrative and propose an angle. Each G0 is a signal your taxonomy has a hole — log it.

X — Exposure (how hot is each gap; derived from user input only)
Attach to a gap code, e.g. G6:X2 = scope answered-but-thin.
CodeEmit-meaningRisk meaning / next moveX1open never touchedfull risk live; strong candidate to askX2answered but thinrisk MASKED not closed; press one follow-upX3answered with substancerisk genuinely lowered; stop askingX4inferred not confirmedhidden risk (sand); convert to confirming MCQX5user-settled hardrisk closed by user; lock, never re-askX6contradicted by latestprior closure undermined by new user input; reopen (no amend machinery — recompute yields this)X7answer revealed newriska pick exposed a risk the batch wasn't probing; reopens selection this turnX8user volunteered offanglefree-text beyond the MCQ → primary signal, not noise; may spawn a new angle

P — Phase (macro gear; advances on user-input conditions)
CodeEmit-meaningGate / effectP1dumping not probingbrain_dump; no MCQs; invite source materialP2choosing the pacemode_choice; no MCQs; offer fast vs coachingP3closing the gapselicitation; emit risk-ranked MCQ batchP4sealing the briefclosure; no MCQs; render brief from settled risks

L — Leverage (how the profile ranks the highest painpoint)
CodeEmit-meaningEffectL1killer beats nicetyrank WRONG_THING / BOUNDLESS gaps above polishL2unlocks many dimensionsprefer the gap that closes several at onceL3sand before structureconfirm X4 assumptions before building furtherL4one blocker firstif a blocker exists, confirm it before breadthL5thin masks dangertreat X2 as risk, not progressL6nothing open stopno live risk remains → advance phaseL7reframe beats coveragehighest-leverage move is a reframe, not the next ranked gap → permit off-profile question

R — Readiness (risk-weighted; keeps "shippable" honest)
CodeEmit-meaningEffectR1name risks firstlist live risks before any percentR2pick-only caps lowMCQ-only-closed gap → dimension ≤ 65R3unconfirmed caps hardopen X4/X6 present → ready_capped held downR4killers block shipany open killer-class gap → cannot exceed ~80R5shippable needs proof≥88 only when killers all X3/X5, ≥12 closed

S — Safe-question shaping (let the user think; choose risk-free)
CodeEmit-meaningEffectS1concrete not abstractoptions are real choices, not "tell me more"S2lowest-risk default visibleinclude the safe/conservative option explicitlyS3one decision eachone question closes one risk; no compound asksS4something-else opens subriska "something else" pick spawns a <parent>__<sub> angle at X1, ranked high — the user found the gap, honour itS5name the tradeoffwhen options compete, state what each costs

Q — Batch discipline (enforced on emitted codes)
CodeEmit-meaningCheckQ1one primary turnsingle lead question unless confirming a blockerQ2no theme repeatdrop any angle already X3/X5Q3no batch collisionno two batch items share a gap codeQ4drop paraphrase askeddrop items paraphrasing prior questionsQ5highest leverage firstorder batch by dimensions-unlockedQ6fewer than fiveif <5 live risks open, ask only those — never padQ7one open probereserve ONE batch item for a non-G-derived question the model judges valuable (guarantees a serendipity slot every turn)

C — Coaching voice (the BA tone, made legible)
CodeEmit-meaningNarrative effectC1acknowledge then reflectopen with warm ack + reflect understandingC2push thin answerstress-test follow-up on an X2 themeC3narrate the decisionone-line "Got it — X. Logged." on each X5C4request source materialbrain_dump only: ask for memos / decks / threadsC5offer two pathsmode_choice only: present fast vs coaching

Count
12 gap + 1 open-gap + 8 exposure + 4 phase + 7 leverage + 5 readiness + 5 shaping

7 batch + 5 coaching = 47 + the open-gap G0 folded in = 54 line items across 47 distinct
behavioural codes. (Exposure flags X1–X8 attach to gaps rather than standing alone, so
the emittable behavioural set is the 47 you approved; the X-flags are modifiers.)


RUBRIC ADDITION — paste into the discovery rubric

Emit your assessment as state codes.
After you have reasoned in full against this rubric — assessing the live discovery the
way a senior BA would — also emit a single line of state codes that declares your read.
Attach an exposure flag to each gap (e.g. G6:X2). The codes are a projection of the
user's input, not a memory of your own prior turns: derive them only from what the user
has actually said and picked.
The codes do not decide your questions — your BA judgment does. Use them to (1) mark
which shippability risks are still live, (2) rank which painpoint most threatens a
shippable build, and (3) shape MCQs that let the user commit to the lowest-risk path.
If you sense a risk no gap code names, emit G0 and articulate it. Every elicitation
turn must include one open probe (Q7) — a question the code profile did not generate.
Example emitted line:
P3 G1:X5 G4:X3 G6:X2 G8:X1 GA:X4 L1 L3 L5 R3 S2 Q7
→ elicitation; user & workflow closed; scope thin (press it); failure-modes wide open;
one assumption built-on-sand to confirm; rank killers, confirm the sand, treat thin as
danger; readiness held by the unconfirmed; surface the safe default; reserve an open probe.

=== USER — turn context (1,587 chars) ===

TURN 7

Apply the rubric in the system message. User input is source of truth; recompute codes each turn.
Enabled output sections: state_codes

--- OUTPUT FORMAT (this turn) ---
Output ONLY one line of state codes — no markdown headers, no prose.
Example: P3 G1:X1 G4:X2 G6:X1 L1 L4 R3 S2 Q1 Q7
Reason against the rubric internally; emit codes only.


--- SESSION MEMORY (includes compressed conversation; recompute codes from user truth) ---
# Discovery memory

> Patched after each LLM turn. **User messages are source of truth** — treat assistant
> codes below as the last declared read, then recompute from all user input each turn.

## Pitch
## Latest state codes
_(none)_

## Latest state codes
P3 G6:X2 G8:X1 GA:X4 L1 L4 R3 S2 Q7

## Settled facts (user-confirmed only)
_(none)_

## Compressed conversation
T1 — user: "" → P1 G0:X1
T2 — user: "Car selling app" → P1 G0:X1 G6:X1 Q7
T3 — user: "Peer-to-peer marketplace connecting private car sellers with buyers — mobile-fir…" → P2 G1:X1 G4:X1 G6:X1 L1 R3 S2 Q7
T4 — user: "MVP: create a listing with photos, browse and search listings, contact the selle…" → P3 G3:X1 G6:X2 G8:X1 GA:X4 L1 L4 R3 S2 Q7
T5 — user: "Trust is critical: light seller verification, report listing, and safety guidanc…" → P3 G1:X1 G8:X1 GA:X4 L1 L4 R3 S2 Q7
T6 — user: "Price is manual negotiation only — no automated pricing, auctions, or instant of…" → P3 G6:X2 G8:X1 GA:X4 L1 L4 R3 S2 Q7


--- NEW USER INPUT (SOURCE OF TRUTH THIS TURN) ---
Out of scope for v1: financing, shipping, professional inspections, and dealer fleet tools. Consumer P2P only.

```

#### <a id="turn-07-output"></a> 2 — Output

```text
P3 G6:X2 G7:X1 L1 L4 R3 S2 Q7
```

---

## Turn 08 — 2026-05-24T09:58:01.738087+00:00

**Model:** `gpt-4o-mini` · prep 0 ms · API wait 1191 ms

| # | What was sent to the LLM | Output | Token spend (input / output) | Total response time |
|---|--------------------------|--------|------------------------------|---------------------|
| **08** | [9,387 chars — expand](#turn-08-sent) | [35 chars — expand](#turn-08-output) | **2,403 / 24** (Σ 2,427) | **1191.2 ms** (1.191 s) |

#### <a id="turn-08-sent"></a> 1 — What was sent to the LLM

```text
=== SYSTEM — llm-rubric.md only (7,583 chars) ===

Discovery State Codes — v0.1 (47 codes)

What this is: a closed vocabulary the model emits to declare its read of the
discovery, after reasoning in full against the discovery rubric. The codes do not
replace judgment — they make it legible, enforceable, and continuous.
Source of truth: the user's pitch and answers ONLY. The code profile is derived
from user input each turn, never from the model's own prior output. The model's
emitted codes are a projection of user truth, not a separate memory.
Hard line: codes are OUTPUT, never INPUT. The model reads the rubric, assesses the
conversation, then emits codes. It must never generate questions mechanically from
codes while skipping the rubric.


⚠ Risk taxonomy — PROVISIONAL (confirm before relying on this)
Every G, L, and R code points at one of these shippability killers. These are
derived from the rubric's 14 dimensions, not confirmed by the product owner. If the
real "what kills a build" list differs, replace this block and the G/L/R codes re-point.

WRONG_THING — user / problem unproven → you build what nobody needs
BOUNDLESS — scope undefined → you build forever, never ship
UNMEASURABLE — no success signal → you can't tell if it worked
FRAGILE — failure / edge modes unhandled → it breaks in prod
BUILT_ON_SAND — assumptions unconfirmed → foundation collapses
UNGOVERNED — runtime / human-review / policy gaps → ships but can't be operated safely


G — Gap pointers (the 12 angles, recast as live risk exposures)
Each marks an unclosed risk and points at the question that closes it.
CodeEmit-meaningRisk classQuestion it drivesG1user unproven riskWRONG_THINGwho exactly, concretelyG2outcome unproven riskWRONG_THINGwhat job, measurablyG3entry unproven riskBOUNDLESShow use beginsG4workflow unproven riskBOUNDLESSthe one core pathG5success undefined riskUNMEASURABLEwhat proves it workedG6scope unbounded riskBOUNDLESSin vs out, v1G7domain rule riskUNGOVERNEDwhat constraint bindsG8failure unhandled riskFRAGILEwhat happens brokenG9tradeoff unsettled riskBOUNDLESSwhich competing optionGAassumption unconfirmed riskBUILT_ON_SANDbelieve vs provenGBruntime policy riskUNGOVERNEDhow it operates liveGChuman review riskUNGOVERNEDwhere humans intervene
Open-class gap (catches risk the taxonomy can't name)
CodeEmit-meaningForcesG0unnamed risk senseda shippability risk no G1–GC fits — model MUST name it in narrative and propose an angle. Each G0 is a signal your taxonomy has a hole — log it.

X — Exposure (how hot is each gap; derived from user input only)
Attach to a gap code, e.g. G6:X2 = scope answered-but-thin.
CodeEmit-meaningRisk meaning / next moveX1open never touchedfull risk live; strong candidate to askX2answered but thinrisk MASKED not closed; press one follow-upX3answered with substancerisk genuinely lowered; stop askingX4inferred not confirmedhidden risk (sand); convert to confirming MCQX5user-settled hardrisk closed by user; lock, never re-askX6contradicted by latestprior closure undermined by new user input; reopen (no amend machinery — recompute yields this)X7answer revealed newriska pick exposed a risk the batch wasn't probing; reopens selection this turnX8user volunteered offanglefree-text beyond the MCQ → primary signal, not noise; may spawn a new angle

P — Phase (macro gear; advances on user-input conditions)
CodeEmit-meaningGate / effectP1dumping not probingbrain_dump; no MCQs; invite source materialP2choosing the pacemode_choice; no MCQs; offer fast vs coachingP3closing the gapselicitation; emit risk-ranked MCQ batchP4sealing the briefclosure; no MCQs; render brief from settled risks

L — Leverage (how the profile ranks the highest painpoint)
CodeEmit-meaningEffectL1killer beats nicetyrank WRONG_THING / BOUNDLESS gaps above polishL2unlocks many dimensionsprefer the gap that closes several at onceL3sand before structureconfirm X4 assumptions before building furtherL4one blocker firstif a blocker exists, confirm it before breadthL5thin masks dangertreat X2 as risk, not progressL6nothing open stopno live risk remains → advance phaseL7reframe beats coveragehighest-leverage move is a reframe, not the next ranked gap → permit off-profile question

R — Readiness (risk-weighted; keeps "shippable" honest)
CodeEmit-meaningEffectR1name risks firstlist live risks before any percentR2pick-only caps lowMCQ-only-closed gap → dimension ≤ 65R3unconfirmed caps hardopen X4/X6 present → ready_capped held downR4killers block shipany open killer-class gap → cannot exceed ~80R5shippable needs proof≥88 only when killers all X3/X5, ≥12 closed

S — Safe-question shaping (let the user think; choose risk-free)
CodeEmit-meaningEffectS1concrete not abstractoptions are real choices, not "tell me more"S2lowest-risk default visibleinclude the safe/conservative option explicitlyS3one decision eachone question closes one risk; no compound asksS4something-else opens subriska "something else" pick spawns a <parent>__<sub> angle at X1, ranked high — the user found the gap, honour itS5name the tradeoffwhen options compete, state what each costs

Q — Batch discipline (enforced on emitted codes)
CodeEmit-meaningCheckQ1one primary turnsingle lead question unless confirming a blockerQ2no theme repeatdrop any angle already X3/X5Q3no batch collisionno two batch items share a gap codeQ4drop paraphrase askeddrop items paraphrasing prior questionsQ5highest leverage firstorder batch by dimensions-unlockedQ6fewer than fiveif <5 live risks open, ask only those — never padQ7one open probereserve ONE batch item for a non-G-derived question the model judges valuable (guarantees a serendipity slot every turn)

C — Coaching voice (the BA tone, made legible)
CodeEmit-meaningNarrative effectC1acknowledge then reflectopen with warm ack + reflect understandingC2push thin answerstress-test follow-up on an X2 themeC3narrate the decisionone-line "Got it — X. Logged." on each X5C4request source materialbrain_dump only: ask for memos / decks / threadsC5offer two pathsmode_choice only: present fast vs coaching

Count
12 gap + 1 open-gap + 8 exposure + 4 phase + 7 leverage + 5 readiness + 5 shaping

7 batch + 5 coaching = 47 + the open-gap G0 folded in = 54 line items across 47 distinct
behavioural codes. (Exposure flags X1–X8 attach to gaps rather than standing alone, so
the emittable behavioural set is the 47 you approved; the X-flags are modifiers.)


RUBRIC ADDITION — paste into the discovery rubric

Emit your assessment as state codes.
After you have reasoned in full against this rubric — assessing the live discovery the
way a senior BA would — also emit a single line of state codes that declares your read.
Attach an exposure flag to each gap (e.g. G6:X2). The codes are a projection of the
user's input, not a memory of your own prior turns: derive them only from what the user
has actually said and picked.
The codes do not decide your questions — your BA judgment does. Use them to (1) mark
which shippability risks are still live, (2) rank which painpoint most threatens a
shippable build, and (3) shape MCQs that let the user commit to the lowest-risk path.
If you sense a risk no gap code names, emit G0 and articulate it. Every elicitation
turn must include one open probe (Q7) — a question the code profile did not generate.
Example emitted line:
P3 G1:X5 G4:X3 G6:X2 G8:X1 GA:X4 L1 L3 L5 R3 S2 Q7
→ elicitation; user & workflow closed; scope thin (press it); failure-modes wide open;
one assumption built-on-sand to confirm; rank killers, confirm the sand, treat thin as
danger; readiness held by the unconfirmed; surface the safe default; reserve an open probe.

=== USER — turn context (1,708 chars) ===

TURN 8

Apply the rubric in the system message. User input is source of truth; recompute codes each turn.
Enabled output sections: state_codes

--- OUTPUT FORMAT (this turn) ---
Output ONLY one line of state codes — no markdown headers, no prose.
Example: P3 G1:X1 G4:X2 G6:X1 L1 L4 R3 S2 Q1 Q7
Reason against the rubric internally; emit codes only.


--- SESSION MEMORY (includes compressed conversation; recompute codes from user truth) ---
# Discovery memory

> Patched after each LLM turn. **User messages are source of truth** — treat assistant
> codes below as the last declared read, then recompute from all user input each turn.

## Pitch
## Latest state codes
_(none)_

## Latest state codes
P3 G6:X2 G7:X1 L1 L4 R3 S2 Q7

## Settled facts (user-confirmed only)
_(none)_

## Compressed conversation
T1 — user: "" → P1 G0:X1
T2 — user: "Car selling app" → P1 G0:X1 G6:X1 Q7
T3 — user: "Peer-to-peer marketplace connecting private car sellers with buyers — mobile-fir…" → P2 G1:X1 G4:X1 G6:X1 L1 R3 S2 Q7
T4 — user: "MVP: create a listing with photos, browse and search listings, contact the selle…" → P3 G3:X1 G6:X2 G8:X1 GA:X4 L1 L4 R3 S2 Q7
T5 — user: "Trust is critical: light seller verification, report listing, and safety guidanc…" → P3 G1:X1 G8:X1 GA:X4 L1 L4 R3 S2 Q7
T6 — user: "Price is manual negotiation only — no automated pricing, auctions, or instant of…" → P3 G6:X2 G8:X1 GA:X4 L1 L4 R3 S2 Q7
T7 — user: "Out of scope for v1: financing, shipping, professional inspections, and dealer f…" → P3 G6:X2 G7:X1 L1 L4 R3 S2 Q7


--- NEW USER INPUT (SOURCE OF TRUTH THIS TURN) ---
Success means a completed sale handoff (buyer marks sold) and sellers who relist or sell again within 30 days.

```

#### <a id="turn-08-output"></a> 2 — Output

```text
P3 G2:X5 G5:X1 G6:X2 L1 L4 R3 S2 Q7
```

---

## Turn 09 — 2026-05-24T09:58:03.172372+00:00

**Model:** `gpt-4o-mini` · prep 0 ms · API wait 1106 ms

| # | What was sent to the LLM | Output | Token spend (input / output) | Total response time |
|---|--------------------------|--------|------------------------------|---------------------|
| **09** | [9,516 chars — expand](#turn-09-sent) | [41 chars — expand](#turn-09-output) | **2,450 / 28** (Σ 2,478) | **1106.2 ms** (1.106 s) |

#### <a id="turn-09-sent"></a> 1 — What was sent to the LLM

```text
=== SYSTEM — llm-rubric.md only (7,583 chars) ===

Discovery State Codes — v0.1 (47 codes)

What this is: a closed vocabulary the model emits to declare its read of the
discovery, after reasoning in full against the discovery rubric. The codes do not
replace judgment — they make it legible, enforceable, and continuous.
Source of truth: the user's pitch and answers ONLY. The code profile is derived
from user input each turn, never from the model's own prior output. The model's
emitted codes are a projection of user truth, not a separate memory.
Hard line: codes are OUTPUT, never INPUT. The model reads the rubric, assesses the
conversation, then emits codes. It must never generate questions mechanically from
codes while skipping the rubric.


⚠ Risk taxonomy — PROVISIONAL (confirm before relying on this)
Every G, L, and R code points at one of these shippability killers. These are
derived from the rubric's 14 dimensions, not confirmed by the product owner. If the
real "what kills a build" list differs, replace this block and the G/L/R codes re-point.

WRONG_THING — user / problem unproven → you build what nobody needs
BOUNDLESS — scope undefined → you build forever, never ship
UNMEASURABLE — no success signal → you can't tell if it worked
FRAGILE — failure / edge modes unhandled → it breaks in prod
BUILT_ON_SAND — assumptions unconfirmed → foundation collapses
UNGOVERNED — runtime / human-review / policy gaps → ships but can't be operated safely


G — Gap pointers (the 12 angles, recast as live risk exposures)
Each marks an unclosed risk and points at the question that closes it.
CodeEmit-meaningRisk classQuestion it drivesG1user unproven riskWRONG_THINGwho exactly, concretelyG2outcome unproven riskWRONG_THINGwhat job, measurablyG3entry unproven riskBOUNDLESShow use beginsG4workflow unproven riskBOUNDLESSthe one core pathG5success undefined riskUNMEASURABLEwhat proves it workedG6scope unbounded riskBOUNDLESSin vs out, v1G7domain rule riskUNGOVERNEDwhat constraint bindsG8failure unhandled riskFRAGILEwhat happens brokenG9tradeoff unsettled riskBOUNDLESSwhich competing optionGAassumption unconfirmed riskBUILT_ON_SANDbelieve vs provenGBruntime policy riskUNGOVERNEDhow it operates liveGChuman review riskUNGOVERNEDwhere humans intervene
Open-class gap (catches risk the taxonomy can't name)
CodeEmit-meaningForcesG0unnamed risk senseda shippability risk no G1–GC fits — model MUST name it in narrative and propose an angle. Each G0 is a signal your taxonomy has a hole — log it.

X — Exposure (how hot is each gap; derived from user input only)
Attach to a gap code, e.g. G6:X2 = scope answered-but-thin.
CodeEmit-meaningRisk meaning / next moveX1open never touchedfull risk live; strong candidate to askX2answered but thinrisk MASKED not closed; press one follow-upX3answered with substancerisk genuinely lowered; stop askingX4inferred not confirmedhidden risk (sand); convert to confirming MCQX5user-settled hardrisk closed by user; lock, never re-askX6contradicted by latestprior closure undermined by new user input; reopen (no amend machinery — recompute yields this)X7answer revealed newriska pick exposed a risk the batch wasn't probing; reopens selection this turnX8user volunteered offanglefree-text beyond the MCQ → primary signal, not noise; may spawn a new angle

P — Phase (macro gear; advances on user-input conditions)
CodeEmit-meaningGate / effectP1dumping not probingbrain_dump; no MCQs; invite source materialP2choosing the pacemode_choice; no MCQs; offer fast vs coachingP3closing the gapselicitation; emit risk-ranked MCQ batchP4sealing the briefclosure; no MCQs; render brief from settled risks

L — Leverage (how the profile ranks the highest painpoint)
CodeEmit-meaningEffectL1killer beats nicetyrank WRONG_THING / BOUNDLESS gaps above polishL2unlocks many dimensionsprefer the gap that closes several at onceL3sand before structureconfirm X4 assumptions before building furtherL4one blocker firstif a blocker exists, confirm it before breadthL5thin masks dangertreat X2 as risk, not progressL6nothing open stopno live risk remains → advance phaseL7reframe beats coveragehighest-leverage move is a reframe, not the next ranked gap → permit off-profile question

R — Readiness (risk-weighted; keeps "shippable" honest)
CodeEmit-meaningEffectR1name risks firstlist live risks before any percentR2pick-only caps lowMCQ-only-closed gap → dimension ≤ 65R3unconfirmed caps hardopen X4/X6 present → ready_capped held downR4killers block shipany open killer-class gap → cannot exceed ~80R5shippable needs proof≥88 only when killers all X3/X5, ≥12 closed

S — Safe-question shaping (let the user think; choose risk-free)
CodeEmit-meaningEffectS1concrete not abstractoptions are real choices, not "tell me more"S2lowest-risk default visibleinclude the safe/conservative option explicitlyS3one decision eachone question closes one risk; no compound asksS4something-else opens subriska "something else" pick spawns a <parent>__<sub> angle at X1, ranked high — the user found the gap, honour itS5name the tradeoffwhen options compete, state what each costs

Q — Batch discipline (enforced on emitted codes)
CodeEmit-meaningCheckQ1one primary turnsingle lead question unless confirming a blockerQ2no theme repeatdrop any angle already X3/X5Q3no batch collisionno two batch items share a gap codeQ4drop paraphrase askeddrop items paraphrasing prior questionsQ5highest leverage firstorder batch by dimensions-unlockedQ6fewer than fiveif <5 live risks open, ask only those — never padQ7one open probereserve ONE batch item for a non-G-derived question the model judges valuable (guarantees a serendipity slot every turn)

C — Coaching voice (the BA tone, made legible)
CodeEmit-meaningNarrative effectC1acknowledge then reflectopen with warm ack + reflect understandingC2push thin answerstress-test follow-up on an X2 themeC3narrate the decisionone-line "Got it — X. Logged." on each X5C4request source materialbrain_dump only: ask for memos / decks / threadsC5offer two pathsmode_choice only: present fast vs coaching

Count
12 gap + 1 open-gap + 8 exposure + 4 phase + 7 leverage + 5 readiness + 5 shaping

7 batch + 5 coaching = 47 + the open-gap G0 folded in = 54 line items across 47 distinct
behavioural codes. (Exposure flags X1–X8 attach to gaps rather than standing alone, so
the emittable behavioural set is the 47 you approved; the X-flags are modifiers.)


RUBRIC ADDITION — paste into the discovery rubric

Emit your assessment as state codes.
After you have reasoned in full against this rubric — assessing the live discovery the
way a senior BA would — also emit a single line of state codes that declares your read.
Attach an exposure flag to each gap (e.g. G6:X2). The codes are a projection of the
user's input, not a memory of your own prior turns: derive them only from what the user
has actually said and picked.
The codes do not decide your questions — your BA judgment does. Use them to (1) mark
which shippability risks are still live, (2) rank which painpoint most threatens a
shippable build, and (3) shape MCQs that let the user commit to the lowest-risk path.
If you sense a risk no gap code names, emit G0 and articulate it. Every elicitation
turn must include one open probe (Q7) — a question the code profile did not generate.
Example emitted line:
P3 G1:X5 G4:X3 G6:X2 G8:X1 GA:X4 L1 L3 L5 R3 S2 Q7
→ elicitation; user & workflow closed; scope thin (press it); failure-modes wide open;
one assumption built-on-sand to confirm; rank killers, confirm the sand, treat thin as
danger; readiness held by the unconfirmed; surface the safe default; reserve an open probe.

=== USER — turn context (1,837 chars) ===

TURN 9

Apply the rubric in the system message. User input is source of truth; recompute codes each turn.
Enabled output sections: state_codes

--- OUTPUT FORMAT (this turn) ---
Output ONLY one line of state codes — no markdown headers, no prose.
Example: P3 G1:X1 G4:X2 G6:X1 L1 L4 R3 S2 Q1 Q7
Reason against the rubric internally; emit codes only.


--- SESSION MEMORY (includes compressed conversation; recompute codes from user truth) ---
# Discovery memory

> Patched after each LLM turn. **User messages are source of truth** — treat assistant
> codes below as the last declared read, then recompute from all user input each turn.

## Pitch
## Latest state codes
_(none)_

## Latest state codes
P3 G2:X5 G5:X1 G6:X2 L1 L4 R3 S2 Q7

## Settled facts (user-confirmed only)
_(none)_

## Compressed conversation
T1 — user: "" → P1 G0:X1
T2 — user: "Car selling app" → P1 G0:X1 G6:X1 Q7
T3 — user: "Peer-to-peer marketplace connecting private car sellers with buyers — mobile-fir…" → P2 G1:X1 G4:X1 G6:X1 L1 R3 S2 Q7
T4 — user: "MVP: create a listing with photos, browse and search listings, contact the selle…" → P3 G3:X1 G6:X2 G8:X1 GA:X4 L1 L4 R3 S2 Q7
T5 — user: "Trust is critical: light seller verification, report listing, and safety guidanc…" → P3 G1:X1 G8:X1 GA:X4 L1 L4 R3 S2 Q7
T6 — user: "Price is manual negotiation only — no automated pricing, auctions, or instant of…" → P3 G6:X2 G8:X1 GA:X4 L1 L4 R3 S2 Q7
T7 — user: "Out of scope for v1: financing, shipping, professional inspections, and dealer f…" → P3 G6:X2 G7:X1 L1 L4 R3 S2 Q7
T8 — user: "Success means a completed sale handoff (buyer marks sold) and sellers who relist…" → P3 G2:X5 G5:X1 G6:X2 L1 L4 R3 S2 Q7


--- NEW USER INPUT (SOURCE OF TRUTH THIS TURN) ---
Primary users: individuals selling one personal vehicle; buyers searching locally within about 50km.

```

#### <a id="turn-09-output"></a> 2 — Output

```text
P3 G1:X1 G2:X5 G6:X2 G7:X1 L1 L4 R3 S2 Q7
```

---

## Turn 10 — 2026-05-24T09:58:04.948558+00:00

**Model:** `gpt-4o-mini` · prep 0 ms · API wait 1425 ms

| # | What was sent to the LLM | Output | Token spend (input / output) | Total response time |
|---|--------------------------|--------|------------------------------|---------------------|
| **10** | [9,659 chars — expand](#turn-10-sent) | [47 chars — expand](#turn-10-output) | **2,506 / 32** (Σ 2,538) | **1424.8 ms** (1.425 s) |

#### <a id="turn-10-sent"></a> 1 — What was sent to the LLM

```text
=== SYSTEM — llm-rubric.md only (7,583 chars) ===

Discovery State Codes — v0.1 (47 codes)

What this is: a closed vocabulary the model emits to declare its read of the
discovery, after reasoning in full against the discovery rubric. The codes do not
replace judgment — they make it legible, enforceable, and continuous.
Source of truth: the user's pitch and answers ONLY. The code profile is derived
from user input each turn, never from the model's own prior output. The model's
emitted codes are a projection of user truth, not a separate memory.
Hard line: codes are OUTPUT, never INPUT. The model reads the rubric, assesses the
conversation, then emits codes. It must never generate questions mechanically from
codes while skipping the rubric.


⚠ Risk taxonomy — PROVISIONAL (confirm before relying on this)
Every G, L, and R code points at one of these shippability killers. These are
derived from the rubric's 14 dimensions, not confirmed by the product owner. If the
real "what kills a build" list differs, replace this block and the G/L/R codes re-point.

WRONG_THING — user / problem unproven → you build what nobody needs
BOUNDLESS — scope undefined → you build forever, never ship
UNMEASURABLE — no success signal → you can't tell if it worked
FRAGILE — failure / edge modes unhandled → it breaks in prod
BUILT_ON_SAND — assumptions unconfirmed → foundation collapses
UNGOVERNED — runtime / human-review / policy gaps → ships but can't be operated safely


G — Gap pointers (the 12 angles, recast as live risk exposures)
Each marks an unclosed risk and points at the question that closes it.
CodeEmit-meaningRisk classQuestion it drivesG1user unproven riskWRONG_THINGwho exactly, concretelyG2outcome unproven riskWRONG_THINGwhat job, measurablyG3entry unproven riskBOUNDLESShow use beginsG4workflow unproven riskBOUNDLESSthe one core pathG5success undefined riskUNMEASURABLEwhat proves it workedG6scope unbounded riskBOUNDLESSin vs out, v1G7domain rule riskUNGOVERNEDwhat constraint bindsG8failure unhandled riskFRAGILEwhat happens brokenG9tradeoff unsettled riskBOUNDLESSwhich competing optionGAassumption unconfirmed riskBUILT_ON_SANDbelieve vs provenGBruntime policy riskUNGOVERNEDhow it operates liveGChuman review riskUNGOVERNEDwhere humans intervene
Open-class gap (catches risk the taxonomy can't name)
CodeEmit-meaningForcesG0unnamed risk senseda shippability risk no G1–GC fits — model MUST name it in narrative and propose an angle. Each G0 is a signal your taxonomy has a hole — log it.

X — Exposure (how hot is each gap; derived from user input only)
Attach to a gap code, e.g. G6:X2 = scope answered-but-thin.
CodeEmit-meaningRisk meaning / next moveX1open never touchedfull risk live; strong candidate to askX2answered but thinrisk MASKED not closed; press one follow-upX3answered with substancerisk genuinely lowered; stop askingX4inferred not confirmedhidden risk (sand); convert to confirming MCQX5user-settled hardrisk closed by user; lock, never re-askX6contradicted by latestprior closure undermined by new user input; reopen (no amend machinery — recompute yields this)X7answer revealed newriska pick exposed a risk the batch wasn't probing; reopens selection this turnX8user volunteered offanglefree-text beyond the MCQ → primary signal, not noise; may spawn a new angle

P — Phase (macro gear; advances on user-input conditions)
CodeEmit-meaningGate / effectP1dumping not probingbrain_dump; no MCQs; invite source materialP2choosing the pacemode_choice; no MCQs; offer fast vs coachingP3closing the gapselicitation; emit risk-ranked MCQ batchP4sealing the briefclosure; no MCQs; render brief from settled risks

L — Leverage (how the profile ranks the highest painpoint)
CodeEmit-meaningEffectL1killer beats nicetyrank WRONG_THING / BOUNDLESS gaps above polishL2unlocks many dimensionsprefer the gap that closes several at onceL3sand before structureconfirm X4 assumptions before building furtherL4one blocker firstif a blocker exists, confirm it before breadthL5thin masks dangertreat X2 as risk, not progressL6nothing open stopno live risk remains → advance phaseL7reframe beats coveragehighest-leverage move is a reframe, not the next ranked gap → permit off-profile question

R — Readiness (risk-weighted; keeps "shippable" honest)
CodeEmit-meaningEffectR1name risks firstlist live risks before any percentR2pick-only caps lowMCQ-only-closed gap → dimension ≤ 65R3unconfirmed caps hardopen X4/X6 present → ready_capped held downR4killers block shipany open killer-class gap → cannot exceed ~80R5shippable needs proof≥88 only when killers all X3/X5, ≥12 closed

S — Safe-question shaping (let the user think; choose risk-free)
CodeEmit-meaningEffectS1concrete not abstractoptions are real choices, not "tell me more"S2lowest-risk default visibleinclude the safe/conservative option explicitlyS3one decision eachone question closes one risk; no compound asksS4something-else opens subriska "something else" pick spawns a <parent>__<sub> angle at X1, ranked high — the user found the gap, honour itS5name the tradeoffwhen options compete, state what each costs

Q — Batch discipline (enforced on emitted codes)
CodeEmit-meaningCheckQ1one primary turnsingle lead question unless confirming a blockerQ2no theme repeatdrop any angle already X3/X5Q3no batch collisionno two batch items share a gap codeQ4drop paraphrase askeddrop items paraphrasing prior questionsQ5highest leverage firstorder batch by dimensions-unlockedQ6fewer than fiveif <5 live risks open, ask only those — never padQ7one open probereserve ONE batch item for a non-G-derived question the model judges valuable (guarantees a serendipity slot every turn)

C — Coaching voice (the BA tone, made legible)
CodeEmit-meaningNarrative effectC1acknowledge then reflectopen with warm ack + reflect understandingC2push thin answerstress-test follow-up on an X2 themeC3narrate the decisionone-line "Got it — X. Logged." on each X5C4request source materialbrain_dump only: ask for memos / decks / threadsC5offer two pathsmode_choice only: present fast vs coaching

Count
12 gap + 1 open-gap + 8 exposure + 4 phase + 7 leverage + 5 readiness + 5 shaping

7 batch + 5 coaching = 47 + the open-gap G0 folded in = 54 line items across 47 distinct
behavioural codes. (Exposure flags X1–X8 attach to gaps rather than standing alone, so
the emittable behavioural set is the 47 you approved; the X-flags are modifiers.)


RUBRIC ADDITION — paste into the discovery rubric

Emit your assessment as state codes.
After you have reasoned in full against this rubric — assessing the live discovery the
way a senior BA would — also emit a single line of state codes that declares your read.
Attach an exposure flag to each gap (e.g. G6:X2). The codes are a projection of the
user's input, not a memory of your own prior turns: derive them only from what the user
has actually said and picked.
The codes do not decide your questions — your BA judgment does. Use them to (1) mark
which shippability risks are still live, (2) rank which painpoint most threatens a
shippable build, and (3) shape MCQs that let the user commit to the lowest-risk path.
If you sense a risk no gap code names, emit G0 and articulate it. Every elicitation
turn must include one open probe (Q7) — a question the code profile did not generate.
Example emitted line:
P3 G1:X5 G4:X3 G6:X2 G8:X1 GA:X4 L1 L3 L5 R3 S2 Q7
→ elicitation; user & workflow closed; scope thin (press it); failure-modes wide open;
one assumption built-on-sand to confirm; rank killers, confirm the sand, treat thin as
danger; readiness held by the unconfirmed; surface the safe default; reserve an open probe.

=== USER — turn context (1,980 chars) ===

TURN 10

Apply the rubric in the system message. User input is source of truth; recompute codes each turn.
Enabled output sections: state_codes

--- OUTPUT FORMAT (this turn) ---
Output ONLY one line of state codes — no markdown headers, no prose.
Example: P3 G1:X1 G4:X2 G6:X1 L1 L4 R3 S2 Q1 Q7
Reason against the rubric internally; emit codes only.


--- SESSION MEMORY (includes compressed conversation; recompute codes from user truth) ---
# Discovery memory

> Patched after each LLM turn. **User messages are source of truth** — treat assistant
> codes below as the last declared read, then recompute from all user input each turn.

## Pitch
## Latest state codes
_(none)_

## Latest state codes
P3 G1:X1 G2:X5 G6:X2 G7:X1 L1 L4 R3 S2 Q7

## Settled facts (user-confirmed only)
_(none)_

## Compressed conversation
T1 — user: "" → P1 G0:X1
T2 — user: "Car selling app" → P1 G0:X1 G6:X1 Q7
T3 — user: "Peer-to-peer marketplace connecting private car sellers with buyers — mobile-fir…" → P2 G1:X1 G4:X1 G6:X1 L1 R3 S2 Q7
T4 — user: "MVP: create a listing with photos, browse and search listings, contact the selle…" → P3 G3:X1 G6:X2 G8:X1 GA:X4 L1 L4 R3 S2 Q7
T5 — user: "Trust is critical: light seller verification, report listing, and safety guidanc…" → P3 G1:X1 G8:X1 GA:X4 L1 L4 R3 S2 Q7
T6 — user: "Price is manual negotiation only — no automated pricing, auctions, or instant of…" → P3 G6:X2 G8:X1 GA:X4 L1 L4 R3 S2 Q7
T7 — user: "Out of scope for v1: financing, shipping, professional inspections, and dealer f…" → P3 G6:X2 G7:X1 L1 L4 R3 S2 Q7
T8 — user: "Success means a completed sale handoff (buyer marks sold) and sellers who relist…" → P3 G2:X5 G5:X1 G6:X2 L1 L4 R3 S2 Q7
T9 — user: "Primary users: individuals selling one personal vehicle; buyers searching locall…" → P3 G1:X1 G2:X5 G6:X2 G7:X1 L1 L4 R3 S2 Q7


--- NEW USER INPUT (SOURCE OF TRUTH THIS TURN) ---
Biggest risk to avoid: scams and unsafe meetups — optimise for fraud prevention over user growth.

```

#### <a id="turn-10-output"></a> 2 — Output

```text
P3 G1:X1 G2:X5 G6:X2 G7:X1 G8:X1 L1 L4 R3 S2 Q7
```
