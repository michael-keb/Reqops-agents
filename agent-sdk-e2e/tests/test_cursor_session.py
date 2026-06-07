"""Cursor session creation E2E tests."""

from __future__ import annotations

import pytest

from lib.client import AgentSdkClient


pytestmark = [pytest.mark.requires_server, pytest.mark.requires_cursor_key]


class TestCursorSessionCreate:
    def test_create_without_body_secrets_uses_server_env(
        self, sdk_client: AgentSdkClient, server_up, cursor_key: str,
    ):
        data = sdk_client.create_session(agent_type="cursor")
        try:
            assert data.get("connected") is True
            assert data.get("session_id")
            assert data.get("agent_type") == "cursor"
            meta = sdk_client.get_session(data["session_id"])
            assert meta.get("agent_type") == "cursor"
            assert "CURSOR_API_KEY" in (meta.get("secrets") or {}).get("keys", [])
        finally:
            sdk_client.delete_session(data["session_id"])

    def test_create_with_explicit_api_key(
        self, sdk_client: AgentSdkClient, server_up, cursor_key: str,
    ):
        data = sdk_client.create_session(
            agent_type="cursor",
            secrets={"CURSOR_API_KEY": cursor_key},
        )
        try:
            assert data.get("connected") is True
            assert data.get("agent_type") == "cursor"
        finally:
            sdk_client.delete_session(data["session_id"])

    def test_invalid_api_key_fails_on_message(
        self, sdk_client: AgentSdkClient, server_up,
    ):
        data = sdk_client.create_session(
            agent_type="cursor",
            secrets={"CURSOR_API_KEY": "crsr_invalid_test_key_000000000000000000000000"},
        )
        session_id = data["session_id"]
        try:
            result = sdk_client.message_stream(session_id, "Reply exactly: NOPE")
            errors = " ".join(result.errors).lower()
            assert (
                "authentication" in errors
                or "401" in errors
                or "api key" in errors
                or not result.text
            )
        finally:
            sdk_client.delete_session(session_id)
