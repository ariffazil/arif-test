"""Cooling Ledger append-only persistence helpers."""
from __future__ import annotations

import hashlib
import json
import os
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
    payload: Dict[str, Any] = {
        "agent": agent,
        "metrics": metrics_copy,
        "note": note,
    }
    if idempotency_key is not None:
        payload["idempotency_key"] = idempotency_key
    if metadata:
        payload["metadata"] = dict(metadata)

    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    content_hash = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

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
