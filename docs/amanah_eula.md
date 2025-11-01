# Amanah Covenant & Usage Charter

This document records the ethical boundaries and governance expectations for operating ArifOS Codex. It complements the
TEARFRAME floors defined in `docs/floors.yaml` and the procedural protocols in `docs/protocols.yaml`.

## Core commitments

1. **Truthfulness (Amanah of Speech)** – Agents must not fabricate, distort, or omit material facts. Any suspected breach requires
   invoking a `SABARPause` and escalating to human review.
2. **Peaceful conduct (Sakinah)** – Outputs must avoid incitement, harassment, or aggressive tone. Use Heart/ASI tuning to restore
   Peace² ≥ 1.0 before sealing.
3. **Mutual flourishing (ΔS ≥ 0)** – Tasks should increase collective clarity and benefit. Requests that aim to harm or exploit are
   refused outright.
4. **Transparency & Traceability** – Every sealed response must carry a Cooling Ledger entry with a verifiable `plan_id`, hash, and
   seal receipt. No silent operations are permitted.
5. **Stewardship of data** – Sensitive tokens (emails, identifiers, private notes) are redacted before persistence and should never
   appear in public artefacts.

## Operator responsibilities

- Maintain the Cooling Ledger in append-only storage and protect it with regular backups.
- Review Phoenix-72 reports to ensure long-term compliance with floors and to identify drift.
- Respect `delay` recommendations from EEE-777; do not override limiter decisions for expediency.
- Document exceptions in the appendix below, noting the `plan_id`, ledger hash, and remedial action.

## Acceptable use

ArifOS Codex may be used for:

- Coaching, caregiving, and cooperative planning tasks.
- Governance automation where transparency and ethical guardrails are required.
- Research on reflective AI alignment methods under supervision.

The system must **not** be used for:

- Surveillance, profiling, or any violation of personal privacy.
- Generating instructions for harm, disinformation, or unlawful behaviour.
- Circumventing democratic, community, or organisational oversight.

## Incident response

1. Trigger `SABARPause` on detection of any floor violation, misinformation, or safety breach.
2. Record the incident in the Cooling Ledger with a dedicated note and metadata flag.
3. File an appendix entry with a root-cause summary and corrective steps.
4. Conduct a Phoenix-72 retrospective to ensure the fix holds across subsequent runs.

## Appendix – Recorded decisions

| Date (UTC) | Plan ID | Ledger Hash | Summary | Follow-up |
| --- | --- | --- | --- | --- |
| _TBD_ |  |  |  |  |

Update this table as new governance events occur.
