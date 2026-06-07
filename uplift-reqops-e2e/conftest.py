"""Pytest fixtures for uplift-reqops E2E."""

from __future__ import annotations

import pytest

from lib.env import load_dotenv, live_agent_enabled
from lib.stack import STACK, check_all

load_dotenv()


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "requires_stack: core services must be reachable",
    )
    config.addinivalue_line(
        "markers",
        "requires_live_agent: real Cursor/agent-sdk LLM call (set UPLIFT_E2E_LIVE=1)",
    )


@pytest.fixture(scope="session")
def stack_results():
    return check_all()


@pytest.fixture(scope="session")
def stack_up(stack_results):
    failed = [r for r in stack_results if not r.ok]
    if failed:
        names = ", ".join(r.spec.name for r in failed)
        pytest.skip(f"Stack not ready — failed: {names}. Run ./scripts/check_stack.sh")


@pytest.fixture(scope="session")
def live_agent():
    if not live_agent_enabled():
        pytest.skip("Set UPLIFT_E2E_LIVE=1 to run live agent tests")


@pytest.fixture(scope="session")
def stack_specs():
    return STACK
