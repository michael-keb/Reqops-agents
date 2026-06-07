# Discovery State Codes — v0.3 (64 codes)

> **Changelog from v0.2**
> - **G — probing drivers:** each gap has a paragraph **Probe** (for MCQ framing) + **Closure test**. Framework-noun answers do not satisfy closure.
> - **X9** — exposure for “question asked last turn; awaiting qualifying answer” (turn-attribution closes GA/GB/GC-style staleness).
> - **Collapse rules:** **`L2`** + **`Q8`** — ops cluster `{G7, GA, GB, GC, GD}` collapses to one primary fork per user concern; **`L8`** — depth-over-breadth when most gaps settled.
> - **P3 / Q1 / Q6 / Q7** — aim at **one primary MCQ per turn** where the pipeline honors it; **Q7 only when earned** (X8, L7, or uncovered angle).
> - **R5** drops “≥12 closed”; adds **`R6` brief-ready**; **`R1`** names blockers in plain language before any percent.
> - **S** renamed to **Sharp shaping**: adds **`S6`–`S8`** (counterfactual stems, mutually exclusive options, ban framework-only closes).
> - **C2** strengthened (counter-argument); adds **`C6`–`C7`** (name cost; blocker callout).
>
> *(v0.1 → v0.2: killer `TRUST_SAFETY`, gap `GD`, closed vocabulary enforcement, L/R re-derive note.)*

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
- **Closure-first:** advancing a gap to `X3`/`X5` requires passing that gap's **Closure test**.
  Mentioning keywords, long prose, or pick-only shortcuts does not suffice when the closure
  test demands names, thresholds, owners, triggers, or scenarios (see **`S8`**).
- **Closed vocabulary:** only the codes in this document are valid. The model must NEVER
  invent a code (e.g. `GCh`). If no gap code fits, it emits `G0` and names the risk. A
  deterministic validator should reject any emitted token not in this legend.

---

## Risk taxonomy — PROVISIONAL

Every `G`, `L`, and `R` code points at one of these shippability killers.

| Killer | Meaning |
|--------|---------|
| `WRONG_THING` | user / problem unproven → you build what nobody needs |
| `BOUNDLESS` | scope undefined → you build forever, never ship |
| `UNMEASURABLE` | no success signal → you can't tell if it worked |
| `FRAGILE` | failure / edge modes unhandled → it breaks in prod |
| `BUILT_ON_SAND` | assumptions unconfirmed → foundation collapses |
| `UNGOVERNED` | **ship rule undefined** — no binding policy for live behaviour (ops, escalation, moderation) — ranks risk; **not** permission to split one concern into parallel MCQs (see **`Q8`**) |
| `TRUST_SAFETY` | **participants can harm each other or be defrauded → ships but isn't safe to use** |

---

## G — Gap pointers (probing decision drivers)

Each gap carries:

- **Emit-meaning** — what stayed unvalidated in user truth.
- **Risk class** — killer mapping (internal ranking).
- **Probe** — paragraph-level prompt the phrasing layer uses to build the stem and options (not the stem verbatim). Written so **category nouns alone** (“verification”, “moderation”, “trust system”) fail the closure test unless tied to mechanism, threshold, owner, or trigger.
- **Closure test** — what the answer **must contain** before the gap may lift to substantive close (`X3` free‑form or `X5` hard lock). If the answer does not pass, keep **`X2`** and apply **`L5`** + sharpened **`C2`** — do not quietly upgrade.

---

### `G1` — user unproven risk · WRONG_THING

**Emit-meaning:** primary user segment is fuzzy or hypothetical.

**Probe.** Name one plausible person who would download this in week one — not a persona slide, a plausible human and what they did **last week** to solve this job without you. Name one concrete user segment you refuse to serve in v1 and why your product intentionally fails them (edge case exclusion). If both cannot be named, you do not know who this is for.

**Closure test.** (a) A named behavioural segment tied to current behaviour/workaround, AND (b) one **excluded** segment plus the deliberate product reason exclusion is correct.

---

### `G2` — outcome unproven risk · WRONG_THING

**Emit-meaning:** the measurable job/outcome (“why this exists”) is mushy.

**Probe.** Describe the workaround users use today — three observable steps — then point to the exact moment inside your experience that must outperform that workaround in the **first meaningful session**. “Better UX” alone is disqualifying; tie superiority to observable behaviour users would notice.

