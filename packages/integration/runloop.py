"""End-to-end orchestration for the Core-5 agents."""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

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


@dataclass(frozen=True)
class RunloopResult:
    """Schema guard for integration outcomes."""

    status: str
    draft: str
    route: str
    psi: float
    metrics: Metrics
    seal_id: Optional[str]
    plan: Dict[str, Any]
    plan_id: str
    seeded: bool
    seed_hash: Optional[str]
    route_history: List[str]

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        if self.status not in {"sealed", "delay"}:
            raise ValueError(f"Unexpected status: {self.status}")
        if not isinstance(self.route_history, list):
            raise ValueError("route_history must be list")
        if self.status == "sealed" and not self.seal_id:
            raise ValueError("sealed results require a seal id")
        if self.status == "delay" and self.seal_id is not None:
            raise ValueError("delay results must not include a seal id")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "draft": self.draft,
            "route": self.route,
            "psi": self.psi,
            "metrics": self.metrics,
            "seal_id": self.seal_id,
            "plan": self.plan,
            "plan_id": self.plan_id,
            "seeded": self.seeded,
            "seed_hash": self.seed_hash,
            "route_history": list(self.route_history),
        }


def _hash_text(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _bootstrap(
    task: str,
    initial_draft: Optional[str],
) -> tuple[str, Metrics, Dict[str, Any], Optional[AGIResponse], bool, Optional[str], List[str]]:
    """Return the starting draft, metrics, plan, AGI context, and provenance."""

    if not initial_draft:
        agi_outcome = respond(task)
        return (
            agi_outcome.draft,
            agi_outcome.metrics,
            agi_outcome.plan,
            agi_outcome,
            False,
            None,
            ["arif-agi"],
        )

    plan = plan_and_reason(task)
    metrics = evaluate_metrics(task, initial_draft)
    return (
        initial_draft,
        metrics,
        plan,
        None,
        True,
        _hash_text(initial_draft),
        ["seeded"],
    )


def runloop(task: str, *, initial_draft: Optional[str] = None) -> Dict[str, Any]:
    """Execute the Mind→Compass→Heart→Soul→EEE flow."""

    floors = get_floors()
    (
        draft,
        metrics,
        plan_data,
        agi_context,
        seeded,
        seed_hash,
        route_history,
    ) = _bootstrap(task, initial_draft)

    plan_id = plan_data["plan_id"]

    if initial_draft:
        if (
            metrics.truth < floors.get("truth", 0.99)
            or metrics.deltaS < floors.get("deltaS", 0.0)
        ):
            raise SABARPause(
                "Initial draft breaches core truth/ΔS floors; invoking refusal-first."
            )

    chosen = route(task, draft, metrics)
    route_history.append(f"compass:{chosen}")
    if chosen == "arif-agi":
        agi_context = respond(task)
        draft = agi_context.draft
        metrics = agi_context.metrics
        plan_data = agi_context.plan
        plan_id = agi_context.plan_id
        route_history.append("arif-agi")
        chosen = route(task, draft, metrics)
        route_history.append(f"compass:{chosen}")

    if chosen == "arif-asi":
        cooling = sabar_orchestrate(draft, metrics)
        draft = cooling["draft"]
        metrics = evaluate_metrics(task, draft)
        route_history.append("arif-asi")
        chosen = "apex-prime"
        route_history.append(f"compass:{chosen}")

    psi = psi_from(metrics, floors)
    limit_decision = limiter("integration", {**asdict(metrics), "psi": psi})
    if limit_decision == "delay":
        result = RunloopResult(
            status="delay",
            draft=draft,
            route=chosen,
            psi=psi,
            metrics=metrics,
            seal_id=None,
            plan=plan_data,
            plan_id=plan_id,
            seeded=seeded,
            seed_hash=seed_hash,
            route_history=route_history,
        )
        return result.to_dict()
    if limit_decision == "block":
        raise SABARPause("EEE limiter blocked the run due to repeated near-threshold Ψ.")

    draft_hash = _hash_text(draft)
    metadata = {
        "plan_id": plan_id,
        "seeded": seeded,
        "seed_hash": seed_hash,
        "route_history": route_history + ["integration"],
    }
    idempotency_key = f"integration:{plan_id}:{draft_hash}:{chosen}"
    seal_id = seal_if_lawful(
        "integration",
        metrics,
        note=task,
        plan_id=plan_id,
        idempotency_key=idempotency_key,
        metadata=metadata,
    )
    result = RunloopResult(
        status="sealed",
        draft=draft,
        route=chosen,
        psi=psi,
        metrics=metrics,
        seal_id=seal_id,
        plan=plan_data,
        plan_id=plan_id,
        seeded=seeded,
        seed_hash=seed_hash,
        route_history=metadata["route_history"],
    )
    return result.to_dict()


__all__ = ["runloop", "RunloopResult"]
