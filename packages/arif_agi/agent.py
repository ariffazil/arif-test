"""AGI response orchestration for ArifOS."""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping

from platform.cooling_ledger.sdk import seal, write_entry
from platform.psi.psi_score import Metrics, SABARPause, get_floors, psi_from

from .metrics import evaluate_metrics
from .planner import plan_and_reason


@dataclass(frozen=True)
class AGIResponse:
    """Structured outcome returned by :func:`respond`."""

    task: str
    plan_id: str
    plan: Dict[str, Any]
    draft: str
    metrics: Metrics
    psi: float
    seal_id: str
    ledger_hash: str


def _draft_from_plan(task: str, plan: Mapping[str, Any]) -> str:
    lines = [
        f"Task: {task}.",
        "We approach with clarity, respect, and cooperative intent.",
        "Plan:",
    ]
    for index, step in enumerate(plan["steps"], 1):
        lines.append(
            f"{index}. {step['phase']} — {step['intent']} ({step['focus']})"
        )
    lines.append(
        "We provide compassionate, calm care and respectful cooperation aligned with the request."
    )
    lines.append(f"Reflection: {plan['reflection']}")
    lines.append("We conclude with transparent actions and shared follow-ups.")
    return " ".join(lines)


def _hash_text(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def respond(task: str) -> AGIResponse:
    """Return a governance-aware response outcome and persist Cooling Ledger traces."""

    plan = plan_and_reason(task)
    plan_id = plan["plan_id"]
    draft = _draft_from_plan(task, plan)
    metrics = evaluate_metrics(task, draft)
    floors = get_floors()
    psi = psi_from(metrics, floors)

    if psi < floors.get("tri_witness", 0.95):  # sanity safeguard
        raise SABARPause("Ψ below governance floor during AGI drafting.")

    entry = {**asdict(metrics), "psi": psi}
    metadata = {
        "plan_id": plan_id,
        "seeded": False,
        "draft_hash": _hash_text(draft),
        "route_history": ["arif-agi"],
    }
    idempotency_key = f"arif-agi:{plan_id}:{metadata['draft_hash']}"
    content_hash = write_entry(
        "arif-agi",
        entry,
        note=f"task={task}",
        idempotency_key=idempotency_key,
        metadata=metadata,
    )
    seal_id = seal(content_hash)
    return AGIResponse(
        task=task,
        plan_id=plan_id,
        plan=plan,
        draft=draft,
        metrics=metrics,
        psi=psi,
        seal_id=seal_id,
        ledger_hash=content_hash,
    )


__all__ = ["AGIResponse", "respond"]
