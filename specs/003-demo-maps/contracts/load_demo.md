# Contract: `shinymap.outline.load_demo`

```python
def load_demo(name: Literal["world", "us_states", "japan"]) -> Outline
```

- Returns a new `Outline` each call (callers may transform it freely).
- Unknown `name` → `ValueError` listing the valid names.
- Works offline; reads only files inside the installed package.
- Region IDs and metadata as in [../data-model.md](../data-model.md).
- Exported from `shinymap.outline`; listed in the quartodoc reference.

Usage the docs must show (SC-001):

```python
from shinymap import input_map
from shinymap.outline import load_demo

input_map("state", load_demo("us_states"), mode="single")
```

# Contract change: `Outline.from_svg`

- Two elements with the same `id` → `ValueError` naming the ID and the file. Previously the later element replaced the earlier one silently.
