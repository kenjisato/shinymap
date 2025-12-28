# shinymap (JS)

Core React/TypeScript package for rendering interactive region maps. This package ships only lightweight demo geometry (simple shapes) and exposes primitives that language adapters or applications can build upon.

## Exports

- `InputMap` – interactive SVG map supporting single selection, multi-selection, cycle, and count modes.
- `OutputMap` – read-only map that renders fills/highlights based on server/state payloads.
- `demoGeometry` / `getDemoGeometry()` – simple shape geometry useful for testing and demos.
- `renderInputMap` / `renderOutputMap` – helpers to imperatively mount the components into non-React hosts (e.g., Shiny bindings).
- Type aliases for geometry, tooltips, aesthetics, and props.

## Features (v0.2.0)

- **Mode support**: single, multiple, cycle (finite state), count (unbounded/capped)
- **Hierarchical aesthetics**: base/hover/select states, per-region overrides
- **Indexed aesthetics**: array-indexed colors for cycle/count modes
- **Polymorphic elements**: Circle, Rect, Ellipse, Path, Polygon, Line, Text
- **Layer system**: underlays, overlays, hidden layers with automatic prefix detection

## Usage

```tsx
import { InputMap, demoGeometry } from "shinymap";

function Example() {
  const [value, setValue] = useState<Record<string, number>>({});

  return (
    <div style={{ width: 240, height: 240 }}>
      <InputMap
        geometry={demoGeometry}
        value={value}
        onChange={setValue}
        modeConfig={{ type: "single" }}
      />
    </div>
  );
}
```

A minimal demo lives under `demo/` for local experimentation.
