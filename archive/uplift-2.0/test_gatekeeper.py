#!/usr/bin/env python3
"""Unit tests for Uplift 2.0 gatekeeper (no OpenAI required)."""

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
from gatekeeper.models import AnswerHistory, UserTurn
from gatekeeper.pipeline import run_pipeline
from gatekeeper.validate import validate_code_line, validate_grid_matches_line
from gatekeeper.derive import enrich_grid, open_gaps
from session_store import Session


LEGACY_SESSION = ROOT.parent / "sessions" / "20260524-202455-car-selling-app"


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


class TestBatch(unittest.TestCase):
    def test_q6_no_padding(self):
        history = AnswerHistory(
            pitch="App",
            turns=[UserTurn(1, "x" * 100), UserTurn(2, "scope MVP only")],
        )
        grid = classify_gaps(history, 2)
        grid = enrich_grid(grid, history)
        plan = build_question_plan(grid)
        opens = len(open_gaps(grid))
        gap_slots = plan.constraints.get("gap_slots", 0)
        self.assertLessEqual(gap_slots, max_batch_size())
        if opens < 5:
            self.assertEqual(gap_slots, min(opens, max_batch_size()))
        self.assertTrue(any(s.is_q7_probe for s in plan.slots) or plan.phase != "P3")


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


if __name__ == "__main__":
    unittest.main()
