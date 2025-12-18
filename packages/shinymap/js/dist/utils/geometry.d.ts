import type { GeometryMap, RegionId } from "../types";
/**
 * Normalize a single path to string format.
 *
 * Accepts both formats:
 * - string: Returns as-is
 * - string[]: Joins with space
 *
 * @param path - Path in string or array format
 * @returns Normalized path string
 */
export declare function normalizePath(path: string | string[]): string;
/**
 * Normalize entire geometry map to flat string format.
 *
 * Converts all paths to strings by joining arrays with spaces.
 * This is the format expected by SVG <path d="..."> attributes.
 *
 * @param geometry - Geometry map with string or array paths
 * @returns Normalized geometry map with only string paths
 */
export declare function normalizeGeometry(geometry: GeometryMap): Record<RegionId, string>;
