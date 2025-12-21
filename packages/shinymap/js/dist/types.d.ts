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
    fillColor?: FillMap;
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
    fillColor?: string | Record<RegionId, string>;
    strokeWidth?: number | Record<RegionId, number>;
    strokeColor?: string | Record<RegionId, string>;
    fillOpacity?: number | Record<RegionId, number>;
    counts?: Record<RegionId, number>;
    activeIds?: RegionId | RegionId[] | null;
    onRegionClick?: (id: RegionId) => void;
    resolveAesthetic?: (args: ResolveOutputAestheticArgs) => AestheticStyle | undefined;
    regionProps?: (args: ResolveOutputAestheticArgs) => React.SVGProps<SVGPathElement>;
    fillColorSelected?: AestheticStyle;
    fillColorNotSelected?: AestheticStyle;
    countPalette?: string[];
    /**
     * Hover highlight aesthetic (rendered as overlay layer on top).
     */
    hoverHighlight?: AestheticStyle;
};
export {};
