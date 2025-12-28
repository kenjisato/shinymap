/**
 * Get a value from an indexed array at the given index.
 * If the value is not an array, returns it as-is.
 * For arrays, uses modulo for wrapping (Cycle mode) or clamping (Count mode).
 */
function getIndexedValue(value, index, wrap) {
    if (value === undefined)
        return undefined;
    if (!Array.isArray(value))
        return value;
    if (value.length === 0)
        return undefined;
    const effectiveIndex = wrap ? index % value.length : Math.min(index, value.length - 1);
    return value[effectiveIndex];
}
/**
 * Resolve an IndexedAestheticData to an AestheticStyle for a given count/state.
 *
 * @param data The indexed aesthetic data
 * @param count The current count/state value
 * @param cycle If provided, use modulo wrapping (count % cycle), otherwise clamp
 */
export function resolveIndexedAesthetic(data, count, cycle) {
    const wrap = cycle !== undefined;
    const index = wrap && cycle > 0 ? count % cycle : count;
    return {
        fillColor: getIndexedValue(data.fillColor, index, wrap),
        fillOpacity: getIndexedValue(data.fillOpacity, index, wrap),
        strokeColor: getIndexedValue(data.strokeColor, index, wrap),
        strokeWidth: getIndexedValue(data.strokeWidth, index, wrap),
        strokeDasharray: getIndexedValue(data.strokeDasharray, index, wrap),
    };
}
/**
 * Get the IndexedAestheticData for a region from an AesIndexedConfig.
 * Returns undefined if no indexed aesthetic applies to this region.
 */
export function getIndexedDataForRegion(config, regionId, geometryMetadata) {
    if (!config)
        return undefined;
    if (config.type === "indexed") {
        return config.value;
    }
    // type === "byGroup"
    // First check if region ID matches directly
    if (config.groups[regionId]) {
        return config.groups[regionId];
    }
    // Check if region belongs to a group that has indexed aesthetic
    if (geometryMetadata === null || geometryMetadata === void 0 ? void 0 : geometryMetadata.groups) {
        for (const [groupName, regionIds] of Object.entries(geometryMetadata.groups)) {
            if (regionIds.includes(regionId) && config.groups[groupName]) {
                return config.groups[groupName];
            }
        }
    }
    return undefined;
}
/**
 * Check if a value is a RelativeExpr object.
 */
export function isRelativeExpr(value) {
    return (typeof value === "object" &&
        value !== null &&
        "__relative__" in value &&
        value.__relative__ === true);
}
/**
 * Resolve a RelativeExpr against a parent value.
 */
export function resolveRelativeExpr(expr, parentValue) {
    switch (expr.operator) {
        case "+":
            return parentValue + expr.operand;
        case "-":
            return parentValue - expr.operand;
        case "*":
            return parentValue * expr.operand;
        case "/":
            return expr.operand !== 0 ? parentValue / expr.operand : parentValue;
        default:
            return parentValue;
    }
}
/**
 * Resolve a value that may be a RelativeExpr or a concrete value.
 */
export function resolveValue(value, parentValue, fallback) {
    if (value === undefined) {
        return fallback;
    }
    if (isRelativeExpr(value)) {
        return resolveRelativeExpr(value, parentValue !== null && parentValue !== void 0 ? parentValue : fallback);
    }
    return value;
}
/**
 * Reserved aesthetic values used as the root of the chain.
 *
 * These are intentionally subtle/neutral - they serve as fallback values
 * when no aesthetics are explicitly provided. For Python Shiny apps,
 * the library defaults are provided via wash() in Python.
 *
 * React developers should use LIBRARY_AESTHETIC_DEFAULTS for a complete
 * out-of-box experience, or define their own aesthetics.
 */
export const DEFAULT_AESTHETIC_VALUES = {
    fillColor: "#f1f5f9", // slate-100: subtle, reserved default
    fillOpacity: 1,
    strokeColor: "#94a3b8", // slate-400: subtle border
    strokeWidth: 0.5,
    strokeDasharray: "",
    nonScalingStroke: false,
};
/**
 * Library defaults for React developers.
 *
 * Use these for a polished out-of-box experience. Equivalent to Python's
 * library-supplied input_map/output_map defaults.
 *
 * Usage:
 *   <InputMap
 *     aesBase={LIBRARY_AESTHETIC_DEFAULTS.base}
 *     aesSelect={LIBRARY_AESTHETIC_DEFAULTS.select}
 *     aesHover={LIBRARY_AESTHETIC_DEFAULTS.hover}
 *     ...
 *   />
 */
