"""HTTP-backed signal store — Postgres via ReqOps internal mutate API."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .store import MutationResult


class RemoteSignalStore:
    """Apply agent actions to ReqOps Postgres through internal mutate + snapshot routes."""

    def __init__(
        self,
        *,
        mutate_url: str,
        snapshot_url: str,
        mutate_token: str | None = None,
        run_id: str = "extract",
    ) -> None:
        self.mutate_url = mutate_url.rstrip("/")
        self.snapshot_url = snapshot_url.rstrip("/")
        self.mutate_token = mutate_token
        self.run_id = run_id
        self._lock = threading.Lock()
        self._snapshot_cache: dict[str, list[dict[str, Any]]] = {}

    def load(self) -> None:
        return

    def save(self) -> None:
        return

    def list_active_nodes(self) -> list[dict[str, Any]]:
        return []

    def _headers(self) -> dict[str, str]:
        headers = {"accept": "application/json", "content-type": "application/json"}
        if self.mutate_token:
            headers["x-uplift-internal-token"] = self.mutate_token
        return headers

    def _request_json(self, *, url: str, method: str = "GET", body: dict | None = None) -> dict[str, Any]:
        data = None
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"error": raw or f"HTTP {exc.code}"}
            if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
                return payload["data"]
            if isinstance(payload, dict):
                return payload
            return {"ok": False, "error": raw or f"HTTP {exc.code}"}
        except urllib.error.URLError as exc:
            return {"ok": False, "error": str(exc.reason)}
        if not raw.strip():
            return {}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {"ok": False, "error": "invalid JSON response"}
        if isinstance(parsed, dict) and "data" in parsed and isinstance(parsed["data"], dict):
            return parsed["data"]
        return parsed if isinstance(parsed, dict) else {}

    def column_snapshot(self, column_id: str) -> list[dict[str, Any]]:
        with self._lock:
            cached = self._snapshot_cache.get(column_id)
            if cached is not None:
                return [dict(row) for row in cached]
        url = f"{self.snapshot_url}?column={urllib.parse.quote(column_id)}"
        payload = self._request_json(url=url)
        rows = payload.get("snapshot")
        if not isinstance(rows, list):
            rows = []
        with self._lock:
            self._snapshot_cache[column_id] = [dict(r) for r in rows if isinstance(r, dict)]
        return [dict(row) for row in self._snapshot_cache.get(column_id, [])]

    def mutate(self, action: dict[str, Any], *, run_id: str) -> MutationResult:
        body = {**action, "run_id": run_id or self.run_id}
        payload = self._request_json(url=self.mutate_url, method="POST", body=body)
        verb = str(action.get("action") or "").lower()
        if verb == "complete":
            return MutationResult(ok=bool(payload.get("ok", True)), action=verb)

        snapshot = payload.get("snapshot")
        column_id = str(action.get("column") or "")
        if isinstance(snapshot, list) and column_id:
            with self._lock:
                self._snapshot_cache[column_id] = [dict(r) for r in snapshot if isinstance(r, dict)]

        node = payload.get("node") if isinstance(payload.get("node"), dict) else None
        return MutationResult(
            ok=bool(payload.get("ok")),
            action=verb,
            error=str(payload["error"]) if payload.get("error") else None,
            conflict=bool(payload.get("conflict")),
            not_found=bool(payload.get("not_found")),
            node=node,
        )
