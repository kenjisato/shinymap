export function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const normalized = hex.replace(/^#/, "");
  if (!/^([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(normalized)) {
    return null;
  }
  const value =
    normalized.length === 3
      ? normalized
          .split("")
          .map((char) => char + char)
          .join("")
      : normalized;
  const intVal = parseInt(value, 16);
  return {
    r: (intVal >> 16) & 255,
    g: (intVal >> 8) & 255,
    b: intVal & 255,
  };
}

export function applyAlpha(hex: string, alpha: number, fallback: string): string {
  const rgb = hexToRgb(hex);
  if (!rgb) {
    return fallback;
  }
  const clamped = Math.max(0, Math.min(1, alpha));
  return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${clamped})`;
}
