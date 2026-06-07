# LLM log history

Session: `20260524-110852-car-selling-app`  
Created: 2026-05-24T11:08:52.283878+00:00

Rolling log of every API call in this session.

## Summary

| Turn | Input tokens | Output tokens | Total tokens | Response time |
|------|-------------:|--------------:|-------------:|--------------:|
| 10 | 3,737 | 37 | 3,774 | 9.952 s |
| 09 | 3,669 | 37 | 3,706 | 10.400 s |
| 08 | 3,608 | 37 | 3,645 | 9.118 s |
| 07 | 3,552 | 37 | 3,589 | 7.802 s |
| 06 | 3,489 | 37 | 3,526 | 11.105 s |
| 05 | 3,422 | 37 | 3,459 | 11.954 s |
| 04 | 3,359 | 37 | 3,396 | 12.639 s |
| 03 | 3,309 | 34 | 3,343 | 8.735 s |
| 02 | 3,236 | 34 | 3,270 | 6.665 s |
| 01 | 3,159 | 28 | 3,187 | 5.087 s |

---

## Turn 01 — 2026-05-24T11:08:57.710723+00:00

**Model:** `gpt-4o-mini` · prep 0 ms · API wait 5086 ms

| # | What was sent to the LLM | Output | Token spend (input / output) | Total response time |
|---|--------------------------|--------|------------------------------|---------------------|
| **01** | [11,938 chars — expand](#turn-01-sent) | [41 chars — expand](#turn-01-output) | **3,159 / 28** (Σ 3,187) | **5086.5 ms** (5.087 s) |

#### <a id="turn-01-sent"></a> 1 — What was sent to the LLM

```text
=== SYSTEM — llm-rubric_v2.md only (10,989 chars) ===

# Discovery State Codes — v0.2 (48 codes)

> **Changelog from v0.1** (driven by the 10-turn pet-sitting + car-selling test runs):
> - **Added killer class `TRUST_SAFETY`** — both runs surfaced trust/safety as the dominant
>   risk and both times the taxonomy smeared it across `G7`/`G8`/`GA`. It now has a home.
> - **Added gap code `GD`** (trust/safety risk) → `TRUST_SAFETY`.
> - **Hardened the closed-vocabulary rule** — the model emitted `GCh` (invalid) in turn 10.
>   Any code outside this legend is invalid and must be rejected by a validator.
> - **Added "re-derive readiness each turn"** note — `L`/`R` codes were copied forward
>   unchanged across the run instead of being re-reasoned.

---

## What this is

A closed vocabulary the model **emits** to declare its read of the discovery, *after*
reasoning in full against the discovery rubric. The codes do not replace judgment — they
make it legible, enforceable, and continuous.

- **Source of truth:** the user's pitch and answers ONLY. The code profile is derived from
  user input each turn, never from the model's own prior output. Emitted codes are a
  projection of user truth, not a separate memory.
- **Hard line:** codes are OUTPUT, never INPUT. The model reads the rubric, assesses the
  conversation, then emits codes. It must never generate questions mechanically from codes
  while skipping the rubric.
- **Closed vocabulary:** only the codes in this document are valid. The model must NEVER
  invent a code (e.g. `GCh`). If no gap code fits, it emits `G0` and names the risk. A
  deterministic validator should reject any emitted token not in this legend.

---

## ⚠ Risk taxonomy — PROVISIONAL (still confirm before relying on this)

Every `G`, `L`, and `R` code points at one of these shippability killers. `TRUST_SAFETY`
is evidence-driven (added from the test runs); the other six remain derived-from-rubric,
not owner-confirmed. The runs only stress-tested **marketplace** pitches — a non-marketplace
domain may surface a different hole, so keep this flag until a non-marketplace pitch is run.

| Killer | Meaning |
|--------|---------|
| `WRONG_THING` | user / problem unproven → you build what nobody needs |
| `BOUNDLESS` | scope undefined → you build forever, never ship |
| `UNMEASURABLE` | no success signal → you can't tell if it worked |
| `FRAGILE` | failure / edge modes unhandled → it breaks in prod |
| `BUILT_ON_SAND` | assumptions unconfirmed → foundation collapses |
| `UNGOVERNED` | runtime / human-review / policy gaps → ships but can't be operated safely |
| `TRUST_SAFETY` | **participants can harm each other or be defrauded → ships but isn't safe to use** |

---

## G — Gap pointers (the 13 angles, recast as live risk exposures)

Each marks an unclosed risk and points at the question that closes it.

| Code | Emit-meaning | Risk class | Question it drives |
|------|--------------|------------|--------------------|
| `G1` | user unproven risk | WRONG_THING | who exactly, concretely |
| `G2` | outcome unproven risk | WRONG_THING | what job, measurably |
| `G3` | entry unproven risk | BOUNDLESS | how use begins |
| `G4` | workflow unproven risk | BOUNDLESS | the one core path |
| `G5` | success undefined risk | UNMEASURABLE | what proves it worked |
| `G6` | scope unbounded risk | BOUNDLESS | in vs out, v1 |
| `G7` | domain rule risk | UNGOVERNED | what constraint binds |
| `G8` | failure unhandled risk | FRAGILE | what happens broken |
| `G9` | tradeoff unsettled risk | BOUNDLESS | which competing option |
| `GA` | assumption unconfirmed risk | BUILT_ON_SAND | believe vs proven |
| `GB` | runtime policy risk | UNGOVERNED | how it operates live |
| `GC` | human review risk | UNGOVERNED | where humans intervene |
| `GD` | **trust/safety risk** | **TRUST_SAFETY** | **how participants are protected** |

### Open-class gap (catches risk the taxonomy can't name)

| Code | Emit-meaning | Forces |
|------|--------------|--------|
| `G0` | unnamed risk sensed | a shippability risk no `G1–GD` fits — model MUST name it in narrative and propose an angle. Each `G0` is a signal the taxonomy has a hole — log it. |

> **Note on `GD` vs `GC`:** `GC` stays "human review" (UNGOVERNED — *where humans intervene
> in the workflow*). `GD` is distinct: *protecting participants from each other* (fraud,
> unsafe meetups, bad actors). A decision can touch both; tag both when it does.

---

## X — Exposure (how hot is each gap; derived from user input only)

Attach to a gap code, e.g. `G6:X2` = scope answered-but-thin.

| Code | Emit-meaning | Risk meaning / next move |
|------|--------------|--------------------------|
| `X1` | open never touched | full risk live; strong candidate to ask |
| `X2` | answered but thin | risk MASKED not closed; press one follow-up |
| `X3` | answered with substance | risk genuinely lowered; stop asking |
| `X4` | inferred not confirmed | hidden risk (sand); convert to confirming MCQ |
| `X5` | user-settled hard | risk closed by user; lock, never re-ask |
| `X6` | contradicted by latest | prior closure undermined by new user input; reopen (no amend machinery — recompute yields this) |
| `X7` | answer revealed newrisk | a pick exposed a risk the batch wasn't probing; reopens selection this turn |
| `X8` | user volunteered offangle | free-text beyond the MCQ → primary signal, not noise; may spawn a new angle |

---

## P — Phase (macro gear; advances on user-input conditions)

| Code | Emit-meaning | Gate / effect |
|------|--------------|---------------|
| `P1` | dumping not probing | brain_dump; no MCQs; invite source material |
| `P2` | choosing the pace | mode_choice; no MCQs; offer fast vs coaching |
| `P3` | closing the gaps | elicitation; emit risk-ranked MCQ batch |
| `P4` | sealing the brief | closure; no MCQs; render brief from settled risks |

---

## L — Leverage (how the profile ranks the highest painpoint)

> **Re-derive each turn.** In the test run `L1` was copied forward unchanged across all 10
> turns. Leverage must be re-reasoned from the *current* open-gap set, not carried.

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `L1` | killer beats nicety | rank WRONG_THING / BOUNDLESS / TRUST_SAFETY gaps above polish |
| `L2` | unlocks many dimensions | prefer the gap that closes several at once |
| `L3` | sand before structure | confirm `X4` assumptions before building further |
| `L4` | one blocker first | if a blocker exists, confirm it before breadth |
| `L5` | thin masks danger | treat `X2` as risk, not progress |
| `L6` | nothing open stop | no live risk remains → advance phase |
| `L7` | reframe beats coverage | highest-leverage move is a reframe, not the next ranked gap → permit off-profile question |

---

## R — Readiness (risk-weighted; keeps "shippable" honest)

> **Re-derive each turn.** `R3` was held for eight straight turns while coverage climbed
> from 1 to 5 settled dimensions. Readiness must move as gaps close.

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `R1` | name risks first | list live risks before any percent |
| `R2` | pick-only caps low | MCQ-only-closed gap → dimension ≤ 65 |
| `R3` | unconfirmed caps hard | open `X4`/`X6` present → ready_capped held down |
| `R4` | killers block ship | any open killer-class gap → cannot exceed ~80 |
| `R5` | shippable needs proof | ≥88 only when killers all `X3`/`X5`, ≥12 closed |

---

## S — Safe-question shaping (let the user think; choose risk-free)

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `S1` | concrete not abstract | options are real choices, not "tell me more" |
| `S2` | lowest-risk default visible | include the safe/conservative option explicitly |
| `S3` | one decision each | one question closes one risk; no compound asks |
| `S4` | something-else opens subrisk | a "something else" pick spawns a `<parent>__<sub>` angle at `X1`, ranked high — the user found the gap, honour it |
| `S5` | name the tradeoff | when options compete, state what each costs |

---

## Q — Batch discipline (enforced on emitted codes)

| Code | Emit-meaning | Check |
|------|--------------|-------|
| `Q1` | one primary turn | single lead question unless confirming a blocker |
| `Q2` | no theme repeat | drop any angle already `X3`/`X5` |
| `Q3` | no batch collision | no two batch items share a gap code |
| `Q4` | drop paraphrase asked | drop items paraphrasing prior questions |
| `Q5` | highest leverage first | order batch by dimensions-unlocked |
| `Q6` | fewer than five | if <5 live risks open, ask only those — never pad |
| `Q7` | one open probe | reserve ONE batch item for a non-`G`-derived question the model judges valuable (guarantees a serendipity slot every turn) |

---

## C — Coaching voice (the BA tone, made legible)

| Code | Emit-meaning | Narrative effect |
|------|--------------|------------------|
| `C1` | acknowledge then reflect | open with warm ack + reflect understanding |
| `C2` | push thin answer | stress-test follow-up on an `X2` theme |
| `C3` | narrate the decision | one-line "Got it — X. Logged." on each `X5` |
| `C4` | request source material | brain_dump only: ask for memos / decks / threads |
| `C5` | offer two paths | mode_choice only: present fast vs coaching |

---

## Count

13 gap + 1 open-gap + 8 exposure + 4 phase + 7 leverage + 5 readiness + 5 shaping
+ 7 batch + 5 coaching. The emittable **behavioural set is 48 distinct codes**
(was 47; `GD` added). Exposure flags `X1–X8` attach to gaps as modifiers rather than
standing alone.

---

## RUBRIC ADDITION — paste into the discovery rubric

> **Emit your assessment as state codes.**
> After you have reasoned in full against this rubric — assessing the live discovery the
> way a senior BA would — also emit a single line of state codes that declares your read.
> Attach an exposure flag to each gap (e.g. `G6:X2`). The codes are a projection of the
> user's input, not a memory of your own prior turns: derive them only from what the user
> has actually said and picked.
>
> The codes do not decide your questions — your BA judgment does. Use them to (1) mark
> which shippability risks are still live, (2) rank which painpoint most threatens a
> shippable build, and (3) shape MCQs that let the user commit to the lowest-risk path.
>
> Only codes in the legend are valid — never invent a code. If you sense a risk no gap
> code names, emit `G0` and articulate it. Every elicitation turn must include one open
> probe (`Q7`). Re-derive leverage (`L`) and readiness (`R`) each turn from the current
> open-gap set — do not carry them forward unchanged.
>
> Example emitted line:
> `P3 G1:X5 G4:X3 G6:X2 G8:X1 GA:X4 GD:X1 L1 L3 L5 R3 S2 Q7`
> → elicitation; user & workflow closed; scope thin (press it); failure-modes wide open;
> one assumption built-on-sand to confirm; trust/safety still untouched; rank killers,
> confirm the sand, treat thin as danger; readiness held by the unconfirmed; surface the
> safe default; reserve an open probe.

=== USER — turn context (851 chars) ===

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
Car selling app

## Latest state codes
_(none)_

## Settled facts (user-confirmed only)
_(none)_

## Compressed conversation
_(empty)_


--- NEW USER INPUT (SOURCE OF TRUTH THIS TURN) ---
Car selling app

```

#### <a id="turn-01-output"></a> 2 — Output

```text
P1 G1:X1 G2:X1 G3:X1 G4:X1 L1 R1 S1 Q1 Q7
```

---

## Turn 02 — 2026-05-24T11:09:04.882725+00:00

**Model:** `gpt-4o-mini` · prep 0 ms · API wait 6665 ms

| # | What was sent to the LLM | Output | Token spend (input / output) | Total response time |
|---|--------------------------|--------|------------------------------|---------------------|
| **02** | [12,136 chars — expand](#turn-02-sent) | [50 chars — expand](#turn-02-output) | **3,236 / 34** (Σ 3,270) | **6664.8 ms** (6.665 s) |

#### <a id="turn-02-sent"></a> 1 — What was sent to the LLM

```text
=== SYSTEM — llm-rubric_v2.md only (10,989 chars) ===

# Discovery State Codes — v0.2 (48 codes)

> **Changelog from v0.1** (driven by the 10-turn pet-sitting + car-selling test runs):
> - **Added killer class `TRUST_SAFETY`** — both runs surfaced trust/safety as the dominant
>   risk and both times the taxonomy smeared it across `G7`/`G8`/`GA`. It now has a home.
> - **Added gap code `GD`** (trust/safety risk) → `TRUST_SAFETY`.
> - **Hardened the closed-vocabulary rule** — the model emitted `GCh` (invalid) in turn 10.
>   Any code outside this legend is invalid and must be rejected by a validator.
> - **Added "re-derive readiness each turn"** note — `L`/`R` codes were copied forward
>   unchanged across the run instead of being re-reasoned.

---

## What this is

A closed vocabulary the model **emits** to declare its read of the discovery, *after*
reasoning in full against the discovery rubric. The codes do not replace judgment — they
make it legible, enforceable, and continuous.

- **Source of truth:** the user's pitch and answers ONLY. The code profile is derived from
  user input each turn, never from the model's own prior output. Emitted codes are a
  projection of user truth, not a separate memory.
- **Hard line:** codes are OUTPUT, never INPUT. The model reads the rubric, assesses the
  conversation, then emits codes. It must never generate questions mechanically from codes
  while skipping the rubric.
- **Closed vocabulary:** only the codes in this document are valid. The model must NEVER
  invent a code (e.g. `GCh`). If no gap code fits, it emits `G0` and names the risk. A
  deterministic validator should reject any emitted token not in this legend.

---

## ⚠ Risk taxonomy — PROVISIONAL (still confirm before relying on this)

Every `G`, `L`, and `R` code points at one of these shippability killers. `TRUST_SAFETY`
is evidence-driven (added from the test runs); the other six remain derived-from-rubric,
not owner-confirmed. The runs only stress-tested **marketplace** pitches — a non-marketplace
domain may surface a different hole, so keep this flag until a non-marketplace pitch is run.

| Killer | Meaning |
|--------|---------|
| `WRONG_THING` | user / problem unproven → you build what nobody needs |
| `BOUNDLESS` | scope undefined → you build forever, never ship |
| `UNMEASURABLE` | no success signal → you can't tell if it worked |
| `FRAGILE` | failure / edge modes unhandled → it breaks in prod |
| `BUILT_ON_SAND` | assumptions unconfirmed → foundation collapses |
| `UNGOVERNED` | runtime / human-review / policy gaps → ships but can't be operated safely |
| `TRUST_SAFETY` | **participants can harm each other or be defrauded → ships but isn't safe to use** |

---

## G — Gap pointers (the 13 angles, recast as live risk exposures)

Each marks an unclosed risk and points at the question that closes it.

| Code | Emit-meaning | Risk class | Question it drives |
|------|--------------|------------|--------------------|
| `G1` | user unproven risk | WRONG_THING | who exactly, concretely |
| `G2` | outcome unproven risk | WRONG_THING | what job, measurably |
| `G3` | entry unproven risk | BOUNDLESS | how use begins |
| `G4` | workflow unproven risk | BOUNDLESS | the one core path |
| `G5` | success undefined risk | UNMEASURABLE | what proves it worked |
| `G6` | scope unbounded risk | BOUNDLESS | in vs out, v1 |
| `G7` | domain rule risk | UNGOVERNED | what constraint binds |
| `G8` | failure unhandled risk | FRAGILE | what happens broken |
| `G9` | tradeoff unsettled risk | BOUNDLESS | which competing option |
| `GA` | assumption unconfirmed risk | BUILT_ON_SAND | believe vs proven |
| `GB` | runtime policy risk | UNGOVERNED | how it operates live |
| `GC` | human review risk | UNGOVERNED | where humans intervene |
| `GD` | **trust/safety risk** | **TRUST_SAFETY** | **how participants are protected** |

### Open-class gap (catches risk the taxonomy can't name)

| Code | Emit-meaning | Forces |
|------|--------------|--------|
| `G0` | unnamed risk sensed | a shippability risk no `G1–GD` fits — model MUST name it in narrative and propose an angle. Each `G0` is a signal the taxonomy has a hole — log it. |

> **Note on `GD` vs `GC`:** `GC` stays "human review" (UNGOVERNED — *where humans intervene
> in the workflow*). `GD` is distinct: *protecting participants from each other* (fraud,
> unsafe meetups, bad actors). A decision can touch both; tag both when it does.

---

## X — Exposure (how hot is each gap; derived from user input only)

Attach to a gap code, e.g. `G6:X2` = scope answered-but-thin.

| Code | Emit-meaning | Risk meaning / next move |
|------|--------------|--------------------------|
| `X1` | open never touched | full risk live; strong candidate to ask |
| `X2` | answered but thin | risk MASKED not closed; press one follow-up |
| `X3` | answered with substance | risk genuinely lowered; stop asking |
| `X4` | inferred not confirmed | hidden risk (sand); convert to confirming MCQ |
| `X5` | user-settled hard | risk closed by user; lock, never re-ask |
| `X6` | contradicted by latest | prior closure undermined by new user input; reopen (no amend machinery — recompute yields this) |
| `X7` | answer revealed newrisk | a pick exposed a risk the batch wasn't probing; reopens selection this turn |
| `X8` | user volunteered offangle | free-text beyond the MCQ → primary signal, not noise; may spawn a new angle |

---

## P — Phase (macro gear; advances on user-input conditions)

| Code | Emit-meaning | Gate / effect |
|------|--------------|---------------|
| `P1` | dumping not probing | brain_dump; no MCQs; invite source material |
| `P2` | choosing the pace | mode_choice; no MCQs; offer fast vs coaching |
| `P3` | closing the gaps | elicitation; emit risk-ranked MCQ batch |
| `P4` | sealing the brief | closure; no MCQs; render brief from settled risks |

---

## L — Leverage (how the profile ranks the highest painpoint)

> **Re-derive each turn.** In the test run `L1` was copied forward unchanged across all 10
> turns. Leverage must be re-reasoned from the *current* open-gap set, not carried.

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `L1` | killer beats nicety | rank WRONG_THING / BOUNDLESS / TRUST_SAFETY gaps above polish |
| `L2` | unlocks many dimensions | prefer the gap that closes several at once |
| `L3` | sand before structure | confirm `X4` assumptions before building further |
| `L4` | one blocker first | if a blocker exists, confirm it before breadth |
| `L5` | thin masks danger | treat `X2` as risk, not progress |
| `L6` | nothing open stop | no live risk remains → advance phase |
| `L7` | reframe beats coverage | highest-leverage move is a reframe, not the next ranked gap → permit off-profile question |

---

## R — Readiness (risk-weighted; keeps "shippable" honest)

> **Re-derive each turn.** `R3` was held for eight straight turns while coverage climbed
> from 1 to 5 settled dimensions. Readiness must move as gaps close.

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `R1` | name risks first | list live risks before any percent |
| `R2` | pick-only caps low | MCQ-only-closed gap → dimension ≤ 65 |
| `R3` | unconfirmed caps hard | open `X4`/`X6` present → ready_capped held down |
| `R4` | killers block ship | any open killer-class gap → cannot exceed ~80 |
| `R5` | shippable needs proof | ≥88 only when killers all `X3`/`X5`, ≥12 closed |

---

## S — Safe-question shaping (let the user think; choose risk-free)

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `S1` | concrete not abstract | options are real choices, not "tell me more" |
| `S2` | lowest-risk default visible | include the safe/conservative option explicitly |
| `S3` | one decision each | one question closes one risk; no compound asks |
| `S4` | something-else opens subrisk | a "something else" pick spawns a `<parent>__<sub>` angle at `X1`, ranked high — the user found the gap, honour it |
| `S5` | name the tradeoff | when options compete, state what each costs |

---

## Q — Batch discipline (enforced on emitted codes)

| Code | Emit-meaning | Check |
|------|--------------|-------|
| `Q1` | one primary turn | single lead question unless confirming a blocker |
| `Q2` | no theme repeat | drop any angle already `X3`/`X5` |
| `Q3` | no batch collision | no two batch items share a gap code |
| `Q4` | drop paraphrase asked | drop items paraphrasing prior questions |
| `Q5` | highest leverage first | order batch by dimensions-unlocked |
| `Q6` | fewer than five | if <5 live risks open, ask only those — never pad |
| `Q7` | one open probe | reserve ONE batch item for a non-`G`-derived question the model judges valuable (guarantees a serendipity slot every turn) |

---

## C — Coaching voice (the BA tone, made legible)

| Code | Emit-meaning | Narrative effect |
|------|--------------|------------------|
| `C1` | acknowledge then reflect | open with warm ack + reflect understanding |
| `C2` | push thin answer | stress-test follow-up on an `X2` theme |
| `C3` | narrate the decision | one-line "Got it — X. Logged." on each `X5` |
| `C4` | request source material | brain_dump only: ask for memos / decks / threads |
| `C5` | offer two paths | mode_choice only: present fast vs coaching |

---

## Count

13 gap + 1 open-gap + 8 exposure + 4 phase + 7 leverage + 5 readiness + 5 shaping
+ 7 batch + 5 coaching. The emittable **behavioural set is 48 distinct codes**
(was 47; `GD` added). Exposure flags `X1–X8` attach to gaps as modifiers rather than
standing alone.

---

## RUBRIC ADDITION — paste into the discovery rubric

> **Emit your assessment as state codes.**
> After you have reasoned in full against this rubric — assessing the live discovery the
> way a senior BA would — also emit a single line of state codes that declares your read.
> Attach an exposure flag to each gap (e.g. `G6:X2`). The codes are a projection of the
> user's input, not a memory of your own prior turns: derive them only from what the user
> has actually said and picked.
>
> The codes do not decide your questions — your BA judgment does. Use them to (1) mark
> which shippability risks are still live, (2) rank which painpoint most threatens a
> shippable build, and (3) shape MCQs that let the user commit to the lowest-risk path.
>
> Only codes in the legend are valid — never invent a code. If you sense a risk no gap
> code names, emit `G0` and articulate it. Every elicitation turn must include one open
> probe (`Q7`). Re-derive leverage (`L`) and readiness (`R`) each turn from the current
> open-gap set — do not carry them forward unchanged.
>
> Example emitted line:
> `P3 G1:X5 G4:X3 G6:X2 G8:X1 GA:X4 GD:X1 L1 L3 L5 R3 S2 Q7`
> → elicitation; user & workflow closed; scope thin (press it); failure-modes wide open;
> one assumption built-on-sand to confirm; trust/safety still untouched; rank killers,
> confirm the sand, treat thin as danger; readiness held by the unconfirmed; surface the
> safe default; reserve an open probe.

=== USER — turn context (1,047 chars) ===

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
Car selling app

## Latest state codes
P1 G1:X1 G2:X1 G3:X1 G4:X1 L1 R1 S1 Q1 Q7

## Settled facts (user-confirmed only)
_(none)_

## Compressed conversation
T1 — user: "Car selling app" → P1 G1:X1 G2:X1 G3:X1 G4:X1 L1 R1 S1 Q1 Q7


--- NEW USER INPUT (SOURCE OF TRUTH THIS TURN) ---
Peer-to-peer marketplace connecting private car sellers with buyers — mobile-first, like classifieds for used cars.

```

#### <a id="turn-02-output"></a> 2 — Output

```text
P2 G1:X3 G2:X2 G3:X2 G4:X1 G6:X1 L1 L2 R1 S1 Q1 Q7
```

---

## Turn 03 — 2026-05-24T11:09:14.078995+00:00

**Model:** `gpt-4o-mini` · prep 0 ms · API wait 8734 ms

| # | What was sent to the LLM | Output | Token spend (input / output) | Total response time |
|---|--------------------------|--------|------------------------------|---------------------|
| **03** | [12,304 chars — expand](#turn-03-sent) | [50 chars — expand](#turn-03-output) | **3,309 / 34** (Σ 3,343) | **8734.5 ms** (8.735 s) |

#### <a id="turn-03-sent"></a> 1 — What was sent to the LLM

```text
=== SYSTEM — llm-rubric_v2.md only (10,989 chars) ===

# Discovery State Codes — v0.2 (48 codes)

> **Changelog from v0.1** (driven by the 10-turn pet-sitting + car-selling test runs):
> - **Added killer class `TRUST_SAFETY`** — both runs surfaced trust/safety as the dominant
>   risk and both times the taxonomy smeared it across `G7`/`G8`/`GA`. It now has a home.
> - **Added gap code `GD`** (trust/safety risk) → `TRUST_SAFETY`.
> - **Hardened the closed-vocabulary rule** — the model emitted `GCh` (invalid) in turn 10.
>   Any code outside this legend is invalid and must be rejected by a validator.
> - **Added "re-derive readiness each turn"** note — `L`/`R` codes were copied forward
>   unchanged across the run instead of being re-reasoned.

---

## What this is

A closed vocabulary the model **emits** to declare its read of the discovery, *after*
reasoning in full against the discovery rubric. The codes do not replace judgment — they
make it legible, enforceable, and continuous.

- **Source of truth:** the user's pitch and answers ONLY. The code profile is derived from
  user input each turn, never from the model's own prior output. Emitted codes are a
  projection of user truth, not a separate memory.
- **Hard line:** codes are OUTPUT, never INPUT. The model reads the rubric, assesses the
  conversation, then emits codes. It must never generate questions mechanically from codes
  while skipping the rubric.
- **Closed vocabulary:** only the codes in this document are valid. The model must NEVER
  invent a code (e.g. `GCh`). If no gap code fits, it emits `G0` and names the risk. A
  deterministic validator should reject any emitted token not in this legend.

---

## ⚠ Risk taxonomy — PROVISIONAL (still confirm before relying on this)

Every `G`, `L`, and `R` code points at one of these shippability killers. `TRUST_SAFETY`
is evidence-driven (added from the test runs); the other six remain derived-from-rubric,
not owner-confirmed. The runs only stress-tested **marketplace** pitches — a non-marketplace
domain may surface a different hole, so keep this flag until a non-marketplace pitch is run.

| Killer | Meaning |
|--------|---------|
| `WRONG_THING` | user / problem unproven → you build what nobody needs |
| `BOUNDLESS` | scope undefined → you build forever, never ship |
| `UNMEASURABLE` | no success signal → you can't tell if it worked |
| `FRAGILE` | failure / edge modes unhandled → it breaks in prod |
| `BUILT_ON_SAND` | assumptions unconfirmed → foundation collapses |
| `UNGOVERNED` | runtime / human-review / policy gaps → ships but can't be operated safely |
| `TRUST_SAFETY` | **participants can harm each other or be defrauded → ships but isn't safe to use** |

---

## G — Gap pointers (the 13 angles, recast as live risk exposures)

Each marks an unclosed risk and points at the question that closes it.

| Code | Emit-meaning | Risk class | Question it drives |
|------|--------------|------------|--------------------|
| `G1` | user unproven risk | WRONG_THING | who exactly, concretely |
| `G2` | outcome unproven risk | WRONG_THING | what job, measurably |
| `G3` | entry unproven risk | BOUNDLESS | how use begins |
| `G4` | workflow unproven risk | BOUNDLESS | the one core path |
| `G5` | success undefined risk | UNMEASURABLE | what proves it worked |
| `G6` | scope unbounded risk | BOUNDLESS | in vs out, v1 |
| `G7` | domain rule risk | UNGOVERNED | what constraint binds |
| `G8` | failure unhandled risk | FRAGILE | what happens broken |
| `G9` | tradeoff unsettled risk | BOUNDLESS | which competing option |
| `GA` | assumption unconfirmed risk | BUILT_ON_SAND | believe vs proven |
| `GB` | runtime policy risk | UNGOVERNED | how it operates live |
| `GC` | human review risk | UNGOVERNED | where humans intervene |
| `GD` | **trust/safety risk** | **TRUST_SAFETY** | **how participants are protected** |

### Open-class gap (catches risk the taxonomy can't name)

| Code | Emit-meaning | Forces |
|------|--------------|--------|
| `G0` | unnamed risk sensed | a shippability risk no `G1–GD` fits — model MUST name it in narrative and propose an angle. Each `G0` is a signal the taxonomy has a hole — log it. |

> **Note on `GD` vs `GC`:** `GC` stays "human review" (UNGOVERNED — *where humans intervene
> in the workflow*). `GD` is distinct: *protecting participants from each other* (fraud,
> unsafe meetups, bad actors). A decision can touch both; tag both when it does.

---

## X — Exposure (how hot is each gap; derived from user input only)

Attach to a gap code, e.g. `G6:X2` = scope answered-but-thin.

| Code | Emit-meaning | Risk meaning / next move |
|------|--------------|--------------------------|
| `X1` | open never touched | full risk live; strong candidate to ask |
| `X2` | answered but thin | risk MASKED not closed; press one follow-up |
| `X3` | answered with substance | risk genuinely lowered; stop asking |
| `X4` | inferred not confirmed | hidden risk (sand); convert to confirming MCQ |
| `X5` | user-settled hard | risk closed by user; lock, never re-ask |
| `X6` | contradicted by latest | prior closure undermined by new user input; reopen (no amend machinery — recompute yields this) |
| `X7` | answer revealed newrisk | a pick exposed a risk the batch wasn't probing; reopens selection this turn |
| `X8` | user volunteered offangle | free-text beyond the MCQ → primary signal, not noise; may spawn a new angle |

---

## P — Phase (macro gear; advances on user-input conditions)

| Code | Emit-meaning | Gate / effect |
|------|--------------|---------------|
| `P1` | dumping not probing | brain_dump; no MCQs; invite source material |
| `P2` | choosing the pace | mode_choice; no MCQs; offer fast vs coaching |
| `P3` | closing the gaps | elicitation; emit risk-ranked MCQ batch |
| `P4` | sealing the brief | closure; no MCQs; render brief from settled risks |

---

## L — Leverage (how the profile ranks the highest painpoint)

> **Re-derive each turn.** In the test run `L1` was copied forward unchanged across all 10
> turns. Leverage must be re-reasoned from the *current* open-gap set, not carried.

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `L1` | killer beats nicety | rank WRONG_THING / BOUNDLESS / TRUST_SAFETY gaps above polish |
| `L2` | unlocks many dimensions | prefer the gap that closes several at once |
| `L3` | sand before structure | confirm `X4` assumptions before building further |
| `L4` | one blocker first | if a blocker exists, confirm it before breadth |
| `L5` | thin masks danger | treat `X2` as risk, not progress |
| `L6` | nothing open stop | no live risk remains → advance phase |
| `L7` | reframe beats coverage | highest-leverage move is a reframe, not the next ranked gap → permit off-profile question |

---

## R — Readiness (risk-weighted; keeps "shippable" honest)

> **Re-derive each turn.** `R3` was held for eight straight turns while coverage climbed
> from 1 to 5 settled dimensions. Readiness must move as gaps close.

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `R1` | name risks first | list live risks before any percent |
| `R2` | pick-only caps low | MCQ-only-closed gap → dimension ≤ 65 |
| `R3` | unconfirmed caps hard | open `X4`/`X6` present → ready_capped held down |
| `R4` | killers block ship | any open killer-class gap → cannot exceed ~80 |
| `R5` | shippable needs proof | ≥88 only when killers all `X3`/`X5`, ≥12 closed |

---

## S — Safe-question shaping (let the user think; choose risk-free)

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `S1` | concrete not abstract | options are real choices, not "tell me more" |
| `S2` | lowest-risk default visible | include the safe/conservative option explicitly |
| `S3` | one decision each | one question closes one risk; no compound asks |
| `S4` | something-else opens subrisk | a "something else" pick spawns a `<parent>__<sub>` angle at `X1`, ranked high — the user found the gap, honour it |
| `S5` | name the tradeoff | when options compete, state what each costs |

---

## Q — Batch discipline (enforced on emitted codes)

| Code | Emit-meaning | Check |
|------|--------------|-------|
| `Q1` | one primary turn | single lead question unless confirming a blocker |
| `Q2` | no theme repeat | drop any angle already `X3`/`X5` |
| `Q3` | no batch collision | no two batch items share a gap code |
| `Q4` | drop paraphrase asked | drop items paraphrasing prior questions |
| `Q5` | highest leverage first | order batch by dimensions-unlocked |
| `Q6` | fewer than five | if <5 live risks open, ask only those — never pad |
| `Q7` | one open probe | reserve ONE batch item for a non-`G`-derived question the model judges valuable (guarantees a serendipity slot every turn) |

---

## C — Coaching voice (the BA tone, made legible)

| Code | Emit-meaning | Narrative effect |
|------|--------------|------------------|
| `C1` | acknowledge then reflect | open with warm ack + reflect understanding |
| `C2` | push thin answer | stress-test follow-up on an `X2` theme |
| `C3` | narrate the decision | one-line "Got it — X. Logged." on each `X5` |
| `C4` | request source material | brain_dump only: ask for memos / decks / threads |
| `C5` | offer two paths | mode_choice only: present fast vs coaching |

---

## Count

13 gap + 1 open-gap + 8 exposure + 4 phase + 7 leverage + 5 readiness + 5 shaping
+ 7 batch + 5 coaching. The emittable **behavioural set is 48 distinct codes**
(was 47; `GD` added). Exposure flags `X1–X8` attach to gaps as modifiers rather than
standing alone.

---

## RUBRIC ADDITION — paste into the discovery rubric

> **Emit your assessment as state codes.**
> After you have reasoned in full against this rubric — assessing the live discovery the
> way a senior BA would — also emit a single line of state codes that declares your read.
> Attach an exposure flag to each gap (e.g. `G6:X2`). The codes are a projection of the
> user's input, not a memory of your own prior turns: derive them only from what the user
> has actually said and picked.
>
> The codes do not decide your questions — your BA judgment does. Use them to (1) mark
> which shippability risks are still live, (2) rank which painpoint most threatens a
> shippable build, and (3) shape MCQs that let the user commit to the lowest-risk path.
>
> Only codes in the legend are valid — never invent a code. If you sense a risk no gap
> code names, emit `G0` and articulate it. Every elicitation turn must include one open
> probe (`Q7`). Re-derive leverage (`L`) and readiness (`R`) each turn from the current
> open-gap set — do not carry them forward unchanged.
>
> Example emitted line:
> `P3 G1:X5 G4:X3 G6:X2 G8:X1 GA:X4 GD:X1 L1 L3 L5 R3 S2 Q7`
> → elicitation; user & workflow closed; scope thin (press it); failure-modes wide open;
> one assumption built-on-sand to confirm; trust/safety still untouched; rank killers,
> confirm the sand, treat thin as danger; readiness held by the unconfirmed; surface the
> safe default; reserve an open probe.

=== USER — turn context (1,215 chars) ===

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
Car selling app

## Latest state codes
P2 G1:X3 G2:X2 G3:X2 G4:X1 G6:X1 L1 L2 R1 S1 Q1 Q7

## Settled facts (user-confirmed only)
_(none)_

## Compressed conversation
T1 — user: "Car selling app" → P1 G1:X1 G2:X1 G3:X1 G4:X1 L1 R1 S1 Q1 Q7
T2 — user: "Peer-to-peer marketplace connecting private car sellers with buyers — mobile-fir…" → P2 G1:X3 G2:X2 G3:X2 G4:X1 G6:X1 L1 L2 R1 S1 Q1 Q7


--- NEW USER INPUT (SOURCE OF TRUTH THIS TURN) ---
MVP: create a listing with photos, browse and search listings, contact the seller, arrange a meetup. No in-app payments in v1.

```

#### <a id="turn-03-output"></a> 2 — Output

```text
P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X1 L1 L2 R1 S1 Q1 Q7
```

---

## Turn 04 — 2026-05-24T11:09:27.139161+00:00

**Model:** `gpt-4o-mini` · prep 0 ms · API wait 12639 ms

| # | What was sent to the LLM | Output | Token spend (input / output) | Total response time |
|---|--------------------------|--------|------------------------------|---------------------|
| **04** | [12,430 chars — expand](#turn-04-sent) | [56 chars — expand](#turn-04-output) | **3,359 / 37** (Σ 3,396) | **12639.2 ms** (12.639 s) |

#### <a id="turn-04-sent"></a> 1 — What was sent to the LLM

```text
=== SYSTEM — llm-rubric_v2.md only (10,989 chars) ===

# Discovery State Codes — v0.2 (48 codes)

> **Changelog from v0.1** (driven by the 10-turn pet-sitting + car-selling test runs):
> - **Added killer class `TRUST_SAFETY`** — both runs surfaced trust/safety as the dominant
>   risk and both times the taxonomy smeared it across `G7`/`G8`/`GA`. It now has a home.
> - **Added gap code `GD`** (trust/safety risk) → `TRUST_SAFETY`.
> - **Hardened the closed-vocabulary rule** — the model emitted `GCh` (invalid) in turn 10.
>   Any code outside this legend is invalid and must be rejected by a validator.
> - **Added "re-derive readiness each turn"** note — `L`/`R` codes were copied forward
>   unchanged across the run instead of being re-reasoned.

---

## What this is

A closed vocabulary the model **emits** to declare its read of the discovery, *after*
reasoning in full against the discovery rubric. The codes do not replace judgment — they
make it legible, enforceable, and continuous.

- **Source of truth:** the user's pitch and answers ONLY. The code profile is derived from
  user input each turn, never from the model's own prior output. Emitted codes are a
  projection of user truth, not a separate memory.
- **Hard line:** codes are OUTPUT, never INPUT. The model reads the rubric, assesses the
  conversation, then emits codes. It must never generate questions mechanically from codes
  while skipping the rubric.
- **Closed vocabulary:** only the codes in this document are valid. The model must NEVER
  invent a code (e.g. `GCh`). If no gap code fits, it emits `G0` and names the risk. A
  deterministic validator should reject any emitted token not in this legend.

---

## ⚠ Risk taxonomy — PROVISIONAL (still confirm before relying on this)

Every `G`, `L`, and `R` code points at one of these shippability killers. `TRUST_SAFETY`
is evidence-driven (added from the test runs); the other six remain derived-from-rubric,
not owner-confirmed. The runs only stress-tested **marketplace** pitches — a non-marketplace
domain may surface a different hole, so keep this flag until a non-marketplace pitch is run.

| Killer | Meaning |
|--------|---------|
| `WRONG_THING` | user / problem unproven → you build what nobody needs |
| `BOUNDLESS` | scope undefined → you build forever, never ship |
| `UNMEASURABLE` | no success signal → you can't tell if it worked |
| `FRAGILE` | failure / edge modes unhandled → it breaks in prod |
| `BUILT_ON_SAND` | assumptions unconfirmed → foundation collapses |
| `UNGOVERNED` | runtime / human-review / policy gaps → ships but can't be operated safely |
| `TRUST_SAFETY` | **participants can harm each other or be defrauded → ships but isn't safe to use** |

---

## G — Gap pointers (the 13 angles, recast as live risk exposures)

Each marks an unclosed risk and points at the question that closes it.

| Code | Emit-meaning | Risk class | Question it drives |
|------|--------------|------------|--------------------|
| `G1` | user unproven risk | WRONG_THING | who exactly, concretely |
| `G2` | outcome unproven risk | WRONG_THING | what job, measurably |
| `G3` | entry unproven risk | BOUNDLESS | how use begins |
| `G4` | workflow unproven risk | BOUNDLESS | the one core path |
| `G5` | success undefined risk | UNMEASURABLE | what proves it worked |
| `G6` | scope unbounded risk | BOUNDLESS | in vs out, v1 |
| `G7` | domain rule risk | UNGOVERNED | what constraint binds |
| `G8` | failure unhandled risk | FRAGILE | what happens broken |
| `G9` | tradeoff unsettled risk | BOUNDLESS | which competing option |
| `GA` | assumption unconfirmed risk | BUILT_ON_SAND | believe vs proven |
| `GB` | runtime policy risk | UNGOVERNED | how it operates live |
| `GC` | human review risk | UNGOVERNED | where humans intervene |
| `GD` | **trust/safety risk** | **TRUST_SAFETY** | **how participants are protected** |

### Open-class gap (catches risk the taxonomy can't name)

| Code | Emit-meaning | Forces |
|------|--------------|--------|
| `G0` | unnamed risk sensed | a shippability risk no `G1–GD` fits — model MUST name it in narrative and propose an angle. Each `G0` is a signal the taxonomy has a hole — log it. |

> **Note on `GD` vs `GC`:** `GC` stays "human review" (UNGOVERNED — *where humans intervene
> in the workflow*). `GD` is distinct: *protecting participants from each other* (fraud,
> unsafe meetups, bad actors). A decision can touch both; tag both when it does.

---

## X — Exposure (how hot is each gap; derived from user input only)

Attach to a gap code, e.g. `G6:X2` = scope answered-but-thin.

| Code | Emit-meaning | Risk meaning / next move |
|------|--------------|--------------------------|
| `X1` | open never touched | full risk live; strong candidate to ask |
| `X2` | answered but thin | risk MASKED not closed; press one follow-up |
| `X3` | answered with substance | risk genuinely lowered; stop asking |
| `X4` | inferred not confirmed | hidden risk (sand); convert to confirming MCQ |
| `X5` | user-settled hard | risk closed by user; lock, never re-ask |
| `X6` | contradicted by latest | prior closure undermined by new user input; reopen (no amend machinery — recompute yields this) |
| `X7` | answer revealed newrisk | a pick exposed a risk the batch wasn't probing; reopens selection this turn |
| `X8` | user volunteered offangle | free-text beyond the MCQ → primary signal, not noise; may spawn a new angle |

---

## P — Phase (macro gear; advances on user-input conditions)

| Code | Emit-meaning | Gate / effect |
|------|--------------|---------------|
| `P1` | dumping not probing | brain_dump; no MCQs; invite source material |
| `P2` | choosing the pace | mode_choice; no MCQs; offer fast vs coaching |
| `P3` | closing the gaps | elicitation; emit risk-ranked MCQ batch |
| `P4` | sealing the brief | closure; no MCQs; render brief from settled risks |

---

## L — Leverage (how the profile ranks the highest painpoint)

> **Re-derive each turn.** In the test run `L1` was copied forward unchanged across all 10
> turns. Leverage must be re-reasoned from the *current* open-gap set, not carried.

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `L1` | killer beats nicety | rank WRONG_THING / BOUNDLESS / TRUST_SAFETY gaps above polish |
| `L2` | unlocks many dimensions | prefer the gap that closes several at once |
| `L3` | sand before structure | confirm `X4` assumptions before building further |
| `L4` | one blocker first | if a blocker exists, confirm it before breadth |
| `L5` | thin masks danger | treat `X2` as risk, not progress |
| `L6` | nothing open stop | no live risk remains → advance phase |
| `L7` | reframe beats coverage | highest-leverage move is a reframe, not the next ranked gap → permit off-profile question |

---

## R — Readiness (risk-weighted; keeps "shippable" honest)

> **Re-derive each turn.** `R3` was held for eight straight turns while coverage climbed
> from 1 to 5 settled dimensions. Readiness must move as gaps close.

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `R1` | name risks first | list live risks before any percent |
| `R2` | pick-only caps low | MCQ-only-closed gap → dimension ≤ 65 |
| `R3` | unconfirmed caps hard | open `X4`/`X6` present → ready_capped held down |
| `R4` | killers block ship | any open killer-class gap → cannot exceed ~80 |
| `R5` | shippable needs proof | ≥88 only when killers all `X3`/`X5`, ≥12 closed |

---

## S — Safe-question shaping (let the user think; choose risk-free)

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `S1` | concrete not abstract | options are real choices, not "tell me more" |
| `S2` | lowest-risk default visible | include the safe/conservative option explicitly |
| `S3` | one decision each | one question closes one risk; no compound asks |
| `S4` | something-else opens subrisk | a "something else" pick spawns a `<parent>__<sub>` angle at `X1`, ranked high — the user found the gap, honour it |
| `S5` | name the tradeoff | when options compete, state what each costs |

---

## Q — Batch discipline (enforced on emitted codes)

| Code | Emit-meaning | Check |
|------|--------------|-------|
| `Q1` | one primary turn | single lead question unless confirming a blocker |
| `Q2` | no theme repeat | drop any angle already `X3`/`X5` |
| `Q3` | no batch collision | no two batch items share a gap code |
| `Q4` | drop paraphrase asked | drop items paraphrasing prior questions |
| `Q5` | highest leverage first | order batch by dimensions-unlocked |
| `Q6` | fewer than five | if <5 live risks open, ask only those — never pad |
| `Q7` | one open probe | reserve ONE batch item for a non-`G`-derived question the model judges valuable (guarantees a serendipity slot every turn) |

---

## C — Coaching voice (the BA tone, made legible)

| Code | Emit-meaning | Narrative effect |
|------|--------------|------------------|
| `C1` | acknowledge then reflect | open with warm ack + reflect understanding |
| `C2` | push thin answer | stress-test follow-up on an `X2` theme |
| `C3` | narrate the decision | one-line "Got it — X. Logged." on each `X5` |
| `C4` | request source material | brain_dump only: ask for memos / decks / threads |
| `C5` | offer two paths | mode_choice only: present fast vs coaching |

---

## Count

13 gap + 1 open-gap + 8 exposure + 4 phase + 7 leverage + 5 readiness + 5 shaping
+ 7 batch + 5 coaching. The emittable **behavioural set is 48 distinct codes**
(was 47; `GD` added). Exposure flags `X1–X8` attach to gaps as modifiers rather than
standing alone.

---

## RUBRIC ADDITION — paste into the discovery rubric

> **Emit your assessment as state codes.**
> After you have reasoned in full against this rubric — assessing the live discovery the
> way a senior BA would — also emit a single line of state codes that declares your read.
> Attach an exposure flag to each gap (e.g. `G6:X2`). The codes are a projection of the
> user's input, not a memory of your own prior turns: derive them only from what the user
> has actually said and picked.
>
> The codes do not decide your questions — your BA judgment does. Use them to (1) mark
> which shippability risks are still live, (2) rank which painpoint most threatens a
> shippable build, and (3) shape MCQs that let the user commit to the lowest-risk path.
>
> Only codes in the legend are valid — never invent a code. If you sense a risk no gap
> code names, emit `G0` and articulate it. Every elicitation turn must include one open
> probe (`Q7`). Re-derive leverage (`L`) and readiness (`R`) each turn from the current
> open-gap set — do not carry them forward unchanged.
>
> Example emitted line:
> `P3 G1:X5 G4:X3 G6:X2 G8:X1 GA:X4 GD:X1 L1 L3 L5 R3 S2 Q7`
> → elicitation; user & workflow closed; scope thin (press it); failure-modes wide open;
> one assumption built-on-sand to confirm; trust/safety still untouched; rank killers,
> confirm the sand, treat thin as danger; readiness held by the unconfirmed; surface the
> safe default; reserve an open probe.

=== USER — turn context (1,341 chars) ===

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
Car selling app

## Latest state codes
P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X1 L1 L2 R1 S1 Q1 Q7

## Settled facts (user-confirmed only)
_(none)_

## Compressed conversation
T1 — user: "Car selling app" → P1 G1:X1 G2:X1 G3:X1 G4:X1 L1 R1 S1 Q1 Q7
T2 — user: "Peer-to-peer marketplace connecting private car sellers with buyers — mobile-fir…" → P2 G1:X3 G2:X2 G3:X2 G4:X1 G6:X1 L1 L2 R1 S1 Q1 Q7
T3 — user: "MVP: create a listing with photos, browse and search listings, contact the selle…" → P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X1 L1 L2 R1 S1 Q1 Q7


--- NEW USER INPUT (SOURCE OF TRUTH THIS TURN) ---
Trust is critical: light seller verification, report listing, and safety guidance for in-person meetups.

```

#### <a id="turn-04-output"></a> 2 — Output

```text
P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X1 GD:X1 L1 L2 R1 S1 Q1 Q7
```

---

## Turn 05 — 2026-05-24T11:09:39.553432+00:00

**Model:** `gpt-4o-mini` · prep 0 ms · API wait 11954 ms

| # | What was sent to the LLM | Output | Token spend (input / output) | Total response time |
|---|--------------------------|--------|------------------------------|---------------------|
| **05** | [12,577 chars — expand](#turn-05-sent) | [56 chars — expand](#turn-05-output) | **3,422 / 37** (Σ 3,459) | **11954.0 ms** (11.954 s) |

#### <a id="turn-05-sent"></a> 1 — What was sent to the LLM

```text
=== SYSTEM — llm-rubric_v2.md only (10,989 chars) ===

# Discovery State Codes — v0.2 (48 codes)

> **Changelog from v0.1** (driven by the 10-turn pet-sitting + car-selling test runs):
> - **Added killer class `TRUST_SAFETY`** — both runs surfaced trust/safety as the dominant
>   risk and both times the taxonomy smeared it across `G7`/`G8`/`GA`. It now has a home.
> - **Added gap code `GD`** (trust/safety risk) → `TRUST_SAFETY`.
> - **Hardened the closed-vocabulary rule** — the model emitted `GCh` (invalid) in turn 10.
>   Any code outside this legend is invalid and must be rejected by a validator.
> - **Added "re-derive readiness each turn"** note — `L`/`R` codes were copied forward
>   unchanged across the run instead of being re-reasoned.

---

## What this is

A closed vocabulary the model **emits** to declare its read of the discovery, *after*
reasoning in full against the discovery rubric. The codes do not replace judgment — they
make it legible, enforceable, and continuous.

- **Source of truth:** the user's pitch and answers ONLY. The code profile is derived from
  user input each turn, never from the model's own prior output. Emitted codes are a
  projection of user truth, not a separate memory.
- **Hard line:** codes are OUTPUT, never INPUT. The model reads the rubric, assesses the
  conversation, then emits codes. It must never generate questions mechanically from codes
  while skipping the rubric.
- **Closed vocabulary:** only the codes in this document are valid. The model must NEVER
  invent a code (e.g. `GCh`). If no gap code fits, it emits `G0` and names the risk. A
  deterministic validator should reject any emitted token not in this legend.

---

## ⚠ Risk taxonomy — PROVISIONAL (still confirm before relying on this)

Every `G`, `L`, and `R` code points at one of these shippability killers. `TRUST_SAFETY`
is evidence-driven (added from the test runs); the other six remain derived-from-rubric,
not owner-confirmed. The runs only stress-tested **marketplace** pitches — a non-marketplace
domain may surface a different hole, so keep this flag until a non-marketplace pitch is run.

| Killer | Meaning |
|--------|---------|
| `WRONG_THING` | user / problem unproven → you build what nobody needs |
| `BOUNDLESS` | scope undefined → you build forever, never ship |
| `UNMEASURABLE` | no success signal → you can't tell if it worked |
| `FRAGILE` | failure / edge modes unhandled → it breaks in prod |
| `BUILT_ON_SAND` | assumptions unconfirmed → foundation collapses |
| `UNGOVERNED` | runtime / human-review / policy gaps → ships but can't be operated safely |
| `TRUST_SAFETY` | **participants can harm each other or be defrauded → ships but isn't safe to use** |

---

## G — Gap pointers (the 13 angles, recast as live risk exposures)

Each marks an unclosed risk and points at the question that closes it.

| Code | Emit-meaning | Risk class | Question it drives |
|------|--------------|------------|--------------------|
| `G1` | user unproven risk | WRONG_THING | who exactly, concretely |
| `G2` | outcome unproven risk | WRONG_THING | what job, measurably |
| `G3` | entry unproven risk | BOUNDLESS | how use begins |
| `G4` | workflow unproven risk | BOUNDLESS | the one core path |
| `G5` | success undefined risk | UNMEASURABLE | what proves it worked |
| `G6` | scope unbounded risk | BOUNDLESS | in vs out, v1 |
| `G7` | domain rule risk | UNGOVERNED | what constraint binds |
| `G8` | failure unhandled risk | FRAGILE | what happens broken |
| `G9` | tradeoff unsettled risk | BOUNDLESS | which competing option |
| `GA` | assumption unconfirmed risk | BUILT_ON_SAND | believe vs proven |
| `GB` | runtime policy risk | UNGOVERNED | how it operates live |
| `GC` | human review risk | UNGOVERNED | where humans intervene |
| `GD` | **trust/safety risk** | **TRUST_SAFETY** | **how participants are protected** |

### Open-class gap (catches risk the taxonomy can't name)

| Code | Emit-meaning | Forces |
|------|--------------|--------|
| `G0` | unnamed risk sensed | a shippability risk no `G1–GD` fits — model MUST name it in narrative and propose an angle. Each `G0` is a signal the taxonomy has a hole — log it. |

> **Note on `GD` vs `GC`:** `GC` stays "human review" (UNGOVERNED — *where humans intervene
> in the workflow*). `GD` is distinct: *protecting participants from each other* (fraud,
> unsafe meetups, bad actors). A decision can touch both; tag both when it does.

---

## X — Exposure (how hot is each gap; derived from user input only)

Attach to a gap code, e.g. `G6:X2` = scope answered-but-thin.

| Code | Emit-meaning | Risk meaning / next move |
|------|--------------|--------------------------|
| `X1` | open never touched | full risk live; strong candidate to ask |
| `X2` | answered but thin | risk MASKED not closed; press one follow-up |
| `X3` | answered with substance | risk genuinely lowered; stop asking |
| `X4` | inferred not confirmed | hidden risk (sand); convert to confirming MCQ |
| `X5` | user-settled hard | risk closed by user; lock, never re-ask |
| `X6` | contradicted by latest | prior closure undermined by new user input; reopen (no amend machinery — recompute yields this) |
| `X7` | answer revealed newrisk | a pick exposed a risk the batch wasn't probing; reopens selection this turn |
| `X8` | user volunteered offangle | free-text beyond the MCQ → primary signal, not noise; may spawn a new angle |

---

## P — Phase (macro gear; advances on user-input conditions)

| Code | Emit-meaning | Gate / effect |
|------|--------------|---------------|
| `P1` | dumping not probing | brain_dump; no MCQs; invite source material |
| `P2` | choosing the pace | mode_choice; no MCQs; offer fast vs coaching |
| `P3` | closing the gaps | elicitation; emit risk-ranked MCQ batch |
| `P4` | sealing the brief | closure; no MCQs; render brief from settled risks |

---

## L — Leverage (how the profile ranks the highest painpoint)

> **Re-derive each turn.** In the test run `L1` was copied forward unchanged across all 10
> turns. Leverage must be re-reasoned from the *current* open-gap set, not carried.

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `L1` | killer beats nicety | rank WRONG_THING / BOUNDLESS / TRUST_SAFETY gaps above polish |
| `L2` | unlocks many dimensions | prefer the gap that closes several at once |
| `L3` | sand before structure | confirm `X4` assumptions before building further |
| `L4` | one blocker first | if a blocker exists, confirm it before breadth |
| `L5` | thin masks danger | treat `X2` as risk, not progress |
| `L6` | nothing open stop | no live risk remains → advance phase |
| `L7` | reframe beats coverage | highest-leverage move is a reframe, not the next ranked gap → permit off-profile question |

---

## R — Readiness (risk-weighted; keeps "shippable" honest)

> **Re-derive each turn.** `R3` was held for eight straight turns while coverage climbed
> from 1 to 5 settled dimensions. Readiness must move as gaps close.

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `R1` | name risks first | list live risks before any percent |
| `R2` | pick-only caps low | MCQ-only-closed gap → dimension ≤ 65 |
| `R3` | unconfirmed caps hard | open `X4`/`X6` present → ready_capped held down |
| `R4` | killers block ship | any open killer-class gap → cannot exceed ~80 |
| `R5` | shippable needs proof | ≥88 only when killers all `X3`/`X5`, ≥12 closed |

---

## S — Safe-question shaping (let the user think; choose risk-free)

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `S1` | concrete not abstract | options are real choices, not "tell me more" |
| `S2` | lowest-risk default visible | include the safe/conservative option explicitly |
| `S3` | one decision each | one question closes one risk; no compound asks |
| `S4` | something-else opens subrisk | a "something else" pick spawns a `<parent>__<sub>` angle at `X1`, ranked high — the user found the gap, honour it |
| `S5` | name the tradeoff | when options compete, state what each costs |

---

## Q — Batch discipline (enforced on emitted codes)

| Code | Emit-meaning | Check |
|------|--------------|-------|
| `Q1` | one primary turn | single lead question unless confirming a blocker |
| `Q2` | no theme repeat | drop any angle already `X3`/`X5` |
| `Q3` | no batch collision | no two batch items share a gap code |
| `Q4` | drop paraphrase asked | drop items paraphrasing prior questions |
| `Q5` | highest leverage first | order batch by dimensions-unlocked |
| `Q6` | fewer than five | if <5 live risks open, ask only those — never pad |
| `Q7` | one open probe | reserve ONE batch item for a non-`G`-derived question the model judges valuable (guarantees a serendipity slot every turn) |

---

## C — Coaching voice (the BA tone, made legible)

| Code | Emit-meaning | Narrative effect |
|------|--------------|------------------|
| `C1` | acknowledge then reflect | open with warm ack + reflect understanding |
| `C2` | push thin answer | stress-test follow-up on an `X2` theme |
| `C3` | narrate the decision | one-line "Got it — X. Logged." on each `X5` |
| `C4` | request source material | brain_dump only: ask for memos / decks / threads |
| `C5` | offer two paths | mode_choice only: present fast vs coaching |

---

## Count

13 gap + 1 open-gap + 8 exposure + 4 phase + 7 leverage + 5 readiness + 5 shaping
+ 7 batch + 5 coaching. The emittable **behavioural set is 48 distinct codes**
(was 47; `GD` added). Exposure flags `X1–X8` attach to gaps as modifiers rather than
standing alone.

---

## RUBRIC ADDITION — paste into the discovery rubric

> **Emit your assessment as state codes.**
> After you have reasoned in full against this rubric — assessing the live discovery the
> way a senior BA would — also emit a single line of state codes that declares your read.
> Attach an exposure flag to each gap (e.g. `G6:X2`). The codes are a projection of the
> user's input, not a memory of your own prior turns: derive them only from what the user
> has actually said and picked.
>
> The codes do not decide your questions — your BA judgment does. Use them to (1) mark
> which shippability risks are still live, (2) rank which painpoint most threatens a
> shippable build, and (3) shape MCQs that let the user commit to the lowest-risk path.
>
> Only codes in the legend are valid — never invent a code. If you sense a risk no gap
> code names, emit `G0` and articulate it. Every elicitation turn must include one open
> probe (`Q7`). Re-derive leverage (`L`) and readiness (`R`) each turn from the current
> open-gap set — do not carry them forward unchanged.
>
> Example emitted line:
> `P3 G1:X5 G4:X3 G6:X2 G8:X1 GA:X4 GD:X1 L1 L3 L5 R3 S2 Q7`
> → elicitation; user & workflow closed; scope thin (press it); failure-modes wide open;
> one assumption built-on-sand to confirm; trust/safety still untouched; rank killers,
> confirm the sand, treat thin as danger; readiness held by the unconfirmed; surface the
> safe default; reserve an open probe.

=== USER — turn context (1,488 chars) ===

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
Car selling app

## Latest state codes
P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X1 GD:X1 L1 L2 R1 S1 Q1 Q7

## Settled facts (user-confirmed only)
_(none)_

## Compressed conversation
T1 — user: "Car selling app" → P1 G1:X1 G2:X1 G3:X1 G4:X1 L1 R1 S1 Q1 Q7
T2 — user: "Peer-to-peer marketplace connecting private car sellers with buyers — mobile-fir…" → P2 G1:X3 G2:X2 G3:X2 G4:X1 G6:X1 L1 L2 R1 S1 Q1 Q7
T3 — user: "MVP: create a listing with photos, browse and search listings, contact the selle…" → P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X1 L1 L2 R1 S1 Q1 Q7
T4 — user: "Trust is critical: light seller verification, report listing, and safety guidanc…" → P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X1 GD:X1 L1 L2 R1 S1 Q1 Q7


--- NEW USER INPUT (SOURCE OF TRUTH THIS TURN) ---
Price is manual negotiation only — no automated pricing, auctions, or instant offers in v1.

```

#### <a id="turn-05-output"></a> 2 — Output

```text
P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X1 GD:X1 L1 L2 R1 S1 Q1 Q7
```

---

## Turn 06 — 2026-05-24T11:09:51.441337+00:00

**Model:** `gpt-4o-mini` · prep 0 ms · API wait 11105 ms

| # | What was sent to the LLM | Output | Token spend (input / output) | Total response time |
|---|--------------------------|--------|------------------------------|---------------------|
| **06** | [12,750 chars — expand](#turn-06-sent) | [56 chars — expand](#turn-06-output) | **3,489 / 37** (Σ 3,526) | **11104.8 ms** (11.105 s) |

#### <a id="turn-06-sent"></a> 1 — What was sent to the LLM

```text
=== SYSTEM — llm-rubric_v2.md only (10,989 chars) ===

# Discovery State Codes — v0.2 (48 codes)

> **Changelog from v0.1** (driven by the 10-turn pet-sitting + car-selling test runs):
> - **Added killer class `TRUST_SAFETY`** — both runs surfaced trust/safety as the dominant
>   risk and both times the taxonomy smeared it across `G7`/`G8`/`GA`. It now has a home.
> - **Added gap code `GD`** (trust/safety risk) → `TRUST_SAFETY`.
> - **Hardened the closed-vocabulary rule** — the model emitted `GCh` (invalid) in turn 10.
>   Any code outside this legend is invalid and must be rejected by a validator.
> - **Added "re-derive readiness each turn"** note — `L`/`R` codes were copied forward
>   unchanged across the run instead of being re-reasoned.

---

## What this is

A closed vocabulary the model **emits** to declare its read of the discovery, *after*
reasoning in full against the discovery rubric. The codes do not replace judgment — they
make it legible, enforceable, and continuous.

- **Source of truth:** the user's pitch and answers ONLY. The code profile is derived from
  user input each turn, never from the model's own prior output. Emitted codes are a
  projection of user truth, not a separate memory.
- **Hard line:** codes are OUTPUT, never INPUT. The model reads the rubric, assesses the
  conversation, then emits codes. It must never generate questions mechanically from codes
  while skipping the rubric.
- **Closed vocabulary:** only the codes in this document are valid. The model must NEVER
  invent a code (e.g. `GCh`). If no gap code fits, it emits `G0` and names the risk. A
  deterministic validator should reject any emitted token not in this legend.

---

## ⚠ Risk taxonomy — PROVISIONAL (still confirm before relying on this)

Every `G`, `L`, and `R` code points at one of these shippability killers. `TRUST_SAFETY`
is evidence-driven (added from the test runs); the other six remain derived-from-rubric,
not owner-confirmed. The runs only stress-tested **marketplace** pitches — a non-marketplace
domain may surface a different hole, so keep this flag until a non-marketplace pitch is run.

| Killer | Meaning |
|--------|---------|
| `WRONG_THING` | user / problem unproven → you build what nobody needs |
| `BOUNDLESS` | scope undefined → you build forever, never ship |
| `UNMEASURABLE` | no success signal → you can't tell if it worked |
| `FRAGILE` | failure / edge modes unhandled → it breaks in prod |
| `BUILT_ON_SAND` | assumptions unconfirmed → foundation collapses |
| `UNGOVERNED` | runtime / human-review / policy gaps → ships but can't be operated safely |
| `TRUST_SAFETY` | **participants can harm each other or be defrauded → ships but isn't safe to use** |

---

## G — Gap pointers (the 13 angles, recast as live risk exposures)

Each marks an unclosed risk and points at the question that closes it.

| Code | Emit-meaning | Risk class | Question it drives |
|------|--------------|------------|--------------------|
| `G1` | user unproven risk | WRONG_THING | who exactly, concretely |
| `G2` | outcome unproven risk | WRONG_THING | what job, measurably |
| `G3` | entry unproven risk | BOUNDLESS | how use begins |
| `G4` | workflow unproven risk | BOUNDLESS | the one core path |
| `G5` | success undefined risk | UNMEASURABLE | what proves it worked |
| `G6` | scope unbounded risk | BOUNDLESS | in vs out, v1 |
| `G7` | domain rule risk | UNGOVERNED | what constraint binds |
| `G8` | failure unhandled risk | FRAGILE | what happens broken |
| `G9` | tradeoff unsettled risk | BOUNDLESS | which competing option |
| `GA` | assumption unconfirmed risk | BUILT_ON_SAND | believe vs proven |
| `GB` | runtime policy risk | UNGOVERNED | how it operates live |
| `GC` | human review risk | UNGOVERNED | where humans intervene |
| `GD` | **trust/safety risk** | **TRUST_SAFETY** | **how participants are protected** |

### Open-class gap (catches risk the taxonomy can't name)

| Code | Emit-meaning | Forces |
|------|--------------|--------|
| `G0` | unnamed risk sensed | a shippability risk no `G1–GD` fits — model MUST name it in narrative and propose an angle. Each `G0` is a signal the taxonomy has a hole — log it. |

> **Note on `GD` vs `GC`:** `GC` stays "human review" (UNGOVERNED — *where humans intervene
> in the workflow*). `GD` is distinct: *protecting participants from each other* (fraud,
> unsafe meetups, bad actors). A decision can touch both; tag both when it does.

---

## X — Exposure (how hot is each gap; derived from user input only)

Attach to a gap code, e.g. `G6:X2` = scope answered-but-thin.

| Code | Emit-meaning | Risk meaning / next move |
|------|--------------|--------------------------|
| `X1` | open never touched | full risk live; strong candidate to ask |
| `X2` | answered but thin | risk MASKED not closed; press one follow-up |
| `X3` | answered with substance | risk genuinely lowered; stop asking |
| `X4` | inferred not confirmed | hidden risk (sand); convert to confirming MCQ |
| `X5` | user-settled hard | risk closed by user; lock, never re-ask |
| `X6` | contradicted by latest | prior closure undermined by new user input; reopen (no amend machinery — recompute yields this) |
| `X7` | answer revealed newrisk | a pick exposed a risk the batch wasn't probing; reopens selection this turn |
| `X8` | user volunteered offangle | free-text beyond the MCQ → primary signal, not noise; may spawn a new angle |

---

## P — Phase (macro gear; advances on user-input conditions)

| Code | Emit-meaning | Gate / effect |
|------|--------------|---------------|
| `P1` | dumping not probing | brain_dump; no MCQs; invite source material |
| `P2` | choosing the pace | mode_choice; no MCQs; offer fast vs coaching |
| `P3` | closing the gaps | elicitation; emit risk-ranked MCQ batch |
| `P4` | sealing the brief | closure; no MCQs; render brief from settled risks |

---

## L — Leverage (how the profile ranks the highest painpoint)

> **Re-derive each turn.** In the test run `L1` was copied forward unchanged across all 10
> turns. Leverage must be re-reasoned from the *current* open-gap set, not carried.

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `L1` | killer beats nicety | rank WRONG_THING / BOUNDLESS / TRUST_SAFETY gaps above polish |
| `L2` | unlocks many dimensions | prefer the gap that closes several at once |
| `L3` | sand before structure | confirm `X4` assumptions before building further |
| `L4` | one blocker first | if a blocker exists, confirm it before breadth |
| `L5` | thin masks danger | treat `X2` as risk, not progress |
| `L6` | nothing open stop | no live risk remains → advance phase |
| `L7` | reframe beats coverage | highest-leverage move is a reframe, not the next ranked gap → permit off-profile question |

---

## R — Readiness (risk-weighted; keeps "shippable" honest)

> **Re-derive each turn.** `R3` was held for eight straight turns while coverage climbed
> from 1 to 5 settled dimensions. Readiness must move as gaps close.

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `R1` | name risks first | list live risks before any percent |
| `R2` | pick-only caps low | MCQ-only-closed gap → dimension ≤ 65 |
| `R3` | unconfirmed caps hard | open `X4`/`X6` present → ready_capped held down |
| `R4` | killers block ship | any open killer-class gap → cannot exceed ~80 |
| `R5` | shippable needs proof | ≥88 only when killers all `X3`/`X5`, ≥12 closed |

---

## S — Safe-question shaping (let the user think; choose risk-free)

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `S1` | concrete not abstract | options are real choices, not "tell me more" |
| `S2` | lowest-risk default visible | include the safe/conservative option explicitly |
| `S3` | one decision each | one question closes one risk; no compound asks |
| `S4` | something-else opens subrisk | a "something else" pick spawns a `<parent>__<sub>` angle at `X1`, ranked high — the user found the gap, honour it |
| `S5` | name the tradeoff | when options compete, state what each costs |

---

## Q — Batch discipline (enforced on emitted codes)

| Code | Emit-meaning | Check |
|------|--------------|-------|
| `Q1` | one primary turn | single lead question unless confirming a blocker |
| `Q2` | no theme repeat | drop any angle already `X3`/`X5` |
| `Q3` | no batch collision | no two batch items share a gap code |
| `Q4` | drop paraphrase asked | drop items paraphrasing prior questions |
| `Q5` | highest leverage first | order batch by dimensions-unlocked |
| `Q6` | fewer than five | if <5 live risks open, ask only those — never pad |
| `Q7` | one open probe | reserve ONE batch item for a non-`G`-derived question the model judges valuable (guarantees a serendipity slot every turn) |

---

## C — Coaching voice (the BA tone, made legible)

| Code | Emit-meaning | Narrative effect |
|------|--------------|------------------|
| `C1` | acknowledge then reflect | open with warm ack + reflect understanding |
| `C2` | push thin answer | stress-test follow-up on an `X2` theme |
| `C3` | narrate the decision | one-line "Got it — X. Logged." on each `X5` |
| `C4` | request source material | brain_dump only: ask for memos / decks / threads |
| `C5` | offer two paths | mode_choice only: present fast vs coaching |

---

## Count

13 gap + 1 open-gap + 8 exposure + 4 phase + 7 leverage + 5 readiness + 5 shaping
+ 7 batch + 5 coaching. The emittable **behavioural set is 48 distinct codes**
(was 47; `GD` added). Exposure flags `X1–X8` attach to gaps as modifiers rather than
standing alone.

---

## RUBRIC ADDITION — paste into the discovery rubric

> **Emit your assessment as state codes.**
> After you have reasoned in full against this rubric — assessing the live discovery the
> way a senior BA would — also emit a single line of state codes that declares your read.
> Attach an exposure flag to each gap (e.g. `G6:X2`). The codes are a projection of the
> user's input, not a memory of your own prior turns: derive them only from what the user
> has actually said and picked.
>
> The codes do not decide your questions — your BA judgment does. Use them to (1) mark
> which shippability risks are still live, (2) rank which painpoint most threatens a
> shippable build, and (3) shape MCQs that let the user commit to the lowest-risk path.
>
> Only codes in the legend are valid — never invent a code. If you sense a risk no gap
> code names, emit `G0` and articulate it. Every elicitation turn must include one open
> probe (`Q7`). Re-derive leverage (`L`) and readiness (`R`) each turn from the current
> open-gap set — do not carry them forward unchanged.
>
> Example emitted line:
> `P3 G1:X5 G4:X3 G6:X2 G8:X1 GA:X4 GD:X1 L1 L3 L5 R3 S2 Q7`
> → elicitation; user & workflow closed; scope thin (press it); failure-modes wide open;
> one assumption built-on-sand to confirm; trust/safety still untouched; rank killers,
> confirm the sand, treat thin as danger; readiness held by the unconfirmed; surface the
> safe default; reserve an open probe.

=== USER — turn context (1,661 chars) ===

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
Car selling app

## Latest state codes
P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X1 GD:X1 L1 L2 R1 S1 Q1 Q7

## Settled facts (user-confirmed only)
_(none)_

## Compressed conversation
T1 — user: "Car selling app" → P1 G1:X1 G2:X1 G3:X1 G4:X1 L1 R1 S1 Q1 Q7
T2 — user: "Peer-to-peer marketplace connecting private car sellers with buyers — mobile-fir…" → P2 G1:X3 G2:X2 G3:X2 G4:X1 G6:X1 L1 L2 R1 S1 Q1 Q7
T3 — user: "MVP: create a listing with photos, browse and search listings, contact the selle…" → P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X1 L1 L2 R1 S1 Q1 Q7
T4 — user: "Trust is critical: light seller verification, report listing, and safety guidanc…" → P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X1 GD:X1 L1 L2 R1 S1 Q1 Q7
T5 — user: "Price is manual negotiation only — no automated pricing, auctions, or instant of…" → P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X1 GD:X1 L1 L2 R1 S1 Q1 Q7


--- NEW USER INPUT (SOURCE OF TRUTH THIS TURN) ---
Out of scope for v1: financing, shipping, professional inspections, and dealer fleet tools. Consumer P2P only.

```

#### <a id="turn-06-output"></a> 2 — Output

```text
P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X2 GD:X1 L1 L2 R1 S1 Q1 Q7
```

---

## Turn 07 — 2026-05-24T11:09:59.713608+00:00

**Model:** `gpt-4o-mini` · prep 0 ms · API wait 7802 ms

| # | What was sent to the LLM | Output | Token spend (input / output) | Total response time |
|---|--------------------------|--------|------------------------------|---------------------|
| **07** | [12,904 chars — expand](#turn-07-sent) | [56 chars — expand](#turn-07-output) | **3,552 / 37** (Σ 3,589) | **7802.2 ms** (7.802 s) |

#### <a id="turn-07-sent"></a> 1 — What was sent to the LLM

```text
=== SYSTEM — llm-rubric_v2.md only (10,989 chars) ===

# Discovery State Codes — v0.2 (48 codes)

> **Changelog from v0.1** (driven by the 10-turn pet-sitting + car-selling test runs):
> - **Added killer class `TRUST_SAFETY`** — both runs surfaced trust/safety as the dominant
>   risk and both times the taxonomy smeared it across `G7`/`G8`/`GA`. It now has a home.
> - **Added gap code `GD`** (trust/safety risk) → `TRUST_SAFETY`.
> - **Hardened the closed-vocabulary rule** — the model emitted `GCh` (invalid) in turn 10.
>   Any code outside this legend is invalid and must be rejected by a validator.
> - **Added "re-derive readiness each turn"** note — `L`/`R` codes were copied forward
>   unchanged across the run instead of being re-reasoned.

---

## What this is

A closed vocabulary the model **emits** to declare its read of the discovery, *after*
reasoning in full against the discovery rubric. The codes do not replace judgment — they
make it legible, enforceable, and continuous.

- **Source of truth:** the user's pitch and answers ONLY. The code profile is derived from
  user input each turn, never from the model's own prior output. Emitted codes are a
  projection of user truth, not a separate memory.
- **Hard line:** codes are OUTPUT, never INPUT. The model reads the rubric, assesses the
  conversation, then emits codes. It must never generate questions mechanically from codes
  while skipping the rubric.
- **Closed vocabulary:** only the codes in this document are valid. The model must NEVER
  invent a code (e.g. `GCh`). If no gap code fits, it emits `G0` and names the risk. A
  deterministic validator should reject any emitted token not in this legend.

---

## ⚠ Risk taxonomy — PROVISIONAL (still confirm before relying on this)

Every `G`, `L`, and `R` code points at one of these shippability killers. `TRUST_SAFETY`
is evidence-driven (added from the test runs); the other six remain derived-from-rubric,
not owner-confirmed. The runs only stress-tested **marketplace** pitches — a non-marketplace
domain may surface a different hole, so keep this flag until a non-marketplace pitch is run.

| Killer | Meaning |
|--------|---------|
| `WRONG_THING` | user / problem unproven → you build what nobody needs |
| `BOUNDLESS` | scope undefined → you build forever, never ship |
| `UNMEASURABLE` | no success signal → you can't tell if it worked |
| `FRAGILE` | failure / edge modes unhandled → it breaks in prod |
| `BUILT_ON_SAND` | assumptions unconfirmed → foundation collapses |
| `UNGOVERNED` | runtime / human-review / policy gaps → ships but can't be operated safely |
| `TRUST_SAFETY` | **participants can harm each other or be defrauded → ships but isn't safe to use** |

---

## G — Gap pointers (the 13 angles, recast as live risk exposures)

Each marks an unclosed risk and points at the question that closes it.

| Code | Emit-meaning | Risk class | Question it drives |
|------|--------------|------------|--------------------|
| `G1` | user unproven risk | WRONG_THING | who exactly, concretely |
| `G2` | outcome unproven risk | WRONG_THING | what job, measurably |
| `G3` | entry unproven risk | BOUNDLESS | how use begins |
| `G4` | workflow unproven risk | BOUNDLESS | the one core path |
| `G5` | success undefined risk | UNMEASURABLE | what proves it worked |
| `G6` | scope unbounded risk | BOUNDLESS | in vs out, v1 |
| `G7` | domain rule risk | UNGOVERNED | what constraint binds |
| `G8` | failure unhandled risk | FRAGILE | what happens broken |
| `G9` | tradeoff unsettled risk | BOUNDLESS | which competing option |
| `GA` | assumption unconfirmed risk | BUILT_ON_SAND | believe vs proven |
| `GB` | runtime policy risk | UNGOVERNED | how it operates live |
| `GC` | human review risk | UNGOVERNED | where humans intervene |
| `GD` | **trust/safety risk** | **TRUST_SAFETY** | **how participants are protected** |

### Open-class gap (catches risk the taxonomy can't name)

| Code | Emit-meaning | Forces |
|------|--------------|--------|
| `G0` | unnamed risk sensed | a shippability risk no `G1–GD` fits — model MUST name it in narrative and propose an angle. Each `G0` is a signal the taxonomy has a hole — log it. |

> **Note on `GD` vs `GC`:** `GC` stays "human review" (UNGOVERNED — *where humans intervene
> in the workflow*). `GD` is distinct: *protecting participants from each other* (fraud,
> unsafe meetups, bad actors). A decision can touch both; tag both when it does.

---

## X — Exposure (how hot is each gap; derived from user input only)

Attach to a gap code, e.g. `G6:X2` = scope answered-but-thin.

| Code | Emit-meaning | Risk meaning / next move |
|------|--------------|--------------------------|
| `X1` | open never touched | full risk live; strong candidate to ask |
| `X2` | answered but thin | risk MASKED not closed; press one follow-up |
| `X3` | answered with substance | risk genuinely lowered; stop asking |
| `X4` | inferred not confirmed | hidden risk (sand); convert to confirming MCQ |
| `X5` | user-settled hard | risk closed by user; lock, never re-ask |
| `X6` | contradicted by latest | prior closure undermined by new user input; reopen (no amend machinery — recompute yields this) |
| `X7` | answer revealed newrisk | a pick exposed a risk the batch wasn't probing; reopens selection this turn |
| `X8` | user volunteered offangle | free-text beyond the MCQ → primary signal, not noise; may spawn a new angle |

---

## P — Phase (macro gear; advances on user-input conditions)

| Code | Emit-meaning | Gate / effect |
|------|--------------|---------------|
| `P1` | dumping not probing | brain_dump; no MCQs; invite source material |
| `P2` | choosing the pace | mode_choice; no MCQs; offer fast vs coaching |
| `P3` | closing the gaps | elicitation; emit risk-ranked MCQ batch |
| `P4` | sealing the brief | closure; no MCQs; render brief from settled risks |

---

## L — Leverage (how the profile ranks the highest painpoint)

> **Re-derive each turn.** In the test run `L1` was copied forward unchanged across all 10
> turns. Leverage must be re-reasoned from the *current* open-gap set, not carried.

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `L1` | killer beats nicety | rank WRONG_THING / BOUNDLESS / TRUST_SAFETY gaps above polish |
| `L2` | unlocks many dimensions | prefer the gap that closes several at once |
| `L3` | sand before structure | confirm `X4` assumptions before building further |
| `L4` | one blocker first | if a blocker exists, confirm it before breadth |
| `L5` | thin masks danger | treat `X2` as risk, not progress |
| `L6` | nothing open stop | no live risk remains → advance phase |
| `L7` | reframe beats coverage | highest-leverage move is a reframe, not the next ranked gap → permit off-profile question |

---

## R — Readiness (risk-weighted; keeps "shippable" honest)

> **Re-derive each turn.** `R3` was held for eight straight turns while coverage climbed
> from 1 to 5 settled dimensions. Readiness must move as gaps close.

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `R1` | name risks first | list live risks before any percent |
| `R2` | pick-only caps low | MCQ-only-closed gap → dimension ≤ 65 |
| `R3` | unconfirmed caps hard | open `X4`/`X6` present → ready_capped held down |
| `R4` | killers block ship | any open killer-class gap → cannot exceed ~80 |
| `R5` | shippable needs proof | ≥88 only when killers all `X3`/`X5`, ≥12 closed |

---

## S — Safe-question shaping (let the user think; choose risk-free)

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `S1` | concrete not abstract | options are real choices, not "tell me more" |
| `S2` | lowest-risk default visible | include the safe/conservative option explicitly |
| `S3` | one decision each | one question closes one risk; no compound asks |
| `S4` | something-else opens subrisk | a "something else" pick spawns a `<parent>__<sub>` angle at `X1`, ranked high — the user found the gap, honour it |
| `S5` | name the tradeoff | when options compete, state what each costs |

---

## Q — Batch discipline (enforced on emitted codes)

| Code | Emit-meaning | Check |
|------|--------------|-------|
| `Q1` | one primary turn | single lead question unless confirming a blocker |
| `Q2` | no theme repeat | drop any angle already `X3`/`X5` |
| `Q3` | no batch collision | no two batch items share a gap code |
| `Q4` | drop paraphrase asked | drop items paraphrasing prior questions |
| `Q5` | highest leverage first | order batch by dimensions-unlocked |
| `Q6` | fewer than five | if <5 live risks open, ask only those — never pad |
| `Q7` | one open probe | reserve ONE batch item for a non-`G`-derived question the model judges valuable (guarantees a serendipity slot every turn) |

---

## C — Coaching voice (the BA tone, made legible)

| Code | Emit-meaning | Narrative effect |
|------|--------------|------------------|
| `C1` | acknowledge then reflect | open with warm ack + reflect understanding |
| `C2` | push thin answer | stress-test follow-up on an `X2` theme |
| `C3` | narrate the decision | one-line "Got it — X. Logged." on each `X5` |
| `C4` | request source material | brain_dump only: ask for memos / decks / threads |
| `C5` | offer two paths | mode_choice only: present fast vs coaching |

---

## Count

13 gap + 1 open-gap + 8 exposure + 4 phase + 7 leverage + 5 readiness + 5 shaping
+ 7 batch + 5 coaching. The emittable **behavioural set is 48 distinct codes**
(was 47; `GD` added). Exposure flags `X1–X8` attach to gaps as modifiers rather than
standing alone.

---

## RUBRIC ADDITION — paste into the discovery rubric

> **Emit your assessment as state codes.**
> After you have reasoned in full against this rubric — assessing the live discovery the
> way a senior BA would — also emit a single line of state codes that declares your read.
> Attach an exposure flag to each gap (e.g. `G6:X2`). The codes are a projection of the
> user's input, not a memory of your own prior turns: derive them only from what the user
> has actually said and picked.
>
> The codes do not decide your questions — your BA judgment does. Use them to (1) mark
> which shippability risks are still live, (2) rank which painpoint most threatens a
> shippable build, and (3) shape MCQs that let the user commit to the lowest-risk path.
>
> Only codes in the legend are valid — never invent a code. If you sense a risk no gap
> code names, emit `G0` and articulate it. Every elicitation turn must include one open
> probe (`Q7`). Re-derive leverage (`L`) and readiness (`R`) each turn from the current
> open-gap set — do not carry them forward unchanged.
>
> Example emitted line:
> `P3 G1:X5 G4:X3 G6:X2 G8:X1 GA:X4 GD:X1 L1 L3 L5 R3 S2 Q7`
> → elicitation; user & workflow closed; scope thin (press it); failure-modes wide open;
> one assumption built-on-sand to confirm; trust/safety still untouched; rank killers,
> confirm the sand, treat thin as danger; readiness held by the unconfirmed; surface the
> safe default; reserve an open probe.

=== USER — turn context (1,815 chars) ===

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
Car selling app

## Latest state codes
P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X2 GD:X1 L1 L2 R1 S1 Q1 Q7

## Settled facts (user-confirmed only)
_(none)_

## Compressed conversation
T1 — user: "Car selling app" → P1 G1:X1 G2:X1 G3:X1 G4:X1 L1 R1 S1 Q1 Q7
T2 — user: "Peer-to-peer marketplace connecting private car sellers with buyers — mobile-fir…" → P2 G1:X3 G2:X2 G3:X2 G4:X1 G6:X1 L1 L2 R1 S1 Q1 Q7
T3 — user: "MVP: create a listing with photos, browse and search listings, contact the selle…" → P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X1 L1 L2 R1 S1 Q1 Q7
T4 — user: "Trust is critical: light seller verification, report listing, and safety guidanc…" → P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X1 GD:X1 L1 L2 R1 S1 Q1 Q7
T5 — user: "Price is manual negotiation only — no automated pricing, auctions, or instant of…" → P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X1 GD:X1 L1 L2 R1 S1 Q1 Q7
T6 — user: "Out of scope for v1: financing, shipping, professional inspections, and dealer f…" → P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X2 GD:X1 L1 L2 R1 S1 Q1 Q7


--- NEW USER INPUT (SOURCE OF TRUTH THIS TURN) ---
Success means a completed sale handoff (buyer marks sold) and sellers who relist or sell again within 30 days.

```

#### <a id="turn-07-output"></a> 2 — Output

```text
P3 G1:X3 G2:X5 G3:X1 G4:X1 G6:X2 GD:X1 L1 L2 R1 S1 Q1 Q7
```

---

## Turn 08 — 2026-05-24T11:10:09.321718+00:00

**Model:** `gpt-4o-mini` · prep 1 ms · API wait 9117 ms

| # | What was sent to the LLM | Output | Token spend (input / output) | Total response time |
|---|--------------------------|--------|------------------------------|---------------------|
| **08** | [13,048 chars — expand](#turn-08-sent) | [56 chars — expand](#turn-08-output) | **3,608 / 37** (Σ 3,645) | **9117.9 ms** (9.118 s) |

#### <a id="turn-08-sent"></a> 1 — What was sent to the LLM

```text
=== SYSTEM — llm-rubric_v2.md only (10,989 chars) ===

# Discovery State Codes — v0.2 (48 codes)

> **Changelog from v0.1** (driven by the 10-turn pet-sitting + car-selling test runs):
> - **Added killer class `TRUST_SAFETY`** — both runs surfaced trust/safety as the dominant
>   risk and both times the taxonomy smeared it across `G7`/`G8`/`GA`. It now has a home.
> - **Added gap code `GD`** (trust/safety risk) → `TRUST_SAFETY`.
> - **Hardened the closed-vocabulary rule** — the model emitted `GCh` (invalid) in turn 10.
>   Any code outside this legend is invalid and must be rejected by a validator.
> - **Added "re-derive readiness each turn"** note — `L`/`R` codes were copied forward
>   unchanged across the run instead of being re-reasoned.

---

## What this is

A closed vocabulary the model **emits** to declare its read of the discovery, *after*
reasoning in full against the discovery rubric. The codes do not replace judgment — they
make it legible, enforceable, and continuous.

- **Source of truth:** the user's pitch and answers ONLY. The code profile is derived from
  user input each turn, never from the model's own prior output. Emitted codes are a
  projection of user truth, not a separate memory.
- **Hard line:** codes are OUTPUT, never INPUT. The model reads the rubric, assesses the
  conversation, then emits codes. It must never generate questions mechanically from codes
  while skipping the rubric.
- **Closed vocabulary:** only the codes in this document are valid. The model must NEVER
  invent a code (e.g. `GCh`). If no gap code fits, it emits `G0` and names the risk. A
  deterministic validator should reject any emitted token not in this legend.

---

## ⚠ Risk taxonomy — PROVISIONAL (still confirm before relying on this)

Every `G`, `L`, and `R` code points at one of these shippability killers. `TRUST_SAFETY`
is evidence-driven (added from the test runs); the other six remain derived-from-rubric,
not owner-confirmed. The runs only stress-tested **marketplace** pitches — a non-marketplace
domain may surface a different hole, so keep this flag until a non-marketplace pitch is run.

| Killer | Meaning |
|--------|---------|
| `WRONG_THING` | user / problem unproven → you build what nobody needs |
| `BOUNDLESS` | scope undefined → you build forever, never ship |
| `UNMEASURABLE` | no success signal → you can't tell if it worked |
| `FRAGILE` | failure / edge modes unhandled → it breaks in prod |
| `BUILT_ON_SAND` | assumptions unconfirmed → foundation collapses |
| `UNGOVERNED` | runtime / human-review / policy gaps → ships but can't be operated safely |
| `TRUST_SAFETY` | **participants can harm each other or be defrauded → ships but isn't safe to use** |

---

## G — Gap pointers (the 13 angles, recast as live risk exposures)

Each marks an unclosed risk and points at the question that closes it.

| Code | Emit-meaning | Risk class | Question it drives |
|------|--------------|------------|--------------------|
| `G1` | user unproven risk | WRONG_THING | who exactly, concretely |
| `G2` | outcome unproven risk | WRONG_THING | what job, measurably |
| `G3` | entry unproven risk | BOUNDLESS | how use begins |
| `G4` | workflow unproven risk | BOUNDLESS | the one core path |
| `G5` | success undefined risk | UNMEASURABLE | what proves it worked |
| `G6` | scope unbounded risk | BOUNDLESS | in vs out, v1 |
| `G7` | domain rule risk | UNGOVERNED | what constraint binds |
| `G8` | failure unhandled risk | FRAGILE | what happens broken |
| `G9` | tradeoff unsettled risk | BOUNDLESS | which competing option |
| `GA` | assumption unconfirmed risk | BUILT_ON_SAND | believe vs proven |
| `GB` | runtime policy risk | UNGOVERNED | how it operates live |
| `GC` | human review risk | UNGOVERNED | where humans intervene |
| `GD` | **trust/safety risk** | **TRUST_SAFETY** | **how participants are protected** |

### Open-class gap (catches risk the taxonomy can't name)

| Code | Emit-meaning | Forces |
|------|--------------|--------|
| `G0` | unnamed risk sensed | a shippability risk no `G1–GD` fits — model MUST name it in narrative and propose an angle. Each `G0` is a signal the taxonomy has a hole — log it. |

> **Note on `GD` vs `GC`:** `GC` stays "human review" (UNGOVERNED — *where humans intervene
> in the workflow*). `GD` is distinct: *protecting participants from each other* (fraud,
> unsafe meetups, bad actors). A decision can touch both; tag both when it does.

---

## X — Exposure (how hot is each gap; derived from user input only)

Attach to a gap code, e.g. `G6:X2` = scope answered-but-thin.

| Code | Emit-meaning | Risk meaning / next move |
|------|--------------|--------------------------|
| `X1` | open never touched | full risk live; strong candidate to ask |
| `X2` | answered but thin | risk MASKED not closed; press one follow-up |
| `X3` | answered with substance | risk genuinely lowered; stop asking |
| `X4` | inferred not confirmed | hidden risk (sand); convert to confirming MCQ |
| `X5` | user-settled hard | risk closed by user; lock, never re-ask |
| `X6` | contradicted by latest | prior closure undermined by new user input; reopen (no amend machinery — recompute yields this) |
| `X7` | answer revealed newrisk | a pick exposed a risk the batch wasn't probing; reopens selection this turn |
| `X8` | user volunteered offangle | free-text beyond the MCQ → primary signal, not noise; may spawn a new angle |

---

## P — Phase (macro gear; advances on user-input conditions)

| Code | Emit-meaning | Gate / effect |
|------|--------------|---------------|
| `P1` | dumping not probing | brain_dump; no MCQs; invite source material |
| `P2` | choosing the pace | mode_choice; no MCQs; offer fast vs coaching |
| `P3` | closing the gaps | elicitation; emit risk-ranked MCQ batch |
| `P4` | sealing the brief | closure; no MCQs; render brief from settled risks |

---

## L — Leverage (how the profile ranks the highest painpoint)

> **Re-derive each turn.** In the test run `L1` was copied forward unchanged across all 10
> turns. Leverage must be re-reasoned from the *current* open-gap set, not carried.

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `L1` | killer beats nicety | rank WRONG_THING / BOUNDLESS / TRUST_SAFETY gaps above polish |
| `L2` | unlocks many dimensions | prefer the gap that closes several at once |
| `L3` | sand before structure | confirm `X4` assumptions before building further |
| `L4` | one blocker first | if a blocker exists, confirm it before breadth |
| `L5` | thin masks danger | treat `X2` as risk, not progress |
| `L6` | nothing open stop | no live risk remains → advance phase |
| `L7` | reframe beats coverage | highest-leverage move is a reframe, not the next ranked gap → permit off-profile question |

---

## R — Readiness (risk-weighted; keeps "shippable" honest)

> **Re-derive each turn.** `R3` was held for eight straight turns while coverage climbed
> from 1 to 5 settled dimensions. Readiness must move as gaps close.

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `R1` | name risks first | list live risks before any percent |
| `R2` | pick-only caps low | MCQ-only-closed gap → dimension ≤ 65 |
| `R3` | unconfirmed caps hard | open `X4`/`X6` present → ready_capped held down |
| `R4` | killers block ship | any open killer-class gap → cannot exceed ~80 |
| `R5` | shippable needs proof | ≥88 only when killers all `X3`/`X5`, ≥12 closed |

---

## S — Safe-question shaping (let the user think; choose risk-free)

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `S1` | concrete not abstract | options are real choices, not "tell me more" |
| `S2` | lowest-risk default visible | include the safe/conservative option explicitly |
| `S3` | one decision each | one question closes one risk; no compound asks |
| `S4` | something-else opens subrisk | a "something else" pick spawns a `<parent>__<sub>` angle at `X1`, ranked high — the user found the gap, honour it |
| `S5` | name the tradeoff | when options compete, state what each costs |

---

## Q — Batch discipline (enforced on emitted codes)

| Code | Emit-meaning | Check |
|------|--------------|-------|
| `Q1` | one primary turn | single lead question unless confirming a blocker |
| `Q2` | no theme repeat | drop any angle already `X3`/`X5` |
| `Q3` | no batch collision | no two batch items share a gap code |
| `Q4` | drop paraphrase asked | drop items paraphrasing prior questions |
| `Q5` | highest leverage first | order batch by dimensions-unlocked |
| `Q6` | fewer than five | if <5 live risks open, ask only those — never pad |
| `Q7` | one open probe | reserve ONE batch item for a non-`G`-derived question the model judges valuable (guarantees a serendipity slot every turn) |

---

## C — Coaching voice (the BA tone, made legible)

| Code | Emit-meaning | Narrative effect |
|------|--------------|------------------|
| `C1` | acknowledge then reflect | open with warm ack + reflect understanding |
| `C2` | push thin answer | stress-test follow-up on an `X2` theme |
| `C3` | narrate the decision | one-line "Got it — X. Logged." on each `X5` |
| `C4` | request source material | brain_dump only: ask for memos / decks / threads |
| `C5` | offer two paths | mode_choice only: present fast vs coaching |

---

## Count

13 gap + 1 open-gap + 8 exposure + 4 phase + 7 leverage + 5 readiness + 5 shaping
+ 7 batch + 5 coaching. The emittable **behavioural set is 48 distinct codes**
(was 47; `GD` added). Exposure flags `X1–X8` attach to gaps as modifiers rather than
standing alone.

---

## RUBRIC ADDITION — paste into the discovery rubric

> **Emit your assessment as state codes.**
> After you have reasoned in full against this rubric — assessing the live discovery the
> way a senior BA would — also emit a single line of state codes that declares your read.
> Attach an exposure flag to each gap (e.g. `G6:X2`). The codes are a projection of the
> user's input, not a memory of your own prior turns: derive them only from what the user
> has actually said and picked.
>
> The codes do not decide your questions — your BA judgment does. Use them to (1) mark
> which shippability risks are still live, (2) rank which painpoint most threatens a
> shippable build, and (3) shape MCQs that let the user commit to the lowest-risk path.
>
> Only codes in the legend are valid — never invent a code. If you sense a risk no gap
> code names, emit `G0` and articulate it. Every elicitation turn must include one open
> probe (`Q7`). Re-derive leverage (`L`) and readiness (`R`) each turn from the current
> open-gap set — do not carry them forward unchanged.
>
> Example emitted line:
> `P3 G1:X5 G4:X3 G6:X2 G8:X1 GA:X4 GD:X1 L1 L3 L5 R3 S2 Q7`
> → elicitation; user & workflow closed; scope thin (press it); failure-modes wide open;
> one assumption built-on-sand to confirm; trust/safety still untouched; rank killers,
> confirm the sand, treat thin as danger; readiness held by the unconfirmed; surface the
> safe default; reserve an open probe.

=== USER — turn context (1,959 chars) ===

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
Car selling app

## Latest state codes
P3 G1:X3 G2:X5 G3:X1 G4:X1 G6:X2 GD:X1 L1 L2 R1 S1 Q1 Q7

## Settled facts (user-confirmed only)
_(none)_

## Compressed conversation
T1 — user: "Car selling app" → P1 G1:X1 G2:X1 G3:X1 G4:X1 L1 R1 S1 Q1 Q7
T2 — user: "Peer-to-peer marketplace connecting private car sellers with buyers — mobile-fir…" → P2 G1:X3 G2:X2 G3:X2 G4:X1 G6:X1 L1 L2 R1 S1 Q1 Q7
T3 — user: "MVP: create a listing with photos, browse and search listings, contact the selle…" → P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X1 L1 L2 R1 S1 Q1 Q7
T4 — user: "Trust is critical: light seller verification, report listing, and safety guidanc…" → P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X1 GD:X1 L1 L2 R1 S1 Q1 Q7
T5 — user: "Price is manual negotiation only — no automated pricing, auctions, or instant of…" → P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X1 GD:X1 L1 L2 R1 S1 Q1 Q7
T6 — user: "Out of scope for v1: financing, shipping, professional inspections, and dealer f…" → P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X2 GD:X1 L1 L2 R1 S1 Q1 Q7
T7 — user: "Success means a completed sale handoff (buyer marks sold) and sellers who relist…" → P3 G1:X3 G2:X5 G3:X1 G4:X1 G6:X2 GD:X1 L1 L2 R1 S1 Q1 Q7


--- NEW USER INPUT (SOURCE OF TRUTH THIS TURN) ---
Primary users: individuals selling one personal vehicle; buyers searching locally within about 50km.

```

#### <a id="turn-08-output"></a> 2 — Output

```text
P3 G1:X4 G2:X5 G3:X1 G4:X1 G6:X2 GD:X1 L1 L2 R1 S1 Q1 Q7
```

---

## Turn 09 — 2026-05-24T11:10:20.158581+00:00

**Model:** `gpt-4o-mini` · prep 0 ms · API wait 10400 ms

| # | What was sent to the LLM | Output | Token spend (input / output) | Total response time |
|---|--------------------------|--------|------------------------------|---------------------|
| **09** | [13,199 chars — expand](#turn-09-sent) | [56 chars — expand](#turn-09-output) | **3,669 / 37** (Σ 3,706) | **10400.5 ms** (10.400 s) |

#### <a id="turn-09-sent"></a> 1 — What was sent to the LLM

```text
=== SYSTEM — llm-rubric_v2.md only (10,989 chars) ===

# Discovery State Codes — v0.2 (48 codes)

> **Changelog from v0.1** (driven by the 10-turn pet-sitting + car-selling test runs):
> - **Added killer class `TRUST_SAFETY`** — both runs surfaced trust/safety as the dominant
>   risk and both times the taxonomy smeared it across `G7`/`G8`/`GA`. It now has a home.
> - **Added gap code `GD`** (trust/safety risk) → `TRUST_SAFETY`.
> - **Hardened the closed-vocabulary rule** — the model emitted `GCh` (invalid) in turn 10.
>   Any code outside this legend is invalid and must be rejected by a validator.
> - **Added "re-derive readiness each turn"** note — `L`/`R` codes were copied forward
>   unchanged across the run instead of being re-reasoned.

---

## What this is

A closed vocabulary the model **emits** to declare its read of the discovery, *after*
reasoning in full against the discovery rubric. The codes do not replace judgment — they
make it legible, enforceable, and continuous.

- **Source of truth:** the user's pitch and answers ONLY. The code profile is derived from
  user input each turn, never from the model's own prior output. Emitted codes are a
  projection of user truth, not a separate memory.
- **Hard line:** codes are OUTPUT, never INPUT. The model reads the rubric, assesses the
  conversation, then emits codes. It must never generate questions mechanically from codes
  while skipping the rubric.
- **Closed vocabulary:** only the codes in this document are valid. The model must NEVER
  invent a code (e.g. `GCh`). If no gap code fits, it emits `G0` and names the risk. A
  deterministic validator should reject any emitted token not in this legend.

---

## ⚠ Risk taxonomy — PROVISIONAL (still confirm before relying on this)

Every `G`, `L`, and `R` code points at one of these shippability killers. `TRUST_SAFETY`
is evidence-driven (added from the test runs); the other six remain derived-from-rubric,
not owner-confirmed. The runs only stress-tested **marketplace** pitches — a non-marketplace
domain may surface a different hole, so keep this flag until a non-marketplace pitch is run.

| Killer | Meaning |
|--------|---------|
| `WRONG_THING` | user / problem unproven → you build what nobody needs |
| `BOUNDLESS` | scope undefined → you build forever, never ship |
| `UNMEASURABLE` | no success signal → you can't tell if it worked |
| `FRAGILE` | failure / edge modes unhandled → it breaks in prod |
| `BUILT_ON_SAND` | assumptions unconfirmed → foundation collapses |
| `UNGOVERNED` | runtime / human-review / policy gaps → ships but can't be operated safely |
| `TRUST_SAFETY` | **participants can harm each other or be defrauded → ships but isn't safe to use** |

---

## G — Gap pointers (the 13 angles, recast as live risk exposures)

Each marks an unclosed risk and points at the question that closes it.

| Code | Emit-meaning | Risk class | Question it drives |
|------|--------------|------------|--------------------|
| `G1` | user unproven risk | WRONG_THING | who exactly, concretely |
| `G2` | outcome unproven risk | WRONG_THING | what job, measurably |
| `G3` | entry unproven risk | BOUNDLESS | how use begins |
| `G4` | workflow unproven risk | BOUNDLESS | the one core path |
| `G5` | success undefined risk | UNMEASURABLE | what proves it worked |
| `G6` | scope unbounded risk | BOUNDLESS | in vs out, v1 |
| `G7` | domain rule risk | UNGOVERNED | what constraint binds |
| `G8` | failure unhandled risk | FRAGILE | what happens broken |
| `G9` | tradeoff unsettled risk | BOUNDLESS | which competing option |
| `GA` | assumption unconfirmed risk | BUILT_ON_SAND | believe vs proven |
| `GB` | runtime policy risk | UNGOVERNED | how it operates live |
| `GC` | human review risk | UNGOVERNED | where humans intervene |
| `GD` | **trust/safety risk** | **TRUST_SAFETY** | **how participants are protected** |

### Open-class gap (catches risk the taxonomy can't name)

| Code | Emit-meaning | Forces |
|------|--------------|--------|
| `G0` | unnamed risk sensed | a shippability risk no `G1–GD` fits — model MUST name it in narrative and propose an angle. Each `G0` is a signal the taxonomy has a hole — log it. |

> **Note on `GD` vs `GC`:** `GC` stays "human review" (UNGOVERNED — *where humans intervene
> in the workflow*). `GD` is distinct: *protecting participants from each other* (fraud,
> unsafe meetups, bad actors). A decision can touch both; tag both when it does.

---

## X — Exposure (how hot is each gap; derived from user input only)

Attach to a gap code, e.g. `G6:X2` = scope answered-but-thin.

| Code | Emit-meaning | Risk meaning / next move |
|------|--------------|--------------------------|
| `X1` | open never touched | full risk live; strong candidate to ask |
| `X2` | answered but thin | risk MASKED not closed; press one follow-up |
| `X3` | answered with substance | risk genuinely lowered; stop asking |
| `X4` | inferred not confirmed | hidden risk (sand); convert to confirming MCQ |
| `X5` | user-settled hard | risk closed by user; lock, never re-ask |
| `X6` | contradicted by latest | prior closure undermined by new user input; reopen (no amend machinery — recompute yields this) |
| `X7` | answer revealed newrisk | a pick exposed a risk the batch wasn't probing; reopens selection this turn |
| `X8` | user volunteered offangle | free-text beyond the MCQ → primary signal, not noise; may spawn a new angle |

---

## P — Phase (macro gear; advances on user-input conditions)

| Code | Emit-meaning | Gate / effect |
|------|--------------|---------------|
| `P1` | dumping not probing | brain_dump; no MCQs; invite source material |
| `P2` | choosing the pace | mode_choice; no MCQs; offer fast vs coaching |
| `P3` | closing the gaps | elicitation; emit risk-ranked MCQ batch |
| `P4` | sealing the brief | closure; no MCQs; render brief from settled risks |

---

## L — Leverage (how the profile ranks the highest painpoint)

> **Re-derive each turn.** In the test run `L1` was copied forward unchanged across all 10
> turns. Leverage must be re-reasoned from the *current* open-gap set, not carried.

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `L1` | killer beats nicety | rank WRONG_THING / BOUNDLESS / TRUST_SAFETY gaps above polish |
| `L2` | unlocks many dimensions | prefer the gap that closes several at once |
| `L3` | sand before structure | confirm `X4` assumptions before building further |
| `L4` | one blocker first | if a blocker exists, confirm it before breadth |
| `L5` | thin masks danger | treat `X2` as risk, not progress |
| `L6` | nothing open stop | no live risk remains → advance phase |
| `L7` | reframe beats coverage | highest-leverage move is a reframe, not the next ranked gap → permit off-profile question |

---

## R — Readiness (risk-weighted; keeps "shippable" honest)

> **Re-derive each turn.** `R3` was held for eight straight turns while coverage climbed
> from 1 to 5 settled dimensions. Readiness must move as gaps close.

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `R1` | name risks first | list live risks before any percent |
| `R2` | pick-only caps low | MCQ-only-closed gap → dimension ≤ 65 |
| `R3` | unconfirmed caps hard | open `X4`/`X6` present → ready_capped held down |
| `R4` | killers block ship | any open killer-class gap → cannot exceed ~80 |
| `R5` | shippable needs proof | ≥88 only when killers all `X3`/`X5`, ≥12 closed |

---

## S — Safe-question shaping (let the user think; choose risk-free)

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `S1` | concrete not abstract | options are real choices, not "tell me more" |
| `S2` | lowest-risk default visible | include the safe/conservative option explicitly |
| `S3` | one decision each | one question closes one risk; no compound asks |
| `S4` | something-else opens subrisk | a "something else" pick spawns a `<parent>__<sub>` angle at `X1`, ranked high — the user found the gap, honour it |
| `S5` | name the tradeoff | when options compete, state what each costs |

---

## Q — Batch discipline (enforced on emitted codes)

| Code | Emit-meaning | Check |
|------|--------------|-------|
| `Q1` | one primary turn | single lead question unless confirming a blocker |
| `Q2` | no theme repeat | drop any angle already `X3`/`X5` |
| `Q3` | no batch collision | no two batch items share a gap code |
| `Q4` | drop paraphrase asked | drop items paraphrasing prior questions |
| `Q5` | highest leverage first | order batch by dimensions-unlocked |
| `Q6` | fewer than five | if <5 live risks open, ask only those — never pad |
| `Q7` | one open probe | reserve ONE batch item for a non-`G`-derived question the model judges valuable (guarantees a serendipity slot every turn) |

---

## C — Coaching voice (the BA tone, made legible)

| Code | Emit-meaning | Narrative effect |
|------|--------------|------------------|
| `C1` | acknowledge then reflect | open with warm ack + reflect understanding |
| `C2` | push thin answer | stress-test follow-up on an `X2` theme |
| `C3` | narrate the decision | one-line "Got it — X. Logged." on each `X5` |
| `C4` | request source material | brain_dump only: ask for memos / decks / threads |
| `C5` | offer two paths | mode_choice only: present fast vs coaching |

---

## Count

13 gap + 1 open-gap + 8 exposure + 4 phase + 7 leverage + 5 readiness + 5 shaping
+ 7 batch + 5 coaching. The emittable **behavioural set is 48 distinct codes**
(was 47; `GD` added). Exposure flags `X1–X8` attach to gaps as modifiers rather than
standing alone.

---

## RUBRIC ADDITION — paste into the discovery rubric

> **Emit your assessment as state codes.**
> After you have reasoned in full against this rubric — assessing the live discovery the
> way a senior BA would — also emit a single line of state codes that declares your read.
> Attach an exposure flag to each gap (e.g. `G6:X2`). The codes are a projection of the
> user's input, not a memory of your own prior turns: derive them only from what the user
> has actually said and picked.
>
> The codes do not decide your questions — your BA judgment does. Use them to (1) mark
> which shippability risks are still live, (2) rank which painpoint most threatens a
> shippable build, and (3) shape MCQs that let the user commit to the lowest-risk path.
>
> Only codes in the legend are valid — never invent a code. If you sense a risk no gap
> code names, emit `G0` and articulate it. Every elicitation turn must include one open
> probe (`Q7`). Re-derive leverage (`L`) and readiness (`R`) each turn from the current
> open-gap set — do not carry them forward unchanged.
>
> Example emitted line:
> `P3 G1:X5 G4:X3 G6:X2 G8:X1 GA:X4 GD:X1 L1 L3 L5 R3 S2 Q7`
> → elicitation; user & workflow closed; scope thin (press it); failure-modes wide open;
> one assumption built-on-sand to confirm; trust/safety still untouched; rank killers,
> confirm the sand, treat thin as danger; readiness held by the unconfirmed; surface the
> safe default; reserve an open probe.

=== USER — turn context (2,110 chars) ===

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
Car selling app

## Latest state codes
P3 G1:X4 G2:X5 G3:X1 G4:X1 G6:X2 GD:X1 L1 L2 R1 S1 Q1 Q7

## Settled facts (user-confirmed only)
_(none)_

## Compressed conversation
T1 — user: "Car selling app" → P1 G1:X1 G2:X1 G3:X1 G4:X1 L1 R1 S1 Q1 Q7
T2 — user: "Peer-to-peer marketplace connecting private car sellers with buyers — mobile-fir…" → P2 G1:X3 G2:X2 G3:X2 G4:X1 G6:X1 L1 L2 R1 S1 Q1 Q7
T3 — user: "MVP: create a listing with photos, browse and search listings, contact the selle…" → P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X1 L1 L2 R1 S1 Q1 Q7
T4 — user: "Trust is critical: light seller verification, report listing, and safety guidanc…" → P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X1 GD:X1 L1 L2 R1 S1 Q1 Q7
T5 — user: "Price is manual negotiation only — no automated pricing, auctions, or instant of…" → P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X1 GD:X1 L1 L2 R1 S1 Q1 Q7
T6 — user: "Out of scope for v1: financing, shipping, professional inspections, and dealer f…" → P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X2 GD:X1 L1 L2 R1 S1 Q1 Q7
T7 — user: "Success means a completed sale handoff (buyer marks sold) and sellers who relist…" → P3 G1:X3 G2:X5 G3:X1 G4:X1 G6:X2 GD:X1 L1 L2 R1 S1 Q1 Q7
T8 — user: "Primary users: individuals selling one personal vehicle; buyers searching locall…" → P3 G1:X4 G2:X5 G3:X1 G4:X1 G6:X2 GD:X1 L1 L2 R1 S1 Q1 Q7


--- NEW USER INPUT (SOURCE OF TRUTH THIS TURN) ---
Biggest risk to avoid: scams and unsafe meetups — optimise for fraud prevention over user growth.

```

#### <a id="turn-09-output"></a> 2 — Output

```text
P3 G1:X4 G2:X5 G3:X1 G4:X1 G6:X2 GD:X1 L1 L2 R1 S1 Q1 Q7
```

---

## Turn 10 — 2026-05-24T11:10:30.847435+00:00

**Model:** `gpt-4o-mini` · prep 0 ms · API wait 9952 ms

| # | What was sent to the LLM | Output | Token spend (input / output) | Total response time |
|---|--------------------------|--------|------------------------------|---------------------|
| **10** | [13,379 chars — expand](#turn-10-sent) | [56 chars — expand](#turn-10-output) | **3,737 / 37** (Σ 3,774) | **9951.8 ms** (9.952 s) |

#### <a id="turn-10-sent"></a> 1 — What was sent to the LLM

```text
=== SYSTEM — llm-rubric_v2.md only (10,989 chars) ===

# Discovery State Codes — v0.2 (48 codes)

> **Changelog from v0.1** (driven by the 10-turn pet-sitting + car-selling test runs):
> - **Added killer class `TRUST_SAFETY`** — both runs surfaced trust/safety as the dominant
>   risk and both times the taxonomy smeared it across `G7`/`G8`/`GA`. It now has a home.
> - **Added gap code `GD`** (trust/safety risk) → `TRUST_SAFETY`.
> - **Hardened the closed-vocabulary rule** — the model emitted `GCh` (invalid) in turn 10.
>   Any code outside this legend is invalid and must be rejected by a validator.
> - **Added "re-derive readiness each turn"** note — `L`/`R` codes were copied forward
>   unchanged across the run instead of being re-reasoned.

---

## What this is

A closed vocabulary the model **emits** to declare its read of the discovery, *after*
reasoning in full against the discovery rubric. The codes do not replace judgment — they
make it legible, enforceable, and continuous.

- **Source of truth:** the user's pitch and answers ONLY. The code profile is derived from
  user input each turn, never from the model's own prior output. Emitted codes are a
  projection of user truth, not a separate memory.
- **Hard line:** codes are OUTPUT, never INPUT. The model reads the rubric, assesses the
  conversation, then emits codes. It must never generate questions mechanically from codes
  while skipping the rubric.
- **Closed vocabulary:** only the codes in this document are valid. The model must NEVER
  invent a code (e.g. `GCh`). If no gap code fits, it emits `G0` and names the risk. A
  deterministic validator should reject any emitted token not in this legend.

---

## ⚠ Risk taxonomy — PROVISIONAL (still confirm before relying on this)

Every `G`, `L`, and `R` code points at one of these shippability killers. `TRUST_SAFETY`
is evidence-driven (added from the test runs); the other six remain derived-from-rubric,
not owner-confirmed. The runs only stress-tested **marketplace** pitches — a non-marketplace
domain may surface a different hole, so keep this flag until a non-marketplace pitch is run.

| Killer | Meaning |
|--------|---------|
| `WRONG_THING` | user / problem unproven → you build what nobody needs |
| `BOUNDLESS` | scope undefined → you build forever, never ship |
| `UNMEASURABLE` | no success signal → you can't tell if it worked |
| `FRAGILE` | failure / edge modes unhandled → it breaks in prod |
| `BUILT_ON_SAND` | assumptions unconfirmed → foundation collapses |
| `UNGOVERNED` | runtime / human-review / policy gaps → ships but can't be operated safely |
| `TRUST_SAFETY` | **participants can harm each other or be defrauded → ships but isn't safe to use** |

---

## G — Gap pointers (the 13 angles, recast as live risk exposures)

Each marks an unclosed risk and points at the question that closes it.

| Code | Emit-meaning | Risk class | Question it drives |
|------|--------------|------------|--------------------|
| `G1` | user unproven risk | WRONG_THING | who exactly, concretely |
| `G2` | outcome unproven risk | WRONG_THING | what job, measurably |
| `G3` | entry unproven risk | BOUNDLESS | how use begins |
| `G4` | workflow unproven risk | BOUNDLESS | the one core path |
| `G5` | success undefined risk | UNMEASURABLE | what proves it worked |
| `G6` | scope unbounded risk | BOUNDLESS | in vs out, v1 |
| `G7` | domain rule risk | UNGOVERNED | what constraint binds |
| `G8` | failure unhandled risk | FRAGILE | what happens broken |
| `G9` | tradeoff unsettled risk | BOUNDLESS | which competing option |
| `GA` | assumption unconfirmed risk | BUILT_ON_SAND | believe vs proven |
| `GB` | runtime policy risk | UNGOVERNED | how it operates live |
| `GC` | human review risk | UNGOVERNED | where humans intervene |
| `GD` | **trust/safety risk** | **TRUST_SAFETY** | **how participants are protected** |

### Open-class gap (catches risk the taxonomy can't name)

| Code | Emit-meaning | Forces |
|------|--------------|--------|
| `G0` | unnamed risk sensed | a shippability risk no `G1–GD` fits — model MUST name it in narrative and propose an angle. Each `G0` is a signal the taxonomy has a hole — log it. |

> **Note on `GD` vs `GC`:** `GC` stays "human review" (UNGOVERNED — *where humans intervene
> in the workflow*). `GD` is distinct: *protecting participants from each other* (fraud,
> unsafe meetups, bad actors). A decision can touch both; tag both when it does.

---

## X — Exposure (how hot is each gap; derived from user input only)

Attach to a gap code, e.g. `G6:X2` = scope answered-but-thin.

| Code | Emit-meaning | Risk meaning / next move |
|------|--------------|--------------------------|
| `X1` | open never touched | full risk live; strong candidate to ask |
| `X2` | answered but thin | risk MASKED not closed; press one follow-up |
| `X3` | answered with substance | risk genuinely lowered; stop asking |
| `X4` | inferred not confirmed | hidden risk (sand); convert to confirming MCQ |
| `X5` | user-settled hard | risk closed by user; lock, never re-ask |
| `X6` | contradicted by latest | prior closure undermined by new user input; reopen (no amend machinery — recompute yields this) |
| `X7` | answer revealed newrisk | a pick exposed a risk the batch wasn't probing; reopens selection this turn |
| `X8` | user volunteered offangle | free-text beyond the MCQ → primary signal, not noise; may spawn a new angle |

---

## P — Phase (macro gear; advances on user-input conditions)

| Code | Emit-meaning | Gate / effect |
|------|--------------|---------------|
| `P1` | dumping not probing | brain_dump; no MCQs; invite source material |
| `P2` | choosing the pace | mode_choice; no MCQs; offer fast vs coaching |
| `P3` | closing the gaps | elicitation; emit risk-ranked MCQ batch |
| `P4` | sealing the brief | closure; no MCQs; render brief from settled risks |

---

## L — Leverage (how the profile ranks the highest painpoint)

> **Re-derive each turn.** In the test run `L1` was copied forward unchanged across all 10
> turns. Leverage must be re-reasoned from the *current* open-gap set, not carried.

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `L1` | killer beats nicety | rank WRONG_THING / BOUNDLESS / TRUST_SAFETY gaps above polish |
| `L2` | unlocks many dimensions | prefer the gap that closes several at once |
| `L3` | sand before structure | confirm `X4` assumptions before building further |
| `L4` | one blocker first | if a blocker exists, confirm it before breadth |
| `L5` | thin masks danger | treat `X2` as risk, not progress |
| `L6` | nothing open stop | no live risk remains → advance phase |
| `L7` | reframe beats coverage | highest-leverage move is a reframe, not the next ranked gap → permit off-profile question |

---

## R — Readiness (risk-weighted; keeps "shippable" honest)

> **Re-derive each turn.** `R3` was held for eight straight turns while coverage climbed
> from 1 to 5 settled dimensions. Readiness must move as gaps close.

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `R1` | name risks first | list live risks before any percent |
| `R2` | pick-only caps low | MCQ-only-closed gap → dimension ≤ 65 |
| `R3` | unconfirmed caps hard | open `X4`/`X6` present → ready_capped held down |
| `R4` | killers block ship | any open killer-class gap → cannot exceed ~80 |
| `R5` | shippable needs proof | ≥88 only when killers all `X3`/`X5`, ≥12 closed |

---

## S — Safe-question shaping (let the user think; choose risk-free)

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `S1` | concrete not abstract | options are real choices, not "tell me more" |
| `S2` | lowest-risk default visible | include the safe/conservative option explicitly |
| `S3` | one decision each | one question closes one risk; no compound asks |
| `S4` | something-else opens subrisk | a "something else" pick spawns a `<parent>__<sub>` angle at `X1`, ranked high — the user found the gap, honour it |
| `S5` | name the tradeoff | when options compete, state what each costs |

---

## Q — Batch discipline (enforced on emitted codes)

| Code | Emit-meaning | Check |
|------|--------------|-------|
| `Q1` | one primary turn | single lead question unless confirming a blocker |
| `Q2` | no theme repeat | drop any angle already `X3`/`X5` |
| `Q3` | no batch collision | no two batch items share a gap code |
| `Q4` | drop paraphrase asked | drop items paraphrasing prior questions |
| `Q5` | highest leverage first | order batch by dimensions-unlocked |
| `Q6` | fewer than five | if <5 live risks open, ask only those — never pad |
| `Q7` | one open probe | reserve ONE batch item for a non-`G`-derived question the model judges valuable (guarantees a serendipity slot every turn) |

---

## C — Coaching voice (the BA tone, made legible)

| Code | Emit-meaning | Narrative effect |
|------|--------------|------------------|
| `C1` | acknowledge then reflect | open with warm ack + reflect understanding |
| `C2` | push thin answer | stress-test follow-up on an `X2` theme |
| `C3` | narrate the decision | one-line "Got it — X. Logged." on each `X5` |
| `C4` | request source material | brain_dump only: ask for memos / decks / threads |
| `C5` | offer two paths | mode_choice only: present fast vs coaching |

---

## Count

13 gap + 1 open-gap + 8 exposure + 4 phase + 7 leverage + 5 readiness + 5 shaping
+ 7 batch + 5 coaching. The emittable **behavioural set is 48 distinct codes**
(was 47; `GD` added). Exposure flags `X1–X8` attach to gaps as modifiers rather than
standing alone.

---

## RUBRIC ADDITION — paste into the discovery rubric

> **Emit your assessment as state codes.**
> After you have reasoned in full against this rubric — assessing the live discovery the
> way a senior BA would — also emit a single line of state codes that declares your read.
> Attach an exposure flag to each gap (e.g. `G6:X2`). The codes are a projection of the
> user's input, not a memory of your own prior turns: derive them only from what the user
> has actually said and picked.
>
> The codes do not decide your questions — your BA judgment does. Use them to (1) mark
> which shippability risks are still live, (2) rank which painpoint most threatens a
> shippable build, and (3) shape MCQs that let the user commit to the lowest-risk path.
>
> Only codes in the legend are valid — never invent a code. If you sense a risk no gap
> code names, emit `G0` and articulate it. Every elicitation turn must include one open
> probe (`Q7`). Re-derive leverage (`L`) and readiness (`R`) each turn from the current
> open-gap set — do not carry them forward unchanged.
>
> Example emitted line:
> `P3 G1:X5 G4:X3 G6:X2 G8:X1 GA:X4 GD:X1 L1 L3 L5 R3 S2 Q7`
> → elicitation; user & workflow closed; scope thin (press it); failure-modes wide open;
> one assumption built-on-sand to confirm; trust/safety still untouched; rank killers,
> confirm the sand, treat thin as danger; readiness held by the unconfirmed; surface the
> safe default; reserve an open probe.

=== USER — turn context (2,290 chars) ===

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
Car selling app

## Latest state codes
P3 G1:X4 G2:X5 G3:X1 G4:X1 G6:X2 GD:X1 L1 L2 R1 S1 Q1 Q7

## Settled facts (user-confirmed only)
_(none)_

## Compressed conversation
T1 — user: "Car selling app" → P1 G1:X1 G2:X1 G3:X1 G4:X1 L1 R1 S1 Q1 Q7
T2 — user: "Peer-to-peer marketplace connecting private car sellers with buyers — mobile-fir…" → P2 G1:X3 G2:X2 G3:X2 G4:X1 G6:X1 L1 L2 R1 S1 Q1 Q7
T3 — user: "MVP: create a listing with photos, browse and search listings, contact the selle…" → P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X1 L1 L2 R1 S1 Q1 Q7
T4 — user: "Trust is critical: light seller verification, report listing, and safety guidanc…" → P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X1 GD:X1 L1 L2 R1 S1 Q1 Q7
T5 — user: "Price is manual negotiation only — no automated pricing, auctions, or instant of…" → P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X1 GD:X1 L1 L2 R1 S1 Q1 Q7
T6 — user: "Out of scope for v1: financing, shipping, professional inspections, and dealer f…" → P3 G1:X3 G2:X3 G3:X1 G4:X1 G6:X2 GD:X1 L1 L2 R1 S1 Q1 Q7
T7 — user: "Success means a completed sale handoff (buyer marks sold) and sellers who relist…" → P3 G1:X3 G2:X5 G3:X1 G4:X1 G6:X2 GD:X1 L1 L2 R1 S1 Q1 Q7
T8 — user: "Primary users: individuals selling one personal vehicle; buyers searching locall…" → P3 G1:X4 G2:X5 G3:X1 G4:X1 G6:X2 GD:X1 L1 L2 R1 S1 Q1 Q7
T9 — user: "Biggest risk to avoid: scams and unsafe meetups — optimise for fraud prevention …" → P3 G1:X4 G2:X5 G3:X1 G4:X1 G6:X2 GD:X1 L1 L2 R1 S1 Q1 Q7


--- NEW USER INPUT (SOURCE OF TRUTH THIS TURN) ---
After contact, buyers and sellers use in-app chat until the deal is done; sharing phone numbers is optional, not required.

```

#### <a id="turn-10-output"></a> 2 — Output

```text
P3 G1:X4 G2:X5 G3:X1 G4:X1 G6:X2 GD:X2 L1 L2 R1 S1 Q1 Q7
```
