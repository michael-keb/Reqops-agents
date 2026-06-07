#!/usr/bin/env python3
"""Unit tests for Uplift 4.0 analyst pipeline (no OpenAI)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analyst.grid.merge import directly_negates
from analyst.guards import killer_code, recency_code
from analyst.models import AnswerHistory, Candidate, DriverScores, UserTurn
from analyst.pipeline import apply_llm_scores, build_selection, run_pipeline
from analyst.routing import dominant_term_and_mode
from analyst.score import compute_score, rank_candidates
from analyst.tables import I_MULT, K_MULT, R_MULT
from session_store import SessionStore


class TestMultipliers(unittest.TestCase):
    def test_turn9_fixture_ga_beats_g1(self):
        """Worked example from instrucitons.md — GA wins, G1 annihilated by R3."""
        asked = {"G1": [8], "GA": [], "GB": [], "G8": [8], "G3": []}
        ga = compute_score(
            Candidate(
                gap="GA",
                intent="believe vs proven",
                exposure="X1",
                risk_class="BUILT_ON_SAND",
            ),
            DriverScores(
                I="I2",
                C="C1",
                E="E0",
                why_now="Fraud priority named; mechanism untouched.",
            ),
            asked_history=asked,
            current_turn=9,
        )
        g1 = compute_score(
            Candidate(
                gap="G1",
                intent="who exactly",
                exposure="X2",
                risk_class="WRONG_THING",
            ),
            DriverScores(I="I0", C="C0", E="E1", why_now="Personas thin."),
            asked_history=asked,
            current_turn=9,
        )
        self.assertGreater(ga.score, g1.score)
        self.assertAlmostEqual(ga.score, 4.0 * 1.0 * 1.0 * 1.0 * 1.6, places=2)
        self.assertLess(g1.score, 0.1)
        self.assertEqual(ga.mode, "FOLLOW")
        self.assertEqual(g1.guards["R"], "R3")

    def test_emit_turn9_format(self):
        from analyst.emit import format_candidate_line

        asked = {"G1": [8], "GA": [], "GB": [], "G8": [8], "G3": []}
        ga = compute_score(
            Candidate(gap="GA", intent="", exposure="X1", risk_class="BUILT_ON_SAND"),
            DriverScores(I="I2", C="C1", E="E0", why_now="fraud mechanism untouched"),
            asked_history=asked,
            current_turn=9,
        )
        line = format_candidate_line(ga)
        self.assertIn("GA  I2C1E0", line)
        self.assertIn("→ FOLLOW", line)


class TestScoreParse(unittest.TestCase):
    def test_compact_lines(self):
        from analyst.scorer_prompt import parse_score_response

        raw = """GA  I2 C1 E0
G1  I0 C0 E1

why: fraud priority named, mechanism missing
"""
        out = parse_score_response(raw)
        self.assertEqual(out["GA"]["I"], "I2")
        self.assertIn("fraud", out["GA"]["why_now"].lower())


class TestRouting(unittest.TestCase):
    def test_c3_confront(self):
        drivers = DriverScores(I="I0", C="C3", E="E0")
        terms = {"I": 1.0, "C": 5.0, "E": 1.0, "R": 1.0, "K": 1.0}
        label, mode = dominant_term_and_mode(drivers, terms, k_term=1.0)
        self.assertEqual(mode, "CONFRONT")
        self.assertIn("C=", label)


class TestGuards(unittest.TestCase):
    def test_k2_trust_safety(self):
        self.assertEqual(killer_code("GA", "BUILT_ON_SAND"), "K2")

    def test_recency_r3(self):
        self.assertEqual(recency_code("G1", {"G1": [8]}, 9), "R3")


class TestLockVeto(unittest.TestCase):
    def test_gd_lock_not_negated(self):
        locked = "optimise for fraud prevention over user growth"
        msg = "Biggest risk: scams — optimise for fraud prevention over user growth."
        self.assertFalse(directly_negates(msg, locked, "GD"))


class TestPipelineDry(unittest.TestCase):
    def test_new_session_intake(self):
        store = SessionStore(ROOT)
        session = store.create("_test-intake")
        result = run_pipeline(
            session,
            1,
            current_user_text="Car selling app",
            llm_scores={},
        )
        self.assertTrue(result.selection.intake)
        self.assertIsNone(result.selection.primary)


if __name__ == "__main__":
    unittest.main()
