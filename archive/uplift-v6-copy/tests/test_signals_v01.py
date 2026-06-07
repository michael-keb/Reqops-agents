"""Unit tests for signals-v01 agent pack."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import sys

ROOT = Path(__file__).resolve().parent.parent
SIG_PKG = ROOT / "signals-v01"
if str(SIG_PKG) not in sys.path:
    sys.path.insert(0, str(SIG_PKG))

from signals_v01.actions import parse_action_blocks, validate_add  # noqa: E402
from signals_v01.columns import COLUMN_BY_ID  # noqa: E402
from signals_v01.column_runner import _resolve_agent_text  # noqa: E402
from signals_v01.extract import extract_signals  # noqa: E402
from signals_v01.store import SignalStore  # noqa: E402
from signals_v01.transcript import build_transcript  # noqa: E402


class TranscriptTest(unittest.TestCase):
    def test_reflection_only_excludes_mcq(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "Memory.md").write_text("# Discovery memory\n\n## Pitch\ncafe app\n", encoding="utf-8")
            turn_dir = root / "turns" / "01"
            turn_dir.mkdir(parents=True)
            (turn_dir / "user-input.txt").write_text(
                "cafe app\n\n---\nUplift output contract (mandatory — copy this shape exactly):\n\n## Reflection\n",
                encoding="utf-8",
            )
            (turn_dir / "response.md").write_text(
                "## Reflection\nNice pitch.\n\n## Questions\n\n### 1. Who?\n- A) x\n",
                encoding="utf-8",
            )
            transcript = build_transcript(root, reflection_only=True)
            self.assertIn("cafe app", transcript)
            self.assertIn("Nice pitch", transcript)
            self.assertNotIn("- A)", transcript)
            self.assertNotIn("## Questions", transcript)
            self.assertNotIn("Uplift output contract", transcript)


class ActionsTest(unittest.TestCase):
    def test_resolve_agent_text_prefers_disk_full_capture(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            col_dir = Path(d)
            turn_dir = col_dir / "turns" / "01"
            turn_dir.mkdir(parents=True)
            full = """## Action

```json
{"action": "add", "column": "goal", "card": {"title": "T", "body": "B", "evidence": ["q"], "confidence": "high"}}
```
"""
            (turn_dir / "response.full.md").write_text(full, encoding="utf-8")
            stripped_event = "Reading skill first.\n## Action\n"
            resolved = _resolve_agent_text(col_dir=col_dir, event_text=stripped_event)
            self.assertEqual(parse_action_blocks(resolved)[0]["action"], "add")

    def test_parse_action_block(self) -> None:
        raw = """## Action

```json
{"action": "add", "column": "risk", "card": {"title": "T", "body": "B", "evidence": ["q"], "confidence": "high"}}
```
"""
        blocks = parse_action_blocks(raw)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["action"], "add")

    def test_parse_truncated_open_fence(self) -> None:
        raw = """Checking skill first.
## Action

```json
{"action": "add", "column": "actor", "card": {"title": "Lead", "body": "Product owner.", "evidence": ["owner"], "confidence": "medium"}}
"""
        blocks = parse_action_blocks(raw)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["column"], "actor")

    def test_validate_add_inferred(self) -> None:
        action = {
            "action": "add",
            "column": "risk",
            "card": {
                "title": "Gap",
                "body": "Missing",
                "confidence": "inferred",
                "rationale": {"gap": "g", "paraphrase": "p"},
            },
        }
        self.assertIsNone(validate_add(action, expected_column="risk"))


class StoreTest(unittest.TestCase):
    def test_add_and_soft_remove(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            store = SignalStore(session_dir=root)
            store.load()
            col = COLUMN_BY_ID["goal"]
            add = {
                "action": "add",
                "column": "goal",
                "card": {
                    "title": "North star",
                    "body": "Sell faster.",
                    "evidence": ["sell faster"],
                    "confidence": "high",
                },
            }
            r = store.mutate(add, run_id="test-run")
            self.assertTrue(r.ok)
            assert r.node
            node_id = r.node["id"]
            updated_at = r.node["updatedAt"]
            snap = store.column_snapshot("goal")
            self.assertEqual(len(snap), 1)
            remove = {
                "action": "remove",
                "column": "goal",
                "id": node_id,
                "updatedAt": updated_at,
                "reason": "superseded",
            }
            r2 = store.mutate(remove, run_id="test-run")
            self.assertTrue(r2.ok)
            self.assertEqual(len(store.column_snapshot("goal")), 0)
            self.assertTrue(store.list_active_nodes() == [])

    def test_edit_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            store = SignalStore(session_dir=root)
            store.load()
            add = {
                "action": "add",
                "column": "risk",
                "card": {
                    "title": "Fraud",
                    "body": "Bad actors.",
                    "evidence": ["scam"],
                    "confidence": "high",
                },
            }
            r = store.mutate(add, run_id="run")
            assert r.node
            edit = {
                "action": "edit",
                "column": "risk",
                "id": r.node["id"],
                "updatedAt": "wrong-timestamp",
                "patch": {"body": "Updated"},
            }
            r2 = store.mutate(edit, run_id="run")
            self.assertFalse(r2.ok)
            self.assertTrue(r2.conflict)


class ExtractTest(unittest.TestCase):
    def test_extract_mock_two_columns(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "Memory.md").write_text(
                "# Discovery memory\n\n## Pitch\nsignal test product\n",
                encoding="utf-8",
            )
            turn_dir = root / "turns" / "01"
            turn_dir.mkdir(parents=True)
            (turn_dir / "user-input.txt").write_text("signal test product", encoding="utf-8")
            (turn_dir / "response.md").write_text("## Reflection\nok\n", encoding="utf-8")

            uplift_root = Path(__file__).resolve().parent.parent
            sys.path.insert(0, str(uplift_root))
            import signals_v01.extract as extract_mod

            with mock.patch.object(extract_mod.sess, "session_path", return_value=root):
                with mock.patch.dict(os.environ, {"UPLIFT_MOCK_AGENT": "1"}):
                    result = extract_signals("test-session", column_ids=["goal", "inputs"])
            self.assertFalse(result["errors"])
            self.assertEqual(len(result["columns"]), 2)
            store_path = root / "signals-v01" / "store.json"
            self.assertTrue(store_path.is_file())
            data = json.loads(store_path.read_text(encoding="utf-8"))
            active = [n for n in data["nodes"] if not n.get("deletedAt")]
            self.assertGreaterEqual(len(active), 2)


if __name__ == "__main__":
    unittest.main()
