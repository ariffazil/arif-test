"""Structured planning heuristics for the Arif-AGI agent."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Dict, List


@dataclass(frozen=True)
class PlanStep:
    """Single step in the AGI plan."""

    phase: str
    intent: str
    focus: str


@dataclass(frozen=True)
class Plan:
    """Collection of planning steps plus reflective notes."""

    task: str
    steps: List[PlanStep]
    reflection: str

    def as_dict(self) -> Dict[str, object]:
        return {
            "task": self.task,
            "steps": [asdict(step) for step in self.steps],
            "reflection": self.reflection,
        }


def _plan_id_from_dict(payload: Dict[str, object]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def plan_and_reason(task: str) -> Dict[str, object]:
    """Return a structured plan covering Sense→Express with ≥2 steps."""

    normalized = task.strip() or "Unnamed task"
    steps = [
        PlanStep(
            phase="Sense",
            intent=f"Clarify the request: {normalized}.",
            focus="Gather context and constraints without judgement.",
        ),
        PlanStep(
            phase="Reflect",
            intent="Highlight user goals and emotional cues.",
            focus="Note any safety, empathy, or factual guardrails.",
        ),
        PlanStep(
            phase="Integrate",
            intent="Form a compassionate, truthful response outline.",
            focus="Sequence ideas from acknowledgement → guidance → invitation.",
        ),
        PlanStep(
            phase="Express",
            intent="Deliver the response with transparency and cooperation.",
            focus="Offer next steps and encourage co-creation.",
        ),
    ]
    reflection = (
        "Ensure ΔS stays positive, speak with calm clarity, and invite respectful"
        " collaboration while documenting outcomes in the Cooling Ledger."
    )
    plan = Plan(task=normalized, steps=steps, reflection=reflection)
    plan_dict = plan.as_dict()
    plan_dict["plan_id"] = _plan_id_from_dict(plan_dict)
    return plan_dict


__all__ = ["plan_and_reason", "Plan", "PlanStep"]
