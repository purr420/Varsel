const OSLO_TIMEZONE = "Europe/Oslo";
const MONTHS_NO = ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"];
const NORWAY_BOUNDS = {
  south: 57.35,
  west: 3.0,
  north: 71.55,
  east: 32.2,
};
const OVERLAY_SIZE = { width: 1200, height: 900 };
const LOW_RES_SIZE = { cols: 300, rows: 225 };
const COAST_BUFFER_KM = 100;

const map = L.map("map", {
  zoomControl: true,
  attributionControl: true,
}).setView([65.0, 13.0], 5);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 18,
  attribution: "&copy; OpenStreetMap",
}).addTo(map);

map.createPane("darknessPane");
map.getPane("darknessPane").style.zIndex = 320;
map.getPane("darknessPane").style.pointerEvents = "none";

const spotLayer = L.featureGroup().addTo(map);
const spotMarkers = [];

const osloPartsFormatter = new Intl.DateTimeFormat("en-GB", {
  timeZone: OSLO_TIMEZONE,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
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
    return { key: "civil", label: "Civilt lys", opacity: 0.2 };
  }
  return { key: "day", label: "Lyst", opacity: 0.0 };
}

function spotMarkerColor(stateKey) {
  if (stateKey === "dark") return "#f8fafc";
  if (stateKey === "civil") return "#fde68a";
  return "#60a5fa";
}

function buildSpotPopup(spot, date) {
  const state = lightState(date, spot.lat, spot.lon);
  return (
    `<div class="popup-title">${spot.name}</div>` +
    `<div class="popup-sub">Lysdata for valgt tidspunkt</div>` +
    `<div>Status: ${state.label}</div>` +
    `<div>Lat/lon: ${spot.lat.toFixed(4)}, ${spot.lon.toFixed(4)}</div>`
  );
}

function updateSpotMarkers(date) {
  spotMarkers.forEach(({ marker, spot }) => {
    const state = lightState(date, spot.lat, spot.lon);
    const color = spotMarkerColor(state.key);
    marker.setStyle({
      color,
      fillColor: color,
      fillOpacity: 0.95,
    });
    marker.setPopupContent(buildSpotPopup(spot, date));
  });
}

