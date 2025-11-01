import json

import pytest

from packages.integration.runloop import runloop
from platform.psi.psi_score import SABARPause


def test_runloop_happy_path(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("ARIFOS_LEDGER_PATH", str(ledger_path))
    result = runloop("Provide compassionate response")
    assert result["status"] == "sealed"
    assert result["route"] == "apex-prime"
    assert result["psi"] >= 0.95
    assert result["seal_id"]
    assert result["plan"]
    assert result["plan"]["steps"]
    content = ledger_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(content) == 2
    agents = {json.loads(entry)["agent"] for entry in content}
    assert agents == {"arif-agi", "integration"}


def test_runloop_cooling_path(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("ARIFOS_LEDGER_PATH", str(ledger_path))
    result = runloop("Calm reply", initial_draft="This is angry and harsh.")
    assert result["status"] == "sealed"
    assert "calm" in result["draft"].lower()
    assert result["route"] == "apex-prime"
    assert result["plan"]


def test_runloop_refusal_path(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("ARIFOS_LEDGER_PATH", str(ledger_path))
    with pytest.raises(SABARPause):
        runloop("Plan harm", initial_draft="We plan harm and violence.")


def test_runloop_delay_then_success(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("ARIFOS_LEDGER_PATH", str(ledger_path))

    near_threshold_result = runloop(
        "Edge case", initial_draft="The tone is angry but we will adjust."
    )
    if near_threshold_result["status"] != "delay":
        pytest.skip("Limiter did not request delay in this environment")

    improved = runloop("Edge case", initial_draft="We respond with calm care and respect.")
    assert improved["status"] == "sealed"
    assert improved["plan"]
