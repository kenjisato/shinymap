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
 * snakeToCamel("geometry_metadata") // "geometryMetadata"
 */
export declare function snakeToCamel(str: string): string;
/**
 * Recursively convert all snake_case keys in an object to camelCase.
 *
 * - Handles nested objects
 * - Handles arrays (converts each element)
 * - Preserves null/undefined/primitives
 * - Preserves region ID keys in geometry/tooltips/value containers
 *
 * @param obj - Object with snake_case keys
 * @returns New object with camelCase keys
 */
export declare function snakeToCamelDeep<T>(obj: T): T;
