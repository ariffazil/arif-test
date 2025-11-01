import pytest

from platform.psi.psi_score import Metrics, SABARPause, get_floors, meets_floors, psi_from


def test_psi_happy_path():
    metrics = Metrics(
        truth=0.995,
        peace2=1.02,
        kappa_r=0.97,
        deltaS=1.20,
        rasa=0.90,
        amanah=0.95,
    )
    psi = psi_from(metrics)
    assert 0.95 <= psi <= 2.0


def test_meets_floors_respects_known_metrics():
    metrics = Metrics(
        truth=1.0,
        peace2=1.1,
        kappa_r=0.98,
        deltaS=0.4,
        rasa=0.92,
        amanah=0.96,
    )
    floors = get_floors()
    assert "tri_witness" in floors
    assert meets_floors(metrics, floors)


def test_floor_breach_triggers_pause():
    metrics = Metrics(
        truth=0.90,
        peace2=1.02,
        kappa_r=0.97,
        deltaS=0.30,
        rasa=0.92,
        amanah=0.95,
    )
    with pytest.raises(SABARPause):
        psi_from(metrics)


def test_low_psi_triggers_pause_even_when_floors_met():
    floors = get_floors()
    metrics = Metrics(
        truth=floors["truth"],
        peace2=floors["peace2"],
        kappa_r=floors["kappa_r"],
        deltaS=0.01,
        rasa=floors["rasa"],
        amanah=floors["amanah"],
    )
    assert meets_floors(metrics, floors)
    with pytest.raises(SABARPause):
        psi_from(metrics, floors)
