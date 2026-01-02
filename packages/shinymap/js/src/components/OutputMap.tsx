import React, { useMemo, useState } from "react";

import type {
  AestheticStyle,
  Element,
  LegacyAesConfig,
  OutputMapProps,
  RegionId,
  RenderedRegion,
} from "../types";
import {
  createRenderedRegion,
  DEFAULT_AESTHETIC_VALUES,
  DEFAULT_HOVER_AESTHETIC,
  getAesForRegion,
  getIndexedDataForRegion,
  isAesPayload,
  resolveIndexedAesthetic,
} from "../types";
import { normalizeRegions } from "../utils/regions";
import { assignLayers, resolveGroupAesthetic } from "../utils/layers";
import { renderElement } from "../utils/renderElement";

const DEFAULT_VIEWBOX = "0 0 100 100";

/**
 * Derive active (selected) regions from value map.
 * A region is considered active/selected if its value > 0.
 */
function deriveActiveFromValue(value: Record<RegionId, number> | undefined): Set<RegionId> {
  if (!value) return new Set();
  const active = new Set<RegionId>();
  for (const [id, count] of Object.entries(value)) {
    if (count > 0) active.add(id);
  }
  return active;
}

function normalize<T>(
  value: T | Record<RegionId, T> | undefined,
  regions: Record<RegionId, Element[]>
): Record<RegionId, T> | undefined {
  if (!value) return undefined;
  if (typeof value === "object" && !Array.isArray(value)) {
    // Already a dict
    return value as Record<RegionId, T>;
  }
  // Scalar value - apply to all regions
  return Object.fromEntries(Object.keys(regions).map((id) => [id, value as T]));
}

