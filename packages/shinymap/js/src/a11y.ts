/**
 * Accessibility constants: keyboard bindings and the default focus indicator.
 *
 * This module is the **single tuning point** for keyboard and focus UX.
 * Both the key bindings and the focus ring are expected to be adjusted after
 * hands-on use, so components must read them from here rather than hardcoding
 * key names or ring colors.
 *
 * See specs/003-accessibility/plan.md (D3, D5).
 */

import type { ResolvedAesthetic } from "./types";

/**
 * Keyboard actions a focused region can trigger.
 *
 * - `next` / `prev`: move focus to the adjacent interactive region (wrapping)
 * - `first` / `last`: move focus to the first / last interactive region
 * - `activate`: same semantics as a mouse click for the current mode
 * - `increment` / `decrement`: adjust the region's value (count and cycle modes)
 */
export type KeyAction = "next" | "prev" | "first" | "last" | "activate" | "increment" | "decrement";

/**
 * Maps `KeyboardEvent.key` values to actions.
 *
 * Keys absent from this map are ignored and must not be `preventDefault()`ed,
 * so browser and screen-reader shortcuts keep working.
 *
 * Note on `"="`: on many keyboard layouts `+` is Shift+`=`, and some browsers
 * report the unshifted key. Both are bound to `increment`.
 */
export const KEY_BINDINGS: Readonly<Record<string, KeyAction>> = {
  ArrowRight: "next",
  ArrowDown: "next",
  ArrowLeft: "prev",
  ArrowUp: "prev",
  Home: "first",
  End: "last",
  Enter: "activate",
  " ": "activate",
  "+": "increment",
  "=": "increment",
  "-": "decrement",
};

/**
 * Default visual indicator for the keyboard-focused region.
 *
 * Rendered as a non-interactive overlay above the hover layer, so it is never
 * obscured by a neighboring region's fill. `fillColor: "none"` keeps the
 * region's own colors visible underneath — the ring alone marks focus, which
 * is what distinguishes it from hover and selection styling.
 */
export const DEFAULT_FOCUS_AESTHETIC: ResolvedAesthetic = {
  strokeColor: "#1d4ed8",
  strokeWidth: 3,
  fillColor: "none",
};
