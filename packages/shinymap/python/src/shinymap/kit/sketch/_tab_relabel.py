"""Sketch app for interactive SVG relabeling and layer assignment.

This module provides sub-tabs within the Relabeling tab:
- Sub-tab 1: Rename - 1:1 rename
- Sub-tab 2: Groups - metadata groups
- Sub-tab 3: Layers - assign regions to layers (main, overlay, underlay, etc.)
"""

from __future__ import annotations

from shiny import reactive, render, ui
from shiny.session import require_active_session

from ... import aes
from ...ui import input_map, update_map

# Layer configuration
LAYERS = ["main", "overlay", "underlay", "annotation", "hidden"]
LAYER_LABELS = {
    "main": "■ Main",
    "overlay": "▲ Overlay",
    "underlay": "▼ Underlay",
    "annotation": "★ Annotation",
    "hidden": "○ Hidden",
}


def _layer_panel(layer: str, label: str):
    """Generate a nav_panel for a specific layer."""
    other_layers = [lyr for lyr in LAYERS if lyr != layer]
    move_buttons = [
        ui.input_action_button(
            f"move_from_{layer}_to_{target}",
            f"Move to {LAYER_LABELS[target]}",
            width="100%",
        )
        for target in other_layers
    ]
    return ui.nav_panel(
        label,
        ui.layout_columns(
            ui.output_ui(f"map_layer_{layer}"),
            ui.TagList(
                ui.div(
                    ui.help_text("Selected regions"),
                    ui.output_text_verbatim(f"selected_layer_{layer}", placeholder=True),
                    style="height: 80px; overflow: scroll;",
                ),
                ui.help_text("Move selected to:"),
                *move_buttons,
            ),
            col_widths=(8, 4),
        ),
        value=layer,
    )


## Relabeling Page =====================================================================

ui_tab_relabeling = ui.nav_panel(
    "Relabeling",
    ui.navset_pill(
        # Sub-tab 1: Renaming & Grouping
        ui.nav_panel(
            "Rename",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.input_action_button("apply_relabel", "Apply Renames", class_="btn-success"),
                    ui.div(
                        ui.help_text("Pending renames"),
                        ui.output_text_verbatim("pending_renames_display", placeholder=True),
                    ),
                ),
                ui.layout_columns(
                    ui.output_ui("map_rename"),
                    ui.TagList(
                        ui.div(
                            ui.help_text("Selected region"),
                            ui.output_text_verbatim("selected_for_rename", placeholder=True),
                        ),
                        ui.div(
                            ui.help_text("New ID"),
                            ui.input_text("rename_new_id", ""),
                        ),
                        ui.input_action_button("do_rename", "Rename", class_="btn-primary"),
                        ui.input_action_button(
                            "undo_rename", "Undo Selected", class_="btn-outline-secondary"
                        ),
                    ),
                    col_widths=(8, 4),
                ),
                border=False,
            ),
        ),
        # Sub-tab 2: Metadata Groups
        ui.nav_panel(
            "Groups",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.div(
                        ui.help_text("Metadata groups"),
                        ui.output_text_verbatim("metadata_groups_display", placeholder=True),
                    ),
                ),
                ui.layout_columns(
                    ui.output_ui("map_groups"),
                    ui.TagList(
                        ui.div(
                            ui.help_text("Selected regions"),
                            ui.output_text_verbatim("selected_for_group", placeholder=True),
                            style="height: 100px; overflow: scroll;",
                        ),
                        ui.div(
                            ui.help_text("Group name"),
                            ui.input_text("group_name", ""),
                        ),
                        ui.input_action_button(
                            "do_add_to_group", "Add to Group", class_="btn-primary"
                        ),
                        ui.input_action_button(
                            "do_remove_from_groups",
                            "Remove from Groups",
                            class_="btn-outline-secondary",
                        ),
                    ),
                    col_widths=(8, 4),
                ),
                border=False,
            ),
        ),
        # Sub-tab 3: Layer Assignment (one layer at a time for accessibility)
        ui.nav_panel(
            "Layers",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.div(
                        ui.help_text("Layer counts"),
                        ui.output_text_verbatim("layer_counts_display", placeholder=True),
                    ),
                ),
                ui.navset_pill(
                    _layer_panel("main", "■ Main"),
                    _layer_panel("overlay", "▲ Overlay"),
                    _layer_panel("underlay", "▼ Underlay"),
                    _layer_panel("annotation", "★ Annotation"),
                    _layer_panel("hidden", "○ Hidden"),
                    id="layer_tabs",
                ),
                border=False,
            ),
        ),
    ),
)


