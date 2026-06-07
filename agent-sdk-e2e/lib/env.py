"""Load config from environment and parent ``Call-backup/.env``."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILES = (
    ROOT / ".env",
    Path(__file__).resolve().parents[1] / ".env",
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
            if not key:
                continue
            if key in ("CURSOR_API_KEY", "cursor_api_key"):
                continue
            if key not in os.environ:
                os.environ[key] = val
    key = (
        os.environ.get("CURSOR_API_KEY")
        or os.environ.get("cursor_api_key")
        or ""
    ).strip()
    for path in DEFAULT_ENV_FILES:
        if not path.is_file():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k = k.strip()
            v = v.strip().strip("'\"")
            if k in ("CURSOR_API_KEY", "cursor_api_key") and v:
                key = key or v
    if key:
        os.environ["CURSOR_API_KEY"] = key


def api_base() -> str:
    return os.environ.get("AGENT_SDK_URL", "http://localhost:7778").rstrip("/")


def cursor_api_key() -> str:
    return (
        os.environ.get("CURSOR_API_KEY")
        or os.environ.get("cursor_api_key")
        or ""
    ).strip()
