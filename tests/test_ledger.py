import json

import pytest

from platform.cooling_ledger.sdk import seal, write_entry


def test_write_entry_creates_append_only_jsonl(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("ARIFOS_LEDGER_PATH", str(ledger_path))

    metrics = {
        "truth": 0.995,
        "peace2": 1.02,
        "kappa_r": 0.97,
        "deltaS": 0.12,
        "rasa": 0.90,
        "amanah": 0.95,
        "Ψ": 1.01,
    }

    first_hash = write_entry("arif-agi", metrics, note="first")
    second_hash = write_entry("arif-agi", metrics, note="second")
    assert first_hash != second_hash

    with ledger_path.open("r", encoding="utf-8") as handle:
        lines = handle.readlines()

    assert len(lines) == 2
    agents = {json.loads(line)["agent"] for line in lines}
    assert agents == {"arif-agi"}


def test_write_entry_respects_idempotency(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("ARIFOS_LEDGER_PATH", str(ledger_path))

    metrics = {"truth": 1.0, "peace2": 1.0, "kappa_r": 1.0, "deltaS": 0.1, "rasa": 0.9, "amanah": 0.95}
    key = "agent:plan:hash"

    first_hash = write_entry(
        "integration",
        metrics,
        note="seed",
        idempotency_key=key,
        metadata={"plan_id": "abc123", "seeded": True, "contact": "care@example.com"},
    )
    second_hash = write_entry(
        "integration",
        metrics,
        note="seed",
        idempotency_key=key,
        metadata={"plan_id": "abc123", "seeded": True},
    )
    assert first_hash == second_hash

    with ledger_path.open("r", encoding="utf-8") as handle:
        lines = handle.readlines()

    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["idempotency_key"] == key
    assert record["metadata"]["plan_id"] == "abc123"
    assert record["metadata"]["contact"] == "[redacted-email]"


def test_write_entry_redacts_sensitive_tokens(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("ARIFOS_LEDGER_PATH", str(ledger_path))

    note = "Reach me at heal@care.org and call 123456789012"
    metrics = {"truth": 1.0, "peace2": 1.1, "kappa_r": 1.0, "deltaS": 0.1, "rasa": 0.95, "amanah": 0.96}

    write_entry(
        "arif-asi",
        metrics,
        note=note,
        metadata={"plan_id": "plan-1", "notes": ["Email heal@care.org", "id 987654321"]},
    )

    record = json.loads(ledger_path.read_text(encoding="utf-8").strip())
    assert "[redacted-email]" in record["note"]
    assert "[redacted-number]" in record["note"]
    assert record["metadata"]["notes"][0] == "Email [redacted-email]"
    assert record["metadata"]["notes"][1] == "id [redacted-number]"


def test_write_entry_rejects_replay_by_plan_id(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("ARIFOS_LEDGER_PATH", str(ledger_path))

    metrics = {"truth": 1.0, "peace2": 1.1, "kappa_r": 1.0, "deltaS": 0.1, "rasa": 0.95, "amanah": 0.96}
    write_entry("integration", metrics, metadata={"plan_id": "plan-dup"})

    with pytest.raises(ValueError):
        write_entry("integration", metrics, metadata={"plan_id": "plan-dup"})


def test_seal_returns_base58_identifier():
    seal_id_one = seal("abc123")
    seal_id_two = seal("abc123")
    assert isinstance(seal_id_one, str)
    assert len(seal_id_one) >= 10
    assert seal_id_one != seal_id_two
