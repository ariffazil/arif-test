"""Cooling Ledger append-only persistence helpers."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Mapping


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


def write_entry(agent: str, metrics: Mapping[str, float], note: str = "") -> str:
    """Append a Cooling Ledger entry and return its deterministic content hash."""

    timestamp = datetime.now(timezone.utc).isoformat()
    metrics_copy: Dict[str, float] = dict(metrics)
    payload = {
        "agent": agent,
        "metrics": metrics_copy,
        "note": note,
    }
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    content_hash = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    record = {
        **payload,
        "ts": timestamp,
        "hash": content_hash,
    }

    ledger_path = _ledger_path()
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
