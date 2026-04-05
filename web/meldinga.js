const MELDINGA_DATA = window.MELDINGA_DATA || { spots: {} };
const LIVE_WIND_DATA = window.LIVE_WIND_DATA || { sources: {}, instantSources: {} };
const NOAA_FORECAST_DATA = window.NOAA_FORECAST_DATA || { spots: {} };
const TIDE_DATA = window.TIDE_DATA || { spots: {} };
const FORECAST_DATA = Object.keys(MELDINGA_DATA.spots || {}).length ? MELDINGA_DATA : NOAA_FORECAST_DATA;

const OSLO_TIMEZONE = "Europe/Oslo";
const MONTHS_NO = ["januar", "februar", "mars", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "desember"];
const WEEKDAYS_NO = ["søndag", "mandag", "tirsdag", "onsdag", "torsdag", "fredag", "lørdag"];
const HOVER_POINTER_QUERY = window.matchMedia("(hover: hover) and (pointer: fine)");
const MOBILE_LAYOUT_QUERY = window.matchMedia("(max-width: 720px)");
const SHOW_DIRECTION_DEGREES_ON_HOVER = true;
const KNOT_TO_MS = 0.514444;
const WINDGURU_WIND_PALETTE = [
  [0, 255, 255, 255],
  [5, 255, 255, 255],
  [8.9, 103, 247, 241],
  [13.5, 0, 255, 0],
  [18.8, 255, 240, 0],
  [24.7, 255, 50, 44],
  [31.7, 255, 10, 200],
  [38, 255, 0, 255],
  [45, 150, 50, 255],
  [60, 60, 60, 255],
  [70, 0, 0, 255],
];
const DETAIL_TIDE_GRAPH = {
  width: 760,
  height: 250,
  marginTop: 20,
  marginRight: 0,
  marginBottom: 34,
  marginLeft: 0,
  astronomicalColor: "#071629",
  secondaryColor: "#1d8fe1",
  fillColor: "rgba(7, 22, 41, 0.08)",
  axisColor: "#071629",
  darkFill: "rgba(7, 22, 41, 0.12)",
  darkOverlayFill: "rgba(7, 22, 41, 0.10)",
  civilFill: "rgba(7, 22, 41, 0.06)",
  dayFill: "#FFFFFF",
};

const OBSERVATION_LAYOUT_CONFIG = {
  "Lista": [
    { name: "Lista Fyr", sourceName: "Lista Fyr" },
    { name: "Søndre Katland", placeholder: true },
  ],
  "Pigsty/Piggy": [
    { name: "Obrestad Fyr", sourceName: "Obrestad Fyr" },
    { name: "Vigdel", sourceName: "Vigdel" },
    { name: "Sola", placeholder: true },
    { name: "Eigerøya", placeholder: true },
    { name: "Kvitsøy - Nordbø", placeholder: true },
    { name: "Hemnes", placeholder: true },
    { name: "Utsira Fyr", placeholder: true },
  ],
};

const DETAIL_TIDE_LABEL_LAYOUT = {
  curveTopInset: 50,
  curveBottomInset: 34,
  highGap: 14,
  lowGap: 14,
  timeToValueGap: 15,
  topLabelMin: 28,
  bottomLabelMax: 16,
  sideInset: 34,
};

const SPOT_ORDER = [
  "Persfjord",
  "Unstad Beach",
  "Hustadvika Gjestegard",
  "Alnes Lighthouse (Godoy)",
  "Ervika",
  "Pigsty/Piggy",
  "Lista",
  "Mandal / Sjosanden",
  "Saltstein",
];

const SPOT_RULE_CONFIG = {
  "Persfjord": {
    displayName: "Varanger",
    wind: { start: 135, end: 315 },
    wave: null,
  },
  "Unstad Beach": {
    displayName: "Lofoten",
    wind: { start: 90, end: 225 },
    wave: { start: 67.5, end: 180 },
  },
  "Hustadvika Gjestegard": {
    displayName: "Hustadvika",
    wind: { start: 135, end: 225 },
    wave: { start: 67.5, end: 180 },
  },
  "Alnes Lighthouse (Godoy)": {
    displayName: "Ålesund",
    wind: { start: 45, end: 180 },
    wave: { start: 67.5, end: 180 },
  },
  "Ervika": {
    displayName: "Stad",
    wind: { start: 45, end: 225 },
    wave: { start: 67.5, end: 157.5 },
  },
  "Pigsty/Piggy": {
    displayName: "Jæren",
    wind: { start: 0, end: 180 },
    wave: { start: 45, end: 135 },
  },
  "Lista": {
    displayName: "Lista",
    wind: { start: 0, end: 90 },
    wave: { start: 45, end: 90 },
  },
  "Mandal / Sjosanden": {
    displayName: "Sjøsanden",
    wind: { start: 67.5, end: 270 },
    wave: { start: 292.5, end: 112.5 },
  },
  "Saltstein": {
    displayName: "Saltsteinen",
    wind: { start: 0, end: 90 },
    wave: { start: 315, end: 45 },
  },
};

const spotListEl = document.getElementById("spot-list");
const overviewViewEl = document.getElementById("overview-view");
const detailViewEl = document.getElementById("detail-view");
const pageShellEl = document.querySelector(".page-shell");
const detailSpotTitleEl = document.getElementById("detail-spot-title");
const detailContentEl = document.getElementById("detail-content");
const detailBackEl = document.getElementById("detail-back");
const detailStickyEl = document.getElementById("detail-sticky");
const detailTopbarEl = detailStickyEl?.querySelector(".detail-topbar") || null;
const detailTabEls = [...document.querySelectorAll("[data-detail-tab]")];
const detailControlsEl = document.getElementById("detail-controls");
const detailDayIndicatorEl = document.getElementById("detail-day-indicator");
const detailWindTargetControlEl = document.getElementById("detail-wind-target-control");
const detailWindTargetEl = document.getElementById("detail-wind-target");
const detailSettingsButtonEl = document.getElementById("detail-settings-button");
const detailSettingsPanelEl = document.getElementById("detail-settings-panel");
const detailWindColorToggleEl = document.getElementById("detail-wind-color-toggle");
const detailWindDirectionModeEl = document.getElementById("detail-wind-direction-mode");
const detailWaveDirectionModeEl = document.getElementById("detail-wave-direction-mode");
const timePanelEl = document.getElementById("time-panel");
const timePanelMetaEl = document.getElementById("time-panel-meta");
const timeRangeEl = document.getElementById("time-range");
const timeValueEl = document.getElementById("time-value");
const timeStartEl = document.getElementById("time-start");
const timeEndEl = document.getElementById("time-end");
const menuButtonEl = document.getElementById("menu-button");
const menuPanelEl = document.getElementById("menu-panel");
const windColorToggleEl = document.getElementById("wind-color-toggle");

const activeSpots = SPOT_ORDER.filter((spotName) => FORECAST_DATA.spots && FORECAST_DATA.spots[spotName]);
const flattenedForecasts = new Map();
const forecastRows = new Map();
const sliderSlots = [];
const detailExpandedDates = new Map();
const selectedWeatherOptionBySpot = new Map();

let selectedIndex = 0;
let currentSpotName = null;
let currentDetailTab = "forecast";
let windColorEnabled = true;
let detailWindDirectionMode = "arrow";
let detailWaveDirectionMode = "arrow";
let shouldResetDetailScroll = false;
let overviewReserveSyncFrame = 0;
let detailStickyStateSyncFrame = 0;

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function getOsloParts(date) {
  const formatter = new Intl.DateTimeFormat("en-GB", {
    timeZone: OSLO_TIMEZONE,
    year: "numeric",
    month: "numeric",
    day: "numeric",
    hour: "numeric",
    minute: "numeric",
    second: "numeric",
    hour12: false,
  });
  const entries = {};
  formatter.formatToParts(date).forEach((part) => {
    if (part.type !== "literal") {
      entries[part.type] = Number(part.value);
    }
  });
  return entries;
}

function weekdayIndexInOslo(date) {
  const weekday = new Intl.DateTimeFormat("en-US", {
    timeZone: OSLO_TIMEZONE,
    weekday: "short",
  }).format(date);
  const map = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 };
  return map[weekday] ?? 0;
}

function formatSelectedTime(date) {
  const parts = getOsloParts(date);
  const weekday = WEEKDAYS_NO[weekdayIndexInOslo(date)];
  const month = MONTHS_NO[parts.month - 1];
  return `${weekday} ${parts.day}. ${month} ${String(parts.hour).padStart(2, "0")}:${String(parts.minute).padStart(2, "0")}`;
}

