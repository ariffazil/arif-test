"""Ψ (Psi) computation utilities for ArifOS.

This module enforces metric floors specified in ``docs/floors.yaml`` and
provides helpers to evaluate whether a set of metrics satisfies the
TEARFRAME governance requirements.  It intentionally keeps the implementation
compact and dependency-light so it can be imported from any agent package.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable

import math

try:  # pragma: no cover - import resolution depends on environment
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    yaml = None  # type: ignore


class SABARPause(RuntimeError):
    """Raised when Ψ or one of the metric floors breaches governance limits."""


@dataclass(frozen=True)
class Metrics:
    """Snapshot of the telemetry metrics produced by an agent run."""

    truth: float
    peace2: float
    kappa_r: float
    deltaS: float
    rasa: float
    amanah: float
    entropy: float = 1.0

    def as_floor_dict(self) -> Dict[str, float]:
        """Expose the metrics as a mapping compatible with the floor schema."""

        return asdict(self)


@lru_cache(maxsize=1)
def _default_floors() -> Dict[str, float]:
    """Load the TEARFRAME floors from ``docs/floors.yaml`` once per process."""

    floors_path = Path(__file__).resolve().parents[2] / "docs" / "floors.yaml"
    with floors_path.open("r", encoding="utf-8") as handle:
        raw = handle.read()

    if yaml is not None:
        data = yaml.safe_load(raw) or {}
    else:  # pragma: no cover - executed when PyYAML is unavailable
        data = _parse_simple_yaml(raw)
    return {str(key): float(value) for key, value in data.items()}


def _parse_simple_yaml(raw: str) -> Dict[str, float]:
    parsed: Dict[str, float] = {}
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        parsed[key.strip()] = float(value.strip())
    return parsed


def get_floors() -> Dict[str, float]:
    """Return a copy of the cached floor configuration."""

    return dict(_default_floors())


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def meets_floors(metrics: Metrics, floors: Dict[str, float] | None = None) -> bool:
    """Return ``True`` when every governed metric satisfies the configured floor."""

    floors = floors or _default_floors()
    metric_map = metrics.as_floor_dict()

    def _iter_floor_checks() -> Iterable[bool]:
        for key, limit in floors.items():
            if key not in metric_map:
                # Floors such as tri_witness apply outside of Metrics and are ignored.
                continue
            value = metric_map[key]
            if not math.isfinite(value):
                yield False
                continue
            yield value >= limit

    return all(_iter_floor_checks())


def psi_from(metrics: Metrics, floors: Dict[str, float] | None = None, *, epsilon: float = 1e-9) -> float:
    """Compute the Ψ score and enforce governance floors.

    ``floors`` defaults to the values from ``docs/floors.yaml``.  The function
    raises :class:`SABARPause` when a floor is breached or the resulting Ψ falls
    below the configured ``psi_min`` (defaults to ``0.95`` when absent).
    """

    floors = floors or _default_floors()
    psi_floor = float(floors.get("psi_min", 0.95))

    if not meets_floors(metrics, floors):
        raise SABARPause("Metric floors breached before Ψ computation.")

    numerator = metrics.deltaS * metrics.peace2 * metrics.kappa_r * metrics.rasa * metrics.amanah
    denominator = max(metrics.entropy, 0.0) + epsilon
    raw_psi = numerator / denominator
    psi = _clamp(raw_psi, 0.0, 2.0)

    if psi < psi_floor:
        raise SABARPause(f"Ψ={psi:.3f} below governance floor {psi_floor:.2f}.")

    return psi


__all__ = ["Metrics", "SABARPause", "psi_from", "meets_floors", "get_floors"]
