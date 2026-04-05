const OSLO_TIMEZONE = "Europe/Oslo";
const MONTHS_NO = ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"];
const TIDE_DATA = window.TIDE_DATA || { spots: {} };
const LIVE_WIND_DATA = window.LIVE_WIND_DATA || { sources: {} };
const NOAA_FORECAST_DATA = window.NOAA_FORECAST_DATA || { spots: {} };
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
const KNOT_TO_MS = 0.514444;
const TIDE_GRAPH = {
  width: 780,
  height: 260,
  marginTop: 40,
  marginRight: 24,
  marginBottom: 56,
  marginLeft: 24,
  astronomicalColor: "#0f172a",
  dkssColor: "#f97316",
  axisColor: "#94a3b8",
  markColor: "#64748b",
};
const NORWAY_BOUNDS = {
  south: 57.35,
  west: 3.0,
  north: 71.55,
  east: 32.2,
};
const MAP_BUFFER_KM = 400;
const TERMINATOR_SAMPLE_DEG = 0.25;

function expandBounds(bounds, bufferKm) {
  const centerLat = (bounds.south + bounds.north) / 2;
  const latBufferDeg = bufferKm / 111.32;
  const lonBufferDeg = bufferKm / (111.32 * Math.cos(centerLat * Math.PI / 180));
  return {
    south: bounds.south - latBufferDeg,
    west: bounds.west - lonBufferDeg,
    north: bounds.north + latBufferDeg,
    east: bounds.east + lonBufferDeg,
  };
}

const MAP_BOUNDS = expandBounds(NORWAY_BOUNDS, MAP_BUFFER_KM);

const map = L.map("map", {
  zoomControl: true,
  attributionControl: true,
  dragging: true,
  scrollWheelZoom: true,
  touchZoom: true,
  doubleClickZoom: true,
  boxZoom: true,
  keyboard: true,
  inertia: true,
}).setView([65.0, 13.0], 5);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 18,
  attribution: "&copy; OpenStreetMap",
}).addTo(map);

map.createPane("terminatorPane");
map.getPane("terminatorPane").style.zIndex = 330;
map.getPane("terminatorPane").style.pointerEvents = "none";

map.createPane("dataLinePane");
map.getPane("dataLinePane").style.zIndex = 520;

map.createPane("dataPointPane");
map.getPane("dataPointPane").style.zIndex = 560;

const spotLayer = L.featureGroup().addTo(map);
const dkssLayer = L.featureGroup().addTo(map);
const spotMarkers = [];
const sourceMarkers = [];
const allMarkerRecords = [];
const spotByName = new Map();

const osloPartsFormatter = new Intl.DateTimeFormat("en-GB", {
  timeZone: OSLO_TIMEZONE,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});
const weekdayFormatterNo = new Intl.DateTimeFormat("nb-NO", {
  timeZone: OSLO_TIMEZONE,
  weekday: "long",
});

function getOsloParts(date) {
  const parts = {};
  osloPartsFormatter.formatToParts(date).forEach((part) => {
    if (part.type !== "literal") {
      parts[part.type] = part.value;
    }
  });
  return {
    year: Number(parts.year),
    month: Number(parts.month),
    day: Number(parts.day),
    hour: Number(parts.hour),
    minute: Number(parts.minute),
  };
}

function makeOsloDate(year, month, day, hour) {
  let guess = new Date(Date.UTC(year, month - 1, day, hour, 0, 0));
  for (let i = 0; i < 2; i += 1) {
    const actual = getOsloParts(guess);
    const actualMinutes = Date.UTC(
      actual.year,
      actual.month - 1,
      actual.day,
      actual.hour,
      actual.minute,
      0
    ) / 60000;
    const wantedMinutes = Date.UTC(year, month - 1, day, hour, 0, 0) / 60000;
    guess = new Date(guess.getTime() + (wantedMinutes - actualMinutes) * 60000);
  }
  return guess;
}

function clampHour(hour) {
  if (hour < 4) return 4;
  if (hour > 23) return 23;
  return hour;
}

function initialHourFromNow() {
  const parts = getOsloParts(new Date());
  const rounded = parts.hour + (parts.minute >= 30 ? 1 : 0);
  return clampHour(rounded);
}

function sunAltitudeDeg(date, lat, lon) {
  return SunCalc.getPosition(date, lat, lon).altitude * (180 / Math.PI);
}

function lightState(date, lat, lon) {
  const altitude = sunAltitudeDeg(date, lat, lon);
  if (altitude < -6) {
    return { key: "dark", label: "Morkt", opacity: 0.5 };
  }
  if (altitude < 0) {
    return { key: "civil", label: "Civilt lys", opacity: 0.25 };
  }
  return { key: "day", label: "Lyst", opacity: 0.0 };
}

function haversineKm(lat1, lon1, lat2, lon2) {
  const toRad = (deg) => deg * Math.PI / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(a));
}

function bearingDeg(lat1, lon1, lat2, lon2) {
  const toRad = (deg) => deg * Math.PI / 180;
  const toDeg = (rad) => rad * 180 / Math.PI;
  const phi1 = toRad(lat1);
  const phi2 = toRad(lat2);
  const deltaLon = toRad(lon2 - lon1);
  const y = Math.sin(deltaLon) * Math.cos(phi2);
  const x =
    Math.cos(phi1) * Math.sin(phi2) -
    Math.sin(phi1) * Math.cos(phi2) * Math.cos(deltaLon);
  return (toDeg(Math.atan2(y, x)) + 360) % 360;
}

function bearingLabel(deg) {
  const directions = ["N", "NNO", "NO", "ONO", "O", "OSO", "SO", "SSO", "S", "SSV", "SV", "VSV", "V", "VNV", "NV", "NNV"];
  return directions[Math.round(deg / 22.5) % 16];
}

function spotMarkerColor(stateKey) {
  if (stateKey === "dark") return "#f8fafc";
  if (stateKey === "civil") return "#fde68a";
  return "#60a5fa";
}

