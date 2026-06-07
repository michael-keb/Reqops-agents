"""Unit tests for bridge artifact persistence."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bridge import artifacts


class ArtifactsTest(unittest.TestCase):
    def test_persist_turn_writes_files(self) -> None:
        sample = """## Reflection
Short reflection.

## Questions

### 1. Who is it for?
Stem here

- A) One
- B) Two
- C) Three
"""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "Memory.md").write_text(
                "# Discovery memory\n\n## Pitch\ntest\n\n## Settled facts\n\n## Turn log\n",
                encoding="utf-8",
            )
            n = artifacts.persist_turn(root, user_input="test pitch", response_text=sample)
            self.assertEqual(n, 1)
            self.assertTrue((root / "turns/01/response.md").is_file())
            self.assertTrue((root / "turns/01/user-input.txt").is_file())
            turn_json = json.loads((root / "turns/01/turn.json").read_text())
            self.assertEqual(turn_json["turn"], 1)
            self.assertGreaterEqual(len(turn_json.get("questions") or []), 1)

    def test_extract_pitch_from_bootstrap(self) -> None:
        raw = "Start uplift discovery for: coffee shop\nSession dir: /tmp/x"
        self.assertEqual(artifacts.extract_pitch(raw), "coffee shop")
        self.assertEqual(artifacts.user_input_for_turn(raw), "coffee shop")

    def test_persist_turn_strips_json_from_response_md(self) -> None:
        sample = "## Reflection\nHi\n\n```json\n{\"turn\": 1}\n```\n"
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "Memory.md").write_text("# Discovery memory\n\n## Pitch\ntest\n\n## Turn log\n", encoding="utf-8")
            artifacts.persist_turn(root, user_input="test", response_text=sample)
            saved = (root / "turns/01/response.md").read_text()
            self.assertNotIn("```json", saved)
            self.assertIn("## Reflection", saved)

    def test_strip_json_fence_blocks(self) -> None:
        raw = "## Reflection\nHi\n\n```json\n{\"turn\": 1}\n```\n"
        self.assertEqual(artifacts.strip_json_fence_blocks(raw), "## Reflection\nHi")

    def test_sanitize_drops_something_else_options(self) -> None:
        sample = """## Reflection
Short reflection.

## Questions

### 1. Who is it for?
Stem here

- A) One
- B) Two
- C) Three
- D) Something else — describe your wedge
"""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "Memory.md").write_text(
                "# Discovery memory\n\n## Pitch\ntest\n\n## Settled facts\n\n## Turn log\n",
                encoding="utf-8",
            )
            artifacts.persist_turn(root, user_input="test pitch", response_text=sample)
            turn_json = json.loads((root / "turns/01/turn.json").read_text())
            opts = turn_json["questions"][0]["options"]
            self.assertEqual(len(opts), 3)
            self.assertTrue(all("Something else" not in o for o in opts))
            self.assertEqual([o[0] for o in opts], ["A", "B", "C"])


if __name__ == "__main__":
    unittest.main()
