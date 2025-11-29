import { jsx as _jsx } from "react/jsx-runtime";
import { useMemo, useState } from "react";
import { applyAlpha } from "../utils/color";
const DEFAULT_VIEWBOX = "0 0 100 100";
const DEFAULT_FILL = "#e2e8f0"; // slate-200
const DEFAULT_STROKE = "#334155"; // slate-700
const DEFAULT_HIGHLIGHT = "#2563eb"; // blue-600
const DEFAULT_HOVER = "#38bdf8"; // sky-400
function isMultiple(props) {
    return props.mode === "multiple";
}
function isCount(props) {
    return props.mode === "count";
}
function isSingle(props) {
    return !props.mode || props.mode === "single";
}
function deriveCountInfo(value) {
    if (!value) {
        return { map: {}, max: 0 };
    }
    let max = 0;
    for (const count of Object.values(value)) {
        if (count > max) {
            max = count;
        }
    }
    return { map: { ...value }, max };
}
function computeCountAlpha(id, info, explicitMax) {
    var _a;
    const count = (_a = info.map[id]) !== null && _a !== void 0 ? _a : 0;
    const max = explicitMax !== null && explicitMax !== void 0 ? explicitMax : info.max;
    if (max <= 0) {
        return 0;
    }
    return Math.max(0, Math.min(1, count / max));
}
export function InputMap(props) {
    var _a;
    const { geometry, tooltips, className, style, viewBox = DEFAULT_VIEWBOX, defaultFill = DEFAULT_FILL, stroke = DEFAULT_STROKE, highlightFill = DEFAULT_HIGHLIGHT, hoverFill = DEFAULT_HOVER, } = props;
    const [hovered, setHovered] = useState(null);
    const selectedSet = useMemo(() => {
        var _a, _b, _c;
        if (isMultiple(props)) {
            return new Set((_a = props.value) !== null && _a !== void 0 ? _a : []);
        }
        if (isCount(props)) {
            const counts = (_b = props.value) !== null && _b !== void 0 ? _b : {};
            const selected = new Set();
            Object.entries(counts).forEach(([id, val]) => {
                if (val > 0) {
                    selected.add(id);
                }
            });
            return selected;
        }
        const single = (_c = props.value) !== null && _c !== void 0 ? _c : null;
        return single ? new Set([single]) : new Set();
    }, [props]);
    const countInfo = useMemo(() => {
        if (isCount(props)) {
            return deriveCountInfo(props.value);
        }
        return { map: {}, max: 0 };
    }, [props]);
    const handleClick = (id) => {
        var _a, _b, _c, _d, _e, _f, _g;
        if (isMultiple(props)) {
            const next = new Set((_a = props.value) !== null && _a !== void 0 ? _a : []);
            if (next.has(id)) {
                next.delete(id);
            }
            else {
                next.add(id);
            }
            (_b = props.onChange) === null || _b === void 0 ? void 0 : _b.call(props, Array.from(next));
            return;
        }
        if (isCount(props)) {
            const current = (_c = props.value) !== null && _c !== void 0 ? _c : {};
            const next = { ...current, [id]: ((_d = current[id]) !== null && _d !== void 0 ? _d : 0) + 1 };
            (_e = props.onChange) === null || _e === void 0 ? void 0 : _e.call(props, next);
            return;
        }
        if (isSingle(props)) {
            const current = (_f = props.value) !== null && _f !== void 0 ? _f : null;
            const next = current === id ? null : id;
            (_g = props.onChange) === null || _g === void 0 ? void 0 : _g.call(props, next);
        }
    };
    const maxCount = isCount(props) ? (_a = props.maxCount) !== null && _a !== void 0 ? _a : countInfo.max : 0;
    return (_jsx("svg", { role: "img", className: className, style: { width: "100%", height: "100%", ...style }, viewBox: viewBox, children: _jsx("g", { children: Object.entries(geometry).map(([id, d]) => {
                const tooltip = tooltips === null || tooltips === void 0 ? void 0 : tooltips[id];
                const isHovered = hovered === id;
                const isSelected = selectedSet.has(id);
                let fill = defaultFill;
                if (isCount(props)) {
                    const alpha = computeCountAlpha(id, countInfo, props.maxCount);
                    if (alpha > 0) {
                        fill = applyAlpha(highlightFill, alpha, defaultFill);
                    }
                }
                else if (isSelected) {
                    fill = highlightFill;
                }
                if (isHovered) {
                    fill = hoverFill;
                }
                const handleMouseEnter = () => setHovered(id);
                const handleMouseLeave = () => setHovered((current) => (current === id ? null : current));
                return (_jsx("path", { d: d, fill: fill, stroke: stroke, strokeWidth: isSelected ? 2 : 1, style: { cursor: "pointer" }, onMouseEnter: handleMouseEnter, onMouseLeave: handleMouseLeave, onFocus: handleMouseEnter, onBlur: handleMouseLeave, onClick: () => handleClick(id), children: tooltip ? _jsx("title", { children: tooltip }) : null }, id));
            }) }) }));
}
