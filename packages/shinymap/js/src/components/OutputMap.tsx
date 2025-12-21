import React, { useMemo, useState } from "react";

import type { AestheticStyle, Element, OutputMapProps, RegionId } from "../types";
import { normalizeGeometry } from "../utils/geometry";
import { renderElement } from "../utils/renderElement";

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
  geometry: Record<RegionId, Element[]>
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

  // Normalize geometry to Element[] format (handles both v0.x strings and v1.x polymorphic elements)
  const normalizedGeometry = useMemo(() => normalizeGeometry(geometry), [geometry]);
  const normalizedOverlayGeometry = useMemo(
    () => (overlayGeometry ? normalizeGeometry(overlayGeometry) : undefined),
    [overlayGeometry]
  );

  const [hovered, setHovered] = useState<RegionId | null>(null);
  const activeSet = normalizeActive(activeIds);
  const normalizedFillColor = normalize(fillColor, normalizedGeometry);
  const normalizedStrokeWidth = normalize(strokeWidthProp, normalizedGeometry);
  const normalizedStrokeColor = normalize(strokeColorProp, normalizedGeometry);
  const normalizedFillOpacity = normalize(fillOpacityProp, normalizedGeometry);
  const countMap = counts ?? {};

  return (
    <svg
      role="img"
      className={className}
      style={{ width: "100%", height: "100%", ...containerStyle }}
      viewBox={viewBox}
    >
      <g>
        {Object.entries(normalizedGeometry).flatMap(([id, elements]) => {
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

          // Render each element in the region
          return elements.map((element, index) =>
            renderElement({
              element,
              key: `${id}-${index}`,
              fill: resolved.fillColor,
              fillOpacity: resolved.fillOpacity,
              stroke: resolved.strokeColor,
              strokeWidth: resolved.strokeWidth,
              cursor: onRegionClick ? "pointer" : undefined,
              onClick: onRegionClick ? () => onRegionClick(id) : undefined,
              onMouseEnter: handleMouseEnter,
              onMouseLeave: handleMouseLeave,
              onFocus: handleMouseEnter,
              onBlur: handleMouseLeave,
              tooltip,
              extraProps: regionOverrides as Record<string, unknown>,
            })
          );
        })}

        {/* Non-interactive overlay (dividers, borders, grids) */}
        {normalizedOverlayGeometry &&
          Object.entries(normalizedOverlayGeometry).flatMap(([id, elements]) => {
            const overlayStyle = {
              ...DEFAULT_AESTHETIC,
              ...overlayAesthetic,
            };
            return elements.map((element, index) =>
              renderElement({
                element,
                key: `overlay-${id}-${index}`,
                fill: overlayStyle.fillColor,
                fillOpacity: overlayStyle.fillOpacity,
                stroke: overlayStyle.strokeColor,
                strokeWidth: overlayStyle.strokeWidth,
                pointerEvents: "none",
              })
            );
          })}

        {/* Selection overlay - render active regions on top to ensure borders are visible */}
        {Array.from(activeSet).flatMap((id) => {
          const elements = normalizedGeometry[id];
          if (!elements) return [];

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

          return elements.map((element, index) =>
            renderElement({
              element,
              key: `selection-overlay-${id}-${index}`,
              fill: resolved.fillColor,
              fillOpacity: resolved.fillOpacity,
              stroke: resolved.strokeColor,
              strokeWidth: resolved.strokeWidth,
              pointerEvents: "none",
            })
          );
        })}

        {/* Hover overlay - rendered on top with pointer-events: none */}
        {hovered &&
          hoverHighlight &&
          normalizedGeometry[hovered]?.map((element, index) =>
            renderElement({
              element,
              key: `hover-overlay-${hovered}-${index}`,
              fill: hoverHighlight.fillColor ?? "none",
              fillOpacity: hoverHighlight.fillOpacity ?? 0,
              stroke: hoverHighlight.strokeColor ?? "#1e40af",
              strokeWidth: hoverHighlight.strokeWidth ?? 2,
              pointerEvents: "none",
            })
          )}
      </g>
    </svg>
  );
}
