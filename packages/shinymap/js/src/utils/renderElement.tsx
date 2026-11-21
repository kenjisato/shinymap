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
  /** Key down handler (keyboard navigation and activation) */
  onKeyDown?: React.KeyboardEventHandler<SVGElement>;
  /** Tab order position (0 = focusable, -1 = focusable only via script) */
  tabIndex?: number;
  /** ARIA role (e.g., "radio", "checkbox", "button") */
  role?: string;
  /** ARIA checked state (rendered as aria-checked) */
  ariaChecked?: boolean;
  /** Accessible name (rendered as aria-label) */
  ariaLabel?: string;
  /** Ref callback receiving the rendered SVG element (for programmatic focus) */
  elementRef?: (element: SVGElement | null) => void;
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
export function renderElement(props: RenderElementProps): React.ReactElement {
  const {
    element,
    key,
    fill,
    fillOpacity,
    stroke,
    strokeWidth,
    strokeDasharray,
    nonScalingStroke,
    cursor,
    pointerEvents,
    onClick,
    onMouseEnter,
    onMouseLeave,
    onFocus,
    onBlur,
    onKeyDown,
    tabIndex,
    role,
    ariaChecked,
    ariaLabel,
    elementRef,
    tooltip,
    extraProps,
  } = props;

  // Non-scaling stroke: default to true for predictable stroke widths
  // When true, stroke-width is in screen pixels regardless of viewBox scaling
  const vectorEffect = nonScalingStroke !== false ? "non-scaling-stroke" : undefined;

  // Focusable elements suppress the UA focus ring: shinymap draws its own
  // focus overlay, which is not obscured by neighboring regions' fills.
  const focusable = tabIndex !== undefined;
  const style =
    cursor || focusable
      ? { ...(cursor ? { cursor } : {}), ...(focusable ? { outline: "none" } : {}) }
      : undefined;

  // Common props for all SVG elements
  const commonProps = {
    fill,
    fillOpacity,
    stroke,
    strokeWidth,
    strokeDasharray,
    vectorEffect,
    style,
    pointerEvents,
    onClick,
    onMouseEnter,
    onMouseLeave,
    onFocus,
    onBlur,
    onKeyDown,
    tabIndex,
    role,
    "aria-checked": ariaChecked,
    "aria-label": ariaLabel,
    ref: elementRef,
    ...extraProps,
  };

  // Title element for tooltip (works inside any SVG element)
  const titleElement = tooltip ? <title>{tooltip}</title> : null;

  // Render appropriate SVG element based on type
  switch (element.type) {
    case "circle":
      return (
        <circle key={key} cx={element.cx} cy={element.cy} r={element.r} {...commonProps}>
          {titleElement}
        </circle>
      );

    case "rect":
      return (
        <rect
          key={key}
          x={element.x}
          y={element.y}
          width={element.width}
          height={element.height}
          rx={element.rx}
          ry={element.ry}
          {...commonProps}
        >
          {titleElement}
        </rect>
      );

    case "path":
      return (
        <path key={key} d={element.d} {...commonProps}>
          {titleElement}
        </path>
      );

    case "polygon":
      return (
        <polygon key={key} points={element.points} {...commonProps}>
          {titleElement}
        </polygon>
      );

    case "ellipse":
      return (
        <ellipse
          key={key}
          cx={element.cx}
          cy={element.cy}
          rx={element.rx}
          ry={element.ry}
          {...commonProps}
        >
          {titleElement}
        </ellipse>
      );

    case "line":
      return (
        <line
          key={key}
          x1={element.x1}
          y1={element.y1}
          x2={element.x2}
          y2={element.y2}
          {...commonProps}
        >
          {titleElement}
        </line>
      );

    case "text":
      return (
        <text
          key={key}
          x={element.x}
          y={element.y}
          fontSize={element.fontSize}
          fontFamily={element.fontFamily}
          fontWeight={element.fontWeight}
          fontStyle={element.fontStyle}
          textAnchor={element.textAnchor}
          dominantBaseline={element.dominantBaseline}
          transform={element.transform}
          {...commonProps}
        >
          {element.text}
          {titleElement}
        </text>
      );

    default:
      // TypeScript ensures this is unreachable if all cases are handled
      const exhaustiveCheck: never = element;
      throw new Error(`Unknown element type: ${(exhaustiveCheck as Element).type}`);
  }
}
