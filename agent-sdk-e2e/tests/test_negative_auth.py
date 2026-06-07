"""Negative auth / agent-type E2E tests."""

from __future__ import annotations

import pytest

from lib.client import AgentSdkClient


pytestmark = [pytest.mark.requires_server]


class TestNegativeAuth:
    def test_claude_without_token_fails_or_errors_on_message(
        self, sdk_client: AgentSdkClient, server_up,
    ):
        """Claude selected without OAuth should not silently succeed."""
        data = sdk_client.create_session(agent_type="claude")
        session_id = data["session_id"]
        try:
            meta = sdk_client.get_session(session_id)
            assert meta.get("agent_type") == "claude"
            result = sdk_client.message_stream(
                session_id, "Reply exactly: NOPE"
            )
            text = result.text.upper()
            errors = " ".join(result.errors).lower()
            assert (
                "NOPE" not in text
                or "401" in errors
                or "invalid bearer" in errors
                or "authentication" in errors
            )
        finally:
            sdk_client.delete_session(session_id)

    def test_claude_with_invalid_token_errors(
        self, sdk_client: AgentSdkClient, server_up,
    ):
        data = sdk_client.create_session(
            agent_type="claude",
            secrets={"CLAUDE_CODE_OAUTH_TOKEN": "invalid-token-for-e2e-test"},
        )
        session_id = data["session_id"]
        try:
            result = sdk_client.message_stream(
                session_id, "Reply exactly: FAIL"
            )
            errors = " ".join(result.errors).lower()
            assert (
                "401" in errors
                or "invalid bearer" in errors
                or "authentication" in errors
                or not result.text
            )
        finally:
            sdk_client.delete_session(session_id)

    def test_cursor_agent_type_not_claude(self, sdk_client: AgentSdkClient, server_up, cursor_key):
        data = sdk_client.create_session(agent_type="cursor")
        try:
            meta = sdk_client.get_session(data["session_id"])
            assert meta.get("agent_type") == "cursor"
            secret_keys = (meta.get("secrets") or {}).get("keys", [])
            assert "CURSOR_API_KEY" in secret_keys
            assert "CLAUDE_CODE_OAUTH_TOKEN" not in secret_keys
        finally:
            sdk_client.delete_session(data["session_id"])
