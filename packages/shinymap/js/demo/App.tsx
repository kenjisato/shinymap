import React, { useMemo, useState } from "react";
import { createRoot } from "react-dom/client";

import { InputMap, OutputMap, palette } from "../src";
import type { GeometryMap, ResolveAestheticArgs, AestheticStyle } from "../src/types";
import geometry from "./geometry.json";

const TOOLTIP_MAP: Record<string, string> = {
  circle: "Circle",
  square: "Square",
  triangle: "Triangle",
};

const demoGeometry = geometry as GeometryMap;

// --- Shared section wrapper
type DemoSectionProps = {
  title: string;
  description: string;
  children: React.ReactNode;
};

function DemoSection({ title, description, children }: DemoSectionProps) {
  return (
    <section style={{ padding: "0.2rem" }}>
      <h2 style={{ margin: "0 0 0.25rem 0" }}>{title}</h2>
      <p style={{ marginTop: 0, marginBottom: "0.75rem", color: "#475569", lineHeight: 1.5 }}>{description}</p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "1rem", alignItems: "flex-start" }}>
        {children}
      </div>
    </section>
  );
}

type DemoSingleProps = {
  geometry: GeometryMap;
  tooltips: Record<string, string>;
};

// --- Single selection demo
function DemoSingle({ geometry, tooltips }: DemoSingleProps) {
  const [counts, setCounts] = useState<Record<string, number>>({ circle: 1 });

  const resolveAesthetic = ({ count, isHovered, baseAesthetic }: ResolveAestheticArgs) => {
    const next: AestheticStyle = { ...baseAesthetic };
    if (count > 0) {
      next.fillColor = palette.qualitative[0];
    }
    if (isHovered) {
      const sw = typeof next.strokeWidth === "number" ? next.strokeWidth : 1;
      next.strokeWidth = sw + 1;
    }
    return next;
  };

  return (
    <DemoSection
      title="Single selection"
      description="Click to toggle a single active region with hover feedback."
    >
      <div style={{ aspectRatio: "1", border: "1px solid #cbd5f5", borderRadius: 6, overflow: "hidden", background: "#f8fafc" }}>
        <InputMap
          mode="single"
          geometry={geometry}
          tooltips={tooltips}
          value={counts}
          onChange={setCounts}
          aes={{ base: { fillColor: palette.neutrals.fill, strokeColor: palette.neutrals.stroke } }}
          resolveAesthetic={resolveAesthetic}
        />
      </div>
      <div style={{ background: "#f8fafc", borderRadius: 8, padding: "0.75rem", border: "1px solid #e2e8f0" }}>
        <strong style={{ display: "block", marginBottom: "0.25rem" }}>Current value</strong>
        <div style={{ color: "#0f172a" }}>
          {Object.entries(counts)
            .filter(([, c]) => c > 0)
            .map(([id]) => id)
            .join(", ") || "(none)"}
        </div>
      </div>
    </DemoSection>
  );
}

type DemoMultipleProps = {
  geometry: GeometryMap;
  tooltips: Record<string, string>;
};

// --- Multiple selection demo
function DemoMultiple({ geometry, tooltips }: DemoMultipleProps) {
  const [counts, setCounts] = useState<Record<string, number>>({ square: 1 });

  const resolveAesthetic = ({ count, isHovered, baseAesthetic }: ResolveAestheticArgs) => {
    const next: AestheticStyle = { ...baseAesthetic };
    if (count > 0) {
      next.fillColor = palette.qualitative[1];
    }
    if (isHovered) {
      const sw = typeof next.strokeWidth === "number" ? next.strokeWidth : 1;
      next.strokeWidth = sw + 1;
    }
    return next;
  };

  return (
    <DemoSection
      title="Multiple selection"
      description="Multi-mode toggles membership in a set of active IDs."
    >
      <div style={{ aspectRatio: "1", border: "1px solid #cbd5f5", borderRadius: 6, overflow: "hidden", background: "#f8fafc" }}>
        <InputMap
          mode="multiple"
          geometry={geometry}
          tooltips={tooltips}
          value={counts}
          onChange={setCounts}
          aes={{ base: { fillColor: palette.neutrals.fill, strokeColor: palette.neutrals.stroke } }}
          resolveAesthetic={resolveAesthetic}
        />
      </div>
      <div style={{ background: "#f8fafc", borderRadius: 8, padding: "0.75rem", border: "1px solid #e2e8f0" }}>
        <strong style={{ display: "block", marginBottom: "0.25rem" }}>Selected IDs</strong>
        <div style={{ color: "#0f172a" }}>
          {Object.entries(counts)
            .filter(([, c]) => c > 0)
            .map(([id]) => id)
            .join(", ") || "(none)"}
        </div>
      </div>
    </DemoSection>
  );
}

