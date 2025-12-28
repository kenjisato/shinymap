import type React from "react";

export type RegionId = string;

/**
 * SVG Element types supported by shinymap.
 *
 * These match the polymorphic elements from the Python backend.
 * Each element type has a `type` field for discriminated unions.
 *
 * Note on aesthetics: These element types preserve SVG aesthetic attributes
 * (fill, stroke, etc.) from the original SVG for export purposes, but shinymap
 * does NOT use these for rendering. Interactive aesthetics are controlled via
 * component props (defaultAesthetic, fillColor, etc.).
 */

export type CircleElement = {
  type: "circle";
  cx: number;
  cy: number;
  r: number;
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
  class?: string;
};

export type RectElement = {
  type: "rect";
  x: number;
  y: number;
  width: number;
  height: number;
  rx?: number;
  ry?: number;
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
  class?: string;
};

export type PathElement = {
  type: "path";
  d: string;
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
  class?: string;
};

export type PolygonElement = {
  type: "polygon";
  points: string;
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
  class?: string;
};

export type EllipseElement = {
  type: "ellipse";
  cx: number;
  cy: number;
  rx: number;
  ry: number;
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
  class?: string;
};

export type LineElement = {
  type: "line";
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  stroke?: string;
  strokeWidth?: number;
  class?: string;
};

export type TextElement = {
  type: "text";
  x: number;
  y: number;
  text: string;
  fontSize?: number;
  fontFamily?: string;
  fontWeight?: string;
  fontStyle?: string;
  textAnchor?: string;
  dominantBaseline?: string;
  transform?: string;
  fill?: string;
  class?: string;
};

/**
 * Discriminated union of all supported SVG element types.
 *
 * The `type` field allows TypeScript to narrow the type in switch statements.
 */
export type Element =
  | CircleElement
  | RectElement
  | PathElement
  | PolygonElement
  | EllipseElement
  | LineElement
  | TextElement;

/**
 * Geometry map supports both v0.x (string paths) and v1.x (polymorphic elements):
 * - v0.x: string | string[] (treated as path elements)
 * - v1.x: Element | Element[] (any SVG element type)
 *
 * Examples:
 *   v0.x: { "region1": "M 0 0 L 10 10" }
 *   v0.x: { "region1": ["M 0 0 L 10 10", "M 20 20 L 30 30"] }
 *   v1.x: { "region1": { type: "circle", cx: 50, cy: 50, r: 30 } }
 *   v1.x: { "region1": [{ type: "circle", ... }, { type: "rect", ... }] }
 */
export type GeometryMap = Record<RegionId, string | string[] | Element | Element[]>;

export type TooltipMap = Record<RegionId, string>;

export type FillMap = string | Record<RegionId, string>;

export type MapModeType = "single" | "multiple" | "count" | "cycle" | "display";

/**
 * Indexed aesthetic value - can be single value or array indexed by state.
 */
export type IndexedValue<T> = T | T[];

/**
 * Indexed aesthetic configuration for multi-state modes (Cycle, Count).
 *
 * Each property can be a single value (applied to all states) or an array
 * indexed by state:
 * - For Cycle mode: index = count % n (wrapping)
 * - For Count mode: index = min(count, len(array) - 1) (clamping)
 */
export type IndexedAestheticData = {
  fillColor?: IndexedValue<string>;
  fillOpacity?: IndexedValue<number>;
  strokeColor?: IndexedValue<string>;
  strokeWidth?: IndexedValue<number>;
  strokeDasharray?: IndexedValue<string>;
};

/**
 * Serialized aesIndexed from Python mode.to_dict().
 */
export type AesIndexedConfig =
  | { type: "indexed"; value: IndexedAestheticData }
  | { type: "byGroup"; groups: Record<string, IndexedAestheticData> };

/**
 * Get a value from an indexed array at the given index.
 * If the value is not an array, returns it as-is.
 * For arrays, uses modulo for wrapping (Cycle mode) or clamping (Count mode).
 */
function getIndexedValue<T>(
  value: IndexedValue<T> | undefined,
  index: number,
  wrap: boolean
): T | undefined {
  if (value === undefined) return undefined;
  if (!Array.isArray(value)) return value;
  if (value.length === 0) return undefined;
  const effectiveIndex = wrap ? index % value.length : Math.min(index, value.length - 1);
  return value[effectiveIndex];
}

/**
 * Resolve an IndexedAestheticData to an AestheticStyle for a given count/state.
 *
 * @param data The indexed aesthetic data
 * @param count The current count/state value
 * @param cycle If provided, use modulo wrapping (count % cycle), otherwise clamp
 */
