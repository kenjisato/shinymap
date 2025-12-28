import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useMemo, useState } from "react";
import { createRenderedRegion, DEFAULT_AESTHETIC_VALUES, DEFAULT_HOVER_AESTHETIC, getIndexedDataForRegion, resolveIndexedAesthetic } from "../types";
import { normalizeGeometry } from "../utils/geometry";
import { assignLayers, resolveGroupAesthetic } from "../utils/layers";
import { renderElement } from "../utils/renderElement";
const DEFAULT_VIEWBOX = "0 0 100 100";
function buildSelected(value) {
    const set = new Set();
    if (!value)
        return set;
    Object.entries(value).forEach(([id, val]) => {
        if (val > 0)
            set.add(id);
    });
    return set;
}
function normalizeFillColor(fillColor, geometry) {
    if (!fillColor)
        return undefined;
    if (typeof fillColor === "string") {
        return Object.fromEntries(Object.keys(geometry).map((id) => [id, fillColor]));
    }
    return fillColor;
}
export function InputMap(props) {
    var _a, _b;
    const { geometry, tooltips, fillColor, className, containerStyle, viewBox = DEFAULT_VIEWBOX, mode: modeConfig, aes, layers, geometryMetadata, value, onChange, resolveAesthetic, regionProps, 
    // Deprecated props (for backward compatibility)
    overlayGeometry, overlayAesthetic, } = props;
    // Extract from nested aes config
    const aesBase = (_a = aes === null || aes === void 0 ? void 0 : aes.base) !== null && _a !== void 0 ? _a : DEFAULT_AESTHETIC_VALUES;
    const aesHover = aes === null || aes === void 0 ? void 0 : aes.hover;
    const aesSelect = aes === null || aes === void 0 ? void 0 : aes.select;
    const aesGroup = aes === null || aes === void 0 ? void 0 : aes.group;
    // Extract from nested layers config
    const underlays = layers === null || layers === void 0 ? void 0 : layers.underlays;
    const overlays = layers === null || layers === void 0 ? void 0 : layers.overlays;
    const hidden = layers === null || layers === void 0 ? void 0 : layers.hidden;
    // Extract from nested mode config
    const modeType = (_b = modeConfig === null || modeConfig === void 0 ? void 0 : modeConfig.type) !== null && _b !== void 0 ? _b : "multiple";
    const cycle = modeConfig === null || modeConfig === void 0 ? void 0 : modeConfig.n;
    const maxSelection = modeConfig === null || modeConfig === void 0 ? void 0 : modeConfig.maxSelection;
    const aesIndexed = modeConfig === null || modeConfig === void 0 ? void 0 : modeConfig.aesIndexed;
    // Normalize geometry to Element[] format (handles both v0.x strings and v1.x polymorphic elements)
    const normalizedGeometry = useMemo(() => normalizeGeometry(geometry), [geometry]);
    // Legacy overlay support (deprecated)
    const normalizedOverlayGeometry = useMemo(() => (overlayGeometry ? normalizeGeometry(overlayGeometry) : undefined), [overlayGeometry]);
    // New layer system: assign regions to layers
    const layerAssignment = useMemo(() => assignLayers(normalizedGeometry, underlays, overlays, hidden, geometryMetadata), [normalizedGeometry, underlays, overlays, hidden, geometryMetadata]);
    const normalizedFillColor = useMemo(() => normalizeFillColor(fillColor, normalizedGeometry), [fillColor, normalizedGeometry]);
    const [hovered, setHovered] = useState(null);
    // Use internal state for counts, initialized from value prop
    const [counts, setCounts] = useState(value !== null && value !== void 0 ? value : {});
    const selected = useMemo(() => buildSelected(counts), [counts]);
    // Sync internal state when value prop changes (for update_map)
    useEffect(() => {
        if (value !== undefined) {
            setCounts(value);
            // Notify Shiny of the new value
            onChange === null || onChange === void 0 ? void 0 : onChange(value);
        }
    }, [value, onChange]);
    // Compute effective cycle and max selection from mode config
    // For "cycle" mode, n is required from modeConfig
    if (modeType === "cycle" && (cycle === undefined || cycle < 2)) {
        throw new Error("Cycle mode requires n >= 2");
    }
    const effectiveCycle = cycle !== null && cycle !== void 0 ? cycle : (modeType === "single" ? 2 : modeType === "multiple" ? 2 : modeType === "count" ? Infinity : 2);
    const effectiveMax = maxSelection !== null && maxSelection !== void 0 ? maxSelection : (modeType === "single"
        ? 1
        : modeType === "multiple"
            ? Infinity
            : modeType === "count"
                ? Infinity
                : Infinity);
    const handleClick = (id) => {
        var _a;
        const current = (_a = counts[id]) !== null && _a !== void 0 ? _a : 0;
        const nextCount = effectiveCycle && Number.isFinite(effectiveCycle) && effectiveCycle > 0
            ? (current + 1) % effectiveCycle
            : current + 1;
        const activeCount = selected.size;
        const isActivating = current === 0 && nextCount > 0;
        const maxSel = Number.isFinite(effectiveMax) ? effectiveMax : Infinity;
        if (isActivating && activeCount >= maxSel) {
            if (maxSel === 1) {
                // Replace the active region with the newly clicked one.
                const next = Object.fromEntries(Object.keys(normalizedGeometry).map((key) => [key, key === id ? nextCount : 0]));
                setCounts(next);
                onChange === null || onChange === void 0 ? void 0 : onChange(next);
            }
            // If maxSelection is >1, block new activation to avoid surprise replacements.
            return;
        }
        const next = { ...counts, [id]: nextCount };
        setCounts(next);
        onChange === null || onChange === void 0 ? void 0 : onChange(next);
    };
    // Helper to render a non-interactive layer (underlay or overlay)
    const renderNonInteractiveLayer = (regionIds, keyPrefix) => {
        return Array.from(regionIds).flatMap((id) => {
            const elements = normalizedGeometry[id];
            if (!elements)
                return [];
            // Build aesthetic chain: default -> aesBase -> groupAes
            let layerAes = { ...DEFAULT_AESTHETIC_VALUES, ...aesBase };
            const groupAes = resolveGroupAesthetic(id, aesGroup, geometryMetadata);
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
                    const elements = normalizedGeometry[id];
                    if (!elements)
                        return [];
                    const tooltip = tooltips === null || tooltips === void 0 ? void 0 : tooltips[id];
                    const isHovered = hovered === id;
                    const isSelected = selected.has(id);
                    const count = (_a = counts[id]) !== null && _a !== void 0 ? _a : 0;
                    let baseAes = { ...DEFAULT_AESTHETIC_VALUES, ...aesBase };
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
                            ...(indexedAes.fillOpacity !== undefined ? { fillOpacity: indexedAes.fillOpacity } : {}),
                            ...(indexedAes.strokeColor !== undefined ? { strokeColor: indexedAes.strokeColor } : {}),
                            ...(indexedAes.strokeWidth !== undefined ? { strokeWidth: indexedAes.strokeWidth } : {}),
                            ...(indexedAes.strokeDasharray !== undefined ? { strokeDasharray: indexedAes.strokeDasharray } : {}),
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
                    const extraProps = regionProps === null || regionProps === void 0 ? void 0 : regionProps({
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
                    return elements.map((element, index) => renderElement({
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
                        extraProps: extraProps,
                    }));
                }) }), normalizedOverlayGeometry && (_jsx("g", { children: Object.entries(normalizedOverlayGeometry).flatMap(([id, elements]) => {
                    const overlayAes = {
                        ...DEFAULT_AESTHETIC_VALUES,
                        ...overlayAesthetic,
                    };
                    const region = createRenderedRegion(id, overlayAes);
                    return elements.map((element, index) => renderElement({
                        element,
                        key: `legacy-overlay-${id}-${index}`,
                        fill: region.aesthetic.fillColor,
                        fillOpacity: region.aesthetic.fillOpacity,
                        stroke: region.aesthetic.strokeColor,
                        strokeWidth: region.aesthetic.strokeWidth,
                        strokeDasharray: region.aesthetic.strokeDasharray,
                        nonScalingStroke: region.aesthetic.nonScalingStroke,
                        pointerEvents: "none",
                    }));
                }) })), _jsx("g", { children: renderNonInteractiveLayer(layerAssignment.overlay, "overlay") }), _jsx("g", { children: !aesIndexed && Array.from(selected).flatMap((id) => {
                    // Only render selection overlay for regions in base layer
                    if (!layerAssignment.base.has(id))
                        return [];
                    const elements = normalizedGeometry[id];
                    if (!elements)
                        return [];
                    // Build base aesthetic
                    let baseAes = { ...DEFAULT_AESTHETIC_VALUES, ...aesBase };
                    const groupAes = resolveGroupAesthetic(id, aesGroup, geometryMetadata);
                    if (groupAes) {
                        baseAes = { ...baseAes, ...groupAes };
                    }
                    if (normalizedFillColor && normalizedFillColor[id]) {
                        baseAes.fillColor = normalizedFillColor[id];
                    }
                    // Create base RenderedRegion
                    const baseRegion = createRenderedRegion(id, baseAes);
                    // Build selection aesthetic on top of base
                    // Note: aesSelect takes precedence - resolveAesthetic is for base layer styling only
                    let selectAes = {};
                    if (aesSelect) {
                        selectAes = { ...aesSelect };
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
                        var _a, _b;
                        // Determine effective hover aesthetic
                        const effectiveHover = aesHover !== null && aesHover !== void 0 ? aesHover : DEFAULT_HOVER_AESTHETIC;
                        // Build the parent chain for the hovered region
                        // Step 1: Create base RenderedRegion
                        let baseAes = { ...DEFAULT_AESTHETIC_VALUES, ...aesBase };
                        const groupAes = resolveGroupAesthetic(hovered, aesGroup, geometryMetadata);
                        if (groupAes) {
                            baseAes = { ...baseAes, ...groupAes };
                        }
                        // Apply indexed aesthetic if available (for Cycle/Count modes)
                        const count = (_a = counts[hovered]) !== null && _a !== void 0 ? _a : 0;
                        const indexedData = getIndexedDataForRegion(aesIndexed, hovered, geometryMetadata);
                        if (indexedData) {
                            const indexedAes = resolveIndexedAesthetic(indexedData, count, cycle);
                            baseAes = {
                                ...baseAes,
                                ...(indexedAes.fillColor !== undefined ? { fillColor: indexedAes.fillColor } : {}),
                                ...(indexedAes.fillOpacity !== undefined ? { fillOpacity: indexedAes.fillOpacity } : {}),
                                ...(indexedAes.strokeColor !== undefined ? { strokeColor: indexedAes.strokeColor } : {}),
                                ...(indexedAes.strokeWidth !== undefined ? { strokeWidth: indexedAes.strokeWidth } : {}),
                                ...(indexedAes.strokeDasharray !== undefined ? { strokeDasharray: indexedAes.strokeDasharray } : {}),
                            };
                        }
                        if (normalizedFillColor && normalizedFillColor[hovered]) {
                            baseAes.fillColor = normalizedFillColor[hovered];
                        }
                        const baseRegion = createRenderedRegion(hovered, baseAes);
                        // Step 2: If selected and not using indexed aesthetics, create selection RenderedRegion
                        let parentRegion = baseRegion;
                        if (!aesIndexed && selected.has(hovered) && aesSelect) {
                            parentRegion = createRenderedRegion(hovered, aesSelect, baseRegion);
                        }
                        // Step 3: Create hover RenderedRegion with parent chain
                        const hoverRegion = createRenderedRegion(hovered, effectiveHover, parentRegion);
                        // Render using resolved aesthetics
                        return (_b = normalizedGeometry[hovered]) === null || _b === void 0 ? void 0 : _b.map((element, index) => {
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
