import React from "react";
import { createRoot } from "react-dom/client";

import { OutputMap, palette } from "../src";
import type { GeometryMap } from "../src/types";
import geometry from "./geometry.json";

const demoGeometry = geometry as GeometryMap;

const SWATCHES: Array<{ name: string; colors: string[] }> = [
  { name: "Qualitative", colors: palette.qualitative },
  { name: "Sequential (blue)", colors: palette.sequential.blue },
  { name: "Sequential (green)", colors: palette.sequential.green },
  { name: "Sequential (orange)", colors: palette.sequential.orange },
];

function PaletteDemo() {
  // Per-region fill colors
  const fillColor = {
    circle: palette.sequential.blue[3],
    square: palette.sequential.green[3],
    triangle: palette.sequential.orange[3],
  };

  // Values determine selection state (value > 0 = selected)
  const value = {
    circle: 1, // selected
    square: 0,
    triangle: 0,
  };

  return (
    <div style={{ display: "grid", gap: "1rem", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}>
      <section style={{ padding: "0.75rem", background: "#fff", borderRadius: 8, boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
        <h2 style={{ marginTop: 0 }}>Palette swatches</h2>
        <div style={{ display: "grid", gap: "0.75rem" }}>
          {SWATCHES.map((swatch) => (
            <div key={swatch.name}>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>{swatch.name}</div>
              <div style={{ display: "flex", gap: 6 }}>
                {swatch.colors.map((c) => (
                  <div key={c} style={{ width: 28, height: 28, borderRadius: 4, background: c, border: "1px solid #e2e8f0" }} />
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section style={{ padding: "0.75rem", background: "#fff", borderRadius: 8, boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
        <h2 style={{ marginTop: 0 }}>Palette applied to map</h2>
        <p style={{ marginTop: 0, color: "#475569" }}>Using sequential palettes for fills; adjust in your app as needed.</p>
        <div style={{ aspectRatio: "1", border: "1px solid #cbd5f5", borderRadius: 6, overflow: "hidden" }}>
          <OutputMap
            geometry={demoGeometry}
            fillColor={fillColor}
            value={value}
            containerStyle={{ width: "100%", height: "100%" }}
          />
        </div>
      </section>
    </div>
  );
}

const container = document.getElementById("root");
if (container) {
  const root = createRoot(container);
  root.render(<PaletteDemo />);
}