window.MAP_DATA.spots.forEach((spot) => {
  const marker = L.circleMarker([spot.lat, spot.lon], {
    radius: spot.kind === "mandal" ? 5.5 : 6.5,
    color: "#60a5fa",
    fillColor: "#60a5fa",
    fillOpacity: 0.95,
    weight: 1.5,
  }).addTo(spotLayer);

  marker.bindTooltip(spot.name, {
    permanent: true,
    direction: "top",
    offset: [0, -6],
    className: "label-tooltip",
  });
  marker.bindPopup("");
  spotMarkers.push({ marker, spot });
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
  const div = L.DomUtil.create("div", "legend");
  div.innerHTML =
    '<div class="title">Lys Over Norge</div>' +
    '<div class="row"><span class="swatch" style="background:rgba(0,0,0,0.50)"></span> Morkt</div>' +
    '<div class="row"><span class="swatch" style="background:rgba(0,0,0,0.20)"></span> Civilt lys</div>' +
    '<div class="row"><span class="swatch" style="background:rgba(255,255,255,0.95)"></span> Etter soloppgang</div>' +
    '<div class="row"><span class="swatch" style="background:#60a5fa"></span> Spot</div>';
  return div;
};
legend.addTo(map);

let darknessOverlay = null;
let norwayBoundary = null;

function smoothstep(edge0, edge1, value) {
  const x = Math.max(0, Math.min(1, (value - edge0) / (edge1 - edge0)));
  return x * x * (3 - 2 * x);
}

function darknessOpacityForAltitude(altitude) {
  if (altitude <= -10) {
    return 0.5;
  }
  if (altitude < -6) {
    const t = smoothstep(-10, -6, altitude);
    return 0.5 + (0.2 - 0.5) * t;
  }
  if (altitude < 1) {
    const t = smoothstep(-6, 1, altitude);
    return 0.2 * (1 - t);
  }
  return 0;
}

function projectToCanvas(lat, lon, width, height) {
  const x = ((lon - NORWAY_BOUNDS.west) / (NORWAY_BOUNDS.east - NORWAY_BOUNDS.west)) * width;
  const y = ((NORWAY_BOUNDS.north - lat) / (NORWAY_BOUNDS.north - NORWAY_BOUNDS.south)) * height;
  return [x, y];
}

function drawRingPath(ctx, ring, width, height) {
  ring.forEach((coord, index) => {
    const [x, y] = projectToCanvas(coord[1], coord[0], width, height);
    if (index === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });
  ctx.closePath();
}

function buildNorwayMaskCanvas(width, height) {
  const maskCanvas = document.createElement("canvas");
  maskCanvas.width = width;
  maskCanvas.height = height;
  const maskCtx = maskCanvas.getContext("2d");

  if (!norwayBoundary) {
    return maskCanvas;
  }

  const bufferPx = (height / ((NORWAY_BOUNDS.north - NORWAY_BOUNDS.south) * 111)) * COAST_BUFFER_KM;
  maskCtx.fillStyle = "#ffffff";
  maskCtx.strokeStyle = "#ffffff";
  maskCtx.lineJoin = "round";
  maskCtx.lineCap = "round";
  maskCtx.lineWidth = bufferPx * 2;

  norwayBoundary.features.forEach((feature) => {
    const polygons = feature.geometry.type === "Polygon"
      ? [feature.geometry.coordinates]
      : feature.geometry.coordinates;

    polygons.forEach((polygon) => {
      maskCtx.beginPath();
      polygon.forEach((ring) => {
        drawRingPath(maskCtx, ring, width, height);
      });
      maskCtx.fill("evenodd");
      maskCtx.stroke();
    });
  });

  return maskCanvas;
}

function drawDarknessOverlay(date) {
  const lowCanvas = document.createElement("canvas");
  lowCanvas.width = LOW_RES_SIZE.cols;
  lowCanvas.height = LOW_RES_SIZE.rows;

  const lowCtx = lowCanvas.getContext("2d");
  const cellWidth = lowCanvas.width / LOW_RES_SIZE.cols;
  const cellHeight = lowCanvas.height / LOW_RES_SIZE.rows;
  const latSpan = NORWAY_BOUNDS.north - NORWAY_BOUNDS.south;
  const lonSpan = NORWAY_BOUNDS.east - NORWAY_BOUNDS.west;

  for (let y = 0; y < LOW_RES_SIZE.rows; y += 1) {
    const lat = NORWAY_BOUNDS.north - ((y + 0.5) / LOW_RES_SIZE.rows) * latSpan;
    for (let x = 0; x < LOW_RES_SIZE.cols; x += 1) {
      const lon = NORWAY_BOUNDS.west + ((x + 0.5) / LOW_RES_SIZE.cols) * lonSpan;
      const opacity = darknessOpacityForAltitude(sunAltitudeDeg(date, lat, lon));
      if (opacity <= 0.002) {
        continue;
      }
      lowCtx.fillStyle = `rgba(0, 0, 0, ${opacity.toFixed(3)})`;
      lowCtx.fillRect(x * cellWidth, y * cellHeight, cellWidth + 1, cellHeight + 1);
    }
  }

  const canvas = document.createElement("canvas");
  canvas.width = OVERLAY_SIZE.width;
  canvas.height = OVERLAY_SIZE.height;
  const ctx = canvas.getContext("2d");
  ctx.imageSmoothingEnabled = true;
  ctx.filter = "blur(10px)";
  ctx.drawImage(lowCanvas, 0, 0, canvas.width, canvas.height);
  ctx.filter = "none";

  const maskCanvas = buildNorwayMaskCanvas(canvas.width, canvas.height);
  ctx.globalCompositeOperation = "destination-in";
  ctx.drawImage(maskCanvas, 0, 0);
  ctx.globalCompositeOperation = "source-over";

  const imageUrl = canvas.toDataURL("image/png");
  const bounds = [
    [NORWAY_BOUNDS.south, NORWAY_BOUNDS.west],
    [NORWAY_BOUNDS.north, NORWAY_BOUNDS.east],
  ];

  if (!darknessOverlay) {
    darknessOverlay = L.imageOverlay(imageUrl, bounds, {
      pane: "darknessPane",
      interactive: false,
      opacity: 1,
    }).addTo(map);
    return;
  }

  darknessOverlay.setUrl(imageUrl);
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
  drawDarknessOverlay(date);
  updateSpotMarkers(date);
}

timeRange.addEventListener("input", (event) => {
  selectedDateInfo.hour = Number(event.target.value);
  renderAtSelectedTime();
});

renderAtSelectedTime();

fetch("./data/norway.geojson")
  .then((response) => response.json())
  .then((geojson) => {
    norwayBoundary = geojson;
    renderAtSelectedTime();
  })
  .catch(() => {
    renderAtSelectedTime();
  });
