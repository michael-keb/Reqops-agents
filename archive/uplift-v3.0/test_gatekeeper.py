#!/usr/bin/env python3
"""Unit tests for Uplift 3.0 gatekeeper (no OpenAI required)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gatekeeper.batch import build_question_plan, max_batch_size
from gatekeeper.classify import classify_gaps
from gatekeeper.emit import grid_to_code_line
from gatekeeper.history import build_history_from_turn_files
from gatekeeper.legend import CANONICAL_GAPS, OPEN_EXPOSURES
from gatekeeper.merge import directly_negates
from gatekeeper.models import AnswerHistory, GapRow, UserTurn
from gatekeeper.pipeline import load_prior_grid, run_pipeline
from gatekeeper.validate import validate_code_line, validate_grid_matches_line
from gatekeeper.derive import enrich_grid, open_gaps
from session_store import MemoryPatch, Session


LEGACY_SESSION = ROOT.parent / "sessions" / "20260524-202455-car-selling-app"
CAR_SESSION = ROOT.parent / "uplift-2.0" / "sessions" / "20260524-211415-car-selling-app"
if not CAR_SESSION.is_dir():
    CAR_SESSION = ROOT / "sessions" / "20260524-211415-car-selling-app"


class TestLegend(unittest.TestCase):
    def test_thirteen_canonical_gaps(self):
        self.assertEqual(len(CANONICAL_GAPS), 13)
        self.assertIn("GD", CANONICAL_GAPS)


class TestValidator(unittest.TestCase):
    def test_rejects_gch(self):
        line = "P3 G1:X1 GCh:X1 L1 R3 Q7"
        vr = validate_code_line(line)
        self.assertFalse(vr.ok)
        self.assertTrue(any("GCh" in e for e in vr.errors))

    def test_accepts_valid_line(self):
        gaps = " ".join(f"G{i}:X1" for i in range(1, 10))
        line = f"P3 G1:X1 G2:X1 G3:X1 G4:X1 G5:X1 G6:X1 G7:X1 G8:X1 G9:X1 GA:X1 GB:X1 GC:X1 GD:X1 L1 R1 Q7"
        vr = validate_code_line(line, require_all_gaps=True)
        self.assertTrue(vr.ok, vr.errors)

    def test_require_all_gaps(self):
        vr = validate_code_line("P3 G1:X1 L1", require_all_gaps=True)
        self.assertFalse(vr.ok)


class TestClassifier(unittest.TestCase):
    def test_turn_one_short_pitch_is_p1_all_x1(self):
        history = AnswerHistory(
            pitch="Car selling app",
            turns=[UserTurn(1, "Car selling app")],
        )
        grid = classify_gaps(history, 1)
        grid = enrich_grid(grid, history)
        self.assertEqual(grid.phase, "P1")
        for g in CANONICAL_GAPS:
            self.assertEqual(grid.rows[g].exposure, "X1")

    def test_success_metric_settled_turn7(self):
        if not LEGACY_SESSION.is_dir():
            self.skipTest("legacy session not present")
        history = build_history_from_turn_files(
            "Car selling app",
            LEGACY_SESSION / "turns",
            through_turn=7,
        )
        grid = classify_gaps(history, 7)
        self.assertIn(grid.rows["G5"].exposure, ("X3", "X5"))

    def test_trust_gap_not_gch(self):
        if not LEGACY_SESSION.is_dir():
            self.skipTest("legacy session not present")
        history = build_history_from_turn_files(
            "Car selling app",
            LEGACY_SESSION / "turns",
            through_turn=9,
        )
        grid = classify_gaps(history, 9)
        line = grid_to_code_line(enrich_grid(grid, history))
        self.assertNotIn("GCh", line)
        self.assertIn("GD:", line)
        vr = validate_code_line(line, require_all_gaps=True)
        self.assertTrue(vr.ok, vr.errors)

    def test_structured_gap_answer_awaiting_depth(self):
        history = AnswerHistory(
            pitch="Car selling app",
            turns=[
                UserTurn(
                    10,
                    "GA: We will validate trust via user reviews and completed-sale counts.\n"
                    "GB: Live ops use automated scam flags plus a daily moderation queue.\n"
                    "GC: Humans intervene only after a user report.",
                ),
            ],
        )
        grid = classify_gaps(history, 10)
        for gap in ("GA", "GB", "GC"):
            self.assertEqual(grid.rows[gap].exposure, "X9", gap)
            self.assertTrue(grid.rows[gap].evidence_snippets)

    def test_structured_answer_hedge_stays_x2(self):
        history = AnswerHistory(
            pitch="App",
            turns=[UserTurn(2, "G7: We might add light verification later.")],
        )
        grid = classify_gaps(history, 2)
        self.assertEqual(grid.rows["G7"].exposure, "X2")


class TestBatch(unittest.TestCase):
    def test_q1_single_primary_slot(self):
        history = AnswerHistory(
            pitch="App",
            turns=[UserTurn(1, "x" * 100), UserTurn(2, "scope MVP only")],
        )
        grid = classify_gaps(history, 2)
        grid = enrich_grid(grid, history)
        plan = build_question_plan(grid, history=history)
        self.assertLessEqual(len(plan.slots), max_batch_size())
        self.assertGreaterEqual(len(plan.slots), 1)

    def test_batch_size_env(self):
        import os

        history = AnswerHistory(
            pitch="Car selling app",
            turns=[
                UserTurn(1, "Car selling app"),
                UserTurn(2, "Peer-to-peer marketplace for used cars."),
            ],
        )
        grid = enrich_grid(classify_gaps(history, 2), history)
        os.environ["MAX_BATCH_SIZE"] = "5"
        try:
            plan = build_question_plan(grid, history=history)
            self.assertEqual(len(plan.slots), 5)
            self.assertEqual(plan.constraints["mcq_count"], 5)
        finally:
            os.environ.pop("MAX_BATCH_SIZE", None)


class TestEmitRoundTrip(unittest.TestCase):
    def test_grid_matches_emitted_line(self):
        history = AnswerHistory(
            pitch="Test",
            turns=[UserTurn(1, "A marketplace app for selling cars with photos and chat")],
        )
        grid = enrich_grid(classify_gaps(history, 1), history)
        line = grid_to_code_line(grid)
        vr = validate_grid_matches_line(grid, line)
        self.assertTrue(vr.ok, vr.errors)
        self.assertTrue(validate_code_line(line, require_all_gaps=True).ok)


class TestLockDurability(unittest.TestCase):
    def test_directly_negates_false_for_gd_near_miss(self):
        locked = (
            "Biggest risk to avoid: scams and unsafe meetups — "
            "optimise for fraud prevention over user growth."
        )
        new = (
            "After contact, buyers and sellers use in-app chat until the deal is done; "
            "sharing phone numbers is optional, not required."
        )
        self.assertFalse(directly_negates(new, locked, "GD"))

    def test_gd_x5_survives_turn10_car_session(self):
        if not CAR_SESSION.is_dir():
            self.skipTest("car-selling session not present")
        meta = json.loads((CAR_SESSION / "session.meta.json").read_text())
        session = Session(root=CAR_SESSION, meta=meta)
        prior = load_prior_grid(session, 10)
        self.assertIsNotNone(prior)
        assert prior is not None
        self.assertEqual(prior.rows["GD"].exposure, "X5")
        result = run_pipeline(session, 10, prior_grid=prior)
        self.assertEqual(result.grid.rows["GD"].exposure, "X5")
        self.assertNotIn("R4", result.grid.readiness)
        self.assertNotIn("L1", result.grid.leverage)
        self.assertIn("L5", result.grid.leverage)
        self.assertIn("Q6", result.grid.batch)

    def test_g6_scope_near_miss_stays_locked(self):
        prior = GapRow(
            gap="G6",
            exposure="X5",
            locked_by="Out of scope for v1: financing, shipping, dealer fleet.",
            locked_turn=5,
            evidence_turns=[5],
            evidence_snippets=["Out of scope for v1: financing, shipping."],
            risk_class="BOUNDLESS",
        )
        fresh = GapRow(
            gap="G6",
            exposure="X2",
            evidence_turns=[5, 12],
            evidence_snippets=["Out of scope for v1.", "saved searches later, not in v1"],
            risk_class="BOUNDLESS",
        )
        history = AnswerHistory(
            pitch="Car app",
            turns=[UserTurn(12, "We might add saved searches later, but not in v1.")],
        )
        from gatekeeper.merge import merge_gap

        merged = merge_gap(
            prior,
            fresh,
            new_message=history.latest().raw_text,  # type: ignore[union-attr]
            history=history,
            turn=12,
        )
        self.assertEqual(merged.exposure, "X5")

    def test_g1_genuine_negation_reopens(self):
        locked = "Primary users: private individuals selling their own cars — consumer-only P2P."
        new = (
            "Change of plan — we're letting small dealers list too, not just private sellers. "
            "Consumer-only was wrong."
        )
        self.assertTrue(directly_negates(new, locked, "G1"))

    def test_re_settle_after_negation(self):
        history = AnswerHistory(
            pitch="Car app",
            turns=[
                UserTurn(
                    18,
                    "Dealers are in, but capped at 5 active listings each, and clearly badged as dealers.",
                ),
            ],
        )
        prior = GapRow(
            gap="G1",
            exposure="X6",
            evidence_turns=[17],
            evidence_snippets=["Change of plan — dealers in."],
            risk_class="WRONG_THING",
        )
        fresh = GapRow(
            gap="G1",
            exposure="X3",
            evidence_turns=[17, 18],
            evidence_snippets=[
                "Change of plan — dealers in.",
                history.turns[-1].raw_text,
            ],
            risk_class="WRONG_THING",
        )
        from gatekeeper.merge import merge_gap

        merged = merge_gap(
            prior,
            fresh,
            new_message=history.turns[-1].raw_text,
            history=history,
            turn=18,
        )
        self.assertEqual(merged.exposure, "X3")
        self.assertTrue(merged.locked_by)
        self.assertIn("Dealers", merged.locked_by)


class TestPipelineReplay(unittest.TestCase):
    def test_replay_ten_turns_no_invalid_tokens(self):
        if not LEGACY_SESSION.is_dir():
            self.skipTest("legacy session not present")
        meta = json.loads((LEGACY_SESSION / "session.meta.json").read_text())
        session = Session(root=LEGACY_SESSION, meta=meta)
        prior = None
        for n in session.list_turn_dirs():
            result = run_pipeline(session, n, prior_grid=prior)
            vr = validate_code_line(result.code_line, require_all_gaps=True)
            self.assertTrue(vr.ok, f"turn {n}: {vr.errors}")
            self.assertNotIn("GCh", result.code_line)
            for g in CANONICAL_GAPS:
                self.assertIn(g, result.grid.rows)
            prior = result.grid


class TestRubricLoader(unittest.TestCase):
    def test_phrasing_prompt_is_full_rubric(self):
        from rubric import RUBRIC_V2_PATH, load_phrasing_system_prompt, load_rubric_v2

        self.assertTrue(RUBRIC_V2_PATH.is_file())
        full = load_rubric_v2()
        text = load_phrasing_system_prompt()
        self.assertEqual(text, full)
        self.assertIn("Phrasing layer (Uplift 3.0)", text)
        self.assertIn("L — Leverage", text)
        self.assertIn("R — Readiness", text)
        self.assertIn("```mermaid", text)


class TestAssessment(unittest.TestCase):
    def test_ops_cluster_collapses_to_one_weakness(self):
        history = AnswerHistory(
            pitch="Car selling app",
            turns=[
                UserTurn(1, "Car selling app"),
                UserTurn(
                    2,
                    "Trust is critical: verification, report listing, safety at meetups. "
                    "Biggest risk: scams and unsafe meetups.",
                ),
            ],
        )
        grid = enrich_grid(classify_gaps(history, 2), history)
        plan = build_question_plan(grid, history=history)
        assessment = plan.constraints["assessment"]
        self.assertGreaterEqual(len(assessment["weaknesses"]), 1)
        self.assertIn("Q8", grid.batch + assessment.get("steering", []))
        self.assertEqual(len(plan.slots), 1)

    def test_fear_spike_adds_l4(self):
        history = AnswerHistory(
            pitch="Car app",
            turns=[
                UserTurn(
                    3,
                    "Biggest risk to avoid: scams — optimise for fraud prevention over growth.",
                ),
            ],
        )
        grid = enrich_grid(classify_gaps(history, 3), history)
        self.assertIn("L4", grid.leverage)


class TestPhrasingBrief(unittest.TestCase):
    def test_brief_is_probe_not_checklist(self):
        from gatekeeper.phrasing_brief import build_slot_brief

        history = AnswerHistory(
            pitch="Car selling app",
            turns=[UserTurn(1, "MVP: listings, chat, meetups. No payments v1.")],
        )
        grid = enrich_grid(classify_gaps(history, 1), history)
        row = grid.rows["G4"]
        brief = build_slot_brief(row, grid=grid, history=history)
        self.assertIn("PRIMARY", brief)
        self.assertNotIn("User just said", brief)
        self.assertIn("next answer", brief.lower())


class TestMemoryForLlm(unittest.TestCase):
    def test_omits_duplicated_sections(self):
        from session_store import MEMORY_TEMPLATE, SessionStore

        store = SessionStore(ROOT)
        session = store.create("Test app")
        session.apply_patch(
            MemoryPatch(
                state_codes="P3 G1:X1 L1 R1",
                facts=["G4: five-step flow locked"],
            ),
            turn=1,
        )
        llm_memory = session.read_memory_for_llm()
        self.assertIn("## Pitch", llm_memory)
        self.assertIn("## Compressed conversation", llm_memory)
        self.assertNotIn("Latest state codes", llm_memory)
        self.assertNotIn("Settled facts", llm_memory)
        full = session.read_memory()
        self.assertIn("Latest state codes", full)
        self.assertIn("Settled facts", full)


if __name__ == "__main__":
    unittest.main()
