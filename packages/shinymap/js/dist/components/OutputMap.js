import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useMemo, useState } from "react";
import { createRenderedRegion, DEFAULT_AESTHETIC_VALUES, DEFAULT_HOVER_AESTHETIC, getIndexedDataForRegion, isAesPayload, resolveIndexedAesthetic, } from "../types";
import { normalizeRegions } from "../utils/regions";
import { assignLayers, resolveGroupAesthetic } from "../utils/layers";
import { renderElement } from "../utils/renderElement";
const DEFAULT_VIEWBOX = "0 0 100 100";
/**
 * Derive active (selected) regions from value map.
 * A region is considered active/selected if its value > 0.
 */
function deriveActiveFromValue(value) {
    if (!value)
        return new Set();
    const active = new Set();
    for (const [id, count] of Object.entries(value)) {
        if (count > 0)
            active.add(id);
    }
    return active;
}
function normalize(value, regions) {
    if (!value)
        return undefined;
    if (typeof value === "object" && !Array.isArray(value)) {
        // Already a dict
        return value;
    }
    // Scalar value - apply to all regions
    return Object.fromEntries(Object.keys(regions).map((id) => [id, value]));
}
export function OutputMap(props) {
    var _a, _b, _c, _d, _e, _f;
    const { regions, tooltips, className, containerStyle, viewBox = DEFAULT_VIEWBOX, mode: modeConfig, aes, layers, outlineMetadata, fillColor, strokeWidth: strokeWidthProp, strokeColor: strokeColorProp, fillOpacity: fillOpacityProp, value, onRegionClick, resolveAesthetic, regionProps, } = props;
    // Extract from nested mode config (supports both string shorthand and full config)
    const normalizedMode = typeof modeConfig === "string" ? { type: modeConfig } : modeConfig;
    const aesIndexed = normalizedMode === null || normalizedMode === void 0 ? void 0 : normalizedMode.aesIndexed;
    // Display mode: clicks only enabled if clickable=true
    const isClickable = (_a = normalizedMode === null || normalizedMode === void 0 ? void 0 : normalizedMode.clickable) !== null && _a !== void 0 ? _a : false;
    // Detect v0.3 payload format (has __all or _metadata at top level)
    const isV03Format = isAesPayload(aes);
    const aesPayload = isV03Format ? aes : undefined;
    // Extract from nested aes config (handles both old and v0.3 formats)
    // For v0.3: use __all.base/select/hover
    // For old format: use aes.base/select/hover directly
    const legacyAes = !isV03Format ? aes : undefined;
    const aesBaseRaw = isV03Format
        ? ((_c = (_b = aesPayload === null || aesPayload === void 0 ? void 0 : aesPayload.__all) === null || _b === void 0 ? void 0 : _b.base) !== null && _c !== void 0 ? _c : DEFAULT_AESTHETIC_VALUES)
        : ((_d = legacyAes === null || legacyAes === void 0 ? void 0 : legacyAes.base) !== null && _d !== void 0 ? _d : DEFAULT_AESTHETIC_VALUES);
    const aesBase = aesBaseRaw;
    const aesHover = isV03Format ? (_e = aesPayload === null || aesPayload === void 0 ? void 0 : aesPayload.__all) === null || _e === void 0 ? void 0 : _e.hover : legacyAes === null || legacyAes === void 0 ? void 0 : legacyAes.hover;
    const aesSelect = isV03Format ? (_f = aesPayload === null || aesPayload === void 0 ? void 0 : aesPayload.__all) === null || _f === void 0 ? void 0 : _f.select : legacyAes === null || legacyAes === void 0 ? void 0 : legacyAes.select;
    const aesNotSelect = legacyAes === null || legacyAes === void 0 ? void 0 : legacyAes.notSelect; // Only in legacy format
    // For v0.3, group aesthetics are in the payload directly (not under .group)
    const aesGroup = isV03Format ? undefined : legacyAes === null || legacyAes === void 0 ? void 0 : legacyAes.group;
    // Extract per-region fill colors from aes.base if it's a dict
    const aesBaseFillColorDict = typeof (aesBaseRaw === null || aesBaseRaw === void 0 ? void 0 : aesBaseRaw.fillColor) === "object" && aesBaseRaw.fillColor !== null
        ? aesBaseRaw.fillColor
        : undefined;
    // Extract from nested layers config
    const underlays = layers === null || layers === void 0 ? void 0 : layers.underlays;
    const overlays = layers === null || layers === void 0 ? void 0 : layers.overlays;
    const hidden = layers === null || layers === void 0 ? void 0 : layers.hidden;
    // Normalize regions to Element[] format (handles both v0.x strings and v1.x polymorphic elements)
    const normalizedRegions = useMemo(() => normalizeRegions(regions), [regions]);
    // New layer system: assign regions to layers
    const layerAssignment = useMemo(() => assignLayers(normalizedRegions, underlays, overlays, hidden, outlineMetadata), [normalizedRegions, underlays, overlays, hidden, outlineMetadata]);
    const [hovered, setHovered] = useState(null);
    // Derive active/selected regions from value (value > 0 means selected)
    const activeSet = deriveActiveFromValue(value);
    const normalizedFillColor = normalize(fillColor, normalizedRegions);
    const normalizedStrokeWidth = normalize(strokeWidthProp, normalizedRegions);
    const normalizedStrokeColor = normalize(strokeColorProp, normalizedRegions);
    const normalizedFillOpacity = normalize(fillOpacityProp, normalizedRegions);
    const countMap = value !== null && value !== void 0 ? value : {};
    // Helper to render a non-interactive layer (underlay or overlay)
    const renderNonInteractiveLayer = (regionIds, keyPrefix) => {
        return Array.from(regionIds).flatMap((id) => {
            const elements = normalizedRegions[id];
            if (!elements)
                return [];
            // Build aesthetic chain: default -> aesBase -> per-region fillColor -> groupAes
            let layerAes = { ...DEFAULT_AESTHETIC_VALUES, ...aesBase };
            if (aesBaseFillColorDict === null || aesBaseFillColorDict === void 0 ? void 0 : aesBaseFillColorDict[id]) {
                layerAes = { ...layerAes, fillColor: aesBaseFillColorDict[id] };
            }
            const groupAes = resolveGroupAesthetic(id, aesGroup, outlineMetadata);
            if (groupAes) {
                layerAes = { ...layerAes, ...groupAes };
            }
            // Create RenderedRegion to resolve any RelativeExpr
            const region = createRenderedRegion(id, layerAes);
            return elements.map((element, index) => renderElement({
                element,
                key: `${keyPrefix}-${id}-${index}`,
                fill: region.aesthetic.fillColor,
                fillOpacity: region.aesthetic.fillOpacity,
                stroke: region.aesthetic.strokeColor,
                strokeWidth: region.aesthetic.strokeWidth,
                strokeDasharray: region.aesthetic.strokeDasharray,
                nonScalingStroke: region.aesthetic.nonScalingStroke,
                pointerEvents: "none",
            }));
        });
    };
    return (_jsxs("svg", { role: "img", className: className, style: { width: "100%", height: "100%", ...containerStyle }, viewBox: viewBox, children: [_jsx("g", { children: renderNonInteractiveLayer(layerAssignment.underlay, "underlay") }), _jsx("g", { children: Array.from(layerAssignment.base).flatMap((id) => {
                    var _a;
                    const elements = normalizedRegions[id];
                    if (!elements)
                        return [];
                    const tooltip = tooltips === null || tooltips === void 0 ? void 0 : tooltips[id];
                    const isActive = activeSet.has(id);
                    const count = (_a = countMap[id]) !== null && _a !== void 0 ? _a : 0;
                    let baseAes = {
                        ...DEFAULT_AESTHETIC_VALUES,
                        ...aesBase,
                    };
                    // Apply per-region fill color from aes.base.fillColor if it's a dict
                    if (aesBaseFillColorDict === null || aesBaseFillColorDict === void 0 ? void 0 : aesBaseFillColorDict[id]) {
                        baseAes = { ...baseAes, fillColor: aesBaseFillColorDict[id] };
                    }
                    // Apply group aesthetic if available
                    const groupAes = resolveGroupAesthetic(id, aesGroup, outlineMetadata);
                    if (groupAes) {
                        baseAes = { ...baseAes, ...groupAes };
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
                        ...((normalizedFillColor === null || normalizedFillColor === void 0 ? void 0 : normalizedFillColor[id]) ? { fillColor: normalizedFillColor[id] } : {}),
                        ...((normalizedStrokeWidth === null || normalizedStrokeWidth === void 0 ? void 0 : normalizedStrokeWidth[id]) !== undefined
                            ? { strokeWidth: normalizedStrokeWidth[id] }
                            : {}),
                        ...((normalizedStrokeColor === null || normalizedStrokeColor === void 0 ? void 0 : normalizedStrokeColor[id]) ? { strokeColor: normalizedStrokeColor[id] } : {}),
                        ...((normalizedFillOpacity === null || normalizedFillOpacity === void 0 ? void 0 : normalizedFillOpacity[id]) !== undefined
                            ? { fillOpacity: normalizedFillOpacity[id] }
                            : {}),
                    };
                    // Apply selection-specific aesthetics (layer 4a)
                    if (isActive && aesSelect) {
                        baseAes = { ...baseAes, ...aesSelect };
                    }
                    else if (!isActive && aesNotSelect) {
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
                        if (overrides)
                            baseAes = { ...baseAes, ...overrides };
                    }
                    // Create RenderedRegion to resolve any RelativeExpr
                    const region = createRenderedRegion(id, baseAes);
                    const regionOverrides = regionProps === null || regionProps === void 0 ? void 0 : regionProps({
                        id,
                        isActive,
                        count,
                        baseAesthetic: baseAes,
                        tooltip,
                    });
                    const handleMouseEnter = () => setHovered(id);
                    const handleMouseLeave = () => setHovered((current) => (current === id ? null : current));
                    // For display mode, only enable clicks if clickable=true
                    const effectiveOnClick = isClickable && onRegionClick ? () => onRegionClick(id) : undefined;
                    // Render each element in the region
                    return elements.map((element, index) => renderElement({
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
                        extraProps: regionOverrides,
                    }));
                }) }), _jsx("g", { children: renderNonInteractiveLayer(layerAssignment.overlay, "overlay") }), _jsx("g", { children: aesSelect &&
                    Array.from(activeSet).flatMap((id) => {
                        var _a;
                        // Only render selection overlay for regions in base layer
                        if (!layerAssignment.base.has(id))
                            return [];
                        const elements = normalizedRegions[id];
                        if (!elements)
                            return [];
                        const count = (_a = countMap[id]) !== null && _a !== void 0 ? _a : 0;
                        // Build base aesthetic
                        let baseAes = {
                            ...DEFAULT_AESTHETIC_VALUES,
                            ...aesBase,
                        };
                        if (aesBaseFillColorDict === null || aesBaseFillColorDict === void 0 ? void 0 : aesBaseFillColorDict[id]) {
                            baseAes = { ...baseAes, fillColor: aesBaseFillColorDict[id] };
                        }
                        const groupAes = resolveGroupAesthetic(id, aesGroup, outlineMetadata);
                        if (groupAes) {
                            baseAes = { ...baseAes, ...groupAes };
                        }
                        baseAes = {
                            ...baseAes,
                            ...((normalizedFillColor === null || normalizedFillColor === void 0 ? void 0 : normalizedFillColor[id]) ? { fillColor: normalizedFillColor[id] } : {}),
                            ...((normalizedStrokeWidth === null || normalizedStrokeWidth === void 0 ? void 0 : normalizedStrokeWidth[id]) !== undefined
                                ? { strokeWidth: normalizedStrokeWidth[id] }
                                : {}),
                            ...((normalizedStrokeColor === null || normalizedStrokeColor === void 0 ? void 0 : normalizedStrokeColor[id]) ? { strokeColor: normalizedStrokeColor[id] } : {}),
                            ...((normalizedFillOpacity === null || normalizedFillOpacity === void 0 ? void 0 : normalizedFillOpacity[id]) !== undefined
                                ? { fillOpacity: normalizedFillOpacity[id] }
                                : {}),
                        };
                        // Create base RenderedRegion
                        const baseRegion = createRenderedRegion(id, baseAes);
                        // Build selection aesthetic on top of base
                        let selectAes = {};
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
                                tooltip: tooltips === null || tooltips === void 0 ? void 0 : tooltips[id],
                            });
                            if (overrides)
                                selectAes = { ...selectAes, ...overrides };
                        }
                        // Create selection RenderedRegion with base as parent
                        const selectRegion = createRenderedRegion(id, selectAes, baseRegion);
                        return elements.map((element, index) => renderElement({
                            element,
                            key: `selection-overlay-${id}-${index}`,
                            fill: selectRegion.aesthetic.fillColor,
                            fillOpacity: selectRegion.aesthetic.fillOpacity,
                            stroke: selectRegion.aesthetic.strokeColor,
                            strokeWidth: selectRegion.aesthetic.strokeWidth,
                            strokeDasharray: selectRegion.aesthetic.strokeDasharray,
                            nonScalingStroke: selectRegion.aesthetic.nonScalingStroke,
                            pointerEvents: "none",
                        }));
                    }) }), _jsx("g", { children: hovered &&
                    aesHover !== null &&
                    layerAssignment.base.has(hovered) &&
                    (() => {
                        var _a;
                        // Determine effective hover aesthetic
                        const effectiveHover = aesHover !== null && aesHover !== void 0 ? aesHover : DEFAULT_HOVER_AESTHETIC;
                        // Build the parent chain for the hovered region
                        // Step 1: Create base RenderedRegion
                        let baseAes = { ...DEFAULT_AESTHETIC_VALUES, ...aesBase };
                        if (aesBaseFillColorDict === null || aesBaseFillColorDict === void 0 ? void 0 : aesBaseFillColorDict[hovered]) {
                            baseAes = { ...baseAes, fillColor: aesBaseFillColorDict[hovered] };
                        }
                        const groupAes = resolveGroupAesthetic(hovered, aesGroup, outlineMetadata);
                        if (groupAes) {
                            baseAes = { ...baseAes, ...groupAes };
                        }
                        baseAes = {
                            ...baseAes,
                            ...((normalizedFillColor === null || normalizedFillColor === void 0 ? void 0 : normalizedFillColor[hovered])
                                ? { fillColor: normalizedFillColor[hovered] }
                                : {}),
                            ...((normalizedStrokeWidth === null || normalizedStrokeWidth === void 0 ? void 0 : normalizedStrokeWidth[hovered]) !== undefined
                                ? { strokeWidth: normalizedStrokeWidth[hovered] }
                                : {}),
                            ...((normalizedStrokeColor === null || normalizedStrokeColor === void 0 ? void 0 : normalizedStrokeColor[hovered])
                                ? { strokeColor: normalizedStrokeColor[hovered] }
                                : {}),
                            ...((normalizedFillOpacity === null || normalizedFillOpacity === void 0 ? void 0 : normalizedFillOpacity[hovered]) !== undefined
                                ? { fillOpacity: normalizedFillOpacity[hovered] }
                                : {}),
                        };
                        const baseRegion = createRenderedRegion(hovered, baseAes);
                        // Step 2: If active, create selection RenderedRegion with base as parent
                        let parentRegion = baseRegion;
                        if (activeSet.has(hovered) && aesSelect) {
                            parentRegion = createRenderedRegion(hovered, aesSelect, baseRegion);
                        }
                        // Step 3: Create hover RenderedRegion with parent chain
                        const hoverRegion = createRenderedRegion(hovered, effectiveHover, parentRegion);
                        // Render using resolved aesthetics
                        return (_a = normalizedRegions[hovered]) === null || _a === void 0 ? void 0 : _a.map((element, index) => {
                            var _a, _b;
                            return renderElement({
                                element,
                                key: `hover-overlay-${hovered}-${index}`,
                                fill: (_a = hoverRegion.aesthetic.fillColor) !== null && _a !== void 0 ? _a : "none",
                                fillOpacity: (_b = hoverRegion.aesthetic.fillOpacity) !== null && _b !== void 0 ? _b : (hoverRegion.aesthetic.fillColor ? 1 : 0),
                                stroke: hoverRegion.aesthetic.strokeColor,
                                strokeWidth: hoverRegion.aesthetic.strokeWidth,
                                strokeDasharray: hoverRegion.aesthetic.strokeDasharray,
                                nonScalingStroke: hoverRegion.aesthetic.nonScalingStroke,
                                pointerEvents: "none",
                            });
                        });
                    })() })] }));
}
