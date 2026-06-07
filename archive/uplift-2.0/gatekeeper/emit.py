"""Serialize StateGrid to authoritative code line."""

from __future__ import annotations

from gatekeeper.legend import GAP_ORDER
from gatekeeper.models import StateGrid


def grid_to_code_line(grid: StateGrid) -> str:
    parts: list[str] = [grid.phase]

    for gap in GAP_ORDER:
        row = grid.rows.get(gap)
        if row:
            parts.append(f"{gap}:{row.exposure}")

    for extra in grid.extras:
        parts.append(f"{extra.gap}:{extra.exposure}")

    parts.extend(grid.leverage)
    parts.extend(grid.readiness)
    parts.extend(grid.shaping)
    parts.extend(grid.batch)

    return " ".join(parts)