export function resolveIndexedAesthetic(
  data: IndexedAestheticData,
  count: number,
  cycle?: number
): AestheticStyle {
  const wrap = cycle !== undefined;
  const index = wrap && cycle > 0 ? count % cycle : count;

  return {
    fillColor: getIndexedValue(data.fillColor, index, wrap),
    fillOpacity: getIndexedValue(data.fillOpacity, index, wrap),
    strokeColor: getIndexedValue(data.strokeColor, index, wrap),
    strokeWidth: getIndexedValue(data.strokeWidth, index, wrap),
    strokeDasharray: getIndexedValue(data.strokeDasharray, index, wrap),
  };
}

/**
 * Get the IndexedAestheticData for a region from an AesIndexedConfig.
 * Returns undefined if no indexed aesthetic applies to this region.
 */
export function getIndexedDataForRegion(
  config: AesIndexedConfig | undefined,
  regionId: RegionId,
  geometryMetadata?: GeometryMetadata
): IndexedAestheticData | undefined {
  if (!config) return undefined;

  if (config.type === "indexed") {
    return config.value;
  }

  // type === "byGroup"
  // First check if region ID matches directly
  if (config.groups[regionId]) {
    return config.groups[regionId];
  }

  // Check if region belongs to a group that has indexed aesthetic
  if (geometryMetadata?.groups) {
    for (const [groupName, regionIds] of Object.entries(geometryMetadata.groups)) {
      if (regionIds.includes(regionId) && config.groups[groupName]) {
        return config.groups[groupName];
      }
    }
  }

  return undefined;
}

/**
 * Mode configuration object (nested API).
 *
 * Python normalizes string mode to this full config before sending to JS.
 */
export type ModeConfig = {
  type: MapModeType;
  /** Allow deselection in single mode */
  allowDeselect?: boolean;
  /** Maximum number of regions that can be selected (multiple mode) */
  maxSelection?: number;
  /** Number of states for cycle mode. Counts advance modulo n. */
  n?: number;
  /** Indexed aesthetic for multi-state visual feedback (Cycle, Count modes) */
  aesIndexed?: AesIndexedConfig;
};

/**
 * Relative expression for parent-relative aesthetic values.
 *
 * Allows expressing values like "parent stroke width + 2" that get resolved
 * at render time against the actual parent aesthetic values.
 *
 * Created by Python's PARENT proxy: `PARENT.stroke_width + 2`
 */
export type RelativeExpr = {
  __relative__: true;
  property: string;
  operator: "+" | "-" | "*" | "/";
  operand: number;
};

/**
 * Check if a value is a RelativeExpr object.
 */
export function isRelativeExpr(value: unknown): value is RelativeExpr {
  return (
    typeof value === "object" &&
    value !== null &&
    "__relative__" in value &&
    (value as RelativeExpr).__relative__ === true
  );
}

/**
 * Resolve a RelativeExpr against a parent value.
 */
export function resolveRelativeExpr(expr: RelativeExpr, parentValue: number): number {
  switch (expr.operator) {
    case "+":
      return parentValue + expr.operand;
    case "-":
      return parentValue - expr.operand;
    case "*":
      return parentValue * expr.operand;
    case "/":
      return expr.operand !== 0 ? parentValue / expr.operand : parentValue;
    default:
      return parentValue;
  }
}

/**
 * Resolve a value that may be a RelativeExpr or a concrete value.
 */
export function resolveValue(
  value: number | RelativeExpr | undefined,
  parentValue: number | undefined,
  fallback: number
): number {
  if (value === undefined) {
    return fallback;
  }
  if (isRelativeExpr(value)) {
    return resolveRelativeExpr(value, parentValue ?? fallback);
  }
  return value;
}

export type AestheticStyle = {
  /** Fill color. Use null or "none" to disable fill. */
  fillColor?: string | null;
  fillOpacity?: number | RelativeExpr;
  /** Stroke color. Use null or "none" to disable stroke. */
  strokeColor?: string | null;
  strokeWidth?: number | RelativeExpr;
  strokeDasharray?: string;
  nonScalingStroke?: boolean;
};

/**
 * Aesthetic with all values resolved to concrete types (no RelativeExpr).
 */
export type ResolvedAesthetic = {
  fillColor?: string;
  fillOpacity?: number;
  strokeColor?: string;
  strokeWidth?: number;
  strokeDasharray?: string;
  nonScalingStroke?: boolean;
};

/**
 * A rendered region with resolved aesthetics and parent reference.
 *
 * This forms a linked-list structure where each layer's rendered element
 * can access its parent's aesthetic values for resolving RelativeExpr.
 *
 * Hierarchy (child → parent):
 *   Hover → Select (if selected) or Base
 *   Select → Base
 *   Base → Default
 */
export type RenderedRegion = {
  id: RegionId;
  aesthetic: ResolvedAesthetic;
  parent?: RenderedRegion;
};

