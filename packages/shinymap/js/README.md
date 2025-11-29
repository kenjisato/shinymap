# shinymap (JS)

Core React/TypeScript package for rendering interactive region maps. This package ships only lightweight demo geometry (simple shapes) and exposes primitives that language adapters or applications can build upon.

## Exports

- `InputMap` – interactive SVG map supporting single selection, multi-selection, and click-count modes.
- `OutputMap` – read-only map that renders fills/highlights based on server/state payloads.
- `demoGeometry` / `getDemoGeometry()` – simple shape geometry useful for testing and demos.
- `renderInputMap` / `renderOutputMap` – helpers to imperatively mount the components into non-React hosts (e.g., Shiny bindings).
- Type aliases for geometry, tooltips, and props.

## Usage

```tsx
import { InputMap, demoGeometry } from "shinymap";

function Example() {
  const [value, setValue] = useState<string | null>(null);

  return (
    <div style={{ width: 240, height: 240 }}>
      <InputMap geometry={demoGeometry} value={value} onChange={setValue} />
    </div>
  );
}
```

A minimal demo lives under `demo/` for local experimentation.
