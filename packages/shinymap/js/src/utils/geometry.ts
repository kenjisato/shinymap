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
export function normalizePath(path: string | string[]): string {
  return Array.isArray(path) ? path.join(" ") : path;
}

/**
 * Normalize entire geometry map to flat string format.
 *
 * Converts all paths to strings by joining arrays with spaces.
 * This is the format expected by SVG <path d="..."> attributes.
 *
 * @param geometry - Geometry map with string or array paths
 * @returns Normalized geometry map with only string paths
 */
export function normalizeGeometry(geometry: GeometryMap): Record<RegionId, string> {
  const result: Record<string, string> = {};
  for (const [regionId, path] of Object.entries(geometry)) {
    result[regionId] = normalizePath(path);
  }
  return result;
}
