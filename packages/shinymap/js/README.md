# shinymap (JS)

Core React/TypeScript package for rendering interactive region maps. This package ships only lightweight demo geometry (simple shapes) and exposes primitives that language adapters or applications can build upon.

## Exports

- `InputMap` – interactive SVG map supporting single selection, multi-selection, cycle, and count modes.
- `OutputMap` – display map with optional click events via Display mode.
- `demoRegions` / `getDemoRegions()` – simple shape geometry useful for testing and demos.
- `renderInputMap` / `renderOutputMap` – helpers to imperatively mount the components into non-React hosts (e.g., Shiny bindings).
- Type aliases for regions, tooltips, aesthetics, and props.

## Features

- **Mode support**: single, multiple, cycle (finite state), count (unbounded/capped), display (output)
- **Hierarchical aesthetics**: base/hover/select states, per-region overrides
- **Indexed aesthetics**: array-indexed colors for cycle/count/display modes
- **Polymorphic elements**: Circle, Rect, Ellipse, Path, Polygon, Line, Text
- **Layer system**: underlays, overlays, hidden layers with automatic prefix detection
- **Value-based selection**: selection derived from `value > 0` (unified model)

## Usage

```tsx
import { InputMap, demoRegions } from "shinymap";

function Example() {
  const [value, setValue] = useState<Record<string, number>>({});

  return (
    <div style={{ width: 240, height: 240 }}>
      <InputMap
        regions={demoRegions}
        value={value}
        onChange={setValue}
        mode={{ type: "single" }}
      />
    </div>
  );
}
```

A minimal demo lives under `demo/` for local experimentation.