/**
 * Reserved aesthetic values used as the root of the chain.
 *
 * These are intentionally subtle/neutral - they serve as fallback values
 * when no aesthetics are explicitly provided. For Python Shiny apps,
 * the library defaults are provided via wash() in Python.
 *
 * React developers should use LIBRARY_AESTHETIC_DEFAULTS for a complete
 * out-of-box experience, or define their own aesthetics.
 */
export const DEFAULT_AESTHETIC_VALUES: Required<ResolvedAesthetic> = {
  fillColor: "#f1f5f9", // slate-100: subtle, reserved default
  fillOpacity: 1,
  strokeColor: "#94a3b8", // slate-400: subtle border
  strokeWidth: 0.5,
  strokeDasharray: "",
  nonScalingStroke: false,
};

/**
 * Library defaults for React developers.
 *
 * Use these for a polished out-of-box experience. Equivalent to Python's
 * library-supplied input_map/output_map defaults.
 *
 * Usage:
 *   <InputMap
 *     aesBase={LIBRARY_AESTHETIC_DEFAULTS.base}
 *     aesSelect={LIBRARY_AESTHETIC_DEFAULTS.select}
 *     aesHover={LIBRARY_AESTHETIC_DEFAULTS.hover}
 *     ...
 *   />
 */
export const LIBRARY_AESTHETIC_DEFAULTS = {
  base: {
    fillColor: "#e2e8f0", // slate-200: neutral base
    strokeColor: "#94a3b8", // slate-400: subtle border
    strokeWidth: 0.5,
  } as AestheticStyle,
  select: {
    fillColor: "#bfdbfe", // blue-200: selected highlight
    strokeColor: "#1e40af", // blue-800: strong border
    strokeWidth: 1,
  } as AestheticStyle,
  hover: {
    strokeColor: "#475569", // slate-600: darker border on hover
    strokeWidth: {
      __relative__: true,
      property: "strokeWidth",
      operator: "+",
      operand: 0.5,
    },
  } as AestheticStyle,
  line: {
    fillColor: "none",
    strokeColor: "#94a3b8", // slate-400
    strokeWidth: 0.5,
  } as AestheticStyle,
  text: {
    fillColor: "#1e293b", // slate-800
  } as AestheticStyle,
};

/**
 * Default hover aesthetic - applied when aesHover is not provided.
 *
 * Uses RelativeExpr to add to parent stroke width, creating a subtle
 * but visible hover effect that works with any stroke width.
 *
 * To disable hover entirely, pass aesHover={null} explicitly.
 */
export const DEFAULT_HOVER_AESTHETIC: AestheticStyle = {
  strokeWidth: {
    __relative__: true,
    property: "strokeWidth",
    operator: "+",
    operand: 1,
  },
};

/**
 * Resolve a numeric property value, walking up the parent chain if needed.
 */
function resolveNumericProperty(
  value: number | RelativeExpr | undefined,
  parent: RenderedRegion | undefined,
  key: "fillOpacity" | "strokeWidth",
  fallback: number
): number {
  if (value === undefined) {
    return parent?.aesthetic[key] ?? fallback;
  }
  if (isRelativeExpr(value)) {
    const parentValue = parent?.aesthetic[key] ?? fallback;
    return resolveRelativeExpr(value, parentValue);
  }
  return value;
}

/**
 * Resolve a string property value, inheriting from parent if undefined.
 *
 * Special handling for null: converts to "none" for SVG fill/stroke attributes.
 * This allows Python to send fill_color=None to disable fill.
 */
function resolveStringProperty(
  value: string | null | undefined,
  parent: RenderedRegion | undefined,
  key: "fillColor" | "strokeColor" | "strokeDasharray",
  fallback: string
): string {
  // null means "none" in SVG (disables fill/stroke)
  if (value === null) {
    return "none";
  }
  if (value === undefined) {
    return parent?.aesthetic[key] ?? fallback;
  }
  return value;
}

/**
 * Create a RenderedRegion by resolving an AestheticStyle against a parent.
 */
export function createRenderedRegion(
  id: RegionId,
  aes: AestheticStyle,
  parent?: RenderedRegion
): RenderedRegion {
  const resolved: ResolvedAesthetic = {
    fillColor: resolveStringProperty(
      aes.fillColor,
      parent,
      "fillColor",
      DEFAULT_AESTHETIC_VALUES.fillColor
    ),
    fillOpacity: resolveNumericProperty(
      aes.fillOpacity,
      parent,
      "fillOpacity",
      DEFAULT_AESTHETIC_VALUES.fillOpacity
    ),
    strokeColor: resolveStringProperty(
      aes.strokeColor,
      parent,
      "strokeColor",
      DEFAULT_AESTHETIC_VALUES.strokeColor
    ),
    strokeWidth: resolveNumericProperty(
      aes.strokeWidth,
      parent,
      "strokeWidth",
      DEFAULT_AESTHETIC_VALUES.strokeWidth
    ),
    strokeDasharray: resolveStringProperty(
      aes.strokeDasharray,
      parent,
      "strokeDasharray",
      DEFAULT_AESTHETIC_VALUES.strokeDasharray
    ),
    nonScalingStroke:
      aes.nonScalingStroke ??
      parent?.aesthetic.nonScalingStroke ??
      DEFAULT_AESTHETIC_VALUES.nonScalingStroke,
  };

  return { id, aesthetic: resolved, parent };
}

