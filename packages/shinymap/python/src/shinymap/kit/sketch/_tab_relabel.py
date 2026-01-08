"""Sketch app for interactive SVG relabeling and layer assignment."""

from __future__ import annotations

from shiny import reactive, render, ui
from shiny.session import require_active_session

from ... import aes
from ...ui import input_map, update_map
from ._layer_chooser import (
    LAYER_CONFIG,
    get_layer_symbol,
    layer_chooser_server,
    layer_chooser_ui,
)

## Relabeling Page =====================================================================

ui_tab_relabeling = ui.nav_panel(
    "Relabeling",
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_action_button("apply_relabel", "Apply All", class_="btn-success"),
            ui.div(
                ui.help_text("Registered objects (pending relabeling)"),
                ui.output_text_verbatim("registered_objects_display", placeholder=True),
            ),
        ),
        ui.layout_columns(
            ui.output_ui("map_relabeling"),
            ui.TagList(
                ui.layout_columns(
                    # Column 1
                    ui.TagList(
                        ui.div(
                            ui.help_text("Old ID (selected objects)"),
                            ui.output_text_verbatim(
                                "selected_original_ids",
                                placeholder=True,
                            ),
                            style="height: 150px; overflow: scroll;",
                        ),
                    ),
                    # Column 2
                    ui.div(
                        ui.help_text("New ID"),
                        ui.input_text("new_id", ""),
                        layer_chooser_ui("layer_chooser", width="90%"),
                    ),
                    col_widths=(6, 6),
                ),
            ),
            col_widths=(6, 6),
        ),
        border=False,
    ),
)


