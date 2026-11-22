"""Color scale utilities for mapping data to colors.

These functions create color mappings from data values, used primarily
with output_map for data visualization.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

from .neutral import NEUTRALS
from .qualitative import QUALITATIVE
from .sequential import SEQUENTIAL_BLUE


def lerp_hex(start: str, end: str, t: float) -> str:
    """Interpolate between two hex colors.

    Args:
        start: Starting hex color (e.g., "#ff0000")
        end: Ending hex color (e.g., "#00ff00")
        t: Interpolation factor, clamped to [0, 1]

    Returns:
        Interpolated hex color
    """
    t = max(0.0, min(1.0, t))
    s_rgb = tuple(int(start[i : i + 2], 16) for i in (1, 3, 5))
    e_rgb = tuple(int(end[i : i + 2], 16) for i in (1, 3, 5))
    mix = tuple(int(s + (e - s) * t) for s, e in zip(s_rgb, e_rgb, strict=True))
    return f"#{mix[0]:02x}{mix[1]:02x}{mix[2]:02x}"


def scale_sequential(
    counts: Mapping[str, int],
    region_ids: list[str],
    palette: list[str] = SEQUENTIAL_BLUE,
    neutral_color: str = NEUTRALS["fill"],
    max_count: int | None = None,
) -> dict[str, str]:
    """Create a sequential color scale based on counts.

    Regions with count=0 get the neutral color.
    Regions with counts are colored from palette[0] (low) to palette[-1] (high).

    Args:
        counts: Mapping of region_id to count
        region_ids: All region IDs to include
        palette: Color palette to use (default: SEQUENTIAL_BLUE)
        neutral_color: Color for regions with count=0
        max_count: Fixed maximum for scaling. If None, uses dynamic max from counts.
                   For interactive visualizations, use a fixed value to prevent
                   other regions from changing color when one region is clicked.

    Returns:
        Mapping of region_id to hex color
    """
    # Determine the maximum count for scaling
    if max_count is None:
        # Dynamic: use the actual maximum from current counts
        max_count = max(counts.values(), default=0)

    if max_count <= 0:
        return {region_id: neutral_color for region_id in region_ids}

    fills = {}
    for region_id in region_ids:
        count = counts.get(region_id, 0)
        # Use continuous color interpolation for smooth visual feedback
        # Interpolate between palette colors based on count
        if count == 0:
            fills[region_id] = palette[0]
        elif count >= max_count:
            fills[region_id] = palette[-1]
        else:
            # Map count to continuous position in palette
            t = count / max_count  # Normalize to [0, 1]
            palette_pos = t * (len(palette) - 1)  # Map to [0, palette_size-1]

            # Interpolate between adjacent palette colors
            lower_idx = int(palette_pos)
            upper_idx = min(lower_idx + 1, len(palette) - 1)
            blend_factor = palette_pos - lower_idx  # Fraction between colors

            fills[region_id] = lerp_hex(palette[lower_idx], palette[upper_idx], blend_factor)

    return fills


def scale_continuous(
    values: Mapping[str, float | None],
    region_ids: list[str],
    palette: list[str] = SEQUENTIAL_BLUE,
    neutral_color: str = NEUTRALS["fill"],
    vmin: float | None = None,
    vmax: float | None = None,
) -> dict[str, str]:
    """Color data values (populations, ratios, ...) along a sequential palette.

    For data rather than click counts: values may be floats, the range is set
    by ``vmin`` / ``vmax`` (values outside are clamped), and regions without a
    value (missing, ``None`` or NaN) get ``neutral_color``, so "no data" stays
    distinguishable from the lowest value. For counts from a Count input, use
    ``scale_sequential``, which treats a missing region as zero.

    Args:
        values: Mapping of region_id to a number (int, float, numpy scalars).
        region_ids: All region IDs to include.
        palette: Color palette to use (default: SEQUENTIAL_BLUE).
        neutral_color: Color for regions without a value.
        vmin: Value mapped to ``palette[0]``. Default: the minimum value.
        vmax: Value mapped to ``palette[-1]``. Default: the maximum value.

    Returns:
        Mapping of region_id to hex color.

    Examples:
        ```pycon
        >>> from shinymap.aes.color import scale_continuous
        >>> fills = scale_continuous({"a": 1.5, "b": 4.5}, ["a", "b", "c"])
        >>> fills["a"], fills["b"], fills["c"]
        ('#eff6ff', '#1d4ed8', '#e2e8f0')

        ```
    """
    present: dict[str, float] = {}
    for region_id, value in values.items():
        if value is None:
            continue
        number = float(value)
        if math.isnan(number):
            continue
        present[region_id] = number

    if vmin is None:
        vmin = min(present.values(), default=0.0)
    if vmax is None:
        vmax = max(present.values(), default=0.0)

    fills = {}
    for region_id in region_ids:
        if region_id not in present:
            fills[region_id] = neutral_color
            continue
        if vmax <= vmin:
            t = 1.0 if present[region_id] >= vmax else 0.0
        else:
            t = max(0.0, min(1.0, (present[region_id] - vmin) / (vmax - vmin)))
        palette_pos = t * (len(palette) - 1)
        lower_idx = int(palette_pos)
        upper_idx = min(lower_idx + 1, len(palette) - 1)
        fills[region_id] = lerp_hex(palette[lower_idx], palette[upper_idx], palette_pos - lower_idx)
    return fills


def scale_diverging(
    values: Mapping[str, float],
    region_ids: list[str],
    low_color: str = "#ef4444",  # red
    mid_color: str = "#f3f4f6",  # gray
    high_color: str = "#3b82f6",  # blue
    midpoint: float = 0.0,
) -> dict[str, str]:
    """Create a diverging color scale (red-white-blue style).

    Args:
        values: Mapping of region_id to numeric value
        region_ids: All region IDs to include
        low_color: Color for low values
        mid_color: Color for midpoint value
        high_color: Color for high values
        midpoint: Value that maps to mid_color

    Returns:
        Mapping of region_id to hex color
    """
    fills = {}
    val_list = [v for v in values.values() if v is not None]
    if not val_list:
        return {region_id: mid_color for region_id in region_ids}

    min_val, max_val = min(val_list), max(val_list)

    for region_id in region_ids:
        value = values.get(region_id)
        if value is None:
            fills[region_id] = mid_color
        elif value <= midpoint:
            # Interpolate from low_color to mid_color
            if min_val < midpoint:
                t = (value - min_val) / (midpoint - min_val)
            else:
                t = 0.0
            fills[region_id] = lerp_hex(low_color, mid_color, t)
        else:
            # Interpolate from mid_color to high_color
            if max_val > midpoint:
                t = (value - midpoint) / (max_val - midpoint)
            else:
                t = 0.0
            fills[region_id] = lerp_hex(mid_color, high_color, t)

    return fills


def scale_qualitative(
    categories: Mapping[str, str | None],
    region_ids: list[str],
    palette: list[str] = QUALITATIVE,
    neutral_color: str = NEUTRALS["fill"],
) -> dict[str, str]:
    """Create a qualitative color scale for categorical data.

    Args:
        categories: Mapping of region_id to category name (or None)
        region_ids: All region IDs to include
        palette: Color palette to use (cycles if more categories than colors)
        neutral_color: Color for regions with no category

    Returns:
        Mapping of region_id to hex color
    """
    # Build category -> color mapping
    unique_cats = sorted({cat for cat in categories.values() if cat is not None})
    cat_colors = {cat: palette[i % len(palette)] for i, cat in enumerate(unique_cats)}

    fills = {}
    for region_id in region_ids:
        cat = categories.get(region_id)
        if cat is None:
            fills[region_id] = neutral_color
        else:
            fills[region_id] = cat_colors[cat]

    return fills


__all__ = ["lerp_hex", "scale_sequential", "scale_diverging", "scale_qualitative"]
