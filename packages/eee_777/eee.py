"""Equilibrium heuristics for EEE-777."""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

import json
import os

from platform.psi.psi_score import Metrics, SABARPause, get_floors
from packages.arif_asi.asi import assess_tone, tune

_LEDGER_FILENAME = "ledger.jsonl"


def _ledger_path() -> Path:
    override = os.getenv("ARIFOS_LEDGER_PATH")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[1] / "cooling_ledger" / _LEDGER_FILENAME


def _normalize_metrics(metrics: Mapping[str, Any] | Metrics) -> Dict[str, float]:
    if isinstance(metrics, Metrics):
        return asdict(metrics)
    if is_dataclass(metrics):  # pragma: no cover - defensive
        return asdict(metrics)
    return {key: float(value) for key, value in metrics.items()}


def _recent_entries(agent: str, limit: int = 5) -> Iterable[Dict[str, Any]]:
    path = _ledger_path()
    if not path.exists():
        return []

    entries: list[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:  # pragma: no cover - defensive
                continue
            if record.get("agent") == agent:
                entries.append(record)
    return entries[-limit:]


def limiter(agent: str, metrics: Mapping[str, Any] | Metrics) -> str:
    """Return ``allow``, ``delay``, or ``block`` based on Ψ trends and floors."""

    floors = get_floors()
    normalized = _normalize_metrics(metrics)
    psi_floor = floors.get("psi_min", 0.95)
    psi_value = float(normalized.get("psi") or normalized.get("Ψ") or 0.0)

    if psi_value <= 0.0:
        psi_value = max(
            normalized.get("deltaS", 0.0) * normalized.get("peace2", 0.0) * normalized.get("kappa_r", 0.0),
            0.0,
        )

    if normalized.get("deltaS", 0.0) < floors.get("deltaS", 0.0):
        return "block"

    if psi_value < psi_floor:
        return "block"

    near_threshold = psi_floor + 0.02
    recent = list(_recent_entries(agent))
    near_recent = sum(1 for entry in recent if float(entry.get("metrics", {}).get("psi", 0.0)) < near_threshold)

    if psi_value < near_threshold:
        return "block" if near_recent >= 1 else "delay"

    if near_recent >= 2:
        return "delay"

    return "allow"


def sabar_orchestrate(draft: str, metrics: Mapping[str, Any] | Metrics) -> Dict[str, Any]:
    """Run SABAR cooling loop and return the cooled draft payload."""

    floors = get_floors()
    normalized = _normalize_metrics(metrics)

    if normalized.get("truth", 0.0) < floors.get("truth", 0.99):
        raise SABARPause("Truth below governance floors during SABAR.")
    if normalized.get("deltaS", 0.0) < floors.get("deltaS", 0.0):
        raise SABARPause("ΔS below governance floors during SABAR.")

    tone = assess_tone(draft)
    if tone["peace2_hint"] >= floors.get("peace2", 1.0) and tone["rasa"] >= floors.get("rasa", 0.85):
        return {"draft": draft, "tone": tone, "modified": False}

    tuned = tune(draft, target_peace2=floors.get("peace2", 1.0))
    new_tone = {"rasa": tuned["rasa"], "peace2_hint": tuned["peace2_hint"]}

    if new_tone["peace2_hint"] < floors.get("peace2", 1.0) or new_tone["rasa"] < floors.get("rasa", 0.85):
        raise SABARPause("Cooling unsuccessful; escalation required.")

    return {"draft": tuned["text"], "tone": new_tone, "modified": bool(tuned.get("modified", False))}


def phoenix_schedule(reference: datetime | None = None) -> str:
    """Return the ISO timestamp for the next Phoenix-72 audit window."""

    reference = reference or datetime.now(timezone.utc)
    next_audit = reference + timedelta(hours=72)
    return next_audit.isoformat()


__all__ = ["limiter", "phoenix_schedule", "sabar_orchestrate"]
