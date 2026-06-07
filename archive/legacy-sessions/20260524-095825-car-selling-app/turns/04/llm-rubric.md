# Discovery State Codes — v0.1 (47 codes)

**What this is:** a closed vocabulary the model emits to declare its read of the discovery, after reasoning in full against the discovery rubric. The codes do not replace judgment — they make it legible, enforceable, and continuous.

**Source of truth:** the user's pitch and answers ONLY. The code profile is derived from user input each turn, never from the model's own prior output. The model's emitted codes are a projection of user truth, not a separate memory.

**Hard line:** codes are OUTPUT, never INPUT. The model reads the rubric, assesses the conversation, then emits codes. It must never generate questions mechanically from codes while skipping the rubric.

---

## Risk taxonomy — PROVISIONAL (confirm before relying on this)

Every G, L, and R code points at one of these shippability killers. These are derived from the rubric's 14 dimensions, not confirmed by the product owner. If the real "what kills a build" list differs, replace this block and the G/L/R codes re-point.

| Risk class | Meaning |
|------------|---------|
| WRONG_THING | user / problem unproven → you build what nobody needs |
| BOUNDLESS | scope undefined → you build forever, never ship |
| UNMEASURABLE | no success signal → you can't tell if it worked |
| FRAGILE | failure / edge modes unhandled → it breaks in prod |
| BUILT_ON_SAND | assumptions unconfirmed → foundation collapses |
| UNGOVERNED | runtime / human-review / policy gaps → ships but can't be operated safely |

---

## G — Gap pointers (the 12 angles, recast as live risk exposures)

Each marks an unclosed risk and points at the question that closes it.

| Code | Emit meaning | Risk class | Question it drives |
|------|--------------|------------|-------------------|
| G1 | user unproven risk | WRONG_THING | who exactly, concretely |
| G2 | outcome unproven risk | WRONG_THING | what job, measurably |
| G3 | entry unproven risk | BOUNDLESS | how use begins |
| G4 | workflow unproven risk | BOUNDLESS | the one core path |
| G5 | success undefined risk | UNMEASURABLE | what proves it worked |
| G6 | scope unbounded risk | BOUNDLESS | in vs out, v1 |
| G7 | domain rule risk | UNGOVERNED | what constraint binds |
| G8 | failure unhandled risk | FRAGILE | what happens broken |
| G9 | tradeoff unsettled risk | BOUNDLESS | which competing option |
| GA | assumption unconfirmed risk | BUILT_ON_SAND | believe vs proven |
| GB | runtime policy risk | UNGOVERNED | how it operates live |
| GC | human review risk | UNGOVERNED | where humans intervene |

### Open-class gap (catches risk the taxonomy can't name)

| Code | Emit meaning | Forces |
|------|--------------|--------|
| G0 | unnamed risk sensed | a shippability risk no G1–GC fits — model MUST name it in narrative and propose an angle. Each G0 is a signal your taxonomy has a hole — log it. |

---

## X — Exposure (how hot is each gap; derived from user input only)

Attach to a gap code, e.g. `G6:X2` = scope answered-but-thin.

| Code | Emit meaning | Risk meaning / next move |
|------|--------------|--------------------------|
| X1 | open never touched | full risk live; strong candidate to ask |
| X2 | answered but thin | risk MASKED not closed; press one follow-up |
| X3 | answered with substance | risk genuinely lowered; stop asking |
| X4 | inferred not confirmed | hidden risk (sand); convert to confirming MCQ |
| X5 | user-settled hard | risk closed by user; lock, never re-ask |
| X6 | contradicted by latest | prior closure undermined by new user input; reopen (no amend machinery — recompute yields this) |
| X7 | answer revealed new risk | a pick exposed a risk the batch wasn't probing; reopens selection this turn |
| X8 | user volunteered off-angle | free-text beyond the MCQ → primary signal, not noise; may spawn a new angle |

---

## P — Phase (macro gear; advances on user-input conditions)

| Code | Emit meaning | Gate / effect |
|------|--------------|---------------|
| P1 | dumping not probing | brain_dump; no MCQs; invite source material |
| P2 | choosing the pace | mode_choice; no MCQs; offer fast vs coaching |
| P3 | closing the gap | elicitation; emit risk-ranked MCQ batch |
| P4 | sealing the brief | closure; no MCQs; render brief from settled risks |

---

## L — Leverage (how the profile ranks the highest painpoint)

