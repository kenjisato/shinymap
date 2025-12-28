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
export type Element = CircleElement | RectElement | PathElement | PolygonElement | EllipseElement | LineElement | TextElement;
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
export type AesIndexedConfig = {
    type: "indexed";
    value: IndexedAestheticData;
} | {
    type: "byGroup";
    groups: Record<string, IndexedAestheticData>;
};
/**
 * Resolve an IndexedAestheticData to an AestheticStyle for a given count/state.
 *
 * @param data The indexed aesthetic data
 * @param count The current count/state value
 * @param cycle If provided, use modulo wrapping (count % cycle), otherwise clamp
 */
export declare function resolveIndexedAesthetic(data: IndexedAestheticData, count: number, cycle?: number): AestheticStyle;
/**
 * Get the IndexedAestheticData for a region from an AesIndexedConfig.
 * Returns undefined if no indexed aesthetic applies to this region.
 */
export declare function getIndexedDataForRegion(config: AesIndexedConfig | undefined, regionId: RegionId, geometryMetadata?: GeometryMetadata): IndexedAestheticData | undefined;
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
export declare function isRelativeExpr(value: unknown): value is RelativeExpr;
/**
 * Resolve a RelativeExpr against a parent value.
 */
export declare function resolveRelativeExpr(expr: RelativeExpr, parentValue: number): number;
/**
 * Resolve a value that may be a RelativeExpr or a concrete value.
 */
export declare function resolveValue(value: number | RelativeExpr | undefined, parentValue: number | undefined, fallback: number): number;
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
export declare const DEFAULT_AESTHETIC_VALUES: Required<ResolvedAesthetic>;
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
export declare const LIBRARY_AESTHETIC_DEFAULTS: {
    base: AestheticStyle;
    select: AestheticStyle;
    hover: AestheticStyle;
    line: AestheticStyle;
    text: AestheticStyle;
};
/**
 * Default hover aesthetic - applied when aesHover is not provided.
 *
 * Uses RelativeExpr to add to parent stroke width, creating a subtle
 * but visible hover effect that works with any stroke width.
 *
 * To disable hover entirely, pass aesHover={null} explicitly.
 */
export declare const DEFAULT_HOVER_AESTHETIC: AestheticStyle;
/**
 * Create a RenderedRegion by resolving an AestheticStyle against a parent.
 */
export declare function createRenderedRegion(id: RegionId, aes: AestheticStyle, parent?: RenderedRegion): RenderedRegion;
/**
 * Geometry metadata with optional group definitions.
 * Groups allow regions to be assigned to layers (underlay/overlay) and aesthetic groups.
 */
export type GeometryMetadata = {
    viewBox?: string;
    groups?: Record<string, RegionId[]>;
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
