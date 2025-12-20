"""ViewBox calculation and SVG path bounds utilities."""

from __future__ import annotations

import re
import warnings
from collections.abc import Callable
from typing import Any

# Type alias for bounds calculator functions
BoundsCalculator = Callable[[str], tuple[float, float, float, float]]


def _parse_svg_dimension(value: str) -> float | None:
    """Parse SVG dimension value to float (handles px, pt, mm, etc.).

    Args:
        value: SVG dimension string (e.g., "100", "100px", "50pt")

    Returns:
        Parsed float value, or None if parsing fails

    Example:
        >>> _parse_svg_dimension("100")
        100.0
        >>> _parse_svg_dimension("100px")
        100.0
        >>> _parse_svg_dimension("50.5pt")
        50.5
        >>> _parse_svg_dimension("invalid")
        None
    """
    # Remove common SVG units and try to parse as float
    # Note: This doesn't convert units (e.g., pt to px) - just strips them
    # For viewBox calculation, we only need numeric values
    value = value.strip()
    for unit in ["px", "pt", "mm", "cm", "in", "pc", "em", "rem", "%"]:
        if value.endswith(unit):
            value = value[: -len(unit)].strip()
            break

    try:
        return float(value)
    except ValueError:
        return None


def _has_complex_commands(path: str) -> bool:
    """Check if SVG path contains complex curve commands.

    Args:
        path: SVG path data string

    Returns:
        True if path contains curve commands (C, Q, A, S, T)

    Example:
        >>> _has_complex_commands("M 0 0 L 10 10")
        False
        >>> _has_complex_commands("M 0 0 C 10 10 20 20 30 30")
        True
    """
    # Complex commands: C (cubic bezier), Q (quadratic), A (arc), S/T (smooth curves)
    return bool(re.search(r"[CcQqAaSsTt]", path))


def _find_complex_commands(path: str) -> set[str]:
    """Extract set of complex curve commands used in SVG path.

    Args:
        path: SVG path data string

    Returns:
        Set of command letters found (uppercase normalized)

    Example:
        >>> _find_complex_commands("M 0 0 L 10 10")
        set()
        >>> _find_complex_commands("M 0 0 C 10 10 20 20 30 30 Q 40 40 50 50")
        {'C', 'Q'}
        >>> _find_complex_commands("m 0 0 c 10 10 20 20 30 30")
        {'C'}
    """
    # Find all curve commands and normalize to uppercase
    matches = re.findall(r"[CcQqAaSsTt]", path)
    return {cmd.upper() for cmd in matches}


def _compute_bounds_accurate(paths: dict[str, str]) -> tuple[float, float, float, float]:
    """Compute accurate bounding box using svgpathtools if available, fallback to regex.

    This function attempts to use svgpathtools for accurate curve bounds calculation.
    If svgpathtools is not installed, falls back to regex-based calculation.

    Args:
        paths: Dict mapping region IDs to SVG path data strings

    Returns:
        Tuple of (min_x, min_y, max_x, max_y)

    Example:
        >>> paths = {"region": "M 0 0 C 10 10 20 20 30 30"}
        >>> _compute_bounds_accurate(paths)
        (0.0, 0.0, 30.0, 30.0)
    """
    try:
        from svgpathtools import parse_path

        # svgpathtools is available - use it for accurate bounds
        all_bounds = []
        for path_d in paths.values():
            try:
                path = parse_path(path_d)
                xmin, xmax, ymin, ymax = path.bbox()
                all_bounds.append((xmin, ymin, xmax, ymax))
            except Exception:
                # Fall back to regex-based parser for this path
                all_bounds.append(_parse_svg_path_bounds(path_d))

        if not all_bounds:
            return (0.0, 0.0, 0.0, 0.0)

        min_x = min(b[0] for b in all_bounds)
        min_y = min(b[1] for b in all_bounds)
        max_x = max(b[2] for b in all_bounds)
        max_y = max(b[3] for b in all_bounds)

        return (min_x, min_y, max_x, max_y)

    except ImportError:
        # svgpathtools not available - fall back to regex for all paths
        all_bounds = [_parse_svg_path_bounds(path_d) for path_d in paths.values()]

        if not all_bounds:
            return (0.0, 0.0, 0.0, 0.0)

        min_x = min(b[0] for b in all_bounds)
        min_y = min(b[1] for b in all_bounds)
        max_x = max(b[2] for b in all_bounds)
        max_y = max(b[3] for b in all_bounds)

        return (min_x, min_y, max_x, max_y)


