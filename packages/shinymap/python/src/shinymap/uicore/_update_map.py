"""Update map function for Shiny.

This module provides the update_map function for updating
map components without full re-render.
"""

from collections.abc import Mapping
from typing import Any

from shiny.module import resolve_id
from shiny.session import Session, require_active_session

from ..aes._core import BaseAesthetic, ByGroup, ByState
from ..types import CountMap, TooltipMap

# Type alias for aes parameter
AesType = ByGroup | ByState | BaseAesthetic | Mapping[str, Mapping[str, Any] | None] | None


def update_map(
    id: str,
    *,
    aes: AesType = None,
    value: CountMap = None,
    tooltips: TooltipMap = None,
    session: Session | None = None,
) -> None:
    """Update an input_map or output_map without full re-render.

    For input_map: Updates aesthetics and selection state.
    For output_map: Updates aesthetics only (use @render_map for data changes).

    Args:
        id: The map element ID
        aes: Aesthetic configuration (ByGroup, ByState, or BaseAesthetic)
        value: (input_map only) Selection state; pass {} to clear all selections
        tooltips: Region tooltips
        session: A Session instance. If not provided, it is inferred via get_current_session()

    Examples:
        ```pycon
        from shinymap import aes
        from shinymap.ui import update_map

        # Update aesthetics with ByGroup (per-region colors)
        update_map("my_map", aes=aes.ByGroup(
            region1=aes.Shape(fill_color="#ff0000"),
            region2=aes.Shape(fill_color="#00ff00"),
        ))

        # Update with ByState (base/select/hover)
        update_map("my_map", aes=aes.ByState(
            base=aes.Shape(fill_color="#e2e8f0"),
            select=aes.Shape(fill_color="#bfdbfe"),
        ))

        # Clear all selections (input_map only)
        update_map("my_map", value={})

        # Set specific selections (input_map only)
        update_map("my_map", value={"region1": 1, "region2": 1})
        ```
    Note:
        - Uses shallow merge semantics: new properties override existing ones
        - Properties not specified are left unchanged
        - For output_map data updates, use @render_map re-execution instead
    """
    session = require_active_session(session)

    # Build update payload (JS will convert snake_case to camelCase)
    updates: dict[str, Any] = {}

    if aes is not None:
        # For update_map, we pass the raw aes object/dict
        # JS handles conversion
        if isinstance(aes, (ByGroup, ByState, BaseAesthetic)):
            # Convert to dict for JSON serialization
            if isinstance(aes, ByGroup):
                updates["aes"] = {
                    k: v.to_js_dict() if hasattr(v, "to_js_dict") else v for k, v in aes.items()
                }
            elif isinstance(aes, ByState):
                updates["aes"] = aes.to_js_dict()
            else:
                updates["aes"] = {"base": aes.to_dict()}
        else:
            updates["aes"] = aes
    if value is not None:
        updates["value"] = value
    if tooltips is not None:
        updates["tooltips"] = tooltips

    if not updates:
        return  # Nothing to update

    # Resolve ID for Shiny module namespacing
    resolved = resolve_id(id)

    # Send custom message to JavaScript (JS handles snake_case to camelCase)
    msg = {"id": resolved, "updates": updates}
    session._send_message_sync({"custom": {"shinymap-update": msg}})