**Closure test.** (a) The named substitute (competitor, spreadsheet, messenger, inertia, hybrid), AND (b) the specific instant of superiority in-product.

---

### `G3` — entry unproven risk · BOUNDLESS

**Emit-meaning:** first-contact / onboarding / landing value unclear.

**Probe.** Minute zero to minute one: without login or commitment, **what artefact earns the second minute** (listing density, preview, pricing signal, trusted peer)? If value requires signup before payoff, expose that bet and defend it vs drop-off — or revise the funnel.

**Closure test.** What is visible/possible pre-account (or why paywall-before-value is unavoidable) AND the payoff that earns the next step.

---

### `G4` — workflow unproven risk · BOUNDLESS

**Emit-meaning:** core journey is unstated or hand-wavy.

**Probe.** Verb-only core loop, ≤ five beats — no marketing adjectives. Identify the silent-failure beat (quit without telling you).
How is it detected **without surveying** everyone? Six-week cutoff: delete one beat — name which and the user-facing cost.

**Closure test.** (a) Five-or-fewer step path (verbs), AND (b) silent-failure step + detection hook, AND (c) removable beat + named cost.

---

### `G5` — success undefined risk · UNMEASURABLE

**Emit-meaning:** falsifiable outcome / kill signal missing.

**Probe.** Pick the **single** number whose failure by day ~90 prompts **termination** — not rebranding — of this initiative. Explain why vanity metrics disqualify here. Specify a leading indicator observable by ~day 30 that predicts hitting or missing the 90-day bar.

**Closure test.** (a) Numeric / observable 90-ish-day outcome plus threshold OR explicit kill qualitative rule tied to observable signal, AND (b) ~30‑day leading indicator, AND (c) explicit consequence if threshold missed.

---

### `G6` — scope unbounded risk · BOUNDLESS

**Emit-meaning:** v1 edge is blurry; everything “maybe later”.

**Probe.** Identify one darling feature WANTED in v1 you still cut AND the user-visible loss from cutting it AND the behaviour that proves the cut was wrong. Surfacing one tacit presumption teammates treat as scoped but never wrote down qualifies.

**Closure test.** (a) Cut feature + user cost + reversible signal OR (b) implicit scope item surfaced + explicit in/out disposition.

---

### `G7` — domain rule / binding constraint risk · UNGOVERNED

**Emit-meaning:** there is no non-negotiable rule that survives operations.

**Probe.** Describe the ONE rule violating which invalidates legitimacy (law, commerce, ethic, contractual). Not a slogan — actionable constraint grammar. Identify decider identity/queue owning breach detection, SLA to act, **default remediation** (“case by case” fails).

**Closure test.** (a) Expressible rule (who may not what), AND (b) owner/authority, AND (c) default enforcement path + SLA class (hours vs days articulated).

---

### `G8` — failure unhandled risk · FRAGILE

**Emit-meaning:** realistic break scenario + response undocumented.

**Probe.** Sixth hour launch day — pick highest-likelihood break given actual architecture/sketch. Customer vs telemetry notices first — what each sees inside ten minutes. Default recovery / communication / degraded mode — specifics, not slogans (“monitor” without signal detail fails).

**Closure test.** (a) Concrete failure vignette AND (b) detector path AND (c) default user-visible response within short window articulated.

---

### `G9` — tradeoff unsettled risk · BOUNDLESS

**Emit-meaning:** mutually exclusive forks both sound fine.

**Probe.** Genuine internal fork with two respectable paths — mutually exclusive given v1. Choose one articulate permanent sacrifice imposed on forsaken lane. Identify stakeholder likely wrong-side if pick holds — falsifying evidence collectible within thirty days altering choice.

**Closure test.** (a) Explicit pick, AND (b) sacrifice on rejected path stated, AND (c) reversible evidence timeframe.

---

### `GA` — assumption / belief unvalidated · BUILT_ON_SAND

**Emit-meaning:** foundation belief stated as certainty without proof hook.

**Probe.** Name unstressed belief risking entire architecture (supply depth, payer willingness, habitual replacement frequency, moderation load). Craft cheapest ≤30‑day falsification experiment BEFORE heavy build sinks cost. Lack of imaginable disproof means belief smuggled as fact.

