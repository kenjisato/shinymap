import { PREF_GEOMETRY } from "./pref_paths.js";

type ThemeConfig = {
  fillDefault: string;
  borderColor: string;
  showBorders: boolean;
  labelColor: string;
};

type MapSize = {
  width: string | null;
  height: string | null;
};

export type MapConfigPayload = {
  regions?: string[];
  okinawa: "original" | "topleft" | "bottomright";
  drawOmissionLine: boolean;
  theme: ThemeConfig;
  size: MapSize;
};

type GeometryLine = {
  origin: [number, number];
  target: [number, number];
};

type GeometryPayload = {
  paths: Record<string, string>;
  viewBox: [number, number, number, number];
  okinawaLine?: GeometryLine | null;
};

export type MapPayload = {
  geometry: GeometryPayload;
  fills: Record<string, string>;
  tooltips: Record<string, string>;
  config: {
    okinawa: "original" | "topleft" | "bottomright";
    drawOmissionLine: boolean;
    theme: ThemeConfig;
    size: MapSize;
  };
  colorbar: { visible: boolean; position: "right" | "bottom"; label: string };
};

const REGIONS: Record<string, string[]> = {
  Hokkaido: ["01"],
  Tohoku: ["02", "03", "04", "05", "06", "07"],
  Kanto: ["08", "09", "10", "11", "12", "13", "14"],
  Chubu: ["15", "16", "17", "18", "19", "20", "21", "22", "23"],
  Kinki: ["24", "25", "26", "27", "28", "29", "30"],
  Chugoku: ["31", "32", "33", "34", "35"],
  Shikoku: ["36", "37", "38", "39"],
  Kyushu: ["40", "41", "42", "43", "44", "45", "46"],
  Okinawa: ["47"],
};

const OKINAWA_BASE_SCALE = 0.42;
const OKINAWA_SCALE_BOOST = 1.5;

const PREF_NAMES: Record<string, string> = {
  "01": "Hokkaido",
  "02": "Aomori",
  "03": "Iwate",
  "04": "Miyagi",
  "05": "Akita",
  "06": "Yamagata",
  "07": "Fukushima",
  "08": "Ibaraki",
  "09": "Tochigi",
  "10": "Gunma",
  "11": "Saitama",
  "12": "Chiba",
  "13": "Tokyo",
  "14": "Kanagawa",
  "15": "Niigata",
  "16": "Toyama",
  "17": "Ishikawa",
  "18": "Fukui",
  "19": "Yamanashi",
  "20": "Nagano",
  "21": "Gifu",
  "22": "Shizuoka",
  "23": "Aichi",
  "24": "Mie",
  "25": "Shiga",
  "26": "Kyoto",
  "27": "Osaka",
  "28": "Hyogo",
  "29": "Nara",
  "30": "Wakayama",
  "31": "Tottori",
  "32": "Shimane",
  "33": "Okayama",
  "34": "Hiroshima",
  "35": "Yamaguchi",
  "36": "Tokushima",
  "37": "Kagawa",
  "38": "Ehime",
  "39": "Kochi",
  "40": "Fukuoka",
  "41": "Saga",
  "42": "Nagasaki",
  "43": "Kumamoto",
  "44": "Oita",
  "45": "Miyazaki",
  "46": "Kagoshima",
  "47": "Okinawa",
};