| Code | Emit meaning | Effect |
|------|--------------|--------|
| L1 | killer beats nicety | rank WRONG_THING / BOUNDLESS gaps above polish |
| L2 | unlocks many dimensions | prefer the gap that closes several at once |
| L3 | sand before structure | confirm X4 assumptions before building further |
| L4 | one blocker first | if a blocker exists, confirm it before breadth |
| L5 | thin masks danger | treat X2 as risk, not progress |
| L6 | nothing open stop | no live risk remains → advance phase |
| L7 | reframe beats coverage | highest-leverage move is a reframe, not the next ranked gap → permit off-profile question |

---

## R — Readiness (risk-weighted; keeps "shippable" honest)

| Code | Emit meaning | Effect |
|------|--------------|--------|
| R1 | name risks first | list live risks before any percent |
| R2 | pick-only caps low | MCQ-only-closed gap → dimension ≤ 65 |
| R3 | unconfirmed caps hard | open X4/X6 present → ready_capped held down |
| R4 | killers block ship | any open killer-class gap → cannot exceed ~80 |
| R5 | shippable needs proof | ≥88 only when killers all X3/X5, ≥12 closed |

---

## S — Safe-question shaping (let the user think; choose risk-free)

| Code | Emit meaning | Effect |
|------|--------------|--------|
| S1 | concrete not abstract | options are real choices, not "tell me more" |
| S2 | lowest-risk default visible | include the safe/conservative option explicitly |
| S3 | one decision each | one question closes one risk; no compound asks |
| S4 | something-else opens sub-risk | a "something else" pick spawns a `<parent>__<sub>` angle at X1, ranked high — the user found the gap, honour it |
| S5 | name the tradeoff | when options compete, state what each costs |

---

## Q — Batch discipline (enforced on emitted codes)

| Code | Emit meaning | Check |
|------|--------------|-------|
| Q1 | one primary turn | single lead question unless confirming a blocker |
| Q2 | no theme repeat | drop any angle already X3/X5 |
| Q3 | no batch collision | no two batch items share a gap code |
| Q4 | drop paraphrase asked | drop items paraphrasing prior questions |
| Q5 | highest leverage first | order batch by dimensions-unlocked |
| Q6 | fewer than five | if <5 live risks open, ask only those — never pad |
| Q7 | one open probe | reserve ONE batch item for a non-G-derived question the model judges valuable (guarantees a serendipity slot every turn) |

---

## C — Coaching voice (the BA tone, made legible)

| Code | Emit meaning | Narrative effect |
|------|--------------|------------------|
| C1 | acknowledge then reflect | open with warm ack + reflect understanding |
| C2 | push thin answer | stress-test follow-up on an X2 theme |
| C3 | narrate the decision | one-line "Got it — X. Logged." on each X5 |
| C4 | request source material | brain_dump only: ask for memos / decks / threads |
| C5 | offer two paths | mode_choice only: present fast vs coaching |

---

## Count

| Category | Count |
|----------|-------|
| Gap (G1–GC) | 12 |
| Open gap (G0) | 1 |
| Exposure (X1–X8) | 8 (modifiers attached to gaps) |
| Phase (P) | 4 |
| Leverage (L) | 7 |
| Readiness (R) | 5 |
| Shaping (S) | 5 |
| Batch (Q) | 7 |
| Coaching (C) | 5 |
| **Emittable behavioural codes** | **47** |

Exposure flags X1–X8 attach to gaps rather than standing alone, so the emittable behavioural set is the 47 you approved; the X-flags are modifiers.

---

## RUBRIC ADDITION — paste into the discovery rubric

**Emit your assessment as state codes.**

After you have reasoned in full against this rubric — assessing the live discovery the way a senior BA would — also emit a single line of state codes that declares your read. Attach an exposure flag to each gap (e.g. `G6:X2`). The codes are a projection of the user's input, not a memory of your own prior turns: derive them only from what the user has actually said and picked.

The codes do not decide your questions — your BA judgment does. Use them to:

1. mark which shippability risks are still live,
2. rank which painpoint most threatens a shippable build, and
3. shape MCQs that let the user commit to the lowest-risk path.

If you sense a risk no gap code names, emit G0 and articulate it. Every elicitation turn must include one open probe (Q7) — a question the code profile did not generate.

**Example emitted line:**

```
P3 G1:X5 G4:X3 G6:X2 G8:X1 GA:X4 L1 L3 L5 R3 S2 Q7
```

→ elicitation; user & workflow closed; scope thin (press it); failure-modes wide open; one assumption built-on-sand to confirm; rank killers, confirm the sand, treat thin as danger; readiness held by the unconfirmed; surface the safe default; reserve an open probe.
