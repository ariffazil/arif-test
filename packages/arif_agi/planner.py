"""Structured planning heuristics for the Arif-AGI agent."""
from __future__ import annotations

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
    return plan.as_dict()


__all__ = ["plan_and_reason", "Plan", "PlanStep"]
