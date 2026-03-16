const OSLO_TIMEZONE = "Europe/Oslo";
const MONTHS_NO = ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"];
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
  maxBounds: [
    [MAP_BOUNDS.south, MAP_BOUNDS.west],
    [MAP_BOUNDS.north, MAP_BOUNDS.east],
  ],
  maxBoundsViscosity: 1.0,
}).setView([65.0, 13.0], 5);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 18,
  attribution: "&copy; OpenStreetMap",
}).addTo(map);

map.createPane("terminatorPane");
map.getPane("terminatorPane").style.zIndex = 330;
map.getPane("terminatorPane").style.pointerEvents = "none";

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
    '<div class="row"><span class="swatch" style="background:rgba(0,0,0,0.25)"></span> Civilt lys</div>' +
    '<div class="row"><span class="swatch" style="background:rgba(255,255,255,0.95)"></span> Etter soloppgang</div>' +
    '<div class="row"><span class="swatch" style="background:#60a5fa"></span> Spot</div>';
  return div;
};
legend.addTo(map);

let civilTerminatorLayer = null;
let nightTerminatorLayer = null;

function buildAltitudeGrid(date) {
  const features = [];
  for (let lat = MAP_BOUNDS.south; lat <= MAP_BOUNDS.north + 1e-9; lat += TERMINATOR_SAMPLE_DEG) {
    for (let lon = MAP_BOUNDS.west; lon <= MAP_BOUNDS.east + 1e-9; lon += TERMINATOR_SAMPLE_DEG) {
      features.push(
        turf.point([lon, lat], {
          altitude: sunAltitudeDeg(date, lat, lon),
        })
      );
    }
  }
  return turf.featureCollection(features);
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

function renderTerminator(date) {
  clearTerminatorLayers();

  if (!turf.isobands) {
    return;
  }

  const altitudeGrid = buildAltitudeGrid(date);

  try {
    const civilBands = turf.isobands(altitudeGrid, [-90, 0], {
      zProperty: "altitude",
    });
    const nightBands = turf.isobands(altitudeGrid, [-90, -6], {
      zProperty: "altitude",
    });

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