export function normalizeConfig(raw: unknown): MapConfigPayload {
  const baseTheme: ThemeConfig = {
    fillDefault: "#ffffff",
    borderColor: "#000000",
    showBorders: true,
    labelColor: "#000000",
  };
  if (!raw || typeof raw !== "object") {
    return {
      okinawa: "original",
      drawOmissionLine: true,
      theme: baseTheme,
      size: { width: null, height: null },
    };
  }
  const obj = raw as Record<string, unknown>;
  const themeRaw = (obj.theme as Record<string, unknown>) || {};
  const sizeRaw = (obj.size as Record<string, unknown>) || {};
  return {
    regions: Array.isArray(obj.regions)
      ? (obj.regions as unknown[]).map((r) => String(r))
      : undefined,
    okinawa: coercePlacement(obj.okinawa),
    drawOmissionLine: coerceBoolean(
      obj.drawOmissionLine ?? obj.draw_omission_line,
      true
    ),
    theme: {
      fillDefault: coerceString(
        themeRaw.fillDefault ?? themeRaw.fill_default,
        baseTheme.fillDefault
      ),
      borderColor: coerceString(
        themeRaw.borderColor ?? themeRaw.border_color,
        baseTheme.borderColor
      ),
      showBorders: coerceBoolean(
        themeRaw.showBorders ?? themeRaw.show_borders,
        baseTheme.showBorders
      ),
      labelColor: coerceString(
        themeRaw.labelColor ?? themeRaw.label_color,
        baseTheme.labelColor
      ),
    },
    size: {
      width: coerceOptionalString(
        sizeRaw.width ?? sizeRaw.map_width ?? (obj as Record<string, unknown>).map_width
      ),
      height: coerceOptionalString(
        sizeRaw.height ?? sizeRaw.map_height ?? (obj as Record<string, unknown>).map_height
      ),
    },
  };
}

export function geometryFromConfig(config: MapConfigPayload): GeometryPayload {
  const filtered = filterRegions(PREF_GEOMETRY.paths, config.regions);
  const adjusted =
    config.okinawa === "original"
      ? { paths: filtered, line: undefined }
      : repositionOkinawa(filtered, config.okinawa);
  const bounds = pathsBounds(adjusted.paths);
  const viewBox: [number, number, number, number] = bounds
    ? [
        bounds.minX,
        bounds.minY,
        bounds.maxX - bounds.minX || 1,
        bounds.maxY - bounds.minY || 1,
      ]
    : [0, 0, PREF_GEOMETRY.width, PREF_GEOMETRY.height];
  return {
    paths: adjusted.paths,
    viewBox,
    okinawaLine: adjusted.line ?? null,
  };
}

export class MapView {
  private el: HTMLElement;
  private svg: SVGSVGElement | null = null;
  private pathsGroup: SVGGElement | null = null;
  private colorbarGroup: SVGGElement | null = null;
  private omissionLine: SVGLineElement | null = null;
  private pathMap = new Map<string, SVGPathElement>();
  private viewBox: [number, number, number, number] = [
    0,
    0,
    PREF_GEOMETRY.width,
    PREF_GEOMETRY.height,
  ];
  private inputId: string | null = null;
  private theme: ThemeConfig = {
    fillDefault: "#ffffff",
    borderColor: "#000000",
    showBorders: true,
    labelColor: "#000000",
  };
  private size: MapSize = { width: null, height: null };

  constructor(el: HTMLElement) {
    this.el = el;
  }

  updateData(payload: MapPayload): void {
    this.theme = payload.config.theme;
    this.size = payload.config.size ?? { width: null, height: null };
    this.viewBox = payload.geometry.viewBox;
    this.ensureSvg();
    this.renderGeometry(payload.geometry.paths);
    this.applyTheme();
    this.applySize();
    this.applyFills(payload.fills);
    this.applyTooltips(payload.tooltips);
    this.renderOmissionLine(
      payload.config,
      payload.geometry.okinawaLine ?? null
    );
    this.renderColorbar(payload.fills, payload.colorbar);
  }

  enableInput(inputId: string | null): void {
    this.inputId = inputId;
    this.pathMap.forEach((path) => {
      path.style.cursor = inputId ? "pointer" : "default";
    });
  }

  bootstrapFromConfig(config: MapConfigPayload, inputId?: string): void {
    if (inputId) {
      this.inputId = inputId;
    }
    const geometry = geometryFromConfig(config);
    const payload: MapPayload = {
      geometry,
      fills: {},
      tooltips: {},
      config: {
        okinawa: config.okinawa,
        drawOmissionLine: config.drawOmissionLine,
        theme: config.theme,
        size: config.size ?? { width: null, height: null },
      },
      colorbar: { visible: false, position: "right", label: "" },
    };
    this.updateData(payload);
    if (inputId) {
      this.enableInput(inputId);
    }
  }

