"""Empathy and conductance heuristics for the Arif-ASI module."""
from __future__ import annotations

from typing import Dict, Iterable, List

import re

from platform.psi.psi_score import get_floors

_POSITIVE_WORDS: frozenset[str] = frozenset(
    {
        "calm",
        "care",
        "clarity",
        "compassionate",
        "cooperate",
        "empathy",
        "gentle",
        "honor",
        "kind",
        "peace",
        "respect",
        "support",
        "together",
        "trust",
        "understand",
    }
)
_NEGATIVE_WORDS: frozenset[str] = frozenset(
    {
        "angry",
        "attack",
        "break",
        "cruel",
        "fight",
        "harm",
        "hurt",
        "reject",
        "shout",
        "threat",
        "toxic",
        "violence",
    }
)

_TOKEN_PATTERN = re.compile(r"[a-zA-Z']+")


def _tokenize(text: str) -> List[str]:
    return [match.group(0).lower() for match in _TOKEN_PATTERN.finditer(text)]


def _marker_score(tokens: Iterable[str], marker: Iterable[str]) -> int:
    marker_set = set(marker)
    return sum(1 for token in tokens if token in marker_set)


def compute_conductance(text_a: str, text_b: str) -> float:
    """Approximate κᵣ using overlap of calming intents and penalties for aggression."""

    tokens_a = _tokenize(text_a)
    tokens_b = _tokenize(text_b)

    if not tokens_a or not tokens_b:
        return 0.8

    unique_a = set(tokens_a)
    unique_b = set(tokens_b)
    shared = unique_a & unique_b
    total = unique_a | unique_b
    overlap = len(shared) / len(total) if total else 0.0

    positive_alignment = (
        _marker_score(shared, _POSITIVE_WORDS) / max(len(shared) or 1, 1)
        if shared
        else 0.0
    )
    aggression_penalty = 0.35 * (
        _marker_score(tokens_a, _NEGATIVE_WORDS) + _marker_score(tokens_b, _NEGATIVE_WORDS)
    )
    kappa = 0.85 + overlap * 0.5 + positive_alignment * 0.6 - aggression_penalty
    return max(0.0, min(1.5, kappa))


def assess_tone(text: str) -> Dict[str, float]:
    """Return tone diagnostics used by ASI and other agents."""

    floors = get_floors()
    tokens = _tokenize(text)
    positive_hits = _marker_score(tokens, _POSITIVE_WORDS)
    negative_hits = _marker_score(tokens, _NEGATIVE_WORDS)
    length = max(len(tokens), 1)

    compassion_ratio = positive_hits / length
    tension_ratio = negative_hits / length

    rasa = max(0.0, min(1.2, 0.7 + compassion_ratio * 1.5 - tension_ratio * 0.6))
    peace2_hint = max(0.0, min(1.5, 0.95 + compassion_ratio * 1.1 - tension_ratio * 0.9))

    if not tokens:
        rasa = max(rasa, floors.get("rasa", 0.85) * 0.95)
        peace2_hint = max(peace2_hint, 0.95)

    return {
        "rasa": rasa,
        "peace2_hint": peace2_hint,
        "positive_hits": positive_hits,
        "negative_hits": negative_hits,
    }


def tune(text: str, target_peace2: float = 1.0) -> Dict[str, float | str | bool]:
    """Adjust the draft to reach the desired Peace² score without harming truth cues."""

    baseline = assess_tone(text)
    floors = get_floors()
    desired = max(target_peace2, floors.get("peace2", 1.0))

    if baseline["peace2_hint"] >= desired:
        return {**baseline, "text": text, "modified": False}

    softened = text
    for marker in _NEGATIVE_WORDS:
        softened = re.sub(rf"\b{marker}\b", "reflect", softened, flags=re.IGNORECASE)

    if "Truth:" in text and "Truth:" not in softened:
        softened = softened.replace("reflect", "Truth: reflect", 1)

    softened += " We respond with calm empathy and shared respect."
    improved = assess_tone(softened)

    if improved["peace2_hint"] < baseline["peace2_hint"]:
        # Do no harm: keep the original text when the heuristic fails.
        return {**baseline, "text": text, "modified": False}

    final_text = softened
    if improved["peace2_hint"] < desired:
        final_text += " Together, we breathe, listen, and adapt."
        improved = assess_tone(final_text)

    return {**improved, "text": final_text, "modified": final_text != text}


__all__ = ["assess_tone", "compute_conductance", "tune"]
