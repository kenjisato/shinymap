"""Visual layer/action chooser module using shinymap output_map.

Provides a clickable button-like interface for:
- Assigning selected regions to layers (Interactive, Overlay, Underlay, Hidden)
- Unregistering selected regions

Each click shows a confirmation modal before executing the action.
"""

from __future__ import annotations

from collections.abc import Callable

from shiny import module, reactive, ui
from shiny.module import resolve_id

from ... import Map, aes
from ...mode import Display
from ...outline import Outline
from ...svg import Rect, Text
from ...ui import output_map, render_map

## Button configuration
# Colors chosen for colorblind accessibility (avoids red-green confusion)
BUTTON_CONFIG = {
    "interactive": {"label": "■ Interactive", "color": "#FF4B00"},
    "overlay": {"label": "▲ Overlay", "color": "#005AFF"},
    "underlay": {"label": "▼ Underlay", "color": "#FFF100"},
    "hidden": {"label": "○ Hidden", "color": "#6b7280"},
    "unregister": {"label": "✕ Unregister", "color": "#dc2626"},  # red-600
}

# Keep LAYER_CONFIG for backward compatibility (excludes unregister)
LAYER_CONFIG = {k: v for k, v in BUTTON_CONFIG.items() if k != "unregister"}


def _create_outline() -> Outline:
    """Create an Outline for the button panel with labels.

    Creates 5 button regions with text labels in overlay.
    Extra gap before the Unregister button to visually separate it.
    """
    regions: dict[str, list[Rect] | list[Text]] = {}
    overlay_ids: list[str] = []
    width = 180
    height = 40
    gap = 3
    separator_gap = 16  # Larger gap before Unregister
    padding_left = 8

    y = gap
    for button_id, config in BUTTON_CONFIG.items():
        # Add extra gap before unregister button
        if button_id == "unregister":
            y += separator_gap - gap  # Add extra space

        # Rectangle region (clickable)
        regions[button_id] = [
            Rect(x=0, y=y, width=width, height=height, rx=4, ry=4),
        ]

        # Text label region (overlay - rendered on top, non-interactive)
        label_id = f"_label_{button_id}"
        regions[label_id] = [
            Text(
                x=padding_left,
                y=y + height / 2,
                text=config["label"],
                font_size=16,
                text_anchor="start",
                dominant_baseline="central",
            ),
        ]
        overlay_ids.append(label_id)

        y += height + gap

    total_height = y

    return Outline(
        regions=regions,  # type: ignore[arg-type]
        metadata={
            "viewBox": f"0 0 {width} {total_height}",
            "overlay": overlay_ids,
        },
    )


def _create_aes() -> aes.ByGroup:
    """Create aesthetics for the button panel.

    Each button gets its own color. Hover shows a thicker stroke.
    """
    group_aes = {}

    # Global hover styling - transparent fill so text labels remain visible
    group_aes["__all"] = aes.ByState(
        base=aes.Shape(stroke_width=0),
        hover=aes.Shape(stroke_width=3, fill_opacity=0),
    )

    for button_id, config in BUTTON_CONFIG.items():
        # Button styling per group
        group_aes[button_id] = aes.Shape(
            fill_color=config["color"],
            fill_opacity=0.3,
            stroke_color=config["color"],
        )
        # Text label styling - dark for visibility
        group_aes[f"_label_{button_id}"] = aes.Text(
            fill_color="#1e293b",  # slate-800
        )
    return aes.ByGroup(**group_aes)


# Pre-create the outline and aesthetics (singleton)
_outline = _create_outline()
_aes = _create_aes()


@module.ui
def layer_chooser_ui(
    width: str = "200px",
    height: str = "290px",
):
    """UI for the layer/action chooser.

    Args:
        width: CSS width of the panel
        height: CSS height of the panel
    """
    # Workaround: resolve_id needed because output_map doesn't resolve click input_id
    # for module namespacing (upstream bug in _output_map.py)
    click_input_id = resolve_id("buttons_click")
    return output_map(
        "buttons",
        _outline,
        mode=Display(clickable=True, input_id=click_input_id),
        aes=_aes,
        height=height,
        width=width,
    )


