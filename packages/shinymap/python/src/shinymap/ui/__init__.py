"""Shiny UI components for shinymap.

This module provides the main UI functions for creating interactive map inputs
and outputs in Shiny applications.

Usage:
    from shinymap.ui import input_map, output_map, update_map
    from shinymap import render_map  # decorator, at top-level

    # UI layer
    input_map("region", geometry, mode="single")
    output_map("my_map", geometry)

    # Server layer
    @render_map
    def my_map():
        return Map().with_value(counts)

    # Update existing map
    update_map("my_map", aes=aes.ByGroup(region1=aes.Shape(fill_color="#ff0000")))
"""

from __future__ import annotations

from ._ui import (
    input_checkbox_group,
    input_map,
    input_radio_buttons,
    output_map,
    update_map,
)

__all__ = [
    "input_map",
    "output_map",
    "update_map",
    "input_radio_buttons",
    "input_checkbox_group",
]
