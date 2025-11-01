"""Tri-witness quorum evaluation utilities."""
from __future__ import annotations

from statistics import mean
from typing import Tuple

from platform.psi.psi_score import get_floors


def _threshold(explicit: float | None = None) -> float:
    if explicit is not None:
        return float(explicit)
    floors = get_floors()
    return float(floors.get("tri_witness", 0.95))


def check_quorum(human: float, ai: float, earth: float, threshold: float | None = None) -> Tuple[bool, float]:
    """Return a tuple of (quorum_met, average_score)."""

    scores = (human, ai, earth)
    avg_score = mean(scores)
    floor = _threshold(threshold)
    passed = all(score >= floor for score in scores) and avg_score >= floor
    return passed, avg_score


__all__ = ["check_quorum"]
