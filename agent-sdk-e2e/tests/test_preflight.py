"""Pre-flight checks before running cursor E2E tests."""

from __future__ import annotations

import httpx
import pytest

from lib.client import list_orphan_cursor_agents


pytestmark = [pytest.mark.requires_server]


class TestPreflight:
    def test_server_health(self, sdk_client, server_up):
        health = sdk_client.health()
        assert health.get("status") == "ok"

    def test_cursor_api_key_configured_on_server(self, sdk_client, server_up):
        health = sdk_client.health()
        assert health.get("cursor_api_key_configured") is True, (
            "Server health reports cursor_api_key_configured=false. "
            "Restart agent-sdk after setting CURSOR_API_KEY in Call-backup/.env"
        )

    def test_no_orphan_cursor_agent_processes(self, server_up):
        orphans = list_orphan_cursor_agents()
        assert not orphans, (
            "Found orphaned (PPID=1) agent acp processes that survived a "
            "supervisor restart and re-poll the keychain: "
            + ", ".join(f"pid={pid}" for pid, _ in orphans)
        )

    def test_ui_reachable(self, sdk_url, server_up):
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            resp = client.get(f"{sdk_url}/ui/")
            assert resp.status_code == 200
            assert "agent-type" in resp.text or "Agent" in resp.text
