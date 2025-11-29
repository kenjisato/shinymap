import React from "react";

import type { OutputMapProps, RegionId } from "../types";

const DEFAULT_VIEWBOX = "0 0 100 100";
const DEFAULT_FILL = "#e2e8f0";
const DEFAULT_STROKE = "#1f2937";

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
    defaultFill = DEFAULT_FILL,
    strokeColor = DEFAULT_STROKE,
    strokeWidth: strokeWidthProp = 1,
    fills,
    activeIds,
    onRegionClick,
    resolveAesthetic,
    regionProps,
  } = props;

  const activeSet = normalizeActive(activeIds);

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
          const baseFill = fills?.[id] ?? defaultFill;
          const isActive = activeSet.has(id);

          let fillColor = baseFill;
          let fillOpacity = 1;
          let strokeColorCurrent = strokeColor;
          let strokeWidthCurrent = strokeWidthProp;

          if (resolveAesthetic) {
            const overrides = resolveAesthetic({
              id,
              isActive,
              baseFill,
              baseStrokeColor: strokeColorCurrent,
              baseStrokeWidth: strokeWidthCurrent,
              tooltip,
            });
            if (overrides) {
              if (overrides.fillColor !== undefined) fillColor = overrides.fillColor;
              if (overrides.fillOpacity !== undefined) fillOpacity = overrides.fillOpacity;
              if (overrides.strokeColor !== undefined) strokeColorCurrent = overrides.strokeColor;
              if (overrides.strokeWidth !== undefined) strokeWidthCurrent = overrides.strokeWidth;
            }
          }

          const regionOverrides = regionProps?.({
            id,
            isActive,
            baseFill,
            baseStrokeColor: strokeColorCurrent,
            baseStrokeWidth: strokeWidthCurrent,
            tooltip,
          });

          return (
            <path
              key={id}
              d={d}
              fill={fillColor}
              fillOpacity={fillOpacity}
              stroke={strokeColorCurrent}
              strokeWidth={strokeWidthCurrent}
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
