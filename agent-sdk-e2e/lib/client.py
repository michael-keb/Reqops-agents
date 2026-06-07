"""HTTP client for agent-sdk server E2E tests."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

import httpx

from lib.env import api_base


@dataclass
class StreamResult:
    text_chunks: list[str]
    raw_events: list[dict[str, Any]]
    errors: list[str]

    @property
    def text(self) -> str:
        return "".join(self.text_chunks)

    @property
    def ok(self) -> bool:
        return not self.errors and bool(self.text_chunks)


class AgentSdkClient:
    def __init__(self, base_url: str | None = None, timeout: float = 120.0) -> None:
        self.base_url = (base_url or api_base()).rstrip("/")
        self.timeout = timeout

    def health(self) -> dict[str, Any]:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{self.base_url}/health")
            resp.raise_for_status()
            return resp.json()

    def create_session(
        self,
        *,
        provider: str = "unix_local",
        agent_type: str = "cursor",
        secrets: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "provider": provider,
            "agent_type": agent_type,
        }
        if secrets:
            body["secrets"] = secrets
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(f"{self.base_url}/sessions", json=body)
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"POST /sessions failed ({resp.status_code}): {resp.text}"
                )
            return resp.json()

    def get_session(self, session_id: str) -> dict[str, Any]:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(f"{self.base_url}/sessions/{session_id}")
            resp.raise_for_status()
            return resp.json()

    def delete_session(self, session_id: str) -> None:
        with httpx.Client(timeout=30.0) as client:
            resp = client.delete(f"{self.base_url}/sessions/{session_id}")
            if resp.status_code not in (200, 204, 404):
                resp.raise_for_status()

    def message_stream(self, session_id: str, message: str) -> StreamResult:
        chunks: list[str] = []
        events: list[dict[str, Any]] = []
        errors: list[str] = []

        with httpx.Client(timeout=self.timeout) as client:
            with client.stream(
                "POST",
                f"{self.base_url}/sessions/{session_id}/message+stream",
                json={"message": message},
            ) as resp:
                if resp.status_code >= 400:
                    body = resp.read().decode("utf-8", errors="replace")
                    raise RuntimeError(
                        f"message+stream failed ({resp.status_code}): {body}"
                    )
                for line in resp.iter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        event = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
                    events.append(event)
                    err = _extract_error(event)
                    if err:
                        errors.append(err)
                    text = _extract_text_chunk(event)
                    if text:
                        chunks.append(text)
        return StreamResult(text_chunks=chunks, raw_events=events, errors=errors)


def _extract_text_chunk(event: dict[str, Any]) -> str:
    if event.get("method") != "session/update":
        return ""
    params = event.get("params") or {}
    update = params.get("update") or {}
    if update.get("sessionUpdate") != "agent_message_chunk":
        return ""
    content = update.get("content") or {}
    if content.get("type") == "text":
        return str(content.get("text") or "")
    return ""


def _extract_error(event: dict[str, Any]) -> str:
    if "error" in event:
        err = event["error"]
        if isinstance(err, dict):
            return str(err.get("message") or err)
        return str(err)
    params = event.get("params") or {}
    update = params.get("update") or {}
    if update.get("sessionUpdate") == "error":
        return str(update.get("message") or update)
    return ""


def list_orphan_cursor_agents() -> list[tuple[int, str]]:
    """Return orphaned (PPID=1) cursor ``agent ... acp`` processes.

    These survive a supervisor restart, poll the macOS keychain, and pop
    "Keychain Not Found" dialogs — regardless of whether --api-key is set.
    """
    import subprocess

    out: list[tuple[int, str]] = []
    try:
        proc = subprocess.run(
            ["ps", "ax", "-o", "pid=,ppid=,command="],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return out
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"(\d+)\s+(\d+)\s+(.*)", line)
        if not m:
            continue
        pid = int(m.group(1))
        ppid = int(m.group(2))
        cmd = m.group(3)
        if " acp" not in cmd and not cmd.rstrip().endswith("acp"):
            continue
        if "/agent" not in cmd and ".local/bin/agent" not in cmd:
            continue
        if ppid != 1:
            continue
        out.append((pid, cmd))
    return out
