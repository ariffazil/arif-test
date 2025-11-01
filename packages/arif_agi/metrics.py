"""Metric estimation heuristics for the Arif-AGI agent."""
from __future__ import annotations

from dataclasses import asdict

from packages.arif_asi.asi import assess_tone, compute_conductance
from platform.psi.psi_score import Metrics, get_floors


def _truth_score(task: str, draft: str) -> float:
    lowered = f"{task} {draft}".lower()
    if any(word in lowered for word in ["harm", "violence", "attack"]):
        return 0.9
    if "evidence" in lowered or "step" in lowered:
        return 1.02
    if "speculative" in lowered:
        return 0.97
    return 1.0


def _delta_s_score(task: str, draft: str) -> float:
    lowered = draft.lower()
    if any(word in lowered for word in ["harm", "violence", "attack"]):
        return -0.2
    if any(word in lowered for word in ["calm", "care", "support", "cooperate"]):
        return 1.1
    if "edge case" in task.lower():
        return 0.9
    return 0.75


def evaluate_metrics(task: str, draft: str) -> Metrics:
    """Return a :class:`Metrics` snapshot derived from the plan draft."""

    floors = get_floors()
    tone = assess_tone(draft)
    kappa = compute_conductance(task, draft)

    truth = max(0.0, _truth_score(task, draft))
    delta_s = max(floors.get("deltaS", 0.0), _delta_s_score(task, draft))
    peace2 = min(1.5, max(floors.get("peace2", 1.0), tone["peace2_hint"] + 0.05))
    rasa = min(1.2, max(floors.get("rasa", 0.85), tone["rasa"] + 0.04))
    kappa_r = min(1.5, max(kappa, floors.get("kappa_r", 0.95)))
    amanah = max(
        floors.get("amanah", 0.9),
        min(1.2, 0.94 + 0.05 * truth + 0.05 * rasa),
    )

    return Metrics(
        truth=truth,
        peace2=peace2,
        kappa_r=kappa_r,
        deltaS=delta_s,
        rasa=rasa,
        amanah=amanah,
    )


def as_dict(metrics: Metrics) -> dict:
    """Expose metrics as a JSON-serialisable mapping for ledger writes."""

    return asdict(metrics)


__all__ = ["evaluate_metrics", "as_dict"]
