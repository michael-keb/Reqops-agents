"""Routing mode from dominant term — step 5."""

from __future__ import annotations

from analyst.models import DriverScores, QuestionMode


def dominant_term_and_mode(
    drivers: DriverScores,
    terms: dict[str, float],
    *,
    k_term: float,
) -> tuple[str, QuestionMode]:
    """Pick largest term and map to question mode."""
    driver_terms = {
        "I": terms["I"],
        "C": terms["C"],
        "E": terms["E"],
    }
    max_driver = max(driver_terms, key=lambda k: driver_terms[k])
    max_val = driver_terms[max_driver]

    flat_drivers = max_val <= 1.0 and k_term >= 1.3
    if flat_drivers and k_term == max(k_term, max_val):
        return f"K={k_term}", "COVERAGE"

    code = getattr(drivers, max_driver)
    label = f"{max_driver}={max_val}"

    if max_driver == "I":
        if code in ("I2", "I3"):
            return label, "FOLLOW"
        return label, "FOLLOW"

    if max_driver == "C":
        if code == "C3":
            return label, "CONFRONT"
        if code == "C2":
            return label, "PROBE_SEAM"
        return label, "PROBE_SEAM"

    if max_driver == "E":
        if code == "E4":
            return label, "REASK_NARROWER"
        if code == "E1":
            return label, "CHALLENGE_GROUNDS"
        return label, "CHALLENGE_GROUNDS"

    return label, "FOLLOW"
