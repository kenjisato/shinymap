"""Calculate optimal viewBox for Japan prefecture geometry."""

import re
from pathlib import Path
from japan_prefectures import get_japan_geometry, get_japan_dividers


def extract_coordinates(path_string: str) -> list[tuple[float, float]]:
    """Extract all x,y coordinate pairs from SVG path."""
    coords = []
    current_x, current_y = 0.0, 0.0

    # Parse SVG path commands
    commands = re.findall(r'([MLHVZ])\s*([\d\s.-]*)', path_string)

    for cmd, params in commands:
        if cmd == 'M' or cmd == 'L':
            # Move or Line - x,y pairs
            numbers = re.findall(r'[-+]?\d+\.?\d*', params)
            for i in range(0, len(numbers) - 1, 2):
                x, y = float(numbers[i]), float(numbers[i + 1])
                coords.append((x, y))
                current_x, current_y = x, y
        elif cmd == 'H':
            # Horizontal line - only x coordinate
            numbers = re.findall(r'[-+]?\d+\.?\d*', params)
            for num in numbers:
                x = float(num)
                coords.append((x, current_y))
                current_x = x
        elif cmd == 'V':
            # Vertical line - only y coordinate
            numbers = re.findall(r'[-+]?\d+\.?\d*', params)
            for num in numbers:
                y = float(num)
                coords.append((current_x, y))
                current_y = y

    return coords


def calculate_bounds(geometry: dict[str, str]) -> tuple[float, float, float, float]:
    """Calculate bounding box for geometry dict."""
    all_x = []
    all_y = []

    for path in geometry.values():
        coords = extract_coordinates(path)
        for x, y in coords:
            all_x.append(x)
            all_y.append(y)

    if not all_x:
        return (0, 0, 0, 0)

    return (min(all_x), min(all_y), max(all_x), max(all_y))


def main():
    """Calculate and print optimal viewBox."""
    geometry = get_japan_geometry()
    dividers = get_japan_dividers()

    # Calculate bounds for prefectures only
    min_x, min_y, max_x, max_y = calculate_bounds(geometry)

    print("Prefecture bounds:")
    print(f"  X: [{min_x:.1f}, {max_x:.1f}]")
    print(f"  Y: [{min_y:.1f}, {max_y:.1f}]")

    # Calculate bounds for dividers
    div_min_x, div_min_y, div_max_x, div_max_y = calculate_bounds(dividers)

    print("\nDivider bounds:")
    print(f"  X: [{div_min_x:.1f}, {div_max_x:.1f}]")
    print(f"  Y: [{div_min_y:.1f}, {div_max_y:.1f}]")

    # Recommended viewBox option 1 - tight to prefectures only
    viewbox_x = min_x
    viewbox_y = min_y
    viewbox_width = max_x - min_x
    viewbox_height = max_y - min_y

    print(f"\nRecommended viewBox (tight to prefectures only):")
    print(f'VIEWBOX = "{viewbox_x:.1f} {viewbox_y:.1f} {viewbox_width:.1f} {viewbox_height:.1f}"')
    print(f"Aspect ratio: {viewbox_width / viewbox_height:.3f}:1")

    # Recommended viewBox option 2 - include both prefectures and dividers
    combined_min_x = min(min_x, div_min_x)
    combined_min_y = min(min_y, div_min_y)
    combined_max_x = max(max_x, div_max_x)
    combined_max_y = max(max_y, div_max_y)

    combined_viewbox_x = combined_min_x
    combined_viewbox_y = combined_min_y
    combined_viewbox_width = combined_max_x - combined_min_x
    combined_viewbox_height = combined_max_y - combined_min_y

    print(f"\nRecommended viewBox (prefectures + dividers):")
    print(f'VIEWBOX = "{combined_viewbox_x:.1f} {combined_viewbox_y:.1f} {combined_viewbox_width:.1f} {combined_viewbox_height:.1f}"')
    print(f"Aspect ratio: {combined_viewbox_width / combined_viewbox_height:.3f}:1")

    # Current viewBox
    print(f"\nCurrent viewBox: \"0.0 0.0 1270.0 1524.0\"")
    print(f"Current aspect ratio: {1270.0 / 1524.0:.3f}:1")


if __name__ == "__main__":
    main()