  private ensureSvg(): void {
    if (!this.svg) {
      const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
      this.el.innerHTML = "";
      this.el.appendChild(svg);
      this.svg = svg;
    }
    if (this.svg) {
      this.svg.setAttribute(
        "viewBox",
        this.viewBox.map((v) => formatNumber(v)).join(" ")
      );
      this.applySize();
    }
  }

  private applySize(): void {
    if (!this.svg) return;
    if (this.size.width) {
      this.svg.style.width = this.size.width;
      if (!this.el.style.width) {
        this.el.style.width = this.size.width;
      }
    } else {
      this.svg.style.width = "100%";
    }
    if (this.size.height) {
      this.svg.style.height = this.size.height;
      if (!this.el.style.height) {
        this.el.style.height = this.size.height;
      }
    } else {
      this.svg.style.height = "100%";
    }
  }

  private renderGeometry(paths: Record<string, string>): void {
    if (!this.svg) return;
    if (!this.pathsGroup) {
      this.pathsGroup = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "g"
      );
      this.pathsGroup.setAttribute("class", "jpmap-paths");
      this.svg.appendChild(this.pathsGroup);
    }
    this.pathMap.clear();
    while (this.pathsGroup.firstChild) {
      this.pathsGroup.removeChild(this.pathsGroup.firstChild);
    }
    Object.entries(paths).forEach(([code, d]) => {
      const path = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "path"
      );
      path.setAttribute("id", `pref-${code}`);
      path.setAttribute("d", d);
      path.dataset.prefCode = code;
      path.dataset.prefName = PREF_NAMES[code] ?? code;
      const defaultTip = path.dataset.prefName;
      path.dataset.defaultTip = defaultTip ?? code;
      const title = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "title"
      );
      title.textContent = defaultTip ?? code;
      path.appendChild(title);
      path.style.cursor = this.inputId ? "pointer" : "default";
      path.addEventListener("pointerenter", () => this.onHover(code, true));
      path.addEventListener("pointerleave", () => this.onHover(code, false));
      path.addEventListener("click", (event) => this.onClick(event, code));
      this.pathsGroup?.appendChild(path);
      this.pathMap.set(code, path);
    });
  }

  private applyTheme(): void {
    const stroke = this.theme.showBorders ? this.theme.borderColor : "none";
    const strokeWidth = this.theme.showBorders ? "1" : "0";
    this.pathMap.forEach((path) => {
      path.setAttribute("stroke", stroke);
      path.setAttribute("stroke-width", strokeWidth);
      if (!path.getAttribute("fill")) {
        path.setAttribute("fill", this.theme.fillDefault);
      }
    });
  }

  private applyFills(fills: Record<string, string>): void {
    this.pathMap.forEach((path, code) => {
      const fill = fills[code] ?? this.theme.fillDefault;
      path.setAttribute("fill", fill);
    });
  }

  private applyTooltips(tooltips: Record<string, string>): void {
    this.pathMap.forEach((path, code) => {
      const tip = tooltips[code] ?? path.dataset.defaultTip ?? code;
      let existing = path.querySelector<SVGTitleElement>("title");
      if (!existing) {
        existing = document.createElementNS(
          "http://www.w3.org/2000/svg",
          "title"
        ) as SVGTitleElement;
        path.insertBefore(existing, path.firstChild);
      }
      existing.textContent = tip;
    });
  }

  private renderOmissionLine(
    config: MapPayload["config"],
    line: GeometryLine | null
  ): void {
    if (!this.svg) return;
    const shouldDraw =
      line &&
      config.okinawa !== "original" &&
      config.drawOmissionLine &&
      this.pathMap.has("47");
    if (!shouldDraw) {
      if (this.omissionLine) {
        this.omissionLine.remove();
        this.omissionLine = null;
      }
      return;
    }
    if (!this.omissionLine) {
      this.omissionLine = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "line"
      );
      this.omissionLine.setAttribute("class", "jpmap-omission-line");
      this.svg.appendChild(this.omissionLine);
    }
    const [ox, oy] = line.origin;
    const [ix, iy] = line.target;
    this.omissionLine.setAttribute("x1", formatNumber(ox));
    this.omissionLine.setAttribute("y1", formatNumber(oy));
    this.omissionLine.setAttribute("x2", formatNumber(ix));
    this.omissionLine.setAttribute("y2", formatNumber(iy));
    this.omissionLine.setAttribute("stroke", "#555");
    this.omissionLine.setAttribute("stroke-width", "1.2");
    this.omissionLine.setAttribute("stroke-dasharray", "6,4");
  }

  private renderColorbar(
    fills: Record<string, string>,
    style: MapPayload["colorbar"]
  ): void {
    if (!this.svg) return;
    const colors = uniqueColors(Object.values(fills));
    if (!style.visible || colors.length === 0) {
      if (this.colorbarGroup) {
        this.colorbarGroup.remove();
        this.colorbarGroup = null;
      }
      return;
    }
    if (!this.colorbarGroup) {
      this.colorbarGroup = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "g"
      );
      this.colorbarGroup.setAttribute("id", "jpmap-colorbar");
      this.svg.appendChild(this.colorbarGroup);
    }
    while (this.colorbarGroup.firstChild) {
      this.colorbarGroup.removeChild(this.colorbarGroup.firstChild);
    }
    const swatch = 18;
    const padding = 12;
    const stroke = this.theme.showBorders ? this.theme.borderColor : "#333";
    if (style.position === "right") {
      const x = this.viewBox[2] - padding - swatch;
      let y = padding;
      colors.forEach((color) => {
        const rect = document.createElementNS(
          "http://www.w3.org/2000/svg",
          "rect"
        );
        rect.setAttribute("x", formatNumber(x));
        rect.setAttribute("y", formatNumber(y));
        rect.setAttribute("width", formatNumber(swatch));
        rect.setAttribute("height", formatNumber(swatch));
        rect.setAttribute("fill", color);
        rect.setAttribute("stroke", stroke);
        rect.setAttribute("stroke-width", "0.6");
        this.colorbarGroup?.appendChild(rect);
        y += swatch;
      });
      if (style.label) {
        const text = document.createElementNS(
          "http://www.w3.org/2000/svg",
          "text"
        );
        text.setAttribute("x", formatNumber(x - 6));
        const labelY = padding + (colors.length * swatch) / 2;
        text.setAttribute("y", formatNumber(labelY));
        text.setAttribute("text-anchor", "end");
        text.setAttribute("dominant-baseline", "middle");
        text.setAttribute("fill", this.theme.labelColor);
        text.textContent = style.label;
        this.colorbarGroup?.appendChild(text);
      }
    } else {
      let x = padding;
      const y = this.viewBox[3] - padding - swatch;
      colors.forEach((color) => {
        const rect = document.createElementNS(
          "http://www.w3.org/2000/svg",
          "rect"
        );
        rect.setAttribute("x", formatNumber(x));
        rect.setAttribute("y", formatNumber(y));
        rect.setAttribute("width", formatNumber(swatch));
        rect.setAttribute("height", formatNumber(swatch));
        rect.setAttribute("fill", color);
        rect.setAttribute("stroke", stroke);
        rect.setAttribute("stroke-width", "0.6");
        this.colorbarGroup?.appendChild(rect);
        x += swatch;
      });
      if (style.label) {
        const text = document.createElementNS(
          "http://www.w3.org/2000/svg",
          "text"
        );
        const labelX = padding + (colors.length * swatch) / 2;
        text.setAttribute("x", formatNumber(labelX));
        text.setAttribute("y", formatNumber(y - 6));
        text.setAttribute("text-anchor", "middle");
        text.setAttribute("fill", this.theme.labelColor);
        text.textContent = style.label;
        this.colorbarGroup?.appendChild(text);
      }
    }
  }

  private onHover(code: string, entering: boolean): void {
    const path = this.pathMap.get(code);
    if (!path) return;
    if (entering) {
      path.classList.add("is-hovered");
    } else {
      path.classList.remove("is-hovered");
    }
  }

  private onClick(event: Event, code: string): void {
    if (!this.inputId) {
      return;
    }
    event.preventDefault();
    const Shiny = (window as unknown as { Shiny?: any }).Shiny;
    if (Shiny && typeof Shiny.setInputValue === "function") {
      Shiny.setInputValue(this.inputId, code, { priority: "event" });
    }
  }
}

