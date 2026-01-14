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
export function resolveGroups(
  groupNames: string[] | undefined,
  regions: Record<RegionId, Element[]>,
  metadata?: OutlineMetadata
): Set<RegionId> {
  const result = new Set<RegionId>();
  if (!groupNames) return result;

  const groups = metadata?.groups ?? {};

  for (const name of groupNames) {
    if (groups[name]) {
      // Named group from metadata
      for (const id of groups[name]) {
        result.add(id);
      }
    } else if (regions[name]) {
      // Use as singleton group (region ID)
      result.add(name);
    }
    // Silently ignore unknown group names
  }

  return result;
}

/**
 * Layer assignment result.
 * Regions are assigned to exactly one layer based on priority.
 */
export type LayerAssignment = {
  underlay: Set<RegionId>;
  base: Set<RegionId>;
  overlay: Set<RegionId>;
  annotation: Set<RegionId>;
  hidden: Set<RegionId>;
};

/**
 * Assigns regions to layers based on group membership.
 *
 * Layer priority (highest to lowest):
 * 1. hidden - not rendered at all
 * 2. annotation - rendered above hover/selection (always on top)
 * 3. overlay - rendered above base but below selection/hover
 * 4. underlay - rendered below base
 * 5. base - default layer for all other regions
 *
 * A region appears in at most one layer.
 *
 * @param regions - The normalized regions map
 * @param underlay - Group names for underlay layer
 * @param overlay - Group names for overlay layer
 * @param annotation - Group names for annotation layer (renders above hover)
 * @param hidden - Group names to hide
 * @param metadata - Optional outline metadata
 * @returns Layer assignment for each region
 */
export function assignLayers(
  regions: Record<RegionId, Element[]>,
  underlay?: string[],
  overlay?: string[],
  annotation?: string[],
  hidden?: string[],
  metadata?: OutlineMetadata
): LayerAssignment {
  // Resolve group names to region IDs
  const underlayRegions = resolveGroups(underlay, regions, metadata);
  const overlayRegions = resolveGroups(overlay, regions, metadata);
  const annotationRegions = resolveGroups(annotation, regions, metadata);
  const hiddenRegions = resolveGroups(hidden, regions, metadata);

  const result: LayerAssignment = {
    underlay: new Set(),
    base: new Set(),
    overlay: new Set(),
    annotation: new Set(),
    hidden: new Set(),
  };

  // Assign each region to exactly one layer based on priority
  for (const id of Object.keys(regions)) {
    if (hiddenRegions.has(id)) {
      result.hidden.add(id);
    } else if (annotationRegions.has(id)) {
      result.annotation.add(id);
    } else if (overlayRegions.has(id)) {
      result.overlay.add(id);
    } else if (underlayRegions.has(id)) {
      result.underlay.add(id);
    } else {
      result.base.add(id);
    }
  }

  return result;
}

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
export function resolveGroupAesthetic(
  id: RegionId,
  aesGroup: Record<string, AestheticStyle> | undefined,
  metadata?: OutlineMetadata
): AestheticStyle | undefined {
  if (!aesGroup) return undefined;

  const groups = metadata?.groups ?? {};
  let result: AestheticStyle | undefined;

  // Find all groups this region belongs to
  for (const [groupName, aesthetic] of Object.entries(aesGroup)) {
    const groupMembers = groups[groupName];
    const isMember = groupMembers ? groupMembers.includes(id) : groupName === id; // Singleton group

    if (isMember) {
      if (!result) {
        result = { ...aesthetic };
      } else {
        // Merge: later groups override earlier ones
        result = { ...result, ...aesthetic };
      }
    }
  }

  return result;
}
