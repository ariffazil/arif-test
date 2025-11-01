from datetime import datetime, timezone

import pytest

from dataclasses import asdict

from packages.eee_777.eee import limiter, phoenix_schedule, sabar_orchestrate
from platform.psi.psi_score import Metrics, SABARPause, get_floors


def good_metrics() -> Metrics:
    return Metrics(truth=0.995, peace2=1.08, kappa_r=1.02, deltaS=1.2, rasa=0.95, amanah=1.0)


def test_limiter_allows_stable_metrics(tmp_path, monkeypatch):
    monkeypatch.setenv("ARIFOS_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
    decision = limiter("integration", {**asdict(good_metrics()), "psi": 1.05})
    assert decision == "allow"


def test_limiter_delays_near_threshold(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("ARIFOS_LEDGER_PATH", str(ledger_path))
    ledger_path.write_text("", encoding="utf-8")
    decision = limiter("integration", {**asdict(good_metrics()), "psi": 0.96})
    assert decision == "delay"


def test_sabar_orchestrate_cools_text(tmp_path, monkeypatch):
    monkeypatch.setenv("ARIFOS_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
    metrics = good_metrics()
    harsh = "This plan feels angry and harsh."
    cooled = sabar_orchestrate(harsh, metrics)
    assert cooled["modified"] is True
    assert cooled["tone"]["peace2_hint"] >= get_floors()["peace2"]


def test_sabar_orchestrate_raises_on_low_truth():
    metrics = Metrics(truth=0.90, peace2=1.1, kappa_r=0.96, deltaS=0.1, rasa=0.9, amanah=0.95)
    with pytest.raises(SABARPause):
        sabar_orchestrate("Calm text", metrics)


def test_phoenix_schedule_72_hours():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    result = phoenix_schedule(start)
    expected = datetime(2024, 1, 4, tzinfo=timezone.utc).isoformat()
    assert result == expected
