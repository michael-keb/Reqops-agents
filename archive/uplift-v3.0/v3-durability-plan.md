# Uplift 3.0 — Gatekeeper Lock Durability

> **Purpose:** Fix X5/X3 lock decay (KeepLock), persist lock evidence, verify with unit tests.  
> **Status:** **Phase 1–2 implemented** in `uplift-v3.0/gatekeeper/`. Phases 3–4 (audit prompts, adversarial script) still open.  
> **Baseline:** Car-selling session `uplift-2.0/sessions/20260524-211415-car-selling-app`; rubric `llm-rubric_v2.md`.

---

## Implemented (v3)

| Item | Status |
|------|--------|
| `gatekeeper/merge.py` | **Done** — KeepLock, `directly_negates`, backfill |
| `GapRow.locked_by` / `locked_turn` | **Done** — persisted in `grid.json` |
| Pipeline `classify → merge → derive` | **Done** |
| GD classifier: no latest-phrase gate | **Done** — uses `combined` history |
| G1 dealer negation in `detect.py` | **Done** |
| `TestLockDurability` in `test_gatekeeper.py` | **Done** — 5 tests, all passing |

### Pipeline

```
classify  →  fresh read per gap
merge     →  sole owner of X3/X5 durability
derive    →  L/R/batch from merged grid
```

Run tests:

```bash
cd uplift-v3.0
python3 test_gatekeeper.py -v
```

---

## Remaining (Phases 3–4)

| Artifact | Path | Status |
|----------|------|--------|
| Diagnostic harness | `prompts/gatekeeper-audit.md` | Not added |
| Adversarial founder | `prompts/adversarial-founder-car-app.md` | Not added |
| Expected grids | `fixtures/car-app-stress-expected.json` | Not added |
| Scripted T11–T20 stress run | manual / harness | Not run |

See `uplift-2.0/v2-durability-plan.md` for full phase write-up, golden case, and adversarial turn script.

---

## Golden case (T9 → T10) — must pass

**Turn 9:** Biggest risk… optimise for fraud prevention over user growth.  
**Turn 10:** In-app chat until deal done; phone optional.

**Expected:** `GD:X5`, `R1` only, `L5`, `Q6` present.

Verified by `TestLockDurability.test_gd_x5_survives_turn10_car_session`.

---

## Files changed

- `gatekeeper/models.py`
- `gatekeeper/merge.py` (new)
- `gatekeeper/pipeline.py`
- `gatekeeper/classify.py`
- `gatekeeper/detect.py`
- `test_gatekeeper.py`