function filterRegions(
  paths: Record<string, string>,
  regions?: string[]
): Record<string, string> {
  if (!regions || regions.length === 0) {
    return { ...paths };
  }
  const allowed = new Set<string>();
  regions.forEach((region) => {
    const codes = REGIONS[region];
    if (codes) {
      codes.forEach((code) => allowed.add(code));
    }
  });
  const result: Record<string, string> = {};
  Object.entries(paths).forEach(([code, d]) => {
    if (allowed.has(code)) {
      result[code] = d;
    }
  });
  return result;
}

function repositionOkinawa(
  paths: Record<string, string>,
  placement: "topleft" | "bottomright"
): { paths: Record<string, string>; line?: GeometryLine } {
  const okinawaPath = paths["47"];
  if (!okinawaPath) {
    return { paths };
  }
  const originalCoords = parseCoords(okinawaPath);
  const originalBBox = bboxFromCoords(originalCoords);
  const width = originalBBox.maxX - originalBBox.minX;
  const height = originalBBox.maxY - originalBBox.minY;
  const scale = OKINAWA_BASE_SCALE * OKINAWA_SCALE_BOOST;
  const mainland = mainlandBBox(paths);
  const minX = mainland ? mainland.minX : 0;
  const minY = mainland ? mainland.minY : 0;
  const maxX = mainland ? mainland.maxX : PREF_GEOMETRY.width;
  const maxY = mainland ? mainland.maxY : PREF_GEOMETRY.height;
  let originX: number;
  let originY: number;
  if (placement === "topleft") {
    originX = minX;
    originY = minY;
  } else {
    originX = maxX - width * scale;
    originY = maxY - height * scale;
  }
  originX = clamp(originX, 0, PREF_GEOMETRY.width - width * scale);
  originY = clamp(originY, 0, PREF_GEOMETRY.height - height * scale);
  const dx = originX - originalBBox.minX * scale;
  const dy = originY - originalBBox.minY * scale;
  const transformed = transformPath(okinawaPath, scale, dx, dy);
  const newCoords = parseCoords(transformed);
  const newBBox = bboxFromCoords(newCoords);
  let line: GeometryLine | undefined;
  if (mainland) {
    const mid: [number, number] =
      placement === "topleft"
        ? [newBBox.maxX, newBBox.maxY]
        : [newBBox.minX, newBBox.minY];
    const availableNE = Math.min(
      mainland.maxX - mid[0],
      mid[1] - mainland.minY
    );
    const availableSW = Math.min(
      mid[0] - mainland.minX,
      mainland.maxY - mid[1]
    );
    const length = Math.max(0, Math.min(availableNE, availableSW));
    const origin: [number, number] = [mid[0] - length, mid[1] + length];
    const target: [number, number] = [mid[0] + length, mid[1] - length];
    line = { origin, target };
  }
  return {
    paths: { ...paths, "47": transformed },
    line,
  };
}

