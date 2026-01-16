"""Generate reference SVG with region ID labels overlaid.

Usage:
    uv run python -m shinymap.kit.caption INPUT [-o OUTPUT] [options]

Arguments:
    INPUT                     Path to SVG or JSON file

Options:
    -o, --output PATH         Output SVG path (default: {input}_labeled.svg)
    -s, --font-size SIZE      Font size: absolute (e.g., '5') or percentage of
                              viewBox (e.g., '3%'); default: 3%
    -c, --color COLOR         Text color (default: #333)
    -e, --exclude ID          Region IDs to exclude (can be repeated)

Examples:
    # Basic usage - generates map_labeled.svg (3% of viewBox)
    uv run python -m shinymap.kit.caption map.svg

    # Custom output path
    uv run python -m shinymap.kit.caption map.svg -o reference.svg

    # Absolute font size
    uv run python -m shinymap.kit.caption map.svg -s 5 -c red

    # Percentage-based font size (2% of smaller viewBox dimension)
    uv run python -m shinymap.kit.caption map.svg -s 2%

    # Exclude specific regions
    uv run python -m shinymap.kit.caption map.svg -e _border -e _grid
"""

import argparse
from pathlib import Path

from shinymap.kit import describe, glaze
from shinymap.outline import Outline, export_svg


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate reference SVG with region ID labels overlaid",
        prog="python -m shinymap.kit.caption",
    )
    parser.add_argument(
        "input",
        type=str,
        help="Path to SVG or JSON file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output SVG path (default: {input}_labeled.svg)",
    )
    parser.add_argument(
        "-s",
        "--font-size",
        type=str,
        default="3%",
        help="Font size: '5' (absolute) or '3%%' (%% of viewBox); default: 3%%",
    )
    parser.add_argument(
        "-c",
        "--color",
        type=str,
        default="#333",
        help="Text color (default: #333)",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        type=str,
        action="append",
        default=[],
        help="Region IDs to exclude (can be repeated)",
    )

    args = parser.parse_args()

    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    suffix = input_path.suffix.lower()
    if suffix not in [".svg", ".json"]:
        raise ValueError(f"Unsupported file type: {suffix}")

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_stem(f"{input_path.stem}_labeled").with_suffix(".svg")

    # Load outline
    if suffix == ".svg":
        outline = Outline.from_svg(input_path)
    else:
        outline = Outline.from_json(input_path)

    # Generate labels
    labels = describe(
        outline,
        exclude=args.exclude if args.exclude else None,
        font_size=args.font_size,
        fill=args.color,
    )

    # Merge labels into outline
    labeled = glaze(outline, labels)

    # Export
    export_svg(labeled, output_path)

    print(f"Generated: {output_path}")


if __name__ == "__main__":
    main()
