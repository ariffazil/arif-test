# ArifOS Codex Summary

ArifOS Codex coordinates specialised agents through PR-first workflows. Each task is defined as a Codex taskfile with explicit
deliverables and acceptance criteria. The system enforces TEARFRAME floors and SABAR pause semantics while collecting telemetry in
the Cooling Ledger.

## Key Principles

1. **PR-First Execution**: Every material change is expressed as a Codex task that creates a pull request with tests,
   documentation, and metric disclosures.
2. **Floors Enforcement**: Metrics must respect thresholds from `docs/floors.yaml`. Sub-Ψ performance triggers a `SABARPause` and
   blocks deployment.
3. **Cooling Ledger**: All agent actions are logged with hashes, timestamps, and zkPC receipts to guarantee integrity.
4. **Tri-Witness Governance**: Human, AI, and Earth witnesses must reach quorum via `check_quorum()` before sealing changes.
5. **Core-5 Workstreams**: Dedicated taskfiles orchestrate AGI planning, empathy enforcement, Amanah adjudication, routing, and
   equilibrium.
6. **CI Discipline**: Pull requests must satisfy the Cooling Ledger checklist, run pytest, and maintain ≥85% coverage.

Consult `docs/protocols.yaml` for TEARFRAME, SABAR, and Phoenix-72 process references. For architectural context review
`docs/architecture.md`, and use `docs/runbook.md` plus `docs/amanah_eula.md` when operating the platform.
