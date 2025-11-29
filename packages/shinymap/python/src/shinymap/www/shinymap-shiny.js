(() => {
  const api = window.shinymap;
  if (!api || typeof api.renderInputMap !== "function" || typeof api.renderOutputMap !== "function") {
    console.warn("[shinymap] Global bundle not found; maps will not render.");
    return;
  }

  const { renderInputMap, renderOutputMap } = api;

  function parseJson(el, key) {
    const raw = el.dataset[key];
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch (err) {
      console.warn("[shinymap] Failed to parse data attribute", key, err);
      return null;
    }
  }

  function mountInput(el) {
    if (el.dataset.shinymapMounted === "input") {
      return;
    }
    const props = parseJson(el, "shinymapProps") || {};
    const inputId = el.dataset.shinymapInputId || el.id;
    const onChange = (value) => {
      if (window.Shiny && typeof window.Shiny.setInputValue === "function" && inputId) {
        window.Shiny.setInputValue(inputId, value, { priority: "event" });
      }
    };
    renderInputMap(el, props, onChange);
    el.dataset.shinymapMounted = "input";
  }

  function mountOutput(el) {
    const payload = parseJson(el, "shinymapPayload") || {};
    const clickInputId = el.dataset.shinymapClickInputId;
    const onRegionClick =
      clickInputId && window.Shiny && typeof window.Shiny.setInputValue === "function"
        ? (id) => window.Shiny.setInputValue(clickInputId, id, { priority: "event" })
        : undefined;

    renderOutputMap(el, { ...payload, onRegionClick });
    el.dataset.shinymapMounted = "output";
  }

  function scan(root = document) {
    root.querySelectorAll("[data-shinymap-input]").forEach(mountInput);
    root.querySelectorAll("[data-shinymap-output]").forEach(mountOutput);
  }

  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      mutation.addedNodes.forEach((node) => {
        if (!(node instanceof HTMLElement)) return;
        scan(node);
      });
      if (
        mutation.type === "attributes" &&
        mutation.target instanceof HTMLElement &&
        mutation.attributeName === "data-shinymap-payload"
      ) {
        mountOutput(mutation.target);
      }
    }
  });

  observer.observe(document.documentElement, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["data-shinymap-payload"],
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => scan());
  } else {
    scan();
  }
})();