**Closure test.** (a) Explicit falsifiable claim, AND (b) concrete inexpensive experiment/timebox, AND (c) disqualifying observable result enumerated.

---

### `GB` — live runtime / degraded-mode risk · UNGOVERNED

**Emit-meaning:** degraded traffic / abuse / infra failure handling vague.

*(Often collapsed with **`G7`** / **`GD`** on same noun — see **`Q8`**.)*

**Probe.** 02:00 incident — creeping fraud percentages, elevated latency, or partial flow failure impacting a minority cohort. Identify pager owner, first dashboard opened, and rollback/throttle/kill-switch choreography. State user-visible degradation vs silent limbo and an SLA-class response window.

**Closure test.** (a) Incident owner/on-call analogue, AND (b) canonical signal surfaced first, AND (c) degraded user path / rollback enumerated.

---

### `GC` — human escalation pipeline risk · UNGOVERNED

*(Often collapsed cluster — **`Q8`**. Distinguished from **`GD`**: escalation workflow vs participant harm posture.)*

**Probe.** Identify automatic human-escalation trigger with precision thresholds (counts, durations, categorical severity). SLA hours & responsible role—not “team.” During queue wait persisted content/live risk state enumerated.

**Closure test.** (a) Automated trigger specificity, AND (b) SLA number + owning role/function, AND (c) interim system behaviour.

---

### `GD` — trust / safety posture · TRUST_SAFETY

**Emit-meaning:** participant-to-participant harm path unresolved.

**Probe.** Timeline walk for credible harm occurrence tomorrow — financial fraud, physical harm, coercion, reputational weaponization, or misuse of sensitive data. Name signals observable **before** harm that you choose to tolerate or defer. State whether accepting that residual is deliberate. Specify first-24-hour response to victims and what you would say externally if pressured.

**Closure test.** (a) Named harm archetype pathway, AND (b) precursor signal articulated, AND (c) preventive/detect/remediate v1 stance chosen with explicit tolerated residual if preventative deferred.

---

### `G0` — unnamed risk · taxonomy hole

| Code | Emit-meaning | Forces |
|------|--------------|--------|
| `G0` | unnamed risk sensed | No `G1–GD` fit — articulate risk in user's words AND author a Probe + Closure pair matching rigor above (`G1`‑style specificity). Each `G0` ⇒ log taxonomy deficiency. Closure requires ≥ two of `{specific name entity, quantitative threshold/time, concrete workflow step, explicit cost/sacrifice, scenario anchor}`. |

> **`GD` vs `GC`:** `GC` — internal human workflow and escalation. `GD` — external participant harm (fraud, unsafe meetups, coercion). Dual-tag when both materially apply.

---

## X — Exposure (per-gap heat; user input derived)

Attach to a gap, e.g. `G6:X2`. Classification **must consult** Gap **Closure tests** (`G`).

| Code | Emit-meaning | Trigger | Action | Audit / failure mode |
|------|--------------|---------|--------|----------------------|
| `X1` | open — never materially resolved | closure test never passed | Candidate primary fork only via leverage stack — avoid coverage sweeps | >3 consecutive turns untouched while open ⇒ classifier staleness audit |
| `X2` | thin / masked progress | touches gap; closure unfinished | Exactly one sharper **`C2`** then rewrite probe (**`L5`**) — forbid MCQ cloning | persists ≥3 turns ⇒ broken probe pipeline |
| `X3` | substantive free‑form closure | closure satisfied in authored prose | stop asking durable until contradiction | downgrade if only category nouns — treat as **`S8`** breach |
| `X4` | inferred not user‑committed | model-implied linkage absent explicit user lock | confirming MCQ next eligible turn — forbid >2 dormant turns (**`L3`**) | new gaps scheduled while dormant X4 lives |
| `X5` | hard lock | explicit locking language ("only","never","we will …") OR pick whose option text clears closure (**`S8`** clean) | persist verbatim excerpt + **`C3`**, forbid re-litigation | downgrade if framework‑only selections |
| `X6` | contradiction | newest message overtly reverses settled `X5` same subject | unlock (prefer `X1`); ask what changed once | fuzzy sentiment ≠ contradiction |
| `X7` | emergent latent risk surfaced | structured answer reveals unscheduled exposure | reopen related selection precedence **this cycle** | missing pivot when obvious |
| `X8` | off‑angle volunteered | free‑text spike outside batch coverage | **`L7` priority** defer generic ranking | ignoring user fear language |
| `X9` | asked — awaiting qualifying answer | prior turn primary MCQ outstanding | hold slot — credit answer addressing that question irrespective naive keyword classifier | answering user ignored |

