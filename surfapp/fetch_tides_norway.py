import argparse
import csv
import math
import os
import re
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import numpy as np
import pygrib
import requests


UTC = timezone.utc
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "data_cache")
PUBLIC_DIR = os.path.join(BASE_DIR, "data_public")
USER_AGENT = "Codex/1.0 https://openai.com"

KARTVERKET_STATIONLIST_URL = (
    "https://vannstand.kartverket.no/tideapi.php"
    "?tide_request=stationlist&type=perm&lang=en"
)
KARTVERKET_LOCATIONDATA_URL = "https://vannstand.kartverket.no/tideapi.php"
MET_TIDALWATER_URL = "https://api.met.no/weatherapi/tidalwater/1.1/"
DMI_DKSS_COLLECTION = "dkss_nsbs"
DMI_DKSS_POSITION_URL = (
    f"https://dmigw.govcloud.dk/v1/forecastedr/collections/{DMI_DKSS_COLLECTION}/position"
)
DMI_DKSS_CUBE_URL = (
    f"https://dmigw.govcloud.dk/v1/forecastedr/collections/{DMI_DKSS_COLLECTION}/cube"
)
DMI_DKSS_STAC_URL = (
    f"https://dmigw.govcloud.dk/v1/forecastdata/collections/{DMI_DKSS_COLLECTION}/items"
)
DMI_API_KEY_EDR = os.getenv("DMI_API_KEY_EDR", "ae501bfc-112e-400e-89df-77a2a6b9af72")
DMI_API_KEY_STAC = os.getenv("DMI_API_KEY_STAC", "a4b09032-bca5-4255-ac85-6fea95a1e02c")

STATION_MAP_CACHE = os.path.join(CACHE_DIR, "tide_spot_stations.csv")
TIDE_CACHE = os.path.join(CACHE_DIR, "tides_norway_spots_cache.csv")
TIDE_PUBLIC = os.path.join(PUBLIC_DIR, "tides_norway_spots_readable.csv")


@dataclass(frozen=True)
class Spot:
    name: str
    slug: str
    lat: float
    lon: float


@dataclass(frozen=True)
class TideStation:
    name: str
    code: str
    lat: float
    lon: float
    harbor_slug: str


SPOTS = [
    Spot("Lista", "lista", 58.0, 6.5),
    Spot("Pigsty/Piggy", "pigsty_piggy", 58.75, 5.25),
    Spot("Saltstein", "saltstein", 58.75, 9.75),
    Spot("Ervika", "ervika", 62.25, 5.0),
    Spot("Alnes Lighthouse (Godoy)", "alnes_lighthouse_godoy", 62.5, 5.75),
    Spot("Hustadvika Gjestegard", "hustadvika_gjestegard", 63.0, 7.0),
    Spot("Unstad Beach", "unstad_beach", 68.25, 13.25),
    Spot("Persfjord", "persfjord", 70.5, 31.0),
]

DEFAULT_STREAMLIT_SPOTS = ("Lista", "Pigsty/Piggy", "Saltstein")
DKSS_DIAGNOSTIC_SPOTS = {"Lista", "Pigsty/Piggy", "Saltstein"}
DKSS_DIAGNOSTIC_LABELS = {
    "Lista": "Lista",
    "Pigsty/Piggy": "Jæren",
    "Saltstein": "Saltstein",
}
DKSS_SURGE_PARAM_ID = 82


_DKSS_METHOD_LOGGED = False
_DKSS_GRID_CACHE: Optional[dict] = None


