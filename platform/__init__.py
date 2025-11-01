"""ArifOS platform namespace package."""
from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import List

__all__ = ["cooling_ledger", "psi", "tri_witness"]


def __getattr__(name: str) -> ModuleType:
    if name in __all__:
        return import_module(f"{__name__}.{name}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> List[str]:
    return sorted(set(globals().keys()) | set(__all__))
