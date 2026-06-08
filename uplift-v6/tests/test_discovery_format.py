"""Discovery workshop prompt wrapping."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bridge.discovery_context import looks_like_code_output, valid_discovery_response
from bridge.discovery_format import (
    MCQ_FORMAT_BLOCK,
    WORKSHOP_ROLE_BLOCK,
    bootstrap_message,
    wrap_discovery_message,
)


class DiscoveryFormatTest(unittest.TestCase):
    def test_wrap_includes_workshop_and_mcq_blocks(self) -> None:
        out = wrap_discovery_message("Who is the first user?")
        self.assertIn(WORKSHOP_ROLE_BLOCK, out)
        self.assertIn(MCQ_FORMAT_BLOCK, out)
        self.assertIn("Who is the first user?", out)

    def test_wrap_embeds_skill_without_path_reference(self) -> None:
        out = wrap_discovery_message("hello")
        self.assertIn("Discovery skill (embedded", out)
        self.assertNotIn("Follow .cursor/skills/", out)

    def test_wrap_idempotent(self) -> None:
        once = wrap_discovery_message("hello")
        twice = wrap_discovery_message(once)
        self.assertEqual(once, twice)

    def test_wrap_includes_session_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "Memory.md").write_text(
                "# Discovery memory\n\n## Pitch\ncafe app\n\n## Turn log\n",
                encoding="utf-8",
            )
            out = wrap_discovery_message("Next question?", session_dir=root)
            self.assertIn("Workshop history (embedded", out)
            self.assertIn("cafe app", out)

    def test_bootstrap_no_skill_file_reference(self) -> None:
        msg = bootstrap_message(pitch="coffee app", session_dir="/tmp/s1")
        self.assertNotIn("Follow .cursor/skills/", msg)
        self.assertIn("workshop", msg.lower())
        self.assertIn(WORKSHOP_ROLE_BLOCK, msg)

    def test_valid_discovery_response(self) -> None:
        good = (
            "## Reflection\nYou want faster visible cards.\n\n## Questions\n\n"
            "### 1. First user\nWho benefits first?\n\n- A) a\n- B) b\n- C) c\n\n"
            "### 2. Speed\nWhat feels slow?\n\n- A) a\n- B) b\n- C) c\n\n"
            "### 3. Visibility\nWhat should users see?\n\n- A) a\n- B) b\n- C) c\n\n"
            "### 4. Scope\nWhich columns matter?\n\n- A) a\n- B) b\n- C) c\n\n"
            "### 5. Constraint\nWhat is fixed?\n\n- A) a\n- B) b\n- C) c\n"
        )
        self.assertTrue(valid_discovery_response(good))
        self.assertFalse(valid_discovery_response("## Action\n```json\n{\"action\":\"add\"}\n```"))
        self.assertFalse(
            valid_discovery_response("## Reflection\nHi\n\n## Questions\n\n### 1. Only one\n- A) a\n- B) b\n- C) c\n")
        )

    def test_valid_discovery_plain_numbered_and_agent_words(self) -> None:
        """Agent often emits '1. Title' (no ###) and mentions description agent in reflection."""
        good = (
            "## Reflection\nYou want a description agent to fill cards after titles land.\n\n## Questions\n\n"
            "1. What should the user see first?\nWhen titles arrive first?\n\n"
            "- A) shells then titles\n- B) wait for batch\n- C) placeholder row\n\n"
            "2. Who is waiting?\nWho watches extraction?\n\n- A) builder\n- B) facilitator\n- C) analyst\n\n"
            "3. When start descriptions?\nTrigger point?\n\n- A) per title\n- B) all titles\n- C) batches\n\n"
            "4. If description lags?\nQueue behavior?\n\n- A) backlog\n- B) cap concurrent\n- C) pause titles\n\n"
            "5. Persistent session?\nWhat failure?\n\n- A) context loss\n- B) UI flicker\n- C) cost\n"
        )
        self.assertTrue(valid_discovery_response(good))
        self.assertFalse(looks_like_code_output(good))

    def test_looks_like_code_output(self) -> None:
        self.assertTrue(looks_like_code_output("Exploring column_runner.py"))
        self.assertFalse(looks_like_code_output("## Reflection\nx\n\n## Questions\n### 1. T\n- A) a\n"))


if __name__ == "__main__":
    unittest.main()