type DemoCountsAlphaProps = {
  geometry: GeometryMap;
  tooltips: Record<string, string>;
};

type DemoHueCountsProps = {
  geometry: GeometryMap;
  tooltips: Record<string, string>;
};

// --- Count mode demo (alpha mapping)
function DemoCountsAlpha({ geometry, tooltips }: DemoCountsAlphaProps) {
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [countCeiling, setCountCeiling] = useState(5);

  const resolveAesthetic = ({ count, isHovered, baseAesthetic }: ResolveAestheticArgs) => {
    const next: AestheticStyle = { ...baseAesthetic };
    if (count > 0) {
      const alpha = countCeiling > 0 ? Math.min(1, count / countCeiling) : 0;
      next.fillColor = palette.sequential.orange[4];
      next.fillOpacity = 0.2 + alpha * 0.8;
    }
    if (isHovered) {
      const sw = typeof next.strokeWidth === "number" ? next.strokeWidth : 1;
      next.strokeWidth = sw + 1;
    }
    return next;
  };

  const resetCounts = () => {
    const next: Record<string, number> = {};
    Object.keys(geometry).forEach((id) => {
      next[id] = 0;
    });
    setCounts(next);
  };

  return (
    <DemoSection
      title="Click counter"
      description="Count mode uses alpha blending; change the ceiling to see ramping."
    >
      <div style={{ aspectRatio: "1", border: "1px solid #cbd5f5", borderRadius: 6, overflow: "hidden", background: "#f8fafc" }}>
        <InputMap
          mode="count"
          geometry={geometry}
          tooltips={tooltips}
          value={counts}
          onChange={setCounts}
          aes={{ base: { fillColor: palette.neutrals.fill, strokeColor: palette.neutrals.stroke } }}
          resolveAesthetic={resolveAesthetic}
        />
      </div>
      <div style={{ background: "#f8fafc", borderRadius: 8, padding: "0.75rem", border: "1px solid #e2e8f0" }}>
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginBottom: "0.5rem" }}>
          <label htmlFor="ceiling">Max count</label>
          <input
            id="ceiling"
            type="range"
            min={1}
            max={10}
            value={countCeiling}
            onChange={(e) => setCountCeiling(Number(e.target.value))}
          />
          <span>{countCeiling}</span>
        </div>
        <strong style={{ display: "block", marginBottom: "0.25rem" }}>Counts</strong>
        <div style={{ color: "#0f172a" }}>
          {Object.entries(counts).map(([id, count]) => `${id}: ${count}`).join(", ") || "(none)"}
        </div>
        <div style={{ marginTop: "0.75rem" }}>
          <button onClick={resetCounts}>Reset counts</button>
        </div>
      </div>
    </DemoSection>
  );
}

// --- Count mode demo (hue mapping)
function DemoHueCounts({ geometry, tooltips }: DemoHueCountsProps) {
  const [counts, setCounts] = useState<Record<string, number>>({});
  const hues = palette.qualitative;
  const maxValue = hues.length;

  const resolveAesthetic = ({ count, isHovered, baseAesthetic }: ResolveAestheticArgs) => {
    const next: AestheticStyle = { ...baseAesthetic };
    if (count > 0) {
      // Direct index: count 1 → hues[0], count 2 → hues[1], etc.
      const idx = Math.min(hues.length - 1, count - 1);
      next.fillColor = hues[idx] ?? hues[0];
    }
    if (isHovered) {
      const sw = typeof next.strokeWidth === "number" ? next.strokeWidth : 1;
      next.strokeWidth = sw + 1;
    }
    return next;
  };

  return (
    <DemoSection
      title="Count to hue"
      description="Map counts to a qualitative palette for quick hue-based feedback."
    >
      <div style={{ aspectRatio: "1", border: "1px solid #cbd5f5", borderRadius: 6, overflow: "hidden", background: "#f8fafc" }}>
        <InputMap
          mode="count"
          geometry={geometry}
          tooltips={tooltips}
          value={counts}
          onChange={setCounts}
          aes={{ base: { fillColor: palette.neutrals.fill, strokeColor: palette.neutrals.stroke } }}
          resolveAesthetic={resolveAesthetic}
        />
      </div>
      <div style={{ background: "#f8fafc", borderRadius: 8, padding: "0.75rem", border: "1px solid #e2e8f0" }}>
        <div style={{ display: "grid", gap: "0.5rem" }}>
          {Object.keys(geometry).map((id) => (
            <label key={id} style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <span style={{ width: 80, textTransform: "capitalize" }}>{id}</span>
              <input
                type="range"
                min={0}
                max={maxValue}
                value={counts[id] ?? 0}
                onChange={(e) => setCounts((prev) => ({ ...prev, [id]: Number(e.target.value) }))}
              />
              <span>{counts[id] ?? 0}</span>
            </label>
          ))}
        </div>
        <div style={{ marginTop: "0.75rem" }}>
          <button onClick={() => setCounts({})}>Reset counts</button>
        </div>
      </div>
    </DemoSection>
  );
}