---

## P — Phase (macro gear)

| Code | Emit-meaning | Gate / effect |
|------|--------------|---------------|
| `P1` | dumping not probing | No MCQs. Reflect gaps using user words (**`C1`**, **`C4`**). Stall >2 rotations ⇒ transition forced sharp small set (`G1`/`G2`) |
| `P2` | pace choice *(optional)* | No MCQs. Fast vs coached paths with explicit costs (**`C5`**). Repeated invocation ⇒ stall |
| `P3` | decision locking elicitation | **One primary MCQ** ideal (**`Q1`**). Supporting confirming slot only precedence conflict (`X4` conversion). Conditional probe (**`Q7`**) |
| `P4` | sealing the brief | No MCQs. Render concise decision record + lingering bets/blockers — optional final challenge line |

---

## L — Leverage (re‑derive EVERY turn — never photocopy forward)

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `L1` | killer beats nicety | While killer‑class exposures open, forbids polish/nice‑to‑have primacy |
| `L2` | unlocks dimensions / cluster collapse engine | Ops cluster overlaps (`{G7,GA,GB,GC,GD}` same concern) ⇒ single synthesized MCQ — multi‑tag downstream credit |
| `L3` | sand before structure | Oldest **`X4`** confirming MCQs before broad new discovery |
| `L4` | blocker / fear dominance | Linguistic spikes ("biggest fear", "won't ship unless", existential worry) preempt generic ranking |
| `L5` | thin masks danger | Treat sustained **`X2`** as hotter than naive **`X1`** — escalate rewrite depth |
| `L6` | nothing material open | `{X1,X2,X4,X6,X7,X8}` empty **and** no gap stuck at unanswered **`X9`** ⇒ advance **`P4`** |
| `L7` | reframe beats repetition | Enables non‑obvious/off‑profile fork after stagnation (**`X8`** auto‑eligible) |
| `L8` | depth > breadth completeness | Majority settled (heuristic ≥10 gaps `X3`/`X5`) + few openings ⇒ forbid coverage re‑sweep; only `X2`/`X4`/`X6`/`X7`/`X8` drivers |

---

## R — Readiness (risk‑weighted honesty)

Re‑derive each turn alongside leverage.

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `R1` | blockers named first | Plain-language blockers BEFORE percent — hide raw codes from UX |
| `R2` | pick-only softness cap | Solely MCQ‑closed gap max dimension 65 absent elaboration lift |
| `R3` | inference / contradiction cap | Active **`X4`** / **`X6`** ⇒ systemic ceiling (~70 heuristic) |
| `R4` | killer wedge | Living killer‑class unresolved gap ⇒ global ≤~80 |
| `R5` | high confidence ship bar | Elevated readiness (≥~88 heuristic) permissible only when: killers resolved `X3+`, core structural trio `{flow G4, boundary G6, posture/harm GD or domain equivalent}` lacks `X1`‑class holes, ZERO **`X4`/`X6`**, contradiction‑free sustained locks |
| `R6` | brief coherence signal | Narrative completeness sufficient that experienced PM confident pasting skeletal PRD excerpt — orthogonal decorative metrics deprecated |

---

## S — Sharp question shaping *(P3 elicitation)*

| Code | Emit-meaning | Effect |
|------|--------------|--------|
| `S1` | adoptable policies not categories | Verbs + objects + bounded scope — ban hollow capabilities |
| `S2` | conservative lane costed | Safe option MUST carry explicit sacrificed speed/throughput/arbitrage |
| `S3` | atomic decision boundaries | forbids multipart stems laundering sequential asks |
| `S4` | rich “Something else” | Option D mandates sub‑angle hint spawning structured follow lineage |
| `S5` | explicit trade juxtaposition | Competing selections carry mutually visible downside framing |
| `S6` | counterfactual / scenario stem | Temporal concrete failure / launch vignette preferred vs abstract operational prompt |
| `S7` | mutual exclusion | Non‑additive v1 bundles — Pick A forbids concurrently shipping B simplistic reading |
| `S8` | anti‑framework fluff lockout | Nouns (`verification`,`moderation`,`AI`,`community`,`trust platform`) worthless alone — demand mechanism / threshold / owning function — framework picks cannot produce standalone **`X5`** |

