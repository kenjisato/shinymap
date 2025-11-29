import React from "react";

import type { AestheticStyle, OutputMapProps, RegionId } from "../types";

const DEFAULT_VIEWBOX = "0 0 100 100";
const DEFAULT_AESTHETIC: AestheticStyle = {
  fillColor: "#e2e8f0",
  fillOpacity: 1,
  strokeColor: "#334155",
  strokeWidth: 1,
};

function normalizeActive(active: OutputMapProps["activeIds"]): Set<RegionId> {
  if (!active) return new Set();
  if (Array.isArray(active)) return new Set(active);
  return new Set([active]);
}

export function OutputMap(props: OutputMapProps) {
  const {
    geometry,
    tooltips,
    className,
    containerStyle,
    viewBox = DEFAULT_VIEWBOX,
    defaultAesthetic = DEFAULT_AESTHETIC,
    fills,
    counts,
    activeIds,
    onRegionClick,
    resolveAesthetic,
    regionProps,
  } = props;

  const activeSet = normalizeActive(activeIds);
  const countMap = counts ?? {};

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
          const isActive = activeSet.has(id);
          const count = countMap[id] ?? 0;

          let resolved: AestheticStyle = {
            ...DEFAULT_AESTHETIC,
            ...defaultAesthetic,
            ...(fills?.[id] ? { fillColor: fills[id] } : {}),
          };

          if (resolveAesthetic) {
            const overrides = resolveAesthetic({
              id,
              isActive,
              count,
              baseAesthetic: resolved,
              tooltip,
            });
            if (overrides) resolved = { ...resolved, ...overrides };
          }

          const regionOverrides = regionProps?.({
            id,
            isActive,
            count,
            baseAesthetic: resolved,
            tooltip,
          });

          return (
            <path
              key={id}
              d={d}
              fill={resolved.fillColor}
              fillOpacity={resolved.fillOpacity}
              stroke={resolved.strokeColor}
              strokeWidth={resolved.strokeWidth}
              onClick={onRegionClick ? () => onRegionClick(id) : undefined}
              style={onRegionClick ? { cursor: "pointer" } : undefined}
              {...regionOverrides}
            >
              {tooltip ? <title>{tooltip}</title> : null}
            </path>
          );
        })}
      </g>
    </svg>
  );
}
