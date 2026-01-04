"""Example: StillLife for static analysis and SVG export.

This script demonstrates how to use StillLife for:
1. Inspecting resolved aesthetics without running a Shiny app
2. Exporting static SVGs with specific selection/hover states

Run this script directly:
    uv run python packages/shinymap/python/examples/example_stilllife.py
"""

from pathlib import Path

from shinymap import Outline, StillLife, Wash, aes

# Define a simple outline with three shapes
outline = Outline.from_dict({
    "circle": ["M25,50 A20,20 0 1 1 24.999,50 Z"],
    "square": ["M55 15 H85 V45 H55 Z"],
    "triangle": ["M75 70 L90 55 L60 55 Z"],
    "_metadata": {"viewBox": "0 0 100 100"},
})

# Create a wash with custom aesthetics
wc = Wash(
    shape=aes.ByState(
        base=aes.Shape(fill_color="#e2e8f0", stroke_color="#94a3b8", stroke_width=1.0),
        select=aes.Shape(fill_color="#3b82f6", stroke_color="#1e40af"),
        hover=aes.Shape(stroke_width=2.0),
    )
)

# Build a MapBuilder with specific values
# value > 0 means selected
builder = wc.build(outline, value={"circle": 1, "square": 0, "triangle": 2})


def example_aes():
    """Example 1: Inspect resolved aesthetics."""
    print("=" * 60)
    print("Example 1: Inspecting resolved aesthetics")
    print("=" * 60)

    # Create StillLife for static analysis
    pic = StillLife(builder)

    # Inspect individual regions
    print("\nCircle (selected, value=1):")
    circle_aes = pic.aes("circle")
    print(f"  fill_color: {circle_aes['fill_color']}")
    print(f"  stroke_color: {circle_aes['stroke_color']}")

    print("\nSquare (not selected, value=0):")
    square_aes = pic.aes("square")
    print(f"  fill_color: {square_aes['fill_color']}")
    print(f"  stroke_color: {square_aes['stroke_color']}")

    print("\nTriangle (selected, value=2):")
    triangle_aes = pic.aes("triangle")
    print(f"  fill_color: {triangle_aes['fill_color']}")


def example_aes_table():
    """Example 2: Get aesthetics for all regions."""
    print("\n" + "=" * 60)
    print("Example 2: Aesthetics table for all regions")
    print("=" * 60)

    pic = StillLife(builder)
    table = pic.aes_table()

    print("\nAll regions:")
    for row in table:
        region_id = row["region_id"]
        fill = row["fill_color"]
        stroke = row["stroke_color"]
        print(f"  {region_id}: fill={fill}, stroke={stroke}")


def example_hover():
    """Example 3: Inspect hover state aesthetics."""
    print("\n" + "=" * 60)
    print("Example 3: Hover state aesthetics")
    print("=" * 60)

    # Create StillLife with square hovered
    pic = StillLife(builder, hovered="square")

    print("\nSquare (hovered, not selected):")
    square_aes = pic.aes("square")
    print(f"  stroke_width: {square_aes['stroke_width']} (hover increases to 2.0)")

    # Or check hover state explicitly
    pic2 = StillLife(builder)
    print("\nUsing is_hovered parameter:")
    print(f"  Normal: stroke_width={pic2.aes('square')['stroke_width']}")
    print(f"  Hovered: stroke_width={pic2.aes('square', is_hovered=True)['stroke_width']}")


def example_svg_export():
    """Example 4: Export static SVG."""
    print("\n" + "=" * 60)
    print("Example 4: SVG export")
    print("=" * 60)

    # Export with current state
    pic = StillLife(builder)
    svg_str = pic.to_svg()
    print(f"\nSVG string (first 200 chars):\n  {svg_str[:200]}...")

    # Export with hover state
    pic_hover = StillLife(builder, hovered="triangle")

    # Save to file
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    svg_path = output_dir / "stilllife_example.svg"
    pic_hover.to_svg(output=svg_path)
    print(f"\nSVG saved to: {svg_path}")


def example_override_value():
    """Example 5: Override value for different scenarios."""
    print("\n" + "=" * 60)
    print("Example 5: Override value parameter")
    print("=" * 60)

    # Original builder has {"circle": 1, "square": 0, "triangle": 2}
    # Create StillLife with different value
    pic = StillLife(builder, value={"circle": 0, "square": 1, "triangle": 0})

    print("\nWith overridden value (square selected):")
    for region in ["circle", "square", "triangle"]:
        fill = pic.aes(region)["fill_color"]
        status = "selected" if pic.aes(region)["fill_color"] == "#3b82f6" else "not selected"
        print(f"  {region}: {status} ({fill})")


if __name__ == "__main__":
    example_aes()
    example_aes_table()
    example_hover()
    example_svg_export()
    example_override_value()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
