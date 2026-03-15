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

DEFAULT_STREAMLIT_SPOTS = ("Lista",)


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


def fetch_dmi_dkss_for_spot(
    spot: Spot,
) -> tuple[dict[datetime, float], Optional[float], Optional[float], Optional[float]]:
    base_params = {
        "coords": f"POINT({spot.lon:.6f} {spot.lat:.6f})",
        "crs": "crs84",
        "parameter-name": "sea-mean-deviation",
        "api-key": DMI_API_KEY_EDR,
        "f": "GeoJSON",
    }
    try:
        resp = requests.get(
            DMI_DKSS_POSITION_URL,
            params=base_params,
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return {}, None, None, None

    features = data.get("features") or []
    rows: dict[datetime, float] = {}
    chosen_lat: Optional[float] = None
    chosen_lon: Optional[float] = None
    chosen_distance_km: Optional[float] = None

    for feature in features:
        geometry = feature.get("geometry") or {}
        coords = geometry.get("coordinates") or []
        props = feature.get("properties") or {}
        value = props.get("sea-mean-deviation")
        step = props.get("step")
        if len(coords) >= 2 and chosen_lat is None and chosen_lon is None:
            chosen_lon = float(coords[0])
            chosen_lat = float(coords[1])
            chosen_distance_km = haversine_km(spot.lat, spot.lon, chosen_lat, chosen_lon)
        if value is None or not step:
            continue
        try:
            rows[parse_iso_utc(step)] = float(value)
        except (TypeError, ValueError):
            continue

    if rows:
        return rows, chosen_lat, chosen_lon, chosen_distance_km

    start_dt = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    end_dt = start_dt + timedelta(days=3)
    cube_common = {
        "crs": "crs84",
        "parameter-name": "sea-mean-deviation",
        "api-key": DMI_API_KEY_EDR,
        "f": "GeoJSON",
        "datetime": f"{start_dt.isoformat()}/{end_dt.isoformat()}",
    }
    search_radii_deg = (0.35, 0.7)

    for radius in search_radii_deg:
        params = dict(cube_common)
        params["bbox"] = (
            f"{spot.lon - radius:.6f},{spot.lat - radius:.6f},"
            f"{spot.lon + radius:.6f},{spot.lat + radius:.6f}"
        )
        try:
            resp = requests.get(
                DMI_DKSS_CUBE_URL,
                params=params,
                headers={"User-Agent": USER_AGENT},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError):
            continue

        grouped: dict[tuple[float, float], dict[datetime, float]] = {}
        for feature in data.get("features") or []:
            geometry = feature.get("geometry") or {}
            coords = geometry.get("coordinates") or []
            props = feature.get("properties") or {}
            value = props.get("sea-mean-deviation")
            step = props.get("step")
            if len(coords) < 2 or value is None or not step:
                continue
            key = (float(coords[1]), float(coords[0]))
            try:
                grouped.setdefault(key, {})[parse_iso_utc(step)] = float(value)
            except (TypeError, ValueError):
                continue

        if not grouped:
            continue

        best = min(
            grouped.items(),
            key=lambda item: (
                haversine_km(spot.lat, spot.lon, item[0][0], item[0][1]),
                -len(item[1]),
            ),
        )
        (chosen_lat, chosen_lon), rows = best
        chosen_distance_km = haversine_km(spot.lat, spot.lon, chosen_lat, chosen_lon)
        return rows, chosen_lat, chosen_lon, chosen_distance_km

    return rows, chosen_lat, chosen_lon, chosen_distance_km


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
        if len(parts) < 8 or not parts[0].isdigit():
            continue
        year, month, day, hour, minute = (int(parts[i]) for i in range(5))
        if minute != 0:
            continue
        dt = datetime(year, month, day, hour, minute, tzinfo=UTC)
        rows[dt] = {
            "surge_m": float(parts[5]),
            "met_tide_m": float(parts[6]),
            "total_m": float(parts[7]),
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
                "met_tide_m",
                "total_water_level_m",
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
        dkss_rows, dkss_point_lat, dkss_point_lon, dkss_distance_km = fetch_dmi_dkss_for_spot(spot)
        station_rows[-1]["dkss_point_lat"] = (
            f"{dkss_point_lat:.6f}" if dkss_point_lat is not None else ""
        )
        station_rows[-1]["dkss_point_lon"] = (
            f"{dkss_point_lon:.6f}" if dkss_point_lon is not None else ""
        )
        station_rows[-1]["dkss_distance_km"] = (
            f"{dkss_distance_km:.1f}" if dkss_distance_km is not None else ""
        )

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
                    "met_tide_m": (
                        f"{corrected_row['met_tide_m']:.3f}" if "met_tide_m" in corrected_row else ""
                    ),
                    "total_water_level_m": (
                        f"{corrected_row['total_m']:.3f}" if "total_m" in corrected_row else ""
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
