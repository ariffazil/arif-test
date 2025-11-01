"""End-to-end orchestration for the Core-5 agents."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Optional

from platform.psi.psi_score import (
    Metrics,
    SABARPause,
    get_floors,
    psi_from,
)
from packages.arif_agi.agent import AGIResponse, respond
from packages.arif_agi.metrics import evaluate_metrics
from packages.apex_prime.judge import seal_if_lawful
from packages.compass_888.compass import route
from packages.eee_777.eee import limiter, sabar_orchestrate


def _bootstrap(task: str, initial_draft: Optional[str]) -> tuple[str, Metrics, Optional[AGIResponse]]:
    """Return the starting draft, metrics, and AGI response context."""

    agi_outcome: Optional[AGIResponse] = respond(task)
    if initial_draft:
        draft = initial_draft
        metrics = evaluate_metrics(task, draft)
    else:
        draft = agi_outcome.draft
        metrics = agi_outcome.metrics
    return draft, metrics, agi_outcome


def runloop(task: str, *, initial_draft: Optional[str] = None) -> Dict[str, Any]:
    """Execute the Mind→Compass→Heart→Soul→EEE flow."""

    floors = get_floors()
    draft, metrics, agi_context = _bootstrap(task, initial_draft)

    if initial_draft:
        if (
            metrics.truth < floors.get("truth", 0.99)
            or metrics.deltaS < floors.get("deltaS", 0.0)
        ):
            raise SABARPause(
                "Initial draft breaches core truth/ΔS floors; invoking refusal-first."
            )

    chosen = route(task, draft, metrics)
    if chosen == "arif-agi" and agi_context is not None:
        draft = agi_context.draft
        metrics = agi_context.metrics
        chosen = route(task, draft, metrics)

    if chosen == "arif-asi":
        cooling = sabar_orchestrate(draft, metrics)
        draft = cooling["draft"]
        metrics = evaluate_metrics(task, draft)
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
            "plan": agi_context.plan if agi_context else None,
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
        "plan": agi_context.plan if agi_context else None,
    }


__all__ = ["runloop"]
