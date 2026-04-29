"""Sketch app for interactive SVG relabeling and layer assignment.

This module provides sub-tabs within the Relabeling tab:
- Sub-tab 1: Rename - 1:1 rename
- Sub-tab 2: Groups - metadata groups
- Sub-tab 3: Layers - assign regions to layers (main, overlay, underlay, etc.)
- Sub-tab 4: Lines - mark regions as lines (stroke-only rendering)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shiny import reactive, render, ui
from shiny.session import require_active_session

from ... import aes
from ...ui import input_map, update_map

if TYPE_CHECKING:
    from ...aes._core import ShapeAesthetic

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
        # Sub-tab 1: Renaming
        ui.nav_panel(
            "Rename",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.div(
                        ui.help_text("Applied renames (new ← original)"),
                        ui.output_text_verbatim("applied_renames_display", placeholder=True),
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
        # Sub-tab 4: Lines (stroke-only regions)
        ui.nav_panel(
            "Lines",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.div(
                        ui.help_text("Regions marked as lines"),
                        ui.output_text_verbatim("lines_as_path_display", placeholder=True),
                    ),
                    ui.hr(),
                    ui.div(
                        ui.help_text("Auto-detected candidates"),
                        ui.output_text_verbatim("line_candidates_display", placeholder=True),
                    ),
                ),
                ui.layout_columns(
                    ui.output_ui("map_lines"),
                    ui.TagList(
                        ui.div(
                            ui.help_text("Selected regions"),
                            ui.output_text_verbatim("selected_for_lines", placeholder=True),
                            style="height: 80px; overflow: scroll;",
                        ),
                        ui.input_action_button(
                            "do_mark_as_line", "Mark as Line", class_="btn-primary"
                        ),
                        ui.input_action_button(
                            "do_unmark_as_line",
                            "Unmark as Line",
                            class_="btn-outline-secondary",
                        ),
                    ),
                    col_widths=(8, 4),
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
        """Handle 1:1 rename operation - applies immediately."""
        new_id = input.rename_new_id().strip()
        if not new_id:
            ui.notification_show("Please enter a New ID.", type="warning")
            return

        # Get current selection from input map (single select mode returns str or None)
        old_id = input.rename_map()
        if not old_id:
            ui.notification_show("No region selected.", type="warning")
            return

        # Check if new_id already exists
        outline = globals.outline()
        if not outline:
            return
        if new_id in outline.regions and new_id != old_id:
            ui.notification_show(f"ID '{new_id}' already exists.", type="error")
            return

        # Apply rename immediately to outline
        outline = outline.relabel({new_id: old_id})
        globals.outline.set(outline)

        # Track the mapping: new_id -> original_id
        # relabel_rules now stores {current_id: original_id} for display
        current_rules = dict(globals.relabel_rules())

        # If old_id was a renamed ID (key in rules), get its original and update
        if old_id in current_rules:
            original_id = current_rules.pop(old_id)
            current_rules[new_id] = original_id
        else:
            # old_id was an original ID
            current_rules[new_id] = old_id

        globals.relabel_rules.set(current_rules)

        # Update metadata_groups to replace old_id with new_id
        current_groups = dict(globals.metadata_groups())
        for group_name, members in current_groups.items():
            if old_id in members:
                current_groups[group_name] = [new_id if m == old_id else m for m in members]
        globals.metadata_groups.set(current_groups)

        # Update layer assignments to replace old_id with new_id
        for layer_getter, layer_setter in [
            (globals.overlay_ids, globals.overlay_ids.set),
            (globals.underlay_ids, globals.underlay_ids.set),
            (globals.hidden_ids, globals.hidden_ids.set),
            (globals.annotation_ids, globals.annotation_ids.set),
        ]:
            layer_ids = layer_getter()
            if old_id in layer_ids:
                layer_ids = (layer_ids - {old_id}) | {new_id}
                layer_setter(layer_ids)

        # Update lines_as_path_ids to replace old_id with new_id
        lines_ids = globals.lines_as_path_ids()
        if old_id in lines_ids:
            globals.lines_as_path_ids.set((lines_ids - {old_id}) | {new_id})

        # Clear selection and input
        update_map("rename_map", value={})
        ui.update_text("rename_new_id", value="", session=session)

    @render.ui
    def map_rename():
        """Render map for renaming (single select)."""
        outline = globals.outline()
        if not outline or not outline.regions:
            return ui.p("No data loaded")

        # Get renamed IDs (current IDs that have been renamed from originals)
        renamed_ids = set(globals.relabel_rules().keys())

        # Create groups for styling: renamed vs original
        layer_groups = {"_renamed": [], "_original": []}
        for rid in outline.regions.keys():
            if rid in renamed_ids:
                layer_groups["_renamed"].append(rid)
            else:
                layer_groups["_original"].append(rid)

        outline_with_groups = outline.update_metadata({"groups": layer_groups})

        group_aes = {
            "__all": aes.ByState(
                base=aes.Shape(stroke_width=4),
                select=aes.Shape(stroke_width=6, stroke_color="#ef4444"),
                hover=aes.Shape(fill_color="#fef08a", fill_opacity=0.6, stroke_width=0),
            ),
            "_original": aes.Shape(fill_color="#cbd5e1", stroke_color="#64748b"),
            "_renamed": aes.Shape(fill_color="#bbf7d0", stroke_color="#22c55e"),
        }

        return input_map(
            "rename_map", outline_with_groups, mode="single", aes=aes.ByGroup(**group_aes)
        )

    @render.text
    def selected_for_rename():
        selected = input.rename_map()
        return selected if selected else "(none)"

    @render.text
    def applied_renames_display():
        """Display applied renames (new_id <- original_id)."""
        current_rules = globals.relabel_rules()
        if not current_rules:
            return "No renames applied."

        lines = []
        for new_id, original_id in sorted(current_rules.items()):
            lines.append(f"{new_id} ← {original_id}")
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
        """Render map for group assignment (multi-select).

        Only main layer regions are interactive. Overlay/underlay/hidden/annotation
        regions are rendered as faded context so they don't block main regions.
        """
        outline = globals.outline()
        if not outline or not outline.regions:
            return ui.p("No data loaded")

        current_groups = globals.metadata_groups()

        # Get main layer IDs (interactive) vs non-main (context)
        all_ids = set(outline.regions.keys())
        non_main_ids = (
            globals.overlay_ids()
            | globals.underlay_ids()
            | globals.hidden_ids()
            | globals.annotation_ids()
        )
        main_ids = all_ids - non_main_ids
        context_ids = list(non_main_ids)

        # Create groups for styling - grouped vs ungrouped (within main layer only)
        grouped_ids = set()
        for members in current_groups.values():
            grouped_ids.update(members)

        layer_groups = {"_grouped": [], "_ungrouped": [], "_context": context_ids}
        for rid in main_ids:
            if rid in grouped_ids:
                layer_groups["_grouped"].append(rid)
            else:
                layer_groups["_ungrouped"].append(rid)

        # Put non-main regions as underlay so they don't block interactive regions
        outline_with_groups = outline.update_metadata(
            {
                "underlay": context_ids,
                "overlay": [],
                "hidden": [],
                "annotation": [],
                "groups": layer_groups,
            }
        )

        group_aes = {
            "__all": aes.ByState(
                base=aes.Shape(stroke_width=4),
                select=aes.Shape(stroke_width=6, stroke_color="#ef4444"),
                hover=aes.Shape(fill_color="#fef08a", fill_opacity=0.6, stroke_width=0),
            ),
            "_ungrouped": aes.Shape(fill_color="#cbd5e1", stroke_color="#64748b"),
            "_grouped": aes.Shape(fill_color="#c7d2fe", stroke_color="#6366f1"),
            # Context regions: very light, non-blocking
            "_context": aes.Shape(
                fill_color="#f8fafc",
                fill_opacity=0.3,
                stroke_color="#e2e8f0",
                stroke_width=0.5,
            ),
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
        modified_outline = outline.update_metadata(
            {
                "underlay": other_ids,
                "overlay": [],
                "hidden": [],
                "annotation": [],
                "groups": {
                    "_interactive": list(layer_ids),
                    "_context": other_ids,
                },
            }
        )

        # Style: interactive regions distinct, context regions very faded
        group_aes: dict[str, aes.ByState | ShapeAesthetic] = {
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

    # ========================================================================
    # Sub-tab 4: Lines (stroke-only regions)
    # ========================================================================

    @reactive.effect
    @reactive.event(input.do_mark_as_line)
    def handle_mark_as_line():
        """Mark selected regions as lines (stroke-only)."""
        current_selected = set(input.map_lines())
        if not current_selected:
            ui.notification_show("No regions selected.", type="warning")
            return

        current_lines = globals.lines_as_path_ids()
        globals.lines_as_path_ids.set(current_lines | current_selected)
        update_map("map_lines", value={})

    @reactive.effect
    @reactive.event(input.do_unmark_as_line)
    def handle_unmark_as_line():
        """Remove selected regions from lines (restore as shapes)."""
        current_selected = set(input.map_lines())
        if not current_selected:
            ui.notification_show("No regions selected.", type="warning")
            return

        current_lines = globals.lines_as_path_ids()
        globals.lines_as_path_ids.set(current_lines - current_selected)
        update_map("map_lines", value={})

    @render.ui
    def map_lines():
        """Render map for line assignment (multi-select).

        Marked lines are rendered as overlay (non-interactive, stroke-only) so
        underlying shapes can be clicked. Shapes and candidates are interactive.
        """
        from ...svg import is_stroke_only_candidate

        outline = globals.outline()
        if not outline or not outline.regions:
            return ui.p("No data loaded")

        current_lines = globals.lines_as_path_ids()

        # Create groups for styling: lines (overlay), candidates, shapes
        layer_groups = {"_lines": [], "_candidates": [], "_shapes": []}
        for rid, elements in outline.regions.items():
            if rid in current_lines:
                layer_groups["_lines"].append(rid)
            elif is_stroke_only_candidate(elements):
                layer_groups["_candidates"].append(rid)
            else:
                layer_groups["_shapes"].append(rid)

        # All regions remain interactive (no layer changes)
        outline_with_groups = outline.update_metadata({"groups": layer_groups})

        # Lines need ByState to explicitly set no fill for ALL states
        # (base, select, hover) - otherwise __all hover will add fill
        line_aesthetic = aes.ByState(
            base=aes.Shape(
                fill_color="transparent", fill_opacity=0, stroke_color="#14b8a6", stroke_width=3
            ),
            select=aes.Shape(
                fill_color="transparent", fill_opacity=0, stroke_color="#ef4444", stroke_width=4
            ),
            hover=aes.Shape(
                fill_color="transparent", fill_opacity=0, stroke_color="#0d9488", stroke_width=4
            ),
        )

        group_aes = {
            "__all": aes.ByState(
                base=aes.Shape(stroke_width=4),
                select=aes.Shape(stroke_width=6, stroke_color="#ef4444"),
                hover=aes.Shape(fill_color="#fef08a", fill_opacity=0.6, stroke_width=0),
            ),
            # Shapes: default gray
            "_shapes": aes.Shape(fill_color="#cbd5e1", stroke_color="#64748b"),
            # Candidates: amber/orange, semi-transparent to hint stroke-only
            "_candidates": aes.Shape(
                fill_color="#fed7aa", fill_opacity=0.3, stroke_color="#f97316", stroke_width=2
            ),
            # Marked as lines: stroke-only with explicit ByState for all states
            "_lines": line_aesthetic,
        }

        return input_map(
            "map_lines",
            outline_with_groups,
            mode="multiple",
            aes=aes.ByGroup(**group_aes),
        )

    @render.text
    def selected_for_lines():
        return "\n".join(input.map_lines())

    @render.text
    def lines_as_path_display():
        """Display regions marked as lines."""
        current_lines = globals.lines_as_path_ids()
        if not current_lines:
            return "No regions marked as lines."

        return "\n".join(f"━ {rid}" for rid in sorted(current_lines))

    @render.text
    def line_candidates_display():
        """Display auto-detected line candidates."""
        from ...svg import is_stroke_only_candidate

        outline = globals.outline()
        if not outline:
            return "No data loaded."

        current_lines = globals.lines_as_path_ids()
        candidates = []
        for rid, elements in outline.regions.items():
            if rid not in current_lines and is_stroke_only_candidate(elements):
                candidates.append(rid)

        if not candidates:
            return "No candidates detected."

        return "\n".join(f"? {rid}" for rid in sorted(candidates))