---

## Q — Batch & sequencing discipline

| Code | Emit-meaning | Check |
|------|--------------|-------|
| `Q1` | single primary focal MCQ | At most ONE primary locking question / turn (excluding pure `X4` conversion substitution) |
| `Q2` | theme starvation | forbid revisiting stabilized `X3`/`X5` themes & near-duplicate intents last ~3 comparable turns |
| `Q3` | collision ban | disallow concurrent slots mapping identical user noun / decision surface |
| `Q4` | paraphrase suppression | Stem similarity heuristic — rewrite or discard |
| `Q5` | leverage ordering residual | contingent multi-slot rarity — rank `L4` > `L1` > `L3` > `L2` … |
| `Q6` | anti-pad contraction | Shrinking cohort of legit opens forbids filler — terminal size 1 or none → **`P4`/`L6`** |
| `Q7` | conditional serendipity probe | Emit ONLY when **`X8`**, stalled novelty, explicit blind spot surfaced — abolish mechanical ever-present slot |
| `Q8` | ops / trust cluster fuse | unify overlapping `{G7, GA, GB, GC, GD}` concern — **`GD`** primary tag if TRUST_SAFETY materially live |

---

## C — Coaching voice (PM-register clarity)

| Code | Emit-meaning | Narrative effect |
|------|--------------|------------------|
| `C1` | acknowledge + reflect specificity | Mandatory tight quote/trace of freshest user substantive clause before abstraction |
| `C2` | pressure thin masking | Furnish credible counter‑pressure scenario negating simplistic prior answer forcing explicit dismissal / amendment |
| `C3` | lock narration | Neutral echo lock text — forbids stealth editorialisation |
| `C4` | artifact sourcing (**P1**) | Demand **two plausible** pasted artifacts shortening path (thread, schematic, comparative link) |
| `C5` | dual pacing (**P2**) | Costs & lost assurances enumerated per lane |
| `C6` | surface sacrifice / cost naming | Tie reflection tightly to relinquished throughput or accepted residual risk |
| `C7` | blocker transparency closer | Closing beat names highest readiness impediment crisply (**`R1`** echo user vocabulary) |

---

## Count

14 gap (`G1–G9`,`GA–GD`,`G0`) + **9 exposure** (`X1–X9`) + **4 phase** + **8 leverage** (`L1–L8`) + **6 readiness** (`R1–R6`) + **8 shaping** (`S1–S8`) + **8 batch** (`Q1–Q8`) + **7 coaching** (`C1–C7`).

Behavioural totals: exposure modifiers attach to gaps; **64 distinct behavioural tokens**.


-----

## How to use the codes (reference map)

Every turn: **reason against the rubric first**, then emit one code line that declares your read.
Codes are **output only** — they make judgment legible; they must never replace BA reasoning or
mechanically drive questions while skipping the rubric. Derive every token from **user input
this turn**, not from your prior emitted line. Re-derive `L` and `R` each turn.

Apply **gap closure tests** before upgrading exposure. Honor **`Q8`** / **`L2`** before building multi-gap batches.