# MET tidalwater uses harbor slugs, not station codes.
HARBOR_BY_STATION_CODE = {
    "AES": "ålesund",
    "ANX": "andenes",
    "BGO": "bergen",
    "BOH": "bøfjorden",
    "BOO": "bodø",
    "BRJ": "bruravik",
    "HAR": "harstad",
    "HEI": "heimsjø",
    "HFT": "hammerfest",
    "HRO": "helgeroa",
    "HVG": "honningsvåg",
    "KAB": "kabelvåg",
    "KSU": "kristiansund",
    "LEH": "leirvik",
    "MAY": "måløy",
    "MSU": "mausund",
    "NVK": "narvik",
    "NYA": "ny-ålesund",
    "OSC": "oscarsborg",
    "OSL": "oslo",
    "RVK": "rørvik",
    "SBG": "sandnes",
    "SIE": "sirevåg",
    "SOY": "solumstrand",
    "SVG": "stavanger",
    "TAZ": "træna",
    "TOS": "tromsø",
    "TRD": "trondheim",
    "TRG": "tregde",
    "VAW": "vardø",
    "VIK": "viker",
}

STATION_OVERRIDE_BY_SPOT = {
    "Pigsty/Piggy": "SIE",
}


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    return 2 * radius_km * math.asin(math.sqrt(a))


def parse_iso_utc(ts: str) -> datetime:
    ts = ts.strip()
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(UTC)
    return dt


def normalize_name(value: str) -> str:
    lowered = unicodedata.normalize("NFKC", value).casefold()
    lowered = re.sub(r"[^0-9a-zæøå]+", " ", lowered)
    return " ".join(lowered.split())


def selected_spots(include_all_spots: bool) -> list[Spot]:
    if include_all_spots:
        return SPOTS
    wanted = set(DEFAULT_STREAMLIT_SPOTS)
    return [spot for spot in SPOTS if spot.name in wanted]


