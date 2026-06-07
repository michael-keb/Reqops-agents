"""Emit multiplier state lines for audit — deterministic after I×C×E×R×K."""

from __future__ import annotations

from analyst.models import ScoredCandidate

_MODE_SHORT: dict[str, str] = {
    "FOLLOW": "FOLLOW",
    "CONFRONT": "CONFRONT",
    "PROBE_SEAM": "PROBE",
    "REASK_NARROWER": "RENARROW",
    "CHALLENGE_GROUNDS": "CHALLENGE",
    "COVERAGE": "COVER",
    "INTAKE": "—",
}


def _driver_compact(drivers) -> str:
    return f"I{drivers.I[1:]}C{drivers.C[1:]}E{drivers.E[1:]}"


def format_candidate_line(sc: ScoredCandidate) -> str:
    """GA  I2C1E0·R0K2 = 6.40 → FOLLOW"""
    r = sc.guards["R"][1:]
    k = sc.guards["K"][1:]
    mode = _MODE_SHORT.get(sc.mode, sc.mode)
    dead = ""
    if sc.guards["R"] == "R3":
        dead = " → dead (R3)"
    elif sc.score < 0.5 and sc.guards["R"] != "R3":
        dead = " → —"
    arrow = dead if dead else f" → {mode}"
    return f"{sc.gap}  {_driver_compact(sc.drivers)}·R{r}K{k} = {sc.score:.2f}{arrow}"


def format_multiplier_audit(
    *,
    turn: int,
    scored: list[ScoredCandidate],
    vetoed: list[dict[str, str]],
    primary: ScoredCandidate | None,
    why: str = "",
) -> str:
    lines: list[str] = [
        f"TURN {turn} — MULTIPLIER STATE",
        "",
        "Format: <gap>  I<n>C<n>E<n>·R<n>K<n> = <score> → <MODE>",
        "",
    ]
    for sc in sorted(scored, key=lambda s: s.score, reverse=True):
        lines.append(format_candidate_line(sc))

    lines.append("")
    if primary:
        mode = _MODE_SHORT.get(primary.mode, primary.mode)
        lines.append(f"PRIMARY: {primary.gap} → {mode}")
    if vetoed:
        for v in vetoed:
            lines.append(f"VETOED: {v['gap']} ({v['reason']})")
    if why.strip():
        lines.append(f"why: {why.strip()}")
    return "\n".join(lines) + "\n"
