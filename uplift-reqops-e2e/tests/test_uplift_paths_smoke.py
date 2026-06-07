"""E-01 … E-03: uplift bridge API paths (no ReqOps DB)."""

from __future__ import annotations

import uuid

import httpx
import pytest

from lib.env import uplift_bridge_url
from lib.sse import read_sse_events

pytestmark = [pytest.mark.requires_stack]


class TestUpliftBridgePaths:
    def test_session_start_and_state(self, stack_up):
        sid = f"e2e-{uuid.uuid4().hex[:12]}"
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{uplift_bridge_url()}/api/start",
                json={
                    "session_id": sid,
                    "pitch": "E2E smoke: dog walking app",
                    "bootstrap": False,
                },
            )
            assert resp.status_code == 200, resp.text
            assert resp.json().get("session_id") == sid

            state = client.get(f"{uplift_bridge_url()}/api/sessions/{sid}/state")
            assert state.status_code == 200

    def test_signals_extract_sse_accepts_goal_column(self, stack_up, live_agent):
        """Live: one SDK session pumps goal cards (set UPLIFT_E2E_LIVE=1)."""
        sid = f"e2e-{uuid.uuid4().hex[:12]}"
        pitch = "E2E smoke: marketplace with per-vendor carts, no cross-vendor mixing."
        with httpx.Client(timeout=30.0) as client:
            start = client.post(
                f"{uplift_bridge_url()}/api/start",
                json={"session_id": sid, "pitch": pitch, "bootstrap": True},
            )
            assert start.status_code == 200, start.text

        url = f"{uplift_bridge_url()}/api/sessions/{sid}/signals/extract/stream"
        with httpx.Client(timeout=180.0) as client:
            events = read_sse_events(
                client,
                method="POST",
                url=url,
                json_body={"columns": ["goal"]},
                timeout=180.0,
            )

        progress = [e.get("message") for e in events if e.get("type") == "progress"]
        assert any("agent ready (sdk)" in (m or "") for m in progress), progress[:5]
        result = next((e for e in events if e.get("type") == "result"), None)
        assert result is not None, events[-3:]
        assert result.get("summary", {}).get("columns_total") == 1