def fetch_station_list() -> list[TideStation]:
    resp = requests.get(
        KARTVERKET_STATIONLIST_URL,
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    stations: list[TideStation] = []
    for loc in root.findall(".//location"):
        code = loc.attrib["code"]
        harbor_slug = HARBOR_BY_STATION_CODE.get(code)
        if not harbor_slug:
            continue
        stations.append(
            TideStation(
                name=loc.attrib["name"],
                code=code,
                lat=float(loc.attrib["latitude"]),
                lon=float(loc.attrib["longitude"]),
                harbor_slug=harbor_slug,
            )
        )
    return stations


def nearest_station(spot: Spot, stations: list[TideStation]) -> tuple[TideStation, float]:
    ranked = sorted(
        (
            (haversine_km(spot.lat, spot.lon, station.lat, station.lon), station)
            for station in stations
        ),
        key=lambda item: item[0],
    )
    distance_km, station = ranked[0]
    return station, distance_km


def station_for_spot(spot: Spot, stations: list[TideStation]) -> tuple[TideStation, float]:
    override_code = STATION_OVERRIDE_BY_SPOT.get(spot.name)
    if override_code:
        for station in stations:
            if station.code == override_code:
                distance_km = haversine_km(spot.lat, spot.lon, station.lat, station.lon)
                return station, distance_km
    return nearest_station(spot, stations)


def fetch_kartverket_predictions(
    station: TideStation,
    start_dt: datetime,
    end_dt: datetime,
) -> dict[datetime, float]:
    params = {
        "tide_request": "locationdata",
        "lat": f"{station.lat:.6f}",
        "lon": f"{station.lon:.6f}",
        "fromtime": start_dt.strftime("%Y-%m-%dT%H:%M"),
        "totime": end_dt.strftime("%Y-%m-%dT%H:%M"),
        "datatype": "pre",
        "refcode": "msl",
        "interval": "60",
        "dst": "0",
        "tzone": "0",
        "lang": "en",
    }
    resp = requests.get(
        KARTVERKET_LOCATIONDATA_URL,
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=25,
    )
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    if root.find(".//nodata") is not None:
        return {}

    predictions: dict[datetime, float] = {}
    for waterlevel in root.findall(".//waterlevel"):
        value_cm = waterlevel.attrib.get("value")
        ts = waterlevel.attrib.get("time")
        if not value_cm or not ts:
            continue
        dt = parse_iso_utc(ts)
        predictions[dt] = float(value_cm) / 100.0
    return predictions


def parse_met_updated_at(raw: str) -> Optional[datetime]:
    match = re.search(r"OPPDATERT:\s*(\d{8})\s+(\d{2}:\d{2})\s+UTC", raw)
    if not match:
        return None
    return datetime.strptime(
        f"{match.group(1)} {match.group(2)}", "%Y%m%d %H:%M"
    ).replace(tzinfo=UTC)


def fetch_dmi_dkss_metadata() -> dict[str, datetime]:
    params = {"limit": 1, "api-key": DMI_API_KEY_STAC}
    try:
        resp = requests.get(
            DMI_DKSS_STAC_URL,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=25,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return {}

    features = data.get("features") or []
    if not features:
        return {}

    props = features[0].get("properties", {})
    meta: dict[str, datetime] = {}
    model_run = props.get("modelRun")
    created = props.get("created")
    if model_run:
        meta["model_run"] = parse_iso_utc(model_run)
    if created:
        meta["created"] = parse_iso_utc(created)
    return meta


def log_dkss_methods_once() -> None:
    global _DKSS_METHOD_LOGGED
    if _DKSS_METHOD_LOGGED:
        return
    print("[DKSS] Previous method: EDR position query with EDR cube bbox fallback.")
    print("[DKSS] New main method: forecastdata GRIB -> nearest valid sea grid cell -> EDR position query at locked gridpoint.")
    _DKSS_METHOD_LOGGED = True


def fetch_dmi_dkss_item_detail() -> Optional[dict]:
    params = {"limit": 1, "api-key": DMI_API_KEY_STAC}
    try:
        resp = requests.get(
            DMI_DKSS_STAC_URL,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=25,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return None

    features = data.get("features") or []
    if not features:
        return None

    item_id = features[0].get("id")
    if not item_id:
        return None

    try:
        resp = requests.get(
            f"{DMI_DKSS_STAC_URL}/{item_id}",
            params={"api-key": DMI_API_KEY_STAC},
            headers={"User-Agent": USER_AGENT},
            timeout=25,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return None


def ensure_dkss_reference_grib(item: dict) -> Optional[str]:
    asset = (item.get("asset") or {}).get("data") or (item.get("assets") or {}).get("data")
    href = (asset or {}).get("href")
    item_id = item.get("id")
    if not href or not item_id:
        return None

    ensure_dir(CACHE_DIR)
    path = os.path.join(CACHE_DIR, item_id)
    if os.path.exists(path):
        return path

    try:
        resp = requests.get(
            href,
            headers={"User-Agent": USER_AGENT},
            timeout=60,
        )
        resp.raise_for_status()
    except requests.RequestException:
        return None

    with open(path, "wb") as f:
        f.write(resp.content)
    return path


def load_dkss_reference_grid() -> Optional[dict]:
    global _DKSS_GRID_CACHE
    if _DKSS_GRID_CACHE is not None:
        return _DKSS_GRID_CACHE

    item = fetch_dmi_dkss_item_detail()
    if not item:
        return None

    grib_path = ensure_dkss_reference_grib(item)
    if not grib_path:
        return None

    try:
        with pygrib.open(grib_path) as grbs:
            msg = next(
                grb for grb in grbs
                if grb.typeOfLevel == "surface" and getattr(grb, "paramId", None) == DKSS_SURGE_PARAM_ID
            )
            lats, lons = msg.latlons()
            values = np.array(msg.values, dtype=float)
    except (OSError, RuntimeError, StopIteration, ValueError):
        return None

    valid_mask = np.isfinite(values)
    props = item.get("properties") or {}
    _DKSS_GRID_CACHE = {
        "item_id": item.get("id"),
        "grib_path": grib_path,
        "valid_time": parse_iso_utc(props["datetime"]) if props.get("datetime") else None,
        "model_run": parse_iso_utc(props["modelRun"]) if props.get("modelRun") else None,
        "lats": lats,
        "lons": lons,
        "values": values,
        "valid_mask": valid_mask,
        "bbox": (-4.125, 48.525, 30.292, 65.875),
        "param_id": DKSS_SURGE_PARAM_ID,
    }
    return _DKSS_GRID_CACHE


def fetch_dmi_dkss_position_rows(
    lat: float,
    lon: float,
) -> tuple[dict[datetime, float], Optional[float], Optional[float]]:
    params = {
        "coords": f"POINT({lon:.6f} {lat:.6f})",
        "crs": "crs84",
        "parameter-name": "sea-mean-deviation",
        "api-key": DMI_API_KEY_EDR,
        "f": "GeoJSON",
    }
    try:
        resp = requests.get(
            DMI_DKSS_POSITION_URL,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return {}, None, None

    rows: dict[datetime, float] = {}
    chosen_lat: Optional[float] = None
    chosen_lon: Optional[float] = None
    for feature in data.get("features") or []:
        geometry = feature.get("geometry") or {}
        coords = geometry.get("coordinates") or []
        props = feature.get("properties") or {}
        value = props.get("sea-mean-deviation")
        step = props.get("step")
        if len(coords) >= 2 and chosen_lat is None and chosen_lon is None:
            chosen_lon = float(coords[0])
            chosen_lat = float(coords[1])
        if value is None or not step:
            continue
        try:
            rows[parse_iso_utc(step)] = float(value)
        except (TypeError, ValueError):
            continue
    return rows, chosen_lat, chosen_lon


def nearest_valid_dkss_gridpoint(spot: Spot) -> tuple[Optional[dict], Optional[str]]:
    grid = load_dkss_reference_grid()
    if not grid:
        return None, "Could not load DKSS reference GRIB grid."

    west, south, east, north = grid["bbox"]
    if not (south <= spot.lat <= north and west <= spot.lon <= east):
        return None, (
            f"Target lies outside dkss_nsbs bbox "
            f"({south:.3f}-{north:.3f}N, {west:.3f}-{east:.3f}E)."
        )

    lats = grid["lats"]
    lons = grid["lons"]
    valid_mask = grid["valid_mask"]
    if not np.any(valid_mask):
        return None, "DKSS GRIB grid had no valid sea cells."

    target_lat_rad = math.radians(spot.lat)
    lat_rad = np.radians(lats)
    dlat = lat_rad - target_lat_rad
    dlon = np.radians(lons - spot.lon)
    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(target_lat_rad) * np.cos(lat_rad) * np.sin(dlon / 2.0) ** 2
    )
    distances_km = 2.0 * 6371.0 * np.arcsin(np.sqrt(a))
    distances_km = np.where(valid_mask, distances_km, np.inf)
    flat_index = int(np.argmin(distances_km))
    if not np.isfinite(distances_km.flat[flat_index]):
        return None, "No valid DKSS sea cell found near target."

    iy, ix = np.unravel_index(flat_index, distances_km.shape)
    return {
        "iy": int(iy),
        "ix": int(ix),
        "lat_used": float(lats[iy, ix]),
        "lon_used": float(lons[iy, ix]),
        "dist_km": float(distances_km[iy, ix]),
        "reference_value": float(grid["values"][iy, ix]),
        "reference_valid_time": grid.get("valid_time"),
        "reference_model_run": grid.get("model_run"),
        "param_id": grid.get("param_id"),
    }, None


def print_dkss_diagnostics(
    spot: Spot,
    direct_rows: dict[datetime, float],
    direct_lat: Optional[float],
    direct_lon: Optional[float],
    locked_rows: dict[datetime, float],
    grid_point: Optional[dict],
    failure_reason: Optional[str],
) -> None:
    if spot.name not in DKSS_DIAGNOSTIC_SPOTS:
        return

    label = DKSS_DIAGNOSTIC_LABELS.get(spot.name, spot.name)
    print(
        f"[DKSS] {label}: target=({spot.lat:.6f}, {spot.lon:.6f}) "
        f"direct_api={'yes' if direct_rows else 'no'}"
    )

    if direct_rows:
        direct_time = sorted(direct_rows)[0]
        direct_value = direct_rows[direct_time]
        coord_note = ""
        if direct_lat is not None and direct_lon is not None:
            coord_note = f" snapped=({direct_lat:.6f}, {direct_lon:.6f})"
        print(
            f"[DKSS] {label}: direct value {direct_value:.3f} m at "
            f"{direct_time.isoformat()}{coord_note}"
        )
    else:
        print(f"[DKSS] {label}: direct coordinate query returned no usable value.")

    if grid_point:
        ref_time = grid_point.get("reference_valid_time")
        ref_time_str = ref_time.isoformat() if isinstance(ref_time, datetime) else "unknown"
        print(
            f"[DKSS] {label}: nearest valid sea cell iy={grid_point['iy']} ix={grid_point['ix']} "
            f"lat={grid_point['lat_used']:.6f} lon={grid_point['lon_used']:.6f} "
            f"dist={grid_point['dist_km']:.1f} km ref_value={grid_point['reference_value']:.3f} m "
            f"ref_time={ref_time_str}"
        )
    elif failure_reason:
        print(f"[DKSS] {label}: {failure_reason}")

    if locked_rows:
        locked_time = sorted(locked_rows)[0]
        locked_value = locked_rows[locked_time]
        print(
            f"[DKSS] {label}: locked-gridpoint value {locked_value:.3f} m at "
            f"{locked_time.isoformat()}"
        )
    elif not failure_reason:
        print(f"[DKSS] {label}: locked-gridpoint query returned no usable value.")


def fetch_dmi_dkss_for_spot(
    spot: Spot,
) -> tuple[
    dict[datetime, float],
    Optional[float],
    Optional[float],
    Optional[float],
    Optional[int],
    Optional[int],
]:
    log_dkss_methods_once()

    direct_rows, direct_lat, direct_lon = fetch_dmi_dkss_position_rows(spot.lat, spot.lon)
    grid_point, failure_reason = nearest_valid_dkss_gridpoint(spot)

    if not grid_point:
        print_dkss_diagnostics(
            spot,
            direct_rows,
            direct_lat,
            direct_lon,
            {},
            None,
            failure_reason,
        )
        return {}, None, None, None, None, None

    locked_rows, _, _ = fetch_dmi_dkss_position_rows(
        grid_point["lat_used"],
        grid_point["lon_used"],
    )
    if not locked_rows and direct_rows:
        locked_rows = direct_rows

    print_dkss_diagnostics(
        spot,
        direct_rows,
        direct_lat,
        direct_lon,
        locked_rows,
        grid_point,
        failure_reason,
    )
    return (
        locked_rows,
        grid_point["lat_used"],
        grid_point["lon_used"],
        grid_point["dist_km"],
        grid_point["iy"],
        grid_point["ix"],
    )


def fetch_met_weathercorrection(harbor_slug: str) -> tuple[Optional[datetime], dict[datetime, dict[str, float]]]:
    resp = requests.get(
        MET_TIDALWATER_URL,
        params={"harbor": harbor_slug, "datatype": "weathercorrection", "content_type": "text/plain"},
        headers={"User-Agent": USER_AGENT},
        timeout=25,
    )
    resp.raise_for_status()
    rows: dict[datetime, dict[str, float]] = {}
    updated_at = parse_met_updated_at(resp.text)

    for line in resp.text.splitlines():
        parts = line.split()
        if len(parts) < 13 or not parts[0].isdigit():
            continue
        year, month, day, hour, minute = (int(parts[i]) for i in range(5))
        if minute != 0:
            continue
        dt = datetime(year, month, day, hour, minute, tzinfo=UTC)
        rows[dt] = {
            "surge_m": float(parts[5]),
            "met_tide_m": float(parts[6]),
            "total_m": float(parts[7]),
            "surge_p0_m": float(parts[8]),
            "surge_p25_m": float(parts[9]),
            "surge_p50_m": float(parts[10]),
            "surge_p75_m": float(parts[11]),
            "surge_p100_m": float(parts[12]),
        }
    return updated_at, rows


def format_local(dt: datetime) -> str:
    return dt.astimezone().strftime("%Y-%m-%d %H:%M")


def write_station_map(rows: list[dict]) -> None:
    ensure_dir(CACHE_DIR)
    fieldnames = [
        "spot",
        "spot_lat",
        "spot_lon",
        "station_name",
        "station_code",
        "station_lat",
        "station_lon",
        "distance_km",
        "met_harbor_slug",
        "dkss_point_lat",
        "dkss_point_lon",
        "dkss_distance_km",
        "dkss_iy",
        "dkss_ix",
    ]
    with open(STATION_MAP_CACHE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_tide_rows(
    path: str,
    rows: list[dict],
    include_local_time: bool,
    dmi_meta: Optional[dict[str, datetime]] = None,
) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write(f"# Created: {datetime.now(UTC).isoformat()}\n")
        if dmi_meta and dmi_meta.get("model_run"):
            f.write(f"# Model run: {dmi_meta['model_run'].isoformat()}\n")
        if dmi_meta and dmi_meta.get("created"):
            f.write(f"# DMI Created: {dmi_meta['created'].isoformat()}\n")
        f.write("# Values are meters above mean sea level (MSL)\n")
        fieldnames = [
            "spot",
            "station_name",
            "station_code",
            "time_utc",
        ]
        if include_local_time:
            fieldnames.append("time_local")
        fieldnames.extend(
            [
                "astronomical_tide_m",
                "surge_m",
                "dmi_dkss_m",
                "dkss_lat_used",
                "dkss_lon_used",
                "dkss_dist_km",
                "dkss_iy",
                "dkss_ix",
                "met_tide_m",
                "total_water_level_m",
                "surge_p0_m",
                "surge_p25_m",
                "surge_p50_m",
                "surge_p75_m",
                "surge_p100_m",
            ]
        )
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def build_rows(spots: list[Spot]) -> tuple[list[dict], list[dict], dict[str, datetime]]:
    stations = fetch_station_list()
    station_rows: list[dict] = []
    tide_rows: list[dict] = []
    dmi_meta = fetch_dmi_dkss_metadata()

    start_dt = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    end_dt = start_dt + timedelta(days=3)

    for spot in spots:
        station, distance_km = station_for_spot(spot, stations)
        station_rows.append(
            {
                "spot": spot.name,
                "spot_lat": f"{spot.lat:.6f}",
                "spot_lon": f"{spot.lon:.6f}",
                "station_name": station.name,
                "station_code": station.code,
                "station_lat": f"{station.lat:.6f}",
                "station_lon": f"{station.lon:.6f}",
                "distance_km": f"{distance_km:.1f}",
                "met_harbor_slug": station.harbor_slug,
            }
        )

        astronomical = fetch_kartverket_predictions(station, start_dt, end_dt)
        _, corrected = fetch_met_weathercorrection(station.harbor_slug)
        dkss_rows, dkss_point_lat, dkss_point_lon, dkss_distance_km, dkss_iy, dkss_ix = fetch_dmi_dkss_for_spot(spot)
        station_rows[-1]["dkss_point_lat"] = (
            f"{dkss_point_lat:.6f}" if dkss_point_lat is not None else ""
        )
        station_rows[-1]["dkss_point_lon"] = (
            f"{dkss_point_lon:.6f}" if dkss_point_lon is not None else ""
        )
        station_rows[-1]["dkss_distance_km"] = (
            f"{dkss_distance_km:.1f}" if dkss_distance_km is not None else ""
        )
        station_rows[-1]["dkss_iy"] = str(dkss_iy) if dkss_iy is not None else ""
        station_rows[-1]["dkss_ix"] = str(dkss_ix) if dkss_ix is not None else ""

        hourly_times = sorted(set(astronomical.keys()) | set(corrected.keys()) | set(dkss_rows.keys()))
        for dt in hourly_times:
            if dt < start_dt or dt > end_dt:
                continue
            corrected_row = corrected.get(dt, {})
            tide_rows.append(
                {
                    "spot": spot.name,
                    "station_name": station.name,
                    "station_code": station.code,
                    "time_utc": dt.isoformat(),
                    "time_local": format_local(dt),
                    "astronomical_tide_m": (
                        f"{astronomical[dt]:.3f}" if dt in astronomical else ""
                    ),
                    "surge_m": (
                        f"{corrected_row['surge_m']:.3f}" if "surge_m" in corrected_row else ""
                    ),
                    "dmi_dkss_m": (
                        f"{dkss_rows[dt]:.3f}" if dt in dkss_rows else ""
                    ),
                    "dkss_lat_used": (
                        f"{dkss_point_lat:.6f}" if dkss_point_lat is not None else ""
                    ),
                    "dkss_lon_used": (
                        f"{dkss_point_lon:.6f}" if dkss_point_lon is not None else ""
                    ),
                    "dkss_dist_km": (
                        f"{dkss_distance_km:.1f}" if dkss_distance_km is not None else ""
                    ),
                    "dkss_iy": str(dkss_iy) if dkss_iy is not None else "",
                    "dkss_ix": str(dkss_ix) if dkss_ix is not None else "",
                    "met_tide_m": (
                        f"{corrected_row['met_tide_m']:.3f}" if "met_tide_m" in corrected_row else ""
                    ),
                    "total_water_level_m": (
                        f"{corrected_row['total_m']:.3f}" if "total_m" in corrected_row else ""
                    ),
                    "surge_p0_m": (
                        f"{corrected_row['surge_p0_m']:.3f}" if "surge_p0_m" in corrected_row else ""
                    ),
                    "surge_p25_m": (
                        f"{corrected_row['surge_p25_m']:.3f}" if "surge_p25_m" in corrected_row else ""
                    ),
                    "surge_p50_m": (
                        f"{corrected_row['surge_p50_m']:.3f}" if "surge_p50_m" in corrected_row else ""
                    ),
                    "surge_p75_m": (
                        f"{corrected_row['surge_p75_m']:.3f}" if "surge_p75_m" in corrected_row else ""
                    ),
                    "surge_p100_m": (
                        f"{corrected_row['surge_p100_m']:.3f}" if "surge_p100_m" in corrected_row else ""
                    ),
                }
            )

    tide_rows.sort(key=lambda row: (normalize_name(row["spot"]), row["time_utc"]))
    return station_rows, tide_rows, dmi_meta


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch tide data for surf spots.")
    parser.add_argument(
        "--all-spots",
        action="store_true",
        help="Fetch tides for all Norway surf spots instead of Lista-only Streamlit mode.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    spots = selected_spots(include_all_spots=args.all_spots)
    station_rows, tide_rows, dmi_meta = build_rows(spots)
    write_station_map(station_rows)
    write_tide_rows(TIDE_CACHE, tide_rows, include_local_time=False, dmi_meta=dmi_meta)
    write_tide_rows(TIDE_PUBLIC, tide_rows, include_local_time=True, dmi_meta=dmi_meta)
    print(
        f"[TIDE] Skrev {len(station_rows)} stasjonskoblinger "
        f"for {len(spots)} spot(s) til {STATION_MAP_CACHE}"
    )
    print(f"[TIDE] Skrev {len(tide_rows)} tide-rader til {TIDE_CACHE}")
    print(f"[TIDE] Skrev lesbar fil til {TIDE_PUBLIC}")


if __name__ == "__main__":
    main()
