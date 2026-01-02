/**
 * Case conversion utilities for Python-JS bridge.
 *
 * Python sends snake_case keys, React expects camelCase.
 * These utilities handle the conversion at the JS boundary.
 */
/**
 * Convert a snake_case string to camelCase.
 *
 * @example
 * snakeToCamel("view_box") // "viewBox"
 * snakeToCamel("outline_metadata") // "outlineMetadata"
 */
export function snakeToCamel(str) {
    return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}
/**
 * Keys that contain region IDs as sub-keys (don't convert those sub-keys).
 */
const REGION_ID_CONTAINERS = new Set([
    "regions",
    "tooltips",
    "value",
    "fill_color",
    "fillColor",
    "stroke_color",
    "strokeColor",
    "stroke_width",
    "strokeWidth",
    "fill_opacity",
    "fillOpacity",
]);
/**
 * Keys that should NOT be converted (preserve exactly).
 * These are special v0.3 payload keys that start with underscore.
 */
function shouldPreserveKey(key) {
    // Preserve keys starting with __ (like __all, __shape, __line, __text)
    // Preserve keys starting with _ (like _metadata)
    return key.startsWith("_");
}
/**
 * Check if a key contains region IDs that shouldn't have case conversion.
 */
function isRegionIdContainer(key) {
    return REGION_ID_CONTAINERS.has(key);
}
/**
 * Convert values in an object without changing keys.
 * Used for containers where keys are region IDs.
 */
function convertValuesOnly(obj) {
    if (obj === null || obj === undefined) {
        return obj;
    }
    if (Array.isArray(obj)) {
        return obj.map((item) => snakeToCamelDeep(item));
    }
    if (typeof obj !== "object") {
        return obj;
    }
    const result = {};
    for (const [key, value] of Object.entries(obj)) {
        // Keep the key (region ID), but convert the value's nested structure
        result[key] = snakeToCamelDeep(value);
    }
    return result;
}
/**
 * Recursively convert all snake_case keys in an object to camelCase.
 *
 * - Handles nested objects
 * - Handles arrays (converts each element)
 * - Preserves null/undefined/primitives
 * - Preserves region ID keys in regions/tooltips/value containers
 *
 * @param obj - Object with snake_case keys
 * @returns New object with camelCase keys
 */
export function snakeToCamelDeep(obj) {
    if (obj === null || obj === undefined) {
        return obj;
    }
    if (Array.isArray(obj)) {
        return obj.map((item) => snakeToCamelDeep(item));
    }
    if (typeof obj !== "object") {
        return obj;
    }
    const result = {};
    for (const [key, value] of Object.entries(obj)) {
        // Preserve keys starting with underscore (v0.3 payload special keys)
        const newKey = shouldPreserveKey(key) ? key : snakeToCamel(key);
        // For regions, tooltips, value, etc. - preserve region ID keys
        if (isRegionIdContainer(key)) {
            result[newKey] = convertValuesOnly(value);
        }
        else {
            result[newKey] = snakeToCamelDeep(value);
        }
    }
    return result;
}
