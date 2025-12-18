import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useMemo, useState } from "react";
import { normalizeGeometry } from "../utils/geometry";
const DEFAULT_VIEWBOX = "0 0 100 100";
const DEFAULT_AESTHETIC = {
    fillColor: "#e2e8f0",
    fillOpacity: 1,
    strokeColor: "#334155",
    strokeWidth: 1,
};
function normalizeActive(active) {
    if (!active)
        return new Set();
    if (Array.isArray(active))
        return new Set(active);
    return new Set([active]);
}
function normalize(value, geometry) {
    if (!value)
        return undefined;
    if (typeof value === "object" && !Array.isArray(value)) {
        // Already a dict
        return value;
    }
    // Scalar value - apply to all regions
    return Object.fromEntries(Object.keys(geometry).map((id) => [id, value]));
}
export function OutputMap(props) {
    var _a, _b, _c, _d;
    const { geometry, tooltips, className, containerStyle, viewBox = DEFAULT_VIEWBOX, defaultAesthetic = DEFAULT_AESTHETIC, fillColor, // RENAMED from fills
    strokeWidth: strokeWidthProp, // NEW
    strokeColor: strokeColorProp, // NEW
    fillOpacity: fillOpacityProp, // NEW
    counts, activeIds, onRegionClick, resolveAesthetic, regionProps, fillColorSelected, // RENAMED from selectionAesthetic
    fillColorNotSelected, // RENAMED from notSelectionAesthetic
    overlayGeometry, overlayAesthetic, hoverHighlight, } = props;
    // Normalize geometry to string format (handles both string and string[] paths)
    const normalizedGeometry = useMemo(() => normalizeGeometry(geometry), [geometry]);
    const normalizedOverlayGeometry = useMemo(() => (overlayGeometry ? normalizeGeometry(overlayGeometry) : undefined), [overlayGeometry]);
    const [hovered, setHovered] = useState(null);
    const activeSet = normalizeActive(activeIds);
    const normalizedFillColor = normalize(fillColor, normalizedGeometry);
    const normalizedStrokeWidth = normalize(strokeWidthProp, normalizedGeometry);
    const normalizedStrokeColor = normalize(strokeColorProp, normalizedGeometry);
    const normalizedFillOpacity = normalize(fillOpacityProp, normalizedGeometry);
    const countMap = counts !== null && counts !== void 0 ? counts : {};
    return (_jsx("svg", { role: "img", className: className, style: { width: "100%", height: "100%", ...containerStyle }, viewBox: viewBox, children: _jsxs("g", { children: [Object.entries(normalizedGeometry).map(([id, d]) => {
                    var _a;
                    const tooltip = tooltips === null || tooltips === void 0 ? void 0 : tooltips[id];
                    const isActive = activeSet.has(id);
                    const count = (_a = countMap[id]) !== null && _a !== void 0 ? _a : 0;
                    let resolved = {
                        ...DEFAULT_AESTHETIC,
                        ...defaultAesthetic,
                        ...((normalizedFillColor === null || normalizedFillColor === void 0 ? void 0 : normalizedFillColor[id]) ? { fillColor: normalizedFillColor[id] } : {}),
                        ...((normalizedStrokeWidth === null || normalizedStrokeWidth === void 0 ? void 0 : normalizedStrokeWidth[id]) !== undefined ? { strokeWidth: normalizedStrokeWidth[id] } : {}),
                        ...((normalizedStrokeColor === null || normalizedStrokeColor === void 0 ? void 0 : normalizedStrokeColor[id]) ? { strokeColor: normalizedStrokeColor[id] } : {}),
                        ...((normalizedFillOpacity === null || normalizedFillOpacity === void 0 ? void 0 : normalizedFillOpacity[id]) !== undefined ? { fillOpacity: normalizedFillOpacity[id] } : {}),
                    };
                    // Apply selection-specific aesthetics (layer 4a)
                    if (isActive && fillColorSelected) {
                        resolved = { ...resolved, ...fillColorSelected };
                    }
                    else if (!isActive && fillColorNotSelected) {
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
                        if (overrides)
                            resolved = { ...resolved, ...overrides };
                    }
                    const regionOverrides = regionProps === null || regionProps === void 0 ? void 0 : regionProps({
                        id,
                        isActive,
                        count,
                        baseAesthetic: resolved,
                        tooltip,
                    });
                    const handleMouseEnter = () => setHovered(id);
                    const handleMouseLeave = () => setHovered((current) => (current === id ? null : current));
                    return (_jsx("path", { d: d, fill: resolved.fillColor, fillOpacity: resolved.fillOpacity, stroke: resolved.strokeColor, strokeWidth: resolved.strokeWidth, onClick: onRegionClick ? () => onRegionClick(id) : undefined, onMouseEnter: handleMouseEnter, onMouseLeave: handleMouseLeave, onFocus: handleMouseEnter, onBlur: handleMouseLeave, style: onRegionClick ? { cursor: "pointer" } : undefined, ...regionOverrides, children: tooltip ? _jsx("title", { children: tooltip }) : null }, id));
                }), normalizedOverlayGeometry &&
                    Object.entries(normalizedOverlayGeometry).map(([id, d]) => {
                        const overlayStyle = {
                            ...DEFAULT_AESTHETIC,
                            ...overlayAesthetic,
                        };
                        return (_jsx("path", { d: d, fill: overlayStyle.fillColor, fillOpacity: overlayStyle.fillOpacity, stroke: overlayStyle.strokeColor, strokeWidth: overlayStyle.strokeWidth, pointerEvents: "none" }, `overlay-${id}`));
                    }), Array.from(activeSet).map((id) => {
                    var _a;
                    if (!normalizedGeometry[id])
                        return null;
                    const count = (_a = countMap[id]) !== null && _a !== void 0 ? _a : 0;
                    let resolved = {
                        ...DEFAULT_AESTHETIC,
                        ...defaultAesthetic,
                        ...((normalizedFillColor === null || normalizedFillColor === void 0 ? void 0 : normalizedFillColor[id]) ? { fillColor: normalizedFillColor[id] } : {}),
                        ...((normalizedStrokeWidth === null || normalizedStrokeWidth === void 0 ? void 0 : normalizedStrokeWidth[id]) !== undefined ? { strokeWidth: normalizedStrokeWidth[id] } : {}),
                        ...((normalizedStrokeColor === null || normalizedStrokeColor === void 0 ? void 0 : normalizedStrokeColor[id]) ? { strokeColor: normalizedStrokeColor[id] } : {}),
                        ...((normalizedFillOpacity === null || normalizedFillOpacity === void 0 ? void 0 : normalizedFillOpacity[id]) !== undefined ? { fillOpacity: normalizedFillOpacity[id] } : {}),
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
                            tooltip: tooltips === null || tooltips === void 0 ? void 0 : tooltips[id],
                        });
                        if (overrides)
                            resolved = { ...resolved, ...overrides };
                    }
                    return (_jsx("path", { d: normalizedGeometry[id], fill: resolved.fillColor, fillOpacity: resolved.fillOpacity, stroke: resolved.strokeColor, strokeWidth: resolved.strokeWidth, pointerEvents: "none" }, `selection-overlay-${id}`));
                }), hovered && hoverHighlight && normalizedGeometry[hovered] && (_jsx("path", { d: normalizedGeometry[hovered], fill: (_a = hoverHighlight.fillColor) !== null && _a !== void 0 ? _a : "none", fillOpacity: (_b = hoverHighlight.fillOpacity) !== null && _b !== void 0 ? _b : 0, stroke: (_c = hoverHighlight.strokeColor) !== null && _c !== void 0 ? _c : "#1e40af", strokeWidth: (_d = hoverHighlight.strokeWidth) !== null && _d !== void 0 ? _d : 2, pointerEvents: "none" }, `hover-overlay-${hovered}`))] }) }));
}
