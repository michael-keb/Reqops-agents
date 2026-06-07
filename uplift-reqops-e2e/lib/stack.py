"""Service definitions and reachability checks for the ReqOps + Uplift stack."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from typing import Any

import httpx

from .env import (
    agent_sdk_url,
    cursor_api_key,
    reqops_backend_url,
    reqops_frontend_url,
    uplift_bridge_url,
)


@dataclass(frozen=True)
class ServiceSpec:
    id: str
    name: str
    port: int
    url: str
    start_hint: str
    required_for: str


STACK: tuple[ServiceSpec, ...] = (
    ServiceSpec(
        id="postgres",
        name="PostgreSQL",
        port=5432,
        url="postgresql://localhost:5432",
        start_hint="docker run --rm -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=thoughtweaver postgres:15",
        required_for="ReqOps sessions, thought nodes, signal cards",
    ),
    ServiceSpec(
        id="reqops_backend",
        name="ReqOps backend",
        port=3000,
        url=f"{reqops_backend_url()}/healthz",
        start_hint="cd Reqops_backend && npm run dev",
        required_for="API, auth, discovery SSE proxy, signal mutate",
    ),
    ServiceSpec(
        id="reqops_frontend",
        name="ReqOps frontend",
        port=8080,
        url=reqops_frontend_url(),
        start_hint="cd Reqops_Frontend && npm run dev",
        required_for="UI at /thoughts/:sessionId",
    ),
    ServiceSpec(
        id="uplift_bridge",
        name="Uplift v6 bridge",
        port=8786,
        url=f"{uplift_bridge_url()}/api/health",
        start_hint="cd uplift-v6 && ./serve",
        required_for="Discovery turns (CLI) + signal extract orchestration",
    ),
    ServiceSpec(
        id="agent_sdk",
        name="agent-sdk server",
        port=7778,
        url=f"{agent_sdk_url()}/health",
        start_hint="cd agent-sdk && uvicorn api.server:app --host 0.0.0.0 --port 7778",
        required_for="Signal board — one persistent session per extract (UPLIFT_SIGNALS_RUNNER=sdk)",
    ),
    ServiceSpec(
        id="cursor_cli",
        name="Cursor agent CLI",
        port=0,
        url="",
        start_hint="curl https://cursor.com/install -fsS | bash && agent login",
        required_for="Phase 01 discovery MCQ turns (headless subprocess)",
    ),
)


@dataclass
class CheckResult:
    spec: ServiceSpec
    ok: bool
    detail: str
    extra: dict[str, Any] | None = None


def check_http(url: str, *, timeout: float = 5.0) -> tuple[bool, str, dict[str, Any] | None]:
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url)
            extra = None
            if resp.headers.get("content-type", "").startswith("application/json"):
                try:
                    extra = resp.json()
                except Exception:
                    extra = None
            if resp.status_code < 500:
                return True, f"HTTP {resp.status_code}", extra
            return False, f"HTTP {resp.status_code}", extra
    except (httpx.HTTPError, OSError) as exc:
        return False, str(exc), None


def check_cursor_cli() -> CheckResult:
    spec = next(s for s in STACK if s.id == "cursor_cli")
    path = shutil.which("agent")
    if not path:
        return CheckResult(spec, False, "agent not on PATH", None)
    try:
        proc = subprocess.run(
            [path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        detail = (proc.stdout or proc.stderr or "").strip()[:120] or "ok"
        ok = proc.returncode == 0
    except (subprocess.TimeoutExpired, OSError) as exc:
        return CheckResult(spec, False, str(exc), None)
    return CheckResult(spec, ok, detail or path, {"path": path})


def check_postgres_via_backend() -> CheckResult:
    spec = next(s for s in STACK if s.id == "postgres")
    ok, detail, extra = check_http(f"{reqops_backend_url()}/healthz")
    if not ok:
        return CheckResult(spec, False, f"backend unreachable — cannot verify DB ({detail})", extra)
    if extra and (extra.get("status") == "ok" or extra.get("ok") is True):
        return CheckResult(spec, True, "reachable via ReqOps /healthz", extra)
    return CheckResult(
        spec,
        False,
        f"backend up but unhealthy: {extra}",
        extra,
    )


def check_service(spec: ServiceSpec) -> CheckResult:
    if spec.id == "postgres":
        return check_postgres_via_backend()
    if spec.id == "cursor_cli":
        return check_cursor_cli()
    ok, detail, extra = check_http(spec.url)
    return CheckResult(spec, ok, detail, extra)


def check_all() -> list[CheckResult]:
    return [check_service(s) for s in STACK]


def format_stack_report(results: list[CheckResult]) -> str:
    lines = ["ReqOps + Uplift stack preflight", "=" * 40]
    for r in results:
        mark = "OK" if r.ok else "FAIL"
        lines.append(f"[{mark}] {r.spec.name} ({r.spec.port or 'PATH'}) — {r.detail}")
        if not r.ok:
            lines.append(f"      start: {r.spec.start_hint}")
        lines.append(f"      used for: {r.spec.required_for}")
    lines.append("")
    key = cursor_api_key()
    lines.append(f"CURSOR_API_KEY: {'set' if key else 'MISSING (Call-backup/.env)'}")
    return "\n".join(lines)
