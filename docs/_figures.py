"""Generate the static figures used across the docs site.

Run by Quarto as a pre-render script (see `_quarto.yml`). Every SVG is drawn
by shinymap itself via `Wash.build()` + `StillLife.to_svg()`, so the pictures
always match the library's rendering. Output goes to `images/generated/`
(git-ignored).

"""

import math
import re
from pathlib import Path

from shinymap import Outline, StillLife, Wash, aes
from shinymap.mode import Count, Cycle
from shinymap.aes.color import (
    scale_continuous,
    scale_diverging,
    scale_qualitative,
    scale_sequential,
)
from shinymap import default_wash  # the look users get by default

OUT = Path(__file__).parent / "images" / "generated"

# ---------------------------------------------------------------------------
# Outlines
# ---------------------------------------------------------------------------


def hex_paths(cols: int, rows: int, r: float = 10.0, x0: float = 1, y0: float = 1):
    """Pointy-top hexagon tiling: any SVG paths work, not just maps."""
    w = math.sqrt(3) * r
    regions: dict[str, list[str]] = {}
    for row in range(rows):
        for col in range(cols):
            cx = x0 + w * (col + 0.5 * (row % 2)) + w / 2
            cy = y0 + 1.5 * r * row + r
            pts = [
                (
                    cx + r * math.cos(math.radians(30 + 60 * k)),
                    cy + r * math.sin(math.radians(30 + 60 * k)),
                )
                for k in range(6)
            ]
            regions[f"r{row * cols + col}"] = [
                "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts) + " Z"
            ]
    width = x0 + w * (cols + 0.5) + 1
    height = y0 + 1.5 * r * (rows - 1) + 2 * r + 1
    return regions, width, height


def hex_grid(cols: int = 5, rows: int = 4, **metadata) -> Outline:
    regions, w, h = hex_paths(cols, rows)
    return Outline.from_dict(
        {**regions, "_metadata": {"viewBox": f"0 0 {w:.1f} {h:.1f}", **metadata}}
    )


HEX = hex_grid()
IDS = list(HEX.regions)

# Two groups (top two rows / bottom two rows) for the ByGroup figures
HEX_GROUPS = hex_grid(groups={"north": IDS[:10], "south": IDS[10:]})

# Hex grid with an underlay background and an open path ("river") on top
_regions, _w, _h = hex_paths(5, 4, x0=6, y0=6)
_W, _H = _w + 5, _h + 5
LAYERED = Outline.from_dict(
    {
        "_background": [f"M0 0 H{_W:.1f} V{_H:.1f} H0 Z"],
        **_regions,
        "_river": [
            f"M2 {_H * 0.75:.1f} C{_W * 0.3:.1f} {_H * 0.2:.1f} {_W * 0.6:.1f} {_H:.1f} {_W - 2:.1f} {_H * 0.3:.1f}"
        ],
        "_metadata": {"viewBox": f"0 0 {_W:.1f} {_H:.1f}"},
    }
).move_layer("underlay", "_background")

# ---------------------------------------------------------------------------
# Washes
# ---------------------------------------------------------------------------

WASH = Wash(
    shape=aes.ByState(
        base=aes.Shape(fill_color="#e2e8f0", stroke_color="#ffffff", stroke_width=1.5),
        select=aes.Shape(
            fill_color="#3b82f6", stroke_color="#1e40af", stroke_width=1.5
        ),
        hover=aes.Shape(stroke_color="#0f172a", stroke_width=2.5),
    ),
    line=aes.Line(stroke_color="#0284c7", stroke_width=2.5),
)

CYCLE_COLORS = ["#e2e8f0", "#86efac", "#fde047", "#f87171"]  # Cycle(n=4)
COUNT_COLORS = ["#e2e8f0", "#bfdbfe", "#93c5fd", "#60a5fa", "#3b82f6", "#1d4ed8"]


def save(
    name: str, outline: Outline = HEX, wash=WASH, *, hovered=None, **build
) -> None:
    builder = wash.build(outline, **build)
    svg = StillLife(builder, hovered=hovered).to_svg()
    # Drop the fixed width/height (viewBox units) so the page decides the size
    svg = re.sub(r'^(<svg[^>]*?) width="[^"]*" height="[^"]*"', r"\1", svg, count=1)
    (OUT / f"{name}.svg").write_text(svg)


def fills(colors: dict[str, str]) -> aes.ByGroup:
    return aes.ByGroup(**{rid: aes.Shape(fill_color=c) for rid, c in colors.items()})


# ---------------------------------------------------------------------------
# Figures, by page
# ---------------------------------------------------------------------------


def home() -> None:
    save("single", value={"r7": 1})
    save("multiple", value={"r1": 1, "r8": 1, "r12": 1, "r16": 1})
    save("hover", value={"r11": 1}, hovered="r12")
    counts = {rid: (i * 7) % 6 for i, rid in enumerate(IDS)}
    save("choropleth", aes=fills(scale_sequential(counts, IDS, max_count=5)))