def _parse_svg_path_bounds(path_d: str) -> tuple[float, float, float, float]:
    """Extract bounding box from SVG path data (simple regex-based implementation).

    Args:
        path_d: SVG path data string (e.g., "M 10 20 L 30 40 Z")

    Returns:
        Tuple of (min_x, min_y, max_x, max_y)

    Note:
        This is a simplified parser for polygon paths (M, L commands).
        Does not handle curves (C, Q, A) accurately - uses only coordinate endpoints.
        Sufficient for simplified map geometries.

        For accurate curve handling, provide a custom bounds_fn using a library
        like svgpathtools.

    Example:
        >>> _parse_svg_path_bounds("M 0 0 L 100 0 L 100 100 Z")
        (0.0, 0.0, 100.0, 100.0)
    """
    # Extract all numbers (handles negative, decimals)
    coord_pattern = r"[-]?\d+\.?\d*"
    coords = re.findall(coord_pattern, path_d)

    if len(coords) < 2:
        return (0.0, 0.0, 0.0, 0.0)

    x_coords = [float(coords[i]) for i in range(0, len(coords), 2)]
    y_coords = [float(coords[i]) for i in range(1, len(coords), 2)]

    return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))


def _normalize_geometry_dict(geometry: dict[str, Any]) -> dict[str, str]:
    """Normalize geometry dict to string-valued format.

    Accepts both string-valued dicts (shinymap format) and list-valued dicts
    (intermediate JSON format). Automatically skips non-string/non-list values
    like _metadata.

    Args:
        geometry: Dict with string or list[str] values representing SVG paths

    Returns:
        Dict with string-valued paths only (lists joined with space)

    Example:
        >>> # String format (already normalized)
        >>> _normalize_geometry_dict({"a": "M 0 0 L 10 10"})
        {'a': 'M 0 0 L 10 10'}

        >>> # List format (intermediate JSON)
        >>> _normalize_geometry_dict({"a": ["M 0 0", "L 10 10"]})
        {'a': 'M 0 0 L 10 10'}

        >>> # Mixed with metadata (skipped)
        >>> _normalize_geometry_dict({
        ...     "_metadata": {"viewBox": "0 0 100 100"},
        ...     "region": "M 0 0 L 100 0"
        ... })
        {'region': 'M 0 0 L 100 0'}
    """
    paths: dict[str, str] = {}

    for key, value in geometry.items():
        if isinstance(value, str):
            # Already string format (shinymap format)
            paths[key] = value
        elif isinstance(value, list):
            # List format (intermediate JSON) - join with space
            paths[key] = " ".join(value)
        # Skip non-string/non-list values (like _metadata dict)

    return paths


