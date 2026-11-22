import type { Element, RegionId, RegionsMap } from "../types";
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
 * Normalize entire regions map to Element array format.
 *
 * Converts all region values to Element[] format, handling both v0.x
 * (string paths) and v1.x (polymorphic elements) formats.
 *
 * @param regions - Regions map in any supported format
 * @returns Normalized regions map with Element[] values
 */
export declare function normalizeRegions(regions: RegionsMap): Record<RegionId, Element[]>;