```mermaid
flowchart TD
    START([User message this turn]) --> REASON["① REASON — full rubric pass<br>Source: user pitch + answers ONLY"]

    REASON --> EMIT_P{"② EMIT P — pick ONE phase"}

    EMIT_P --> P1["P1 dumping<br>→ C4 artefacts · NO MCQs"]
    EMIT_P --> P2["P2 pace · C5<br>→ NO MCQs"]
    EMIT_P --> P3["P3 elicitation<br>→ ONE primary MCQ · Q8 collapse"]
    EMIT_P --> P4["P4 seal brief<br>→ brief + blockers"]

    P1 --> EMIT_LINE
    P2 --> EMIT_LINE
    P4 --> EMIT_LINE

    P3 --> EMIT_GX["③ EMIT G:X — closure-test aware<br>X9 while awaiting qualifying answer"]

    subgraph G_LEGEND["G"]
        direction TB
        Gslot["Each G has Probe + Closure test"]
    end

    subgraph X_LEGEND["X — exposure"]
        direction TB
        X1["X1 open"]
        X2["X2 thin"]
        X3["X3 substance"]
        X4["X4 inferred"]
        X5["X5 locked"]
        X6["X6 contradiction"]
        X7["X7 new risk surfaced"]
        X8["X8 off-angle priority"]
        X9["X9 asked-awaiting"]
    end

    EMIT_GX --> G_LEGEND
    EMIT_GX --> X_LEGEND

    G_LEGEND --> EMIT_LR
    X_LEGEND --> EMIT_LR

    EMIT_LR["④ EMIT L + R — re-derive THIS turn"]

    subgraph L_LEGEND["L"]
        direction TB
        L1["L1 killers first"]
        L2["L2 collapse cluster"]
        L3["L3 sand first"]
        L4["L4 fear/blocker leap"]
        L5["L5 thin danger"]
        L6["L6 → P4"]
        L7["L7 reframe"]
        L8["L8 depth not sweep"]
    end

    subgraph R_LEGEND["R"]
        direction TB
        R1["R1 blockers before %"]
        R2["R2 pick-soft cap"]
        R3["R3 X4/X6 ceiling"]
        R4["R4 killer wedge"]
        R5["R5 high bar rules"]
        R6["R6 brief coherence"]
    end

    EMIT_LR --> L_LEGEND
    EMIT_LR --> R_LEGEND

    L_LEGEND --> APPLY
    R_LEGEND --> APPLY

    APPLY{"⑤ APPLY S + Q + C<br>Sharp stems · primary MCQ"}

    subgraph S_LEGEND["S sharp shaping"]
        direction TB
        S1["S1 policies"]
        S2["S2 cost conservative"]
        S3["S3 atomic asks"]
        S4["S4 rich Else"]
        S5["S5 trade surfaced"]
        S6["S6 counterfactual"]
        S7["S7 mutex options"]
        S8["S8 anti-fluff"]
    end

    subgraph Q_LEGEND["Q"]
        direction TB
        Q1["Q1 one primary"]
        Q2["Q2 no stabilized repeat"]
        Q3["Q3 no noun collision"]
        Q4["Q4 anti-paraphrase"]
        Q5["Q5 order residual"]
        Q6["Q6 anti-pad"]
        Q7["Q7 conditional"]
        Q8["Q8 fuse ops cluster"]
    end

    subgraph C_LEGEND["C"]
        direction TB
        C1["C1 trace quote"]
        C2["C2 pressure thin"]
        C3["C3 lock neutral"]
        C4["C4 artefacts P1"]
        C5["C5 pacing P2"]
        C6["C6 surface cost"]
        C7["C7 blocker closer"]
    end

    APPLY --> S_LEGEND
    APPLY --> Q_LEGEND
    APPLY --> C_LEGEND

    S_LEGEND --> EMIT_LINE
    Q_LEGEND --> EMIT_LINE
    C_LEGEND --> EMIT_LINE

    EMIT_LINE["⑥ EMIT line + ONE primary (+ optional confirming)<br>e.g. P3 G7:X9 GA:X9 … GD:X4 L4 L8 R3 Q1 Q8"] 

    EMIT_LINE --> VALIDATE{"Validator:<br>token in legend?"}
    VALIDATE -->|"invalid"| REJECT["Reject · retry ≤2"]
    REJECT --> REASON
    VALIDATE -->|"valid"| PERSIST["Persist · next derives from HISTORY"]

    PERSIST -.-> START

    classDef phase fill:#E1F5EE,stroke:#0F6E56,color:#04342C
    classDef gap fill:#EEEDFE,stroke:#534AB7,color:#26215C
    classDef expose fill:#FAECE7,stroke:#993C1D,color:#4A1B0C
    classDef rank fill:#FAEEDA,stroke:#854F0B,color:#412402
    classDef shape fill:#FCEBEB,stroke:#A32D2D,color:#501313
    classDef emit fill:#E8F4FC,stroke:#0969DA,color:#032563

    class P1,P2,P3,P4 phase
    class Gslot gap
    class X1,X2,X3,X4,X5,X6,X7,X8,X9 expose
    class L1,L2,L3,L4,L5,L6,L7,L8,R1,R2,R3,R4,R5,R6 rank
    class S1,S2,S3,S4,S5,S6,S7,S8,Q1,Q2,Q3,Q4,Q5,Q6,Q7,Q8,C1,C2,C3,C4,C5,C6,C7 shape
    class EMIT_LINE,PERSIST emit
```

