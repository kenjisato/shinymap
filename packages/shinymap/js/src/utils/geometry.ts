import type { Element, GeometryMap, PathElement, RegionId } from "../types";

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
export function normalizeRegion(value: string | string[] | Element | Element[]): Element[] {
  // v1.x: Already Element or Element[]
  if (typeof value === "object" && "type" in value) {
    return Array.isArray(value) ? value : [value];
  }

  // v0.x: string or string[] (treated as path elements)
  if (typeof value === "string") {
    return [{ type: "path", d: value } as PathElement];
  }

  if (Array.isArray(value)) {
    // Could be Element[] or string[]
    if (value.length === 0) return [];

    // Check first element to determine type
    const first = value[0];
    if (typeof first === "object" && "type" in first) {
      // Element[]
      return value as Element[];
    } else {
      // string[] - convert to PathElement[]
      return value.map((d) => ({ type: "path", d }) as PathElement);
    }
  }

  // Shouldn't reach here with proper types
  throw new Error(`Invalid region value: ${JSON.stringify(value)}`);
}

/**
 * Normalize entire geometry map to Element array format.
 *
 * Converts all region values to Element[] format, handling both v0.x
 * (string paths) and v1.x (polymorphic elements) formats.
 *
 * @param geometry - Geometry map in any supported format
 * @returns Normalized geometry map with Element[] values
 */
export function normalizeGeometry(geometry: GeometryMap): Record<RegionId, Element[]> {
  const result: Record<string, Element[]> = {};
  for (const [regionId, value] of Object.entries(geometry)) {
    result[regionId] = normalizeRegion(value);
  }
  return result;
}
