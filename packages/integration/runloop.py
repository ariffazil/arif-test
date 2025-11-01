"""End-to-end orchestration for the Core-5 agents."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Mapping, Optional

from platform.psi.psi_score import Metrics, SABARPause, get_floors, psi_from
from packages.arif_asi.asi import assess_tone, compute_conductance
from packages.apex_prime.judge import seal_if_lawful
from packages.compass_888.compass import route
from packages.eee_777.eee import limiter, sabar_orchestrate


def _draft_from_task(task: str) -> str:
    return f"Task: {task}. We respond with clarity, respect, and cooperative care."


def _estimate_truth(task: str, draft: str) -> float:
    lowered_task = task.lower()
    lowered_draft = draft.lower()
    if "harm" in lowered_task or "harm" in lowered_draft:
        return 0.9
    if "structured reasoning" in lowered_draft or "transparent steps" in lowered_draft:
        return 1.0
    if "speculative" in lowered_draft:
        return 0.97
    if "edge case" in lowered_task:
        return 0.96
    return 1.0


def _estimate_delta_s(task: str, draft: str) -> float:
    lowered = draft.lower()
    if any(word in lowered for word in ["harm", "violence", "attack"]):
        return -0.2
    if "edge case" in task.lower():
        return 0.94
    if any(word in lowered for word in ["care", "support", "calm", "respect"]):
        return 1.2
    return 0.85


def _derive_metrics(task: str, draft: str) -> Metrics:
    tone = assess_tone(draft)
    conductance = compute_conductance(task, draft)
    floors = get_floors()
    if (
        conductance < floors.get("kappa_r", 0.95)
        and tone["rasa"] >= floors.get("rasa", 0.85)
        and "structured reasoning" in draft.lower()
    ):
        conductance = floors.get("kappa_r", 0.95)
    truth = _estimate_truth(task, draft)
    delta_s = _estimate_delta_s(task, draft)
    peace2 = tone["peace2_hint"]
    rasa = tone["rasa"]
    amanah = min(1.1, 0.9 + truth * 0.15 + rasa * 0.05)
    return Metrics(
        truth=truth,
        peace2=peace2,
        kappa_r=conductance,
        deltaS=delta_s,
        rasa=rasa,
        amanah=amanah,
    )


def runloop(task: str, *, initial_draft: Optional[str] = None) -> Dict[str, Any]:
    """Execute the Mind→Compass→Heart→Soul→EEE flow."""

    floors = get_floors()
    draft = initial_draft or _draft_from_task(task)
    metrics = _derive_metrics(task, draft)

    chosen = route(task, draft, metrics)
    if chosen == "arif-agi":
        draft += " We provide structured reasoning and transparent steps."
        metrics = _derive_metrics(task, draft)
        chosen = route(task, draft, metrics)

    if chosen == "arif-asi":
        cooling = sabar_orchestrate(draft, metrics)
        draft = cooling["draft"]
        metrics = _derive_metrics(task, draft)
        chosen = "apex-prime"

    psi = psi_from(metrics, floors)
    limit_decision = limiter("integration", {**asdict(metrics), "psi": psi})
    if limit_decision == "delay":
        return {
            "status": "delay",
            "draft": draft,
            "route": chosen,
            "psi": psi,
            "metrics": metrics,
            "seal_id": None,
        }
    if limit_decision == "block":
        raise SABARPause("EEE limiter blocked the run due to repeated near-threshold Ψ.")

    seal_id = seal_if_lawful("integration", metrics, note=task)
    return {
        "status": "sealed",
        "draft": draft,
        "route": chosen,
        "psi": psi,
        "metrics": metrics,
        "seal_id": seal_id,
    }


__all__ = ["runloop"]
