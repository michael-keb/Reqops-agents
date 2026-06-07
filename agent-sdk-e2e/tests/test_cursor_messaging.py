"""Cursor messaging E2E tests."""

from __future__ import annotations

import pytest

from lib.client import AgentSdkClient


pytestmark = [pytest.mark.requires_server, pytest.mark.requires_cursor_key]


class TestCursorMessaging:
    def test_single_turn_exact_reply(self, sdk_client: AgentSdkClient, cursor_session):
        session_id = cursor_session["session_id"]
        result = sdk_client.message_stream(
            session_id, "Reply with exactly one word: HELLO"
        )
        assert not result.errors, result.errors
        assert "HELLO" in result.text.upper(), result.text

    def test_follow_up_turn(self, sdk_client: AgentSdkClient, cursor_session):
        session_id = cursor_session["session_id"]
        first = sdk_client.message_stream(
            session_id, "Reply with exactly: FIRST"
        )
        assert not first.errors, first.errors
        assert "FIRST" in first.text.upper()

        second = sdk_client.message_stream(
            session_id, "Reply with exactly: SECOND"
        )
        assert not second.errors, second.errors
        assert "SECOND" in second.text.upper()

    def test_no_auth_error_in_stream(self, sdk_client: AgentSdkClient, cursor_session):
        session_id = cursor_session["session_id"]
        result = sdk_client.message_stream(
            session_id, "Say hi in one short sentence."
        )
        joined_errors = " ".join(result.errors).lower()
        assert "401" not in joined_errors
        assert "invalid bearer" not in joined_errors
        assert "authentication" not in joined_errors or result.text
