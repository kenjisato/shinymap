# shinyjpmap

Shiny for Python input/output components for a Japan prefecture map.

## API

```python
import shinyjpmap as jp
from shiny import App, Inputs, Outputs, Session, render, ui

df = ...  # DataFrame with columns pref_code, color, tip

app_ui = ui.page_fluid(
    jp.input_map(
        "pref_in",
        regions=["Tohoku", "Hokkaido"],
        okinawa="bottomright",
        map_width="360px",
        map_height="360px",
    ),
    jp.output_map("pref_out"),
    ui.output_text("clicked"),
)

def server(input: Inputs, output: Outputs, session: Session):
    @output
    @render.ui
    def pref_out():
        img = jp.map(
            df,
            color="color",
            tooltip="tip",
            map_width="360px",
            map_height="360px",
            palette="viridis",
        )
        return img.as_ui()

    @output
    @render.text
    def clicked():
        value = input.pref_in()
        return f"clicked: {value}" if value else "clicked: (none)"

app = App(app_ui, server=server)
```

---

### Notes

- Geometry paths for all 47 prefectures ship with the package (`src/shinyjpmap/data/pref_paths.json`).
- `scripts/geojson_to_svg_paths.py` converts GeoJSON input into the packaged SVG paths.
- Prefecture outlines derive from `piuccio/open-data-jp-prefectures-geojson` (MIT).
- Okinawa can render in-place or as an inset (`original`, `topleft`, `bottomright`) with omission line support.
- Set `map_width`/`map_height` to control the rendered SVG footprint independently from the container size.
- Use the `palette` argument with `jp.map(...)` to transform numeric or categorical data into colors automatically (built-in options include `viridis`, `magma`, `plasma`, `cividis`, `tab10`, and `pastel`).
- Use `jp.map(...)` to generate an SVG or PNG on demand. The result exposes helpers such as `.as_ui()` (for `render.ui`) and `.as_data_url()` / `.as_image()` for image outputs. PNG support requires the optional `cairosvg` dependency.
- Input maps emit `pref_code` strings (`"01"`–`"47"`) via `Shiny.setInputValue` on click and highlight on hover.
- Color output supports basic tooltips, default fills, a minimal SVG colorbar, and parity with `jp.export_svg(...)`.

### Geometry maintenance

Prefecture boundary data is adapted from the MIT-licensed repository `piuccio/open-data-jp-prefectures-geojson`.

Run `scripts/refresh_geometry.sh` to download the latest GeoJSON, regenerate `pref_paths.json`, and rebuild the JavaScript bundle. The raw download is kept at `data/prefectures.geojson` (ignored by git) so collaborators can iterate without bloating the repository.

