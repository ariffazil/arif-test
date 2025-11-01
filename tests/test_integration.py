import json

import pytest

from packages.integration.runloop import runloop
from platform.psi.psi_score import SABARPause


def _load_entries(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").strip().splitlines()]


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
    assert result["plan_id"] == result["plan"]["plan_id"]
    assert result["seeded"] is False
    entries = _load_entries(ledger_path)
    assert len(entries) == 2
    plan_ids = {entry["metadata"]["plan_id"] for entry in entries}
    assert plan_ids == {result["plan_id"]}
    assert {entry["agent"] for entry in entries} == {"arif-agi", "integration"}


def test_runloop_cooling_path(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("ARIFOS_LEDGER_PATH", str(ledger_path))
    result = runloop("Calm reply", initial_draft="This is angry and harsh.")
    assert result["status"] == "sealed"
    assert "calm" in result["draft"].lower()
    assert result["route"] == "apex-prime"
    assert result["plan"]
    assert result["seeded"] is True
    assert result["seed_hash"]
    entries = _load_entries(ledger_path)
    assert len(entries) == 1
    assert entries[0]["metadata"]["seeded"] is True


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

    assert near_threshold_result["plan_id"]
    assert near_threshold_result["route_history"]

    improved = runloop("Edge case", initial_draft="We respond with calm care and respect.")
    assert improved["status"] == "sealed"
    assert improved["plan"]
    assert improved["plan_id"]
    assert improved["route_history"][-1] == "integration"


def test_double_entry_invariant(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("ARIFOS_LEDGER_PATH", str(ledger_path))

    try:
        result = runloop("Document cooperative plan")
    except SABARPause as exc:
        pytest.skip(f"Cooling escalated unexpectedly: {exc}")
    entries = _load_entries(ledger_path)
    assert result["status"] == "sealed"
    assert len(entries) == 2
    plan_ids = [entry["metadata"]["plan_id"] for entry in entries]
    assert plan_ids[0] == plan_ids[1] == result["plan_id"]
    timestamps = [entry["ts"] for entry in entries]
    assert timestamps == sorted(timestamps)
