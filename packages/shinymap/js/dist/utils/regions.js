/**
 * Normalize a single region value to Element array format.
 *
 * Handles both v0.x (string paths) and v1.x (polymorphic elements):
 * - string → PathElement
 * - string[] → PathElement[]
 * - Element → [Element]
 * - Element[] → Element[]
 *
 * @param value - Region value in any supported format
 * @returns Array of Element objects
 */
export function normalizeRegion(value) {
    // v1.x: Already Element or Element[]
    if (typeof value === "object" && "type" in value) {
        return Array.isArray(value) ? value : [value];
    }
    // v0.x: string or string[] (treated as path elements)
    if (typeof value === "string") {
        return [{ type: "path", d: value }];
    }
    if (Array.isArray(value)) {
        // Could be Element[] or string[]
        if (value.length === 0)
            return [];
        // Check first element to determine type
        const first = value[0];
        if (typeof first === "object" && "type" in first) {
            // Element[]
            return value;
        }
        else {
            // string[] - convert to PathElement[]
            return value.map((d) => ({ type: "path", d }));
        }
    }
    // Shouldn't reach here with proper types
    throw new Error(`Invalid region value: ${JSON.stringify(value)}`);
}
/**
 * Normalize entire regions map to Element array format.
 *
 * Converts all region values to Element[] format, handling both v0.x
 * (string paths) and v1.x (polymorphic elements) formats.
 *
 * @param regions - Regions map in any supported format
 * @returns Normalized regions map with Element[] values
 */
export function normalizeRegions(regions) {
    const result = {};
    for (const [regionId, value] of Object.entries(regions)) {
        result[regionId] = normalizeRegion(value);
    }
    return result;
}
