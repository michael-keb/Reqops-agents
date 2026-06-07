"""Load .env from project root; validate OpenAI credentials."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PLACEHOLDER_MARKERS = ("sk-your", "key-here", "your-key", "changeme")


def load_project_env(env_path: Path) -> None:
    """Parse .env; last assignment per key wins (handles duplicate keys)."""
    if not env_path.is_file():
        return

    try:
        from dotenv import load_dotenv

        load_dotenv(env_path, override=True)
        return
    except ImportError:
        pass

    values: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key:
            values[key] = value.strip().strip("'\"")

    for key, value in values.items():
        os.environ[key] = value


def mask_api_key(key: str) -> str:
    if len(key) <= 11:
        return "***"
    return f"{key[:7]}…{key[-4:]}"


def get_openai_api_key(env_path: Path) -> str:
    load_project_env(env_path)
    key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not key:
        sys.exit(
            f"OPENAI_API_KEY missing. Set it in {env_path} (see .env.example)."
        )
    lower = key.lower()
    if any(m in lower for m in PLACEHOLDER_MARKERS):
        sys.exit(
            f"OPENAI_API_KEY in {env_path} looks like a placeholder. "
            "Paste your real key from https://platform.openai.com/account/api-keys"
        )
    if not key.startswith("sk-"):
        sys.exit("OPENAI_API_KEY should start with sk-")
    return key
