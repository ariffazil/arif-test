import json
from pathlib import Path

import pytest

from packages.apex_prime.judge import judge, seal_if_lawful
from platform.psi.psi_score import Metrics, SABARPause, get_floors


def test_judge_allows_metrics_above_floors():
    metrics = Metrics(truth=0.995, peace2=1.08, kappa_r=1.02, deltaS=1.2, rasa=0.95, amanah=1.0)
    decision = judge(metrics)
    assert decision["allowed"] is True
    assert "Ψ=" in decision["reason"]


def test_judge_blocks_floor_failure():
    metrics = Metrics(truth=0.90, peace2=0.8, kappa_r=0.5, deltaS=-0.1, rasa=0.5, amanah=0.5)
    decision = judge(metrics)
    assert decision["allowed"] is False


def test_seal_if_lawful_writes_entry(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("ARIFOS_LEDGER_PATH", str(ledger_path))
    metrics = Metrics(truth=0.995, peace2=1.06, kappa_r=1.01, deltaS=1.2, rasa=0.95, amanah=1.0)

    seal_id = seal_if_lawful("apex-prime", metrics, note="unit-test")
    assert isinstance(seal_id, str) and len(seal_id) > 8

    content = ledger_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(content) == 1
    record = json.loads(content[0])
    assert record["agent"] == "apex-prime"
    assert record["metrics"]["psi"] >= get_floors().get("psi_min", 0.95)


def test_seal_if_lawful_raises_on_failure(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("ARIFOS_LEDGER_PATH", str(ledger_path))
    metrics = Metrics(truth=0.90, peace2=0.8, kappa_r=0.5, deltaS=-0.1, rasa=0.5, amanah=0.5)

    with pytest.raises(SABARPause):
        seal_if_lawful("apex-prime", metrics)
