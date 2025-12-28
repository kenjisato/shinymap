import React from "react";
import type { Element } from "../types";
/**
 * Props for rendering an SVG element with shinymap aesthetics.
 *
 * These props control the visual appearance and interactivity,
 * overriding any aesthetic properties stored in the element itself.
 */
export type RenderElementProps = {
    /** The element to render */
    element: Element;
    /** Unique key for React reconciliation */
    key: string;
    /** Fill color (overrides element.fill) */
    fill?: string;
    /** Fill opacity (0-1) */
    fillOpacity?: number;
    /** Stroke color (overrides element.stroke) */
    stroke?: string;
    /** Stroke width (overrides element.strokeWidth) */
    strokeWidth?: number;
    /** Stroke dash pattern (e.g., "5,5" for dashed lines) */
    strokeDasharray?: string;
    /** Non-scaling stroke (true = stroke width in screen pixels, default true) */
    nonScalingStroke?: boolean;
    /** CSS cursor style */
    cursor?: string;
    /** Pointer events (e.g., "none" for overlays) */
    pointerEvents?: string;
    /** Click handler */
    onClick?: () => void;
    /** Mouse enter handler */
    onMouseEnter?: () => void;
    /** Mouse leave handler */
    onMouseLeave?: () => void;
    /** Focus handler */
    onFocus?: () => void;
    /** Blur handler */
    onBlur?: () => void;
    /** Tooltip content (rendered as <title> inside SVG element) */
    tooltip?: string;
    /** Additional SVG props (spread onto element) */
    extraProps?: Record<string, unknown>;
};
/**
 * Render an SVG element based on its type.
 *
 * Supports polymorphic SVG element types (circle, rect, path, polygon, ellipse,
 * line, text), rendering the appropriate SVG tag with the provided aesthetic
 * overrides.
 *
 * Note: Elements may contain aesthetic properties (fill, stroke, etc.) preserved
 * from source SVG files, but these are IGNORED during rendering. Visual appearance
 * is controlled entirely by the props (fill, fillOpacity, stroke, strokeWidth).
 *
 * @param props - Element and rendering properties
 * @returns React SVG element
 */
export declare function renderElement(props: RenderElementProps): React.ReactElement;
