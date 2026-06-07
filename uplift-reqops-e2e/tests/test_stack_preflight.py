"""P-01 … P-12: verify every service required for /thoughts uplift flow."""

from __future__ import annotations

import httpx
import pytest

from lib.env import (
    agent_sdk_url,
    cursor_api_key,
    reqops_backend_url,
    uplift_bridge_url,
)
from lib.stack import STACK, check_all, format_stack_report

pytestmark = [pytest.mark.requires_stack]


class TestStackPreflight:
    def test_report_prints(self, stack_results, capsys):
        """Always emit a human-readable stack table (see pytest -s)."""
        print("\n" + format_stack_report(stack_results))
        assert STACK

    def test_postgres_via_backend(self, stack_up, stack_results):
        row = next(r for r in stack_results if r.spec.id == "postgres")
        assert row.ok, row.detail

    def test_reqops_backend_health(self, stack_up):
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{reqops_backend_url()}/healthz")
            assert resp.status_code == 200
            body = resp.json()
            assert body.get("status") == "ok" or body.get("ok") is True

    def test_reqops_frontend_serves_spa(self, stack_up):
        from lib.env import reqops_frontend_url

        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            resp = client.get(f"{reqops_frontend_url()}/")
            assert resp.status_code == 200
            assert "ReqOps" in resp.text or "root" in resp.text

    def test_uplift_bridge_health(self, stack_up):
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{uplift_bridge_url()}/api/health")
            assert resp.status_code == 200
            body = resp.json()
            assert body.get("ok") is True
            assert body.get("mode") == "headless", (
                "ReqOps discovery expects UPLIFT_AGENT_MODE=headless (./serve default)"
            )

    def test_uplift_runners_are_sdk(self, stack_up):
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{uplift_bridge_url()}/api/health")
            body = resp.json()
            assert body.get("discovery_runner") == "sdk", (
                "Discovery needs UPLIFT_DISCOVERY_RUNNER=sdk (see uplift-v6/serve)"
            )
            assert body.get("signals_runner") == "sdk", (
                "Signal board needs UPLIFT_SIGNALS_RUNNER=sdk (see uplift-v6/serve)"
            )

    def test_agent_sdk_health(self, stack_up):
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{agent_sdk_url()}/health")
            assert resp.status_code == 200
            body = resp.json()
            assert body.get("status") == "ok"
            assert body.get("cursor_api_key_configured") is True, (
                "agent-sdk needs CURSOR_API_KEY from Call-backup/.env"
            )

    def test_cursor_cli_on_path(self, stack_up, stack_results):
        row = next(r for r in stack_results if r.spec.id == "cursor_cli")
        assert row.ok, row.detail

    def test_cursor_api_key_in_env(self, stack_up):
        assert cursor_api_key(), "CURSOR_API_KEY missing in Call-backup/.env"

    def test_reqops_discovery_engine_uplift(self, stack_up):
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{reqops_backend_url()}/api/v1/discovery/config")
            assert resp.status_code == 200
            engine = resp.json().get("data", {}).get("engine")
            assert engine == "uplift", (
                f"Reqops_backend/.env needs DISCOVERY_ENGINE=uplift (got {engine!r})"
            )

    def test_all_stack_services_green(self, stack_results):
        failed = [r for r in stack_results if not r.ok]
        assert not failed, format_stack_report(stack_results)