export const LIBRARY_AESTHETIC_DEFAULTS = {
    base: {
        fillColor: "#e2e8f0", // slate-200: neutral base
        strokeColor: "#94a3b8", // slate-400: subtle border
        strokeWidth: 0.5,
    },
    select: {
        fillColor: "#bfdbfe", // blue-200: selected highlight
        strokeColor: "#1e40af", // blue-800: strong border
        strokeWidth: 1,
    },
    hover: {
        strokeColor: "#475569", // slate-600: darker border on hover
        strokeWidth: {
            __relative__: true,
            property: "strokeWidth",
            operator: "+",
            operand: 0.5,
        },
    },
    line: {
        fillColor: "none",
        strokeColor: "#94a3b8", // slate-400
        strokeWidth: 0.5,
    },
    text: {
        fillColor: "#1e293b", // slate-800
    },
};
/**
 * Default hover aesthetic - applied when aesHover is not provided.
 *
 * Uses RelativeExpr to add to parent stroke width, creating a subtle
 * but visible hover effect that works with any stroke width.
 *
 * To disable hover entirely, pass aesHover={null} explicitly.
 */
export const DEFAULT_HOVER_AESTHETIC = {
    strokeWidth: {
        __relative__: true,
        property: "strokeWidth",
        operator: "+",
        operand: 1,
    },
};
/**
 * Resolve a numeric property value, walking up the parent chain if needed.
 */
function resolveNumericProperty(value, parent, key, fallback) {
    var _a, _b;
    if (value === undefined) {
        return (_a = parent === null || parent === void 0 ? void 0 : parent.aesthetic[key]) !== null && _a !== void 0 ? _a : fallback;
    }
    if (isRelativeExpr(value)) {
        const parentValue = (_b = parent === null || parent === void 0 ? void 0 : parent.aesthetic[key]) !== null && _b !== void 0 ? _b : fallback;
        return resolveRelativeExpr(value, parentValue);
    }
    return value;
}
/**
 * Resolve a string property value, inheriting from parent if undefined.
 *
 * Special handling for null: converts to "none" for SVG fill/stroke attributes.
 * This allows Python to send fill_color=None to disable fill.
 */
function resolveStringProperty(value, parent, key, fallback) {
    var _a;
    // null means "none" in SVG (disables fill/stroke)
    if (value === null) {
        return "none";
    }
    if (value === undefined) {
        return (_a = parent === null || parent === void 0 ? void 0 : parent.aesthetic[key]) !== null && _a !== void 0 ? _a : fallback;
    }
    return value;
}
/**
 * Create a RenderedRegion by resolving an AestheticStyle against a parent.
 */
export function createRenderedRegion(id, aes, parent) {
    var _a, _b;
    const resolved = {
        fillColor: resolveStringProperty(aes.fillColor, parent, "fillColor", DEFAULT_AESTHETIC_VALUES.fillColor),
        fillOpacity: resolveNumericProperty(aes.fillOpacity, parent, "fillOpacity", DEFAULT_AESTHETIC_VALUES.fillOpacity),
        strokeColor: resolveStringProperty(aes.strokeColor, parent, "strokeColor", DEFAULT_AESTHETIC_VALUES.strokeColor),
        strokeWidth: resolveNumericProperty(aes.strokeWidth, parent, "strokeWidth", DEFAULT_AESTHETIC_VALUES.strokeWidth),
        strokeDasharray: resolveStringProperty(aes.strokeDasharray, parent, "strokeDasharray", DEFAULT_AESTHETIC_VALUES.strokeDasharray),
        nonScalingStroke: (_b = (_a = aes.nonScalingStroke) !== null && _a !== void 0 ? _a : parent === null || parent === void 0 ? void 0 : parent.aesthetic.nonScalingStroke) !== null && _b !== void 0 ? _b : DEFAULT_AESTHETIC_VALUES.nonScalingStroke,
    };
    return { id, aesthetic: resolved, parent };
}
