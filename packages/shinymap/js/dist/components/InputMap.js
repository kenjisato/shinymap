import { jsx as _jsx } from "react/jsx-runtime";
import { useMemo, useState } from "react";
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
export function InputMap(props) {
    var _a;
    const { geometry, tooltips, className, containerStyle, viewBox = DEFAULT_VIEWBOX, defaultAesthetic = DEFAULT_AESTHETIC, resolveAesthetic, regionProps, value, onChange, cycle, maxSelection, } = props;
    const [hovered, setHovered] = useState(null);
    const counts = value !== null && value !== void 0 ? value : {};
    const selected = useMemo(() => buildSelected(value), [value]);
    // Determine mode: explicit prop wins; else cycle implies count; else multiple.
    const mode = (_a = props.mode) !== null && _a !== void 0 ? _a : (cycle ? "count" : "multiple");
    const effectiveCycle = cycle !== null && cycle !== void 0 ? cycle : (mode === "single" ? 2 : mode === "multiple" ? 2 : mode === "count" ? Infinity : 2);
    const effectiveMax = maxSelection !== null && maxSelection !== void 0 ? maxSelection : (mode === "single" ? 1 : mode === "multiple" ? Infinity : mode === "count" ? Infinity : Infinity);
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
                const next = Object.fromEntries(Object.keys(geometry).map((key) => [key, key === id ? nextCount : 0]));
                onChange === null || onChange === void 0 ? void 0 : onChange(next);
            }
            // If maxSelection is >1, block new activation to avoid surprise replacements.
            return;
        }
        const next = { ...counts, [id]: nextCount };
        onChange === null || onChange === void 0 ? void 0 : onChange(next);
    };
    return (_jsx("svg", { role: "img", className: className, style: { width: "100%", height: "100%", ...containerStyle }, viewBox: viewBox, children: _jsx("g", { children: Object.entries(geometry).map(([id, d]) => {
                var _a;
                const tooltip = tooltips === null || tooltips === void 0 ? void 0 : tooltips[id];
                const isHovered = hovered === id;
                const isSelected = selected.has(id);
                const count = (_a = counts[id]) !== null && _a !== void 0 ? _a : 0;
                let resolved = { ...DEFAULT_AESTHETIC, ...defaultAesthetic };
                if (resolveAesthetic) {
                    const overrides = resolveAesthetic({
                        id,
                        mode,
                        isHovered,
                        isSelected,
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
                return (_jsx("path", { d: d, fill: resolved.fillColor, fillOpacity: resolved.fillOpacity, stroke: resolved.strokeColor, strokeWidth: resolved.strokeWidth, style: { cursor: "pointer" }, onMouseEnter: handleMouseEnter, onMouseLeave: handleMouseLeave, onFocus: handleMouseEnter, onBlur: handleMouseLeave, onClick: () => handleClick(id), ...extraProps, children: tooltip ? _jsx("title", { children: tooltip }) : null }, id));
            }) }) }));
}
