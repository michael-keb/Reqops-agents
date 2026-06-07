"""Load config from Call-backup/.env and optional uplift-reqops-e2e/.env."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = Path(__file__).resolve().parents[1]

DEFAULT_ENV_FILES = (
    ROOT / ".env",
    PKG / ".env",
)


def load_dotenv() -> None:
    for path in DEFAULT_ENV_FILES:
        if not path.is_file():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip("'\"")
            if key and key not in os.environ:
                os.environ[key] = val


def url(name: str, default: str) -> str:
    return os.environ.get(name, default).rstrip("/")


def reqops_backend_url() -> str:
    return url("REQOPS_BACKEND_URL", "http://127.0.0.1:3000")


def reqops_frontend_url() -> str:
    return url("REQOPS_FRONTEND_URL", "http://127.0.0.1:8080")


def uplift_bridge_url() -> str:
    return url("UPLIFT_BRIDGE_URL", "http://127.0.0.1:8786")


def agent_sdk_url() -> str:
    return url("AGENT_SDK_URL", "http://127.0.0.1:7778")


def cursor_api_key() -> str:
    return (os.environ.get("CURSOR_API_KEY") or "").strip()


def live_agent_enabled() -> bool:
    return os.environ.get("UPLIFT_E2E_LIVE", "").strip().lower() in ("1", "true", "yes")
