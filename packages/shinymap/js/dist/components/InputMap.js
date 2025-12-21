import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
import { useEffect, useMemo, useState } from "react";
import { normalizeGeometry } from "../utils/geometry";
import { renderElement } from "../utils/renderElement";
const DEFAULT_VIEWBOX = "0 0 100 100";
const DEFAULT_AESTHETIC = {
    fillColor: "#e2e8f0",
    fillOpacity: 1,
    strokeColor: "#334155",
    strokeWidth: 1,
};
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
    const { geometry, tooltips, fillColor, className, containerStyle, viewBox = DEFAULT_VIEWBOX, defaultAesthetic = DEFAULT_AESTHETIC, resolveAesthetic, regionProps, value, onChange, cycle, maxSelection, overlayGeometry, overlayAesthetic, hoverHighlight, selectedAesthetic, } = props;
    // Normalize geometry to Element[] format (handles both v0.x strings and v1.x polymorphic elements)
    const normalizedGeometry = useMemo(() => normalizeGeometry(geometry), [geometry]);
    const normalizedOverlayGeometry = useMemo(() => (overlayGeometry ? normalizeGeometry(overlayGeometry) : undefined), [overlayGeometry]);
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
    // Determine mode: explicit prop wins; else cycle implies count; else multiple.
    const mode = (_a = props.mode) !== null && _a !== void 0 ? _a : (cycle ? "count" : "multiple");
    const effectiveCycle = cycle !== null && cycle !== void 0 ? cycle : (mode === "single" ? 2 : mode === "multiple" ? 2 : mode === "count" ? Infinity : 2);
    const effectiveMax = maxSelection !== null && maxSelection !== void 0 ? maxSelection : (mode === "single"
        ? 1
        : mode === "multiple"
            ? Infinity
            : mode === "count"
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
    return (_jsxs("svg", { role: "img", className: className, style: { width: "100%", height: "100%", ...containerStyle }, viewBox: viewBox, children: [_jsxs("g", { children: [Object.entries(normalizedGeometry).flatMap(([id, elements]) => {
                        var _a;
                        const tooltip = tooltips === null || tooltips === void 0 ? void 0 : tooltips[id];
                        const isHovered = hovered === id;
                        const isSelected = selected.has(id);
                        const count = (_a = counts[id]) !== null && _a !== void 0 ? _a : 0;
                        let resolved = { ...DEFAULT_AESTHETIC, ...defaultAesthetic };
                        // Apply fillColor if provided
                        if (normalizedFillColor && normalizedFillColor[id]) {
                            resolved.fillColor = normalizedFillColor[id];
                        }
                        // For base layer: do NOT apply selectedAesthetic or selection styling from resolveAesthetic
                        if (resolveAesthetic) {
                            // Always pass isHovered=false and isSelected=false for base layer
                            const overrides = resolveAesthetic({
                                id,
                                mode,
                                isHovered: false,
                                isSelected: false,
                                count,
                                baseAesthetic: resolved,
                            });
                            if (overrides) {
                                resolved = { ...resolved, ...overrides };
                            }
                        }
                        const extraProps = regionProps === null || regionProps === void 0 ? void 0 : regionProps({
                            id,
                            mode,
                            isHovered,
                            isSelected,
                            count,
                            baseAesthetic: resolved,
                        });
                        const handleMouseEnter = () => setHovered(id);
                        const handleMouseLeave = () => setHovered((current) => (current === id ? null : current));
                        // Render each element in the region
                        return elements.map((element, index) => renderElement({
                            element,
                            key: `${id}-${index}`,
                            fill: resolved.fillColor,
                            fillOpacity: resolved.fillOpacity,
                            stroke: resolved.strokeColor,
                            strokeWidth: resolved.strokeWidth,
                            cursor: "pointer",
                            onMouseEnter: handleMouseEnter,
                            onMouseLeave: handleMouseLeave,
                            onFocus: handleMouseEnter,
                            onBlur: handleMouseLeave,
                            onClick: () => handleClick(id),
                            tooltip,
                            extraProps: extraProps,
                        }));
                    }), normalizedOverlayGeometry &&
                        Object.entries(normalizedOverlayGeometry).flatMap(([id, elements]) => {
                            const overlayStyle = {
                                ...DEFAULT_AESTHETIC,
                                ...overlayAesthetic,
                            };
                            return elements.map((element, index) => renderElement({
                                element,
                                key: `overlay-${id}-${index}`,
                                fill: overlayStyle.fillColor,
                                fillOpacity: overlayStyle.fillOpacity,
                                stroke: overlayStyle.strokeColor,
                                strokeWidth: overlayStyle.strokeWidth,
                                pointerEvents: "none",
                            }));
                        })] }), _jsx("g", { children: Array.from(selected).flatMap((id) => {
                    var _a;
                    const elements = normalizedGeometry[id];
                    if (!elements)
                        return [];
                    const count = (_a = counts[id]) !== null && _a !== void 0 ? _a : 0;
                    let resolved = { ...DEFAULT_AESTHETIC, ...defaultAesthetic };
                    // Apply fillColor if provided
                    if (normalizedFillColor && normalizedFillColor[id]) {
                        resolved.fillColor = normalizedFillColor[id];
                    }
                    // Apply selectedAesthetic if provided
                    if (selectedAesthetic) {
                        resolved = { ...resolved, ...selectedAesthetic };
                    }
                    // Apply resolveAesthetic with isSelected=true
                    if (resolveAesthetic) {
                        const overrides = resolveAesthetic({
                            id,
                            mode,
                            isHovered: false,
                            isSelected: true,
                            count,
                            baseAesthetic: resolved,
                        });
                        if (overrides) {
                            resolved = { ...resolved, ...overrides };
                        }
                    }
                    return elements.map((element, index) => renderElement({
                        element,
                        key: `selection-overlay-${id}-${index}`,
                        fill: resolved.fillColor,
                        fillOpacity: resolved.fillOpacity,
                        stroke: resolved.strokeColor,
                        strokeWidth: resolved.strokeWidth,
                        pointerEvents: "none",
                    }));
                }) }), _jsx("g", { children: hovered &&
                    hoverHighlight &&
                    ((_b = normalizedGeometry[hovered]) === null || _b === void 0 ? void 0 : _b.map((element, index) => {
                        var _a, _b, _c, _d;
                        return renderElement({
                            element,
                            key: `hover-overlay-${hovered}-${index}`,
                            fill: (_a = hoverHighlight.fillColor) !== null && _a !== void 0 ? _a : "none",
                            fillOpacity: (_b = hoverHighlight.fillOpacity) !== null && _b !== void 0 ? _b : (hoverHighlight.fillColor ? 1 : 0),
                            stroke: (_c = hoverHighlight.strokeColor) !== null && _c !== void 0 ? _c : "#1e40af",
                            strokeWidth: (_d = hoverHighlight.strokeWidth) !== null && _d !== void 0 ? _d : 2,
                            pointerEvents: "none",
                        });
                    })) })] }));
}