type DemoOutputProps = {
  geometry: GeometryMap;
  tooltips: Record<string, string>;
};

// --- Output map demo
function DemoOutput({ geometry, tooltips }: DemoOutputProps) {
  const [values, setValues] = useState<Record<string, number>>({ circle: 5, square: 3, triangle: 7 });
  const [maxValue, setMaxValue] = useState(10);

  const setValueFor = (id: string, val: number) => {
    setValues((prev) => ({ ...prev, [id]: val }));
  };

  const styleForRegion = ({ id, baseAesthetic }: { id: string; baseAesthetic: AestheticStyle }) => {
    const value = values[id] ?? 0;
    const alpha = maxValue > 0 ? Math.max(0, Math.min(1, value / maxValue)) : 0;
    if (value <= 0) {
      return { fillColor: palette.neutrals.fill, fillOpacity: 1 };
    }
    return {
      fillColor: baseAesthetic.fillColor,
      fillOpacity: 0.2 + alpha * 0.8,
    };
  };

  const fills = useMemo(
    () => ({
      circle: palette.sequential.blue[2],
      square: palette.sequential.green[2],
      triangle: palette.sequential.orange[4],
    }),
    []
  );

  const resetValues = () => {
    setValues({ circle: 0, square: 0, triangle: 0 });
  };

  return (
    <DemoSection
      title="Output map"
      description="Provide fills and optionally a styleForRegion callback to control appearance."
    >
      <div style={{ background: "#f8fafc", borderRadius: 8, padding: "0.75rem", border: "1px solid #e2e8f0" }}>
        <div style={{ display: "grid", gap: "0.5rem" }}>
          {["circle", "square", "triangle"].map((id) => (
            <label key={id} style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <span style={{ width: 80, textTransform: "capitalize" }}>{id}</span>
              <input
                type="range"
                min={0}
                max={maxValue}
                value={values[id] ?? 0}
                onChange={(e) => setValueFor(id, Number(e.target.value))}
              />
              <span>{values[id] ?? 0}</span>
            </label>
          ))}
        </div>
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginTop: "0.75rem" }}>
          <label htmlFor="max-value">Max value</label>
          <input
            id="max-value"
            type="range"
            min={1}
            max={20}
            value={maxValue}
            onChange={(e) => setMaxValue(Number(e.target.value))}
          />
          <span>{maxValue}</span>
        </div>
        <div style={{ marginTop: "0.75rem" }}>
          <button onClick={resetValues}>Reset values</button>
        </div>
      </div>
      <div style={{ aspectRatio: "1", border: "1px solid #cbd5f5", borderRadius: 6, overflow: "hidden", background: "#f8fafc" }}>
        <OutputMap
          geometry={geometry}
          tooltips={tooltips}
          fillColor={fills}
          value={values}
          resolveAesthetic={({ id, baseAesthetic }) => styleForRegion({ id, baseAesthetic })}
        />
      </div>
    </DemoSection>
  );
}

const singleContainer = document.getElementById("root-single");
if (singleContainer) {
  createRoot(singleContainer).render(<DemoSingle geometry={demoGeometry} tooltips={TOOLTIP_MAP} />);
}

const multipleContainer = document.getElementById("root-multiple");
if (multipleContainer) {
  createRoot(multipleContainer).render(<DemoMultiple geometry={demoGeometry} tooltips={TOOLTIP_MAP} />);
}

const countsContainer = document.getElementById("root-counts");
if (countsContainer) {
  createRoot(countsContainer).render(
    <>
      <DemoCountsAlpha geometry={demoGeometry} tooltips={TOOLTIP_MAP} />
      <DemoHueCounts geometry={demoGeometry} tooltips={TOOLTIP_MAP} />
    </>
  );
}

const outputContainer = document.getElementById("root-output");
if (outputContainer) {
  createRoot(outputContainer).render(<DemoOutput geometry={demoGeometry} tooltips={TOOLTIP_MAP} />);
}
