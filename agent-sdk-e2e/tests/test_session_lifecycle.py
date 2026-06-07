"""Session lifecycle E2E tests."""

from __future__ import annotations

import pytest

from lib.client import AgentSdkClient


pytestmark = [pytest.mark.requires_server, pytest.mark.requires_cursor_key]


class TestSessionLifecycle:
    def test_disconnect_and_new_session(self, sdk_client: AgentSdkClient, server_up):
        first = sdk_client.create_session(agent_type="cursor")
        assert first.get("connected") is True
        first_id = first["session_id"]
        sdk_client.delete_session(first_id)

        second = sdk_client.create_session(agent_type="cursor")
        try:
            assert second.get("connected") is True
            assert second["session_id"] != first_id
            result = sdk_client.message_stream(
                second["session_id"], "Reply exactly: OK"
            )
            assert not result.errors, result.errors
            assert "OK" in result.text.upper()
        finally:
            sdk_client.delete_session(second["session_id"])

    def test_get_session_metadata(self, sdk_client: AgentSdkClient, cursor_session):
        session_id = cursor_session["session_id"]
        meta = sdk_client.get_session(session_id)
        assert meta["session_id"] == session_id
        assert meta.get("agent_type") == "cursor"
        assert meta.get("sandbox_ref")
