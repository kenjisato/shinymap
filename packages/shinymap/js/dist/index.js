import { jsx as _jsx } from "react/jsx-runtime";
import { createRoot as reactCreateRoot } from "react-dom/client";
import { InputMap } from "./components/InputMap";
import { OutputMap } from "./components/OutputMap";
export { InputMap } from "./components/InputMap";
export { OutputMap } from "./components/OutputMap";
export { palette, neutrals, qualitative, sequential } from "./palette";
function createRoot(target) {
    return reactCreateRoot(target);
}
function getRoot(target) {
    const existing = target.__shinymapRoot;
    if (existing) {
        return existing;
    }
    const created = createRoot(target);
    target.__shinymapRoot = created;
    return created;
}
/**
 * Imperatively render an InputMap into a target element. Useful for non-React hosts (e.g., Shiny).
 */
export function renderInputMap(target, props, onChange) {
    const root = getRoot(target);
    const componentProps = { ...props, onChange: onChange !== null && onChange !== void 0 ? onChange : props.onChange };
    const Component = InputMap;
    root.render(_jsx(Component, { ...componentProps }));
    return root;
}
/**
 * Imperatively render an OutputMap into a target element. Useful for non-React hosts (e.g., Shiny).
 */
export function renderOutputMap(target, props) {
    const root = getRoot(target);
    const Component = OutputMap;
    root.render(_jsx(Component, { ...props }));
    return root;
}
