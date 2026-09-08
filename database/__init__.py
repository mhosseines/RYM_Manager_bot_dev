"""Compatibility facade for the complete legacy database API."""

import importlib.util
from pathlib import Path


_legacy_path = Path(__file__).resolve().parent / "legacy.py"
_spec = importlib.util.spec_from_file_location("_rym_legacy_database", _legacy_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Could not load database implementation: {_legacy_path}")

_legacy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_legacy)

for _name in dir(_legacy):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_legacy, _name)

__all__ = [name for name in globals() if not name.startswith("_")]