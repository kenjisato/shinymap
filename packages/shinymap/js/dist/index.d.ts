import type { InputMapProps, OutputMapProps } from "./types";
export type { GeometryMap, InputMapProps, OutputMapProps, RegionId, TooltipMap } from "./types";
export { InputMap } from "./components/InputMap";
export { OutputMap } from "./components/OutputMap";
export { palette, neutrals, qualitative, sequential } from "./palette";
type CreateRootFn = typeof import("react-dom/client").createRoot;
type Root = ReturnType<CreateRootFn>;
/**
 * Imperatively render an InputMap into a target element. Useful for non-React hosts (e.g., Shiny).
 */
export declare function renderInputMap(target: HTMLElement, props: InputMapProps, onChange?: InputMapProps["onChange"]): Root;
/**
 * Imperatively render an OutputMap into a target element. Useful for non-React hosts (e.g., Shiny).
 */
export declare function renderOutputMap(target: HTMLElement, props: OutputMapProps): Root;
