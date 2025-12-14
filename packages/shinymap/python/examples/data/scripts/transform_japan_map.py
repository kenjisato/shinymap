"""Script to transform Japan prefecture map for better visualization.

Transformations:
1. Move Okinawa (47) and Kagoshima's island regions to top-left corner
2. Scale them by 1.3x for better visibility
3. Add dividing lines to show they've been repositioned
4. Adjust viewBox to be more square
"""

import json
import re
from typing import Dict, List, Tuple


def parse_path_commands(path: str) -> List[Tuple[str, List[float]]]:
    """Parse SVG path into commands and coordinates."""
    commands = []
    # Match command letter followed by numbers
    pattern = r'([MLZmlz])\s*([\d\s,.-]*)'

    for match in re.finditer(pattern, path):
        cmd = match.group(1)
        coords_str = match.group(2).strip()

        if coords_str:
            # Split by spaces and commas, convert to floats
            coords = [float(x) for x in re.findall(r'[-+]?\d+\.?\d*', coords_str)]
        else:
            coords = []

        commands.append((cmd, coords))

    return commands


def build_path_string(commands: List[Tuple[str, List[float]]]) -> str:
    """Build SVG path string from commands."""
    parts = []
    for cmd, coords in commands:
        if coords:
            coords_str = ' '.join(f'{c:.2f}' for c in coords)
            parts.append(f'{cmd}{coords_str}')
        else:
            parts.append(cmd)
    return ' '.join(parts)


def get_path_bounds(path: str) -> Tuple[float, float, float, float]:
    """Get bounding box of a path (min_x, min_y, max_x, max_y)."""
    commands = parse_path_commands(path)

    x_coords = []
    y_coords = []

    for cmd, coords in commands:
        if cmd.upper() in ['M', 'L'] and coords:
            # Extract x, y pairs
            for i in range(0, len(coords), 2):
                if i + 1 < len(coords):
                    x_coords.append(coords[i])
                    y_coords.append(coords[i + 1])

    if not x_coords:
        return (0, 0, 0, 0)

    return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))


def transform_path(path: str, dx: float, dy: float, scale: float = 1.0,
                   center_x: float = 0, center_y: float = 0) -> str:
    """Transform path: translate by (dx, dy) and scale around a center point."""
    commands = parse_path_commands(path)

    transformed = []
    for cmd, coords in commands:
        if cmd.upper() in ['M', 'L'] and coords:
            new_coords = []
            for i in range(0, len(coords), 2):
                if i + 1 < len(coords):
                    x, y = coords[i], coords[i + 1]

                    # Scale around center
                    if scale != 1.0:
                        x = center_x + (x - center_x) * scale
                        y = center_y + (y - center_y) * scale

                    # Translate
                    x += dx
                    y += dy

                    new_coords.extend([x, y])
            transformed.append((cmd, new_coords))
        else:
            transformed.append((cmd, coords))

    return build_path_string(transformed)


