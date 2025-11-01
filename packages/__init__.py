"""Support modules for ArifOS agent packages.

All importable modules use Python-friendly underscore names (``arif_asi``,
``apex_prime`` and so on).  Earlier revisions also stored hyphenated directory
names to mirror the governance terminology, but those shims have been removed
so that imports resolve deterministically.  Runtime code should import from the
underscore variants exclusively.
"""

__all__ = [
    "arif_agi",
    "arif_asi",
    "apex_prime",
    "compass_888",
    "eee_777",
    "integration",
]
