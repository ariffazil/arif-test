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
from packages.arif_agi.planner import plan_and_reason
from packages.apex_prime.judge import seal_if_lawful
from packages.compass_888.compass import route
from packages.eee_777.eee import limiter, sabar_orchestrate


def _bootstrap(
    task: str, initial_draft: Optional[str]
) -> tuple[str, Metrics, Dict[str, Any], Optional[AGIResponse]]:
    """Return the starting draft, metrics, plan, and AGI response context."""

    if not initial_draft:
        agi_outcome = respond(task)
        return agi_outcome.draft, agi_outcome.metrics, agi_outcome.plan, agi_outcome

    plan = plan_and_reason(task)
    metrics = evaluate_metrics(task, initial_draft)
    return initial_draft, metrics, plan, None


def runloop(task: str, *, initial_draft: Optional[str] = None) -> Dict[str, Any]:
    """Execute the Mind→Compass→Heart→Soul→EEE flow."""

    floors = get_floors()
    draft, metrics, plan_data, agi_context = _bootstrap(task, initial_draft)

    if initial_draft:
        if (
            metrics.truth < floors.get("truth", 0.99)
            or metrics.deltaS < floors.get("deltaS", 0.0)
        ):
            raise SABARPause(
                "Initial draft breaches core truth/ΔS floors; invoking refusal-first."
            )

    chosen = route(task, draft, metrics)
    if chosen == "arif-agi":
        if agi_context is None:
            agi_context = respond(task)
            draft = agi_context.draft
            metrics = agi_context.metrics
            plan_data = agi_context.plan
        else:
            draft = agi_context.draft
            metrics = agi_context.metrics
            plan_data = agi_context.plan
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
            "plan": plan_data,
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
        "plan": plan_data,
    }


__all__ = ["runloop"]
