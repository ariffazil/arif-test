"""AGI response orchestration for ArifOS."""
from __future__ import annotations

from dataclasses import asdict

from platform.cooling_ledger.sdk import seal, write_entry
from platform.psi.psi_score import get_floors, psi_from

from .metrics import evaluate_metrics
from .planner import plan_and_reason


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
    lines.append(f"Reflection: {plan['reflection']}")
    lines.append("We conclude with transparent actions and shared follow-ups.")
    return " ".join(lines)


def respond(task: str) -> str:
    """Return a governance-aware response draft and persist Cooling Ledger traces."""

    plan = plan_and_reason(task)
    draft = _draft_from_plan(task, plan)
    metrics = evaluate_metrics(task, draft)
    floors = get_floors()
    psi = psi_from(metrics, floors)

    entry = {**asdict(metrics), "psi": psi}
    content_hash = write_entry("arif-agi", entry, note=f"task={task}")
    seal(content_hash)
    return draft


__all__ = ["respond"]