def server_relabeling(input, globals):
    # Capture session now (in main app context) for use in module callbacks
    session = require_active_session(None)

    def do_register(layer: str):
        """Register selected objects to a layer."""
        new_id = input.new_id().strip()
        if not new_id:
            return

        # Get current selection from input map
        current_selected = set(input.relabeling())
        if not current_selected:
            return

        # Update relabel_rules with format: {"new_id": ["old_id1", "old_id2"]}
        current_rules = dict(globals.relabel_rules())
        current_overlay = globals.overlay_ids()

        # First, remove selected IDs from any existing mappings (allow re-registration)
        # Also track which old new_ids need to be removed from overlay_ids
        old_new_ids_to_remove = set()
        for existing_new_id, old_ids in list(current_rules.items()):
            # Remove selected IDs from this mapping
            remaining = [oid for oid in old_ids if oid not in current_selected]
            if remaining:
                current_rules[existing_new_id] = remaining
            else:
                # Remove the mapping entirely if no old IDs remain
                del current_rules[existing_new_id]
                # Track this new_id for removal from overlay_ids
                old_new_ids_to_remove.add(existing_new_id)

        # Now add selected IDs to the new_id mapping
        if new_id in current_rules:
            # Append to existing list (avoid duplicates)
            existing = set(current_rules[new_id])
            current_rules[new_id] = list(existing | current_selected)
        else:
            # Create new list for this new_id
            current_rules[new_id] = list(current_selected)

        globals.relabel_rules.set(current_rules)

        # Update layer assignments based on target layer
        # Remove old new_ids that no longer have any regions mapped to them
        current_overlay = current_overlay - old_new_ids_to_remove
        current_underlay = globals.underlay_ids() - old_new_ids_to_remove
        current_hidden = globals.hidden_ids() - old_new_ids_to_remove

        # Remove new_id from all layers first (in case it was previously assigned)
        current_overlay = current_overlay - {new_id}
        current_underlay = current_underlay - {new_id}
        current_hidden = current_hidden - {new_id}

        # Add new_id to the selected layer (interactive means not in any layer set)
        if layer == "overlay":
            current_overlay = current_overlay | {new_id}
        elif layer == "underlay":
            current_underlay = current_underlay | {new_id}
        elif layer == "hidden":
            current_hidden = current_hidden | {new_id}
        # "interactive" - no layer assignment needed

        globals.overlay_ids.set(current_overlay)
        globals.underlay_ids.set(current_underlay)
        globals.hidden_ids.set(current_hidden)

        # Move from S to R: add to registered
        current_registered = globals.registered_ids()
        globals.registered_ids.set(current_registered | current_selected)

        # Clear selection in the map
        update_map("relabeling", value={})

        # Clear the new_id input for next entry (use captured session to avoid module namespace)
        ui.update_text("new_id", value="", session=session)

    def do_unregister():
        """Unregister selected objects."""
        # Get current selection from input map
        current_selected = set(input.relabeling())
        current_registered = globals.registered_ids()

        # Only unregister objects that are both selected AND registered
        to_unregister = current_selected & current_registered

        if not to_unregister:
            return

        # Remove from relabel_rules (format: {"new_id": ["old_id1", "old_id2"]})
        current_rules = dict(globals.relabel_rules())
        updated_rules = {}
        removed_new_ids = set()

        for new_id, old_ids in current_rules.items():
            # Remove unregistered IDs from the list
            remaining = [oid for oid in old_ids if oid not in to_unregister]
            # Only keep the entry if there are still IDs mapped to this new_id
            if remaining:
                updated_rules[new_id] = remaining
            else:
                # Track new_ids that were completely removed
                removed_new_ids.add(new_id)

        globals.relabel_rules.set(updated_rules)

        # Remove from R
        globals.registered_ids.set(current_registered - to_unregister)

        # Remove any layer IDs that no longer have regions mapped to them
        globals.overlay_ids.set(globals.overlay_ids() - removed_new_ids)
        globals.underlay_ids.set(globals.underlay_ids() - removed_new_ids)
        globals.hidden_ids.set(globals.hidden_ids() - removed_new_ids)

        # Clear selection in the map
        update_map("relabeling", value={})

    # Initialize the layer chooser module with callbacks
    layer_chooser_server(
        "layer_chooser",
        on_register=do_register,
        on_unregister=do_unregister,
        get_selected_ids=lambda: list(input.relabeling()),
        get_new_id=lambda: input.new_id().strip(),
    )

    @render.ui
    def map_relabeling():
        """Preview the extracted geometry with state-based styling."""
        data = globals.message
        if "error" in data:
            return ui.p("Invalid data")

        # Get Outline object from loaded data
        outline = globals.outline()
        if not outline:
            return ui.p("Invalid data")

        if not outline.regions:
            return ui.p("Invalid data")

        # Get current state
        current_registered = globals.registered_ids()
        current_rules = globals.relabel_rules()
        overlay_ids = globals.overlay_ids()
        underlay_ids = globals.underlay_ids()
        hidden_ids = globals.hidden_ids()

        # Build old_id -> layer mapping from relabel_rules and layer assignments
        def get_layer_for_old_id(old_id: str) -> str:
            """Get the target layer for an old_id based on its new_id assignment."""
            for new_id, old_ids in current_rules.items():
                if old_id in old_ids:
                    if new_id in overlay_ids:
                        return "overlay"
                    elif new_id in underlay_ids:
                        return "underlay"
                    elif new_id in hidden_ids:
                        return "hidden"
                    return "interactive"
            return "interactive"  # Default for unregistered

        # Create groups per layer for registered regions
        layer_groups: dict[str, list[str]] = {
            "_layer_interactive": [],
            "_layer_overlay": [],
            "_layer_underlay": [],
            "_layer_hidden": [],
            "_unregistered": [],
        }

        for rid in outline.regions.keys():
            if rid in current_registered:
                layer = get_layer_for_old_id(rid)
                layer_groups[f"_layer_{layer}"].append(rid)
            else:
                layer_groups["_unregistered"].append(rid)

        # Add groups to metadata for group-based aesthetics
        outline_with_groups = outline.update_metadata({"groups": layer_groups})

        # Build aesthetics with layer-specific stroke colors
        group_aes = {
            "__all": aes.ByState(
                base=aes.Shape(stroke_width=4),
                select=aes.Shape(stroke_width=6),
                hover=aes.Shape(
                    fill_color="#fef08a",
                    fill_opacity=0.6,
                    stroke_width=0,
                ),
            ),
            # Unregistered regions: gray-ish (needs attention)
            "_unregistered": aes.Shape(
                fill_color="#cbd5e1",  # slate-300
                stroke_color="#64748b",  # slate-500
            ),
        }

        # Add layer-specific aesthetics with matching stroke colors
        for layer_id, config in LAYER_CONFIG.items():
            group_aes[f"_layer_{layer_id}"] = aes.Shape(
                fill_color="#f8fafc",  # slate-50 (registered base)
                stroke_color=config["color"],
                stroke_width=6,
            )

        return input_map(
            "relabeling",
            outline_with_groups,
            mode="multiple",
            aes=aes.ByGroup(**group_aes),
        )

    @render.text
    def selected_original_ids():
        return "\n".join(input.relabeling())

    @render.text
    def registered_objects_display():
        """Display registered objects with their new IDs and layer assignments."""
        current_rules = globals.relabel_rules()

        if not current_rules:
            return "No objects registered for relabeling."

        # Get layer assignments
        overlay = globals.overlay_ids()
        underlay = globals.underlay_ids()
        hidden = globals.hidden_ids()

        def _get_layer_for_id(new_id: str) -> str:
            if new_id in overlay:
                return "overlay"
            elif new_id in underlay:
                return "underlay"
            elif new_id in hidden:
                return "hidden"
            return "interactive"

        lines = []
        # Format: {"new_id": ["old_id1", "old_id2"]}
        for new_id, old_ids in sorted(current_rules.items()):
            old_ids_str = ", ".join(sorted(old_ids))
            layer_symbol = get_layer_symbol(_get_layer_for_id(new_id))
            lines.append(f"{layer_symbol} {new_id} ← [{old_ids_str}]")

        return "\n".join(lines)

    @reactive.effect
    @reactive.event(input.apply_relabel)
    def handle_apply():
        """Apply relabeling changes to globals.outline().

        Note: Layer assignments (overlay_ids, etc.) are NOT applied here.
        They are tracked separately and applied at export time in the Finishing tab.
        This keeps overlay regions interactive for further editing.
        """
        current_rules = globals.relabel_rules()

        if not current_rules:
            return

        # Get current outline
        outline = globals.outline()
        if not outline:
            return

        # Apply relabeling only (not layer changes)
        outline = outline.relabel(current_rules)

        # Update globals.outline with the transformed outline
        globals.outline.set(outline)

        # Clear relabeling state (changes are now applied)
        # Note: overlay_ids is NOT cleared - it's tracked for export
        globals.relabel_rules.set({})
        globals.registered_ids.set(set())
