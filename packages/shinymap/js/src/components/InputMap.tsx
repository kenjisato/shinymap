import React, { useEffect, useMemo, useState } from "react";

import type {
  AestheticStyle,
  Element,
  InputMapProps,
  LegacyAesConfig,
  MapModeType,
  RegionId,
  RenderedRegion,
} from "../types";
import {
  createRenderedRegion,
  DEFAULT_AESTHETIC_VALUES,
  DEFAULT_HOVER_AESTHETIC,
  getIndexedDataForRegion,
  isAesPayload,
  resolveIndexedAesthetic,
} from "../types";
import { normalizeGeometry } from "../utils/geometry";
import { assignLayers, resolveGroupAesthetic } from "../utils/layers";
import { renderElement } from "../utils/renderElement";

const DEFAULT_VIEWBOX = "0 0 100 100";

function buildSelected(value: Record<RegionId, number> | undefined): Set<RegionId> {
  const set = new Set<RegionId>();
  if (!value) return set;
  Object.entries(value).forEach(([id, val]) => {
    if (val > 0) set.add(id);
  });
  return set;
}

function normalizeFillColor(
  fillColor: string | Record<RegionId, string> | undefined,
  geometry: Record<RegionId, Element[]>
): Record<RegionId, string> | undefined {
  if (!fillColor) return undefined;
  if (typeof fillColor === "string") {
    return Object.fromEntries(Object.keys(geometry).map((id) => [id, fillColor]));
  }
  return fillColor;
}

