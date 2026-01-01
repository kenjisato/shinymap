/**
 * Shiny bridge for shinymap.
 *
 * This module provides the glue code between Python Shiny and the React components.
 * It handles:
 * - Waiting for the global bundle to load
 * - Converting snake_case props from Python to camelCase for React
 * - Mounting input/output map components
 * - Handling Shiny custom messages for update_map()
 *
 * Built separately from the main bundle and loaded after shinymap.global.js.
 */
import { snakeToCamelDeep } from "./utils/caseConvert";
const RETRY_MS = 50;
const MAX_WAIT_MS = 5000;
function bootstrap(start = performance.now()) {
    var _a;
    const api = (typeof globalThis !== "undefined" && globalThis.shinymap) ||
        (typeof window !== "undefined" && window.shinymap) ||
        (typeof shinymap !== "undefined" ? shinymap : null);
    if (!api ||
        typeof api.renderInputMap !== "function" ||
        typeof api.renderOutputMap !== "function") {
        const elapsed = performance.now() - start;
        if (elapsed < MAX_WAIT_MS) {
            setTimeout(() => bootstrap(start), RETRY_MS);
        }
        else {
            console.warn("[shinymap] Global bundle not found after waiting; maps will not render.");
        }
        return;
    }
    const DEBUG = Boolean((_a = window.localStorage) === null || _a === void 0 ? void 0 : _a.getItem("shinymapDebug"));
    const log = (...args) => {
        if (DEBUG)
            console.log(...args);
    };
    const { renderInputMap, renderOutputMap } = api;
    function parseJson(el, key) {
        var _a, _b, _c;
        const camelKey = key;
        const snakeKey = key.replace(/([A-Z])/g, "_$1").toLowerCase();
        const kebabKey = key.replace(/[A-Z]/g, (m) => `-${m.toLowerCase()}`);
        const raw = (_c = (_b = (_a = el.dataset[camelKey]) !== null && _a !== void 0 ? _a : el.dataset[snakeKey]) !== null && _b !== void 0 ? _b : el.getAttribute(`data-${kebabKey}`)) !== null && _c !== void 0 ? _c : el.getAttribute(`data_${snakeKey}`);
        if (!raw)
            return null;
        try {
            return JSON.parse(raw);
        }
        catch (err) {
            console.warn("[shinymap] Failed to parse data attribute", key, err);
            return null;
        }
    }
    function mountInput(el) {
        var _a;
        log("[shinymap] mountInput", el);
        if (el.dataset.shinymapMounted === "input") {
            return;
        }
        // Parse props and convert snake_case to camelCase
        const rawProps = parseJson(el, "shinymapProps") || parseJson(el, "shinymap_props") || {};
        const props = snakeToCamelDeep(rawProps);
        const inputId = el.dataset.shinymapInputId || el.dataset.shinymap_input_id || el.id;
        // Extract mode type from nested mode config
        const modeConfig = (props.mode || {});
        const modeType = modeConfig.type ||
            el.dataset.shinymapInputMode ||
            el.dataset.shinymap_input_mode ||
            "multiple";
        // Transform count map to appropriate format based on mode
        const transformValue = (countMap) => {
            if (modeType === "count" || modeType === "cycle") {
                return countMap;
            }
            const selected = Object.entries(countMap)
                .filter(([, count]) => count > 0)
                .map(([id]) => id);
            if (modeType === "single") {
                return selected.length > 0 ? selected[0] : null;
            }
            return selected;
        };
        const onChange = (value) => {
            if (window.Shiny &&
                typeof window.Shiny.setInputValue === "function" &&
                inputId) {
                const transformed = transformValue(value);
                window.Shiny.setInputValue(inputId, transformed, { priority: "event" });
            }
        };
        renderInputMap(el, props, onChange);
        // Set initial value with aggressive retries
        const initialCountMap = (_a = props.value) !== null && _a !== void 0 ? _a : {};
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
                }
                else {
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
        // Parse payload and convert snake_case to camelCase
        const rawPayload = parseJson(el, "shinymapPayload") || parseJson(el, "shinymap_payload") || {};
        const payload = snakeToCamelDeep(rawPayload);
        const clickInputId = el.dataset.shinymapClickInputId || el.dataset.shinymap_click_input_id;
        const onRegionClick = clickInputId &&
            window.Shiny &&
            typeof window.Shiny.setInputValue === "function"
            ? (id) => window.Shiny.setInputValue(clickInputId, id, { priority: "event" })
            : undefined;
        renderOutputMap(el, { ...payload, onRegionClick });
        el.dataset.shinymapMounted = "output";
    }
    function scan(root = document) {
        const inputSelector = "[data-shinymap-input],[data_shinymap_input],.shinymap-input";
        const outputSelector = "[data-shinymap-output],[data_shinymap_output],.shinymap-output";
        const inputs = Array.from(root.querySelectorAll(inputSelector));
        const outputs = Array.from(root.querySelectorAll(outputSelector));
        // Also check if the root element itself matches
        if (root !== document && root instanceof HTMLElement) {
            if (root.matches(inputSelector))
                inputs.push(root);
            if (root.matches(outputSelector))
                outputs.push(root);
        }
        log("[shinymap] scan found", inputs.length, "inputs", outputs.length, "outputs");
        inputs.forEach(mountInput);
        outputs.forEach(mountOutput);
    }
    const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            mutation.addedNodes.forEach((node) => {
                if (!(node instanceof HTMLElement))
                    return;
                scan(node);
            });
            if (mutation.type === "attributes" &&
                mutation.target instanceof HTMLElement &&
                (mutation.attributeName === "data-shinymap-payload" ||
                    mutation.attributeName === "data_shinymap_payload")) {
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
        }
        else {
            scan();
        }
    };
    document.addEventListener("shiny:outputupdated", (event) => {
        var _a;
        log("[shinymap] shiny:outputupdated event for", (_a = event.target) === null || _a === void 0 ? void 0 : _a.id);
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
    }
    else {
        doInitialScan();
    }
    // Delayed scans for outputs that render after initial load
    setTimeout(() => scan(), 25);
    setTimeout(() => scan(), 150);
    setTimeout(() => scan(), 300);
    setTimeout(() => scan(), 500);
    setTimeout(() => scan(), 1000);
    setTimeout(() => scan(), 2000);
    window.shinymapScan = scan;
    // Register custom message handler for update_map()
    if (window.Shiny) {
        window.Shiny.addCustomMessageHandler("shinymap-update", (message) => {
            var _a;
            try {
                const { id, updates: rawUpdates } = message;
                // Convert updates from snake_case to camelCase
                const updates = snakeToCamelDeep(rawUpdates);
                const el = document.getElementById(id);
                if (!el) {
                    console.warn(`[shinymap] update_map: element with id="${id}" not found`);
                    return;
                }
                const isInput = el.classList.contains("shinymap-input") || el.dataset.shinymapInput;
                const isOutput = el.classList.contains("shinymap-output") || el.dataset.shinymapOutput;
                if (isInput) {
                    // Parse current props and convert
                    const currentRaw = parseJson(el, "shinymapProps") || {};
                    const currentProps = snakeToCamelDeep(currentRaw);
                    // Merge updates
                    const newProps = { ...currentProps, ...updates };
                    // Preserve current value if not explicitly provided
                    if (updates.value === undefined) {
                        const currentValue = currentProps.value;
                        if (currentValue && Object.keys(currentValue).length > 0) {
                            newProps.value = currentValue;
                        }
                        else {
                            delete newProps.value;
                        }
                    }
                    el.dataset.shinymapProps = JSON.stringify(newProps);
                    // Re-render
                    if (el.__shinymapRoot && ((_a = window.shinymap) === null || _a === void 0 ? void 0 : _a.renderInputMap)) {
                        const inputId = el.dataset.shinymapInputId ||
                            el.dataset.shinymap_input_id ||
                            el.id;
                        const modeConfig = (newProps.mode || {});
                        const modeType = modeConfig.type ||
                            el.dataset.shinymapInputMode ||
                            el.dataset.shinymap_input_mode ||
                            "multiple";
                        const transformValue = (countMap) => {
                            if (modeType === "count" || modeType === "cycle")
                                return countMap;
                            const selected = Object.entries(countMap)
                                .filter(([, count]) => count > 0)
                                .map(([id]) => id);
                            if (modeType === "single") {
                                return selected.length > 0 ? selected[0] : null;
                            }
                            return selected;
                        };
                        const onChange = (value) => {
                            if (window.Shiny &&
                                typeof window.Shiny.setInputValue === "function" &&
                                inputId) {
                                const transformed = transformValue(value);
                                window.Shiny.setInputValue(inputId, transformed, {
                                    priority: "event",
                                });
                            }
                        };
                        window.shinymap.renderInputMap(el, newProps, onChange);
                    }
                    else {
                        // Fallback: unmount and remount
                        if (el.__shinymapRoot) {
                            el.__shinymapRoot.unmount();
                            delete el.__shinymapRoot;
                        }
                        delete el.dataset.shinymapMounted;
                        mountInput(el);
                    }
                }
                else if (isOutput) {
                    // Parse current payload and convert
                    const currentRaw = parseJson(el, "shinymapPayload") || {};
                    const currentPayload = snakeToCamelDeep(currentRaw);
                    const newPayload = { ...currentPayload, ...updates };
                    el.dataset.shinymapPayload = JSON.stringify(newPayload);
                    // Unmount and remount
                    if (el.__shinymapRoot) {
                        el.__shinymapRoot.unmount();
                        delete el.__shinymapRoot;
                    }
                    delete el.dataset.shinymapMounted;
                    mountOutput(el);
                }
                else {
                    console.warn(`[shinymap] update_map: element id="${id}" is neither input nor output map`);
                }
            }
            catch (error) {
                console.error("[shinymap] update_map error:", error);
            }
        });
    }
}
bootstrap();
