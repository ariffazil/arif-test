import math

from packages.arif_asi.asi import assess_tone, compute_conductance, tune
from platform.psi.psi_score import get_floors


def test_compute_conductance_aligned_text():
    task = "Provide supportive guidance"  # rich in positive cues
    draft = "We provide supportive guidance with care and respect."
    kappa = compute_conductance(task, draft)
    assert 0.0 <= kappa <= 1.5
    assert kappa >= get_floors()["kappa_r"]


def test_assess_tone_compassionate_text():
    tone = assess_tone("We respond with calm care, empathy, and respect for all.")
    assert tone["rasa"] >= get_floors()["rasa"]
    assert tone["peace2_hint"] >= 1.0


def test_tune_increases_peace_without_breaking_truth():
    raw = "Truth: The situation is tense and angry."
    baseline = assess_tone(raw)
    assert baseline["peace2_hint"] < 1.0

    tuned = tune(raw, target_peace2=1.05)
    assert tuned["peace2_hint"] >= 1.0
    assert "Truth:" in tuned["text"]
    assert tuned["peace2_hint"] >= baseline["peace2_hint"]
