import React, { useMemo, useState } from "react";

import type { AestheticStyle, Element, OutputMapProps, RegionId, RenderedRegion } from "../types";
import { createRenderedRegion, DEFAULT_AESTHETIC_VALUES, DEFAULT_HOVER_AESTHETIC } from "../types";
import { normalizeGeometry } from "../utils/geometry";
import { assignLayers, resolveGroupAesthetic } from "../utils/layers";
import { renderElement } from "../utils/renderElement";

const DEFAULT_VIEWBOX = "0 0 100 100";

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
    aes,
    layers,
    geometryMetadata,
    fillColor,
    strokeWidth: strokeWidthProp,
    strokeColor: strokeColorProp,
    fillOpacity: fillOpacityProp,
    value,
    activeIds,
    onRegionClick,
    resolveAesthetic,
    regionProps,
    // Deprecated props (for backward compatibility)
    overlayGeometry,
    overlayAesthetic,
  } = props;

  // Extract from nested aes config
  // Note: aes.base.fillColor can be a single color or a per-region dict
  const aesBaseRaw = aes?.base ?? DEFAULT_AESTHETIC_VALUES;
  const aesBase = aesBaseRaw;
  const aesHover = aes?.hover;
  const aesSelect = aes?.select;
  const aesNotSelect = aes?.notSelect;
  const aesGroup = aes?.group;

  // Extract per-region fill colors from aes.base if it's a dict
  const aesBaseFillColorDict = typeof aesBaseRaw.fillColor === "object" && aesBaseRaw.fillColor !== null
    ? aesBaseRaw.fillColor as Record<RegionId, string>
    : undefined;

  // Extract from nested layers config
  const underlays = layers?.underlays;
  const overlays = layers?.overlays;
  const hidden = layers?.hidden;

  // Normalize geometry to Element[] format (handles both v0.x strings and v1.x polymorphic elements)
  const normalizedGeometry = useMemo(() => normalizeGeometry(geometry), [geometry]);

  // Legacy overlay support (deprecated)
  const normalizedOverlayGeometry = useMemo(
    () => (overlayGeometry ? normalizeGeometry(overlayGeometry) : undefined),
    [overlayGeometry]
  );

  // New layer system: assign regions to layers
  const layerAssignment = useMemo(
    () => assignLayers(normalizedGeometry, underlays, overlays, hidden, geometryMetadata),
    [normalizedGeometry, underlays, overlays, hidden, geometryMetadata]
  );

  const [hovered, setHovered] = useState<RegionId | null>(null);
  const activeSet = normalizeActive(activeIds);
  const normalizedFillColor = normalize(fillColor, normalizedGeometry);
  const normalizedStrokeWidth = normalize(strokeWidthProp, normalizedGeometry);
  const normalizedStrokeColor = normalize(strokeColorProp, normalizedGeometry);
  const normalizedFillOpacity = normalize(fillOpacityProp, normalizedGeometry);
  const countMap = value ?? {};

  // Helper to render a non-interactive layer (underlay or overlay)
  const renderNonInteractiveLayer = (regionIds: Set<RegionId>, keyPrefix: string) => {
    return Array.from(regionIds).flatMap((id) => {
      const elements = normalizedGeometry[id];
      if (!elements) return [];

      // Build aesthetic chain: default -> aesBase -> per-region fillColor -> groupAes
      let layerAes: AestheticStyle = { ...DEFAULT_AESTHETIC_VALUES, ...aesBase };
      if (aesBaseFillColorDict?.[id]) {
        layerAes = { ...layerAes, fillColor: aesBaseFillColorDict[id] };
      }
      const groupAes = resolveGroupAesthetic(id, aesGroup, geometryMetadata);
      if (groupAes) {
        layerAes = { ...layerAes, ...groupAes };
      }

      // Create RenderedRegion to resolve any RelativeExpr
      const region = createRenderedRegion(id, layerAes);

      return elements.map((element, index) =>
        renderElement({
          element,
          key: `${keyPrefix}-${id}-${index}`,
          fill: region.aesthetic.fillColor,
          fillOpacity: region.aesthetic.fillOpacity,
          stroke: region.aesthetic.strokeColor,
          strokeWidth: region.aesthetic.strokeWidth,
          strokeDasharray: region.aesthetic.strokeDasharray,
          nonScalingStroke: region.aesthetic.nonScalingStroke,
          pointerEvents: "none",
        })
      );
    });
  };

  return (
    <svg
      role="img"
      className={className}
      style={{ width: "100%", height: "100%", ...containerStyle }}
      viewBox={viewBox}
    >
      {/* Layer 1: Underlay - background elements (grids, etc.) */}
      <g>{renderNonInteractiveLayer(layerAssignment.underlay, "underlay")}</g>

      {/* Layer 2: Base layer - interactive/display regions */}
      <g>
        {Array.from(layerAssignment.base).flatMap((id) => {
          const elements = normalizedGeometry[id];
          if (!elements) return [];

          const tooltip = tooltips?.[id];
          const isActive = activeSet.has(id);
          const count = countMap[id] ?? 0;

          let baseAes: AestheticStyle = {
            ...DEFAULT_AESTHETIC_VALUES,
            ...aesBase,
          };

          // Apply per-region fill color from aes.base.fillColor if it's a dict
          if (aesBaseFillColorDict?.[id]) {
            baseAes = { ...baseAes, fillColor: aesBaseFillColorDict[id] };
          }

          // Apply group aesthetic if available
          const groupAes = resolveGroupAesthetic(id, aesGroup, geometryMetadata);
          if (groupAes) {
            baseAes = { ...baseAes, ...groupAes };
          }

          // Apply per-region overrides from top-level props
          baseAes = {
            ...baseAes,
            ...(normalizedFillColor?.[id] ? { fillColor: normalizedFillColor[id] } : {}),
            ...(normalizedStrokeWidth?.[id] !== undefined ? { strokeWidth: normalizedStrokeWidth[id] } : {}),
            ...(normalizedStrokeColor?.[id] ? { strokeColor: normalizedStrokeColor[id] } : {}),
            ...(normalizedFillOpacity?.[id] !== undefined ? { fillOpacity: normalizedFillOpacity[id] } : {}),
          };

          // Apply selection-specific aesthetics (layer 4a)
          if (isActive && aesSelect) {
            baseAes = { ...baseAes, ...aesSelect };
          } else if (!isActive && aesNotSelect) {
            baseAes = { ...baseAes, ...aesNotSelect };
          }

          // Apply resolveAesthetic callback (layer 4b)
          if (resolveAesthetic) {
            const overrides = resolveAesthetic({
              id,
              isActive,
              count,
              baseAesthetic: baseAes,
              tooltip,
            });
            if (overrides) baseAes = { ...baseAes, ...overrides };
          }

          // Create RenderedRegion to resolve any RelativeExpr
          const region = createRenderedRegion(id, baseAes);

          const regionOverrides = regionProps?.({
            id,
            isActive,
            count,
            baseAesthetic: baseAes,
            tooltip,
          });

          const handleMouseEnter = () => setHovered(id);
          const handleMouseLeave = () => setHovered((current) => (current === id ? null : current));

          // Render each element in the region
          return elements.map((element, index) =>
            renderElement({
              element,
              key: `${id}-${index}`,
              fill: region.aesthetic.fillColor,
              fillOpacity: region.aesthetic.fillOpacity,
              stroke: region.aesthetic.strokeColor,
              strokeWidth: region.aesthetic.strokeWidth,
              strokeDasharray: region.aesthetic.strokeDasharray,
              nonScalingStroke: region.aesthetic.nonScalingStroke,
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
      </g>

      {/* Layer 3a: Legacy overlay (deprecated - for backward compatibility) */}
      {normalizedOverlayGeometry && (
        <g>
          {Object.entries(normalizedOverlayGeometry).flatMap(([id, elements]) => {
            const overlayAes: AestheticStyle = {
              ...DEFAULT_AESTHETIC_VALUES,
              ...overlayAesthetic,
            };
            const region = createRenderedRegion(id, overlayAes);
            return elements.map((element, index) =>
              renderElement({
                element,
                key: `legacy-overlay-${id}-${index}`,
                fill: region.aesthetic.fillColor,
                fillOpacity: region.aesthetic.fillOpacity,
                stroke: region.aesthetic.strokeColor,
                strokeWidth: region.aesthetic.strokeWidth,
                strokeDasharray: region.aesthetic.strokeDasharray,
                nonScalingStroke: region.aesthetic.nonScalingStroke,
                pointerEvents: "none",
              })
            );
          })}
        </g>
      )}

      {/* Layer 3b: Overlay - annotations (borders, labels) */}
      <g>{renderNonInteractiveLayer(layerAssignment.overlay, "overlay")}</g>

      {/* Layer 4: Selection overlay - render active regions on top to ensure borders are visible */}
      <g>
        {Array.from(activeSet).flatMap((id) => {
          // Only render selection overlay for regions in base layer
          if (!layerAssignment.base.has(id)) return [];

          const elements = normalizedGeometry[id];
          if (!elements) return [];

          const count = countMap[id] ?? 0;

          // Build base aesthetic
          let baseAes: AestheticStyle = {
            ...DEFAULT_AESTHETIC_VALUES,
            ...aesBase,
          };
          if (aesBaseFillColorDict?.[id]) {
            baseAes = { ...baseAes, fillColor: aesBaseFillColorDict[id] };
          }
          const groupAes = resolveGroupAesthetic(id, aesGroup, geometryMetadata);
          if (groupAes) {
            baseAes = { ...baseAes, ...groupAes };
          }
          baseAes = {
            ...baseAes,
            ...(normalizedFillColor?.[id] ? { fillColor: normalizedFillColor[id] } : {}),
            ...(normalizedStrokeWidth?.[id] !== undefined ? { strokeWidth: normalizedStrokeWidth[id] } : {}),
            ...(normalizedStrokeColor?.[id] ? { strokeColor: normalizedStrokeColor[id] } : {}),
            ...(normalizedFillOpacity?.[id] !== undefined ? { fillOpacity: normalizedFillOpacity[id] } : {}),
          };

          // Create base RenderedRegion
          const baseRegion = createRenderedRegion(id, baseAes);

          // Build selection aesthetic on top of base
          let selectAes: AestheticStyle = {};
          if (aesSelect) {
            selectAes = { ...aesSelect };
          }

          // Apply resolveAesthetic callback
          if (resolveAesthetic) {
            const overrides = resolveAesthetic({
              id,
              isActive: true,
              count,
              baseAesthetic: baseAes,
              tooltip: tooltips?.[id],
            });
            if (overrides) selectAes = { ...selectAes, ...overrides };
          }

          // Create selection RenderedRegion with base as parent
          const selectRegion = createRenderedRegion(id, selectAes, baseRegion);

          return elements.map((element, index) =>
            renderElement({
              element,
              key: `selection-overlay-${id}-${index}`,
              fill: selectRegion.aesthetic.fillColor,
              fillOpacity: selectRegion.aesthetic.fillOpacity,
              stroke: selectRegion.aesthetic.strokeColor,
              strokeWidth: selectRegion.aesthetic.strokeWidth,
              strokeDasharray: selectRegion.aesthetic.strokeDasharray,
              nonScalingStroke: selectRegion.aesthetic.nonScalingStroke,
              pointerEvents: "none",
            })
          );
        })}
      </g>

      {/* Layer 5: Hover overlay - rendered on top with pointer-events: none */}
      {/* aesHover: undefined = default, null = disabled, object = custom */}
      <g>
        {hovered &&
          aesHover !== null &&
          layerAssignment.base.has(hovered) &&
          (() => {
            // Determine effective hover aesthetic
            const effectiveHover = aesHover ?? DEFAULT_HOVER_AESTHETIC;

            // Build the parent chain for the hovered region
            // Step 1: Create base RenderedRegion
            let baseAes: AestheticStyle = { ...DEFAULT_AESTHETIC_VALUES, ...aesBase };
            if (aesBaseFillColorDict?.[hovered]) {
              baseAes = { ...baseAes, fillColor: aesBaseFillColorDict[hovered] };
            }
            const groupAes = resolveGroupAesthetic(hovered, aesGroup, geometryMetadata);
            if (groupAes) {
              baseAes = { ...baseAes, ...groupAes };
            }
            baseAes = {
              ...baseAes,
              ...(normalizedFillColor?.[hovered] ? { fillColor: normalizedFillColor[hovered] } : {}),
              ...(normalizedStrokeWidth?.[hovered] !== undefined ? { strokeWidth: normalizedStrokeWidth[hovered] } : {}),
              ...(normalizedStrokeColor?.[hovered] ? { strokeColor: normalizedStrokeColor[hovered] } : {}),
              ...(normalizedFillOpacity?.[hovered] !== undefined ? { fillOpacity: normalizedFillOpacity[hovered] } : {}),
            };
            const baseRegion = createRenderedRegion(hovered, baseAes);

            // Step 2: If active, create selection RenderedRegion with base as parent
            let parentRegion: RenderedRegion = baseRegion;
            if (activeSet.has(hovered) && aesSelect) {
              parentRegion = createRenderedRegion(hovered, aesSelect, baseRegion);
            }

            // Step 3: Create hover RenderedRegion with parent chain
            const hoverRegion = createRenderedRegion(hovered, effectiveHover, parentRegion);

            // Render using resolved aesthetics
            return normalizedGeometry[hovered]?.map((element, index) =>
              renderElement({
                element,
                key: `hover-overlay-${hovered}-${index}`,
                fill: hoverRegion.aesthetic.fillColor ?? "none",
                fillOpacity: hoverRegion.aesthetic.fillOpacity ?? (hoverRegion.aesthetic.fillColor ? 1 : 0),
                stroke: hoverRegion.aesthetic.strokeColor,
                strokeWidth: hoverRegion.aesthetic.strokeWidth,
                strokeDasharray: hoverRegion.aesthetic.strokeDasharray,
                nonScalingStroke: hoverRegion.aesthetic.nonScalingStroke,
                pointerEvents: "none",
              })
            );
          })()}
      </g>
    </svg>
  );
}
