"""AGI response orchestration for ArifOS."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Any

from platform.cooling_ledger.sdk import seal, write_entry
from platform.psi.psi_score import Metrics, get_floors, psi_from

from .metrics import evaluate_metrics
from .planner import plan_and_reason


@dataclass(frozen=True)
class AGIResponse:
    """Structured outcome returned by :func:`respond`."""

    task: str
    plan: Dict[str, Any]
    draft: str
    metrics: Metrics
    psi: float
    seal_id: str


def _draft_from_plan(task: str, plan: dict) -> str:
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


def respond(task: str) -> AGIResponse:
    """Return a governance-aware response outcome and persist Cooling Ledger traces."""

    plan = plan_and_reason(task)
    draft = _draft_from_plan(task, plan)
    metrics = evaluate_metrics(task, draft)
    floors = get_floors()
    psi = psi_from(metrics, floors)

    entry = {**asdict(metrics), "psi": psi}
    content_hash = write_entry("arif-agi", entry, note=f"task={task}")
    seal_id = seal(content_hash)
    return AGIResponse(
        task=task,
        plan=plan,
        draft=draft,
        metrics=metrics,
        psi=psi,
        seal_id=seal_id,
    )


__all__ = ["AGIResponse", "respond"]
