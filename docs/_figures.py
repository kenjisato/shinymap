"""Generate the static figures shown on the docs home page.

Run by Quarto as a pre-render script (see `_quarto.yml`). The SVGs are drawn
by shinymap itself via `StillLife.to_svg()`, so they always match the
released rendering. Output goes to `images/generated/` (git-ignored).
"""

import math
from pathlib import Path

from shinymap import Outline, StillLife, Wash, aes
from shinymap.aes.color import scale_sequential

OUT = Path(__file__).parent / "images" / "generated"


def hex_grid(cols: int, rows: int, r: float = 10.0) -> Outline:
    """A pointy-top hexagon tiling: any SVG paths work, not just maps."""
    w = math.sqrt(3) * r
    regions: dict[str, list[str]] = {}
    for row in range(rows):
        for col in range(cols):
            cx = w * (col + 0.5 * (row % 2)) + w / 2 + 1
            cy = 1.5 * r * row + r + 1
            pts = [
                (cx + r * math.cos(math.radians(30 + 60 * k)),
                 cy + r * math.sin(math.radians(30 + 60 * k)))
                for k in range(6)
            ]
            d = "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts) + " Z"
            regions[f"r{row * cols + col}"] = [d]
    width = w * (cols + 0.5) + 2
    height = 1.5 * r * (rows - 1) + 2 * r + 2
    return Outline.from_dict({**regions, "_metadata": {"viewBox": f"0 0 {width:.1f} {height:.1f}"}})


OUTLINE = hex_grid(cols=5, rows=4)
IDS = list(OUTLINE.regions)

WASH = Wash(
    shape=aes.ByState(
        base=aes.Shape(fill_color="#e2e8f0", stroke_color="#ffffff", stroke_width=1.5),
        select=aes.Shape(fill_color="#3b82f6", stroke_color="#1e40af", stroke_width=1.5),
        hover=aes.Shape(stroke_color="#0f172a", stroke_width=2.5),
    )
)


def save(name: str, **build_kwargs) -> None:
    hovered = build_kwargs.pop("hovered", None)
    builder = WASH.build(OUTLINE, **build_kwargs)
    StillLife(builder, hovered=hovered).to_svg(OUT / f"{name}.svg")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # input_map(mode="single"): one region selected, like a radio button
    save("single", value={"r7": 1})

    # input_map(mode="multiple"): several regions selected, like checkboxes
    save("multiple", value={"r1": 1, "r8": 1, "r12": 1, "r16": 1})

    # Hover highlight drawn on top of its neighbours
    save("hover", value={"r11": 1}, hovered="r12")

    # output_map: a choropleth from counts
    counts = {rid: (i * 7) % 6 for i, rid in enumerate(IDS)}
    fills = scale_sequential(counts, IDS, max_count=5)
    save("choropleth", aes=aes.ByGroup(**{rid: aes.Shape(fill_color=c) for rid, c in fills.items()}))


if __name__ == "__main__":
    main()