def transform_japan_map(input_file: str, output_file: str):
    """Transform Japan map with Okinawa and southern islands relocated."""

    # Load original geometry
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Filter out metadata
    geometry = {k: v for k, v in data.items() if not k.startswith('_')}

    # Define which prefectures to move
    # 47 = Okinawa, 46 = Kagoshima (includes Amami islands)
    islands_to_move = ['46', '47']

    # Calculate bounds for islands
    island_bounds = {}
    for code in islands_to_move:
        if code in geometry:
            island_bounds[code] = get_path_bounds(geometry[code])

    # Calculate overall bounds for islands
    if island_bounds:
        all_island_x = [b[0] for b in island_bounds.values()] + [b[2] for b in island_bounds.values()]
        all_island_y = [b[1] for b in island_bounds.values()] + [b[3] for b in island_bounds.values()]

        island_min_x = min(all_island_x)
        island_min_y = min(all_island_y)
        island_max_x = max(all_island_x)
        island_max_y = max(all_island_y)

        island_center_x = (island_min_x + island_max_x) / 2
        island_center_y = (island_min_y + island_max_y) / 2

        print(f"Original island bounds: x=[{island_min_x:.1f}, {island_max_x:.1f}], y=[{island_min_y:.1f}, {island_max_y:.1f}]")
        print(f"Island center: ({island_center_x:.1f}, {island_center_y:.1f})")

    # Target position: top-left corner with padding
    padding = 20
    target_x = padding
    target_y = padding
    scale_factor = 1.3

    # Calculate translation needed
    dx = target_x - island_min_x * scale_factor
    dy = target_y - island_min_y * scale_factor

    print(f"\nTransformation:")
    print(f"  Scale: {scale_factor}x")
    print(f"  Translate: dx={dx:.1f}, dy={dy:.1f}")

    # Transform the island prefectures
    transformed_geometry = {}
    for code, path in geometry.items():
        if code in islands_to_move:
            # Scale around center, then translate
            transformed_geometry[code] = transform_path(
                path, dx, dy, scale_factor, island_center_x, island_center_y
            )
        else:
            transformed_geometry[code] = path

    # Calculate new bounds for transformed islands
    transformed_island_bounds = {}
    for code in islands_to_move:
        if code in transformed_geometry:
            transformed_island_bounds[code] = get_path_bounds(transformed_geometry[code])

    if transformed_island_bounds:
        all_x = [b[0] for b in transformed_island_bounds.values()] + [b[2] for b in transformed_island_bounds.values()]
        all_y = [b[1] for b in transformed_island_bounds.values()] + [b[3] for b in transformed_island_bounds.values()]
        print(f"\nTransformed island bounds: x=[{min(all_x):.1f}, {max(all_x):.1f}], y=[{min(all_y):.1f}, {max(all_y):.1f}]")

    # Add inverted-L-shaped dividing line to separate Okinawa from mainland
    # Start at right edge of islands, draw vertical line down, then horizontal line to the right
    divider_gap = 15
    islands_right_x = max(all_x)
    islands_bottom_y = max(all_y)

    # Vertical segment: from bottom-right of islands, going down
    vertical_start_x = islands_right_x
    vertical_start_y = islands_bottom_y + divider_gap
    vertical_end_y = vertical_start_y + 60  # Length of vertical segment

    # Horizontal segment: continues to the right edge of the map
    horizontal_end_x = vertical_start_x + 200  # Extend to the right

    # Create inverted-L path: M(start) L(down) L(right)
    divider_inverted_l = (
        f"M{vertical_start_x:.1f} {vertical_start_y:.1f} "
        f"L{vertical_start_x:.1f} {vertical_end_y:.1f} "
        f"L{horizontal_end_x:.1f} {vertical_end_y:.1f}"
    )

    # Store divider with special key
    transformed_geometry['_divider_1'] = divider_inverted_l

    # Calculate overall bounds (excluding islands that will be transformed)
    all_bounds = [get_path_bounds(p) for code, p in geometry.items() if code not in islands_to_move]
    all_x = [b[0] for b in all_bounds] + [b[2] for b in all_bounds]
    all_y = [b[1] for b in all_bounds] + [b[3] for b in all_bounds]

    # Include transformed islands
    for bounds in transformed_island_bounds.values():
        min_x, min_y, max_x, max_y = bounds
        all_x.extend([min_x, max_x])
        all_y.extend([min_y, max_y])

    overall_min_x = min(all_x)
    overall_min_y = min(all_y)
    overall_max_x = max(all_x)
    overall_max_y = max(all_y)

    # Calculate viewBox with padding
    viewbox_padding = 10
    viewbox_x = overall_min_x - viewbox_padding
    viewbox_y = overall_min_y - viewbox_padding
    viewbox_width = overall_max_x - overall_min_x + 2 * viewbox_padding
    viewbox_height = overall_max_y - overall_min_y + 2 * viewbox_padding

    print(f"\nNew ViewBox: \"{viewbox_x:.1f} {viewbox_y:.1f} {viewbox_width:.1f} {viewbox_height:.1f}\"")
    print(f"Aspect ratio: {viewbox_width/viewbox_height:.2f}:1")

    # Save transformed geometry
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(transformed_geometry, f, ensure_ascii=False, indent=2)

    print(f"\nTransformed map saved to: {output_file}")
    print(f"\nUpdate your app with:")
    print(f"VIEWBOX = \"{viewbox_x:.1f} {viewbox_y:.1f} {viewbox_width:.1f} {viewbox_height:.1f}\"")


if __name__ == '__main__':
    from pathlib import Path
    data_dir = Path(__file__).parent / "data"

    transform_japan_map(
        input_file=str(data_dir / 'japan_prefectures.json'),
        output_file=str(data_dir / 'japan_prefectures_transformed.json')
    )
