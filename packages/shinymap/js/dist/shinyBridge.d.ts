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
import type { InputMapProps, OutputMapProps, RegionId } from "./types";
interface ShinyMapAPI {
    renderInputMap: (target: HTMLElement, props: InputMapProps, onChange?: (value: Record<RegionId, number>) => void) => {
        unmount: () => void;
    };
    renderOutputMap: (target: HTMLElement, props: OutputMapProps) => {
        unmount: () => void;
    };
}
interface ShinyInterface {
    setInputValue: (id: string, value: unknown, options?: {
        priority?: string;
    }) => void;
    addCustomMessageHandler: (type: string, handler: (message: unknown) => void) => void;
}
declare global {
    interface Window {
        shinymap?: ShinyMapAPI;
        Shiny?: ShinyInterface;
        shinymapScan?: (root?: HTMLElement | Document) => void;
        localStorage?: Storage;
    }
    var shinymap: ShinyMapAPI | undefined;
}
export {};
