# ArifOS Codex

ArifOS Codex is a monorepo scaffold for orchestrating PR-first automation tasks across the Core-5 governance agents. It provides
metrics enforcement, double-entry ledgering, and end-to-end orchestration that other teams can reuse when bringing new agents
online.

## Repository layout

- `platform/`
  - `cooling_ledger/` – append-only JSONL storage with redaction, idempotency, and replay detection safeguards.
  - `psi/` – Ψ computation helpers and TEARFRAME floor loading.
  - `tri_witness/` – quorum utilities and checklist references.
- `packages/`
  - `arif_agi/` – planner, metrics, and structured `AGIResponse` wrapper (Mind).
  - `arif_asi/` – tone assessment and conductance tuning (Heart).
  - `apex_prime/` – refusal-first adjudication and sealing (Soul).
  - `compass_888/` – routing logic and noise filtering (Direction).
  - `eee_777/` – SABAR orchestration and limiter heuristics (Equilibrium).
  - `integration/` – governed runloop that binds the Core-5 and writes ledger entries with provenance metadata.
- `docs/` – governance floors, protocols, architecture notes, runbook, and Amanah covenant.
- `tests/` – pytest suite that exercises each module plus end-to-end flows.

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

Set `ARIFOS_LEDGER_PATH` to redirect ledger writes during local experiments.

## Key documents

- [`docs/summary.md`](docs/summary.md) – condensed operating principles.
- [`docs/architecture.md`](docs/architecture.md) – Core-5 component map, data flow, and extensibility seams.
- [`docs/runbook.md`](docs/runbook.md) – operational checklist for running the system day to day.
- [`docs/amanah_eula.md`](docs/amanah_eula.md) – usage covenant and incident response expectations.
- [`docs/floors.yaml`](docs/floors.yaml) – TEARFRAME thresholds consumed by the Psi engine.
- [`docs/protocols.yaml`](docs/protocols.yaml) – TEARFRAME, SABAR, and Phoenix-72 process references.

## Tooling

- `pyproject.toml` / `setup.cfg` define import paths and pytest defaults.
- `.github/workflows/ci.yml` (when present) runs pytest for pull requests.
- `.codex/tasks/*.yaml` (optional) describe Codex automation jobs and acceptance criteria.

## Next steps

Upcoming Phase 3 work will add federation adapters, telemetry dashboards, Phoenix-72 automation, and expanded documentation
appendices. See `docs/runbook.md` for interim manual procedures.
