import type { AestheticStyle, Element, OutlineMetadata, RegionId } from "../types";
/**
 * Resolves group names to region IDs using outline metadata.
 *
 * Groups can be:
 * 1. Named groups defined in outlineMetadata.groups (e.g., "grid" -> ["grid_lat", "grid_lon"])
 * 2. Individual region IDs used as singleton groups (e.g., "tokyo" -> ["tokyo"])
 *
 * @param groupNames - Array of group names to resolve
 * @param regions - The regions map (for fallback to region IDs)
 * @param metadata - Optional outline metadata containing group definitions
 * @returns Set of region IDs
 */
export declare function resolveGroups(groupNames: string[] | undefined, regions: Record<RegionId, Element[]>, metadata?: OutlineMetadata): Set<RegionId>;
/**
 * Layer assignment result.
 * Regions are assigned to exactly one layer based on priority.
 */
export type LayerAssignment = {
    underlay: Set<RegionId>;
    base: Set<RegionId>;
    overlay: Set<RegionId>;
    hidden: Set<RegionId>;
};
/**
 * Assigns regions to layers based on group membership.
 *
 * Layer priority (highest to lowest):
 * 1. hidden - not rendered at all
 * 2. overlay - rendered above base
 * 3. underlay - rendered below base
 * 4. base - default layer for all other regions
 *
 * A region appears in at most one layer.
 *
 * @param regions - The normalized regions map
 * @param underlay - Group names for underlay layer
 * @param overlay - Group names for overlay layer
 * @param hidden - Group names to hide
 * @param metadata - Optional outline metadata
 * @returns Layer assignment for each region
 */
export declare function assignLayers(regions: Record<RegionId, Element[]>, underlay?: string[], overlay?: string[], hidden?: string[], metadata?: OutlineMetadata): LayerAssignment;
/**
 * Resolves aesthetic for a region based on group membership.
 *
 * Aesthetics are merged in group order, with later groups overriding earlier ones.
 * Only explicitly set properties override (MISSING values don't override).
 *
 * @param id - Region ID
 * @param aesGroup - Per-group aesthetic overrides
 * @param metadata - Optional outline metadata
 * @returns Merged aesthetic style for the region
 */
export declare function resolveGroupAesthetic(id: RegionId, aesGroup: Record<string, AestheticStyle> | undefined, metadata?: OutlineMetadata): AestheticStyle | undefined;
