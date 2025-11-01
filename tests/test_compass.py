from packages.compass_888.compass import noise_score, route
from platform.psi.psi_score import Metrics, get_floors


def test_route_low_truth_goes_to_agi():
    floors = get_floors()
    metrics = Metrics(truth=floors["truth"] - 0.05, peace2=1.1, kappa_r=1.0, deltaS=0.1, rasa=0.9, amanah=0.95)
    decision = route("Explain the concept", "Draft is calm and clear", metrics)
    assert decision == "arif-agi"


def test_route_low_peace_goes_to_asi():
    floors = get_floors()
    metrics = Metrics(truth=1.0, peace2=0.7, kappa_r=0.96, deltaS=0.1, rasa=0.9, amanah=0.95)
    decision = route("Assist kindly", "This draft feels harsh and angry", metrics)
    assert decision == "arif-asi"


def test_route_good_metrics_go_to_apex_prime():
    metrics = Metrics(truth=1.0, peace2=1.12, kappa_r=1.1, deltaS=1.3, rasa=0.95, amanah=1.02)
    decision = route("Assist kindly", "We assist kindly with care and respect", metrics)
    assert decision == "apex-prime"


def test_noise_score_flags_aggressive_text():
    noisy = noise_score("This is angry!! and harsh!!")
    assert 0.0 <= noisy <= 1.0
    assert noisy > 0.5
