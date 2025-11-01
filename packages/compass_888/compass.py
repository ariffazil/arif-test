"""Rule-based routing heuristics for the Compass-888 module."""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

from platform.psi.psi_score import Metrics, get_floors
from packages.arif_asi.asi import assess_tone, compute_conductance


def _as_mapping(metrics: Mapping[str, Any] | Metrics) -> Mapping[str, float]:
    if isinstance(metrics, Metrics):
        return asdict(metrics)
    if is_dataclass(metrics):  # pragma: no cover - defensive
        return asdict(metrics)
    return metrics


def noise_score(text: str) -> float:
    """Return a heuristic noise score in ``[0, 1]`` based on aggression markers."""

    tone = assess_tone(text)
    hits = tone["negative_hits"] + (1 if text.count("!!") else 0)
    length = max(len(text.split()), 1)
    raw = hits / length
    return max(0.0, min(1.0, raw * 3.0))


def route(task: str, draft: str, metrics: Mapping[str, Any] | Metrics) -> str:
    """Select the next module in the Core-5 chain based on telemetry."""

    floors = get_floors()
    mapping = _as_mapping(metrics)

    truth = float(mapping.get("truth", 0.0))
    deltaS = float(mapping.get("deltaS", 0.0))
    peace2 = float(mapping.get("peace2", 0.0))
    kappa = float(mapping.get("kappa_r", 0.0))

    if noise_score(draft) > 0.65:
        return "arif-asi"

    if truth < floors.get("truth", 0.99) or deltaS < floors.get("deltaS", 0.0):
        return "arif-agi"

    if peace2 < floors.get("peace2", 1.0) or kappa < floors.get("kappa_r", 0.95):
        return "arif-asi"

    kappa_margin = floors.get("kappa_r", 0.95) + 0.01
    if kappa <= kappa_margin:
        conductance = compute_conductance(task, draft)
        if conductance < floors.get("kappa_r", 0.95):
            return "arif-asi"

    return "apex-prime"


__all__ = ["noise_score", "route"]
