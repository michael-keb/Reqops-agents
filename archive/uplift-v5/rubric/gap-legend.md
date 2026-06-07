# Gap legend (audit only — never use as question titles)

Use these codes internally when scoring and logging. User-facing questions must **not** lead with gap codes or intent labels.

| Gap | Intent | Risk class | K tier |
|-----|--------|------------|--------|
| G1 | who exactly, concretely | WRONG_THING | K1 |
| G2 | what job, measurably | WRONG_THING | K1 |
| G3 | how use begins | BOUNDLESS | K0 |
| G4 | the one core path | BOUNDLESS | K0 |
| G5 | what proves it worked | UNMEASURABLE | K1 |
| G6 | in vs out, v1 | BOUNDLESS | K0 |
| G7 | what constraint binds | UNGOVERNED | K0 |
| G8 | what happens broken | FRAGILE | K1 |
| G9 | which competing option | BOUNDLESS | K0 |
| GA | believe vs proven | BUILT_ON_SAND | K2 |
| GB | how it operates live | UNGOVERNED | K2 |
| GC | where humans intervene | UNGOVERNED | K2 |
| GD | how participants are protected | TRUST_SAFETY | K2 |

Trust/safety cluster: G7, G8, GA, GB, GC, GD (K2 on GA–GD).

## Lock rule (L)

When the user **commits** to something (scope, priority, policy), treat that gap as **L2 locked**. Do not re-litigate unless their new message **directly negates** the lock.

## Recency rule (R)

Track which gaps you asked each turn. Gaps asked **last turn** get R3 (effectively dead). Asked 1–2 turns ago get R2. Do not loop — especially G1.