export function InputMap(props: InputMapProps) {
  const {
    geometry,
    tooltips,
    fillColor,
    className,
    containerStyle,
    viewBox = DEFAULT_VIEWBOX,
    mode: modeConfig,
    aes,
    layers,
    geometryMetadata,
    value,
    onChange,
    resolveAesthetic,
    regionProps,
    // Deprecated props (for backward compatibility)
    overlayGeometry,
    overlayAesthetic,
  } = props;

  // Detect v0.3 payload format (has __all or _metadata at top level)
  const isV03Format = isAesPayload(aes);
  const aesPayload = isV03Format ? aes : undefined;

  // Extract from nested aes config (handles both old and v0.3 formats)
  // For v0.3: use __all.base/select/hover
  // For old format: use aes.base/select/hover directly
  const legacyAes = !isV03Format ? (aes as LegacyAesConfig | undefined) : undefined;
  const aesBase = isV03Format
    ? (aesPayload?.__all?.base ?? DEFAULT_AESTHETIC_VALUES)
    : (legacyAes?.base ?? DEFAULT_AESTHETIC_VALUES);
  const aesHover = isV03Format ? aesPayload?.__all?.hover : legacyAes?.hover;
  const aesSelect = isV03Format ? aesPayload?.__all?.select : legacyAes?.select;
  // For v0.3, group aesthetics are in the payload directly (not under .group)
  const aesGroup = isV03Format
    ? undefined // v0.3 uses getAesForRegion instead
    : legacyAes?.group;

  // Extract from nested layers config
  const underlays = layers?.underlays;
  const overlays = layers?.overlays;
  const hidden = layers?.hidden;

  // Extract from nested mode config (supports both string shorthand and full config)
  const normalizedMode = typeof modeConfig === "string" ? { type: modeConfig } : modeConfig;
  const modeType: MapModeType = normalizedMode?.type ?? "multiple";
  const cycle = normalizedMode?.n;
  const maxSelection = normalizedMode?.maxSelection;
  const aesIndexed = normalizedMode?.aesIndexed;

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

  const normalizedFillColor = useMemo(
    () => normalizeFillColor(fillColor, normalizedGeometry),
    [fillColor, normalizedGeometry]
  );
  const [hovered, setHovered] = useState<RegionId | null>(null);
  // Use internal state for counts, initialized from value prop
  const [counts, setCounts] = useState<Record<RegionId, number>>(value ?? {});
  const selected = useMemo(() => buildSelected(counts), [counts]);

  // Sync internal state when value prop changes (for update_map)
  useEffect(() => {
    if (value !== undefined) {
      setCounts(value);
      // Notify Shiny of the new value
      onChange?.(value);
    }
  }, [value, onChange]);

  // Compute effective cycle and max selection from mode config
  // For "cycle" mode, n is required from modeConfig
  if (modeType === "cycle" && (cycle === undefined || cycle < 2)) {
    throw new Error("Cycle mode requires n >= 2");
  }
  const effectiveCycle =
    cycle ??
    (modeType === "single" ? 2 : modeType === "multiple" ? 2 : modeType === "count" ? Infinity : 2);
  const effectiveMax =
    maxSelection ??
    (modeType === "single"
      ? 1
      : modeType === "multiple"
        ? Infinity
        : modeType === "count"
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
          Object.keys(normalizedGeometry).map((key) => [key, key === id ? nextCount : 0])
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

  // Helper to render a non-interactive layer (underlay or overlay)
  const renderNonInteractiveLayer = (regionIds: Set<RegionId>, keyPrefix: string) => {
    return Array.from(regionIds).flatMap((id) => {
      const elements = normalizedGeometry[id];
      if (!elements) return [];

      // Build aesthetic chain: default -> aesBase -> groupAes
      let layerAes: AestheticStyle = { ...DEFAULT_AESTHETIC_VALUES, ...aesBase };
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

      {/* Layer 2: Base layer - interactive regions */}
      <g>
        {Array.from(layerAssignment.base).flatMap((id) => {
          const elements = normalizedGeometry[id];
          if (!elements) return [];

          const tooltip = tooltips?.[id];
          const isHovered = hovered === id;
          const isSelected = selected.has(id);
          const count = counts[id] ?? 0;

          let baseAes: AestheticStyle = { ...DEFAULT_AESTHETIC_VALUES, ...aesBase };

          // Apply group aesthetic if available
          const groupAes = resolveGroupAesthetic(id, aesGroup, geometryMetadata);
          if (groupAes) {
            baseAes = { ...baseAes, ...groupAes };
          }

          // Apply indexed aesthetic if available (for Cycle/Count modes)
          const indexedData = getIndexedDataForRegion(aesIndexed, id, geometryMetadata);
          if (indexedData) {
            const indexedAes = resolveIndexedAesthetic(indexedData, count, cycle);
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

          // Apply fillColor if provided (overrides indexed)
          if (normalizedFillColor && normalizedFillColor[id]) {
            baseAes.fillColor = normalizedFillColor[id];
          }

          // For base layer: do NOT apply aesSelect or selection styling from resolveAesthetic
          if (resolveAesthetic) {
            // Always pass isHovered=false and isSelected=false for base layer
            const overrides = resolveAesthetic({
              id,
              mode: modeType,
              isHovered: false,
              isSelected: false,
              count,
              baseAesthetic: baseAes,
            });
            if (overrides) {
              baseAes = { ...baseAes, ...overrides };
            }
          }

          // Create RenderedRegion to resolve any RelativeExpr
          const region = createRenderedRegion(id, baseAes);

          const extraProps = regionProps?.({
            id,
            mode: modeType,
            isHovered,
            isSelected,
            count,
            baseAesthetic: baseAes,
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
              cursor: "pointer",
              onMouseEnter: handleMouseEnter,
              onMouseLeave: handleMouseLeave,
              onFocus: handleMouseEnter,
              onBlur: handleMouseLeave,
              onClick: () => handleClick(id),
              tooltip,
              extraProps: extraProps as Record<string, unknown>,
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

      {/* Layer 4: Selection layer - selected regions only, non-interactive */}
      {/* Skip selection layer when using aesIndexed (base layer already shows state) */}
      {/* Also skip when no aesSelect is defined - resolveAesthetic handles styling in base layer */}
      <g>
        {!aesIndexed &&
          aesSelect &&
          Array.from(selected).flatMap((id) => {
            // Only render selection overlay for regions in base layer
            if (!layerAssignment.base.has(id)) return [];

            const elements = normalizedGeometry[id];
            if (!elements) return [];

            const count = counts[id] ?? 0;

            // Build base aesthetic
            let baseAes: AestheticStyle = { ...DEFAULT_AESTHETIC_VALUES, ...aesBase };
            const groupAes = resolveGroupAesthetic(id, aesGroup, geometryMetadata);
            if (groupAes) {
              baseAes = { ...baseAes, ...groupAes };
            }
            if (normalizedFillColor && normalizedFillColor[id]) {
              baseAes.fillColor = normalizedFillColor[id];
            }

            // Apply resolveAesthetic to base (without selection state)
            if (resolveAesthetic) {
              const overrides = resolveAesthetic({
                id,
                mode: modeType,
                isHovered: false,
                isSelected: false,
                count,
                baseAesthetic: baseAes,
              });
              if (overrides) {
                baseAes = { ...baseAes, ...overrides };
              }
            }

            // Create base RenderedRegion
            const baseRegion = createRenderedRegion(id, baseAes);

            // Build selection aesthetic on top of base
            const selectAes: AestheticStyle = { ...aesSelect };

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

      {/* Layer 5: Hover layer - hovered region only, non-interactive */}
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
            const groupAes = resolveGroupAesthetic(hovered, aesGroup, geometryMetadata);
            if (groupAes) {
              baseAes = { ...baseAes, ...groupAes };
            }

            // Apply indexed aesthetic if available (for Cycle/Count modes)
            const count = counts[hovered] ?? 0;
            const indexedData = getIndexedDataForRegion(aesIndexed, hovered, geometryMetadata);
            if (indexedData) {
              const indexedAes = resolveIndexedAesthetic(indexedData, count, cycle);
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

            if (normalizedFillColor && normalizedFillColor[hovered]) {
              baseAes.fillColor = normalizedFillColor[hovered];
            }

            // Apply resolveAesthetic to get proper styling (including selection colors)
            if (resolveAesthetic) {
              const overrides = resolveAesthetic({
                id: hovered,
                mode: modeType,
                isHovered: false, // We're building the parent, not hover state
                isSelected: selected.has(hovered),
                count,
                baseAesthetic: baseAes,
              });
              if (overrides) {
                baseAes = { ...baseAes, ...overrides };
              }
            }

            const baseRegion = createRenderedRegion(hovered, baseAes);

            // Step 2: If selected and not using indexed aesthetics, create selection RenderedRegion
            let parentRegion: RenderedRegion = baseRegion;
            if (!aesIndexed && selected.has(hovered) && aesSelect) {
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
