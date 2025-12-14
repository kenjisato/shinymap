import React, { useState } from "react";

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

function normalize<T>(
  value: T | Record<RegionId, T> | undefined,
  geometry: Record<RegionId, string>
): Record<RegionId, T> | undefined {
  if (!value) return undefined;
  if (typeof value === "object" && !Array.isArray(value)) {
    // Already a dict
    return value as Record<RegionId, T>;
  }
  // Scalar value - apply to all regions
  return Object.fromEntries(Object.keys(geometry).map((id) => [id, value as T]));
}

export function OutputMap(props: OutputMapProps) {
  const {
    geometry,
    tooltips,
    className,
    containerStyle,
    viewBox = DEFAULT_VIEWBOX,
    defaultAesthetic = DEFAULT_AESTHETIC,
    fillColor,  // RENAMED from fills
    strokeWidth: strokeWidthProp,  // NEW
    strokeColor: strokeColorProp,  // NEW
    fillOpacity: fillOpacityProp,  // NEW
    counts,
    activeIds,
    onRegionClick,
    resolveAesthetic,
    regionProps,
    fillColorSelected,  // RENAMED from selectionAesthetic
    fillColorNotSelected,  // RENAMED from notSelectionAesthetic
    overlayGeometry,
    overlayAesthetic,
    hoverHighlight,
  } = props;

  const [hovered, setHovered] = useState<RegionId | null>(null);
  const activeSet = normalizeActive(activeIds);
  const normalizedFillColor = normalize(fillColor, geometry);
  const normalizedStrokeWidth = normalize(strokeWidthProp, geometry);
  const normalizedStrokeColor = normalize(strokeColorProp, geometry);
  const normalizedFillOpacity = normalize(fillOpacityProp, geometry);
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
            ...(normalizedFillColor?.[id] ? { fillColor: normalizedFillColor[id] } : {}),
            ...(normalizedStrokeWidth?.[id] !== undefined ? { strokeWidth: normalizedStrokeWidth[id] } : {}),
            ...(normalizedStrokeColor?.[id] ? { strokeColor: normalizedStrokeColor[id] } : {}),
            ...(normalizedFillOpacity?.[id] !== undefined ? { fillOpacity: normalizedFillOpacity[id] } : {}),
          };

          // Apply selection-specific aesthetics (layer 4a)
          if (isActive && fillColorSelected) {
            resolved = { ...resolved, ...fillColorSelected };
          } else if (!isActive && fillColorNotSelected) {
            resolved = { ...resolved, ...fillColorNotSelected };
          }

          // Apply resolveAesthetic callback (layer 4b)
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
              onClick={onRegionClick ? () => onRegionClick(id) : undefined}
              onMouseEnter={handleMouseEnter}
              onMouseLeave={handleMouseLeave}
              onFocus={handleMouseEnter}
              onBlur={handleMouseLeave}
              style={onRegionClick ? { cursor: "pointer" } : undefined}
              {...regionOverrides}
            >
              {tooltip ? <title>{tooltip}</title> : null}
            </path>
          );
        })}

        {/* Non-interactive overlay (dividers, borders, grids) */}
        {overlayGeometry &&
          Object.entries(overlayGeometry).map(([id, d]) => {
            const overlayStyle = {
              ...DEFAULT_AESTHETIC,
              ...overlayAesthetic,
            };
            return (
              <path
                key={`overlay-${id}`}
                d={d}
                fill={overlayStyle.fillColor}
                fillOpacity={overlayStyle.fillOpacity}
                stroke={overlayStyle.strokeColor}
                strokeWidth={overlayStyle.strokeWidth}
                pointerEvents="none"
              />
            );
          })}

        {/* Selection overlay - render active regions on top to ensure borders are visible */}
        {Array.from(activeSet).map((id) => {
          if (!geometry[id]) return null;

          const count = countMap[id] ?? 0;
          let resolved: AestheticStyle = {
            ...DEFAULT_AESTHETIC,
            ...defaultAesthetic,
            ...(normalizedFillColor?.[id] ? { fillColor: normalizedFillColor[id] } : {}),
            ...(normalizedStrokeWidth?.[id] !== undefined ? { strokeWidth: normalizedStrokeWidth[id] } : {}),
            ...(normalizedStrokeColor?.[id] ? { strokeColor: normalizedStrokeColor[id] } : {}),
            ...(normalizedFillOpacity?.[id] !== undefined ? { fillOpacity: normalizedFillOpacity[id] } : {}),
          };

          // Apply selection-specific aesthetics
          if (fillColorSelected) {
            resolved = { ...resolved, ...fillColorSelected };
          }

          // Apply resolveAesthetic callback
          if (resolveAesthetic) {
            const overrides = resolveAesthetic({
              id,
              isActive: true,
              count,
              baseAesthetic: resolved,
              tooltip: tooltips?.[id],
            });
            if (overrides) resolved = { ...resolved, ...overrides };
          }

          return (
            <path
              key={`selection-overlay-${id}`}
              d={geometry[id]}
              fill={resolved.fillColor}
              fillOpacity={resolved.fillOpacity}
              stroke={resolved.strokeColor}
              strokeWidth={resolved.strokeWidth}
              pointerEvents="none"
            />
          );
        })}

        {/* Hover overlay - rendered on top with pointer-events: none */}
        {hovered && hoverHighlight && geometry[hovered] && (
          <path
            key={`hover-overlay-${hovered}`}
            d={geometry[hovered]}
            fill={hoverHighlight.fillColor ?? "none"}
            fillOpacity={hoverHighlight.fillOpacity ?? 0}
            stroke={hoverHighlight.strokeColor ?? "#1e40af"}
            strokeWidth={hoverHighlight.strokeWidth ?? 2}
            pointerEvents="none"
          />
        )}
      </g>
    </svg>
  );
}
