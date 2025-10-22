// Keep this file focused on Shiny interop only.
// Rendering lives in map_view.ts

import {
  MapConfigPayload,
  MapPayload,
  MapView,
  normalizeConfig,
} from "./map_view.js";

const views = new Map<string, MapView>();
const registeredHandlers = new Set<string>();
const initializedInputs = new Set<string>();
const pendingHandlers = new Set<string>();
let shinyReady = false;

function ensureView(el: HTMLElement): MapView {
  let view = views.get(el.id);
  if (!view) {
    view = new MapView(el);
    views.set(el.id, view);
  }
  return view;
}

function onSetData(id: string, payload: MapPayload): void {
  const el = document.getElementById(id) as HTMLElement | null;
  if (!el) return;
  const view = ensureView(el);
  view.enableInput(null);
  view.updateData(payload);
}

function registerHandler(id: string): void {
  if (!id || registeredHandlers.has(id)) return;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const Shiny: any = (window as any).Shiny;
  if (!Shiny || !Shiny.addCustomMessageHandler) return;
  Shiny.addCustomMessageHandler(`jpmap:set_data:${id}`, (payload: MapPayload) =>
    onSetData(id, payload)
  );
  registeredHandlers.add(id);
}

function queueHandler(id: string): void {
  if (!id) return;
  if (shinyReady) {
    registerHandler(id);
  } else {
    pendingHandlers.add(id);
  }
}

function flushPendingHandlers(): void {
  pendingHandlers.forEach((id) => registerHandler(id));
  pendingHandlers.clear();
}

function bootstrapOutputs(scope: ParentNode = document): void {
  scope.querySelectorAll<HTMLElement>(".jpmap-output").forEach((el) => {
    queueHandler(el.id);
  });
}

function bootstrapInputs(scope: ParentNode = document): void {
  scope.querySelectorAll<HTMLElement>(".jpmap-input").forEach((el) => {
    if (!el.id || initializedInputs.has(el.id)) return;
    const view = ensureView(el);
    const config = readConfig(el);
    view.bootstrapFromConfig(config, el.id);
    view.enableInput(el.id);
    initializedInputs.add(el.id);
  });
}

function readConfig(el: HTMLElement): MapConfigPayload {
  const container = el.closest<HTMLElement>(".jpmap");
  const raw = container?.dataset.jpmapConfig;
  if (!raw) {
    return normalizeConfig(null);
  }
  try {
    const parsed = JSON.parse(raw);
    return normalizeConfig(parsed);
  } catch {
    return normalizeConfig(null);
  }
}

const observer = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    mutation.addedNodes.forEach((node) => {
      if (!(node instanceof HTMLElement)) return;
      if (node.classList.contains("jpmap-output")) {
        queueHandler(node.id);
      }
      if (node.classList.contains("jpmap-input")) {
        if (!initializedInputs.has(node.id) && node.id) {
          const view = ensureView(node);
          const config = readConfig(node);
          view.bootstrapFromConfig(config, node.id);
          view.enableInput(node.id);
          initializedInputs.add(node.id);
        }
      }
      bootstrapOutputs(node);
      bootstrapInputs(node);
    });
  });
});

observer.observe(document.documentElement, { childList: true, subtree: true });

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    bootstrapOutputs();
    bootstrapInputs();
  });
} else {
  bootstrapOutputs();
  bootstrapInputs();
}

document.addEventListener("shiny:connected", () => {
  shinyReady = true;
  flushPendingHandlers();
});
