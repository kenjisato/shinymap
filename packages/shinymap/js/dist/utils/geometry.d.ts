import type { Element, GeometryMap, RegionId } from "../types";
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
export declare function normalizeRegion(value: string | string[] | Element | Element[]): Element[];
/**
 * Normalize entire geometry map to Element array format.
 *
 * Converts all region values to Element[] format, handling both v0.x
 * (string paths) and v1.x (polymorphic elements) formats.
 *
 * @param geometry - Geometry map in any supported format
 * @returns Normalized geometry map with Element[] values
 */
export declare function normalizeGeometry(geometry: GeometryMap): Record<RegionId, Element[]>;
