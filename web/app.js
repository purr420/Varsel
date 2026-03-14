const OSLO_TIMEZONE = "Europe/Oslo";
const MONTHS_NO = ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"];
const NORWAY_BOUNDS = {
  south: 57.35,
  west: 3.0,
  north: 71.55,
  east: 32.2,
};
const COAST_BUFFER_KM = 100;

const map = L.map("map", {
  zoomControl: true,
  attributionControl: true,
}).setView([65.0, 13.0], 5);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 18,
  attribution: "&copy; OpenStreetMap",
}).addTo(map);

map.createPane("frontPane");
map.getPane("frontPane").style.zIndex = 330;
map.getPane("frontPane").style.pointerEvents = "none";

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
    '<div class="row"><span class="swatch" style="background:rgba(0,0,0,0.60)"></span> Morkt</div>' +
    '<div class="row"><span class="swatch" style="background:rgba(0,0,0,0.20)"></span> Civilt lys</div>' +
    '<div class="row"><span class="swatch" style="background:rgba(255,255,255,0.95)"></span> Etter soloppgang</div>' +
    '<div class="row"><span class="swatch" style="background:#60a5fa"></span> Spot</div>';
  return div;
};
legend.addTo(map);

let bufferedNorway = null;
let daylightOverlay = null;

function smoothstep(edge0, edge1, value) {
  const x = Math.max(0, Math.min(1, (value - edge0) / (edge1 - edge0)));
  return x * x * (3 - 2 * x);
}

function darknessOpacityForAltitude(altitude) {
  if (altitude <= -6) {
    return 0.6;
  }
  if (altitude < -0.8) {
    const t = smoothstep(-6, -0.8, altitude);
    return 0.6 + (0.2 - 0.6) * t;
  }
  if (altitude < 0.35) {
    const t = smoothstep(-0.8, 0.35, altitude);
    return 0.2 * (1 - t);
  }
  return 0;
}

function geoToCanvasPoint(lat, lon, width, height) {
  const x = ((lon - NORWAY_BOUNDS.west) / (NORWAY_BOUNDS.east - NORWAY_BOUNDS.west)) * width;
  const y = ((NORWAY_BOUNDS.north - lat) / (NORWAY_BOUNDS.north - NORWAY_BOUNDS.south)) * height;
  return [x, y];
}

function drawFeaturePath(ctx, feature) {
  const polygons = feature.geometry.type === "Polygon"
    ? [feature.geometry.coordinates]
    : feature.geometry.coordinates;

  polygons.forEach((polygon) => {
    polygon.forEach((ring) => {
      ring.forEach((coord, index) => {
        const point = geoToCanvasPoint(coord[1], coord[0], ctx.canvas.width, ctx.canvas.height);
        if (index === 0) {
          ctx.moveTo(point[0], point[1]);
        } else {
          ctx.lineTo(point[0], point[1]);
        }
      });
      ctx.closePath();
    });
  });
}

function buildLowResOverlay(date, width, height) {
  const sampleWidth = Math.max(360, Math.round(width / 2));
  const sampleHeight = Math.max(300, Math.round(height / 2));
  const offscreen = document.createElement("canvas");
  offscreen.width = sampleWidth;
  offscreen.height = sampleHeight;
  const offCtx = offscreen.getContext("2d");

  for (let y = 0; y < sampleHeight; y += 1) {
    for (let x = 0; x < sampleWidth; x += 1) {
      const lon = NORWAY_BOUNDS.west + ((x + 0.5) / sampleWidth) * (NORWAY_BOUNDS.east - NORWAY_BOUNDS.west);
      const lat = NORWAY_BOUNDS.north - ((y + 0.5) / sampleHeight) * (NORWAY_BOUNDS.north - NORWAY_BOUNDS.south);
      const altitude = sunAltitudeDeg(date, lat, lon);
      const darkOpacity = darknessOpacityForAltitude(altitude);

      if (darkOpacity > 0.002) {
        offCtx.fillStyle = `rgba(5, 7, 11, ${darkOpacity.toFixed(3)})`;
        offCtx.fillRect(x, y, 1, 1);
      }
    }
  }

  return offscreen;
}

function drawDarknessOverlay(date) {
  const width = 960;
  const height = 700;
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  const fieldCanvas = buildLowResOverlay(date, width, height);

  ctx.clearRect(0, 0, width, height);
  ctx.save();
  if (bufferedNorway) {
    ctx.beginPath();
    drawFeaturePath(ctx, bufferedNorway);
    ctx.clip("evenodd");
  }
  ctx.imageSmoothingEnabled = true;
  ctx.filter = "blur(2px)";
  ctx.drawImage(fieldCanvas, 0, 0, width, height);
  ctx.filter = "none";
  ctx.restore();

  const url = canvas.toDataURL("image/png");
  const bounds = [
    [NORWAY_BOUNDS.south, NORWAY_BOUNDS.west],
    [NORWAY_BOUNDS.north, NORWAY_BOUNDS.east],
  ];

  if (!daylightOverlay) {
    daylightOverlay = L.imageOverlay(url, bounds, {
      pane: "frontPane",
      interactive: false,
      opacity: 1,
    }).addTo(map);
  } else {
    daylightOverlay.setUrl(url);
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
    bufferedNorway = turf.buffer(geojson.features[0], COAST_BUFFER_KM, { units: "kilometers" });
    renderAtSelectedTime();
  })
  .catch(() => {
    renderAtSelectedTime();
  });