function formatShortTime(date) {
  const parts = getOsloParts(date);
  const month = MONTHS_NO[parts.month - 1];
  return `${parts.day}. ${month}`;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function pad2(value) {
  return String(value).padStart(2, "0");
}

function dateLocalFromUtc(timeUtc) {
  const parts = getOsloParts(new Date(timeUtc));
  return `${parts.year}-${pad2(parts.month)}-${pad2(parts.day)}`;
}

function timeLocalFromUtc(timeUtc) {
  const parts = getOsloParts(new Date(timeUtc));
  return `${pad2(parts.hour)}:${pad2(parts.minute)}`;
}

function parseTimeLocalMinutes(timeLocal) {
  if (typeof timeLocal !== "string") return Number.NaN;
  const [hourText, minuteText = "0"] = timeLocal.split(":");
  const hour = Number(hourText);
  const minute = Number(minuteText);
  if (!Number.isFinite(hour) || !Number.isFinite(minute)) return Number.NaN;
  return (hour * 60) + minute;
}

function normalizeForecastRow(row) {
  if (!row?.timeUtc) return row;
  return {
    ...row,
    dateLocal: row.dateLocal || dateLocalFromUtc(row.timeUtc),
    timeLocal: row.timeLocal || timeLocalFromUtc(row.timeUtc),
    showGust: Boolean(row.showGust || Number.isFinite(row.windGustMs)),
  };
}

function rgbToHsl(rgb) {
  const [r, g, b] = rgb.map((value) => value / 255);
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const lightness = (max + min) / 2;
  const delta = max - min;

  if (delta === 0) {
    return [0, 0, lightness * 100];
  }

  const saturation = lightness > 0.5 ? delta / (2 - max - min) : delta / (max + min);

  let hue;
  switch (max) {
    case r:
      hue = ((g - b) / delta) + (g < b ? 6 : 0);
      break;
    case g:
      hue = ((b - r) / delta) + 2;
      break;
    default:
      hue = ((r - g) / delta) + 4;
      break;
  }

  return [(hue * 60) % 360, saturation * 100, lightness * 100];
}

function hueToRgb(p, q, t) {
  let value = t;
  if (value < 0) value += 1;
  if (value > 1) value -= 1;
  if (value < 1 / 6) return p + (q - p) * 6 * value;
  if (value < 1 / 2) return q;
  if (value < 2 / 3) return p + (q - p) * (2 / 3 - value) * 6;
  return p;
}

function hslToRgb(hsl) {
  const [h, sRaw, lRaw] = hsl;
  const hNorm = ((h % 360) + 360) % 360 / 360;
  const s = clamp(sRaw, 0, 100) / 100;
  const l = clamp(lRaw, 0, 100) / 100;

  if (s === 0) {
    const gray = Math.round(l * 255);
    return [gray, gray, gray];
  }

  const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
  const p = 2 * l - q;

  return [
    Math.round(hueToRgb(p, q, hNorm + 1 / 3) * 255),
    Math.round(hueToRgb(p, q, hNorm) * 255),
    Math.round(hueToRgb(p, q, hNorm - 1 / 3) * 255),
  ];
}

function adjustWindguruRgb(rgb) {
  const [h, s, l] = rgbToHsl(rgb);
  return hslToRgb([h + 2, s - 2, l + 2]);
}

const WINDGURU_ADJUSTED_PALETTE = WINDGURU_WIND_PALETTE.map((point) => [
  point[0],
  ...adjustWindguruRgb(point.slice(1, 4)),
]);

function msToKnots(ms) {
  return ms / KNOT_TO_MS;
}

function interpolateWindColor(knots, sourcePalette) {
  if (knots <= sourcePalette[0][0]) {
    return sourcePalette[0].slice(1, 4);
  }
  if (knots >= sourcePalette[sourcePalette.length - 1][0]) {
    return sourcePalette[sourcePalette.length - 1].slice(1, 4);
  }

  for (let i = 0; i < sourcePalette.length - 1; i += 1) {
    const start = sourcePalette[i];
    const end = sourcePalette[i + 1];
    if (knots >= start[0] && knots <= end[0]) {
      const ratio = (knots - start[0]) / (end[0] - start[0] || 1);
      return [0, 1, 2].map((channelIndex) => {
        const startValue = start[channelIndex + 1];
        const endValue = end[channelIndex + 1];
        return Math.round(startValue + (endValue - startValue) * ratio);
      });
    }
  }

  return sourcePalette[sourcePalette.length - 1].slice(1, 4);
}

function rgbCss(rgb, alpha = 1) {
  return `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, ${alpha})`;
}

function windHighlightColor(speedMs, enabled = windColorEnabled) {
  if (!enabled || !Number.isFinite(speedMs)) {
    return "transparent";
  }
  return rgbCss(interpolateWindColor(msToKnots(speedMs), WINDGURU_ADJUSTED_PALETTE), 1);
}

function windHighlightStyle(speedMs, enabled = windColorEnabled) {
  return `background:${windHighlightColor(speedMs, enabled)};`;
}

function formatNoNumber(value, options = {}) {
  if (!Number.isFinite(value)) return "-";
  const { minimumFractionDigits = 1, maximumFractionDigits = 1 } = options;
  return value.toLocaleString("no-NO", {
    minimumFractionDigits,
    maximumFractionDigits,
  });
}

function formatStreamlitDecimal(value) {
  if (!Number.isFinite(value)) return "-";
  return formatNoNumber(value, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
}

function formatStreamlitInteger(value) {
  if (!Number.isFinite(value)) return "-";
  return String(Math.round(value));
}

function unitHtml(unit) {
  return `<span class="forecast-unit">${escapeHtml(unit)}</span>`;
}

function formatDirectionDegrees(deg) {
  if (!Number.isFinite(deg)) return "";
  return `${Math.round(normalizeCompassDeg(deg)) % 360}°`;
}

function normalizeDirectionDisplayMode(mode) {
  if (mode === "degrees" || mode === "compass") return mode;
  return "arrow";
}

function formatDirectionCompass(deg) {
  if (!Number.isFinite(deg)) return "";
  const labels = ["N", "NNØ", "NØ", "ØNØ", "Ø", "ØSØ", "SØ", "SSØ", "S", "SSV", "SV", "VSV", "V", "VNV", "NV", "NNV"];
  const normalized = normalizeCompassDeg(deg);
  return labels[Math.round(normalized / 22.5) % labels.length];
}

function directionIconMeta(kind) {
  if (kind === "swell") {
    return {
      src: "symbols/meldinga-swell-arrow-270.svg",
      baseDeg: 270,
    };
  }
  return {
    src: "symbols/meldinga-wind-arrow-270.svg",
    baseDeg: 270,
  };
}

function directionIconHtml(kind) {
  const { src } = directionIconMeta(kind);
  return `<img class="forecast-arrow-icon forecast-arrow-icon--${escapeHtml(kind)}" src="${src}" alt="" draggable="false">`;
}

function directionTextHtml(text, kind, mode) {
  const emptyClass = text ? "" : " forecast-direction-text--empty";
  return (
    `<span class="forecast-direction-text forecast-direction-text--${escapeHtml(kind)} forecast-direction-text--${escapeHtml(mode)}${emptyClass}">` +
    `${escapeHtml(text)}` +
    `</span>`
  );
}

function degToArrowHtml(deg, kind = "wind", options = {}) {
  const directionMode = normalizeDirectionDisplayMode(options.mode);
  if (!Number.isFinite(deg)) {
    if (directionMode === "degrees" || directionMode === "compass") {
      return directionTextHtml("", kind, directionMode);
    }
    return '<span class="forecast-arrow-empty"></span>';
  }
  if (directionMode === "degrees") {
    return directionTextHtml(formatDirectionDegrees(deg), kind, directionMode);
  }
  if (directionMode === "compass") {
    return directionTextHtml(formatDirectionCompass(deg), kind, directionMode);
  }
  const { baseDeg } = directionIconMeta(kind);
  const rotation = (deg - baseDeg + 360) % 360;
  const degreeText = formatDirectionDegrees(deg);
  const hoverAttrs = SHOW_DIRECTION_DEGREES_ON_HOVER
    ? ` title="${escapeHtml(degreeText)}" aria-label="${escapeHtml(degreeText)}"`
    : "";
  return `<span class="forecast-arrow forecast-arrow--${escapeHtml(kind)}" style="transform:rotate(${rotation.toFixed(0)}deg)"${hoverAttrs}>${directionIconHtml(kind)}</span>`;
}

function swellHeightClass(value) {
  if (!Number.isFinite(value)) return "";
  if (value < 0.8) return "forecast-value-faint";
  return "";
}

function swellPeriodClass(value) {
  if (!Number.isFinite(value)) return "";
  if (value < 6) return "forecast-value-faint";
  return "";
}

function renderEmptySwellSystem() {
  return (
    `<div class="forecast-swell-system forecast-swell-system--empty">` +
    `<span class="forecast-swell-value forecast-swell-value--height"></span>` +
    `<span class="forecast-swell-value forecast-swell-value--period"></span>` +
    `<span class="forecast-swell-dir"></span>` +
    `</div>`
  );
}

function renderSwellSystem(swell, options = {}) {
  const { blankIfMissing = false, directionMode = "arrow" } = options;
  if (!swell) {
    return blankIfMissing ? renderEmptySwellSystem() : renderEmptySwellSystem();
  }

  const heightText = formatStreamlitDecimal(swell.heightM);
  const periodText = formatStreamlitInteger(swell.periodS);

  return (
    `<div class="forecast-swell-system">` +
    `<span class="forecast-swell-value forecast-swell-value--height ${swellHeightClass(swell.heightM)}">` +
    `${escapeHtml(heightText)}<span class="forecast-unit">m</span>` +
    `</span>` +
    `<span class="forecast-swell-value forecast-swell-value--period ${swellPeriodClass(swell.periodS)}">` +
    `${escapeHtml(periodText)}<span class="forecast-unit">s</span>` +
    `</span>` +
    `<span class="forecast-swell-dir">${degToArrowHtml(swell.dirDeg, "swell", { mode: directionMode })}</span>` +
    `</div>`
  );
}

function renderSecondarySwells(swells, options = {}) {
  const { directionMode = "arrow" } = options;
  const secondary = Array.isArray(swells) ? swells.slice(1, 3) : [];
  const first = secondary[0] || null;
  const second = secondary[1] || null;

  return (
    `<div class="forecast-secondary">` +
    `<div class="forecast-secondary-slot">${renderSwellSystem(first, { blankIfMissing: true, directionMode })}</div>` +
    `<div class="forecast-secondary-slot">${renderSwellSystem(second, { blankIfMissing: true, directionMode })}</div>` +
    `</div>`
  );
}

function normalizeMeldingaRow(row) {
  const effectiveWind = row?.effectiveWind || null;
  const yr = row?.yr || null;
  return normalizeForecastRow({
    timeUtc: row?.timeUtc,
    timeLocal: row?.timeLocal,
    swells: Array.isArray(row?.noaa?.swells) ? row.noaa.swells : [],
    windSpeedMs: effectiveWind?.windSpeedMs,
    windGustMs: effectiveWind?.windGustMs,
    windDirDeg: effectiveWind?.windDirDeg,
    precipMm: yr?.precipMm,
    airTempC: yr?.airTempC,
    cloudPct: yr?.cloudPct,
    showGust: Number.isFinite(effectiveWind?.windGustMs),
    scores: row?.scores || null,
  });
}

function normalizeLegacyRow(row, showGust) {
  return normalizeForecastRow({
    ...row,
    showGust: Boolean(showGust || Number.isFinite(row?.windGustMs)),
  });
}

function waveScoreForRow(row) {
  if (Number.isFinite(row?.scores?.waveScore)) {
    return clamp(Math.round(row.scores.waveScore), 0, 3);
  }
  const swells = Array.isArray(row?.swells) ? row.swells : [];
  return swells.reduce((maxCount, swell) => (
    Math.max(maxCount, swellSignalCountForSwell(swell))
  ), 0);
}

function surfColorForRow(row, spotName) {
  if (typeof row?.scores?.surfColor === "string") {
    return row.scores.surfColor;
  }
  return swellSignalColorForRow(row, spotName);
}

function surfScoreFromColorAndWave(color, waveScore) {
  const count = clamp(Math.round(waveScore), 0, 3);
  if (count <= 0) return 0;
  if (color === "green") return 6 + count;
  if (color === "orange") return 3 + count;
  return count;
}

function surfScoreForRow(row, spotName) {
  if (Number.isFinite(row?.scores?.surfScore)) {
    return clamp(Math.round(row.scores.surfScore), 0, 9);
  }
  const waveScore = waveScoreForRow(row);
  if (waveScore <= 0) return 0;
  return surfScoreFromColorAndWave(surfColorForRow(row, spotName), waveScore);
}

function slotSortMs(slot) {
  if (Number.isFinite(slot?.sortMs)) {
    return slot.sortMs;
  }
  if (slot?.sortTimeUtc) {
    return new Date(slot.sortTimeUtc).getTime();
  }
  if (typeof slot?.dateLocal === "string") {
    return new Date(`${slot.dateLocal}T12:00:00`).getTime();
  }
  return Number.POSITIVE_INFINITY;
}

function rowsForSpot(spotName) {
  return forecastRows.get(spotName) || [];
}

function anyRowForDate(dateLocal) {
  for (const spotName of activeSpots) {
    const row = rowsForSpot(spotName).find((entry) => entry.dateLocal === dateLocal);
    if (row) return row;
  }
  return null;
}

function weekdayNameForDateLocal(dateLocal) {
  const sampleRow = anyRowForDate(dateLocal);
  if (sampleRow?.timeUtc) {
    return WEEKDAYS_NO[weekdayIndexInOslo(new Date(sampleRow.timeUtc))];
  }
  const [year, month, day] = dateLocal.split("-").map(Number);
  return WEEKDAYS_NO[new Date(Date.UTC(year, month - 1, day, 12, 0, 0)).getUTCDay()];
}

function dateLabelForSlot(dateLocal, options = {}) {
  const { todayLabel = false } = options;
  const [year, month, day] = dateLocal.split("-").map(Number);
  const monthName = MONTHS_NO[month - 1];
  const weekday = weekdayNameForDateLocal(dateLocal);
  const title = todayLabel ? "I dag" : `${weekday.charAt(0).toUpperCase()}${weekday.slice(1)}`;
  return `${title} ${day}. ${monthName}`;
}

function shortDateLabelForSlot(dateLocal) {
  const [, month, day] = dateLocal.split("-").map(Number);
  return `${day}. ${MONTHS_NO[month - 1]}`;
}

function formatClock(date) {
  const parts = getOsloParts(date);
  return `${pad2(parts.hour)}:${pad2(parts.minute)}`;
}

function formatDayMonth(date) {
  const parts = getOsloParts(date);
  return `${parts.day}. ${MONTHS_NO[parts.month - 1]}`;
}

function formatCompactDateTime(date) {
  const parts = getOsloParts(date);
  return `${pad2(parts.day)}.${pad2(parts.month)}. ${pad2(parts.hour)}:${pad2(parts.minute)}`;
}

function formatUtcHour(date) {
  return pad2(date.getUTCHours());
}

function capitalizeLabel(text) {
  if (!text) return "";
  return `${text.charAt(0).toUpperCase()}${text.slice(1)}`;
}

function hashSpotName() {
  const prefix = "#spot=";
  if (!window.location.hash.startsWith(prefix)) {
    return null;
  }
  const spotName = decodeURIComponent(window.location.hash.slice(prefix.length));
  return activeSpots.includes(spotName) ? spotName : null;
}

function navigateToSpot(spotName) {
  if (!activeSpots.includes(spotName)) return;
  const nextHash = `${prefixForSpotHash()}${encodeURIComponent(spotName)}`;
  shouldResetDetailScroll = true;
  if (window.location.hash === nextHash) {
    applyRoute();
    return;
  }
  window.location.hash = nextHash;
}

function prefixForSpotHash() {
  return "#spot=";
}

function clearSpotRoute() {
  const cleanUrl = `${window.location.pathname}${window.location.search}`;
  window.history.pushState({}, "", cleanUrl);
  applyRoute();
}

function setMenuOpen(isOpen) {
  if (!menuPanelEl || !menuButtonEl) return;
  menuPanelEl.hidden = !isOpen;
  menuButtonEl.setAttribute("aria-expanded", isOpen ? "true" : "false");
}

function setDetailSettingsOpen(isOpen) {
  if (!detailSettingsPanelEl || !detailSettingsButtonEl) return;
  detailSettingsPanelEl.hidden = !isOpen;
  detailSettingsButtonEl.setAttribute("aria-expanded", isOpen ? "true" : "false");
}

function syncWindColorControls() {
  if (windColorToggleEl) {
    windColorToggleEl.checked = windColorEnabled;
  }
  if (detailWindColorToggleEl) {
    detailWindColorToggleEl.checked = windColorEnabled;
  }
}

function setWindColorEnabled(nextValue) {
  windColorEnabled = Boolean(nextValue);
  syncWindColorControls();
  applyRoute();
}

function syncDetailDirectionModeControls() {
  if (detailWindDirectionModeEl) {
    detailWindDirectionModeEl.value = detailWindDirectionMode;
  }
  if (detailWaveDirectionModeEl) {
    detailWaveDirectionModeEl.value = detailWaveDirectionMode;
  }
}

function setDetailWindDirectionMode(nextMode) {
  detailWindDirectionMode = normalizeDirectionDisplayMode(nextMode);
  syncDetailDirectionModeControls();
}

function setDetailWaveDirectionMode(nextMode) {
  detailWaveDirectionMode = normalizeDirectionDisplayMode(nextMode);
  syncDetailDirectionModeControls();
}

function normalizeDetailTab(tab) {
  if (tab === "observations" || tab === "statistics") return tab;
  return "forecast";
}

function setCurrentDetailTab(nextTab) {
  currentDetailTab = normalizeDetailTab(nextTab);
  syncDetailTabButtons();
}

function syncDetailTabButtons() {
  detailTabEls.forEach((tabEl) => {
    const isActive = tabEl.dataset.detailTab === currentDetailTab;
    tabEl.classList.toggle("detail-tab--active", isActive);
    tabEl.setAttribute("aria-pressed", isActive ? "true" : "false");
  });
}

function liveWindSeriesSourceEntries() {
  const sourceMap = LIVE_WIND_DATA?.seriesSources || LIVE_WIND_DATA?.sources || {};
  return Object.values(sourceMap);
}

function liveWindInstantSourceEntries() {
  const sourceMap = LIVE_WIND_DATA?.instantSources || {};
  return Object.values(sourceMap);
}

function sortObservationSources(left, right) {
  const leftDistance = Number.isFinite(left?.distanceKm) ? left.distanceKm : Number.POSITIVE_INFINITY;
  const rightDistance = Number.isFinite(right?.distanceKm) ? right.distanceKm : Number.POSITIVE_INFINITY;
  if (leftDistance !== rightDistance) {
    return leftDistance - rightDistance;
  }
  return String(left?.name || "").localeCompare(String(right?.name || ""), "no");
}

function liveWindSeriesSourcesForSpot(spotName) {
  return liveWindSeriesSourceEntries()
    .filter((source) => source?.linkedSpot === spotName)
    .sort(sortObservationSources);
}

function liveWindInstantSourcesForSpot(spotName) {
  return liveWindInstantSourceEntries()
    .filter((source) => source?.linkedSpot === spotName)
    .sort(sortObservationSources);
}

function observationResolutionLabel(resolution) {
  switch (resolution) {
    case "PT1M":
      return "1 min";
    case "PT10M":
      return "10 min";
    case "PT30M":
      return "30 min";
    case "PT1H":
      return "time";
    case "PT6H":
      return "6 t";
    default:
      return resolution ? resolution.replace(/^PT/, "") : "serie";
  }
}

function observationProviderLabel(source, fallback = "observasjon") {
  if (source?.provider) return source.provider;
  return fallback;
}

function detailLiveDataGeneratedAtDate() {
  const raw = LIVE_WIND_DATA?.generatedAtUtc;
  if (!raw) return null;
  const candidate = new Date(raw);
  return Number.isFinite(candidate.getTime()) ? candidate : null;
}

function observationRowsForDisplay(source) {
  const rows = Array.isArray(source?.rows) ? source.rows : [];
  if (!rows.length) return [];
  const latestDateLocal = rows[0]?.timeUtc ? dateLocalFromUtc(rows[0].timeUtc) : null;
  if (!latestDateLocal) {
    return rows.slice(0, 18);
  }
  const sameDayRows = rows.filter((row) => row?.timeUtc && dateLocalFromUtc(row.timeUtc) === latestDateLocal);
  return (sameDayRows.length ? sameDayRows : rows).slice(0, 18);
}

function observationMeasuredLabel(timeUtc) {
  if (!timeUtc) return "målt ukjent tid";
  return `målt ${timeLocalFromUtc(timeUtc)}`;
}

function observationUpdatedLabel() {
  const generatedAt = detailLiveDataGeneratedAtDate();
  if (!generatedAt) return "";
  return `Sist hentet ${formatClock(generatedAt)}`;
}

function normalizeObservationName(value) {
  return String(value || "")
    .toLocaleLowerCase("no")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function detailDayShortTitleForDate(dateLocal) {
  const todayKey = dateLocalFromUtc(new Date().toISOString());
  if (dateLocal === todayKey) {
    return "I dag";
  }
  return capitalizeLabel(weekdayNameForDateLocal(dateLocal));
}

function detailStickyRowGapPx() {
  if (!detailStickyEl) return 0;
  const styles = window.getComputedStyle(detailStickyEl);
  return Number.parseFloat(styles.rowGap || styles.gap) || 0;
}

function syncDetailStickyLayoutMetrics() {
  if (!detailStickyEl) return;
  const stickyTopValue = `${Math.max(0, Math.ceil(detailStickyEl.offsetHeight || 0))}px`;
  detailViewEl?.style.setProperty("--detail-day-sticky-top", stickyTopValue);
  detailContentEl?.style.setProperty("--detail-day-sticky-top", stickyTopValue);
  detailStickyEl.dataset.hasWindTarget = detailWindTargetControlEl && !detailWindTargetControlEl.hidden ? "true" : "false";
}

function setActiveStickyDaySection(activeSection) {
  if (!detailContentEl) return;
  [...detailContentEl.querySelectorAll(".detail-day[data-day-toggle]")].forEach((section) => {
    if (section === activeSection) {
      section.dataset.stickyActive = "true";
    } else {
      delete section.dataset.stickyActive;
    }
  });
  if (detailStickyEl) {
    detailStickyEl.dataset.dayIndicatorActive = activeSection ? "true" : "false";
  }
}

function activeExpandedDetailDaySection() {
  if (!detailContentEl || !detailStickyEl || !currentSpotName) return null;
  const expandedSections = [...detailContentEl.querySelectorAll(".detail-day--expanded[data-day-toggle]")];
  if (!expandedSections.length) return null;

  const controlsRect = detailControlsEl?.getBoundingClientRect() || null;
  const stickyRect = detailStickyEl.getBoundingClientRect();
  const thresholdTop = MOBILE_LAYOUT_QUERY.matches
    ? (controlsRect?.top || stickyRect.bottom)
    : stickyRect.bottom;
  let activeSection = null;

  expandedSections.forEach((section) => {
    const titleEl = section.querySelector(".detail-day-title");
    if (!titleEl) return;
    const titleRect = titleEl.getBoundingClientRect();
    const sectionRect = section.getBoundingClientRect();
    if (titleRect.top <= (thresholdTop + 1) && sectionRect.bottom > (thresholdTop + titleRect.height + detailStickyRowGapPx())) {
      activeSection = section;
    }
  });

  return activeSection;
}

function syncDetailDayIndicator() {
  if (!detailDayIndicatorEl) return;
  if (!currentSpotName || detailViewEl.hidden || currentDetailTab !== "forecast") {
    detailDayIndicatorEl.hidden = true;
    detailDayIndicatorEl.textContent = "";
    setActiveStickyDaySection(null);
    return;
  }

  const activeSection = activeExpandedDetailDaySection();
  if (!activeSection) {
    detailDayIndicatorEl.hidden = true;
    detailDayIndicatorEl.textContent = "";
    setActiveStickyDaySection(null);
    return;
  }

  const fullLabel = activeSection.dataset.dayLabelFull || "";
  const shortLabel = activeSection.dataset.dayLabelShort || fullLabel;
  const shouldUseShortLabel = MOBILE_LAYOUT_QUERY.matches && detailWindTargetControlEl && !detailWindTargetControlEl.hidden;
  detailDayIndicatorEl.textContent = shouldUseShortLabel ? shortLabel : fullLabel;
  detailDayIndicatorEl.hidden = !detailDayIndicatorEl.textContent;
  setActiveStickyDaySection(detailDayIndicatorEl.hidden ? null : activeSection);
}

function scheduleDetailStickyStateSync() {
  if (detailStickyStateSyncFrame) {
    window.cancelAnimationFrame(detailStickyStateSyncFrame);
  }
  detailStickyStateSyncFrame = window.requestAnimationFrame(() => {
    detailStickyStateSyncFrame = 0;
    syncDetailStickyLayoutMetrics();
    syncDetailDayIndicator();
  });
}

function latestYrUpdatedAtDate() {
  let latest = null;
  activeSpots.forEach((spotName) => {
    const raw = spotDataEntry(spotName)?.yrUpdatedAtUtc;
    if (!raw) return;
    const candidate = new Date(raw);
    if (!Number.isFinite(candidate.getTime())) return;
    if (!latest || candidate > latest) {
      latest = candidate;
    }
  });
  return latest;
}

function ww3RunDate() {
  const raw = FORECAST_DATA?.noaa?.runUtc || FORECAST_DATA?.noaaRunUtc || null;
  if (!raw) return null;
  const candidate = new Date(raw);
  return Number.isFinite(candidate.getTime()) ? candidate : null;
}

function overviewModelRunText() {
  const yrUpdatedAt = latestYrUpdatedAtDate();
  const waveRunAt = ww3RunDate();
  const waveRunId = FORECAST_DATA?.noaa?.runId || FORECAST_DATA?.noaaRunId || null;
  const isMobile = MOBILE_LAYOUT_QUERY.matches;
  const parts = [];

  if (yrUpdatedAt) {
    parts.push(
      isMobile
        ? `MET/Yr oppdatert ${formatClock(yrUpdatedAt)}`
        : `MET/Yr Locationforecast oppdatert ${formatClock(yrUpdatedAt)}`
    );
  }
  if (waveRunAt) {
    parts.push(
      isMobile
        ? `NOAA GFSwave (WW3) modelrun ${formatUtcHour(waveRunAt)}UTC`
        : `NOAA GFSwave (WW3) modelrun ${formatUtcHour(waveRunAt)}UTC`
    );
  } else if (waveRunId) {
    const runMatch = waveRunId.match(/_t(\d{2})z$/i);
    const runLabel = runMatch ? runMatch[1] : waveRunId;
    parts.push(
      isMobile
        ? `NOAA GFSwave (WW3) modelrun ${runLabel}UTC`
        : `NOAA GFSwave (WW3) modelrun ${runLabel}UTC`
    );
  }

  return parts.join(", ");
}

function syncOverviewTimePanelReserve() {
  if (!pageShellEl || !timePanelEl || timePanelEl.hidden) return;

  const panelRect = timePanelEl.getBoundingClientRect();
  if (!panelRect.height) return;

  const panelBottomPx = Number.parseFloat(window.getComputedStyle(timePanelEl).bottom) || 0;
  const reservePx = panelRect.height + panelBottomPx;
  pageShellEl.style.setProperty("--time-panel-reserve", `${Math.ceil(reservePx)}px`);
}

function scheduleOverviewTimePanelReserveSync() {
  if (overviewReserveSyncFrame) {
    window.cancelAnimationFrame(overviewReserveSyncFrame);
  }
  overviewReserveSyncFrame = window.requestAnimationFrame(() => {
    overviewReserveSyncFrame = 0;
    syncOverviewTimePanelReserve();
  });
}

function expandedDatesForSpot(spotName) {
  if (!detailExpandedDates.has(spotName)) {
    detailExpandedDates.set(spotName, new Set());
  }
  return detailExpandedDates.get(spotName);
}

function isDetailDayExpanded(spotName, dateLocal) {
  return expandedDatesForSpot(spotName).has(dateLocal);
}

function toggleDetailDay(spotName, dateLocal) {
  const expanded = expandedDatesForSpot(spotName);
  if (expanded.has(dateLocal)) {
    expanded.delete(dateLocal);
  } else {
    expanded.add(dateLocal);
  }
}

function timeTextForMinutes(totalMinutes) {
  const hour = Math.floor(totalMinutes / 60);
  const minute = totalMinutes % 60;
  return `${pad2(hour)}:${pad2(minute)}`;
}

function rowForExactLocalTime(spotName, dateLocal, targetMinutes) {
  return rowsForSpot(spotName).find((row) => (
    row.dateLocal === dateLocal && parseTimeLocalMinutes(row.timeLocal) === targetMinutes
  )) || null;
}

function primarySwellStrengthForRow(row) {
  const primarySwell = Array.isArray(row?.swells) ? row.swells[0] : null;
  if (!Number.isFinite(primarySwell?.heightM) || !Number.isFinite(primarySwell?.periodS)) {
    return Number.NEGATIVE_INFINITY;
  }
  return primarySwell.heightM * primarySwell.periodS;
}

function bestRowForDay(spotName, dateLocal) {
  let bestRow = null;
  let bestSurfScore = -1;
  let bestPrimarySwellStrength = Number.NEGATIVE_INFINITY;
  let bestGust = Number.POSITIVE_INFINITY;

  rowsForSpot(spotName).forEach((row) => {
    if (row.dateLocal !== dateLocal) return;
    const surfScore = surfScoreForRow(row, spotName);
    const primarySwellStrength = primarySwellStrengthForRow(row);
    const gustValue = Number.isFinite(effectiveForecastGust(row))
      ? effectiveForecastGust(row)
      : Number.POSITIVE_INFINITY;

    if (
      surfScore > bestSurfScore
      || (surfScore === bestSurfScore && primarySwellStrength > bestPrimarySwellStrength)
      || (
        surfScore === bestSurfScore
        && primarySwellStrength === bestPrimarySwellStrength
        && gustValue < bestGust
      )
    ) {
      bestRow = row;
      bestSurfScore = surfScore;
      bestPrimarySwellStrength = primarySwellStrength;
      bestGust = gustValue;
    }
  });

  return bestRow;
}

function buildSharedTimeSlot(dateLocal, targetMinutes, options = {}) {
  const { todayLabel = false } = options;
  const [year, month, day] = dateLocal.split("-").map(Number);

  return {
    key: `shared:${dateLocal}:${targetMinutes}`,
    kind: "shared",
    dateLocal,
    targetMinutes,
    displayText: `${dateLabelForSlot(dateLocal, { todayLabel })} ${timeTextForMinutes(targetMinutes)}`,
    shortText: shortDateLabelForSlot(dateLocal),
    sortMs: Date.UTC(year, month - 1, day, 0, targetMinutes, 0),
  };
}

function buildDailyBestSlot(dateLocal) {
  const rowsBySpot = {};
  let sampleRow = null;

  activeSpots.forEach((spotName) => {
    const bestRow = bestRowForDay(spotName, dateLocal);
    if (bestRow) {
      rowsBySpot[spotName] = bestRow;
      if (!sampleRow || new Date(bestRow.timeUtc).getTime() < new Date(sampleRow.timeUtc).getTime()) {
        sampleRow = bestRow;
      }
    }
  });

  if (!sampleRow) return null;

  return {
    key: `daily:${dateLocal}`,
    kind: "daily-best",
    dateLocal,
    rowsBySpot,
    displayText: `${dateLabelForSlot(dateLocal)} (beste time)`,
    shortText: shortDateLabelForSlot(dateLocal),
    sortTimeUtc: sampleRow.timeUtc,
  };
}

function buildSliderSlots() {
  const dateKeys = new Set();
  activeSpots.forEach((spotName) => {
    rowsForSpot(spotName).forEach((row) => {
      if (row?.dateLocal) {
        dateKeys.add(row.dateLocal);
      }
    });
  });

  const sortedDates = [...dateKeys].sort();
  if (!sortedDates.length) return [];

  const now = new Date();
  const todayKey = dateLocalFromUtc(now.toISOString());
  const tomorrowDate = new Date(now.getTime() + (24 * 60 * 60 * 1000));
  const tomorrowKey = dateLocalFromUtc(tomorrowDate.toISOString());
  const slots = [];

  if (sortedDates.includes(todayKey)) {
    for (let hour = 6; hour <= 18; hour += 1) {
      const slot = buildSharedTimeSlot(todayKey, hour * 60, { todayLabel: true });
      if (slot) slots.push(slot);
    }
  }

  if (sortedDates.includes(tomorrowKey)) {
    [6, 9, 12, 15, 18].forEach((hour) => {
      const slot = buildSharedTimeSlot(tomorrowKey, hour * 60);
      if (slot) slots.push(slot);
    });
  }

  sortedDates
    .filter((dateLocal) => dateLocal > tomorrowKey)
    .forEach((dateLocal) => {
      const slot = buildDailyBestSlot(dateLocal);
      if (slot) slots.push(slot);
    });

  if (!slots.length) {
    activeSpots.forEach((spotName) => {
      rowsForSpot(spotName).forEach((row) => {
        slots.push({
          key: `fallback:${row.timeUtc}`,
          kind: "shared",
          dateLocal: row.dateLocal,
          targetMinutes: parseTimeLocalMinutes(row.timeLocal),
          displayText: formatSelectedTime(new Date(row.timeUtc)),
          shortText: formatShortTime(new Date(row.timeUtc)),
          sortTimeUtc: row.timeUtc,
        });
      });
    });
  }

  return slots
    .sort((left, right) => slotSortMs(left) - slotSortMs(right))
    .filter((slot, index, allSlots) => index === 0 || slot.key !== allSlots[index - 1].key);
}

function resolveRowForSlot(spotName, slot) {
  if (!slot) return null;
  if (slot.kind === "daily-best") {
    return slot.rowsBySpot?.[spotName] || null;
  }
  if (slot.kind === "shared" && Number.isFinite(slot.targetMinutes)) {
    return rowForExactLocalTime(spotName, slot.dateLocal, slot.targetMinutes);
  }
  return null;
}

function spotDataEntry(spotName) {
  return FORECAST_DATA.spots?.[spotName] || null;
}

function weatherOptionsForSpot(spotName) {
  const options = spotDataEntry(spotName)?.weatherOptions;
  return Array.isArray(options) ? options : [];
}

function defaultWeatherOptionForSpot(spotName) {
  const explicitDefault = spotDataEntry(spotName)?.defaultWeatherOption;
  if (typeof explicitDefault === "string" && explicitDefault) {
    return explicitDefault;
  }
  return weatherOptionsForSpot(spotName)[0]?.name || null;
}

function selectedWeatherOptionForSpot(spotName) {
  const options = weatherOptionsForSpot(spotName);
  if (!options.length) return null;

  const validNames = new Set(options.map((option) => option.name));
  const selected = selectedWeatherOptionBySpot.get(spotName);
  if (selected && validNames.has(selected)) {
    return selected;
  }

  const fallback = defaultWeatherOptionForSpot(spotName) || options[0].name;
  selectedWeatherOptionBySpot.set(spotName, fallback);
  return fallback;
}

function setSelectedWeatherOptionForSpot(spotName, optionName) {
  const options = weatherOptionsForSpot(spotName);
  const validNames = new Set(options.map((option) => option.name));
  if (!optionName || !validNames.has(optionName)) {
    selectedWeatherOptionBySpot.delete(spotName);
    return;
  }
  selectedWeatherOptionBySpot.set(spotName, optionName);
}

function weatherVariantEntryForSpot(spotName, optionName = selectedWeatherOptionForSpot(spotName)) {
  if (!optionName) return null;
  return spotDataEntry(spotName)?.weatherVariants?.[optionName] || null;
}

function weatherVariantRowsForSpot(spotName, optionName = selectedWeatherOptionForSpot(spotName)) {
  const variantEntry = weatherVariantEntryForSpot(spotName, optionName);
  if (!variantEntry) {
    return rowsForSpot(spotName);
  }

  if (!Array.isArray(variantEntry.normalizedRows)) {
    variantEntry.normalizedRows = Array.isArray(variantEntry.rows)
      ? variantEntry.rows.map((row) => normalizeMeldingaRow(row))
      : [];
  }

  return variantEntry.normalizedRows;
}

function weatherVariantRowForExactLocalTime(spotName, dateLocal, targetMinutes) {
  return weatherVariantRowsForSpot(spotName).find((row) => (
    row.dateLocal === dateLocal && parseTimeLocalMinutes(row.timeLocal) === targetMinutes
  )) || null;
}

function tideSpotEntry(spotName) {
  const entry = TIDE_DATA.spots?.[spotName] || null;
  if (!entry) return null;

  if (!entry.parsedRowsLocal) {
    entry.parsedRowsLocal = (entry.rows || []).map((row) => ({
      timeUtc: row.timeUtc,
      timeMs: new Date(row.timeUtc).getTime(),
      dateLocal: dateLocalFromUtc(row.timeUtc),
      timeLocal: timeLocalFromUtc(row.timeUtc),
      minutesLocal: parseTimeLocalMinutes(timeLocalFromUtc(row.timeUtc)),
      astronomical: Number.isFinite(row.astronomical) ? row.astronomical : null,
    }));
  }

  if (!entry.parsedDkssRowsLocal) {
    entry.parsedDkssRowsLocal = (((entry.dkss || {}).rows) || []).map((row) => ({
      timeUtc: row.timeUtc,
      timeMs: new Date(row.timeUtc).getTime(),
      dateLocal: dateLocalFromUtc(row.timeUtc),
      timeLocal: timeLocalFromUtc(row.timeUtc),
      minutesLocal: parseTimeLocalMinutes(timeLocalFromUtc(row.timeUtc)),
      deviation: Number.isFinite(row.deviation) ? row.deviation : null,
      total: Number.isFinite(row.total) ? row.total : null,
    }));
  }

  if (!entry.parsedEventsLocal) {
    entry.parsedEventsLocal = (entry.events || []).map((event) => ({
      timeUtc: event.timeUtc,
      timeMs: new Date(event.timeUtc).getTime(),
      dateLocal: dateLocalFromUtc(event.timeUtc),
      timeLocal: timeLocalFromUtc(event.timeUtc),
      minutesLocal: parseTimeLocalMinutes(timeLocalFromUtc(event.timeUtc)),
      kind: event.kind,
      astronomical: Number.isFinite(event.astronomical) ? event.astronomical : null,
    }));
  }

  return entry;
}

function lightWindowForDate(spotName, dateLocal) {
  const variantEntry = weatherVariantEntryForSpot(spotName);
  const lightWindows = Array.isArray(variantEntry?.lightWindows)
    ? variantEntry.lightWindows
    : spotDataEntry(spotName)?.lightWindows;
  return Array.isArray(lightWindows)
    ? lightWindows.find((entry) => entry.dateLocal === dateLocal) || null
    : null;
}

function detailDayTitleForDate(dateLocal) {
  const todayKey = dateLocalFromUtc(new Date().toISOString());
  const shortDate = shortDateLabelForSlot(dateLocal);
  if (dateLocal === todayKey) {
    return `I dag, ${shortDate}`;
  }
  return `${capitalizeLabel(weekdayNameForDateLocal(dateLocal))} ${shortDate}`;
}

function uniqueDateLocalsForSpot(spotName) {
  const todayKey = dateLocalFromUtc(new Date().toISOString());
  return [...new Set(rowsForSpot(spotName).map((row) => row?.dateLocal).filter(Boolean))]
    .sort()
    .filter((dateLocal) => dateLocal >= todayKey);
}

function roundToNearestHourMinutes(totalMinutes) {
  return Math.round(totalMinutes / 60) * 60;
}

function roundUpToWholeHourMinutes(totalMinutes) {
  return Math.ceil(totalMinutes / 60) * 60;
}

function detailCollapsedMinutes() {
  return [6 * 60, 12 * 60, 18 * 60];
}

function detailExpandedMinutesForDate(spotName, dateLocal) {
  const lightWindow = lightWindowForDate(spotName, dateLocal);
  const civilStart = parseTimeLocalMinutes(lightWindow?.model?.civilStartLocal);
  const civilEnd = parseTimeLocalMinutes(lightWindow?.model?.civilEndLocal);

  let startMinutes = 6 * 60;
  let endMinutes = 18 * 60;

  if (Number.isFinite(civilStart) && Number.isFinite(civilEnd)) {
    startMinutes = clamp(roundToNearestHourMinutes(civilStart) - (2 * 60), 0, 23 * 60);
    endMinutes = clamp(roundUpToWholeHourMinutes(civilEnd), 0, 23 * 60);
  }

  if (endMinutes < startMinutes) {
    return detailCollapsedMinutes();
  }

  const result = [];
  for (let minutes = startMinutes; minutes <= endMinutes; minutes += 60) {
    result.push(minutes);
  }
  return result;
}

function detailTimeLabel(minutes) {
  return pad2(Math.floor(minutes / 60));
}

function nearestDkssRowForTime(spotName, timeUtc) {
  const rows = tideSpotEntry(spotName)?.dkss?.rows;
  if (!Array.isArray(rows) || !rows.length || !timeUtc) return null;
  const targetMs = new Date(timeUtc).getTime();
  let bestRow = null;
  let bestDiff = Number.POSITIVE_INFINITY;

  rows.forEach((row) => {
    const rowMs = new Date(row.timeUtc).getTime();
    const diff = Math.abs(rowMs - targetMs);
    if (diff < bestDiff) {
      bestRow = row;
      bestDiff = diff;
    }
  });

  return bestDiff <= (35 * 60 * 1000) ? bestRow : null;
}

function tideKindLabel(kind) {
  if (kind === "high") return "Flo";
  if (kind === "low") return "Fjære";
  return "-";
}

function formatTideMeters(value) {
  if (!Number.isFinite(value)) return "-";
  return formatNoNumber(value, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
}

function formatMinutesClock(totalMinutes) {
  if (!Number.isFinite(totalMinutes)) return "--:--";
  const normalized = ((Math.round(totalMinutes) % (24 * 60)) + (24 * 60)) % (24 * 60);
  return `${pad2(Math.floor(normalized / 60))}:${pad2(normalized % 60)}`;
}

function tideRowsForDateLocal(spotName, dateLocal) {
  const entry = tideSpotEntry(spotName);
  if (!entry) {
    return { entry: null, astronomicalRows: [], secondaryRows: [], events: [] };
  }

  return {
    entry,
    astronomicalRows: entry.parsedRowsLocal.filter((row) => row.dateLocal === dateLocal),
    secondaryRows: entry.parsedDkssRowsLocal.filter((row) => row.dateLocal === dateLocal),
    events: entry.parsedEventsLocal.filter((event) => event.dateLocal === dateLocal),
  };
}

function borrowNeighborRowsForDate(rows, dateLocal, borrowLimitMinutes = 60) {
  const sortedRows = (rows || [])
    .filter((row) => Number.isFinite(row.timeMs))
    .slice()
    .sort((left, right) => left.timeMs - right.timeMs);
  const dayRows = sortedRows
    .filter((row) => row.dateLocal === dateLocal)
    .map((row) => ({ ...row }));
  if (!dayRows.length) {
    return { dayRows: [], plotRows: [] };
  }

  const plotRows = dayRows.map((row) => ({ ...row }));
  const firstDayRow = dayRows[0];
  const lastDayRow = dayRows[dayRows.length - 1];
  const previousRow = [...sortedRows].reverse().find((row) => row.timeMs < firstDayRow.timeMs);
  const nextRow = sortedRows.find((row) => row.timeMs > lastDayRow.timeMs);

  if (previousRow) {
    const diffMinutes = (firstDayRow.timeMs - previousRow.timeMs) / 60000;
    if (diffMinutes > 0 && diffMinutes <= borrowLimitMinutes) {
      plotRows.unshift({
        ...previousRow,
        minutesLocal: firstDayRow.minutesLocal - diffMinutes,
      });
    }
  }

  if (nextRow) {
    const diffMinutes = (nextRow.timeMs - lastDayRow.timeMs) / 60000;
    if (diffMinutes > 0 && diffMinutes <= borrowLimitMinutes) {
      plotRows.push({
        ...nextRow,
        minutesLocal: lastDayRow.minutesLocal + diffMinutes,
      });
    }
  }

  return { dayRows, plotRows };
}

function tideGraphValueRange(seriesDefs) {
  const values = seriesDefs
    .flatMap((seriesDef) => (
      (seriesDef.rows || [])
        .map((row) => row[seriesDef.valueKey])
        .filter((value) => Number.isFinite(value))
    ));
  if (!values.length) {
    return { min: -0.5, max: 0.5 };
  }
  const rawMin = Math.min(...values);
  const rawMax = Math.max(...values);
  if (rawMin === rawMax) {
    return { min: rawMin - 0.24, max: rawMax + 0.24 };
  }
  const padding = Math.max(0.28, (rawMax - rawMin) * 0.9);
  return {
    min: rawMin - padding,
    max: rawMax + padding,
  };
}

function fixedTideGraphRangeForSpot(spotName) {
  if (spotName === "Persfjord") return { min: 0, max: 4.0 };
  if (spotName === "Unstad Beach") return { min: 0, max: 3.4 };
  if (spotName === "Hustadvika Gjestegard") return { min: 0, max: 2.8 };
  if (spotName === "Alnes Lighthouse (Godoy)") return { min: 0, max: 2.5 };
  if (spotName === "Ervika") return { min: 0, max: 2.4 };
  if (spotName === "Pigsty/Piggy") return { min: -0.1, max: 1.5 };
  if (spotName === "Lista") return { min: -0.1, max: 1.2 };
  if (spotName === "Mandal / Sjosanden") return { min: -0.2, max: 1.2 };
  if (spotName === "Saltstein") return { min: -0.2, max: 1.6 };
  return null;
}

function roundOutwardToStep(value, step, direction) {
  if (!Number.isFinite(value)) return value;
  if (direction === "up") {
    return Math.ceil(value / step) * step;
  }
  return Math.floor(value / step) * step;
}

function resolvedTideGraphRangeForSpot(spotName, seriesDefs, roundingStep = 0.05) {
  const base = fixedTideGraphRangeForSpot(spotName);
  if (!base) {
    return tideGraphValueRange(seriesDefs);
  }
  const values = seriesDefs
    .flatMap((seriesDef) => (
      (seriesDef.rows || [])
        .map((row) => row[seriesDef.valueKey])
        .filter((value) => Number.isFinite(value))
    ));
  if (!values.length) {
    return { min: base.min, max: base.max };
  }
  const actualMin = Math.min(...values);
  const actualMax = Math.max(...values);
  return {
    min: actualMin < base.min ? roundOutwardToStep(actualMin, roundingStep, "down") : base.min,
    max: actualMax > base.max ? roundOutwardToStep(actualMax, roundingStep, "up") : base.max,
  };
}

function buildGraphDarkSegments(lightWindow) {
  const model = lightWindow?.model;
  const civilStart = parseTimeLocalMinutes(model?.civilStartLocal);
  const civilEnd = parseTimeLocalMinutes(model?.civilEndLocal);

  if (![civilStart, civilEnd].every(Number.isFinite)) {
    return [];
  }

  return [
    { startMinutes: 0, endMinutes: clamp(civilStart, 0, 24 * 60) },
    { startMinutes: clamp(civilEnd, 0, 24 * 60), endMinutes: 24 * 60 },
  ].filter((segment) => segment.endMinutes > segment.startMinutes);
}

function buildPointSegments(rows, valueKey, xFor, yFor, maxGapMinutes = 90) {
  const segments = [];
  let currentSegment = [];

  rows.forEach((row) => {
    const value = row[valueKey];
    if (!Number.isFinite(value) || !Number.isFinite(row.minutesLocal)) {
      if (currentSegment.length) {
        segments.push(currentSegment);
        currentSegment = [];
      }
      return;
    }
    const point = {
      x: xFor(row.minutesLocal),
      y: yFor(value),
      minutesLocal: row.minutesLocal,
    };
    const previous = currentSegment[currentSegment.length - 1];
    if (previous && Math.abs(point.minutesLocal - previous.minutesLocal) > maxGapMinutes) {
      segments.push(currentSegment);
      currentSegment = [];
    }
    currentSegment.push(point);
  });

  if (currentSegment.length) {
    segments.push(currentSegment);
  }
  return segments;
}

function smoothPathFromPoints(points) {
  if (!points.length) return "";
  if (points.length <= 2) {
    return points
      .map((point, index) => `${index === 0 ? "M" : "L"}${point.x.toFixed(1)},${point.y.toFixed(1)}`)
      .join(" ");
  }

  let path = `M${points[0].x.toFixed(1)},${points[0].y.toFixed(1)}`;
  for (let index = 0; index < points.length - 1; index += 1) {
    const p0 = points[index - 1] || points[index];
    const p1 = points[index];
    const p2 = points[index + 1];
    const p3 = points[index + 2] || p2;
    const cp1x = p1.x + (p2.x - p0.x) / 6;
    const cp1y = p1.y + (p2.y - p0.y) / 6;
    const cp2x = p2.x - (p3.x - p1.x) / 6;
    const cp2y = p2.y - (p3.y - p1.y) / 6;
    path += ` C${cp1x.toFixed(1)},${cp1y.toFixed(1)} ${cp2x.toFixed(1)},${cp2y.toFixed(1)} ${p2.x.toFixed(1)},${p2.y.toFixed(1)}`;
  }
  return path;
}

function buildSmoothPath(rows, valueKey, xFor, yFor, maxGapMinutes = 90) {
  return buildPointSegments(rows, valueKey, xFor, yFor, maxGapMinutes)
    .map((points) => smoothPathFromPoints(points))
    .join(" ");
}

function smoothSeriesRows(rows, valueKey, radius = 4) {
  const finiteRows = (rows || []).filter((row) => Number.isFinite(row[valueKey]) && Number.isFinite(row.minutesLocal));
  if (!finiteRows.length) return [];

  return finiteRows.map((row, index) => {
    let totalWeight = 0;
    let weightedSum = 0;
    for (let offset = -radius; offset <= radius; offset += 1) {
      const neighbor = finiteRows[index + offset];
      if (!neighbor) continue;
      const weight = radius + 1 - Math.abs(offset);
      totalWeight += weight;
      weightedSum += neighbor[valueKey] * weight;
    }
    return {
      ...row,
      [valueKey]: totalWeight ? (weightedSum / totalWeight) : row[valueKey],
    };
  });
}

function buildAreaPath(rows, valueKey, xFor, yFor, baselineY, maxGapMinutes = 90) {
  return buildPointSegments(rows, valueKey, xFor, yFor, maxGapMinutes)
    .map((points) => {
      if (!points.length) return "";
      const linePath = smoothPathFromPoints(points);
      return `${linePath} L${points[points.length - 1].x.toFixed(1)},${baselineY.toFixed(1)} L${points[0].x.toFixed(1)},${baselineY.toFixed(1)} Z`;
    })
    .join(" ");
}

function interpolateSeriesAtMinutes(rows, valueKey, targetMinutes, maxGapMinutes = 120) {
  const finiteRows = (rows || []).filter((row) => Number.isFinite(row[valueKey]) && Number.isFinite(row.minutesLocal));
  if (!finiteRows.length || !Number.isFinite(targetMinutes)) return null;

  let previous = null;
  let next = null;
  for (const row of finiteRows) {
    if (row.minutesLocal <= targetMinutes) {
      previous = row;
    }
    if (row.minutesLocal >= targetMinutes) {
      next = row;
      break;
    }
  }

  if (previous && next) {
    const span = next.minutesLocal - previous.minutesLocal;
    if (span === 0) return previous[valueKey];
    if (span <= maxGapMinutes) {
      const ratio = (targetMinutes - previous.minutesLocal) / span;
      return previous[valueKey] + ((next[valueKey] - previous[valueKey]) * ratio);
    }
  }

  const candidates = [previous, next]
    .filter(Boolean)
    .map((row) => ({ row, delta: Math.abs(row.minutesLocal - targetMinutes) }))
    .sort((left, right) => left.delta - right.delta);
  if (!candidates.length || candidates[0].delta > maxGapMinutes) {
    return null;
  }
  return candidates[0].row[valueKey];
}

function tideEventValueSvg(astronomicalValue, secondaryValue) {
  const astronomicalText = formatTideMeters(astronomicalValue);
  if (Number.isFinite(secondaryValue)) {
    return (
      `<tspan fill="#071629">${escapeHtml(astronomicalText)}</tspan>` +
      `<tspan fill="${DETAIL_TIDE_GRAPH.secondaryColor}"> (${escapeHtml(formatTideMeters(secondaryValue))})</tspan>` +
      `<tspan fill="#071629"> m</tspan>`
    );
  }
  return (
    `<tspan fill="#071629">${escapeHtml(astronomicalText)}</tspan>` +
    `<tspan fill="#071629"> m</tspan>`
  );
}

function tideEventValueInlineHtml(astronomicalValue, secondaryValue) {
  const astronomicalText = formatTideMeters(astronomicalValue);
  if (Number.isFinite(secondaryValue)) {
    return (
      `<span class="detail-tide-mobile-value-main">${escapeHtml(astronomicalText)}</span>` +
      `<span class="detail-tide-mobile-value-adjusted" style="color:${DETAIL_TIDE_GRAPH.secondaryColor}"> (${escapeHtml(formatTideMeters(secondaryValue))})</span>` +
      `<span class="detail-tide-mobile-unit"> m</span>`
    );
  }
  return (
    `<span class="detail-tide-mobile-value-main">${escapeHtml(astronomicalText)}</span>` +
    `<span class="detail-tide-mobile-unit"> m</span>`
  );
}

function tideEventClockLabel(event) {
  if (typeof event?.timeLocal === "string" && /^\d{2}:\d{2}$/.test(event.timeLocal)) {
    return event.timeLocal;
  }
  return formatMinutesClock(event?.minutesLocal);
}

function tideLabelPositions(eventKind, anchorY, plotTop, plotBottom, curveTop, curveBottom) {
  const topMin = plotTop + DETAIL_TIDE_LABEL_LAYOUT.topLabelMin;
  const topMax = curveTop - DETAIL_TIDE_LABEL_LAYOUT.highGap;
  const bottomMin = curveBottom + DETAIL_TIDE_LABEL_LAYOUT.lowGap;
  const bottomMax = plotBottom - DETAIL_TIDE_LABEL_LAYOUT.bottomLabelMax;

  if (eventKind === "high") {
    const valueY = clamp(
      anchorY - DETAIL_TIDE_LABEL_LAYOUT.highGap,
      topMin + DETAIL_TIDE_LABEL_LAYOUT.timeToValueGap,
      topMax
    );
    return {
      timeY: valueY - DETAIL_TIDE_LABEL_LAYOUT.timeToValueGap,
      valueY,
    };
  }

  const timeY = clamp(
    anchorY + DETAIL_TIDE_LABEL_LAYOUT.lowGap,
    bottomMin,
    bottomMax - DETAIL_TIDE_LABEL_LAYOUT.timeToValueGap
  );
  return {
    timeY,
    valueY: timeY + DETAIL_TIDE_LABEL_LAYOUT.timeToValueGap,
  };
}

function renderMobileTideEventRows(events, secondaryRows) {
  const grouped = {
    high: events
      .filter((event) => Number.isFinite(event.minutesLocal) && Number.isFinite(event.astronomical) && event.kind === "high")
      .sort((left, right) => left.minutesLocal - right.minutesLocal),
    low: events
      .filter((event) => Number.isFinite(event.minutesLocal) && Number.isFinite(event.astronomical) && event.kind === "low")
      .sort((left, right) => left.minutesLocal - right.minutesLocal),
  };
  const maxCount = Math.max(grouped.high.length, grouped.low.length);
  if (!maxCount) return "";

  const rows = ["high", "low"]
    .filter((kind) => grouped[kind].length)
    .map((kind) => {
      const cells = [];
      for (let index = 0; index < maxCount; index += 1) {
        const event = grouped[kind][index];
        if (!event) {
          cells.push('<td class="detail-tide-mobile-time"></td>');
          cells.push('<td class="detail-tide-mobile-value"></td>');
          continue;
        }
        const secondaryValue = interpolateSeriesAtMinutes(secondaryRows, "total", event.minutesLocal);
        cells.push(`<td class="detail-tide-mobile-time">${escapeHtml(tideEventClockLabel(event))}</td>`);
        cells.push(
          `<td class="detail-tide-mobile-value">${tideEventValueInlineHtml(event.astronomical, secondaryValue)}</td>`
        );
      }

      return (
        `<tr class="detail-tide-mobile-row">` +
        `<th class="detail-tide-mobile-label" scope="row">${kind === "high" ? "Høy:" : "Lav:"}</th>` +
        cells.join("") +
        `</tr>`
      );
    })
    .join("");

  return (
    `<div class="detail-tide-mobile-events">` +
    `<table class="detail-tide-mobile-table"><tbody>${rows}</tbody></table>` +
    `</div>`
  );
}

function isMobileLayout() {
  return MOBILE_LAYOUT_QUERY.matches;
}

function renderTideGraphSvg(spotName, dateLocal) {
  const { entry, astronomicalRows, secondaryRows, events } = tideRowsForDateLocal(spotName, dateLocal);
  if (!entry || !astronomicalRows.length) {
    return `<div class="detail-tide-empty">Ingen tidevannsdata tilgjengelig for denne dagen.</div>`;
  }

  const {
    dayRows: secondaryDayRows,
    plotRows: secondaryPlotRows,
  } = borrowNeighborRowsForDate(entry.parsedDkssRowsLocal, dateLocal, 60);
  const secondaryRenderRows = secondaryPlotRows.map((row) => ({ ...row }));

  const mobileLayout = isMobileLayout();
  const graphWidth = DETAIL_TIDE_GRAPH.width;
  const graphHeight = DETAIL_TIDE_GRAPH.height;
  const plotLeft = DETAIL_TIDE_GRAPH.marginLeft;
  const plotTop = DETAIL_TIDE_GRAPH.marginTop;
  const plotRight = graphWidth - DETAIL_TIDE_GRAPH.marginRight;
  const plotBottom = graphHeight - DETAIL_TIDE_GRAPH.marginBottom;
  const plotWidth = plotRight - plotLeft;
  const plotHeight = plotBottom - plotTop;
  const curveTop = mobileLayout ? plotTop : plotTop + DETAIL_TIDE_LABEL_LAYOUT.curveTopInset;
  const curveBottom = mobileLayout ? plotBottom : plotBottom - DETAIL_TIDE_LABEL_LAYOUT.curveBottomInset;
  const range = resolvedTideGraphRangeForSpot(spotName, [
    { rows: astronomicalRows, valueKey: "astronomical" },
    { rows: secondaryDayRows, valueKey: "total" },
  ]);

  const clipId = `detail-tide-clip-${escapeHtml(spotName).replace(/[^a-zA-Z0-9_-]+/g, "-")}-${dateLocal}`;
  const xFor = (minutesLocal) => plotLeft + (clamp(minutesLocal, 0, 24 * 60) / (24 * 60)) * plotWidth;
  const yFor = (value) => curveTop + ((range.max - value) / (range.max - range.min || 1)) * (curveBottom - curveTop);
  const timeFontSize = mobileLayout ? 24 : 11;
  const valueFontSize = mobileLayout ? 24 : 11.5;
  const darkOverlaySvg = buildGraphDarkSegments(lightWindowForDate(spotName, dateLocal))
    .map((segment) => {
      const x = xFor(segment.startMinutes);
      const width = Math.max(0.25, xFor(segment.endMinutes) - x);
      return `<rect x="${x.toFixed(1)}" y="${plotTop}" width="${width.toFixed(1)}" height="${plotHeight}" fill="${DETAIL_TIDE_GRAPH.darkOverlayFill}"></rect>`;
    })
    .join("");

  const astronomicalPath = buildSmoothPath(astronomicalRows, "astronomical", xFor, yFor);
  const secondaryPath = secondaryRenderRows.length
    ? buildSmoothPath(secondaryRenderRows, "total", xFor, yFor)
    : "";
  const tickHours = [3, 6, 9, 12, 15, 18, 21];
  const ticksSvg = tickHours.map((hour) => {
    const x = xFor(hour * 60);
    return (
      `<line x1="${x.toFixed(1)}" y1="${plotBottom}" x2="${x.toFixed(1)}" y2="${(plotBottom + 5).toFixed(1)}" stroke="${DETAIL_TIDE_GRAPH.axisColor}" stroke-width="1"></line>` +
      `<text x="${x.toFixed(1)}" y="${(plotBottom + 18).toFixed(1)}" text-anchor="middle" font-size="10.5" fill="${DETAIL_TIDE_GRAPH.axisColor}">${pad2(hour)}</text>`
    );
  }).join("");

  const eventLabelsSvg = mobileLayout ? "" : events
    .filter((event) => Number.isFinite(event.minutesLocal) && Number.isFinite(event.astronomical) && ["high", "low"].includes(event.kind))
    .map((event) => {
      const x = clamp(
        xFor(event.minutesLocal),
        plotLeft + DETAIL_TIDE_LABEL_LAYOUT.sideInset,
        plotRight - DETAIL_TIDE_LABEL_LAYOUT.sideInset
      );
      const secondaryValue = interpolateSeriesAtMinutes(secondaryRenderRows, "total", event.minutesLocal);
      const anchorValue = Number.isFinite(secondaryValue)
        ? (event.kind === "high"
          ? Math.max(event.astronomical, secondaryValue)
          : Math.min(event.astronomical, secondaryValue))
        : event.astronomical;
      const anchorY = yFor(anchorValue);
      const { timeY, valueY } = tideLabelPositions(
        event.kind,
        anchorY,
        plotTop,
        plotBottom,
        curveTop,
        curveBottom
      );
      return (
        `<text x="${x.toFixed(1)}" y="${timeY.toFixed(1)}" text-anchor="middle" font-size="${timeFontSize}" font-weight="400" fill="#071629">${escapeHtml(tideEventClockLabel(event))}</text>` +
        `<text x="${x.toFixed(1)}" y="${valueY.toFixed(1)}" text-anchor="middle" font-size="${valueFontSize}" font-weight="500" fill="#071629">${tideEventValueSvg(event.astronomical, secondaryValue)}</text>`
      );
    })
    .join("");

  return (
    `<div class="detail-tide-graph">` +
    `<svg viewBox="0 0 ${graphWidth} ${graphHeight}" aria-hidden="true">` +
    `<defs><clipPath id="${clipId}"><rect x="${plotLeft}" y="${plotTop}" width="${plotWidth}" height="${plotHeight}" rx="12" ry="12"></rect></clipPath></defs>` +
    `<rect x="${plotLeft}" y="${plotTop}" width="${plotWidth}" height="${plotHeight}" rx="12" ry="12" fill="${DETAIL_TIDE_GRAPH.dayFill}"></rect>` +
    `<g clip-path="url(#${clipId})">` +
    darkOverlaySvg +
    `<path d="${astronomicalPath}" fill="none" stroke="${DETAIL_TIDE_GRAPH.astronomicalColor}" stroke-width="2"></path>` +
    (secondaryPath ? `<path d="${secondaryPath}" fill="none" stroke="${DETAIL_TIDE_GRAPH.secondaryColor}" stroke-width="2.25"></path>` : "") +
    `</g>` +
    ticksSvg +
    eventLabelsSvg +
    `</svg>` +
    (mobileLayout ? renderMobileTideEventRows(events, secondaryRenderRows) : "") +
    `</div>`
  );
}

function renderLightSideInfo(spotName, dateLocal) {
  const lightWindow = lightWindowForDate(spotName, dateLocal);
  if (!lightWindow) {
    return `<div class="detail-empty-note">Ingen lysdata tilgjengelig for denne dagen.</div>`;
  }

  const adjustedSuffix = lightWindow.weatherAdjusted ? " (værjustert)" : "";
  return (
    `<div class="detail-light-stack">` +
    `<div class="detail-side-line">` +
    `<span class="detail-side-label">Første/siste lys:</span>` +
    `<span class="detail-side-copy"><span class="detail-side-emphasis">${escapeHtml(lightWindow.firstLightLocal)} / ${escapeHtml(lightWindow.lastLightLocal)}</span></span>` +
    (adjustedSuffix ? `<span class="detail-side-note">${escapeHtml(adjustedSuffix)}</span>` : "") +
    `</div>` +
    `</div>`
  );
}

function renderSeaTemperatureInfo(spotName) {
  const seaTemperature = spotDataEntry(spotName)?.seaTemperature;
  if (!seaTemperature || !Number.isFinite(seaTemperature.seaTempC)) {
    return (
      `<div class="detail-sea-line">` +
      `<span class="detail-side-label">Sjøtemp:</span>` +
      `<span class="detail-sea-copy">Ingen målt sjøtemperatur tilgjengelig akkurat nå.</span>` +
      `</div>`
    );
  }

  const observedDate = seaTemperature.observedDateLabel || "--/--";
  const location = seaTemperature.location || "ukjent lokasjon";
  return (
    `<div class="detail-sea-line">` +
    `<span class="detail-side-label">Sjøtemp:</span>` +
    `<span class="detail-sea-copy"><span class="detail-side-emphasis">${escapeHtml(formatTideMeters(seaTemperature.seaTempC))} °C</span> målt ${escapeHtml(observedDate)} ved ${escapeHtml(location)}</span>` +
    `</div>`
  );
}

function renderTideSupportPanel(spotName, dateLocal) {
  const tideEntry = tideSpotEntry(spotName);
  const hasDkss = Boolean(tideEntry?.parsedDkssRowsLocal?.length);
  const titleLocation = tideEntry?.stationName || tideEntry?.dkss?.sourceName || "ukjent lokasjon";

  return (
    `<div class="detail-tide-panel">` +
    `<div class="detail-tide-head">` +
    `<div class="detail-tide-title-wrap">` +
    `<h3 class="detail-tide-title">Tidevann <span class="detail-tide-title-location">(${escapeHtml(titleLocation)})</span></h3>` +
    (hasDkss
      ? (
        `<div class="detail-tide-legend">` +
        `<span class="detail-tide-legend-item"><span class="detail-tide-legend-dot" style="color:${DETAIL_TIDE_GRAPH.astronomicalColor}"></span>Tidevann</span>` +
        `<span class="detail-tide-legend-item"><span class="detail-tide-legend-dot" style="color:${DETAIL_TIDE_GRAPH.secondaryColor}"></span>Justert for værbidrag</span>` +
        `</div>`
      )
      : "") +
    `</div>` +
    `</div>` +
    `<div class="detail-tide-layout">` +
    `<div class="detail-tide-graph-wrap">${renderTideGraphSvg(spotName, dateLocal)}</div>` +
    `<div class="detail-tide-side">` +
    renderLightSideInfo(spotName, dateLocal) +
    renderSeaTemperatureInfo(spotName) +
    `</div>` +
    `</div>` +
    `</div>`
  );
}

function renderDetailLabels() {
  return [
    renderLabelCell("Tid", "forecast-label--time"),
    renderLabelCell("Surf", "forecast-label--center"),
    renderLabelCell("Vind m/s", "forecast-label--center"),
    renderLabelCell("Primærswell", "forecast-label--center"),
    renderLabelCell("Sekundærswell", "forecast-label--center"),
    renderLabelCell("Nedbør", "forecast-label--center"),
    renderLabelCell("Luft", "forecast-label--center"),
    renderLabelCell("Sky", "forecast-label--center"),
  ].join("");
}

function detailRowForExactLocalTime(spotName, dateLocal, targetMinutes) {
  const baseRow = rowForExactLocalTime(spotName, dateLocal, targetMinutes);
  const weatherRow = weatherVariantRowForExactLocalTime(spotName, dateLocal, targetMinutes);

  if (!weatherRow) {
    return baseRow;
  }
  if (!baseRow) {
    return weatherRow;
  }

  return {
    ...baseRow,
    windSpeedMs: weatherRow.windSpeedMs,
    windGustMs: weatherRow.windGustMs,
    windDirDeg: weatherRow.windDirDeg,
    precipMm: weatherRow.precipMm,
    airTempC: weatherRow.airTempC,
    cloudPct: weatherRow.cloudPct,
    showGust: Boolean(weatherRow.showGust || Number.isFinite(weatherRow.windGustMs)),
  };
}

function renderDetailValueRow(spotName, row, targetMinutes) {
  const swells = Array.isArray(row?.swells) ? row.swells : [];
  const showGust = Boolean(row?.showGust || Number.isFinite(row?.windGustMs));
  const blankExtra = renderBlankExtraValue();

  return [
    renderValueCell(escapeHtml(detailTimeLabel(targetMinutes)), "forecast-cell--time"),
    renderValueCell(renderSwellSignalCell(row, spotName), "forecast-cell--surf forecast-cell--center"),
    renderValueCell(renderWindCell(row, showGust, { directionMode: detailWindDirectionMode }), "forecast-cell--wind forecast-cell--center"),
    renderValueCell(renderSwellSystem(swells[0], { directionMode: detailWaveDirectionMode }), "forecast-cell--swell forecast-cell--center"),
    renderValueCell(renderSecondarySwells(swells, { directionMode: detailWaveDirectionMode }), "forecast-cell--secondary forecast-cell--center"),
    renderValueCell(row ? renderExtraValue(row?.precipMm, "mm", formatStreamlitDecimal) : blankExtra, "forecast-cell--extra forecast-cell--center"),
    renderValueCell(row ? renderExtraValue(row?.airTempC, "°C", formatStreamlitInteger) : blankExtra, "forecast-cell--extra forecast-cell--center"),
    renderValueCell(row ? renderExtraValue(row?.cloudPct, "%", formatStreamlitInteger) : blankExtra, "forecast-cell--extra forecast-cell--center"),
  ].join("");
}

function renderLightCard(spotName, dateLocal) {
  const lightWindow = lightWindowForDate(spotName, dateLocal);
  if (!lightWindow) {
    return (
      `<div class="detail-info-card">` +
      `<h3 class="detail-info-title">Lys</h3>` +
      `<div class="detail-empty-note">Ingen lysdata tilgjengelig for denne dagen.</div>` +
      `</div>`
    );
  }

  return (
    `<div class="detail-info-card">` +
    `<h3 class="detail-info-title">Lys</h3>` +
    `<div class="detail-light-line">` +
    `<span class="detail-light-label">${escapeHtml(lightWindow.label)}</span>` +
    `<span>${escapeHtml(lightWindow.firstLightLocal)} / ${escapeHtml(lightWindow.lastLightLocal)}</span>` +
    `</div>` +
    `</div>`
  );
}

function renderTideCard(spotName, dateLocal) {
  const tideSpot = tideSpotEntry(spotName);
  const events = Array.isArray(tideSpot?.events)
    ? tideSpot.events.filter((event) => dateLocalFromUtc(event.timeUtc) === dateLocal)
    : [];

  if (!events.length) {
    return (
      `<div class="detail-info-card">` +
      `<h3 class="detail-info-title">Tidevann</h3>` +
      `<div class="detail-empty-note">Ingen tidevannsdata tilgjengelig for denne dagen.</div>` +
      `</div>`
    );
  }

  const rowsHtml = events.map((event) => {
    const dkssRow = nearestDkssRowForTime(spotName, event.timeUtc);
    const dkssText = Number.isFinite(dkssRow?.total) ? formatStreamlitDecimal(dkssRow.total) : "-";
    const astronomical = Number.isFinite(event.astronomical) ? formatStreamlitDecimal(event.astronomical) : "-";
    return (
      `<tr>` +
      `<td>${escapeHtml(timeLocalFromUtc(event.timeUtc))}</td>` +
      `<td>${escapeHtml(tideKindLabel(event.kind))}</td>` +
      `<td>${escapeHtml(astronomical)}</td>` +
      `<td>${escapeHtml(dkssText)}</td>` +
      `</tr>`
    );
  }).join("");

  return (
    `<div class="detail-info-card">` +
    `<h3 class="detail-info-title">Tidevann</h3>` +
    `<table class="detail-tide-table">` +
    `<thead><tr><th>Tid</th><th>Type</th><th>Astro</th><th>DKSS</th></tr></thead>` +
    `<tbody>${rowsHtml}</tbody>` +
    `</table>` +
    `</div>`
  );
}

function renderDetailDaySection(spotName, dateLocal) {
  const expanded = isDetailDayExpanded(spotName, dateLocal);
  const minuteSlots = expanded ? detailExpandedMinutesForDate(spotName, dateLocal) : detailCollapsedMinutes();
  const labels = renderDetailLabels();
  const fullDayLabel = detailDayTitleForDate(dateLocal);
  const shortDayLabel = detailDayShortTitleForDate(dateLocal);
  const rowsHtml = minuteSlots.map((targetMinutes) => (
    `<div class="forecast-row forecast-row--values">` +
    renderDetailValueRow(spotName, detailRowForExactLocalTime(spotName, dateLocal, targetMinutes), targetMinutes) +
    `</div>`
  )).join("");

  const supportHtml = expanded
    ? (
      `<div class="detail-support">` +
      renderTideSupportPanel(spotName, dateLocal) +
      `</div>`
    )
    : "";

  return (
    `<section class="detail-day${expanded ? " detail-day--expanded" : ""}" data-day-toggle="${escapeHtml(dateLocal)}" data-day-label-full="${escapeHtml(fullDayLabel)}" data-day-label-short="${escapeHtml(shortDayLabel)}">` +
    `<h3 class="detail-day-title">${escapeHtml(fullDayLabel)}</h3>` +
    `<div class="detail-day-table-scroll">` +
    `<div class="detail-day-table">` +
    `<div class="forecast-row forecast-row--labels">${labels}</div>` +
    rowsHtml +
    `</div>` +
    `</div>` +
    supportHtml +
    `</section>`
  );
}

function observationDistanceLabel(distanceKm) {
  if (!Number.isFinite(distanceKm) || distanceKm <= 0) return "";
  return `${formatNoNumber(distanceKm, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} km`;
}

function observationSeriesMeta(source) {
  return [
    observationProviderLabel(source, "Frost"),
    observationResolutionLabel(source?.windResolution),
    observationDistanceLabel(source?.distanceKm),
  ].filter(Boolean).join(" · ");
}

function observationSnapshotMeta(source) {
  return observationMeasuredLabel(source?.sensorTimeUtc);
}

function observationLatestCardCopy(source) {
  return [
    observationProviderLabel(source, "observasjon"),
    source?.latestObservationFromSeries ? observationResolutionLabel(source?.windResolution) : "",
    observationDistanceLabel(source?.distanceKm),
  ].filter(Boolean).join(" · ");
}

function latestObservationSourcesForSpot(spotName) {
  const instantSources = liveWindInstantSourcesForSpot(spotName)
    .filter((source) => source?.latestObservation || source?.snapshot);
  const seenNames = new Set(instantSources.map((source) => normalizeObservationName(source?.name)));
  const seriesFallbacks = liveWindSeriesSourcesForSpot(spotName)
    .filter((source) => observationRowsForDisplay(source).length)
    .filter((source) => !seenNames.has(normalizeObservationName(source?.name)))
    .map((source) => {
      const latestRow = observationRowsForDisplay(source)[0];
      return {
        ...source,
        sensorTimeUtc: latestRow?.timeUtc || null,
        latestObservationFromSeries: true,
        latestObservation: latestRow
          ? {
            sensorTimeUtc: latestRow.timeUtc,
            windSpeedMs: latestRow.windSpeedMs,
            windDirDeg: latestRow.windDirDeg,
            windGustMs: latestRow.windGustMs,
          }
          : null,
      };
    });
  return [...instantSources, ...seriesFallbacks].sort(sortObservationSources);
}

function observationDisplaySourcesForSpot(spotName) {
  const configured = OBSERVATION_LAYOUT_CONFIG[spotName];
  const actualSources = [
    ...liveWindSeriesSourcesForSpot(spotName),
    ...liveWindInstantSourcesForSpot(spotName),
  ];

  if (!configured?.length) {
    return actualSources;
  }

  const sourceByName = new Map(actualSources.map((source) => [normalizeObservationName(source?.name), source]));
  return configured.map((entry) => {
    if (entry.placeholder) {
      return {
        name: entry.name,
        linkedSpot: spotName,
        placeholder: true,
      };
    }
    return sourceByName.get(normalizeObservationName(entry.sourceName || entry.name)) || {
      name: entry.name,
      linkedSpot: spotName,
      placeholder: true,
    };
  });
}

function observationTableRows(source) {
  const seriesRows = observationRowsForDisplay(source);
  if (seriesRows.length) {
    return seriesRows;
  }

  const snapshot = source?.latestObservation || source?.snapshot || null;
  if (!snapshot) {
    return [];
  }

  const timeUtc = snapshot.sensorTimeUtc || source?.sensorTimeUtc || null;
  return [
    {
      timeUtc,
      timeLocal: timeUtc ? timeLocalFromUtc(timeUtc) : "--",
      windSpeedMs: snapshot.windSpeedMs,
      windDirDeg: snapshot.windDirDeg,
      windGustMs: snapshot.windGustMs,
    },
  ];
}

function renderObservationSeriesBlock(source) {
  const rows = observationTableRows(source);
  const labels = [
    renderLabelCell("Tid", "forecast-label--time"),
    renderLabelCell("Vind m/s", "forecast-label--center"),
  ].join("");
  const valueRows = rows.map((row) => {
    const showGust = Number.isFinite(row?.windGustMs);
    const windRow = {
      windSpeedMs: row?.windSpeedMs,
      windDirDeg: row?.windDirDeg,
      windGustMs: row?.windGustMs,
    };
    return (
      `<div class="forecast-row forecast-row--values">` +
      renderValueCell(escapeHtml(row?.timeLocal || (row?.timeUtc ? timeLocalFromUtc(row.timeUtc) : "--")), "forecast-cell--time") +
      renderValueCell(renderWindCell(windRow, showGust, { directionMode: detailWindDirectionMode }), "forecast-cell--wind forecast-cell--center") +
      `</div>`
    );
  }).join("");

  return (
    `<section class="detail-observation-series-card">` +
    `<div class="detail-observation-series-head">` +
    `<h3 class="detail-observation-series-title">${escapeHtml(source?.name || "Ukjent stasjon")}</h3>` +
    `</div>` +
    `<div class="detail-observation-table-scroll">` +
    `<div class="detail-observation-table">` +
    `<div class="forecast-row forecast-row--labels">${labels}</div>` +
    valueRows +
    `</div>` +
    `</div>` +
    `</section>`
  );
}

function renderObservationInstantCard(source) {
  const snapshot = source?.latestObservation || source?.snapshot || null;
  const windRow = snapshot
    ? {
      windSpeedMs: snapshot.windSpeedMs,
      windDirDeg: snapshot.windDirDeg,
      windGustMs: snapshot.windGustMs,
    }
    : null;
  const showGust = Number.isFinite(snapshot?.windGustMs);
  const sourceCopy = observationLatestCardCopy(source);

  return (
    `<article class="detail-observation-card">` +
    `<div class="detail-observation-card-head">` +
    `<h3 class="detail-observation-card-title">${escapeHtml(source?.name || "Ukjent stasjon")}</h3>` +
    `<div class="detail-observation-card-meta">${escapeHtml(observationSnapshotMeta(source))}</div>` +
    `</div>` +
    (sourceCopy
      ? `<div class="detail-observation-card-copy">${escapeHtml(sourceCopy)}</div>`
      : "") +
    `<div class="detail-observation-card-wind">${renderWindCell(windRow, showGust, { directionMode: detailWindDirectionMode })}</div>` +
    `</article>`
  );
}

function renderObservationsView(spotName) {
  const sources = observationDisplaySourcesForSpot(spotName);

  if (!sources.length) {
    return (
      `<div class="detail-empty-note detail-observation-empty">` +
      `Fant ingen observasjoner for denne spotten ennå.` +
      `</div>`
    );
  }

  return (
    `<section class="detail-observations">` +
    `<div class="detail-observation-series">` +
    sources.map((source) => renderObservationSeriesBlock(source)).join("") +
    `</div>` +
    `</section>`
  );
}

function renderStatisticsPlaceholder() {
  return (
    `<div class="detail-info-card">` +
    `<h3 class="detail-info-title">Statistikk</h3>` +
    `<div class="detail-empty-note">Statistikkfanen er ikke bygget ut ennå.</div>` +
    `</div>`
  );
}

function syncDetailWeatherControls(spotName) {
  if (!detailWindTargetControlEl || !detailWindTargetEl) return;

  if (currentDetailTab !== "forecast") {
    detailWindTargetControlEl.hidden = true;
    scheduleDetailStickyStateSync();
    return;
  }

  const options = weatherOptionsForSpot(spotName);
  if (options.length <= 1) {
    detailWindTargetControlEl.hidden = true;
    detailWindTargetEl.innerHTML = "";
    scheduleDetailStickyStateSync();
    return;
  }

  const selectedOption = selectedWeatherOptionForSpot(spotName);
  detailWindTargetEl.innerHTML = options.map((option) => (
    `<option value="${escapeHtml(option.name)}"${option.name === selectedOption ? " selected" : ""}>${escapeHtml(option.name)}</option>`
  )).join("");
  detailWindTargetEl.value = selectedOption;
  detailWindTargetControlEl.hidden = false;
  scheduleDetailStickyStateSync();
}

function detailScrollContainer() {
  return pageShellEl?.classList.contains("page-shell--detail") ? pageShellEl : detailViewEl;
}

function renderDetailView(spotName) {
  const title = displaySpotName(spotName);
  detailSpotTitleEl.textContent = title;
  syncDetailTabButtons();
  syncDetailWeatherControls(spotName);
  syncDetailDirectionModeControls();

  let detailHtml = "";
  if (currentDetailTab === "observations") {
    detailHtml = renderObservationsView(spotName);
  } else if (currentDetailTab === "statistics") {
    detailHtml = renderStatisticsPlaceholder();
  } else {
    const dates = uniqueDateLocalsForSpot(spotName);
    detailHtml = dates.length
      ? dates.map((dateLocal) => renderDetailDaySection(spotName, dateLocal)).join("")
      : `<div class="empty-state">Fant ingen detaljerte rader for denne spotten.</div>`;
  }
  detailContentEl.innerHTML = detailHtml;

  overviewViewEl.hidden = true;
  detailViewEl.hidden = false;
  if (timePanelMetaEl) {
    timePanelMetaEl.hidden = true;
  }
  timePanelEl.hidden = true;
  pageShellEl?.classList.add("page-shell--detail");
  if (shouldResetDetailScroll) {
    detailScrollContainer()?.scrollTo({ top: 0, left: 0, behavior: "auto" });
    shouldResetDetailScroll = false;
  }
  scheduleDetailStickyStateSync();
}

function scrollDetailDayToTop(dateLocal) {
  if (!detailContentEl) return;
  const targetSection = [...detailContentEl.querySelectorAll("[data-day-toggle]")]
    .find((element) => element.dataset.dayToggle === dateLocal);
  if (!targetSection) return;
  const scrollContainer = detailScrollContainer();
  if (!scrollContainer) return;
  const stickyHeight = detailStickyEl?.offsetHeight || 0;
  const containerRect = scrollContainer.getBoundingClientRect();
  const targetRect = targetSection.getBoundingClientRect();
  const targetTop = Math.max(0, scrollContainer.scrollTop + (targetRect.top - containerRect.top) - stickyHeight - 8);
  scrollContainer.scrollTo({ top: targetTop, behavior: "auto" });
}

function renderExtraValue(value, unit, formatter) {
  const text = formatter(value);
  if (text === "-") {
    return `<span class="forecast-extra"><span class="forecast-extra-value">-</span></span>`;
  }
  return (
    `<span class="forecast-extra">` +
    `<span class="forecast-extra-value">${escapeHtml(text)}</span>` +
    unitHtml(unit) +
    `</span>`
  );
}

function renderBlankExtraValue() {
  return `<span class="forecast-extra"></span>`;
}

function normalizeCompassDeg(deg) {
  return ((deg % 360) + 360) % 360;
}

function isDegWithinSector(deg, sector) {
  if (!Number.isFinite(deg) || !sector) return false;
  const value = normalizeCompassDeg(deg);
  const start = normalizeCompassDeg(sector.start);
  const end = normalizeCompassDeg(sector.end);
  if (start <= end) {
    return value >= start && value <= end;
  }
  return value >= start || value <= end;
}

function spotRuleConfigFor(spotName) {
  return SPOT_RULE_CONFIG[spotName] || null;
}

function displaySpotName(spotName) {
  return spotRuleConfigFor(spotName)?.displayName || spotName;
}

function swellSignalCountForSwell(swell) {
  if (!swell) return 0;
  const height = swell.heightM;
  const period = swell.periodS;
  if (!Number.isFinite(height) || !Number.isFinite(period)) {
    return 0;
  }
  if (height > 3 && period > 7.5) {
    return 3;
  }
  if (height > 2 && period > 6.5) {
    return 2;
  }
  if ((height * period * period) > 70 && period >= 6.5) {
    return 1;
  }
  return 0;
}

function bestSignalSwellForRow(row) {
  const swells = Array.isArray(row?.swells) ? row.swells : [];
  let bestSwell = null;
  let bestCount = 0;
  let bestScore = -Infinity;

  swells.forEach((swell) => {
    const count = swellSignalCountForSwell(swell);
    const score = Number.isFinite(swell?.heightM) && Number.isFinite(swell?.periodS)
      ? swell.heightM * swell.periodS * swell.periodS
      : -Infinity;
    if (count > bestCount || (count === bestCount && score > bestScore)) {
      bestSwell = swell;
      bestCount = count;
      bestScore = score;
    }
  });

  return bestSwell;
}

function effectiveForecastGust(row) {
  if (Number.isFinite(row?.windGustMs)) {
    return row.windGustMs;
  }
  return row?.windSpeedMs;
}

function windDirectionLooksGood(spotName, deg) {
  const windSector = spotRuleConfigFor(spotName)?.wind;
  if (!windSector) return true;
  return isDegWithinSector(deg, windSector);
}

function waveDirectionLooksGood(spotName, deg) {
  const blockedWaveSector = spotRuleConfigFor(spotName)?.wave;
  if (!blockedWaveSector) return true;
  return !isDegWithinSector(deg, blockedWaveSector);
}

function swellSignalColorForRow(row, spotName) {
  const gust = effectiveForecastGust(row);
  const bestSwell = bestSignalSwellForRow(row);
  const windGood = windDirectionLooksGood(spotName, row?.windDirDeg);
  const waveGood = bestSwell ? waveDirectionLooksGood(spotName, bestSwell.dirDeg) : true;

  if (Number.isFinite(gust) && gust > 20) {
    return "red";
  }
  if (Number.isFinite(gust) && gust < 5) {
    return "green";
  }
  if (windGood && waveGood) {
    if (Number.isFinite(gust) && gust > 12) {
      return "orange";
    }
    return "green";
  }
  return "red";
}

function renderSwellSignalCell(row, spotName) {
  if (!row) {
    return `<span class="forecast-signal-wrap"></span>`;
  }
  const scoreCount = Number.isFinite(row?.scores?.waveScore) ? row.scores.waveScore : Number.NaN;
  const count = Number.isFinite(scoreCount)
    ? Math.max(0, Math.min(3, Math.round(scoreCount)))
    : (Array.isArray(row?.swells) ? row.swells : []).reduce((maxCount, swell) => (
      Math.max(maxCount, swellSignalCountForSwell(swell))
    ), 0);

  let src = "symbols/bars-0.svg";
  let alt = "0 surf bars";
  if (count > 0) {
    const color = typeof row?.scores?.surfColor === "string"
      ? row.scores.surfColor
      : swellSignalColorForRow(row, spotName);
    src = `symbols/bars-${color}-${count}.svg`;
    alt = `${count} ${color} surf bars`;
  }

  return (
    `<span class="forecast-signal-wrap">` +
    `<img class="forecast-signal-symbol" src="${src}" alt="${escapeHtml(alt)}" draggable="false">` +
    `</span>`
  );
}

function renderWindCell(row, showGust, options = {}) {
  const directionMode = options.directionMode ?? "arrow";
  if (!row) {
    return (
      `<div class="forecast-wind forecast-wind--empty">` +
      `<span class="forecast-wind-pill"></span>` +
      `<span class="forecast-wind-dir">${degToArrowHtml(Number.NaN, "wind", { mode: directionMode })}</span>` +
      `</div>`
    );
  }

  const speed = row.windSpeedMs;
  const gust = showGust ? row.windGustMs : Number.NaN;
  const speedText = formatStreamlitInteger(speed);
  const gustText = formatStreamlitInteger(gust);
  const windColorsEnabled = options.windColorsEnabled ?? windColorEnabled;

  let pillText = "";
  let highlightSpeed = Number.NaN;
  if (speedText !== "-" && gustText !== "-") {
    pillText =
      `<span class="forecast-wind-value">${escapeHtml(speedText)}</span>` +
      `<span class="forecast-wind-gap">&nbsp;</span>` +
      `<span class="forecast-wind-bracket forecast-wind-bracket-muted">(</span>` +
      `<span class="forecast-wind-value">${escapeHtml(gustText)}</span>` +
      `<span class="forecast-wind-bracket forecast-wind-bracket-muted">)</span>`;
    highlightSpeed = gust;
  } else if (speedText !== "-") {
    pillText = `<span class="forecast-wind-value">${escapeHtml(speedText)}</span>`;
    highlightSpeed = speed;
  } else if (gustText !== "-") {
    pillText = `<span class="forecast-wind-value">${escapeHtml(gustText)}</span>`;
    highlightSpeed = gust;
  }

  return (
    `<div class="forecast-wind${pillText ? "" : " forecast-wind--empty"}">` +
    `<span class="forecast-wind-pill">` +
    `<span class="forecast-wind-pill-fill" style="${windHighlightStyle(highlightSpeed, windColorsEnabled)}">` +
    `<span class="forecast-wind-pill-text">${pillText}</span>` +
    `</span>` +
    `</span>` +
    `<span class="forecast-wind-dir">${degToArrowHtml(row.windDirDeg, "wind", { mode: directionMode })}</span>` +
    `</div>`
  );
}

function flattenSpotRows(spotName) {
  const spotEntry = FORECAST_DATA.spots[spotName];
  const rowByUtc = new Map();
  if (!spotEntry) {
    return rowByUtc;
  }

  if (Array.isArray(spotEntry.rows)) {
    spotEntry.rows.forEach((row) => {
      if (row?.timeUtc) {
        rowByUtc.set(row.timeUtc, normalizeMeldingaRow(row));
      }
    });
    return rowByUtc;
  }

  if (!Array.isArray(spotEntry.days)) {
    return rowByUtc;
  }

  spotEntry.days.forEach((day) => {
    const previewRows = Array.isArray(day.previewRows) ? day.previewRows : [];
    const detailRows = Array.isArray(day.detailRows) && day.detailRows.length ? day.detailRows : previewRows;

    detailRows.forEach((row) => {
      rowByUtc.set(row.timeUtc, normalizeLegacyRow(row, day.showGust));
    });

    previewRows.forEach((row) => {
      if (!rowByUtc.has(row.timeUtc)) {
        rowByUtc.set(row.timeUtc, normalizeLegacyRow(row, day.showGust));
      }
    });
  });

  return rowByUtc;
}

function preferredStartIndex(slots) {
  if (!slots.length) return 0;
  const now = new Date();
  const nowMs = now.getTime();
  const todayKey = dateLocalFromUtc(now.toISOString());
  const osloNow = getOsloParts(now);
  const roundedHour = Math.round((osloNow.hour * 60 + osloNow.minute) / 60) * 60;
  const preferredMinutes = clamp(roundedHour, 6 * 60, 18 * 60);
  const preferredIndex = slots.findIndex((slot) => (
    slot.kind === "shared"
    && slot.dateLocal === todayKey
    && slot.targetMinutes === preferredMinutes
  ));

  if (preferredIndex >= 0) {
    return preferredIndex;
  }

  let bestIndex = 0;
  let bestDiff = Number.POSITIVE_INFINITY;

  slots.forEach((slot, index) => {
    const diff = Math.abs(slotSortMs(slot) - nowMs);
    if (diff < bestDiff) {
      bestDiff = diff;
      bestIndex = index;
    }
  });

  return bestIndex;
}

function renderLabelCell(text, className = "") {
  const classes = ["forecast-label"];
  if (className) classes.push(className);
  return `<div class="${classes.join(" ")}">${escapeHtml(text)}</div>`;
}

function renderValueCell(content, className = "") {
  const classes = ["forecast-cell"];
  if (className) classes.push(className);
  return `<div class="${classes.join(" ")}">${content}</div>`;
}

function renderSpotBlock(spotName, row) {
  const swells = Array.isArray(row?.swells) ? row.swells : [];
  const displayName = displaySpotName(spotName);
  const showGust = Boolean(row?.showGust || Number.isFinite(row?.windGustMs));
  const blankExtra = renderBlankExtraValue();

  const labels = [
    renderLabelCell("Spot", "forecast-label--spot"),
    renderLabelCell("Surf", "forecast-label--center"),
    renderLabelCell("Vind m/s", "forecast-label--center"),
    renderLabelCell("Primærswell", "forecast-label--center"),
    renderLabelCell("Sekundærswell", "forecast-label--center"),
    renderLabelCell("Nedbør", "forecast-label--center"),
    renderLabelCell("Luft", "forecast-label--center"),
    renderLabelCell("Sky", "forecast-label--center"),
  ].join("");

  const values = [
    renderValueCell(escapeHtml(displayName), "forecast-cell--spot"),
    renderValueCell(renderSwellSignalCell(row, spotName), "forecast-cell--surf forecast-cell--center"),
    renderValueCell(renderWindCell(row, showGust), "forecast-cell--wind forecast-cell--center"),
    renderValueCell(renderSwellSystem(swells[0]), "forecast-cell--swell forecast-cell--center"),
    renderValueCell(renderSecondarySwells(swells), "forecast-cell--secondary forecast-cell--center"),
    renderValueCell(row ? renderExtraValue(row?.precipMm, "mm", formatStreamlitDecimal) : blankExtra, "forecast-cell--extra forecast-cell--center"),
    renderValueCell(row ? renderExtraValue(row?.airTempC, "°C", formatStreamlitInteger) : blankExtra, "forecast-cell--extra forecast-cell--center"),
    renderValueCell(row ? renderExtraValue(row?.cloudPct, "%", formatStreamlitInteger) : blankExtra, "forecast-cell--extra forecast-cell--center"),
  ].join("");

  return (
    `<section class="forecast-spot forecast-spot--interactive" data-spot="${escapeHtml(spotName)}" tabindex="0" role="link" aria-label="Åpne varsel for ${escapeHtml(displayName)}">` +
    `<div class="forecast-row forecast-row--labels">${labels}</div>` +
    `<div class="forecast-row forecast-row--values">${values}</div>` +
    `</section>`
  );
}

function renderEmptyState(message) {
  overviewViewEl.hidden = false;
  detailViewEl.hidden = true;
  timePanelEl.hidden = false;
  pageShellEl?.classList.remove("page-shell--detail");
  pageShellEl?.scrollTo({ top: 0, left: 0, behavior: "auto" });
  spotListEl.innerHTML = `<div class="empty-state">${escapeHtml(message)}</div>`;
  if (timePanelMetaEl) {
    timePanelMetaEl.hidden = true;
    timePanelMetaEl.textContent = "";
  }
  timeValueEl.textContent = "--";
  timeStartEl.textContent = "--";
  timeEndEl.textContent = "--";
  timeRangeEl.disabled = true;
  if (detailDayIndicatorEl) {
    detailDayIndicatorEl.hidden = true;
    detailDayIndicatorEl.textContent = "";
  }
  scheduleOverviewTimePanelReserveSync();
}

function renderOverviewView() {
  if (!sliderSlots.length) {
    renderEmptyState("Fant ingen tider for slideren akkurat nå.");
    return;
  }

  const selectedSlot = sliderSlots[selectedIndex];
  const modelRunText = overviewModelRunText();
  if (timePanelMetaEl) {
    timePanelMetaEl.textContent = modelRunText;
    timePanelMetaEl.hidden = !modelRunText;
  }
  timeValueEl.textContent = selectedSlot.displayText;
  spotListEl.innerHTML = activeSpots.map((spotName) => (
    renderSpotBlock(spotName, resolveRowForSlot(spotName, selectedSlot))
  )).join("");
  overviewViewEl.hidden = false;
  detailViewEl.hidden = true;
  timePanelEl.hidden = false;
  pageShellEl?.classList.remove("page-shell--detail");
  pageShellEl?.scrollTo({ top: 0, left: 0, behavior: "auto" });
  if (detailDayIndicatorEl) {
    detailDayIndicatorEl.hidden = true;
    detailDayIndicatorEl.textContent = "";
  }
  scheduleOverviewTimePanelReserveSync();
}

function applyRoute() {
  currentSpotName = hashSpotName();
  setMenuOpen(false);
  setDetailSettingsOpen(false);
  if (currentSpotName) {
    renderDetailView(currentSpotName);
    return;
  }
  renderOverviewView();
}

function init() {
  if (!activeSpots.length) {
    renderEmptyState("Fant ingen Meldinga-spotter å vise.");
    return;
  }

  activeSpots.forEach((spotName) => {
    const rowsByUtc = flattenSpotRows(spotName);
    flattenedForecasts.set(spotName, rowsByUtc);
    forecastRows.set(
      spotName,
      [...rowsByUtc.values()].sort((left, right) => left.timeUtc.localeCompare(right.timeUtc)),
    );
  });

  buildSliderSlots().forEach((slot) => sliderSlots.push(slot));

  if (!sliderSlots.length) {
    renderEmptyState("Fant ingen tider for slideren akkurat nå.");
    return;
  }

  selectedIndex = preferredStartIndex(sliderSlots);
  timeRangeEl.min = "0";
  timeRangeEl.max = String(sliderSlots.length - 1);
  timeRangeEl.value = String(selectedIndex);
  timeStartEl.textContent = sliderSlots[0].shortText;
  timeEndEl.textContent = sliderSlots[sliderSlots.length - 1].shortText;

  timeRangeEl.addEventListener("input", (event) => {
    selectedIndex = Number(event.target.value);
    renderOverviewView();
  });

  spotListEl.addEventListener("click", (event) => {
    const spotCard = event.target.closest("[data-spot]");
    if (!spotCard) return;
    navigateToSpot(spotCard.dataset.spot);
  });

  spotListEl.addEventListener("keydown", (event) => {
    const spotCard = event.target.closest("[data-spot]");
    if (!spotCard) return;
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      navigateToSpot(spotCard.dataset.spot);
    }
  });

  detailContentEl.addEventListener("click", (event) => {
    const daySection = event.target.closest("[data-day-toggle]");
    if (!daySection || !currentSpotName) return;
    const { dayToggle } = daySection.dataset;
    const wasExpanded = isDetailDayExpanded(currentSpotName, dayToggle);
    toggleDetailDay(currentSpotName, dayToggle);
    renderDetailView(currentSpotName);
    if (wasExpanded) {
      scrollDetailDayToTop(dayToggle);
    }
  });

  detailBackEl.addEventListener("click", (event) => {
    event.preventDefault();
    clearSpotRoute();
  });

  detailTabEls.forEach((tabEl) => {
    tabEl.addEventListener("click", () => {
      const nextTab = normalizeDetailTab(tabEl.dataset.detailTab);
      if (nextTab === currentDetailTab) return;
      setCurrentDetailTab(nextTab);
      if (currentSpotName) {
        shouldResetDetailScroll = true;
        renderDetailView(currentSpotName);
      }
    });
  });

  menuButtonEl.addEventListener("click", (event) => {
    event.stopPropagation();
    setMenuOpen(menuPanelEl.hidden);
  });

  menuPanelEl.addEventListener("click", (event) => {
    event.stopPropagation();
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest(".menu-wrap")) {
      setMenuOpen(false);
    }
    if (!event.target.closest(".detail-settings-wrap")) {
      setDetailSettingsOpen(false);
    }
  });

  if (windColorToggleEl) {
    windColorEnabled = windColorToggleEl.checked;
  } else if (detailWindColorToggleEl) {
    windColorEnabled = detailWindColorToggleEl.checked;
  }
  syncWindColorControls();

  if (detailWindDirectionModeEl) {
    detailWindDirectionMode = normalizeDirectionDisplayMode(detailWindDirectionModeEl.value);
  }
  if (detailWaveDirectionModeEl) {
    detailWaveDirectionMode = normalizeDirectionDisplayMode(detailWaveDirectionModeEl.value);
  }
  syncDetailDirectionModeControls();

  if (windColorToggleEl) {
    windColorToggleEl.addEventListener("change", () => {
      setWindColorEnabled(windColorToggleEl.checked);
    });
  }

  if (detailSettingsButtonEl) {
    detailSettingsButtonEl.addEventListener("click", (event) => {
      event.stopPropagation();
      setDetailSettingsOpen(detailSettingsPanelEl?.hidden);
    });
  }

  if (detailSettingsPanelEl) {
    detailSettingsPanelEl.addEventListener("click", (event) => {
      event.stopPropagation();
    });
  }

  if (detailWindColorToggleEl) {
    detailWindColorToggleEl.addEventListener("change", () => {
      setWindColorEnabled(detailWindColorToggleEl.checked);
    });
  }

  if (detailWindDirectionModeEl) {
    detailWindDirectionModeEl.addEventListener("change", () => {
      setDetailWindDirectionMode(detailWindDirectionModeEl.value);
      if (currentSpotName) {
        renderDetailView(currentSpotName);
      }
    });
  }

  if (detailWaveDirectionModeEl) {
    detailWaveDirectionModeEl.addEventListener("change", () => {
      setDetailWaveDirectionMode(detailWaveDirectionModeEl.value);
      if (currentSpotName) {
        renderDetailView(currentSpotName);
      }
    });
  }

  if (detailWindTargetEl) {
    detailWindTargetEl.addEventListener("change", () => {
      if (currentSpotName) {
        setSelectedWeatherOptionForSpot(currentSpotName, detailWindTargetEl.value);
        renderDetailView(currentSpotName);
      }
    });
  }

  window.addEventListener("hashchange", applyRoute);
  window.addEventListener("popstate", applyRoute);
  window.addEventListener("resize", scheduleOverviewTimePanelReserveSync);
  window.addEventListener("resize", scheduleDetailStickyStateSync);
  pageShellEl?.addEventListener("scroll", scheduleDetailStickyStateSync, { passive: true });
  detailViewEl?.addEventListener("scroll", scheduleDetailStickyStateSync, { passive: true });
  MOBILE_LAYOUT_QUERY.addEventListener("change", applyRoute);

  syncDetailTabButtons();
  applyRoute();
}

init();
