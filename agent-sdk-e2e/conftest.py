"""Pytest fixtures for agent-sdk E2E tests."""

from __future__ import annotations

import httpx
import pytest

from lib.client import AgentSdkClient
from lib.env import api_base, cursor_api_key, load_dotenv

load_dotenv()


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "requires_server: test needs agent-sdk server running on AGENT_SDK_URL",
    )
    config.addinivalue_line(
        "markers",
        "requires_cursor_key: test needs CURSOR_API_KEY in environment",
    )


@pytest.fixture(scope="session")
def sdk_url() -> str:
    return api_base()


@pytest.fixture(scope="session")
def sdk_client(sdk_url: str) -> AgentSdkClient:
    return AgentSdkClient(base_url=sdk_url)


@pytest.fixture(scope="session")
def server_up(sdk_url: str) -> None:
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{sdk_url}/health")
            resp.raise_for_status()
    except (httpx.HTTPError, OSError) as exc:
        pytest.skip(f"agent-sdk server not reachable at {sdk_url}: {exc}")


@pytest.fixture(scope="session")
def cursor_key() -> str:
    key = cursor_api_key()
    if not key:
        pytest.skip("CURSOR_API_KEY not set (check Call-backup/.env)")
    return key


@pytest.fixture
def cursor_session(sdk_client: AgentSdkClient, server_up: None, cursor_key: str):
    """Create a cursor session; delete after test."""
    data = sdk_client.create_session(agent_type="cursor")
    assert data.get("connected") is True
    session_id = data["session_id"]
    yield data
    sdk_client.delete_session(session_id)
