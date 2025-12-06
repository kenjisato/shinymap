(() => {
  const RETRY_MS = 50;
  const MAX_WAIT_MS = 5000;

  function bootstrap(start = performance.now()) {
    const api =
      (typeof globalThis !== "undefined" && globalThis.shinymap) ||
      (typeof window !== "undefined" && window.shinymap) ||
      (typeof shinymap !== "undefined" ? shinymap : null);

    if (!api || typeof api.renderInputMap !== "function" || typeof api.renderOutputMap !== "function") {
      const elapsed = performance.now() - start;
      if (elapsed < MAX_WAIT_MS) {
        setTimeout(() => bootstrap(start), RETRY_MS);
      } else {
        console.warn("[shinymap] Global bundle not found after waiting; maps will not render.");
      }
      return;
    }

    const DEBUG = Boolean(window.localStorage?.shinymapDebug);
    const log = (...args) => {
      if (DEBUG) console.log(...args);
    };

    const { renderInputMap, renderOutputMap } = api;

    function parseJson(el, key) {
      const raw =
        el.dataset[key] ??
        el.dataset[key.replace(/([A-Z])/g, "_$1").toLowerCase()] ?? // support snake_case dataset (data_shinymap_payload)
        el.getAttribute(`data-${key.replace(/[A-Z]/g, (m) => `-${m.toLowerCase()}`)}`) ??
        el.getAttribute(`data_${key.replace(/[A-Z]/g, (m) => `_${m.toLowerCase()}`)}`);
      if (!raw) return null;
      try {
        return JSON.parse(raw);
      } catch (err) {
        console.warn("[shinymap] Failed to parse data attribute", key, err);
        return null;
      }
    }

    function mountInput(el) {
      log("[shinymap] mountInput", el);
      if (el.dataset.shinymapMounted === "input") {
        return;
      }
      const props = parseJson(el, "shinymapProps") || parseJson(el, "shinymap_props") || {};
      const inputId = el.dataset.shinymapInputId || el.dataset.shinymap_input_id || el.id;
      const mode = el.dataset.shinymapInputMode || el.dataset.shinymap_input_mode || props.mode;

      // Transform count map to appropriate format based on mode
      const transformValue = (countMap) => {
        if (mode === "count") {
          // Count mode: return the count map as-is
          return countMap;
        }
        // For single/multiple modes: extract selected IDs (count > 0)
        const selected = Object.entries(countMap)
          .filter(([_, count]) => count > 0)
          .map(([id, _]) => id);

        if (mode === "single") {
          // Single mode: return single ID or null
          return selected.length > 0 ? selected[0] : null;
        }
        // Multiple mode: return list of IDs
        return selected;
      };

      const onChange = (value) => {
        if (window.Shiny && typeof window.Shiny.setInputValue === "function" && inputId) {
          const transformed = transformValue(value);
          window.Shiny.setInputValue(inputId, transformed, { priority: "event" });
        }
      };

      // Add default resolveAesthetic if not provided
      if (!props.resolveAesthetic) {
        // Use cycle as fixed max if available, otherwise default to 10
        const countCeiling = props.cycle && Number.isFinite(props.cycle) ? props.cycle - 1 : 10;

        // Hue cycle colors (matches Python HUE_CYCLE_COLORS)
        const hueCycleColors = [
          "#e2e8f0", // 0: neutral gray (NEUTRALS["fill"])
          "#ef4444", // 1: red
          "#eab308", // 2: yellow
          "#22c55e", // 3: green
        ];

        props.resolveAesthetic = ({ mode, isSelected, isHovered, count, baseAesthetic }) => {
          const next = { ...baseAesthetic };

          // For single/multiple modes: highlight selected regions
          if ((mode === "single" || mode === "multiple") && isSelected) {
            next.fillOpacity = 0.8;
            next.strokeWidth = 2;
            next.strokeColor = "#1e40af"; // blue-800
          }

          // For count mode with cycle=4: use hue cycling
          if (mode === "count" && props.cycle === 4 && !props.fills) {
            const colorIndex = count % hueCycleColors.length;
            next.fillColor = hueCycleColors[colorIndex];
            next.fillOpacity = 1;
          }
          // For count mode (general): use saturated color with fixed opacity calculation
          else if (mode === "count" && count > 0 && !props.fills) {
            const alpha = countCeiling > 0 ? Math.min(1, count / countCeiling) : 0;
            next.fillColor = "#f97316"; // orange-500
            next.fillOpacity = 0.3 + alpha * 0.65;
          }

          // Hover highlighting: apply user-defined hover effects
          if (isHovered && props.hoverHighlight) {
            const hover = props.hoverHighlight;

            if (hover.stroke_width !== undefined) {
              next.strokeWidth = (next.strokeWidth ?? 1) + hover.stroke_width;
            }
            if (hover.fill_opacity !== undefined) {
              next.fillOpacity = Math.max(0, Math.min(1, (next.fillOpacity ?? 1) + hover.fill_opacity));
            }
            if (hover.stroke_color !== undefined) {
              next.strokeColor = hover.stroke_color;
            }
            if (hover.fill_color !== undefined) {
              next.fillColor = hover.fill_color;
            }
          }
          // Default hover behavior if no hover_highlight specified
          else if (isHovered) {
            next.strokeWidth = (next.strokeWidth ?? 1) + 1;
          }

          return next;
        };
      }

      renderInputMap(el, props, onChange);

      // Set initial value with aggressive retries
      const initialCountMap = props.value ?? {};
      const initialValue = transformValue(initialCountMap);
      if (inputId) {
        let attempts = 0;
        const maxAttempts = 50;
        const trySetValue = () => {
          attempts++;
          if (window.Shiny && typeof window.Shiny.setInputValue === "function") {
            window.Shiny.setInputValue(inputId, initialValue);
            log("[shinymap] Set initial value for", inputId, initialValue, `(attempt ${attempts})`);
            return true;
          }
          if (attempts < maxAttempts) {
            setTimeout(trySetValue, 50);
          } else {
            console.warn("[shinymap] Failed to set initial value for", inputId, "after", maxAttempts, "attempts");
          }
          return false;
        };
        trySetValue();
      }

      el.dataset.shinymapMounted = "input";
    }

    function mountOutput(el) {
      log("[shinymap] mountOutput", el);
      const payload = parseJson(el, "shinymapPayload") || parseJson(el, "shinymap_payload") || {};
      const clickInputId = el.dataset.shinymapClickInputId || el.dataset.shinymap_click_input_id;
      const onRegionClick =
        clickInputId && window.Shiny && typeof window.Shiny.setInputValue === "function"
          ? (id) => window.Shiny.setInputValue(clickInputId, id, { priority: "event" })
          : undefined;

      renderOutputMap(el, { ...payload, onRegionClick });
      el.dataset.shinymapMounted = "output";
    }

    function scan(root = document) {
      const inputSelector = "[data-shinymap-input],[data_shinymap_input],.shinymap-input";
      const outputSelector = "[data-shinymap-output],[data_shinymap_output],.shinymap-output";

      let inputs = Array.from(root.querySelectorAll(inputSelector));
      let outputs = Array.from(root.querySelectorAll(outputSelector));

      // Also check if the root element itself matches
      if (root !== document && root instanceof HTMLElement) {
        if (root.matches(inputSelector)) inputs.push(root);
        if (root.matches(outputSelector)) outputs.push(root);
      }

      log("[shinymap] scan found", inputs.length, "inputs", outputs.length, "outputs");
      inputs.forEach(mountInput);
      outputs.forEach(mountOutput);
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
          (mutation.attributeName === "data-shinymap-payload" || mutation.attributeName === "data_shinymap_payload")
        ) {
          log("[shinymap] Payload attribute changed on", mutation.target);
          mountOutput(mutation.target);
        }
      }
    });

    observer.observe(document.documentElement, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["data-shinymap-payload", "data_shinymap_payload"],
    });

    const rescan = (root) => {
      if (root && root instanceof HTMLElement) {
        scan(root);
      } else {
        scan();
      }
    };

    document.addEventListener("shiny:outputupdated", (event) => {
      log("[shinymap] shiny:outputupdated event for", event.target.id);
      // Delay scan slightly to ensure DOM is updated
      setTimeout(() => rescan(event.target), 10);
    });
    document.addEventListener("shiny:idle", () => {
      log("[shinymap] shiny:idle event");
      rescan();
    });
    document.addEventListener("shiny:connected", () => {
      log("[shinymap] shiny:connected event");
      rescan();
    });

    const doInitialScan = () => scan();
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", doInitialScan);
    } else {
      doInitialScan();
    }

    // A few delayed scans help catch outputs that render after initial load in Shiny.
    setTimeout(() => scan(), 25);
    setTimeout(() => scan(), 150);
    setTimeout(() => scan(), 300);
    setTimeout(() => scan(), 500);
    setTimeout(() => scan(), 1000);
    setTimeout(() => scan(), 2000);

    window.shinymapScan = scan;
  }

  bootstrap();
})();