export function OutputMap(props: OutputMapProps) {
  const {
    regions,
    tooltips,
    className,
    containerStyle,
    viewBox = DEFAULT_VIEWBOX,
    mode: modeConfig,
    aes,
    layers,
    outlineMetadata,
    fillColor,
    strokeWidth: strokeWidthProp,
    strokeColor: strokeColorProp,
    fillOpacity: fillOpacityProp,
    value,
    onRegionClick,
    resolveAesthetic,
    regionProps,
  } = props;

  // Extract from nested mode config (supports both string shorthand and full config)
  const normalizedMode = typeof modeConfig === "string" ? { type: modeConfig } : modeConfig;
  const aesIndexed = normalizedMode?.aesIndexed;
  // Display mode: clicks only enabled if clickable=true
  const isClickable = normalizedMode?.clickable ?? false;

  // Detect v0.3 payload format (has __all or _metadata at top level)
  const isV03Format = isAesPayload(aes);
  const aesPayload = isV03Format ? aes : undefined;

  // Extract from nested aes config (handles both old and v0.3 formats)
  // For v0.3: use __all.base/select/hover
  // For old format: use aes.base/select/hover directly
  const legacyAes = !isV03Format ? (aes as LegacyAesConfig | undefined) : undefined;
  const aesBaseRaw = isV03Format
    ? (aesPayload?.__all?.base ?? DEFAULT_AESTHETIC_VALUES)
    : (legacyAes?.base ?? DEFAULT_AESTHETIC_VALUES);
  const aesBase = aesBaseRaw;
  const aesHover = isV03Format ? aesPayload?.__all?.hover : legacyAes?.hover;
  const aesSelect = isV03Format ? aesPayload?.__all?.select : legacyAes?.select;
  const aesNotSelect = legacyAes?.notSelect; // Only in legacy format
  // For v0.3, group aesthetics are in the payload directly (not under .group)
  const aesGroup = isV03Format ? undefined : legacyAes?.group;

  // Extract per-region fill colors from aes.base if it's a dict
  const aesBaseFillColorDict =
    typeof aesBaseRaw?.fillColor === "object" && aesBaseRaw.fillColor !== null
      ? (aesBaseRaw.fillColor as Record<RegionId, string>)
      : undefined;

  // Extract from nested layers config
  const underlays = layers?.underlays;
  const overlays = layers?.overlays;
  const hidden = layers?.hidden;

  // Normalize regions to Element[] format (handles both v0.x strings and v1.x polymorphic elements)
  const normalizedRegions = useMemo(() => normalizeRegions(regions), [regions]);

  // New layer system: assign regions to layers
  const layerAssignment = useMemo(
    () => assignLayers(normalizedRegions, underlays, overlays, hidden, outlineMetadata),
    [normalizedRegions, underlays, overlays, hidden, outlineMetadata]
  );

  const [hovered, setHovered] = useState<RegionId | null>(null);
  // Derive active/selected regions from value (value > 0 means selected)
  const activeSet = deriveActiveFromValue(value);
  const normalizedFillColor = normalize(fillColor, normalizedRegions);
  const normalizedStrokeWidth = normalize(strokeWidthProp, normalizedRegions);
  const normalizedStrokeColor = normalize(strokeColorProp, normalizedRegions);
  const normalizedFillOpacity = normalize(fillOpacityProp, normalizedRegions);
  const countMap = value ?? {};

  // Helper to determine element type for a region from _metadata
  const getElementType = (regionId: RegionId): "shape" | "line" | "text" => {
    const metadata = aesPayload?._metadata;
    if (metadata) {
      if (metadata.__line?.includes(regionId)) return "line";
      if (metadata.__text?.includes(regionId)) return "text";
    }
    return "shape";
  };

  // Helper to render a non-interactive layer (underlay or overlay)
  const renderNonInteractiveLayer = (regionIds: Set<RegionId>, keyPrefix: string) => {
    return Array.from(regionIds).flatMap((id) => {
      const elements = normalizedRegions[id];
      if (!elements) return [];

      // Build aesthetic chain
      let layerAes: AestheticStyle = { ...DEFAULT_AESTHETIC_VALUES };

      if (isV03Format && aesPayload) {
        // v0.3 format: use getAesForRegion for proper type-based lookup
        const elementType = getElementType(id);
        const byState = getAesForRegion(id, elementType, aesPayload);
        if (byState?.base) {
          layerAes = { ...layerAes, ...byState.base };
        }
      } else {
        // Legacy format: use aesBase + groupAes
        layerAes = { ...layerAes, ...aesBase };
        if (aesBaseFillColorDict?.[id]) {
          layerAes = { ...layerAes, fillColor: aesBaseFillColorDict[id] };
        }
        const groupAes = resolveGroupAesthetic(id, aesGroup, outlineMetadata);
        if (groupAes) {
          layerAes = { ...layerAes, ...groupAes };
        }
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
          const elements = normalizedRegions[id];
          if (!elements) return [];

          const tooltip = tooltips?.[id];
          const isActive = activeSet.has(id);
          const count = countMap[id] ?? 0;

          let baseAes: AestheticStyle = { ...DEFAULT_AESTHETIC_VALUES };

          if (isV03Format && aesPayload) {
            // v0.3 format: use getAesForRegion for proper type-based lookup
            const elementType = getElementType(id);
            const byState = getAesForRegion(id, elementType, aesPayload);
            if (byState?.base) {
              baseAes = { ...baseAes, ...byState.base };
            }
          } else {
            // Legacy format: use aesBase + groupAes
            baseAes = { ...baseAes, ...aesBase };
            // Apply per-region fill color from aes.base.fillColor if it's a dict
            if (aesBaseFillColorDict?.[id]) {
              baseAes = { ...baseAes, fillColor: aesBaseFillColorDict[id] };
            }
            // Apply group aesthetic if available
            const groupAes = resolveGroupAesthetic(id, aesGroup, outlineMetadata);
            if (groupAes) {
              baseAes = { ...baseAes, ...groupAes };
            }
          }

          // Apply indexed aesthetic if available (for Display mode with aesIndexed)
          const indexedData = getIndexedDataForRegion(aesIndexed, id, outlineMetadata);
          if (indexedData) {
            // For display mode, use clamping (no wrapping)
            const indexedAes = resolveIndexedAesthetic(indexedData, count, undefined);
            // Merge indexed aesthetic - only override properties that are defined
            baseAes = {
              ...baseAes,
              ...(indexedAes.fillColor !== undefined ? { fillColor: indexedAes.fillColor } : {}),
              ...(indexedAes.fillOpacity !== undefined
                ? { fillOpacity: indexedAes.fillOpacity }
                : {}),
              ...(indexedAes.strokeColor !== undefined
                ? { strokeColor: indexedAes.strokeColor }
                : {}),
              ...(indexedAes.strokeWidth !== undefined
                ? { strokeWidth: indexedAes.strokeWidth }
                : {}),
              ...(indexedAes.strokeDasharray !== undefined
                ? { strokeDasharray: indexedAes.strokeDasharray }
                : {}),
            };
          }

          // Apply per-region overrides from top-level props
          baseAes = {
            ...baseAes,
            ...(normalizedFillColor?.[id] ? { fillColor: normalizedFillColor[id] } : {}),
            ...(normalizedStrokeWidth?.[id] !== undefined
              ? { strokeWidth: normalizedStrokeWidth[id] }
              : {}),
            ...(normalizedStrokeColor?.[id] ? { strokeColor: normalizedStrokeColor[id] } : {}),
            ...(normalizedFillOpacity?.[id] !== undefined
              ? { fillOpacity: normalizedFillOpacity[id] }
              : {}),
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

          // For display mode, only enable clicks if clickable=true
          const effectiveOnClick =
            isClickable && onRegionClick ? () => onRegionClick(id) : undefined;

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
              cursor: effectiveOnClick ? "pointer" : undefined,
              onClick: effectiveOnClick,
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

      {/* Layer 3: Overlay - annotations (borders, labels) */}
      <g>{renderNonInteractiveLayer(layerAssignment.overlay, "overlay")}</g>

      {/* Layer 4: Selection overlay - render active regions on top to ensure borders are visible */}
      {/* Skip when no aesSelect is defined - no point rendering duplicate paths */}
      <g>
        {aesSelect &&
          Array.from(activeSet).flatMap((id) => {
            // Only render selection overlay for regions in base layer
            if (!layerAssignment.base.has(id)) return [];

            const elements = normalizedRegions[id];
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
            const groupAes = resolveGroupAesthetic(id, aesGroup, outlineMetadata);
            if (groupAes) {
              baseAes = { ...baseAes, ...groupAes };
            }
            baseAes = {
              ...baseAes,
              ...(normalizedFillColor?.[id] ? { fillColor: normalizedFillColor[id] } : {}),
              ...(normalizedStrokeWidth?.[id] !== undefined
                ? { strokeWidth: normalizedStrokeWidth[id] }
                : {}),
              ...(normalizedStrokeColor?.[id] ? { strokeColor: normalizedStrokeColor[id] } : {}),
              ...(normalizedFillOpacity?.[id] !== undefined
                ? { fillOpacity: normalizedFillOpacity[id] }
                : {}),
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
            const groupAes = resolveGroupAesthetic(hovered, aesGroup, outlineMetadata);
            if (groupAes) {
              baseAes = { ...baseAes, ...groupAes };
            }
            baseAes = {
              ...baseAes,
              ...(normalizedFillColor?.[hovered]
                ? { fillColor: normalizedFillColor[hovered] }
                : {}),
              ...(normalizedStrokeWidth?.[hovered] !== undefined
                ? { strokeWidth: normalizedStrokeWidth[hovered] }
                : {}),
              ...(normalizedStrokeColor?.[hovered]
                ? { strokeColor: normalizedStrokeColor[hovered] }
                : {}),
              ...(normalizedFillOpacity?.[hovered] !== undefined
                ? { fillOpacity: normalizedFillOpacity[hovered] }
                : {}),
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
            return normalizedRegions[hovered]?.map((element, index) =>
              renderElement({
                element,
                key: `hover-overlay-${hovered}-${index}`,
                fill: hoverRegion.aesthetic.fillColor ?? "none",
                fillOpacity:
                  hoverRegion.aesthetic.fillOpacity ?? (hoverRegion.aesthetic.fillColor ? 1 : 0),
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