@module.server
def layer_chooser_server(
    input,
    output,
    session,
    *,
    on_register: Callable[[str], None],
    on_unregister: Callable[[], None],
    get_selected_ids: Callable[[], list[str]],
    get_new_id: Callable[[], str],
):
    """Server logic for the layer/action chooser.

    Args:
        on_register: Callback when registering to a layer. Receives layer name.
        on_unregister: Callback when unregistering.
        get_selected_ids: Function to get currently selected region IDs.
        get_new_id: Function to get the new ID from text input.
    """

    @render_map
    def buttons():
        """Render the button panel."""
        return Map()

    @reactive.effect
    @reactive.event(input.buttons_click)
    def handle_click():
        """Handle button clicks - show confirmation modal."""
        clicked = input.buttons_click()
        if not clicked:
            return

        selected_ids = get_selected_ids()
        new_id = get_new_id()

        if clicked == "unregister":
            # Unregister modal
            if not selected_ids:
                ui.notification_show(
                    "No regions selected to unregister.",
                    type="warning",
                )
                return

            modal = ui.modal(
                ui.p(f"Unregister {len(selected_ids)} region(s)?"),
                ui.tags.ul([ui.tags.li(rid) for rid in sorted(selected_ids)]),
                title="Confirm Unregister",
                easy_close=True,
                footer=ui.TagList(
                    ui.modal_button("Cancel"),
                    ui.input_action_button("confirm_unregister", "Unregister", class_="btn-danger"),
                ),
            )
            ui.modal_show(modal)
        else:
            # Register to layer modal
            layer = clicked
            if not selected_ids:
                ui.notification_show(
                    "No regions selected to register.",
                    type="warning",
                )
                return
            if not new_id:
                ui.notification_show(
                    "Please enter a New ID.",
                    type="warning",
                )
                return

            symbol = get_layer_symbol(layer)
            modal = ui.modal(
                ui.p(f"Register {len(selected_ids)} region(s) as:"),
                ui.p(
                    ui.strong(f"{symbol} {new_id}"),
                    f" ({layer} layer)",
                ),
                ui.tags.ul([ui.tags.li(rid) for rid in sorted(selected_ids)]),
                title="Confirm Registration",
                easy_close=True,
                footer=ui.TagList(
                    ui.modal_button("Cancel"),
                    ui.input_action_button("confirm_register", "Register", class_="btn-primary"),
                ),
            )
            ui.modal_show(modal)

    # Store clicked layer for confirmation
    _pending_layer = reactive.value(None)

    @reactive.effect
    @reactive.event(input.buttons_click)
    def store_pending_layer():
        clicked = input.buttons_click()
        if clicked and clicked != "unregister":
            _pending_layer.set(clicked)

    @reactive.effect
    @reactive.event(input.confirm_register)
    def handle_confirm_register():
        """Handle register confirmation."""
        layer = _pending_layer()
        if layer:
            on_register(layer)
            ui.modal_remove()
            _pending_layer.set(None)

    @reactive.effect
    @reactive.event(input.confirm_unregister)
    def handle_confirm_unregister():
        """Handle unregister confirmation."""
        on_unregister()
        ui.modal_remove()


def get_layer_symbol(layer: str) -> str:
    """Get the symbol for a layer type.

    Args:
        layer: Layer name ("interactive", "overlay", "underlay", "hidden")

    Returns:
        Unicode symbol representing the layer
    """
    symbols = {
        "interactive": "■",
        "overlay": "▲",
        "underlay": "▼",
        "hidden": "○",
        "unregister": "✕",
    }
    return symbols.get(layer, "■")


## Standalone app for testing =====================================================

if __name__ == "__main__":
    from shiny import App, render

    # Test state
    _test_selected = reactive.value(["region_1", "region_2"])
    _test_new_id = reactive.value("new_name")
    _test_log = reactive.value([])

    def _on_register(layer: str):
        log = list(_test_log())
        log.append(f"Registered to {layer}: {_test_selected()}")
        _test_log.set(log)

    def _on_unregister():
        log = list(_test_log())
        log.append(f"Unregistered: {_test_selected()}")
        _test_log.set(log)

    app_ui = ui.page_fluid(
        ui.h2("Layer Chooser Test"),
        ui.layout_columns(
            ui.TagList(
                layer_chooser_ui("test_chooser"),
            ),
            ui.TagList(
                ui.h4("Action Log:"),
                ui.output_text_verbatim("log_output", placeholder=True),
            ),
            col_widths=(4, 8),
        ),
    )

    def server(input, output, session):
        layer_chooser_server(
            "test_chooser",
            on_register=_on_register,
            on_unregister=_on_unregister,
            get_selected_ids=lambda: _test_selected(),
            get_new_id=lambda: _test_new_id(),
        )

        @render.text
        def log_output():
            return "\n".join(_test_log())

    app = App(app_ui, server)
    app.run()