function sourceMarkerStyle(source) {
  if (source.provider === "NOAA testpunkt") {
    return {
      lineColor: "#f97316",
      stroke: "#7c2d12",
      fill: "#f97316",
      radius: 5,
    };
  }
  if (source.provider === "DMI DKSS") {
    return {
      lineColor: "#f97316",
      stroke: "#7c2d12",
      fill: "#f97316",
      radius: 5,
    };
  }
  if (source.provider === "Frost") {
    return {
      lineColor: "#10b981",
      stroke: "#065f46",
      fill: "#10b981",
      radius: 4.5,
    };
  }
  if (source.provider === "Kystverket") {
    return {
      lineColor: "#0ea5e9",
      stroke: "#075985",
      fill: "#0ea5e9",
      radius: 4.5,
    };
  }
  if (source.provider === "Kartverket tidevann") {
    return {
      lineColor: "#94a3b8",
      stroke: "#475569",
      fill: "#cbd5e1",
      radius: 4.5,
    };
  }
  if (source.provider === "Yr") {
    return {
      lineColor: "#eab308",
      stroke: "#854d0e",
      fill: "#fde047",
      radius: 4.5,
    };
  }
  if (source.provider === "NOAA vind") {
    return {
      lineColor: "#06b6d4",
      stroke: "#155e75",
      fill: "#22d3ee",
      radius: 4.5,
    };
  }
  if (source.provider === "gfs atmos 0.25") {
    return {
      lineColor: "#ef4444",
      stroke: "#991b1b",
      fill: "#f87171",
      radius: 4.5,
    };
  }
  if (source.provider === "ICON-EU") {
    return {
      lineColor: "#22c55e",
      stroke: "#166534",
      fill: "#4ade80",
      radius: 4.5,
    };
  }
  if (source.provider === "DMI vind") {
    return {
      lineColor: "#f59e0b",
      stroke: "#92400e",
      fill: "#fbbf24",
      radius: 4.5,
    };
  }
  return {
    lineColor: "#94a3b8",
    stroke: "#475569",
    fill: "#94a3b8",
    radius: 4.5,
  };
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

const COMPASS_ROSE_TICKS = Array.from({ length: 16 }, (_, index) => index * 22.5);
const COMPASS_ROSE_LABELS = [
  { deg: 0, label: "N" },
  { deg: 90, label: "Ø" },
  { deg: 180, label: "S" },
  { deg: 270, label: "V" },
];

const SPOT_RULE_CONFIG = {
  "Persfjord": {
    displayName: "Varanger",
    wind: { start: 135, end: 315, startLabel: "SØ", endLabel: "NV" },
    wave: null,
    waveVisual: { kind: "peak", peak: 35, orangeSpan: 180, yellowSpan: 90, greenSpan: 45 },
  },
  "Unstad Beach": {
    displayName: "Lofoten",
    wind: { start: 90, end: 225, startLabel: "Ø", endLabel: "SV" },
    wave: { start: 67.5, end: 180, startLabel: "ØNØ", endLabel: "S" },
    waveVisual: { kind: "peak", peak: 300, orangeSpan: 180, yellowSpan: 90, greenSpan: 45 },
  },
  "Hustadvika Gjestegard": {
    displayName: "Hustadvika",
    wind: { start: 135, end: 225, startLabel: "SØ", endLabel: "SV" },
    wave: { start: 67.5, end: 180, startLabel: "ØNØ", endLabel: "S" },
    waveVisual: { kind: "peak", peak: 325, orangeSpan: 180, yellowSpan: 90, greenSpan: 45 },
  },
  "Alnes Lighthouse (Godoy)": {
    displayName: "Ålesund",
    wind: { start: 45, end: 180, startLabel: "NØ", endLabel: "S" },
    wave: { start: 67.5, end: 180, startLabel: "ØNØ", endLabel: "S" },
    waveVisual: { kind: "peak", peak: 315, orangeSpan: 180, yellowSpan: 90, greenSpan: 45 },
  },
  "Ervika": {
    displayName: "Stad",
    wind: { start: 45, end: 225, startLabel: "NØ", endLabel: "SV" },
    wave: { start: 67.5, end: 157.5, startLabel: "ØNØ", endLabel: "SSØ" },
    waveVisual: { kind: "peak", peak: 300, orangeSpan: 180, yellowSpan: 90, greenSpan: 45 },
  },
  "Pigsty/Piggy": {
    displayName: "Jæren",
    wind: { start: 0, end: 180, startLabel: "N", endLabel: "S" },
    wave: { start: 45, end: 135, startLabel: "NØ", endLabel: "SØ" },
    waveVisual: { kind: "peak", peak: 270, orangeSpan: 180, yellowSpan: 90, greenSpan: 45 },
  },
  "Lista": {
    displayName: "Lista",
    wind: { start: 0, end: 90, startLabel: "N", endLabel: "Ø" },
    wave: { start: 45, end: 90, startLabel: "NØ", endLabel: "Ø" },
    waveVisual: { kind: "formula", formula: "lista" },
  },
  "Mandal / Sjosanden": {
    displayName: "Sjøsanden",
    wind: { start: 67.5, end: 270, startLabel: "ØNØ", endLabel: "V" },
    wave: { start: 292.5, end: 112.5, startLabel: "VNV", endLabel: "ØSØ" },
    waveVisual: { kind: "formula", formula: "sjosanden" },
  },
  "Saltstein": {
    displayName: "Saltsteinen",
    wind: { start: 0, end: 90, startLabel: "N", endLabel: "Ø" },
    wave: { start: 315, end: 45, startLabel: "NV", endLabel: "NØ" },
    waveVisual: { kind: "peak", peak: 210, orangeSpan: 180, yellowSpan: 90, greenSpan: 45 },
  },
};

function spotRuleConfigFor(spotName) {
  return SPOT_RULE_CONFIG[spotName] || null;
}

function displaySpotName(spotName) {
  return spotRuleConfigFor(spotName)?.displayName || spotName;
}

function displaySourceName(source) {
  if (source.provider === "NOAA vind") {
    return `${displaySpotName(source.linkedSpot)} NOAA vindpunkt`;
  }
  return source.name;
}

function displaySourceSummary(source) {
  if (source.provider === "NOAA vind") {
    return `Naermeste NOAA GFS Wave Arctic 9km-grid med ws/wdir-data brukt for ${displaySpotName(source.linkedSpot)}. Punktet brukes til bolgevarselet og enkel vindsammenlikning i popupen.`;
  }
  return source.summary;
}

function clockwiseSpan(startDeg, endDeg) {
  const normalized = ((endDeg - startDeg) % 360 + 360) % 360;
  return normalized === 0 ? 360 : normalized;
}

function polarPoint(cx, cy, radius, deg) {
  const radians = (deg - 90) * Math.PI / 180;
  return {
    x: cx + radius * Math.cos(radians),
    y: cy + radius * Math.sin(radians),
  };
}

function sectorPath(cx, cy, radius, startDeg, endDeg) {
  const span = clockwiseSpan(startDeg, endDeg);
  if (span >= 359.999) return "";
  const start = polarPoint(cx, cy, radius, startDeg);
  const end = polarPoint(cx, cy, radius, endDeg);
  const largeArcFlag = span > 180 ? 1 : 0;
  return [
    `M ${cx} ${cy}`,
    `L ${start.x.toFixed(2)} ${start.y.toFixed(2)}`,
    `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${end.x.toFixed(2)} ${end.y.toFixed(2)}`,
    "Z",
  ].join(" ");
}

function compassRoseSvg({ baseColor, overlays = [], centerLabel }) {
  const size = 180;
  const cx = 90;
  const cy = 90;
  const circleRadius = 44;
  const tickInner = 51;
  const tickOuter = 56;
  const labelRadius = 69;
  const overlayMarkup = overlays.map((overlay) => {
    const overlayPath = sectorPath(cx, cy, circleRadius, overlay.start, overlay.end);
    return overlayPath ? `<path d="${overlayPath}" fill="${overlay.color}"></path>` : "";
  }).join("");

  const ticks = COMPASS_ROSE_TICKS.map((deg) => {
    const inner = polarPoint(cx, cy, tickInner, deg);
    const outer = polarPoint(cx, cy, tickOuter, deg);
    return `<line x1="${inner.x.toFixed(2)}" y1="${inner.y.toFixed(2)}" x2="${outer.x.toFixed(2)}" y2="${outer.y.toFixed(2)}" class="spot-rule-tick"></line>`;
  }).join("");

  const labels = COMPASS_ROSE_LABELS.map(({ deg, label }) => {
    const point = polarPoint(cx, cy, labelRadius, deg);
    return `<text x="${point.x.toFixed(2)}" y="${(point.y + 2.5).toFixed(2)}" text-anchor="middle" class="spot-rule-label">${escapeHtml(label)}</text>`;
  }).join("");

  return (
    `<svg class="spot-rule-svg" viewBox="0 0 ${size} ${size}" aria-hidden="true">` +
    `<circle cx="${cx}" cy="${cy}" r="${circleRadius}" fill="${baseColor}"></circle>` +
    overlayMarkup +
    ticks +
    `<circle cx="${cx}" cy="${cy}" r="${circleRadius}" fill="none" stroke="rgba(15,23,42,0.22)" stroke-width="1.2"></circle>` +
    `<circle cx="${cx}" cy="${cy}" r="15" fill="rgba(255,255,255,0.95)" stroke="rgba(148,163,184,0.36)" stroke-width="1"></circle>` +
    `<text x="${cx}" y="${cy + 4}" text-anchor="middle" class="spot-rule-center">${escapeHtml(centerLabel)}</text>` +
    labels +
    `</svg>`
  );
}

function buildWavePeakOverlays(waveVisual) {
  const peak = normalizeCompassDeg(waveVisual.peak);
  const orangeSpan = waveVisual.orangeSpan || 180;
  const yellowSpan = waveVisual.yellowSpan || 90;
  const greenSpan = waveVisual.greenSpan || 45;
  const spanToSector = (span, color) => ({
    start: normalizeCompassDeg(peak - (span / 2)),
    end: normalizeCompassDeg(peak + (span / 2)),
    color,
  });

  return [
    spanToSector(orangeSpan, "#f59e0b"),
    spanToSector(yellowSpan, "#fde047"),
    spanToSector(greenSpan, "#22c55e"),
  ];
}

const FORMULA_WAVE_VISUALS = {
  lista: {
    samples: [
      { heightM: 1.0, periodS: 7.5 },
      { heightM: 1.8, periodS: 9.0 },
      { heightM: 2.5, periodS: 11.0 },
    ],
  },
  sjosanden: {
    samples: [
      { heightM: 1.2, periodS: 8.0 },
      { heightM: 2.0, periodS: 10.0 },
      { heightM: 2.8, periodS: 12.0 },
    ],
  },
};

const FORMULA_WAVE_COLORS = {
  1: "#f59e0b",
  2: "#fde047",
  3: "#22c55e",
};

function classifyListaWaveBaseForVisual(heightM, periodS, dirDeg) {
  if (heightM <= 0.3 || periodS <= 5.0) {
    return 0;
  }

  const score =
    1.13 * heightM +
    0.18 * Math.sqrt(heightM + 0.39) * (periodS - 6.0) -
    0.49 -
    2.03 * (Math.max(0, 194.0 - dirDeg) / 78.0) ** 2 -
    0.61 * (Math.max(0, dirDeg - 259.0) / 32.0) ** 2 +
    0.26 * Math.max(0, 1.0 - ((dirDeg - 235.0) / 30.0) ** 2) -
    0.06 * (Math.max(0, dirDeg - 272.0) / 40.0) ** 2 -
    1.10 * Math.max(0, 0.55 - heightM) * Math.max(0, 12.0 - periodS) -
    0.07 * (Math.max(0, dirDeg - 275.0) / 20.0) * Math.max(0, periodS - 10.5);

  if (periodS <= 6.0) {
    return score < 0.58 ? 0 : 1;
  }
  if (score < 0.58) return 0;
  if (score < 1.69) return 1;
  if (score < 3.44) return 2;
  return 3;
}

function classifyListaWaveForVisual(heightM, periodS, dirDeg) {
  const baseClass = classifyListaWaveBaseForVisual(heightM, periodS, dirDeg);
  if (dirDeg >= 280.0) {
    let cap = 3;
    if (heightM < 0.5) {
      cap = 0;
    } else if (heightM < 1.0) {
      cap = 1;
    } else if (heightM < 4.0) {
      cap = 2;
    }
    return Math.min(baseClass, cap);
  }
  return baseClass;
}

function classifySjosandenWaveForVisual(heightM, periodS, dirDeg) {
  if (dirDeg < 135.0 || dirDeg > 270.0) {
    return 0;
  }

  const score =
    heightM +
    0.25 * (periodS - 7.0) -
    (Math.max(0, dirDeg - 190.0) / 40.0) ** 2 -
    (Math.max(0, 170.0 - dirDeg) / 25.0) ** 2;

  if (score < 1.9) return 0;
  if (score < 3.0) return 1;
  if (score < 4.0) return 2;
  return 3;
}

function classifyFormulaWaveForVisual(formulaName, heightM, periodS, dirDeg) {
  if (formulaName === "lista") {
    return classifyListaWaveForVisual(heightM, periodS, dirDeg);
  }
  if (formulaName === "sjosanden") {
    return classifySjosandenWaveForVisual(heightM, periodS, dirDeg);
  }
  return 0;
}

function buildDirectionalSectorsFromClasses(classMap, targetClass, color) {
  if (!classMap.some((value) => value === targetClass)) {
    return [];
  }

  const sectors = [];
  let start = null;
  for (let deg = 0; deg < 360; deg += 1) {
    if (classMap[deg] === targetClass) {
      if (start === null) {
        start = deg;
      }
    } else if (start !== null) {
      sectors.push({ start, end: deg, color });
      start = null;
    }
  }
  if (start !== null) {
    sectors.push({ start, end: 360, color });
  }

  if (sectors.length > 1 && sectors[0].start === 0 && sectors[sectors.length - 1].end === 360) {
    const first = sectors.shift();
    const last = sectors.pop();
    sectors.unshift({
      start: last.start,
      end: first.end,
      color,
    });
  }

  return sectors.map((sector) => ({
    start: normalizeCompassDeg(sector.start),
    end: normalizeCompassDeg(sector.end),
    color: sector.color,
  }));
}

function buildFormulaWaveOverlays(waveVisual) {
  const descriptor = FORMULA_WAVE_VISUALS[waveVisual.formula];
  if (!descriptor) {
    return [];
  }

  const classMap = Array.from({ length: 360 }, (_, dirDeg) => {
    let bestClass = 0;
    descriptor.samples.forEach(({ heightM, periodS }) => {
      bestClass = Math.max(
        bestClass,
        classifyFormulaWaveForVisual(waveVisual.formula, heightM, periodS, dirDeg)
      );
    });
    return bestClass;
  });

  return [1, 2, 3].flatMap((targetClass) => (
    buildDirectionalSectorsFromClasses(classMap, targetClass, FORMULA_WAVE_COLORS[targetClass])
  ));
}

function buildSpotRuleCard(type, descriptor) {
  const isWind = type === "wind";
  const title = isWind ? "God vind" : "Bølgeretning";
  const greenColor = "#22c55e";
  const redColor = "#ef4444";
  const centerLabel = isWind ? "vind" : "bølge";
  let baseColor = isWind ? redColor : greenColor;
  let overlays = [];
  let caption = isWind ? "Ingen vindregel satt" : "Ingen bølgeregel satt";
  let note = isWind
    ? "Resten av sirkelen er ugunstig vind."
    : "Resten av sirkelen er tillatt bølgeretning.";

  if (isWind && descriptor) {
    overlays = [{ start: descriptor.start, end: descriptor.end, color: greenColor }];
    caption = `Grønn: ${descriptor.startLabel} til ${descriptor.endLabel} med klokka`;
  } else if (!isWind && descriptor?.kind === "peak") {
    baseColor = redColor;
    overlays = buildWavePeakOverlays(descriptor);
    caption = `Grønn kjerne: 45° rundt ${bearingLabel(descriptor.peak)}`;
    note = "Gult og oransje er gradvis svakere. Rødt er dårlige swellretninger.";
  } else if (!isWind && descriptor?.kind === "formula") {
    baseColor = redColor;
    overlays = buildFormulaWaveOverlays(descriptor);
    caption = "Rødt=0, oransje=1, gult=2, grønt=3";
    note = "Fargene følger spotformelen for bølgeretning, ikke bare en symmetrisk peak-vinkel.";
  } else if (!isWind && descriptor) {
    baseColor = greenColor;
    overlays = [{ start: descriptor.start, end: descriptor.end, color: redColor }];
    caption = `Rød: ${descriptor.startLabel} til ${descriptor.endLabel} med klokka`;
    note = "Resten av sirkelen er tillatt bølgeretning.";
  }

  return (
    `<div class="spot-rule-card">` +
    `<div class="spot-rule-title">${escapeHtml(title)}</div>` +
    compassRoseSvg({ baseColor, overlays, centerLabel }) +
    `<div class="spot-rule-caption">${escapeHtml(caption)}</div>` +
    `<div class="spot-rule-subcaption">${escapeHtml(note)}</div>` +
    `</div>`
  );
}

function buildSpotRuleBlock(spotName) {
  const config = spotRuleConfigFor(spotName);
  if (!config || !config.wind) return "";
  const waveDescriptor = config.waveVisual || config.wave || null;
  const waveNote = waveDescriptor?.kind === "formula"
    ? "Bølgeringen viser faktisk formelklasse per retning: rødt=0, oransje=1, gult=2, grønt=3."
    : waveDescriptor?.kind === "peak"
      ? "Grønn sektor viser optimal swellretning. Gult/oransje blir gradvis svakere, og rødt er dårlige retninger."
      : "Grønn sektor markerer god vind. For bølger er rød sektor det som skal ekskluderes.";
  return (
    `<div class="spot-rule-block">` +
    `<div class="spot-rule-note">${escapeHtml(waveNote)}</div>` +
    `<div class="spot-rule-grid">` +
    buildSpotRuleCard("wind", config.wind) +
    buildSpotRuleCard("wave", waveDescriptor) +
    `</div>` +
    `</div>`
  );
}

function formatResolutions(summary) {
  const matches = summary.match(/PT\d+[MH]/g) || [];
  return [...new Set(matches)];
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
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

  const saturation = lightness > 0.5
    ? delta / (2 - max - min)
    : delta / (max + min);

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

function windCellColor(speedMs) {
  if (!Number.isFinite(speedMs)) {
    return "rgba(248, 250, 252, 0.9)";
  }
  return rgbCss(interpolateWindColor(msToKnots(speedMs), WINDGURU_ADJUSTED_PALETTE), 0.66);
}

function windHighlightColor(speedMs) {
  if (!Number.isFinite(speedMs)) {
    return "transparent";
  }
  return rgbCss(interpolateWindColor(msToKnots(speedMs), WINDGURU_ADJUSTED_PALETTE), 0.66);
}

function windHighlightStyle(speedMs) {
  return `background:${windHighlightColor(speedMs)}`;
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

function formatWindValue(speed, gust) {
  if (!Number.isFinite(speed) && !Number.isFinite(gust)) {
    return "-";
  }
  const speedText = formatStreamlitInteger(speed);
  const gustText = formatStreamlitInteger(gust);
  if (speedText === "-") {
    return gustText;
  }
  if (gustText === "-") {
    return speedText;
  }
  return `${speedText}(${gustText})`;
}

function unitHtml(unit) {
  return `<span class="forecast-unit">${escapeHtml(unit)}</span>`;
}

function formatClock(date) {
  const parts = getOsloParts(date);
  return `${String(parts.hour).padStart(2, "0")}:${String(parts.minute).padStart(2, "0")}`;
}

function formatDayMonth(date) {
  const parts = getOsloParts(date);
  return `${parts.day}. ${MONTHS_NO[parts.month - 1]}`;
}

function formatMeters(value) {
  return formatNoNumber(value, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function capitalize(value) {
  if (!value) return "";
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function degToArrowHtml(deg) {
  if (!Number.isFinite(deg)) {
    return '<span class="forecast-arrow-empty">-</span>';
  }
  const rotation = (deg + 180) % 360;
  return `<span class="forecast-arrow" style="transform:rotate(${rotation.toFixed(0)}deg)">↑</span>`;
}

function swellHeightClass(value) {
  if (!Number.isFinite(value)) return "";
  if (value > 1.8) return "forecast-height--strong";
  if (value < 0.8) return "forecast-height--faint";
  return "";
}

function swellPeriodClass(value) {
  if (!Number.isFinite(value)) return "";
  if (value > 7) return "forecast-period--strong";
  if (value < 6) return "forecast-period--faint";
  return "";
}

function forecastValueWithUnit(value, unit, formatter) {
  const text = formatter(value);
  if (text === "-") return "-";
  return `${text}${unitHtml(unit)}`;
}

function renderSwellCell(swell) {
  if (!swell) {
    return "-";
  }
  const heightValue = forecastValueWithUnit(swell.heightM, "m", formatStreamlitDecimal);
  const periodValue = forecastValueWithUnit(swell.periodS, "s", formatStreamlitInteger);
  return (
    `<div class="forecast-swell-inner">` +
    `<span class="forecast-height ${swellHeightClass(swell.heightM)}">${heightValue}</span>` +
    `<span class="forecast-period ${swellPeriodClass(swell.periodS)}">${periodValue}</span>` +
    `<span class="forecast-dir">${degToArrowHtml(swell.dirDeg)}</span>` +
    `</div>`
  );
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

function swellSignalCountForRow(row) {
  const swells = Array.isArray(row.swells) ? row.swells : [];
  return swells.reduce((maxCount, swell) => (
    Math.max(maxCount, swellSignalCountForSwell(swell))
  ), 0);
}

function bestSignalSwellForRow(row) {
  const swells = Array.isArray(row.swells) ? row.swells : [];
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
  if (Number.isFinite(row.windGustMs)) {
    return row.windGustMs;
  }
  return row.windSpeedMs;
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
  const windGood = windDirectionLooksGood(spotName, row.windDirDeg);
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
  const count = swellSignalCountForRow(row);
  let src = "symbols/bars-0.svg";
  let alt = "0 surf bars";
  if (count > 0) {
    const color = swellSignalColorForRow(row, spotName);
    src = `symbols/bars-${color}-${count}.svg`;
    alt = `${count} ${color} surf bars`;
  }
  return (
    `<span class="forecast-signal-wrap">` +
    `<img class="forecast-signal-symbol" src="${src}" alt="${escapeHtml(alt)}" draggable="false">` +
    `</span>`
  );
}

function renderWindCell(row, showGust) {
  const speed = row.windSpeedMs;
  const gust = showGust ? row.windGustMs : Number.NaN;
  const speedText = formatStreamlitInteger(speed);
  const gustText = formatStreamlitInteger(gust);
  let windValueHtml = "-";

  if (speedText !== "-" && gustText !== "-") {
    windValueHtml =
      `<span class="forecast-wind-highlight" style="${windHighlightStyle(gust)}">` +
      `<span class="forecast-wind-speed">${escapeHtml(speedText)}</span>` +
      `<span class="forecast-wind-bracket forecast-wind-bracket-muted">(</span>` +
      `<span class="forecast-wind-gust-value">${escapeHtml(gustText)}</span>` +
      `<span class="forecast-wind-bracket forecast-wind-bracket-muted">)</span>` +
      `</span>` +
      unitHtml("m/s");
  } else if (speedText !== "-") {
    windValueHtml =
      `<span class="forecast-wind-highlight" style="${windHighlightStyle(speed)}">${escapeHtml(speedText)}</span>` +
      unitHtml("m/s");
  } else if (gustText !== "-") {
    windValueHtml =
      `<span class="forecast-wind-highlight" style="${windHighlightStyle(gust)}">${escapeHtml(gustText)}</span>` +
      unitHtml("m/s");
  }

  return (
    `<div class="forecast-wind-inner">` +
    `<span class="forecast-wind-value">${windValueHtml}</span>` +
    `<span class="forecast-wind-dir">${degToArrowHtml(row.windDirDeg)}</span>` +
    `</div>`
  );
}

function renderExtraCell(value, unit, formatter) {
  const text = formatter(value);
  if (text === "-") return "-";
  return `<span class="forecast-extra">${text}${unitHtml(unit)}</span>`;
}

function formatForecastHourLabel(value) {
  if (typeof value !== "string" || !value) return "-";
  if (value.includes(":")) return value.slice(0, 2);
  return value;
}

function buildForecastTable(day, spotName) {
  const showSignalColumn = true;
  const showGust = Boolean(day.showGust);
  const previewRows = Array.isArray(day.previewRows) ? day.previewRows : [];
  const previewTimes = new Set(previewRows.map((row) => row.timeLocal));
  const detailRows = Array.isArray(day.detailRows) && day.detailRows.length
    ? day.detailRows
    : previewRows;
  const detailTimes = new Set(detailRows.map((row) => row.timeLocal));
  const rowByTime = new Map();

  detailRows.forEach((row) => {
    rowByTime.set(row.timeLocal, row);
  });
  previewRows.forEach((row) => {
    if (!rowByTime.has(row.timeLocal)) {
      rowByTime.set(row.timeLocal, row);
    }
  });

  const mergedRows = [...rowByTime.values()].sort((left, right) => (
    String(left.timeLocal).localeCompare(String(right.timeLocal), "no")
  ));

  const bodyRows = mergedRows.map((row) => {
    const swells = Array.isArray(row.swells) ? row.swells : [];
    const classNames = ["forecast-row"];
    if (detailTimes.has(row.timeLocal)) {
      classNames.push("forecast-row--detail");
    }
    if (previewTimes.has(row.timeLocal)) {
      classNames.push("forecast-row--preview");
      if (!detailTimes.has(row.timeLocal)) {
        classNames.push("forecast-row--preview-only");
      }
    }
    const cells = [
      `<td class="forecast-time forecast-divider-right">${escapeHtml(formatForecastHourLabel(row.timeLocal))}</td>`,
      ...(showSignalColumn ? [`<td class="forecast-signal-cell forecast-divider-left forecast-divider-right">${renderSwellSignalCell(row, spotName)}</td>`] : []),
      `<td class="forecast-wind-cell forecast-divider-left forecast-divider-right">${renderWindCell(row, showGust)}</td>`,
      `<td class="forecast-swell-cell forecast-swell-cell--primary forecast-divider-left forecast-divider-right">${renderSwellCell(swells[0])}</td>`,
      `<td class="forecast-swell-cell forecast-swell-cell--secondary forecast-divider-left forecast-divider-right">${renderSwellCell(swells[1])}</td>`,
      `<td class="forecast-swell-cell forecast-swell-cell--secondary forecast-divider-left forecast-divider-right">${renderSwellCell(swells[2])}</td>`,
      `<td class="forecast-divider-left">${renderExtraCell(row.precipMm, "mm", formatStreamlitDecimal)}</td>`,
      `<td>${renderExtraCell(row.airTempC, "°C", formatStreamlitInteger)}</td>`,
      `<td>${renderExtraCell(row.cloudPct, "%", formatStreamlitInteger)}</td>`,
    ];

    return `<tr class="${classNames.join(" ")}">${cells.join("")}</tr>`;
  }).join("");

  return (
    `<div class="forecast-scroll">` +
    `<table class="forecast-table">` +
    `<thead><tr>` +
    `<th>Tid</th>` +
    (showSignalColumn ? `<th class="forecast-signal-head">Surf</th>` : "") +
    `<th>Vind</th>` +
    `<th>Primærswell</th>` +
    `<th colspan="2">Sekundærswell</th>` +
    `<th>Nedbor</th>` +
    `<th>Luft</th>` +
    `<th>Sky</th>` +
    `</tr></thead>` +
    `<tbody>${bodyRows}</tbody>` +
    `</table>` +
    `</div>`
  );
}

function forecastEntryForSpot(spotName) {
  const spots = NOAA_FORECAST_DATA && NOAA_FORECAST_DATA.spots;
  if (!spots) return null;
  return spots[spotName] || null;
}

function liveWindKey(source) {
  return `${source.name}__${source.linkedSpot}`;
}

function liveWindEntryForSource(source) {
  const sources = LIVE_WIND_DATA && LIVE_WIND_DATA.sources;
  if (!sources) return null;
  return sources[liveWindKey(source)] || null;
}

function renderLiveDirection(deg) {
  if (!Number.isFinite(deg)) return "-";
  return (
    `<span class="live-wind-dir">` +
    `${degToArrowHtml(deg)}` +
    `<span class="live-wind-deg">${escapeHtml(formatStreamlitInteger(deg))}°</span>` +
    `</span>`
  );
}

function buildLiveWindBlock(source) {
  if (source.provider !== "Frost") return "";
  const entry = liveWindEntryForSource(source);
  if (!entry) return "";
  const rows = Array.isArray(entry.rows) ? entry.rows : [];
  if (!rows.length) {
    return `<div class="live-wind-block"><div class="live-wind-empty">Fant ingen live-vinddata for denne stasjonen akkurat na.</div></div>`;
  }

  const metaParts = [`Siste ${rows.length} rader`];
  if (entry.windResolution) {
    metaParts.push(`vind/retning ${entry.windResolution}`);
  }
  if (entry.gustResolution) {
    metaParts.push(`kast ${entry.gustResolution}`);
  }
  if (entry.latestTimeUtc) {
    const latest = new Date(entry.latestTimeUtc);
    metaParts.push(`oppdatert ${formatDayMonth(latest)} ${formatClock(latest)}`);
  }

  const bodyRows = rows.map((row) => (
    `<tr>` +
    `<td class="live-wind-time">${escapeHtml(`${formatDayMonth(new Date(row.timeUtc))} ${formatClock(new Date(row.timeUtc))}`)}</td>` +
    `<td class="live-wind-value-cell" style="background:${windCellColor(row.windSpeedMs)}"><span class="live-wind-value">${forecastValueWithUnit(row.windSpeedMs, "m/s", formatStreamlitDecimal)}</span></td>` +
    `<td class="live-wind-value-cell" style="background:${windCellColor(Number.isFinite(row.windGustMs) ? row.windGustMs : row.windSpeedMs)}"><span class="live-wind-value">${forecastValueWithUnit(row.windGustMs, "m/s", formatStreamlitDecimal)}</span></td>` +
    `<td>${renderLiveDirection(row.windDirDeg)}</td>` +
    `</tr>`
  )).join("");

  return (
    `<div class="live-wind-block">` +
    `<div class="popup-sub" style="margin:0 0 6px">Live vind</div>` +
    `<div class="live-wind-meta">${escapeHtml(metaParts.join(" | "))}</div>` +
    `<div class="live-wind-scroll">` +
    `<table class="live-wind-table">` +
    `<thead><tr><th>Tid</th><th>Vind</th><th>Kast</th><th>Retning</th></tr></thead>` +
    `<tbody>${bodyRows}</tbody>` +
    `</table>` +
    `</div>` +
    `</div>`
  );
}

function buildNoaaForecastBlock(spot) {
  const forecastEntry = forecastEntryForSpot(spot.name);
  if (!forecastEntry) {
    return "";
  }
  const days = Array.isArray(forecastEntry.days) ? forecastEntry.days : [];
  if (!days.length) {
    return `<div class="forecast-block"><div class="forecast-empty">Fant ikke varseldata for ${escapeHtml(displaySpotName(spot.name))} akkurat na.</div></div>`;
  }

  const metaParts = [];
  if (forecastEntry.yrUpdatedAtUtc) {
    metaParts.push(`Yr oppdatert ${formatDayMonth(new Date(forecastEntry.yrUpdatedAtUtc))} ${formatClock(new Date(forecastEntry.yrUpdatedAtUtc))}`);
  }
  if (NOAA_FORECAST_DATA.noaaRunId) {
    metaParts.push(`NOAA run ${NOAA_FORECAST_DATA.noaaRunId}`);
  }

  const daySections = days.map((day) => {
    const collapsedLabel = day.collapsedLabel || "Trykk for alle tider";
    const expandedLabel = "Trykk i tabellen for aa lukke";
    return (
      `<section class="forecast-day" data-expanded="false">` +
      `<button class="forecast-day-toggle" type="button" aria-expanded="false">` +
      `<div class="forecast-day-head">` +
      `<span class="forecast-day-title">${escapeHtml(day.title)}</span>` +
      `<span class="forecast-day-step" data-collapsed-label="${escapeHtml(collapsedLabel)}" data-expanded-label="${escapeHtml(expandedLabel)}">${escapeHtml(collapsedLabel)}</span>` +
      `</div>` +
      `</button>` +
      `<div class="forecast-hint">Sveip til siden for nedbor, lufttemperatur og skydekke.</div>` +
      buildForecastTable(day, spot.name) +
      `</section>`
    );
  }).join("");

  return (
    `<div class="forecast-block">` +
    `<div class="popup-sub" style="margin:0 0 6px">Varsel</div>` +
    (metaParts.length ? `<div class="forecast-meta">${escapeHtml(metaParts.join(" | "))}</div>` : "") +
    daySections +
    `</div>`
  );
}

function setForecastDayExpanded(dayEl, expanded) {
  if (!dayEl) return;
  dayEl.classList.toggle("forecast-day--expanded", expanded);
  dayEl.dataset.expanded = expanded ? "true" : "false";
  const toggleButton = dayEl.querySelector(".forecast-day-toggle");
  if (toggleButton) {
    toggleButton.setAttribute("aria-expanded", expanded ? "true" : "false");
  }
  const step = dayEl.querySelector(".forecast-day-step");
  if (step) {
    step.textContent = expanded ? (step.dataset.expandedLabel || "") : (step.dataset.collapsedLabel || "");
  }
}

function toggleForecastDay(dayEl) {
  if (!dayEl) return;
  setForecastDayExpanded(dayEl, !dayEl.classList.contains("forecast-day--expanded"));
}

function pointerMoved(startValue, endValue) {
  return Number.isFinite(startValue) && Number.isFinite(endValue) && Math.abs(endValue - startValue) > 6;
}

document.addEventListener("pointerdown", (event) => {
  const scroll = event.target.closest(".forecast-scroll");
  if (!scroll) return;
  scroll.dataset.pointerX = String(event.clientX);
  scroll.dataset.pointerY = String(event.clientY);
  scroll.dataset.pointerScrollLeft = String(scroll.scrollLeft);
}, true);

document.addEventListener("click", (event) => {
  const toggleButton = event.target.closest(".forecast-day-toggle");
  if (toggleButton) {
    event.preventDefault();
    toggleForecastDay(toggleButton.closest(".forecast-day"));
    return;
  }

  const scroll = event.target.closest(".forecast-scroll");
  if (!scroll) return;
  const dayEl = scroll.closest(".forecast-day");
  if (!dayEl || !dayEl.classList.contains("forecast-day--expanded")) return;

  const startX = Number(scroll.dataset.pointerX);
  const startY = Number(scroll.dataset.pointerY);
  const startScrollLeft = Number(scroll.dataset.pointerScrollLeft);
  const movedPointer = pointerMoved(startX, event.clientX) || pointerMoved(startY, event.clientY);
  const movedScroll = Number.isFinite(startScrollLeft) && Math.abs(scroll.scrollLeft - startScrollLeft) > 6;
  if (movedPointer || movedScroll) return;

  setForecastDayExpanded(dayEl, false);
}, true);

function formatDayTitle(date, index) {
  if (index === 0) return `I dag ${formatDayMonth(date)}`;
  if (index === 1) return `I morgen ${formatDayMonth(date)}`;
  return `${capitalize(weekdayFormatterNo.format(date))} ${formatDayMonth(date)}`;
}

function tideDayCount() {
  const count = Number(TIDE_DATA.dayCount);
  return Number.isFinite(count) && count > 0 ? count : 5;
}

function tideBaseDate() {
  return new Date(TIDE_DATA.startUtc || Date.now());
}

function tideDayBounds(index) {
  const baseParts = getOsloParts(tideBaseDate());
  return {
    start: makeOsloDate(baseParts.year, baseParts.month, baseParts.day + index, 0),
    end: makeOsloDate(baseParts.year, baseParts.month, baseParts.day + index + 1, 0),
  };
}

function lightFillColor(key) {
  if (key === "dark") return "rgba(15, 23, 42, 0.16)";
  if (key === "civil") return "rgba(148, 163, 184, 0.18)";
  return "rgba(255, 255, 255, 0.92)";
}

function getTideEntry(spotName) {
  const spots = TIDE_DATA.spots || {};
  const entry = spots[spotName];
  if (!entry) return null;
  if (!entry.parsedRows) {
    entry.parsedRows = (entry.rows || []).map((row) => ({
      date: new Date(row.timeUtc),
      astronomical: Number.isFinite(row.astronomical) ? row.astronomical : null,
    }));
  }
  if (!entry.parsedDkssRows) {
    entry.parsedDkssRows = (((entry.dkss || {}).rows) || []).map((row) => ({
      date: new Date(row.timeUtc),
      deviation: Number.isFinite(row.deviation) ? row.deviation : null,
      total: Number.isFinite(row.total) ? row.total : null,
    }));
  }
  if (!entry.parsedEvents) {
    entry.parsedEvents = (entry.events || []).map((event) => ({
      date: new Date(event.timeUtc),
      kind: event.kind,
      astronomical: Number.isFinite(event.astronomical) ? event.astronomical : null,
    }));
  }
  return entry;
}

function tideRowsForDay(entry, index) {
  const bounds = tideDayBounds(index);
  const rows = entry.parsedRows.filter((row) => row.date >= bounds.start && row.date < bounds.end);
  return {
    start: bounds.start,
    end: bounds.end,
    rows,
  };
}

function dkssRowsForDay(entry, index) {
  const bounds = tideDayBounds(index);
  const rows = (entry.parsedDkssRows || []).filter((row) => row.date >= bounds.start && row.date < bounds.end);
  return {
    start: bounds.start,
    end: bounds.end,
    rows,
  };
}

function tideValueRange(seriesDefs) {
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
    return { min: rawMin - 0.1, max: rawMax + 0.1 };
  }
  const padding = Math.max(0.14, (rawMax - rawMin) * 0.35);
  return {
    min: rawMin - padding,
    max: rawMax + padding,
  };
}

function interpolateSeriesValue(rows, valueKey, targetDate, maxGapMs = 2.5 * 3600 * 1000) {
  const finiteRows = (rows || []).filter((row) => Number.isFinite(row[valueKey]));
  if (!finiteRows.length || !(targetDate instanceof Date)) return null;
  const targetMs = targetDate.getTime();
  let previous = null;
  let next = null;

  for (const row of finiteRows) {
    const rowMs = row.date.getTime();
    if (rowMs <= targetMs) {
      previous = row;
    }
    if (rowMs >= targetMs) {
      next = row;
      break;
    }
  }

  if (previous && next) {
    const prevMs = previous.date.getTime();
    const nextMs = next.date.getTime();
    const spanMs = nextMs - prevMs;
    if (spanMs === 0) {
      return previous[valueKey];
    }
    if (spanMs <= maxGapMs) {
      const ratio = (targetMs - prevMs) / spanMs;
      return previous[valueKey] + (next[valueKey] - previous[valueKey]) * ratio;
    }
  }

  const candidates = [previous, next]
    .filter(Boolean)
    .map((row) => ({ row, delta: Math.abs(row.date.getTime() - targetMs) }))
    .sort((a, b) => a.delta - b.delta);
  if (!candidates.length || candidates[0].delta > maxGapMs) {
    return null;
  }
  return candidates[0].row[valueKey];
}

function tideEventLabel(astronomicalValue, secondaryValue) {
  const astronomicalText = formatMeters(astronomicalValue);
  if (Number.isFinite(secondaryValue)) {
    return `${astronomicalText} (${formatMeters(secondaryValue)}) m`;
  }
  return `${astronomicalText} m`;
}

function buildSvgPath(rows, valueKey, xFor, yFor) {
  let path = "";
  let open = false;
  rows.forEach((row) => {
    const value = row[valueKey];
    if (!Number.isFinite(value)) {
      open = false;
      return;
    }
    const command = open ? "L" : "M";
    path += `${command}${xFor(row.date).toFixed(1)},${yFor(value).toFixed(1)} `;
    open = true;
  });
  return path.trim();
}

function buildSmoothSvgPath(rows, valueKey, xFor, yFor, maxGapMs) {
  const segments = [];
  let currentSegment = [];

  rows.forEach((row) => {
    const value = row[valueKey];
    if (!Number.isFinite(value)) {
      if (currentSegment.length) {
        segments.push(currentSegment);
        currentSegment = [];
      }
      return;
    }
    const point = {
      x: xFor(row.date),
      y: yFor(value),
      date: row.date,
    };
    const previous = currentSegment[currentSegment.length - 1];
    if (
      previous &&
      Number.isFinite(maxGapMs) &&
      Math.abs(point.date.getTime() - previous.date.getTime()) > maxGapMs
    ) {
      segments.push(currentSegment);
      currentSegment = [];
    }
    currentSegment.push(point);
  });

  if (currentSegment.length) {
    segments.push(currentSegment);
  }

  return segments.map((points) => {
    if (points.length <= 2) {
      return points.map((point, index) => `${index === 0 ? "M" : "L"}${point.x.toFixed(1)},${point.y.toFixed(1)}`).join(" ");
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
  }).join(" ");
}

function tideEventsForDay(entry, start, end) {
  return (entry.parsedEvents || []).filter((event) => (
    event.date >= start &&
    event.date < end &&
    Number.isFinite(event.astronomical) &&
    (event.kind === "high" || event.kind === "low")
  ));
}

function buildLightBands(start, end, lat, lon) {
  const segments = [];
  let segmentStart = start.getTime();
  let segmentState = lightState(start, lat, lon).key;
  const stepMs = 10 * 60 * 1000;
  for (let ts = start.getTime() + stepMs; ts <= end.getTime(); ts += stepMs) {
    const sampleDate = new Date(Math.min(ts, end.getTime() - 60 * 1000));
    const nextState = lightState(sampleDate, lat, lon).key;
    if (nextState === segmentState) continue;
    segments.push({
      key: segmentState,
      start: new Date(segmentStart),
      end: new Date(ts),
    });
    segmentStart = ts;
    segmentState = nextState;
  }
  segments.push({
    key: segmentState,
    start: new Date(segmentStart),
    end,
  });
  return segments;
}

function buildTideSvg(entry, options) {
  const {
    astronomicalRows,
    secondaryRows = [],
    secondaryKey = null,
    secondaryColor = null,
    smoothSecondary = false,
    start,
    end,
    lat,
    lon,
  } = options;
  const range = tideValueRange([
    { rows: astronomicalRows, valueKey: "astronomical" },
    ...(secondaryKey ? [{ rows: secondaryRows, valueKey: secondaryKey }] : []),
  ]);
  const plotLeft = TIDE_GRAPH.marginLeft;
  const plotTop = TIDE_GRAPH.marginTop;
  const plotRight = TIDE_GRAPH.width - TIDE_GRAPH.marginRight;
  const plotBottom = TIDE_GRAPH.height - TIDE_GRAPH.marginBottom;
  const plotWidth = plotRight - plotLeft;
  const plotHeight = plotBottom - plotTop;
  const daySpanMs = end.getTime() - start.getTime();
  const xFor = (date) => plotLeft + ((date.getTime() - start.getTime()) / daySpanMs) * plotWidth;
  const yFor = (value) => plotTop + ((range.max - value) / (range.max - range.min)) * plotHeight;

  const bandsSvg = buildLightBands(start, end, lat, lon)
    .map((segment) => {
      const x = xFor(segment.start);
      const width = Math.max(0.5, xFor(segment.end) - x);
      return (
        `<rect x="${x.toFixed(1)}" y="${plotTop}" width="${width.toFixed(1)}" height="${plotHeight}" fill="${lightFillColor(segment.key)}"></rect>`
      );
    })
    .join("");

  const axisY = plotBottom;
  const zeroVisible = range.min < 0 && range.max > 0;
  const zeroLine = zeroVisible
    ? `<line x1="${plotLeft}" y1="${yFor(0).toFixed(1)}" x2="${plotRight}" y2="${yFor(0).toFixed(1)}" stroke="rgba(148,163,184,0.6)" stroke-dasharray="3 4" stroke-width="1"></line>`
    : "";

  const astronomicalPath = buildSvgPath(astronomicalRows, "astronomical", xFor, yFor);
  const secondaryPath = secondaryKey
    ? (
      smoothSecondary
        ? buildSmoothSvgPath(secondaryRows, secondaryKey, xFor, yFor, 2.1 * 3600 * 1000)
        : buildSvgPath(secondaryRows, secondaryKey, xFor, yFor)
    )
    : "";
  const extremaSvg = tideEventsForDay(entry, start, end)
    .map((item) => {
      const x = Math.max(plotLeft + 32, Math.min(plotRight - 32, xFor(item.date)));
      const astronomicalValue = item.astronomical;
      const secondaryValue = secondaryKey
        ? interpolateSeriesValue(secondaryRows, secondaryKey, item.date)
        : null;
      const anchorValue = Number.isFinite(secondaryValue)
        ? (item.kind === "high"
          ? Math.max(astronomicalValue, secondaryValue)
          : Math.min(astronomicalValue, secondaryValue))
        : astronomicalValue;
      const anchorY = yFor(anchorValue);
      const timeY = item.kind === "high"
        ? Math.max(18, anchorY - 28)
        : Math.min(TIDE_GRAPH.height - 34, anchorY + 18);
      const valueY = item.kind === "high"
        ? Math.max(32, anchorY - 13)
        : Math.min(TIDE_GRAPH.height - 18, timeY + 14);
      return (
        `<text x="${x.toFixed(1)}" y="${timeY.toFixed(1)}" text-anchor="middle" font-size="11.5" font-weight="700" fill="#0f172a" style="paint-order:stroke;stroke:rgba(248,250,252,0.96);stroke-width:3px;stroke-linejoin:round">${escapeHtml(formatClock(item.date))}</text>` +
        `<text x="${x.toFixed(1)}" y="${valueY.toFixed(1)}" text-anchor="middle" font-size="11" font-weight="600" fill="#0f172a" style="paint-order:stroke;stroke:rgba(248,250,252,0.96);stroke-width:3px;stroke-linejoin:round">${escapeHtml(tideEventLabel(astronomicalValue, secondaryValue))}</text>`
      );
    })
    .join("");

  const ticksSvg = Array.from({ length: 8 }, (_, index) => index * 3)
    .map((hour) => {
      const x = plotLeft + (hour / 24) * plotWidth;
      return (
        `<line x1="${x.toFixed(1)}" y1="${plotBottom}" x2="${x.toFixed(1)}" y2="${plotBottom + 5}" stroke="${TIDE_GRAPH.axisColor}" stroke-width="1"></line>` +
        `<text x="${x.toFixed(1)}" y="${plotBottom + 18}" text-anchor="middle" font-size="10.5" fill="#475569">${String(hour).padStart(2, "0")}</text>`
      );
    })
    .join("");

  return (
    `<svg viewBox="0 0 ${TIDE_GRAPH.width} ${TIDE_GRAPH.height}" aria-hidden="true">` +
    `<rect x="${plotLeft}" y="${plotTop}" width="${plotWidth}" height="${plotHeight}" rx="10" ry="10" fill="rgba(255,255,255,0.9)" stroke="rgba(148,163,184,0.22)"></rect>` +
    bandsSvg +
    zeroLine +
    `<path d="${astronomicalPath}" fill="none" stroke="${TIDE_GRAPH.astronomicalColor}" stroke-width="2"></path>` +
    (secondaryPath && secondaryColor ? `<path d="${secondaryPath}" fill="none" stroke="${secondaryColor}" stroke-width="2"></path>` : "") +
    `<line x1="${plotLeft}" y1="${axisY}" x2="${plotRight}" y2="${axisY}" stroke="${TIDE_GRAPH.axisColor}" stroke-width="1"></line>` +
    ticksSvg +
    extremaSvg +
    `</svg>`
  );
}

function buildTideBlock(source) {
  if (!["DMI DKSS", "Kartverket tidevann"].includes(source.provider)) return "";
  const entry = getTideEntry(source.linkedSpot);
  if (!entry || !entry.parsedRows.length) {
    return `<div class="tide-block"><div class="tide-empty">Fant ingen tide-data for denne popupen akkurat na.</div></div>`;
  }

  const isDkss = source.provider === "DMI DKSS";
  const dkssMeta = entry.dkss || null;
  const hasDkssRows = isDkss && (entry.parsedDkssRows || []).length > 0;
  if (isDkss && !hasDkssRows) {
    return (
      `<div class="tide-block">` +
      `<div class="popup-sub" style="margin:0 0 6px">Tidevann</div>` +
      `<div class="tide-empty">Fant ingen DKSS-serie for dette punktet akkurat na.</div>` +
      `</div>`
    );
  }

  const panels = [];
  for (let index = 0; index < tideDayCount(); index += 1) {
    const astronomicalDay = tideRowsForDay(entry, index);
    const dkssDay = isDkss ? dkssRowsForDay(entry, index) : { rows: [] };
    if (!astronomicalDay.rows.length && !dkssDay.rows.length) continue;
    panels.push(
      `<div class="tide-day">` +
      `<div class="tide-day-title">${formatDayTitle(astronomicalDay.start, index)}</div>` +
      buildTideSvg(entry, {
        astronomicalRows: astronomicalDay.rows,
        secondaryRows: dkssDay.rows,
        secondaryKey: isDkss ? "total" : null,
        secondaryColor: isDkss ? TIDE_GRAPH.dkssColor : null,
        smoothSecondary: isDkss,
        start: astronomicalDay.start,
        end: astronomicalDay.end,
        lat: entry.spotLat || entry.stationLat,
        lon: entry.spotLon || entry.stationLon,
      }) +
      `</div>`
    );
  }

  const note = isDkss
    ? (
      dkssMeta && dkssMeta.throughUtc
        ? `Oransje kurve viser astronomisk tide pluss DKSS sea-mean-deviation til ${formatDayMonth(new Date(dkssMeta.throughUtc))} ${formatClock(new Date(dkssMeta.throughUtc))}. High/low-markeringene følger offisiell tide-tabell fra Kartverket.`
        : "Oransje kurve viser astronomisk tide pluss DKSS sea-mean-deviation. High/low-markeringene følger offisiell tide-tabell fra Kartverket."
    )
    : "Kun astronomisk tide fra valgt Kartverket-stasjon vises i denne popupen.";
  const meta = isDkss
    ? `Kartverket tidevann fra <b>${escapeHtml(entry.stationName)}</b> kombinert med DKSS ved <b>${escapeHtml(dkssMeta.sourceName || source.name)}</b>.`
    : `Kartverket tidevann fra <b>${escapeHtml(entry.stationName)}</b>.`;

  return (
    `<div class="tide-block">` +
    `<div class="popup-sub" style="margin:0 0 6px">Tidevann</div>` +
    `<div class="tide-meta">${meta}</div>` +
    `<div class="tide-legend">` +
    `<span class="tide-legend-item"><span class="tide-legend-line" style="border-top-color:${TIDE_GRAPH.astronomicalColor}"></span>Astronomisk tide</span>` +
    (isDkss ? `<span class="tide-legend-item"><span class="tide-legend-line" style="border-top-color:${TIDE_GRAPH.dkssColor}"></span>DKSS-justert vannstand</span>` : "") +
    `</div>` +
    panels.join("") +
    `<div class="tide-note">${escapeHtml(note)}</div>` +
    `</div>`
  );
}

function buildSourcePopup(source, relationHtml) {
  const linkedSpotLabel = displaySpotName(source.linkedSpot);
  const title = displaySourceName(source);
  const summary = displaySourceSummary(source);
  const ruleBlock = source.provider === "NOAA vind" ? buildSpotRuleBlock(source.linkedSpot) : "";
  return (
    `<div class="popup-title">${escapeHtml(title)}</div>` +
    `<div class="popup-sub">${source.provider}</div>` +
    ruleBlock +
    `<div>Knyttet til: ${escapeHtml(linkedSpotLabel)}</div>` +
    relationHtml +
    `<div>Lat/lon: ${source.lat.toFixed(4)}, ${source.lon.toFixed(4)}</div>` +
    `<div style="margin-top:6px">${escapeHtml(summary)}</div>` +
    buildSourceDetails(source) +
    buildWindCompareBlock(source) +
    buildLiveWindBlock(source) +
    buildTideBlock(source)
  );
}

function sourcePopupOptions(source) {
  const hasTide = ["DMI DKSS", "Kartverket tidevann"].includes(source.provider) && Boolean(getTideEntry(source.linkedSpot));
  const hasLiveWind = source.provider === "Frost" && Boolean(liveWindEntryForSource(source));
  const hasCompare = ["DMI vind", "NOAA vind", "gfs atmos 0.25", "ICON-EU"].includes(source.provider) && Boolean(windCompareEntryForSource(source));
  if (!hasTide && !hasLiveWind && !hasCompare) return {};
  return {
    className: hasTide ? "tide-popup" : "forecast-popup",
    maxWidth: hasTide ? 980 : (hasCompare ? 1120 : 720),
  };
}

function renderInfoList(items) {
  if (!items.length) return "";
  return `<div style="margin-top:6px"><b>Tilgjengelig:</b><ul style="margin:4px 0 0 18px;padding:0">${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul></div>`;
}

function buildNoaaDetails(spot) {
  if (!spot.noaaUsed) return "";
  const items = [
    "WW og swell-kandidater behandles likt og rangeres samlet etter Hs × periode.",
    "Kun de 3 sterkeste systemene beholdes etter denne sorteringen.",
    "Et WW-system beholdes bare hvis det faktisk havner i topp 3.",
    "De 3 viste systemene presenteres ryddet med Hs (m), periode (s) og retning (grader).",
    "Vind i tabellen hentes fra et eget Yr-punkt, markert gult pa kartet.",
  ];
  return renderInfoList(items);
}

function windCompareEntryForSource(source) {
  if (!["DMI vind", "NOAA vind", "gfs atmos 0.25", "ICON-EU"].includes(source.provider)) return null;
  if (!window.WIND_COMPARE_DATA || !window.WIND_COMPARE_DATA.spots) return null;
  return window.WIND_COMPARE_DATA.spots[source.linkedSpot] || null;
}

function formatWindCompareMeasure(speedMs, gustMs, dirDeg) {
  const windValue = formatWindValue(speedMs, gustMs);
  const speedText = windValue === "-" ? "-" : `${escapeHtml(windValue)} m/s`;
  const dirText = Number.isFinite(dirDeg) ? `${escapeHtml(formatStreamlitInteger(dirDeg))}°` : "-";
  return `${speedText} / ${dirText}`;
}

function formatSignedDecimal(value) {
  if (!Number.isFinite(value)) return "-";
  const absText = formatNoNumber(Math.abs(value), {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
  if (Math.abs(value) < 0.05) return absText;
  return `${value > 0 ? "+" : "-"}${absText}`;
}

function formatSignedInteger(value) {
  if (!Number.isFinite(value)) return "-";
  const rounded = Math.round(value);
  if (rounded === 0) return "0";
  return `${rounded > 0 ? "+" : "-"}${Math.abs(rounded)}`;
}

function formatWindCompareDelta(speedDeltaMs, gustDeltaMs, dirDeltaDeg) {
  const speedText = formatSignedDecimal(speedDeltaMs);
  const gustText = formatSignedDecimal(gustDeltaMs);
  const dirText = Number.isFinite(dirDeltaDeg) ? `${escapeHtml(formatSignedInteger(dirDeltaDeg))}°` : "-";
  let windText = "-";
  if (speedText !== "-" && gustText !== "-") {
    windText = `${speedText}(${gustText}) m/s`;
  } else if (speedText !== "-") {
    windText = `${speedText} m/s`;
  } else if (gustText !== "-") {
    windText = `${gustText} m/s`;
  }
  return `${windText} / ${dirText}`;
}

function buildWindCompareBlock(source) {
  const entry = windCompareEntryForSource(source);
  if (!entry) return "";
  if (source.provider === "DMI vind" && source.status === "bad") return "";
  const samples = Array.isArray(entry.samples) ? entry.samples : [];
  if (!samples.length) return "";

  const metaParts = [];
  if (window.WIND_COMPARE_DATA?.gfsAtmosRunId) {
    metaParts.push(`GFS atmos ${escapeHtml(window.WIND_COMPARE_DATA.gfsAtmosRunId)}`);
  }
  if (window.WIND_COMPARE_DATA?.iconEuRunId) {
    metaParts.push(`ICON-EU ${escapeHtml(window.WIND_COMPARE_DATA.iconEuRunId)}`);
  }
  if (window.WIND_COMPARE_DATA?.gfsWaveRunId) {
    metaParts.push(`GFS wave ${escapeHtml(window.WIND_COMPARE_DATA.gfsWaveRunId)}`);
  } else if (window.WIND_COMPARE_DATA?.noaaRunId) {
    metaParts.push(`GFS wave ${escapeHtml(window.WIND_COMPARE_DATA.noaaRunId)}`);
  }
  if (entry.dmiCollection) {
    metaParts.push(entry.dmiCollection.toUpperCase().replaceAll("_", " "));
  }
  if (window.WIND_COMPARE_DATA?.startDateLocal && window.WIND_COMPARE_DATA?.endDateLocal) {
    metaParts.push(
      `${escapeHtml(window.WIND_COMPARE_DATA.startDateLocal)} til ${escapeHtml(window.WIND_COMPARE_DATA.endDateLocal)}`
    );
  }

  const bodyRows = samples.map((sample) => (
    `<tr>` +
    `<td>${escapeHtml(sample.label || "-")}</td>` +
    `<td>${formatWindCompareMeasure(sample.yr?.speedMs, sample.yr?.gustMs, sample.yr?.dirDeg)}</td>` +
    `<td>${formatWindCompareDelta(sample.deltaGfsAtmosVsYr?.speedMs, sample.deltaGfsAtmosVsYr?.gustMs, sample.deltaGfsAtmosVsYr?.dirDeg)}</td>` +
    `<td>${formatWindCompareDelta(sample.deltaIconEuVsYr?.speedMs, sample.deltaIconEuVsYr?.gustMs, sample.deltaIconEuVsYr?.dirDeg)}</td>` +
    `<td>${formatWindCompareDelta(sample.deltaGfsWaveVsYr?.speedMs, sample.deltaGfsWaveVsYr?.gustMs, sample.deltaGfsWaveVsYr?.dirDeg)}</td>` +
    `<td>${formatWindCompareDelta(sample.deltaDmiVsYr?.speedMs, sample.deltaDmiVsYr?.gustMs, sample.deltaDmiVsYr?.dirDeg)}</td>` +
    `</tr>`
  )).join("");

  const noteParts = [
    "To prover per dag der Yr har data. Hvis DMI gaar lenger enn Yr, fortsetter tabellen med to DMI-tider per dag videre.",
    "Yr-kolonnen viser speed(gust) og retning. De andre kolonnene viser bare avvik mot Yr i m/s og grader.",
    "GFS atmos 0.25 bruker 10 m U/V som regnes om til vindstyrke og vindretning i koden, og gust hentes fra surface GUST.",
    "ICON-EU bruker 10 m U/V som regnes om til vindstyrke og vindretning i koden, og gust hentes fra VMAX_10M.",
    "GFS wave bruker ws/wdir fra NOAA GFS Wave Arctic 9km og har ikke gust i dette uttrekket.",
  ];
  if (entry.dmiPoint) {
    noteParts.push("DMI WAM gir vindstyrke og retning, men ikke gust i dette uttrekket.");
  } else {
    noteParts.push("DMI-kolonnen er tom her fordi jeg ikke bruker et eget brukbart DMI-vindpunkt for dette spotet.");
  }

  return (
    `<div class="wind-compare-block">` +
    `<div class="popup-sub" style="margin:0 0 6px">Yr / GFS atmos / ICON-EU / GFS wave / DMI</div>` +
    (metaParts.length ? `<div class="wind-compare-meta">${metaParts.join(" | ")}</div>` : "") +
    `<div class="wind-compare-wrap">` +
    `<table class="wind-compare-table">` +
    `<thead><tr><th>Tid</th><th>Yr</th><th>GFS atmos</th><th>ICON-EU</th><th>GFS wave</th><th>DMI</th></tr></thead>` +
    `<tbody>${bodyRows}</tbody>` +
    `</table>` +
    `</div>` +
    `<div class="wind-compare-note">${noteParts.join(" ")}</div>` +
    `</div>`
  );
}

function buildSourceDetails(source) {
  const summary = source.summary || "";
  const resolutions = formatResolutions(summary);

  if (source.provider === "Frost") {
    const items = [
      `Datatype: tidsserie${resolutions.length ? ` i ${resolutions.join(", ")}` : ""}.`,
      "Vindstyrke og vindretning er tilgjengelig når serien finnes for stasjonen.",
      summary.toLowerCase().includes("kast") ? "Vindkast vises som maksverdi for perioden der gust-serie finnes." : "Vindkast er ikke bekreftet som tilgjengelig i denne serien.",
      resolutions.some((value) => value === "PT1H") ? "PT1H tolkes som aggregert timeverdi for timen, ikke et øyeblikkssnapshot." : "Periodeverdier tolkes som aggregert verdi for oppløsningen, ikke et øyeblikkssnapshot.",
      "PT10M/PT30M/PT1H/PT6H leses som periodeaggregerte observasjoner for den oppgitte perioden.",
    ];
    return renderInfoList(items);
  }

  if (source.provider === "Kystverket") {
    const items = [
      "Datatype: øyeblikksoppdatering / siste tilgjengelige sensorverdi.",
      "Vindstyrke og vindretning vises når sensoren svarer.",
      summary.includes("WINDGUS") || summary.toLowerCase().includes("kraftigste vindkast") ? "Vindkast vises som siste tilgjengelige gust-felt når det finnes." : "Vindkast er ikke bekreftet i siste svar for denne stasjonen.",
      summary.includes("WINDGUSDIR") ? "Vindkastretning finnes i denne kilden når feltet svarer." : "Vindkastretning er ikke bekreftet i denne kilden akkurat nå.",
    ];
    return renderInfoList(items);
  }

  if (source.provider === "DMI DKSS") {
    return renderInfoList([
      "Testpunkt for DKSS sea-mean-deviation.",
      "Brukes som kontrollpunkt for valgt gridcelle og presenteres som modellert vannstandsavvik.",
      "Tideblokken viser astronomisk tide fra valgt Kartverket-stasjon pluss DKSS-avvik ved dette punktet.",
    ]);
  }

  if (source.provider === "Kartverket tidevann") {
    return renderInfoList([
      "Datatype: predikert tidevann ved tidevannsstasjonen.",
      "Vises som én valgt permanent Kartverket-stasjon per spot.",
      "Denne popupen viser kun astronomisk tide og offisielle high/low fra valgt stasjon.",
    ]);
  }

  if (source.provider === "Yr") {
    return renderInfoList([
      "Datatype: Locationforecast punktvarsel fra Yr/MET for dette koordinatpunktet.",
      "Vindtabellen under NOAA-popupen bruker dette punktet for vind, retning og gust nar gust finnes.",
      "Tabellen viser bare faktiske Yr-tidspunkter. Nar opplosningen blir grovere, vises bare de tilgjengelige tidene.",
    ]);
  }

  if (source.provider === "NOAA vind") {
    return renderInfoList([
      "Datatype: NOAA GFS Wave Arctic 9km vind fra naermeste gridpunkt til Yr-vindpunktet.",
      "Her brukes feltene ws og wdir fra samme arctic-wave-grib som bolgevisningen bygger pa.",
      "Dette uttrekket har ikke gust-felt, sa NOAA-kolonnen viser bare styrke og retning.",
    ]);
  }

  if (source.provider === "gfs atmos 0.25") {
    return renderInfoList([
      "Datatype: NOAA NOMADS GFS 0.25 grader atmosfaere fra naermeste gridpunkt til Yr-vindpunktet.",
      "Vind hentes som 10 m UGRD/VGRD og regnes om til styrke og retning i koden.",
      "Gust hentes fra surface GUST. Ekstra felter som 2 m temperatur, visibility, skydekke, PRATE, APCP og PRMSL leses og lagres i samme uttrekk.",
    ]);
  }

  if (source.provider === "ICON-EU") {
    return renderInfoList([
      "Datatype: DWD ICON-EU fra naermeste regular lat/lon-gridpunkt til Yr-vindpunktet.",
      "Vind hentes som 10 m U/V og regnes om til styrke og retning i koden.",
      "Gust hentes fra VMAX_10M. ICON-EU gaar til +120 h, med timessteg til +78 h og 3-timerssteg videre.",
    ]);
  }

  if (source.provider === "DMI vind") {
    return renderInfoList([
      "Datatype: modellert vind fra naermeste DMI-gridpunkt for valgt collection.",
      "WAM-kildene gir vindstyrke og retning time for time, men ikke gust i dette uttrekket.",
      "Markoren viser faktisk DMI-gridpunkt, ikke bare onsket koordinat.",
    ]);
  }

  return "";
}

function buildSpotPopup(spot) {
  const noaaUsed = spot.noaaUsed;
  const displayName = displaySpotName(spot.name);
  if (noaaUsed) {
    return (
      `<div class="popup-title">${escapeHtml(displayName)}</div>` +
      `<div class="popup-sub">NOAA bolgedata</div>` +
      buildSpotRuleBlock(spot.name) +
      `<div>Koordinater: <b>${noaaUsed.lat.toFixed(4)}, ${noaaUsed.lon.toFixed(4)}</b></div>` +
      buildNoaaDetails(spot) +
      buildNoaaForecastBlock(spot)
    );
  }
  return (
    `<div class="popup-title">${escapeHtml(displayName)}</div>` +
    `<div class="popup-sub">Spot</div>` +
    `<div>Lat/lon: ${spot.lat.toFixed(4)}, ${spot.lon.toFixed(4)}</div>`
  );
}

function spotPopupOptions(spot) {
  const forecastEntry = forecastEntryForSpot(spot.name);
  const hasForecast = Boolean(forecastEntry && Array.isArray(forecastEntry.days) && forecastEntry.days.length);
  if (!hasForecast) return {};
  return {
    className: "forecast-popup",
    maxWidth: 860,
  };
}

function updateSpotMarkers(date) {
  spotMarkers.forEach(({ marker, spot }) => {
    if (spot.markerStyle === "noaa") {
      marker.setStyle({
        color: "#60a5fa",
        fillColor: "#60a5fa",
        fillOpacity: 0.95,
      });
      return;
    }
    const state = lightState(date, spot.lat, spot.lon);
    const color = spotMarkerColor(state.key);
    marker.setStyle({
      color,
      fillColor: color,
      fillOpacity: 0.95,
    });
  });
}

function coordinateGroupKey(lat, lon) {
  return `${lat.toFixed(5)},${lon.toFixed(5)}`;
}

function spreadRadiusPx(zoom, count) {
  if (count < 2) return 0;
  return Math.max(6, Math.min(30, (12 - zoom) * 3));
}

function getSpreadLatLng(anchorLat, anchorLon, index, count, zoom) {
  const radiusPx = spreadRadiusPx(zoom, count);
  if (!radiusPx) {
    return L.latLng(anchorLat, anchorLon);
  }

  const basePoint = map.latLngToLayerPoint([anchorLat, anchorLon]);
  const angle = (-Math.PI / 2) + ((Math.PI * 2) / count) * index;
  const point = L.point(
    basePoint.x + Math.cos(angle) * radiusPx,
    basePoint.y + Math.sin(angle) * radiusPx
  );
  return map.layerPointToLatLng(point);
}

function applyMarkerSpread() {
  const grouped = new Map();
  allMarkerRecords.forEach((record) => {
    const key = coordinateGroupKey(record.anchorLat, record.anchorLon);
    if (!grouped.has(key)) {
      grouped.set(key, []);
    }
    grouped.get(key).push(record);
  });

  const zoom = map.getZoom();
  grouped.forEach((records) => {
    records.forEach((record, index) => {
      const latLng = getSpreadLatLng(record.anchorLat, record.anchorLon, index, records.length, zoom);
      record.displayLatLng = latLng;
      record.marker.setLatLng(latLng);
      if (record.type === "spot") {
        record.spot.displayLatLng = latLng;
      }
    });
  });

  sourceMarkers.forEach((record) => {
    if (!record.line) return;
    const linkedSpot = spotByName.get(record.source.linkedSpot);
    const fromLatLng = linkedSpot?.displayLatLng ?? L.latLng(record.anchorLat, record.anchorLon);
    record.line.setLatLngs([fromLatLng, record.displayLatLng]);
  });
}

function hardenPopupInteraction(popup) {
  const root = popup?.getElement?.();
  if (!root) return;

  root.querySelectorAll(".leaflet-popup-content, .forecast-scroll, .wind-compare-wrap, .live-wind-scroll").forEach((element) => {
    L.DomEvent.disableClickPropagation(element);
    L.DomEvent.disableScrollPropagation(element);
  });
}

window.MAP_DATA.spots.forEach((spot) => {
  spotByName.set(spot.name, spot);
  const baseColor = "#60a5fa";
  const marker = L.circleMarker([spot.lat, spot.lon], {
    radius: spot.kind === "mandal" ? 5.5 : 6.5,
    color: baseColor,
    fillColor: baseColor,
    fillOpacity: 0.95,
    weight: 1.5,
    pane: "dataPointPane",
  }).addTo(spotLayer);

  marker.bindTooltip(displaySpotName(spot.name), {
    permanent: true,
    direction: "top",
    offset: [0, -6],
    className: "label-tooltip",
  });
  marker.bindPopup(buildSpotPopup(spot), spotPopupOptions(spot));
  const record = {
    type: "spot",
    marker,
    spot,
    anchorLat: spot.lat,
    anchorLon: spot.lon,
    displayLatLng: L.latLng(spot.lat, spot.lon),
  };
  spot.displayLatLng = record.displayLatLng;
  spotMarkers.push(record);
  allMarkerRecords.push(record);
});

window.MAP_DATA.sources
  .filter((source) => ["DMI DKSS", "DMI vind", "NOAA vind", "NOAA testpunkt", "gfs atmos 0.25", "ICON-EU", "Frost", "Kystverket", "Kartverket tidevann", "Yr"].includes(source.provider))
  .filter((source) => !["Frost", "Kystverket"].includes(source.provider) || source.status === "good")
  .forEach((source) => {
    const linkedSpot = spotByName.get(source.linkedSpot);
    const markerLat = source.lat;
    const markerLon = source.lon;
    let relationHtml = "";
    const markerStyle = sourceMarkerStyle(source);
    let line = null;

    if (linkedSpot) {
      const distanceKm = haversineKm(linkedSpot.lat, linkedSpot.lon, source.lat, source.lon);
      const bearing = bearingDeg(linkedSpot.lat, linkedSpot.lon, source.lat, source.lon);
      relationHtml =
        `<div>Fra ${escapeHtml(displaySpotName(linkedSpot.name))}: <b>${distanceKm.toFixed(1)} km</b> mot <b>${bearingLabel(bearing)}</b> (${bearing.toFixed(0)}°)</div>`;

      line = L.polyline(
        [
          [linkedSpot.lat, linkedSpot.lon],
          [markerLat, markerLon],
        ],
        {
          color: markerStyle.lineColor,
          weight: 1.5,
          opacity: 0.65,
          dashArray: "4 4",
          pane: "dataLinePane",
        }
      ).addTo(dkssLayer);
    }

    const marker = L.circleMarker([markerLat, markerLon], {
      radius: markerStyle.radius,
      color: markerStyle.stroke,
      fillColor: markerStyle.fill,
      fillOpacity: 0.95,
      weight: 1.5,
      pane: "dataPointPane",
    }).addTo(dkssLayer);

    marker.bindTooltip(source.provider === "NOAA vind" ? displaySourceName(source) : source.name, {
      direction: "top",
      offset: [0, -4],
      className: "label-tooltip",
    });
    marker.bindPopup(buildSourcePopup(source, relationHtml), sourcePopupOptions(source));

    const record = {
      type: "source",
      marker,
      line,
      source,
      anchorLat: source.lat,
      anchorLon: source.lon,
      displayLatLng: L.latLng(source.lat, source.lon),
    };
    sourceMarkers.push(record);
    allMarkerRecords.push(record);
  });

map.fitBounds(
  [
    [NORWAY_BOUNDS.south, NORWAY_BOUNDS.west],
    [NORWAY_BOUNDS.north, NORWAY_BOUNDS.east],
  ],
  { padding: [20, 20] }
);

const legend = L.control({ position: "topright" });
legend.onAdd = function () {
  const todayParts = getOsloParts(new Date());
  const todayLabel = `I dag ${todayParts.day}. ${MONTHS_NO[todayParts.month - 1]}`;
  const div = L.DomUtil.create("div", "legend");
  div.innerHTML =
    `<div class="title">${todayLabel}</div>` +
    '<div class="row"><span class="swatch" style="background:rgba(0,0,0,0.50)"></span> Morkt</div>' +
    '<div class="row"><span class="swatch" style="background:rgba(0,0,0,0.25)"></span> Civilt lys</div>' +
    '<div class="row"><span class="swatch" style="background:rgba(255,255,255,0.95)"></span> Etter soloppgang</div>' +
    '<div class="row"><span class="swatch" style="background:#60a5fa"></span> Spot</div>' +
    '<div class="row"><span class="swatch" style="background:#fde047"></span> Yr vindpunkt</div>' +
    '<div class="row"><span class="swatch" style="background:#f97316"></span> DKSS-gridpunkt</div>';
  return div;
};
legend.addTo(map);

map.on("zoomend moveend", applyMarkerSpread);
map.on("popupopen", (event) => {
  hardenPopupInteraction(event.popup);
});
applyMarkerSpread();

let civilTerminatorLayer = null;
let nightTerminatorLayer = null;

function buildAltitudeGrid(date) {
  const features = [];
  let minAltitude = Infinity;
  let maxAltitude = -Infinity;
  for (let lat = MAP_BOUNDS.south; lat <= MAP_BOUNDS.north + 1e-9; lat += TERMINATOR_SAMPLE_DEG) {
    for (let lon = MAP_BOUNDS.west; lon <= MAP_BOUNDS.east + 1e-9; lon += TERMINATOR_SAMPLE_DEG) {
      const altitude = sunAltitudeDeg(date, lat, lon);
      minAltitude = Math.min(minAltitude, altitude);
      maxAltitude = Math.max(maxAltitude, altitude);
      features.push(
        turf.point([lon, lat], {
          altitude,
        })
      );
    }
  }
  return {
    collection: turf.featureCollection(features),
    minAltitude,
    maxAltitude,
  };
}

function clearTerminatorLayers() {
  if (civilTerminatorLayer) {
    map.removeLayer(civilTerminatorLayer);
    civilTerminatorLayer = null;
  }
  if (nightTerminatorLayer) {
    map.removeLayer(nightTerminatorLayer);
    nightTerminatorLayer = null;
  }
}

function buildTerminatorLayer(features) {
  return L.geoJSON(features, {
    pane: "terminatorPane",
    interactive: false,
    style: () => ({
      stroke: false,
      fillColor: "#05070b",
      fillOpacity: 0.25,
    }),
  }).addTo(map);
}

function mapBoundsFeatureCollection() {
  return turf.featureCollection([
    turf.bboxPolygon([MAP_BOUNDS.west, MAP_BOUNDS.south, MAP_BOUNDS.east, MAP_BOUNDS.north]),
  ]);
}

function terminatorBandForThreshold(altitudeGrid, upperBound) {
  if (altitudeGrid.maxAltitude < upperBound) {
    return mapBoundsFeatureCollection();
  }
  if (altitudeGrid.minAltitude >= upperBound) {
    return turf.featureCollection([]);
  }
  return turf.isobands(altitudeGrid.collection, [-90, upperBound], {
    zProperty: "altitude",
  });
}

function renderTerminator(date) {
  clearTerminatorLayers();

  if (!turf.isobands) {
    return;
  }

  const altitudeGrid = buildAltitudeGrid(date);

  try {
    const civilBands = terminatorBandForThreshold(altitudeGrid, 0);
    const nightBands = terminatorBandForThreshold(altitudeGrid, -6);

    if (civilBands.features.length > 0) {
      civilTerminatorLayer = buildTerminatorLayer(civilBands);
    }
    if (nightBands.features.length > 0) {
      nightTerminatorLayer = buildTerminatorLayer(nightBands);
    }
  } catch (error) {
    clearTerminatorLayers();
  }
}

function formatTimeLabel(date) {
  const parts = getOsloParts(date);
  const monthName = MONTHS_NO[parts.month - 1];
  return `${parts.day}. ${monthName} ${String(parts.hour).padStart(2, "0")}:00`;
}

const timeRange = document.getElementById("time-range");
const timeValue = document.getElementById("time-value");
const nowOslo = getOsloParts(new Date());
const selectedDateInfo = {
  year: nowOslo.year,
  month: nowOslo.month,
  day: nowOslo.day,
  hour: initialHourFromNow(),
};

timeRange.value = String(selectedDateInfo.hour);

function currentSelectedDate() {
  return makeOsloDate(
    selectedDateInfo.year,
    selectedDateInfo.month,
    selectedDateInfo.day,
    selectedDateInfo.hour
  );
}

function renderAtSelectedTime() {
  const date = currentSelectedDate();
  timeValue.textContent = formatTimeLabel(date);
  renderTerminator(date);
  updateSpotMarkers(date);
}

timeRange.addEventListener("input", (event) => {
  selectedDateInfo.hour = Number(event.target.value);
  renderAtSelectedTime();
});

renderAtSelectedTime();
