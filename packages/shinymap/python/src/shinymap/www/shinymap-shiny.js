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

      // Extract per-region aesthetics (from update_map or initial props)
      const strokeWidths = props.strokeWidth;
      const strokeColors = props.strokeColor;
      const fillOpacities = props.fillOpacity;

      // Clean up - these aren't valid InputMap props
      delete props.strokeWidth;
      delete props.strokeColor;
      delete props.fillOpacity;

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

        props.resolveAesthetic = ({ id, mode, isSelected, count, baseAesthetic }) => {
          const next = { ...baseAesthetic };

          // Apply per-region aesthetics first (from update_map)
          if (strokeWidths && typeof strokeWidths === "object" && strokeWidths[id] !== undefined) {
            next.strokeWidth = strokeWidths[id];
          }
          if (strokeColors && typeof strokeColors === "object" && strokeColors[id] !== undefined) {
            next.strokeColor = strokeColors[id];
          }
          if (fillOpacities && typeof fillOpacities === "object" && fillOpacities[id] !== undefined) {
            next.fillOpacity = fillOpacities[id];
          }

          // For single/multiple modes: highlight selected regions
          // BUT: skip if selectedAesthetic is explicitly provided (it takes precedence)
          if ((mode === "single" || mode === "multiple") && isSelected && !props.selectedAesthetic) {
            next.fillOpacity = 0.8;
            next.strokeWidth = 2;
            next.strokeColor = "#1e40af"; // blue-800
          }

          // For count mode with cycle=4: use hue cycling
          if (mode === "count" && props.cycle === 4 && !props.fillColor) {
            const colorIndex = count % hueCycleColors.length;
            next.fillColor = hueCycleColors[colorIndex];
            next.fillOpacity = 1;
          }
          // For count mode (general): use saturated color with fixed opacity calculation
          else if (mode === "count" && count > 0 && !props.fillColor) {
            const alpha = countCeiling > 0 ? Math.min(1, count / countCeiling) : 0;
            next.fillColor = "#f97316"; // orange-500
            next.fillOpacity = 0.3 + alpha * 0.65;
          }

          // NOTE: Hover highlighting is now handled by hoverHighlight prop
          // and rendered as a separate overlay layer in the React component

          return next;
        };
      }

      // Merge hoverHighlight with defaults (allow partial overrides)
      if (!props.hoverHighlight) {
        props.hoverHighlight = {
          strokeWidth: 2,
          strokeColor: "#1e40af", // blue-800
        };
      } else {
        // Merge user-provided partial hoverHighlight with defaults
        props.hoverHighlight = {
          strokeWidth: 2,
          strokeColor: "#1e40af",
          ...props.hoverHighlight, // User values override defaults
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

      // Note: OutputMap.tsx now handles fillColorSelected/fillColorNotSelected directly,
      // so we just pass the props through without creating resolveAesthetic logic
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

    // Register custom message handler for update_map()
    if (window.Shiny) {
      window.Shiny.addCustomMessageHandler("shinymap-update", function (message) {
        try {
          const { id, updates } = message;
          const el = document.getElementById(id);
          if (!el) {
            console.warn(`[shinymap] update_map: element with id="${id}" not found`);
            return;
          }

          const isInput = el.classList.contains("shinymap-input") || el.dataset.shinymapInput;
          const isOutput = el.classList.contains("shinymap-output") || el.dataset.shinymapOutput;

          if (isInput) {
            // For input maps, update props
            const currentProps = parseJson(el, "shinymapProps") || {};

            // Merge updates with current props
            const newProps = { ...currentProps, ...updates };

            // Preserve current value ONLY if not explicitly provided in updates
            // This allows update_map(id, value={}) to clear selections
            // Don't preserve null or empty values - let React component state take precedence
            if (updates.value === undefined) {
              if (currentProps.value && Object.keys(currentProps.value).length > 0) {
                newProps.value = currentProps.value;
              } else {
                // Don't pass null/empty value to React - delete it to let component state persist
                delete newProps.value;
              }
            }

            el.dataset.shinymapProps = JSON.stringify(newProps);

            // Re-render using existing root (preserves React state)
            if (el.__shinymapRoot && window.shinymap && window.shinymap.renderInputMap) {
              const inputId = el.dataset.shinymapInputId || el.dataset.shinymap_input_id || el.id;
              const mode = el.dataset.shinymapInputMode || el.dataset.shinymap_input_mode || newProps.mode;

              // Extract per-region aesthetics
              const strokeWidths = newProps.strokeWidth;
              const strokeColors = newProps.strokeColor;
              const fillOpacities = newProps.fillOpacity;

              // Clean up - these aren't valid InputMap props
              delete newProps.strokeWidth;
              delete newProps.strokeColor;
              delete newProps.fillOpacity;

              // Add default resolveAesthetic if not provided (same logic as mountInput)
              if (!newProps.resolveAesthetic) {
                const countCeiling = newProps.cycle && Number.isFinite(newProps.cycle) ? newProps.cycle - 1 : 10;
                const hueCycleColors = ["#e2e8f0", "#ef4444", "#eab308", "#22c55e"];

                newProps.resolveAesthetic = ({ id, mode, isSelected, count, baseAesthetic }) => {
                  const next = { ...baseAesthetic };

                  // Apply per-region aesthetics first
                  if (strokeWidths && typeof strokeWidths === "object" && strokeWidths[id] !== undefined) {
                    next.strokeWidth = strokeWidths[id];
                  }
                  if (strokeColors && typeof strokeColors === "object" && strokeColors[id] !== undefined) {
                    next.strokeColor = strokeColors[id];
                  }
                  if (fillOpacities && typeof fillOpacities === "object" && fillOpacities[id] !== undefined) {
                    next.fillOpacity = fillOpacities[id];
                  }

                  // Selection styling (skip if selectedAesthetic provided)
                  if ((mode === "single" || mode === "multiple") && isSelected && !newProps.selectedAesthetic) {
                    next.fillOpacity = 0.8;
                    next.strokeWidth = 2;
                    next.strokeColor = "#1e40af";
                  }

                  // Count mode coloring (skip if fillColor provided)
                  if (mode === "count" && newProps.cycle === 4 && !newProps.fillColor) {
                    const colorIndex = count % hueCycleColors.length;
                    next.fillColor = hueCycleColors[colorIndex];
                    next.fillOpacity = 1;
                  } else if (mode === "count" && count > 0 && !newProps.fillColor) {
                    const alpha = countCeiling > 0 ? Math.min(1, count / countCeiling) : 0;
                    next.fillColor = "#f97316";
                    next.fillOpacity = 0.3 + alpha * 0.65;
                  }

                  return next;
                };
              }

              // Merge hoverHighlight with defaults (allow partial overrides)
              if (!newProps.hoverHighlight) {
                newProps.hoverHighlight = {
                  strokeWidth: 2,
                  strokeColor: "#1e40af",
                };
              } else {
                // Merge user-provided partial hoverHighlight with defaults
                newProps.hoverHighlight = {
                  strokeWidth: 2,
                  strokeColor: "#1e40af",
                  ...newProps.hoverHighlight, // User values override defaults
                };
              }

              // Re-create onChange handler
              const transformValue = (countMap) => {
                if (mode === "count") return countMap;
                const selected = Object.entries(countMap)
                  .filter(([_, count]) => count > 0)
                  .map(([id, _]) => id);
                if (mode === "single") {
                  return selected.length > 0 ? selected[0] : null;
                }
                return selected;
              };
              const onChange = (value) => {
                if (window.Shiny && typeof window.Shiny.setInputValue === "function" && inputId) {
                  const transformed = transformValue(value);
                  window.Shiny.setInputValue(inputId, transformed, { priority: "event" });
                }
              };

              window.shinymap.renderInputMap(el, newProps, onChange);
            } else {
              // Fallback: unmount and remount
              if (el.__shinymapRoot) {
                el.__shinymapRoot.unmount();
                delete el.__shinymapRoot;
              }
              delete el.dataset.shinymapMounted;
              mountInput(el);
            }
          } else if (isOutput) {
            // For output maps, update payload
            const currentPayload = parseJson(el, "shinymapPayload") || {};
            const newPayload = { ...currentPayload, ...updates };
            el.dataset.shinymapPayload = JSON.stringify(newPayload);

            // Unmount existing React root to force complete re-render
            if (el.__shinymapRoot) {
              el.__shinymapRoot.unmount();
              delete el.__shinymapRoot;
            }

            // Remove mounted flag to force re-render
            delete el.dataset.shinymapMounted;
            mountOutput(el);
          } else {
            console.warn(`[shinymap] update_map: element id="${id}" is neither input nor output map`);
          }
        } catch (error) {
          console.error("[shinymap] update_map error:", error);
        }
      });
    }
  }

  bootstrap();
})();
