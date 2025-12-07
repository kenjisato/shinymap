import React from "react";
import { createRoot as reactCreateRoot } from "react-dom/client";

import type { InputMapProps, OutputMapProps } from "./types";
import { InputMap } from "./components/InputMap";
import { OutputMap } from "./components/OutputMap";

export type { GeometryMap, InputMapProps, OutputMapProps, RegionId, TooltipMap } from "./types";
export { InputMap } from "./components/InputMap";
export { OutputMap } from "./components/OutputMap";
export { palette, neutrals, qualitative, sequential } from "./palette";

type CreateRootFn = typeof import("react-dom/client").createRoot;

type Root = ReturnType<CreateRootFn>;

function createRoot(target: HTMLElement): Root {
  return reactCreateRoot(target);
}

function getRoot(target: HTMLElement): Root {
  const existing = (target as { __shinymapRoot?: Root }).__shinymapRoot;
  if (existing) {
    return existing;
  }
  const created = createRoot(target);
  (target as { __shinymapRoot?: Root }).__shinymapRoot = created;
  return created;
}

/**
 * Imperatively render an InputMap into a target element. Useful for non-React hosts (e.g., Shiny).
 */
export function renderInputMap(
  target: HTMLElement,
  props: InputMapProps,
  onChange?: InputMapProps["onChange"]
): Root {
  const root = getRoot(target);
  const componentProps = { ...props, onChange: onChange ?? props.onChange } as InputMapProps;
  const Component = InputMap as React.ComponentType<InputMapProps>;
  root.render(<Component {...componentProps} />);
  return root;
}

/**
 * Imperatively render an OutputMap into a target element. Useful for non-React hosts (e.g., Shiny).
 */
export function renderOutputMap(target: HTMLElement, props: OutputMapProps): Root {
  const root = getRoot(target);
  const Component = OutputMap as React.ComponentType<OutputMapProps>;
  root.render(<Component {...props} />);
  return root;
}