function mainlandBBox(paths: Record<string, string>) {
  const xs: number[] = [];
  const ys: number[] = [];
  Object.entries(paths).forEach(([code, d]) => {
    if (code === "47") return;
    parseCoords(d).forEach(([x, y]) => {
      xs.push(x);
      ys.push(y);
    });
  });
  if (xs.length === 0) return null;
  return {
    minX: Math.min(...xs),
    minY: Math.min(...ys),
    maxX: Math.max(...xs),
    maxY: Math.max(...ys),
  };
}

function pathsBounds(paths: Record<string, string>) {
  const xs: number[] = [];
  const ys: number[] = [];
  Object.values(paths).forEach((d) => {
    parseCoords(d).forEach(([x, y]) => {
      xs.push(x);
      ys.push(y);
    });
  });
  if (xs.length === 0) return null;
  return {
    minX: Math.min(...xs),
    minY: Math.min(...ys),
    maxX: Math.max(...xs),
    maxY: Math.max(...ys),
  };
}

function parseCoords(path: string): Array<[number, number]> {
  const tokens = tokenize(path);
  const coords: Array<[number, number]> = [];
  for (let i = 0; i < tokens.length; ) {
    const token = tokens[i++];
    if (token === "M" || token === "L") {
      const x = parseFloat(tokens[i++]);
      const y = parseFloat(tokens[i++]);
      coords.push([x, y]);
    }
  }
  return coords;
}

