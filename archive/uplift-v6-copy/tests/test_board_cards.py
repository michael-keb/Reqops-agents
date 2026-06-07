"""Unit tests for board card extraction."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bridge import board_cards, board_extract
from bridge.board_columns import COLUMN_BY_ID


class BoardCardsTest(unittest.TestCase):
    def test_build_transcript_from_turns(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "Memory.md").write_text("# Discovery memory\n\n## Pitch\ncafe app\n", encoding="utf-8")
            turn_dir = root / "turns" / "01"
            turn_dir.mkdir(parents=True)
            (turn_dir / "user-input.txt").write_text("cafe app", encoding="utf-8")
            (turn_dir / "response.md").write_text("## Reflection\nNice pitch.\n", encoding="utf-8")
            transcript = board_cards.build_transcript(root)
            self.assertIn("cafe app", transcript)
            self.assertIn("Nice pitch", transcript)

    def test_parse_column_response(self) -> None:
        column = COLUMN_BY_ID["actor"]
        raw = """## Reflection
Two actors stood out.

## Cards

```json
{
  "column": "actor",
  "cards": [
    {
      "title": "Cafe owner",
      "body": "Runs the shop and sets the menu.",
      "evidence": ["cafe owner mentioned in pitch"],
      "confidence": "high"
    }
  ]
}
```
"""
        payload = board_cards.parse_column_response(raw, column=column)
        self.assertEqual(payload["id"], "actor")
        self.assertEqual(len(payload["cards"]), 1)
        self.assertEqual(payload["cards"][0]["title"], "Cafe owner")

    def test_save_and_load_board(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            columns = [{"id": "goal", "title": "Goal", "cards": []}]
            path = board_cards.save_board(root, columns, elapsed_s=1.2)
            self.assertTrue(path.is_file())
            loaded = board_cards.load_board(root)
            assert loaded is not None
            self.assertEqual(len(loaded["columns"]), 1)
            self.assertEqual(loaded["elapsed_s"], 1.2)


class BoardExtractTest(unittest.TestCase):
    def test_extract_board_mock(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "Memory.md").write_text(
                "# Discovery memory\n\n## Pitch\nboard test product\n\n## Turn log\n",
                encoding="utf-8",
            )
            turn_dir = root / "turns" / "01"
            turn_dir.mkdir(parents=True)
            (turn_dir / "user-input.txt").write_text("board test product", encoding="utf-8")
            (turn_dir / "response.md").write_text("## Reflection\nok\n", encoding="utf-8")

            with mock.patch.object(board_extract.sess, "session_path", return_value=root):
                with mock.patch.dict(os.environ, {"UPLIFT_MOCK_AGENT": "1"}):
                    board_extract.MOCK = True
                    result = board_extract.extract_board("test-session", column_ids=["goal", "risk"])
            self.assertEqual(len(result["columns"]), 2)
            self.assertFalse(result["errors"])
            board = board_cards.load_board(root)
            assert board is not None
            self.assertEqual(len(board["columns"]), 2)


if __name__ == "__main__":
    unittest.main()
