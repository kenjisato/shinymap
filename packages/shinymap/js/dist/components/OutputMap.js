import { jsx as _jsx } from "react/jsx-runtime";
const DEFAULT_VIEWBOX = "0 0 100 100";
const DEFAULT_FILL = "#e2e8f0";
const DEFAULT_STROKE = "#1f2937";
const ACTIVE_STROKE = "#0f172a";
function normalizeActive(active) {
    if (!active) {
        return new Set();
    }
    if (Array.isArray(active)) {
        return new Set(active);
    }
    return new Set([active]);
}
export function OutputMap(props) {
    const { geometry, tooltips, className, style, viewBox = DEFAULT_VIEWBOX, defaultFill = DEFAULT_FILL, stroke = DEFAULT_STROKE, fills, activeIds, onRegionClick, styleForRegion, } = props;
    const activeSet = normalizeActive(activeIds);
    return (_jsx("svg", { role: "img", className: className, style: { width: "100%", height: "100%", ...style }, viewBox: viewBox, children: _jsx("g", { children: Object.entries(geometry).map(([id, d]) => {
                var _a;
                const tooltip = tooltips === null || tooltips === void 0 ? void 0 : tooltips[id];
                const regionFill = (_a = fills === null || fills === void 0 ? void 0 : fills[id]) !== null && _a !== void 0 ? _a : defaultFill;
                const isActive = activeSet.has(id);
                let fill = regionFill;
                let fillOpacity = 1;
                let strokeColor = isActive ? ACTIVE_STROKE : stroke;
                let strokeWidth = isActive ? 2 : 1;
                if (styleForRegion) {
                    const overrides = styleForRegion({
                        id,
                        baseFill: regionFill,
                        isActive,
                        tooltip,
                    });
                    if (overrides.fill !== undefined)
                        fill = overrides.fill;
                    if (overrides.fillOpacity !== undefined)
                        fillOpacity = overrides.fillOpacity;
                    if (overrides.stroke !== undefined)
                        strokeColor = overrides.stroke;
                    if (overrides.strokeWidth !== undefined)
                        strokeWidth = overrides.strokeWidth;
                }
                return (_jsx("path", { d: d, fill: fill, fillOpacity: fillOpacity, stroke: strokeColor, strokeWidth: strokeWidth, onClick: onRegionClick ? () => onRegionClick(id) : undefined, style: onRegionClick ? { cursor: "pointer" } : undefined, children: tooltip ? _jsx("title", { children: tooltip }) : null }, id));
            }) }) }));
}
