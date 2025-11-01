"""Support modules for ArifOS agent packages.

The repository exposes both hyphenated package directories (to align with the
original governance naming) and underscore-based importable modules.  The
underscore variants host the actual implementation so that Python imports can
resolve cleanly, while the hyphenated directories simply re-export the public
APIs.  Tests and runtime code should import from the underscore modules, e.g.
``packages.arif_asi``.
"""

__all__ = [
    "arif_asi",
    "apex_prime",
    "compass_888",
    "eee_777",
    "integration",
]
