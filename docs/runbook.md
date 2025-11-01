# ArifOS Core-5 Runbook

This runbook captures the day-to-day operations required to keep ArifOS Codex healthy. All commands assume you are at the root of
the repository.

Consult [`docs/status.md`](status.md) for current completion metrics and system health before beginning a new operations cycle.

## 1. Prepare the environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

To use a custom ledger location for local experiments, set `ARIFOS_LEDGER_PATH` to a writable path.

## 2. Execute the Core-5 runloop

```python
from packages.integration.runloop import runloop
result = runloop("Offer supportive guidance to the team")
```

Inspect the result payload:

- `status`: `sealed` or `delay`
- `plan`: structured reasoning map with `plan_id`
- `psi`: equilibrium score produced by `psi_from`
- `route_history`: ordered list of compass decisions and module visits
- `seeded`: whether the run used an externally provided draft

If `status == "delay"`, wait for cooling feedback from EEE-777, adjust the draft, and call `runloop` again with the improved
text.

## 3. Cooling Ledger hygiene

Ledger entries are stored in JSON Lines format. Use the helper below to inspect recent events without exposing redacted content:

```python
import json
from pathlib import Path

ledger_path = Path("platform/cooling_ledger/ledger.jsonl")
for line in ledger_path.read_text(encoding="utf-8").splitlines()[-5:]:
    record = json.loads(line)
    print(record["ts"], record["agent"], record["metrics"]["psi"], record["metadata"].get("plan_id"))
```

If a replay error occurs, verify that the incoming request reuses an existing `plan_id`/hash pair. Differentiate new attempts by
adjusting the draft text or by clearing the idempotency key when appropriate.

### Ledger invariants checklist

- **Sanitisation** – All notes and metadata are redacted for emails and long numeric strings before writes. Review suspicious
  fields in-memory rather than persisting raw inputs.
- **Idempotency provenance** – Keys are derived from `plan_id`, `route_history`, and any seed hashes. When altering inputs,
  update at least one of these components to avoid false-positive rejections.
- **Replay guard** – The ledger rejects duplicates that reuse the same `(plan_id, hash)` pair. Investigate unexpected
  rejections to confirm whether a previous seal already covers the plan.

## 4. Manual Phoenix-72 audit

Until the scheduled job is automated, run a manual audit to summarise the last 72 hours:

```python
from datetime import datetime, timedelta, timezone

cutoff = datetime.now(timezone.utc) - timedelta(hours=72)
entries = []
for record in ledger_path.read_text(encoding="utf-8").splitlines():
    payload = json.loads(record)
    if datetime.fromisoformat(payload["ts"]) >= cutoff:
        entries.append(payload)

print("Records in window", len(entries))
print("Min Ψ", min(entry["metrics"]["psi"] for entry in entries))
print("Max Ψ", max(entry["metrics"]["psi"] for entry in entries))
```

Flag any run whose Ψ dips below the governance floor and schedule additional ASI cooling for that agent.

## 5. Running tests

Execute the full suite before publishing artefacts:

```bash
pytest -q
```

All tests should pass. Two integration tests may skip if the limiter does not trigger a delay; the skip is expected and does not
indicate failure.

## 6. Troubleshooting checklist

| Symptom | Action |
| --- | --- |
| `SABARPause` raised immediately | Confirm initial draft meets Truth ≥ 0.99 and ΔS ≥ 0.0. |
| Ledger replay error | Ensure the plan text changed or the runloop generated a fresh `plan_id`. |
| Compass loops back to Mind repeatedly | Review plan steps – add clarity to the initial task or provide calming context. |
| Delay status persists | Allow more time between attempts and rely on ASI `tune()` to soften tone before retrying. |

## 7. Preparing federation agents

When adding @WELL, @RIF, @WEALTH, @PROMPT, or @GEOX adapters:

1. Import `runloop` and forward the incoming task description.
2. Attach agent-specific metadata to the ledger by extending the `metadata` payload.
3. Honour the returned `status`; refuse or delay external responses when a SABAR pause is in effect.

## 8. Documenting decisions

Record significant governance decisions in `docs/amanah_eula.md` under an appendix entry. Reference the relevant plan identifier
and Cooling Ledger hash for traceability.
