import warnings
from typing import Any

def _warn_invalid_keys(
        d: dict[str, Any], 
        valid_keys: set[str], 
        context: str | None = None, 
        stacklevel: int = 4
    ):
    """Warn if dict contains invalid keys"""
    unknown = set(d.keys()) - valid_keys

    if unknown:
        context = "" if context is None else f" for {context}"
        warnings.warn(
            f"Unknown keys {context}: {unknown}. Valid keys are: {sorted(valid_keys)}",
            UserWarning,
            stacklevel=stacklevel,
        )