def server_relabeling(input, globals):
    # Capture session now (in main app context) for use in module callbacks
    session = require_active_session(None)

    # ========================================================================
    # Sub-tab 1: Renaming
    # ========================================================================

    @reactive.effect
    @reactive.event(input.do_rename)
    def handle_rename():
        """Handle 1:1 rename operation."""
        new_id = input.rename_new_id().strip()
        if not new_id:
            ui.notification_show("Please enter a New ID.", type="warning")
            return

        # Get current selection from input map (single select)
        current_selected = list(input.rename_map())
        if not current_selected:
            ui.notification_show("No region selected.", type="warning")
            return

        if len(current_selected) > 1:
            ui.notification_show("Please select only one region for rename.", type="warning")
            return

        old_id = current_selected[0]

        # Check if new_id already exists
        outline = globals.outline()
        if outline and new_id in outline.regions and new_id != old_id:
            ui.notification_show(f"ID '{new_id}' already exists.", type="error")
            return

        # Update relabel_rules with 1:1 mapping
        current_rules = dict(globals.relabel_rules())

        # Remove old_id from any existing mapping
        for existing_new_id, old_ids in list(current_rules.items()):
            if old_id in old_ids:
                remaining = [oid for oid in old_ids if oid != old_id]
                if remaining:
                    current_rules[existing_new_id] = remaining
                else:
                    del current_rules[existing_new_id]
                break

        # Add 1:1 mapping
        current_rules[new_id] = [old_id]
        globals.relabel_rules.set(current_rules)

        # Mark as registered
        current_registered = globals.registered_ids()
        globals.registered_ids.set(current_registered | {old_id})

        # Clear selection and input
        update_map("rename_map", value={})
        ui.update_text("rename_new_id", value="", session=session)

    @reactive.effect
    @reactive.event(input.undo_rename)
    def handle_undo_rename():
        """Undo rename for selected region."""
        current_selected = set(input.rename_map())
        if not current_selected:
            return

        current_rules = dict(globals.relabel_rules())
        current_registered = globals.registered_ids()
        to_unregister = set()

        # Remove selected IDs from relabel_rules
        for new_id, old_ids in list(current_rules.items()):
            remaining = [oid for oid in old_ids if oid not in current_selected]
            if remaining:
                current_rules[new_id] = remaining
            else:
                del current_rules[new_id]
            to_unregister.update(set(old_ids) & current_selected)

        globals.relabel_rules.set(current_rules)
        globals.registered_ids.set(current_registered - to_unregister)
        update_map("rename_map", value={})

    @reactive.effect
    @reactive.event(input.apply_relabel)
    def handle_apply():
        """Apply relabeling changes to globals.outline()."""
        current_rules = globals.relabel_rules()

        if not current_rules:
            return

        outline = globals.outline()
        if not outline:
            return

        # Apply relabeling
        outline = outline.relabel(current_rules)

        # Update globals.outline with the transformed outline
        globals.outline.set(outline)

        # Clear relabeling state
        globals.relabel_rules.set({})
        globals.registered_ids.set(set())

    @render.ui
    def map_rename():
        """Render map for renaming (single select)."""
        outline = globals.outline()
        if not outline or not outline.regions:
            return ui.p("No data loaded")

        current_registered = globals.registered_ids()

        # Create groups for styling
        layer_groups = {"_registered": [], "_unregistered": []}
        for rid in outline.regions.keys():
            if rid in current_registered:
                layer_groups["_registered"].append(rid)
            else:
                layer_groups["_unregistered"].append(rid)

        outline_with_groups = outline.update_metadata({"groups": layer_groups})

        group_aes = {
            "__all": aes.ByState(
                base=aes.Shape(stroke_width=4),
                select=aes.Shape(stroke_width=6, stroke_color="#ef4444"),
                hover=aes.Shape(fill_color="#fef08a", fill_opacity=0.6, stroke_width=0),
            ),
            "_unregistered": aes.Shape(fill_color="#cbd5e1", stroke_color="#64748b"),
            "_registered": aes.Shape(fill_color="#bbf7d0", stroke_color="#22c55e"),
        }

        return input_map(
            "rename_map", outline_with_groups, mode="single", aes=aes.ByGroup(**group_aes)
        )

    @render.text
    def selected_for_rename():
        selected = input.rename_map()
        return selected if selected else "(none)"

    @render.text
    def pending_renames_display():
        """Display pending renames."""
        current_rules = globals.relabel_rules()
        if not current_rules:
            return "No pending renames."

        lines = []
        for new_id, old_ids in sorted(current_rules.items()):
            old_ids_str = ", ".join(sorted(old_ids))
            lines.append(f"{new_id} ← {old_ids_str}")
        return "\n".join(lines)

    # ========================================================================
    # Sub-tab 2: Metadata Groups
    # ========================================================================

    @reactive.effect
    @reactive.event(input.do_add_to_group)
    def handle_add_to_group():
        """Add selected regions to a metadata group."""
        group_name = input.group_name().strip()
        if not group_name:
            ui.notification_show("Please enter a group name.", type="warning")
            return

        current_selected = set(input.groups_map())
        if not current_selected:
            ui.notification_show("No regions selected.", type="warning")
            return

        # Update metadata_groups
        current_groups = dict(globals.metadata_groups())
        if group_name in current_groups:
            existing = set(current_groups[group_name])
            current_groups[group_name] = list(existing | current_selected)
        else:
            current_groups[group_name] = list(current_selected)

        globals.metadata_groups.set(current_groups)
        update_map("groups_map", value={})
        ui.update_text("group_name", value="", session=session)

    @reactive.effect
    @reactive.event(input.do_remove_from_groups)
    def handle_remove_from_groups():
        """Remove selected regions from all metadata groups."""
        current_selected = set(input.groups_map())
        if not current_selected:
            return

        current_groups = dict(globals.metadata_groups())
        updated_groups = {}

        for group_name, members in current_groups.items():
            remaining = [m for m in members if m not in current_selected]
            if remaining:
                updated_groups[group_name] = remaining

        globals.metadata_groups.set(updated_groups)
        update_map("groups_map", value={})

    @render.ui
    def map_groups():
        """Render map for group assignment (multi-select)."""
        outline = globals.outline()
        if not outline or not outline.regions:
            return ui.p("No data loaded")

        current_groups = globals.metadata_groups()

        # Create groups for styling - regions in any group vs ungrouped
        grouped_ids = set()
        for members in current_groups.values():
            grouped_ids.update(members)

        layer_groups = {"_grouped": [], "_ungrouped": []}
        for rid in outline.regions.keys():
            if rid in grouped_ids:
                layer_groups["_grouped"].append(rid)
            else:
                layer_groups["_ungrouped"].append(rid)

        outline_with_groups = outline.update_metadata({"groups": layer_groups})

        group_aes = {
            "__all": aes.ByState(
                base=aes.Shape(stroke_width=4),
                select=aes.Shape(stroke_width=6, stroke_color="#ef4444"),
                hover=aes.Shape(fill_color="#fef08a", fill_opacity=0.6, stroke_width=0),
            ),
            "_ungrouped": aes.Shape(fill_color="#cbd5e1", stroke_color="#64748b"),
            "_grouped": aes.Shape(fill_color="#c7d2fe", stroke_color="#6366f1"),
        }

        return input_map(
            "groups_map",
            outline_with_groups,
            mode="multiple",
            aes=aes.ByGroup(**group_aes),
        )

    @render.text
    def selected_for_group():
        return "\n".join(input.groups_map())

    @render.text
    def metadata_groups_display():
        """Display metadata groups."""
        current_groups = globals.metadata_groups()
        if not current_groups:
            return "No groups defined."

        lines = []
        for group_name, members in sorted(current_groups.items()):
            lines.append(f"{group_name}: {len(members)} region(s)")
            for m in sorted(members):
                lines.append(f"  - {m}")
        return "\n".join(lines)

    # ========================================================================
    # Sub-tab 3: Layer Assignment (one layer at a time)
    # ========================================================================

    def get_ids_for_layer(layer: str) -> set[str]:
        """Get region IDs belonging to a specific layer."""
        outline = globals.outline()
        if not outline:
            return set()

        all_ids = set(outline.regions.keys())
        overlay = globals.overlay_ids()
        underlay = globals.underlay_ids()
        annotation = globals.annotation_ids()
        hidden = globals.hidden_ids()

        if layer == "main":
            return all_ids - overlay - underlay - annotation - hidden
        elif layer == "overlay":
            return overlay
        elif layer == "underlay":
            return underlay
        elif layer == "annotation":
            return annotation
        elif layer == "hidden":
            return hidden
        return set()

    def move_between_layers(source: str, target: str):
        """Move selected regions from source layer to target layer."""
        map_id = f"map_layer_{source}"
        current_selected = set(getattr(input, map_id)())
        if not current_selected:
            ui.notification_show("No regions selected.", type="warning")
            return

        # Get current layer assignments
        current_overlay = globals.overlay_ids()
        current_underlay = globals.underlay_ids()
        current_hidden = globals.hidden_ids()
        current_annotation = globals.annotation_ids()

        # Remove selected from all layers
        current_overlay = current_overlay - current_selected
        current_underlay = current_underlay - current_selected
        current_hidden = current_hidden - current_selected
        current_annotation = current_annotation - current_selected

        # Add to target layer (main = not in any layer set)
        if target == "overlay":
            current_overlay = current_overlay | current_selected
        elif target == "underlay":
            current_underlay = current_underlay | current_selected
        elif target == "annotation":
            current_annotation = current_annotation | current_selected
        elif target == "hidden":
            current_hidden = current_hidden | current_selected

        globals.overlay_ids.set(current_overlay)
        globals.underlay_ids.set(current_underlay)
        globals.hidden_ids.set(current_hidden)
        globals.annotation_ids.set(current_annotation)

        update_map(map_id, value={})

    # Generate move handlers for all source->target combinations
    for src in LAYERS:
        for tgt in LAYERS:
            if src != tgt:
                _src, _tgt = src, tgt  # Capture in closure

                def make_handler(s, t):
                    @reactive.effect
                    @reactive.event(getattr(input, f"move_from_{s}_to_{t}"))
                    def handler():
                        move_between_layers(s, t)

                make_handler(_src, _tgt)

    # Generate map and selection display for each layer
    @render.ui
    def map_layer_main():
        return _render_layer_map("main")

    @render.ui
    def map_layer_overlay():
        return _render_layer_map("overlay")

    @render.ui
    def map_layer_underlay():
        return _render_layer_map("underlay")

    @render.ui
    def map_layer_annotation():
        return _render_layer_map("annotation")

    @render.ui
    def map_layer_hidden():
        return _render_layer_map("hidden")

    def _render_layer_map(layer: str):
        """Render map for a specific layer.

        Target layer regions become interactive.
        Other regions are shown as non-interactive underlay for spatial context.
        """
        outline = globals.outline()
        if not outline or not outline.regions:
            return ui.p("No data loaded")

        layer_ids = get_ids_for_layer(layer)
        if not layer_ids:
            return ui.p(f"No regions in {LAYER_LABELS[layer]} layer")

        # Get all other region IDs (for underlay context)
        all_ids = set(outline.regions.keys())
        other_ids = list(all_ids - layer_ids)

        # Create modified metadata: target layer as interactive, others as underlay
        # Also create groups for styling distinction
        # (update_metadata merges, so set layer keys to empty/override to clear them)
        modified_outline = outline.update_metadata({
            "underlay": other_ids,
            "overlay": [],
            "hidden": [],
            "annotation": [],
            "groups": {
                "_interactive": list(layer_ids),
                "_context": other_ids,
            },
        })

        # Style: interactive regions distinct, context regions very faded
        group_aes = {
            "__all": aes.ByState(
                base=aes.Shape(stroke_width=2),
                select=aes.Shape(stroke_width=4, stroke_color="#dc2626"),  # red-600
                hover=aes.Shape(fill_color="#fef08a", fill_opacity=0.8, stroke_width=0),
            ),
            # Interactive regions: blue tint, solid stroke
            "_interactive": aes.Shape(
                fill_color="#bfdbfe",  # blue-200
                fill_opacity=1.0,
                stroke_color="#1e40af",  # blue-800
            ),
            # Context regions: very light gray, dashed appearance
            "_context": aes.Shape(
                fill_color="#f8fafc",  # slate-50
                fill_opacity=0.3,
                stroke_color="#e2e8f0",  # slate-200
                stroke_width=0.5,
            ),
        }

        return input_map(
            f"map_layer_{layer}",
            modified_outline,
            mode="multiple",
            aes=aes.ByGroup(**group_aes),
        )

    @render.text
    def selected_layer_main():
        return "\n".join(input.map_layer_main())

    @render.text
    def selected_layer_overlay():
        return "\n".join(input.map_layer_overlay())

    @render.text
    def selected_layer_underlay():
        return "\n".join(input.map_layer_underlay())

    @render.text
    def selected_layer_annotation():
        return "\n".join(input.map_layer_annotation())

    @render.text
    def selected_layer_hidden():
        return "\n".join(input.map_layer_hidden())

    @render.text
    def layer_counts_display():
        """Display layer counts."""
        outline = globals.outline()
        if not outline or not outline.regions:
            return "No data loaded"

        total = len(outline.regions)
        overlay_count = len(globals.overlay_ids())
        underlay_count = len(globals.underlay_ids())
        annotation_count = len(globals.annotation_ids())
        hidden_count = len(globals.hidden_ids())
        main_count = total - overlay_count - underlay_count - annotation_count - hidden_count

        lines = [
            f"Total regions: {total}",
            "",
            f"■ Main: {main_count}",
            f"▲ Overlay: {overlay_count}",
            f"▼ Underlay: {underlay_count}",
            f"★ Annotation: {annotation_count}",
            f"○ Hidden: {hidden_count}",
        ]
        return "\n".join(lines)
