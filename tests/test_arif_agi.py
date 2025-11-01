import json

import pytest

from packages.arif_agi.agent import AGIResponse, respond
from packages.arif_agi.metrics import evaluate_metrics
from packages.arif_agi.planner import plan_and_reason
from platform.psi.psi_score import Metrics, SABARPause, get_floors


def test_plan_and_reason_structure():
    plan = plan_and_reason("Guide a friend kindly")
    assert plan["task"].startswith("Guide")
    assert len(plan["steps"]) >= 2
    assert all({"phase", "intent", "focus"} <= step.keys() for step in plan["steps"])
    assert len(plan["plan_id"]) == 16


def test_evaluate_metrics_returns_metrics():
    draft = (
        "Task: Support. We respond with calm respect and clarity. We offer steps and"
        " cooperation."
    )
    metrics = evaluate_metrics("Support a peer", draft)
    assert isinstance(metrics, Metrics)
    floors = get_floors()
    assert metrics.truth >= 0.9 * floors["truth"]
    assert metrics.peace2 >= floors["peace2"]
    assert metrics.kappa_r >= 0.9 * floors["kappa_r"]


def test_respond_seals_and_logs(monkeypatch, tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("ARIFOS_LEDGER_PATH", str(ledger_path))
    outcome = respond("Offer grounded guidance")
    assert isinstance(outcome, AGIResponse)
    assert "Task:" in outcome.draft
    assert outcome.seal_id
    assert outcome.plan_id == outcome.plan["plan_id"]
    entries = ledger_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(entries) == 1
    record = json.loads(entries[0])
    assert record["agent"] == "arif-agi"
    assert record["metadata"]["plan_id"] == outcome.plan_id
    assert record["metadata"]["seeded"] is False
    assert record["idempotency_key"].startswith("arif-agi:")
    assert pytest.approx(record["metrics"]["psi"], rel=1e-6) == outcome.psi


def test_respond_raises_when_metrics_fail(monkeypatch, tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("ARIFOS_LEDGER_PATH", str(ledger_path))

    from packages import arif_agi as arif_agi_pkg
    import packages.arif_agi.metrics as metrics_module

    floors = get_floors()

    def _bad_metrics(task: str, draft: str) -> Metrics:
        return Metrics(
            truth=floors["truth"] - 0.2,
            peace2=floors["peace2"],
            kappa_r=floors["kappa_r"],
            deltaS=floors["deltaS"],
            rasa=floors["rasa"],
            amanah=floors["amanah"],
        )

    monkeypatch.setattr(metrics_module, "evaluate_metrics", _bad_metrics)

    with pytest.raises(SABARPause):
        arif_agi_pkg.respond("Plan harm")

    assert not ledger_path.exists()
