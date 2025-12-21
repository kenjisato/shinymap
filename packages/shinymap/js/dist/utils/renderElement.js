import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
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
export function renderElement(props) {
    const { element, key, fill, fillOpacity, stroke, strokeWidth, cursor, pointerEvents, onClick, onMouseEnter, onMouseLeave, onFocus, onBlur, tooltip, extraProps, } = props;
    // Common props for all SVG elements
    const commonProps = {
        fill,
        fillOpacity,
        stroke,
        strokeWidth,
        style: cursor ? { cursor } : undefined,
        pointerEvents,
        onClick,
        onMouseEnter,
        onMouseLeave,
        onFocus,
        onBlur,
        ...extraProps,
    };
    // Title element for tooltip (works inside any SVG element)
    const titleElement = tooltip ? _jsx("title", { children: tooltip }) : null;
    // Render appropriate SVG element based on type
    switch (element.type) {
        case "circle":
            return (_jsx("circle", { cx: element.cx, cy: element.cy, r: element.r, ...commonProps, children: titleElement }, key));
        case "rect":
            return (_jsx("rect", { x: element.x, y: element.y, width: element.width, height: element.height, rx: element.rx, ry: element.ry, ...commonProps, children: titleElement }, key));
        case "path":
            return (_jsx("path", { d: element.d, ...commonProps, children: titleElement }, key));
        case "polygon":
            return (_jsx("polygon", { points: element.points, ...commonProps, children: titleElement }, key));
        case "ellipse":
            return (_jsx("ellipse", { cx: element.cx, cy: element.cy, rx: element.rx, ry: element.ry, ...commonProps, children: titleElement }, key));
        case "line":
            return (_jsx("line", { x1: element.x1, y1: element.y1, x2: element.x2, y2: element.y2, ...commonProps, children: titleElement }, key));
        case "text":
            return (_jsxs("text", { x: element.x, y: element.y, fontSize: element.fontSize, fontFamily: element.fontFamily, fontWeight: element.fontWeight, fontStyle: element.fontStyle, textAnchor: element.textAnchor, dominantBaseline: element.dominantBaseline, transform: element.transform, ...commonProps, children: [element.text, titleElement] }, key));
        default:
            // TypeScript ensures this is unreachable if all cases are handled
            const exhaustiveCheck = element;
            throw new Error(`Unknown element type: ${exhaustiveCheck.type}`);
    }
}