/**
 * Geometry metadata with optional group definitions.
 * Groups allow regions to be assigned to layers (underlay/overlay) and aesthetic groups.
 */
export type GeometryMetadata = {
  viewBox?: string;
  groups?: Record<string, RegionId[]>; // Group name → region IDs
};

/**
 * Nested aesthetic configuration (new API).
 *
 * Groups all aesthetic settings under a single `aes` prop.
 */
export type AesConfig = {
  /** Base aesthetic for all regions (not selected, not hovered). */
  base?: AestheticStyle;
  /** Aesthetic override for hovered regions. null disables hover effect. */
  hover?: AestheticStyle | null;
  /** Aesthetic override for selected regions. */
  select?: AestheticStyle;
  /** Aesthetic for non-selected regions when activeIds is set. */
  notSelect?: AestheticStyle;
  /** Per-group aesthetic overrides. Group name → aesthetic style. */
  group?: Record<string, AestheticStyle>;
};

/**
 * Nested layer configuration (new API).
 *
 * Groups all layer settings under a single `layers` prop.
 */
export type LayersConfig = {
  /** Group names to render in underlay layer (below base regions). */
  underlays?: string[];
  /** Group names to render in overlay layer (above base regions). */
  overlays?: string[];
  /** Group names to hide completely (not rendered). */
  hidden?: string[];
};

export type ResolveAestheticArgs = {
  id: RegionId;
  mode: MapModeType;
  isHovered: boolean;
  isSelected: boolean;
  count: number;
  baseAesthetic: AestheticStyle;
};

export type InputMapProps = {
  geometry: GeometryMap;
  tooltips?: TooltipMap;
  fillColor?: FillMap;
  viewBox?: string;
  className?: string;
  containerStyle?: React.CSSProperties;
  /**
   * Mode configuration (normalized by Python to full ModeConfig).
   */
  mode?: ModeConfig;
  /**
   * Nested aesthetic configuration.
   */
  aes?: AesConfig;
  /**
   * Nested layer configuration.
   */
  layers?: LayersConfig;
  /**
   * Geometry metadata containing group definitions.
   */
  geometryMetadata?: GeometryMetadata;
  value?: Record<RegionId, number>;
  onChange?: (value: Record<RegionId, number>) => void;
  resolveAesthetic?: (args: ResolveAestheticArgs) => AestheticStyle | undefined;
  regionProps?: (args: ResolveAestheticArgs) => React.SVGProps<SVGPathElement>;
  /**
   * Non-interactive overlay geometry (dividers, borders, grids).
   * @deprecated Use layers.overlays + aes.group instead
   */
  overlayGeometry?: GeometryMap;
  /**
   * Default aesthetic for overlay regions.
   * @deprecated Use aes.group instead
   */
  overlayAesthetic?: AestheticStyle;
};

export type ResolveOutputAestheticArgs = {
  id: RegionId;
  isActive: boolean;
  count: number;
  baseAesthetic: AestheticStyle;
  tooltip?: string;
};

export type OutputMapProps = {
  geometry: GeometryMap;
  tooltips?: TooltipMap;
  viewBox?: string;
  className?: string;
  containerStyle?: React.CSSProperties;
  /**
   * Nested aesthetic configuration.
   */
  aes?: AesConfig;
  /**
   * Nested layer configuration.
   */
  layers?: LayersConfig;
  /**
   * Geometry metadata containing group definitions.
   */
  geometryMetadata?: GeometryMetadata;
  fillColor?: string | Record<RegionId, string>;
  strokeWidth?: number | Record<RegionId, number>;
  strokeColor?: string | Record<RegionId, string>;
  fillOpacity?: number | Record<RegionId, number>;
  value?: Record<RegionId, number>;
  activeIds?: RegionId | RegionId[] | null;
  onRegionClick?: (id: RegionId) => void;
  resolveAesthetic?: (args: ResolveOutputAestheticArgs) => AestheticStyle | undefined;
  regionProps?: (args: ResolveOutputAestheticArgs) => React.SVGProps<SVGPathElement>;
  /** @deprecated Use layers.overlays + aes.group instead */
  overlayGeometry?: GeometryMap;
  /** @deprecated Use aes.group instead */
  overlayAesthetic?: AestheticStyle;
};
