"""Payload builder for v0.3 aesthetic format.

This module handles the final step of converting aesthetic configurations
to JSON payloads for JavaScript. The key architectural principle is:

- Python (this module) does all resolution and merging
- JavaScript only does simple lookup (no merging)

This module is imported only by the UI layer (_input_map.py, _output_map.py)
and should not be imported by other modules to avoid circular dependencies.
"""

from ._aes import build_aes_payload

__all__ = ["build_aes_payload"]