def getting_started() -> None:
    # Same outline as the code on the page, with the library's default look
    outline = Outline.from_dict(
        {
            "region_a": [{"type": "rect", "x": 10, "y": 10, "width": 30, "height": 30}],
            "region_b": [{"type": "rect", "x": 50, "y": 10, "width": 30, "height": 30}],
            "region_c": [{"type": "rect", "x": 30, "y": 50, "width": 30, "height": 30}],
            "_metadata": {"viewBox": "0 0 100 100"},
        }
    )
    save("gs-before", outline, default_wash)
    save("gs-hover", outline, default_wash, hovered="region_b")
    save("gs-after", outline, default_wash, value={"region_b": 1})


def modes() -> None:
    save("mode-single", value={"r7": 1})
    save("mode-multiple", value={"r1": 1, "r8": 1, "r12": 1, "r16": 1})
    cycle = {rid: (i * 3) % 4 for i, rid in enumerate(IDS)}
    save(
        "mode-cycle",
        mode=Cycle(n=4, aes=aes.Indexed(fill_color=CYCLE_COLORS)),
        value=cycle,
    )
    count = {"r2": 1, "r6": 3, "r7": 5, "r8": 2, "r12": 4, "r13": 1}
    save(
        "mode-count", mode=Count(aes=aes.Indexed(fill_color=COUNT_COLORS)), value=count
    )


def aesthetics() -> None:
    # ByState: the same region in each state
    save("state-base")
    save("state-hover", hovered="r7")
    save("state-select", value={"r7": 1})

    # ByGroup: groups come from the outline's metadata
    save(
        "bygroup",
        HEX_GROUPS,
        aes=aes.ByGroup(
            north=aes.Shape(fill_color="#fde68a"),
            south=aes.Shape(fill_color="#a7f3d0"),
        ),
    )

    # Precedence: each step adds a more specific entry on top of the last
    steps = [
        ("prec-1-wash", aes.ByGroup()),
        ("prec-2-all", aes.ByGroup(__all=aes.Shape(fill_color="#c7d2fe"))),
        (
            "prec-3-group",
            aes.ByGroup(
                __all=aes.Shape(fill_color="#c7d2fe"),
                north=aes.Shape(fill_color="#fde68a"),
            ),
        ),
        (
            "prec-4-region",
            aes.ByGroup(
                __all=aes.Shape(fill_color="#c7d2fe"),
                north=aes.Shape(fill_color="#fde68a"),
                r7=aes.Shape(fill_color="#f87171"),
            ),
        ),
    ]
    for name, a in steps:
        save(name, HEX_GROUPS, aes=a)

    # Color scales
    counts = {rid: (i * 7) % 6 for i, rid in enumerate(IDS)}
    save("scale-sequential", aes=fills(scale_sequential(counts, IDS, max_count=5)))
    data = {rid: 10.0 + (i * 37) % 90 for i, rid in enumerate(IDS) if i % 9 != 4}
    save("scale-continuous", aes=fills(scale_continuous(data, IDS, vmin=0, vmax=100)))
    values = {rid: (i % 5) - 2.0 for i, rid in enumerate(IDS)}
    save("scale-diverging", aes=fills(scale_diverging(values, IDS)))
    cats = {rid: ["A", "B", "C", None][i % 4] for i, rid in enumerate(IDS)}
    save("scale-qualitative", aes=fills(scale_qualitative(cats, IDS)))


def layers() -> None:
    bg = aes.ByGroup(
        _background=aes.Shape(fill_color="#e0f2fe", stroke_color="#e0f2fe")
    )
    lined = LAYERED.path_as_line("_river").move_layer("overlay", "_river")
    base_only = Outline.from_dict(
        {k: v for k, v in LAYERED.to_dict().items() if k != "_river"}
    )
    underlay_only = Outline.from_dict(
        {
            "_background": LAYERED.to_dict()["_background"],
            "_metadata": LAYERED.to_dict()["_metadata"],
        }
    ).move_layer("underlay", "_background")

    save("layer-1-underlay", underlay_only, aes=bg)
    save("layer-2-base", base_only, aes=bg)
    save("layer-3-overlay", lined, aes=bg)
    save("layer-4-select", lined, aes=bg, value={"r7": 1, "r8": 1})
    save("layer-5-hover", lined, aes=bg, value={"r7": 1, "r8": 1}, hovered="r12")

    # Annotation: a marker on the hovered region stays above the hover outline
    w = math.sqrt(3) * 10
    pin = {"type": "circle", "cx": 6 + 2 * w + w / 2, "cy": 6 + 30 + 10, "r": 3.5}
    pinned = Outline.from_dict({**lined.to_dict(), "_pin": [pin]})
    pinned = pinned.path_as_line("_river").move_layer("overlay", "_river")
    pinned = pinned.move_layer("annotation", "_pin")
    save(
        "layer-6-annotation",
        pinned,
        aes=aes.ByGroup(
            _background=aes.Shape(fill_color="#e0f2fe", stroke_color="#e0f2fe"),
            _pin=aes.Shape(
                fill_color="#f97316", stroke_color="#ffffff", stroke_width=1
            ),
        ),
        value={"r7": 1, "r8": 1},
        hovered="r12",
    )

    # The same open path without and with path_as_line()
    save("line-as-shape", LAYERED.move_layer("overlay", "_river"), aes=bg)
    save("line-as-line", lined, aes=bg)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    home()
    getting_started()
    modes()
    aesthetics()
    layers()


if __name__ == "__main__":
    main()
