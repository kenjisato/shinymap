import { jsx as _jsx } from "react/jsx-runtime";
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
export function OutputMap(props) {
    const { geometry, tooltips, className, containerStyle, viewBox = DEFAULT_VIEWBOX, defaultAesthetic = DEFAULT_AESTHETIC, fills, counts, activeIds, onRegionClick, resolveAesthetic, regionProps, } = props;
    const activeSet = normalizeActive(activeIds);
    const countMap = counts !== null && counts !== void 0 ? counts : {};
    return (_jsx("svg", { role: "img", className: className, style: { width: "100%", height: "100%", ...containerStyle }, viewBox: viewBox, children: _jsx("g", { children: Object.entries(geometry).map(([id, d]) => {
                var _a;
                const tooltip = tooltips === null || tooltips === void 0 ? void 0 : tooltips[id];
                const isActive = activeSet.has(id);
                const count = (_a = countMap[id]) !== null && _a !== void 0 ? _a : 0;
                let resolved = {
                    ...DEFAULT_AESTHETIC,
                    ...defaultAesthetic,
                    ...((fills === null || fills === void 0 ? void 0 : fills[id]) ? { fillColor: fills[id] } : {}),
                };
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
                return (_jsx("path", { d: d, fill: resolved.fillColor, fillOpacity: resolved.fillOpacity, stroke: resolved.strokeColor, strokeWidth: resolved.strokeWidth, onClick: onRegionClick ? () => onRegionClick(id) : undefined, style: onRegionClick ? { cursor: "pointer" } : undefined, ...regionOverrides, children: tooltip ? _jsx("title", { children: tooltip }) : null }, id));
            }) }) }));
}