---

## Classification (reference — align implementation)

High level: diff user message → closure tests → exposures including **`X9`** while pending → **`L*` / `R*`** derived → **`Q8`** collapse before **`Q1`** emission → **`Q7`** only if gates satisfied.

(Update deterministic grid code paths to honour **`X9`**, **`Q8`**, softened multi‑batch **`Q6`** / retired mechanical **`Q7`**.)


-----

## RUBRIC ADDITION — paste into the discovery rubric

> **Emit your assessment as state codes.**
> After you have reasoned in full against this rubric — assessing the live discovery the
> way a senior practitioner would — also emit a single line of state codes that declares your read.
> Attach an exposure flag to each gap (e.g. `G6:X2`). The codes are a projection of the
> user's input, not a memory of your own prior turns: derive them only from what the user
> has actually said and picked — using each gap **Closure test** (`G`).
>
> Codes inform risk and readiness; **questions** must still be probing: use each gap's **Probe** to frame stems and apply **`S*`** (shaping) and **`C*`** (coaching) codes. Aim for **one primary MCQ** per elicitation turn (**`Q1`**). Collapse overlapping ops/trust gaps with **`Q8`** / **`L2`**. Add **`Q7`** only when earned (off-angle **`X8`**, stagnation **`L7`**, or a genuine uncovered angle).
>
> Only codes in the legend are valid — never invent a code. If you sense a risk no gap code names, emit `G0` and articulate it per `G0` rules.
> Re‑derive leverage (`L`) and readiness (`R`) each turn from the current grid — never copy‑paste unchanged.
>
> Example emitted line (illustrative):
> `P3 G7:X9 GA:X9 GD:X4 GC:X9 GB:X9 G4:X3 … L4 L8 R3 Q1 Q8 S6 S7 S8 C7`

---

## Phrasing layer (Uplift 3.0)

> **Role:** You receive a **Discovery Assessment** + **Question Plan** from the gatekeeper.
> Your job is coaching voice and **one pointed probe** per turn (**Q1**). You do **not** decide
> codes, batch size, or phase.

### Assessment-first (required)

Each turn the gatekeeper:

1. Reviews user answers and chat context.
2. Names the **greatest weaknesses** in scoped discovery (not a gap checklist).
3. Selects **one primary probe** (optional second only for X4 confirm).
4. Codes (`G*`, `L*`, `X*`) are **steering lenses** — concern domains and pressure — not
   "one MCQ per code."

Read **DISCOVERY ASSESSMENT** in the user message before phrasing. The reflection should name
the top weakness in plain language; the MCQ should **attack that weakness**.

### Non-negotiable: respond to this user, not a template

1. Read **NEW USER INPUT** first.
2. Use **`brief`**, **`probe_angle`**, and that gap's **Probe** (G section) + **`S*`** / **`C*`**.
3. **Banned:** generic discovery questionnaires unless tied to their app and last message.
4. **Options A–C** test plausible resolutions — apply **`S1`**, **`S8`**. Not textbook best practices.
5. Respect **LOCKED FACTS** — do not re-litigate settled decisions.

### Options (evidence, not instant closure)

The user may submit **`Gx: <chosen option text>`**. That records a candidate policy; the gatekeeper
judges closure on the **next** answer against the gap **Closure test**. Write options as specific,
bounded policies to **test thinking** — not vague exploration.

### Hard rules (phrasing LLM)

- Never invent gap codes.
- Do **not** emit `## State codes`.
- Emit exactly one MCQ per plan slot (**Q1** — typically one slot).
- One atomic decision per question (**`S3`**).
- Options A–D; D = "Something else" with sub-angle hint (**`S4`**).
- **`S2`** when choices compete; **`C2`** when exposure is thin (X2).

### Output format (when Questions are enabled)

#### Reflection
1–2 sentences (**`C1`**): ack NEW USER INPUT + name the **greatest weakness** from assessment.

#### Questions

### 1. `<gap>` — `<title tied to the weakness>`
`<question>`
- A) ...
- B) ...
- C) ...
- D) Something else — [hint]

When phase is P1, P2, or P4: write `_(no MCQs this turn — phase gate)_` and explain next step.

