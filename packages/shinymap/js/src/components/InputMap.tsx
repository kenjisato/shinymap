import React, { useMemo, useState } from "react";

import type { AestheticStyle, InputMapMode, InputMapProps, RegionId } from "../types";

const DEFAULT_VIEWBOX = "0 0 100 100";
const DEFAULT_AESTHETIC: AestheticStyle = {
  fillColor: "#e2e8f0",
  fillOpacity: 1,
  strokeColor: "#334155",
  strokeWidth: 1,
};

function buildSelected(value: Record<RegionId, number> | undefined): Set<RegionId> {
  const set = new Set<RegionId>();
  if (!value) return set;
  Object.entries(value).forEach(([id, val]) => {
    if (val > 0) set.add(id);
  });
  return set;
}

export function InputMap(props: InputMapProps) {
  const {
    geometry,
    tooltips,
    fills,
    className,
    containerStyle,
    viewBox = DEFAULT_VIEWBOX,
    defaultAesthetic = DEFAULT_AESTHETIC,
    resolveAesthetic,
    regionProps,
    value,
    onChange,
    cycle,
    maxSelection,
  } = props;

  const [hovered, setHovered] = useState<RegionId | null>(null);
  // Use internal state for counts, initialized from value prop
  const [counts, setCounts] = useState<Record<RegionId, number>>(value ?? {});
  const selected = useMemo(() => buildSelected(counts), [counts]);
  // Determine mode: explicit prop wins; else cycle implies count; else multiple.
  const mode: InputMapMode = props.mode ?? (cycle ? "count" : "multiple");
  const effectiveCycle =
    cycle ?? (mode === "single" ? 2 : mode === "multiple" ? 2 : mode === "count" ? Infinity : 2);
  const effectiveMax =
    maxSelection ??
    (mode === "single"
      ? 1
      : mode === "multiple"
        ? Infinity
        : mode === "count"
          ? Infinity
          : Infinity);

  const handleClick = (id: RegionId) => {
    const current = counts[id] ?? 0;
    const nextCount =
      effectiveCycle && Number.isFinite(effectiveCycle) && effectiveCycle > 0
        ? (current + 1) % effectiveCycle
        : current + 1;

    const activeCount = selected.size;
    const isActivating = current === 0 && nextCount > 0;
    const maxSel = Number.isFinite(effectiveMax) ? effectiveMax : Infinity;
    if (isActivating && activeCount >= maxSel) {
      if (maxSel === 1) {
        // Replace the active region with the newly clicked one.
        const next = Object.fromEntries(
          Object.keys(geometry).map((key) => [key, key === id ? nextCount : 0])
        );
        setCounts(next);
        onChange?.(next);
      }
      // If maxSelection is >1, block new activation to avoid surprise replacements.
      return;
    }

    const next = { ...counts, [id]: nextCount };
    setCounts(next);
    onChange?.(next);
  };

  return (
    <svg
      role="img"
      className={className}
      style={{ width: "100%", height: "100%", ...containerStyle }}
      viewBox={viewBox}
    >
      <g>
        {Object.entries(geometry).map(([id, d]) => {
          const tooltip = tooltips?.[id];
          const isHovered = hovered === id;
          const isSelected = selected.has(id);
          const count = counts[id] ?? 0;

          let resolved: AestheticStyle = { ...DEFAULT_AESTHETIC, ...defaultAesthetic };

          // Apply fills if provided
          if (fills && fills[id]) {
            resolved.fillColor = fills[id];
          }

          if (resolveAesthetic) {
            const overrides = resolveAesthetic({
              id,
              mode,
              isHovered,
              isSelected,
              count,
              baseAesthetic: resolved,
            });
            if (overrides) {
              resolved = { ...resolved, ...overrides };
            }
          }

          const extraProps = regionProps?.({
            id,
            mode,
            isHovered,
            isSelected,
            count,
            baseAesthetic: resolved,
          });

          const handleMouseEnter = () => setHovered(id);
          const handleMouseLeave = () => setHovered((current) => (current === id ? null : current));

          return (
            <path
              key={id}
              d={d}
              fill={resolved.fillColor}
              fillOpacity={resolved.fillOpacity}
              stroke={resolved.strokeColor}
              strokeWidth={resolved.strokeWidth}
              style={{ cursor: "pointer" }}
              onMouseEnter={handleMouseEnter}
              onMouseLeave={handleMouseLeave}
              onFocus={handleMouseEnter}
              onBlur={handleMouseLeave}
              onClick={() => handleClick(id)}
              {...extraProps}
            >
              {tooltip ? <title>{tooltip}</title> : null}
            </path>
          );
        })}
      </g>
    </svg>
  );
}
