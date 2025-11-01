"""Cooling Ledger append-only persistence helpers."""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional


_LEDGER_FILENAME = "ledger.jsonl"


def _ledger_path() -> Path:
    env_override = os.getenv("ARIFOS_LEDGER_PATH")
    if env_override:
        return Path(env_override)
    return Path(__file__).resolve().parent / _LEDGER_FILENAME


def _encode_base58(data: bytes) -> str:
    alphabet = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    num = int.from_bytes(data, "big")
    if num == 0:
        return alphabet[0:1].decode()

    encoded = bytearray()
    while num > 0:
        num, remainder = divmod(num, 58)
        encoded.append(alphabet[remainder])

    encoded.reverse()
    return encoded.decode()


def _existing_hash_for_key(path: Path, key: str) -> Optional[str]:
    if not key:
        return None
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:  # pragma: no cover - guardrail
                continue
            if payload.get("idempotency_key") == key:
                return payload.get("hash")
    return None


_EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_DIGIT_PATTERN = re.compile(r"\b\d{6,}\b")


def _redact_text(value: str) -> str:
    """Return a privacy-safe representation of ``value``."""

    redacted = _EMAIL_PATTERN.sub("[redacted-email]", value)
    redacted = _DIGIT_PATTERN.sub("[redacted-number]", redacted)
    return redacted


def _sanitize_metadata(metadata: Mapping[str, Any]) -> Dict[str, Any]:
    def _clean(value: Any) -> Any:
        if isinstance(value, str):
            return _redact_text(value)
        if isinstance(value, Mapping):
            return {key: _clean(inner) for key, inner in value.items()}
        if isinstance(value, list):
            return [_clean(item) for item in value]
        return value

    return {key: _clean(value) for key, value in metadata.items()}


def _replay_exists(path: Path, plan_id: Optional[str], content_hash: str) -> bool:
    if not plan_id or not content_hash or not path.exists():
        return False
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:  # pragma: no cover - guardrail
                continue
            if payload.get("hash") != content_hash:
                continue
            metadata = payload.get("metadata") or {}
            if metadata.get("plan_id") == plan_id:
                return True
    return False


def write_entry(
    agent: str,
    metrics: Mapping[str, float],
    note: str = "",
    *,
    idempotency_key: Optional[str] = None,
    metadata: Optional[Mapping[str, Any]] = None,
) -> str:
    """Append a Cooling Ledger entry and return its deterministic content hash."""

    ledger_path = _ledger_path()
    existing_hash = _existing_hash_for_key(ledger_path, idempotency_key) if idempotency_key else None
    if existing_hash:
        return existing_hash

    timestamp = datetime.now(timezone.utc).isoformat()
    metrics_copy: Dict[str, float] = dict(metrics)
    redacted_note = _redact_text(note)
    payload: Dict[str, Any] = {
        "agent": agent,
        "metrics": metrics_copy,
        "note": redacted_note,
    }
    if idempotency_key is not None:
        payload["idempotency_key"] = idempotency_key
    if metadata:
        sanitized_metadata = _sanitize_metadata(metadata)
        payload["metadata"] = sanitized_metadata
    else:
        sanitized_metadata = None

    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    content_hash = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    plan_id = None
    if sanitized_metadata:
        potential_plan_id = sanitized_metadata.get("plan_id")
        if isinstance(potential_plan_id, str) and potential_plan_id:
            plan_id = potential_plan_id

    if _replay_exists(ledger_path, plan_id, content_hash):
        raise ValueError(
            "Cooling Ledger replay detected for plan_id and content hash pair."
        )

    record: Dict[str, Any] = {
        **payload,
        "ts": timestamp,
        "hash": content_hash,
    }

    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")

    return content_hash


def seal(content_hash: str) -> str:
    """Return a zkPC-like receipt identifier derived from the hash and timestamp."""

    timestamp = datetime.now(timezone.utc).isoformat()
    digest = hashlib.sha256(f"{content_hash}:{timestamp}".encode("utf-8")).digest()
    seal_id = _encode_base58(digest)
    return seal_id


__all__ = ["write_entry", "seal"]
