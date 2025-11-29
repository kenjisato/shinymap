export type RegionId = string;
export type PrefectureGeometry = Record<RegionId, string>;

// Placeholder: actual prefecture paths will be populated later.
export const prefectureGeometry: PrefectureGeometry = {};

export function getPrefectureGeometry(): PrefectureGeometry {
  return { ...prefectureGeometry };
}
