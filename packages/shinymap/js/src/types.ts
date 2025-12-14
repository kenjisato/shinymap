import type React from "react";

export type RegionId = string;

export type GeometryMap = Record<RegionId, string>;

export type TooltipMap = Record<RegionId, string>;

export type FillMap = string | Record<RegionId, string>;

export type InputMapMode = "single" | "multiple" | "count";

export type AestheticStyle = {
  fillColor?: string;
  fillOpacity?: number;
  strokeColor?: string;
  strokeWidth?: number;
};

export type ResolveAestheticArgs = {
  id: RegionId;
  mode: InputMapMode;
  isHovered: boolean;
  isSelected: boolean;
  count: number;
  baseAesthetic: AestheticStyle;
};

export type InputMapProps = {
  geometry: GeometryMap;
  tooltips?: TooltipMap;
  fillColor?: FillMap;  // Renamed from fills for consistency
  viewBox?: string;
  className?: string;
  containerStyle?: React.CSSProperties;
  defaultAesthetic?: AestheticStyle;
  resolveAesthetic?: (args: ResolveAestheticArgs) => AestheticStyle | undefined;
  regionProps?: (args: ResolveAestheticArgs) => React.SVGProps<SVGPathElement>;
  mode?: InputMapMode;
  value?: Record<RegionId, number>;
  onChange?: (value: Record<RegionId, number>) => void;
  /**
   * Counts advance modulo this value. `2` = toggle, omit or `Infinity` = increment.
   */
  cycle?: number;
  /**
   * Maximum number of regions allowed to be non-zero. Default is unlimited.
   */
  maxSelection?: number;
  /**
   * Non-interactive overlay geometry (dividers, borders, grids).
   */
  overlayGeometry?: GeometryMap;
  /**
   * Default aesthetic for overlay regions.
   */
  overlayAesthetic?: AestheticStyle;
  /**
   * Hover highlight aesthetic (rendered as overlay layer on top).
   */
  hoverHighlight?: AestheticStyle;
  /**
   * Aesthetic override for selected regions (isSelected=true).
   */
  selectedAesthetic?: AestheticStyle;
};

type BaseOutputProps = {
  geometry: GeometryMap;
  tooltips?: TooltipMap;
  viewBox?: string;
  className?: string;
  containerStyle?: React.CSSProperties;
  defaultAesthetic?: AestheticStyle;
  overlayGeometry?: GeometryMap;
  overlayAesthetic?: AestheticStyle;
};

export type ResolveOutputAestheticArgs = {
  id: RegionId;
  isActive: boolean;
  count: number;
  baseAesthetic: AestheticStyle;
  tooltip?: string;
};

export type OutputMapProps = BaseOutputProps & {
  fillColor?: string | Record<RegionId, string>;  // RENAMED from fills (singular, consistent)
  strokeWidth?: number | Record<RegionId, number>;  // NEW (per-region support)
  strokeColor?: string | Record<RegionId, string>;  // NEW (per-region support)
  fillOpacity?: number | Record<RegionId, number>;  // NEW (per-region support)
  counts?: Record<RegionId, number>;
  activeIds?: RegionId | RegionId[] | null;
  onRegionClick?: (id: RegionId) => void;
  resolveAesthetic?: (args: ResolveOutputAestheticArgs) => AestheticStyle | undefined;
  regionProps?: (args: ResolveOutputAestheticArgs) => React.SVGProps<SVGPathElement>;
  // Selection-specific aesthetics (RENAMED for consistency)
  fillColorSelected?: AestheticStyle;  // RENAMED from selectionAesthetic
  fillColorNotSelected?: AestheticStyle;  // RENAMED from notSelectionAesthetic
  countPalette?: string[];
  /**
   * Hover highlight aesthetic (rendered as overlay layer on top).
   */
  hoverHighlight?: AestheticStyle;
};
