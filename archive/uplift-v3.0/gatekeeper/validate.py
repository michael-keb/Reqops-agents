"""Validate state code lines and grid consistency."""

from __future__ import annotations

import re

from gatekeeper.legend import (
    ALL_BEHAVIOURAL,
    CANONICAL_GAPS,
    EXPOSURES,
    GAP_CODES,
)
from gatekeeper.models import StateGrid, ValidationResult

GAP_EXPOSURE_RE = re.compile(r"^(G[0-9A-D]|G0):(X[1-9])$")
TOKEN_RE = re.compile(r"\b([A-Z]+\d?|[A-Z]{2})\b")


def parse_code_line(line: str) -> tuple[list[str], dict[str, str]]:
    """Return (bare tokens, gap->exposure map)."""
    tokens: list[str] = []
    gap_map: dict[str, str] = {}
    for raw in line.replace("`", "").split():
        tok = raw.strip()
        if not tok:
            continue
        m = GAP_EXPOSURE_RE.match(tok)
        if m:
            gap, exp = m.group(1), m.group(2)
            gap_map[gap] = exp
            continue
        tokens.append(tok)
    return tokens, gap_map


def validate_token(token: str) -> bool:
    return token in ALL_BEHAVIOURAL or GAP_EXPOSURE_RE.match(token) is not None


def validate_code_line(line: str, *, require_all_gaps: bool = False) -> ValidationResult:
    if not line or not line.strip():
        return ValidationResult.failure("empty code line")

    errors: list[str] = []
    warnings: list[str] = []
    tokens, gap_map = parse_code_line(line)

    for tok in tokens:
        if not validate_token(tok):
            errors.append(f"invalid token: {tok}")

    for gap, exp in gap_map.items():
        if gap not in GAP_CODES:
            errors.append(f"invalid gap code: {gap}")
        if exp not in EXPOSURES:
            errors.append(f"invalid exposure: {exp}")

    if require_all_gaps:
        missing = [g for g in CANONICAL_GAPS if g not in gap_map]
        if missing:
            errors.append(f"missing gaps in line: {', '.join(missing)}")

    seen: set[str] = set()
    for gap in gap_map:
        if gap in seen:
            errors.append(f"duplicate gap in line: {gap}")
        seen.add(gap)

    return ValidationResult(ok=not errors, errors=errors, warnings=warnings)


def validate_grid_matches_line(grid: StateGrid, line: str) -> ValidationResult:
    vr = validate_code_line(line, require_all_gaps=True)
    if not vr.ok:
        return vr

    _, gap_map = parse_code_line(line)
    errors: list[str] = []
    for gap, row in grid.rows.items():
        expected = f"{gap}:{row.exposure}"
        actual = f"{gap}:{gap_map.get(gap, '?')}"
        if actual != expected:
            errors.append(f"grid/line mismatch {gap}: grid={row.exposure} line={gap_map.get(gap)}")

    if grid.phase not in line.split():
        errors.append(f"phase {grid.phase} missing from code line")

    return ValidationResult(ok=not errors, errors=errors)


def validate_mcq_count(plan_slots: int, mcq_headers: int) -> ValidationResult:
    if mcq_headers != plan_slots:
        return ValidationResult.failure(
            f"MCQ count {mcq_headers} != plan slots {plan_slots}"
        )
    return ValidationResult.success()


def count_mcq_headers(reply: str) -> int:
    return len(re.findall(r"^###\s+\d+\.", reply, re.MULTILINE))
