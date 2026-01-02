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
export function resolveGroups(groupNames, regions, metadata) {
    var _a;
    const result = new Set();
    if (!groupNames)
        return result;
    const groups = (_a = metadata === null || metadata === void 0 ? void 0 : metadata.groups) !== null && _a !== void 0 ? _a : {};
    for (const name of groupNames) {
        if (groups[name]) {
            // Named group from metadata
            for (const id of groups[name]) {
                result.add(id);
            }
        }
        else if (regions[name]) {
            // Use as singleton group (region ID)
            result.add(name);
        }
        // Silently ignore unknown group names
    }
    return result;
}
/**
 * Assigns regions to layers based on group membership.
 *
 * Layer priority (highest to lowest):
 * 1. hidden - not rendered at all
 * 2. overlays - rendered above base
 * 3. underlays - rendered below base
 * 4. base - default layer for all other regions
 *
 * A region appears in at most one layer.
 *
 * @param regions - The normalized regions map
 * @param underlays - Group names for underlay layer
 * @param overlays - Group names for overlay layer
 * @param hidden - Group names to hide
 * @param metadata - Optional outline metadata
 * @returns Layer assignment for each region
 */
export function assignLayers(regions, underlays, overlays, hidden, metadata) {
    // Resolve group names to region IDs
    const underlayRegions = resolveGroups(underlays, regions, metadata);
    const overlayRegions = resolveGroups(overlays, regions, metadata);
    const hiddenRegions = resolveGroups(hidden, regions, metadata);
    const result = {
        underlay: new Set(),
        base: new Set(),
        overlay: new Set(),
        hidden: new Set(),
    };
    // Assign each region to exactly one layer based on priority
    for (const id of Object.keys(regions)) {
        if (hiddenRegions.has(id)) {
            result.hidden.add(id);
        }
        else if (overlayRegions.has(id)) {
            result.overlay.add(id);
        }
        else if (underlayRegions.has(id)) {
            result.underlay.add(id);
        }
        else {
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
export function resolveGroupAesthetic(id, aesGroup, metadata) {
    var _a;
    if (!aesGroup)
        return undefined;
    const groups = (_a = metadata === null || metadata === void 0 ? void 0 : metadata.groups) !== null && _a !== void 0 ? _a : {};
    let result;
    // Find all groups this region belongs to
    for (const [groupName, aesthetic] of Object.entries(aesGroup)) {
        const groupMembers = groups[groupName];
        const isMember = groupMembers ? groupMembers.includes(id) : groupName === id; // Singleton group
        if (isMember) {
            if (!result) {
                result = { ...aesthetic };
            }
            else {
                // Merge: later groups override earlier ones
                result = { ...result, ...aesthetic };
            }
        }
    }
    return result;
}