def calculate_viewbox(
    paths: dict[str, str],
    padding: float = 0.0,
    bounds_fn: BoundsCalculator | None = None,
) -> tuple[float, float, float, float]:
    """Calculate viewBox that covers all paths with optional padding.

    Automatically uses svgpathtools for accurate curve bounds if available.
    Falls back to regex-based calculation if svgpathtools is not installed.

    Args:
        paths: Dict mapping region IDs to SVG path data strings
        padding: Percentage of dimensions to add as padding (0.05 = 5%)
        bounds_fn: Optional custom function to calculate path bounds (advanced usage).
                  Takes path_d string, returns (min_x, min_y, max_x, max_y).
                  If None, uses automatic detection (svgpathtools if available, else regex).

    Returns:
        Tuple of (min_x, min_y, width, height) for SVG viewBox

    Example:
        >>> # Automatic bounds calculation (uses svgpathtools if available)
        >>> paths = {"a": "M 0 0 L 100 0 L 100 100 Z"}
        >>> calculate_viewbox(paths, padding=0.1)
        (-5.0, -5.0, 110.0, 110.0)

        >>> # Format as viewBox string
        >>> vb = calculate_viewbox(paths)
        >>> viewbox_str = f"{vb[0]} {vb[1]} {vb[2]} {vb[3]}"
        >>> viewbox_str
        '0.0 0.0 100.0 100.0'

        >>> # Curves are handled accurately if svgpathtools is installed
        >>> paths = {"region": "M 0 0 C 10 10 20 20 30 30"}
        >>> calculate_viewbox(paths)
        (0.0, 0.0, 30.0, 30.0)
    """
    if not paths:
        return (0.0, 0.0, 100.0, 100.0)

    # Check if paths contain complex curve commands
    all_complex_commands: set[str] = set()
    has_curves = False
    for path_d in paths.values():
        if _has_complex_commands(path_d):
            has_curves = True
            all_complex_commands.update(_find_complex_commands(path_d))

    # Use custom bounds_fn if provided, otherwise auto-detect
    if bounds_fn is None:
        # Try to use svgpathtools for accurate bounds
        try:
            import svgpathtools  # noqa: F401

            # svgpathtools available - use _compute_bounds_accurate
            min_x, min_y, max_x, max_y = _compute_bounds_accurate(paths)
        except ImportError:
            # svgpathtools not available
            if has_curves:
                # Warn user about inaccurate curve handling
                cmd_list = ", ".join(sorted(all_complex_commands))
                warnings.warn(
                    f"SVG paths contain curve commands ({cmd_list}) "
                    f"but svgpathtools is not installed. "
                    f"Using simplified regex-based bounds calculation "
                    f"which may be inaccurate.\n\n"
                    f"For accurate curve handling:\n"
                    f"  Install svgpathtools: pip install svgpathtools\n\n"
                    f"Or provide viewBox in _metadata when creating geometry JSON.",
                    UserWarning,
                    stacklevel=2,
                )

            # Fall back to regex-based calculation
            min_x, min_y, max_x, max_y = _compute_bounds_accurate(paths)
    else:
        # Custom bounds_fn provided - use it
        all_bounds = [bounds_fn(path_d) for path_d in paths.values()]
        min_x = min(b[0] for b in all_bounds)
        min_y = min(b[1] for b in all_bounds)
        max_x = max(b[2] for b in all_bounds)
        max_y = max(b[3] for b in all_bounds)

    width = max_x - min_x
    height = max_y - min_y

    # Apply padding
    if padding > 0:
        pad_x = width * padding
        pad_y = height * padding
        min_x -= pad_x
        min_y -= pad_y
        width += 2 * pad_x
        height += 2 * pad_y

    return (min_x, min_y, width, height)


def compute_viewbox_from_dict(
    geometry: dict[str, str | list[str]],
    padding: float = 0.0,
    bounds_fn: BoundsCalculator | None = None,
) -> str:
    """Compute viewBox string directly from a geometry dictionary.

    This is a convenience function that computes viewBox from a geometry dict
    without requiring file I/O. Accepts both string-valued dicts (shinymap format)
    and list-valued dicts (intermediate JSON format).

    Automatically uses svgpathtools for accurate curve bounds if available.

    Args:
        geometry: Dict mapping region IDs to SVG path data (string or list of strings).
                  Non-string/non-list values (like _metadata) are automatically skipped.
        padding: Percentage of dimensions to add as padding (0.05 = 5%)
        bounds_fn: Optional custom function to calculate path bounds (advanced usage).
                  Takes path_d string, returns (min_x, min_y, max_x, max_y).
                  If None, automatically uses svgpathtools if available, else regex-based.

    Returns:
        ViewBox string in format "min_x min_y width height"

    Note:
        Automatically uses svgpathtools for accurate curve bounds if installed.
        If curve commands are detected but svgpathtools is not available,
        a warning is issued suggesting installation.

    Example:
        >>> # From shinymap format (string values)
        >>> geometry = {"a": "M 0 0 L 100 0 L 100 100 Z"}
        >>> compute_viewbox_from_dict(geometry)
        '0.0 0.0 100.0 100.0'

        >>> # With padding
        >>> compute_viewbox_from_dict(geometry, padding=0.1)
        '-10.0 -10.0 120.0 120.0'

        >>> # From intermediate JSON format (list values)
        >>> intermediate = {
        ...     "_metadata": {"viewBox": "ignored"},
        ...     "path_1": ["M 10 10 L 40 10 L 40 40 Z"],
        ... }
        >>> compute_viewbox_from_dict(intermediate)
        '10.0 10.0 30.0 30.0'
    """
    # Normalize geometry dict to string format
    paths = _normalize_geometry_dict(geometry)

    # Compute viewBox using existing calculate_viewbox
    vb_tuple = calculate_viewbox(paths, padding=padding, bounds_fn=bounds_fn)

    # Format as viewBox string
    return f"{vb_tuple[0]} {vb_tuple[1]} {vb_tuple[2]} {vb_tuple[3]}"
