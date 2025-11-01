"""Refusal-first firewall and sealing guard for ArifOS."""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Mapping, Optional

from platform.cooling_ledger.sdk import seal, write_entry
from platform.psi.psi_score import Metrics, SABARPause, get_floors, meets_floors, psi_from


def _normalize_metrics(metrics: Mapping[str, Any] | Metrics) -> Metrics:
    if isinstance(metrics, Metrics):
        return metrics
    if is_dataclass(metrics):  # pragma: no cover - defensive
        return Metrics(**asdict(metrics))
    return Metrics(**{key: float(value) for key, value in metrics.items() if key in Metrics.__annotations__})


def judge(metrics: Mapping[str, Any] | Metrics) -> Dict[str, Any]:
    """Return an allow/deny decision with reasoning."""

    floors = get_floors()
    try:
        normalized = _normalize_metrics(metrics)
    except TypeError as exc:  # pragma: no cover - invalid payloads
        raise SABARPause("Invalid metrics payload.") from exc

    if not meets_floors(normalized, floors):
        return {"allowed": False, "reason": "Metric floors breached."}

    try:
        psi = psi_from(normalized, floors)
    except SABARPause as exc:
        return {"allowed": False, "reason": str(exc)}

    return {"allowed": True, "reason": f"Ψ={psi:.3f} satisfies governance."}


def seal_if_lawful(
    agent: str,
    metrics: Mapping[str, Any] | Metrics,
    note: str = "",
    *,
    plan_id: Optional[str] = None,
    idempotency_key: Optional[str] = None,
    metadata: Optional[Mapping[str, Any]] = None,
) -> str:
    """Persist a Cooling Ledger entry and return the zkPC receipt when lawful."""

    floors = get_floors()
    normalized = _normalize_metrics(metrics)

    decision = judge(normalized)
    if not decision["allowed"]:
        raise SABARPause(decision["reason"])

    psi = psi_from(normalized, floors)
    payload = asdict(normalized)
    payload["psi"] = psi

    merged_metadata: Dict[str, Any] = dict(metadata or {})
    if plan_id is not None:
        merged_metadata.setdefault("plan_id", plan_id)
    merged_metadata.setdefault("agent", agent)

    content_hash = write_entry(
        agent,
        payload,
        note=note,
        idempotency_key=idempotency_key,
        metadata=merged_metadata if merged_metadata else None,
    )
    return seal(content_hash)


__all__ = ["judge", "seal_if_lawful"]