function transformPath(
  path: string,
  scale: number,
  dx: number,
  dy: number
): string {
  const tokens = tokenize(path);
  const out: string[] = [];
  for (let i = 0; i < tokens.length; ) {
    const token = tokens[i++];
    if (token === "M" || token === "L") {
      const x = parseFloat(tokens[i++]);
      const y = parseFloat(tokens[i++]);
      const nx = x * scale + dx;
      const ny = y * scale + dy;
      out.push(`${token}${formatNumber(nx)} ${formatNumber(ny)}`);
    } else if (token === "Z") {
      out.push("Z");
    }
  }
  return out.join("");
}

function tokenize(path: string): string[] {
  return path
    .replace(/([MLZ])/g, " $1 ")
    .trim()
    .split(/\s+/);
}

function bboxFromCoords(coords: Array<[number, number]>) {
  let minX = Number.POSITIVE_INFINITY;
  let minY = Number.POSITIVE_INFINITY;
  let maxX = Number.NEGATIVE_INFINITY;
  let maxY = Number.NEGATIVE_INFINITY;
  coords.forEach(([x, y]) => {
    if (x < minX) minX = x;
    if (y < minY) minY = y;
    if (x > maxX) maxX = x;
    if (y > maxY) maxY = y;
  });
  return { minX, minY, maxX, maxY };
}

function bboxCenter(bbox: ReturnType<typeof bboxFromCoords>): [number, number] {
  return [(bbox.minX + bbox.maxX) / 2, (bbox.minY + bbox.maxY) / 2];
}

function coercePlacement(
  value: unknown
): "original" | "topleft" | "bottomright" {
  const val = typeof value === "string" ? value.toLowerCase() : "";
  if (val === "topleft") return "topleft";
  if (val === "bottomright") return "bottomright";
  return "original";
}

function coerceBoolean(value: unknown, fallback: boolean): boolean {
  if (typeof value === "boolean") {
    return value;
  }
  if (typeof value === "string") {
    if (value.toLowerCase() === "true") return true;
    if (value.toLowerCase() === "false") return false;
  }
  return fallback;
}

function coerceString(value: unknown, fallback: string): string {
  return typeof value === "string" ? value : fallback;
}

function coerceOptionalString(value: unknown): string | null {
  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed.length > 0 ? trimmed : null;
  }
  return null;
}

function uniqueColors(colors: string[]): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  colors.forEach((color) => {
    if (!seen.has(color)) {
      seen.add(color);
      result.push(color);
    }
  });
  return result;
}

function clamp(value: number, minValue: number, maxValue: number): number {
  return Math.min(Math.max(value, minValue), maxValue);
}

function formatNumber(value: number): string {
  const text = value.toFixed(2).replace(/\.?0+$/, "");
  return text === "" ? "0" : text;
}
