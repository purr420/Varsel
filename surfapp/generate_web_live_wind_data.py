import json
import math
import os
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

import requests


UTC = timezone.utc
OSLO = ZoneInfo("Europe/Oslo")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "..", "web")
MAP_DATA_PATH = os.path.join(WEB_DIR, "data.js")
OUTPUT_PATH = os.path.join(WEB_DIR, "live-wind-data.js")
USER_AGENT = "varsel-app/1.0 github.com/purr420"
FROST_SOURCES_URL = "https://frost.met.no/sources/v0.jsonld"
FROST_AVAILABLE_URL = "https://frost.met.no/observations/availableTimeSeries/v0.jsonld"
FROST_OBSERVATIONS_URL = "https://frost.met.no/observations/v0.jsonld"
KYSTVERKET_BASE_URL = "https://mobvaer.kystverket.no/v4"
KYSTVERKET_USER = "publicread"
KYSTVERKET_PASSWORD = "PublicReadOnly"
DISPLAY_MAX_ROWS = 24
DETAIL_SLOT_MINUTES = 5
DETAIL_SLOT_COUNT = 13
HOURLY_ROW_COUNT = DISPLAY_MAX_ROWS - DETAIL_SLOT_COUNT
FREE_LOG_MAX_SAMPLES = 900
HOURLY_LOG_MAX_SAMPLES = 64
FROST_LOOKBACK_HOURS = 16


@dataclass(frozen=True)
class MapSpot:
    name: str
    lat: float
    lon: float


@dataclass(frozen=True)
class StationSpec:
    display_name: str
    frost_aliases: tuple[str, ...] = ()
    kystverket_aliases: tuple[str, ...] = ()
    extra_spots: tuple[str, ...] = ()


STATION_SPECS = [
    StationSpec("Lista Fyr", frost_aliases=("LISTA FYR",), kystverket_aliases=("Lista Fyr",)),
    StationSpec("Søndre Katland", kystverket_aliases=("Søndre Katland",)),
    StationSpec("Lindesnes Fyr", frost_aliases=("LINDESNES FYR",), kystverket_aliases=("Lindesnes Fyr",)),
    StationSpec("Eigerøya", frost_aliases=("EIGERØYA",), kystverket_aliases=("Eigerøya",)),
    StationSpec("Obrestad Fyr", frost_aliases=("OBRESTAD FYR",), kystverket_aliases=("Obrestad Fyr",)),
    StationSpec("Vigdel", kystverket_aliases=("Vigdel",)),
    StationSpec("Sola", frost_aliases=("SOLA",), kystverket_aliases=("Sola",)),
    StationSpec("Kvitsøy - Nordbø", frost_aliases=("KVITSØY - NORDBØ",), kystverket_aliases=("Kvitsøy - Nordbø",)),
    StationSpec("Hemnes", frost_aliases=("KARMØY - HEMNES",), kystverket_aliases=("Hemnes",)),
    StationSpec("Utsira Fyr", frost_aliases=("UTSIRA FYR",), kystverket_aliases=("Utsira Fyr",)),
    StationSpec("Jomfruland", frost_aliases=("JOMFRULAND",), kystverket_aliases=("Jomfruland",)),
    StationSpec("Fugløya", frost_aliases=("LARVIK - FUGLØYA",), kystverket_aliases=("Fugløya",)),
    StationSpec("Svenner Fyr", frost_aliases=("SVENNER FYR",), kystverket_aliases=("Svenner Fyr",)),
    StationSpec("Strømtangen Fyr", frost_aliases=("STRØMTANGEN FYR",), kystverket_aliases=("Strømtangen Fyr",)),
    StationSpec("Vikertangen", kystverket_aliases=("Vikertangen",)),
    StationSpec("Vågsfjorden", kystverket_aliases=("Vågsfjorden",)),
    StationSpec("Kråkenes", frost_aliases=("KRÅKENES",), kystverket_aliases=("Kråkenes",)),
    StationSpec(
        "Svinøy Fyr",
        frost_aliases=("SVINØY FYR",),
        kystverket_aliases=("Svinøy Fyr",),
        extra_spots=("Alnes Lighthouse (Godoy)",),
    ),
    StationSpec("Vigra", frost_aliases=("VIGRA",), kystverket_aliases=("Vigra",)),
    StationSpec("Finnøya", frost_aliases=("FINNØYA FERJEKAI",), kystverket_aliases=("Finnøya",)),
    StationSpec("Ona II", frost_aliases=("ONA II",), kystverket_aliases=("Ona Ii",)),
    StationSpec("Røst Lufthavn", frost_aliases=("RØST LUFTHAVN",), kystverket_aliases=("Røst Lufthavn",)),
    StationSpec("Bodø Havn", kystverket_aliases=("Bodø Havn",)),
    StationSpec("Helligvær II", frost_aliases=("HELLIGVÆR II",), kystverket_aliases=("Helligvær Ii",)),
    StationSpec("Værøy Heliport", frost_aliases=("VÆRØY HELIPORT",), kystverket_aliases=("Værøy Heliport",)),
    StationSpec("Leknes Lufthavn", frost_aliases=("LEKNES LUFTHAVN",), kystverket_aliases=("Leknes Lufthavn",)),
    StationSpec("Bø I Vesterålen III", frost_aliases=("BØ I VESTERÅLEN III",)),
    StationSpec("Anda fyr", frost_aliases=("ANDA FYR II",), kystverket_aliases=("Anda fyr",)),
    StationSpec("Andøya", frost_aliases=("ANDØYA",), kystverket_aliases=("Andøya",)),
    StationSpec("Hekkingen Fyr", frost_aliases=("HEKKINGEN FYR",), kystverket_aliases=("Hekkingen Fyr",)),
    StationSpec("Vadsø Lufthavn", frost_aliases=("VADSØ LUFTHAVN",), kystverket_aliases=("Vadsø Lufthavn",)),
    StationSpec("Slettnes Fyr", frost_aliases=("SLETTNES FYR",), kystverket_aliases=("Slettnes Fyr",)),
    StationSpec("Berlevåg Lufthavn", frost_aliases=("BERLEVÅG LUFTHAVN",), kystverket_aliases=("Berlevåg Lufthavn",)),
    StationSpec("Makkaur Fyr", frost_aliases=("MAKKAUR FYR",), kystverket_aliases=("Makkaur Fyr",)),
    StationSpec("Vardø Lufthavn", frost_aliases=("VARDØ LUFTHAVN",), kystverket_aliases=("Vardø Lufthavn",)),
    StationSpec("Vardø Radio", frost_aliases=("VARDØ RADIO",), kystverket_aliases=("Vardø Radio",)),
]


def load_local_env() -> None:
    for path in (
        os.path.join(BASE_DIR, ".env"),
        os.path.join(os.path.dirname(BASE_DIR), ".env"),
    ):
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value


def parse_iso_utc(ts: str) -> datetime:
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def iso_z(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def local_clock(dt: datetime) -> str:
    return dt.astimezone(OSLO).strftime("%H:%M")


def normalize_name(value: str) -> str:
    lowered = value.casefold()
    lowered = lowered.replace("æ", "ae").replace("ø", "oe").replace("å", "aa")
    lowered = unicodedata.normalize("NFKD", lowered).encode("ascii", "ignore").decode("ascii")
    lowered = re.sub(r"[^0-9a-z]+", " ", lowered)
    return " ".join(lowered.split())


def parse_duration_seconds(value: str) -> int:
    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", value)
    if not match:
        return 10**9
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius_km * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def load_map_spots() -> list[MapSpot]:
    with open(MAP_DATA_PATH, encoding="utf-8") as handle:
        text = handle.read()
    head = text.split("],\n  sources:")[0]
    pattern = re.compile(r'\{\s*name: "([^"]+)", lat: ([0-9.]+), lon: ([0-9.]+)')
    return [
        MapSpot(name=name, lat=float(lat), lon=float(lon))
        for name, lat, lon in pattern.findall(head)
    ]


def nearest_spot_name(spots: list[MapSpot], lat: float, lon: float) -> str:
    return min(spots, key=lambda spot: haversine_km(lat, lon, spot.lat, spot.lon)).name


def station_spots(spec: StationSpec, spots: list[MapSpot], lat: float, lon: float) -> list[str]:
    names = [nearest_spot_name(spots, lat, lon)]
    for extra in spec.extra_spots:
        if extra not in names:
            names.append(extra)
    return names


def login_kystverket(session: requests.Session) -> str:
    response = session.post(
        f"{KYSTVERKET_BASE_URL}/login",
        json={"username": KYSTVERKET_USER, "password": KYSTVERKET_PASSWORD},
        timeout=20,
    )
    response.raise_for_status()
    cookie = response.headers.get("Set-Cookie", "")
    if "H2AUTH=" not in cookie:
        raise RuntimeError("Klarte ikke logge inn mot Kystverket")
    return cookie.split("H2AUTH=")[1].split(";")[0]


def best_named_item(items: list[dict], aliases: tuple[str, ...], key: str) -> Optional[dict]:
    if not aliases:
        return None
    normalized_aliases = [normalize_name(alias) for alias in aliases if alias]
    best_item = None
    best_score = None
    for item in items:
        candidate = normalize_name(str(item.get(key) or ""))
        if not candidate:
            continue
        for alias_index, alias in enumerate(normalized_aliases):
            if candidate == alias:
                score = (0, alias_index, len(candidate))
            elif alias in candidate or candidate in alias:
                score = (1, alias_index, abs(len(candidate) - len(alias)))
            else:
                continue
            if best_score is None or score < best_score:
                best_score = score
                best_item = item
    return best_item


def load_all_frost_sources(session: requests.Session) -> list[dict]:
    response = session.get(
        FROST_SOURCES_URL,
        params={"types": "SensorSystem", "fields": "id,name,geometry"},
        timeout=40,
    )
    response.raise_for_status()
    return response.json().get("data") or []


def load_all_kystverket_stations(session: requests.Session, auth_cookie: str) -> list[dict]:
    response = session.get(
        f"{KYSTVERKET_BASE_URL}/stations",
        headers={"Cookie": f"H2AUTH={auth_cookie}"},
        timeout=40,
    )
    response.raise_for_status()
    return response.json() or []


def resolve_frost_source(all_sources: list[dict], spec: StationSpec) -> Optional[dict]:
    if not spec.frost_aliases:
        return None
    match = best_named_item(all_sources, spec.frost_aliases, "name")
    if not match:
        return None
    coordinates = (match.get("geometry") or {}).get("coordinates") or []
    if len(coordinates) < 2:
        return None
    return {
        "sourceId": f"{match['id']}:0",
        "officialName": match.get("name") or spec.display_name,
        "resolvedLat": float(coordinates[1]),
        "resolvedLon": float(coordinates[0]),
    }


def resolve_kystverket_source(all_stations: list[dict], spec: StationSpec) -> Optional[dict]:
    if not spec.kystverket_aliases:
        return None
    match = best_named_item(all_stations, spec.kystverket_aliases, "Name")
    if not match:
        return None
    lat = match.get("Latitude")
    lon = match.get("Longitude")
    if lat is None or lon is None:
        return None
    return {
        "sourceId": str(match["Id"]),
        "officialName": match.get("Name") or spec.display_name,
        "resolvedLat": float(lat),
        "resolvedLon": float(lon),
    }


def choose_gust_candidate(candidates: list[dict], target_resolution: Optional[str]) -> Optional[dict]:
    if not candidates or not target_resolution:
        return None
    target_seconds = parse_duration_seconds(target_resolution)
    return min(
        candidates,
        key=lambda item: (
            item["timeResolution"] != target_resolution,
            abs(parse_duration_seconds(item["timeResolution"]) - target_seconds),
            parse_duration_seconds(item["timeResolution"]),
        ),
    )


def select_frost_series(session: requests.Session, source_id: str) -> dict:
    response = session.get(
        FROST_AVAILABLE_URL,
        params={
            "sources": source_id,
            "elements": ",".join(
                [
                    "wind_speed",
                    "wind_from_direction",
                    "max(wind_speed_of_gust PT1M)",
                    "max(wind_speed_of_gust PT10M)",
                    "max(wind_speed_of_gust PT20M)",
                    "max(wind_speed_of_gust PT30M)",
                    "max(wind_speed_of_gust PT1H)",
                ]
            ),
        },
        timeout=25,
    )
    response.raise_for_status()
    data = response.json().get("data") or []

    shared_resolutions = sorted(
        {
            item.get("timeResolution")
            for item in data
            if item.get("elementId") in {"wind_speed", "wind_from_direction"} and item.get("timeResolution")
        }
    )
    wind_speed_resolutions = {
        item.get("timeResolution")
        for item in data
        if item.get("elementId") == "wind_speed" and item.get("timeResolution")
    }
    wind_dir_resolutions = {
        item.get("timeResolution")
        for item in data
        if item.get("elementId") == "wind_from_direction" and item.get("timeResolution")
    }
    available = sorted(wind_speed_resolutions & wind_dir_resolutions, key=parse_duration_seconds)
    fine_resolution = available[0] if available else None
    hourly_resolution = "PT1H" if "PT1H" in available else None

    gust_candidates = [
        {"elementId": item.get("elementId"), "timeResolution": item.get("timeResolution")}
        for item in data
        if str(item.get("elementId") or "").startswith("max(wind_speed_of_gust ")
        and item.get("timeResolution")
    ]
    fine_gust = choose_gust_candidate(gust_candidates, fine_resolution)
    hourly_gust = choose_gust_candidate(gust_candidates, hourly_resolution)

    return {
        "fineResolution": fine_resolution,
        "hourlyResolution": hourly_resolution,
        "fineGust": fine_gust,
        "hourlyGust": hourly_gust,
        "gustCandidates": gust_candidates,
        "availableResolutions": available,
    }


def fetch_frost_rows(session: requests.Session, source_id: str, selection: dict, now_utc: datetime) -> dict[str, list[dict]]:
    start = now_utc - timedelta(hours=FROST_LOOKBACK_HOURS)
    elements = {
        "wind_speed",
        "wind_from_direction",
    }
    for candidate in selection.get("gustCandidates") or []:
        if candidate.get("elementId"):
            elements.add(candidate["elementId"])

    response = session.get(
        FROST_OBSERVATIONS_URL,
        params={
            "sources": source_id,
            "elements": ",".join(sorted(elements)),
            "referencetime": f"{iso_z(start)}/{iso_z(now_utc)}",
        },
        timeout=35,
    )
    response.raise_for_status()
    data = response.json().get("data") or []

    rows_by_resolution: dict[str, dict[str, dict]] = {}
    for entry in data:
        dt = parse_iso_utc(entry["referenceTime"])
        grouped_rows: dict[str, dict] = {}
        for obs in entry.get("observations") or []:
            resolution = obs.get("timeResolution")
            if not resolution:
                continue
            row = grouped_rows.setdefault(
                resolution,
                {
                    "timeUtc": iso_z(dt),
                    "timeLocal": local_clock(dt),
                    "windSpeedMs": None,
                    "windDirDeg": None,
                    "windGustMs": None,
                },
            )
            element_id = obs.get("elementId")
            if element_id == "wind_speed":
                row["windSpeedMs"] = obs.get("value")
            elif element_id == "wind_from_direction":
                row["windDirDeg"] = obs.get("value")
            elif str(element_id or "").startswith("max(wind_speed_of_gust "):
                row["windGustMs"] = obs.get("value")
        for resolution, row in grouped_rows.items():
            if (
                row["windSpeedMs"] is None
                and row["windDirDeg"] is None
                and row["windGustMs"] is None
            ):
                continue
            rows_by_resolution.setdefault(resolution, {})[row["timeUtc"]] = row

    return {
        resolution: sorted(rows.values(), key=lambda item: item["timeUtc"], reverse=True)
        for resolution, rows in rows_by_resolution.items()
    }


def fetch_kyst_measurements(
    session: requests.Session,
    auth_cookie: str,
    station_id: str,
    kind: str,
) -> list[dict]:
    response = session.get(
        f"{KYSTVERKET_BASE_URL}/stations/{station_id}/{kind}",
        headers={"Cookie": f"H2AUTH={auth_cookie}"},
        timeout=25,
    )
    response.raise_for_status()
    return response.json() or []


def kyst_measurement_numbers(definitions: list[dict]) -> dict[str, Optional[int]]:
    numbers: dict[str, Optional[int]] = {"windSpeed": None, "windDir": None, "windGust": None}
    for item in definitions:
        name = normalize_name(str(item.get("Name") or ""))
        number = item.get("No")
        if number is None:
            continue
        if name in {"windspd", "vindhastighet 10 meter over bakken"}:
            numbers["windSpeed"] = int(number)
        elif name in {"winddir", "vindretning ff"}:
            numbers["windDir"] = int(number)
        elif name in {"windgus", "kraftigste vindkast siste 10 min"}:
            numbers["windGust"] = int(number)
    return numbers


def parse_kyst_value(sample: dict) -> Optional[float]:
    value = sample.get("Value")
    status = sample.get("Status")
    if value in (None, -999999, -999999.0):
        return None
    if status not in (None, 0):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fetch_kyst_log(
    session: requests.Session,
    auth_cookie: str,
    station_id: str,
    kind: str,
    measurement_no: Optional[int],
    now_utc: datetime,
    max_samples: int,
) -> list[dict]:
    if measurement_no is None:
        return []
    response = session.get(
        f"{KYSTVERKET_BASE_URL}/stations/{station_id}/{kind}/{measurement_no}/log",
        params={"to": iso_z(now_utc), "maxSamples": max_samples},
        headers={"Cookie": f"H2AUTH={auth_cookie}"},
        timeout=30,
    )
    response.raise_for_status()
    raw = response.json() or []
    rows = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        timestamp = item.get("Timestamp")
        if not timestamp:
            continue
        dt = parse_iso_utc(str(timestamp))
        value = parse_kyst_value(item)
        if value is None:
            continue
        rows.append({"time": dt, "value": value})
    rows.sort(key=lambda item: item["time"])
    return rows


def fetch_kyst_snapshot(session: requests.Session, auth_cookie: str, station_id: str) -> Optional[dict]:
    response = session.get(
        f"{KYSTVERKET_BASE_URL}/stations/{station_id}/instantaneous/valuesnames",
        headers={"Cookie": f"H2AUTH={auth_cookie}"},
        timeout=25,
    )
    response.raise_for_status()
    data = response.json() or []
    lookup = {normalize_name(str(item.get("Name") or "")): item for item in data if item.get("Name")}

    def value(*names: str) -> Optional[float]:
        for name in names:
            item = lookup.get(normalize_name(name)) or {}
            parsed = parse_kyst_value(item)
            if parsed is not None:
                return parsed
        return None

    def timestamp(*names: str) -> Optional[str]:
        for name in names:
            item = lookup.get(normalize_name(name)) or {}
            raw = item.get("Timestamp")
            if raw:
                return iso_z(parse_iso_utc(str(raw)))
        return None

    snapshot = {
        "sensorTimeUtc": timestamp("Vindhastighet (10 meter over bakken)", "WINDSPD", "Vindretning (FF)", "WINDDIR", "Kraftigste vindkast (siste 10 min)", "WINDGUS"),
        "fetchTimeUtc": iso_z(datetime.now(UTC)),
        "windSpeedMs": value("Vindhastighet (10 meter over bakken)", "WINDSPD"),
        "windDirDeg": value("Vindretning (FF)", "WINDDIR"),
        "windGustMs": value("Kraftigste vindkast (siste 10 min)", "WINDGUS"),
        "windGustDirDeg": value("WINDGUSDIR"),
    }
    if snapshot["windSpeedMs"] is None and snapshot["windDirDeg"] is None and snapshot["windGustMs"] is None:
        return None
    return snapshot


def append_snapshot_sample(samples: list[dict], snapshot_time: Optional[str], snapshot_value: Optional[float]) -> list[dict]:
    if snapshot_time is None or snapshot_value is None:
        return samples
    dt = parse_iso_utc(snapshot_time)
    if any(abs((item["time"] - dt).total_seconds()) < 1 for item in samples):
        return samples
    return sorted([*samples, {"time": dt, "value": snapshot_value}], key=lambda item: item["time"])


def current_detail_slot(now_utc: datetime) -> datetime:
    slot_minute = (now_utc.minute // DETAIL_SLOT_MINUTES) * DETAIL_SLOT_MINUTES
    return now_utc.replace(minute=slot_minute, second=0, microsecond=0)


def detail_slot_times(now_utc: datetime) -> list[datetime]:
    end_slot = current_detail_slot(now_utc)
    return [end_slot - timedelta(minutes=DETAIL_SLOT_MINUTES * index) for index in range(DETAIL_SLOT_COUNT)]


def hourly_slot_times(now_utc: datetime) -> list[datetime]:
    hour_floor = current_detail_slot(now_utc).replace(minute=0)
    return [hour_floor - timedelta(hours=index + 1) for index in range(HOURLY_ROW_COUNT)]


def closest_sample(
    samples: list[dict],
    target: datetime,
    *,
    preferred_start: Optional[datetime] = None,
    preferred_end: Optional[datetime] = None,
    max_delta: Optional[timedelta] = None,
) -> Optional[dict]:
    if not samples:
        return None
    preferred = [
        sample
        for sample in samples
        if (preferred_start is None or sample["time"] >= preferred_start)
        and (preferred_end is None or sample["time"] < preferred_end)
    ]
    candidate_pool = preferred or samples
    best = min(candidate_pool, key=lambda sample: abs((sample["time"] - target).total_seconds()))
    if max_delta is not None and abs((best["time"] - target).total_seconds()) > max_delta.total_seconds():
        return None
    return best


def rows_by_time(rows: list[dict]) -> list[dict]:
    return sorted(
        [row for row in rows if row.get("timeUtc")],
        key=lambda item: item["timeUtc"],
    )


def closest_row(rows: list[dict], target: datetime, max_delta: Optional[timedelta] = None) -> Optional[dict]:
    if not rows:
        return None
    best = min(rows, key=lambda row: abs((parse_iso_utc(row["timeUtc"]) - target).total_seconds()))
    if max_delta is not None and abs((parse_iso_utc(best["timeUtc"]) - target).total_seconds()) > max_delta.total_seconds():
        return None
    return best


def row_with_label(
    label_time: datetime,
    wind_speed: Optional[float],
    wind_dir: Optional[float],
    wind_gust: Optional[float],
) -> dict:
    return {
        "timeUtc": iso_z(label_time),
        "timeLocal": local_clock(label_time),
        "windSpeedMs": wind_speed,
        "windDirDeg": wind_dir,
        "windGustMs": wind_gust,
    }


def row_has_any_value(row: Optional[dict]) -> bool:
    if not row:
        return False
    return any(
        value is not None and isinstance(value, (int, float)) and math.isfinite(value)
        for value in (row.get("windSpeedMs"), row.get("windDirDeg"), row.get("windGustMs"))
    )


def kyst_row_from_samples(
    speed_samples: list[dict],
    dir_samples: list[dict],
    gust_samples: list[dict],
    label_time: datetime,
    *,
    preferred_start: Optional[datetime] = None,
    preferred_end: Optional[datetime] = None,
    max_delta: Optional[timedelta] = None,
) -> Optional[dict]:
    row = row_with_label(
        label_time,
        (closest_sample(
            speed_samples,
            label_time,
            preferred_start=preferred_start,
            preferred_end=preferred_end,
            max_delta=max_delta,
        ) or {}).get("value"),
        (closest_sample(
            dir_samples,
            label_time,
            preferred_start=preferred_start,
            preferred_end=preferred_end,
            max_delta=max_delta,
        ) or {}).get("value"),
        (closest_sample(
            gust_samples,
            label_time,
            preferred_start=preferred_start,
            preferred_end=preferred_end,
            max_delta=max_delta,
        ) or {}).get("value"),
    )
    return row if row_has_any_value(row) else None


def merge_rows(primary: Optional[dict], fallback: Optional[dict], label_time: datetime) -> Optional[dict]:
    if not row_has_any_value(primary) and not row_has_any_value(fallback):
        return None
    return row_with_label(
        label_time,
        primary.get("windSpeedMs") if row_has_any_value(primary) and primary.get("windSpeedMs") is not None else fallback.get("windSpeedMs") if fallback else None,
        primary.get("windDirDeg") if row_has_any_value(primary) and primary.get("windDirDeg") is not None else fallback.get("windDirDeg") if fallback else None,
        primary.get("windGustMs") if row_has_any_value(primary) and primary.get("windGustMs") is not None else fallback.get("windGustMs") if fallback else None,
    )


def sample_frost_row_to_slot(rows: list[dict], slot_time: datetime, slot_minutes: int) -> Optional[dict]:
    if not rows:
        return None
    slot_end = slot_time + timedelta(minutes=slot_minutes)
    candidates = [
        row for row in rows
        if slot_time <= parse_iso_utc(row["timeUtc"]) < slot_end
    ]
    chosen = candidates[-1] if candidates else closest_row(rows, slot_time, max_delta=timedelta(minutes=slot_minutes))
    if not chosen:
        return None
    return row_with_label(slot_time, chosen.get("windSpeedMs"), chosen.get("windDirDeg"), chosen.get("windGustMs"))


def build_frost_detail_rows(rows: list[dict], resolution: Optional[str], now_utc: datetime) -> list[dict]:
    if not rows or not resolution:
        return []
    resolution_seconds = parse_duration_seconds(resolution)
    end_slot = current_detail_slot(now_utc)
    window_start = end_slot - timedelta(minutes=DETAIL_SLOT_MINUTES * (DETAIL_SLOT_COUNT - 1))
    if resolution_seconds <= DETAIL_SLOT_MINUTES * 60:
        sampled = [
            sample_frost_row_to_slot(rows, slot_time, DETAIL_SLOT_MINUTES)
            for slot_time in detail_slot_times(now_utc)
        ]
        return [row for row in sampled if row_has_any_value(row)]
    filtered = [
        row for row in rows
        if window_start <= parse_iso_utc(row["timeUtc"]) <= end_slot
    ]
    filtered.sort(key=lambda item: item["timeUtc"], reverse=True)
    return filtered


def build_kyst_noninstant_detail_rows(
    speed_samples: list[dict],
    dir_samples: list[dict],
    gust_samples: list[dict],
    now_utc: datetime,
) -> list[dict]:
    end_slot = current_detail_slot(now_utc)
    window_start = end_slot - timedelta(hours=1)
    timestamps = sorted(
        {
            sample["time"].replace(second=0, microsecond=0)
            for sample in [*speed_samples, *dir_samples, *gust_samples]
            if window_start <= sample["time"] <= end_slot
        },
        reverse=True,
    )
    rows = [
        kyst_row_from_samples(
            speed_samples,
            dir_samples,
            gust_samples,
            label_time,
            max_delta=timedelta(minutes=30),
        )
        for label_time in timestamps
    ]
    return [row for row in rows if row_has_any_value(row)]


def circular_mean_degrees(values: list[float]) -> Optional[float]:
    if not values:
        return None
    sin_sum = sum(math.sin(math.radians(value)) for value in values)
    cos_sum = sum(math.cos(math.radians(value)) for value in values)
    if abs(sin_sum) < 1e-9 and abs(cos_sum) < 1e-9:
        return None
    angle = math.degrees(math.atan2(sin_sum, cos_sum))
    return angle % 360


def hourly_row_from_kyst_samples(
    speed_samples: list[dict],
    dir_samples: list[dict],
    gust_samples: list[dict],
    hour_end: datetime,
) -> Optional[dict]:
    hour_start = hour_end - timedelta(hours=1)
    speed_values = [item["value"] for item in speed_samples if hour_start <= item["time"] < hour_end]
    dir_values = [item["value"] for item in dir_samples if hour_start <= item["time"] < hour_end]
    gust_values = [item["value"] for item in gust_samples if hour_start <= item["time"] < hour_end]

    if speed_values or dir_values or gust_values:
        return row_with_label(
            hour_end,
            sum(speed_values) / len(speed_values) if speed_values else None,
            circular_mean_degrees(dir_values),
            max(gust_values) if gust_values else None,
        )

    speed_nearest = closest_sample(speed_samples, hour_end, max_delta=timedelta(minutes=45))
    dir_nearest = closest_sample(dir_samples, hour_end, max_delta=timedelta(minutes=45))
    gust_nearest = closest_sample(gust_samples, hour_end, max_delta=timedelta(minutes=45))
    fallback = row_with_label(
        hour_end,
        speed_nearest["value"] if speed_nearest else None,
        dir_nearest["value"] if dir_nearest else None,
        gust_nearest["value"] if gust_nearest else None,
    )
    return fallback if row_has_any_value(fallback) else None


def hourly_row_from_kyst_hour_samples(
    speed_samples: list[dict],
    dir_samples: list[dict],
    gust_samples: list[dict],
    hour_end: datetime,
) -> Optional[dict]:
    return kyst_row_from_samples(
        speed_samples,
        dir_samples,
        gust_samples,
        hour_end,
        preferred_start=hour_end - timedelta(minutes=5),
        preferred_end=hour_end + timedelta(minutes=5),
        max_delta=timedelta(minutes=70),
    )


def build_station_column(
    spec: StationSpec,
    spot_name: str,
    now_utc: datetime,
    frost: Optional[dict],
    kyst: Optional[dict],
) -> Optional[dict]:
    frost_fine_rows = frost.get("fineRows") if frost else []
    frost_hourly_rows = frost.get("hourlyRows") if frost else []
    frost_detail_rows = build_frost_detail_rows(frost_fine_rows, frost.get("fineResolution") if frost else None, now_utc)

    kyst_speed = kyst.get("speedSamples") if kyst else []
    kyst_dir = kyst.get("dirSamples") if kyst else []
    kyst_gust = kyst.get("gustSamples") if kyst else []
    kyst_hour_speed = kyst.get("hourSpeedSamples") if kyst else []
    kyst_hour_dir = kyst.get("hourDirSamples") if kyst else []
    kyst_hour_gust = kyst.get("hourGustSamples") if kyst else []

    detailed_rows: list[dict] = []
    if kyst and kyst.get("snapshot"):
        for slot_time in detail_slot_times(now_utc):
            slot_end = slot_time + timedelta(minutes=DETAIL_SLOT_MINUTES)
            primary = kyst_row_from_samples(
                kyst_speed,
                kyst_dir,
                kyst_gust,
                slot_time,
                preferred_start=slot_time,
                preferred_end=slot_end,
                max_delta=timedelta(minutes=DETAIL_SLOT_MINUTES),
            )
            fallback = closest_row(frost_detail_rows, slot_time, max_delta=timedelta(minutes=30))
            merged = merge_rows(primary, fallback, slot_time)
            if merged:
                detailed_rows.append(merged)
    elif kyst:
        for primary in build_kyst_noninstant_detail_rows(kyst_speed, kyst_dir, kyst_gust, now_utc):
            label_time = parse_iso_utc(primary["timeUtc"])
            fallback = closest_row(frost_detail_rows, label_time, max_delta=timedelta(minutes=30))
            merged = merge_rows(primary, fallback, label_time)
            if merged:
                detailed_rows.append(merged)
        if not detailed_rows:
            detailed_rows = frost_detail_rows
    else:
        detailed_rows = frost_detail_rows

    hourly_rows: list[dict] = []
    for hour_time in hourly_slot_times(now_utc):
        primary = None
        if kyst:
            if kyst_hour_speed or kyst_hour_dir or kyst_hour_gust:
                primary = hourly_row_from_kyst_hour_samples(kyst_hour_speed, kyst_hour_dir, kyst_hour_gust, hour_time)
            if primary is None:
                primary = hourly_row_from_kyst_samples(kyst_speed, kyst_dir, kyst_gust, hour_time)
        fallback_source = frost_hourly_rows or frost_fine_rows
        fallback = closest_row(fallback_source, hour_time, max_delta=timedelta(minutes=70)) if fallback_source else None
        merged = merge_rows(primary, fallback, hour_time)
        if merged:
            hourly_rows.append(merged)

    rows = [*detailed_rows, *hourly_rows]
    rows.sort(key=lambda item: item["timeUtc"], reverse=True)
    rows = rows[:DISPLAY_MAX_ROWS]
    if not rows:
        return None

    providers = []
    if frost:
        providers.append("Frost")
    if kyst:
        providers.append("Kystverket")
    return {
        "name": spec.display_name,
        "linkedSpot": spot_name,
        "providerLabel": " + ".join(providers),
        "rows": rows,
    }


def build_payload() -> dict:
    load_local_env()
    client_id = os.getenv("FROST_CLIENT_ID")
    if not client_id:
        raise RuntimeError("Mangler FROST_CLIENT_ID i miljo eller .env")

    map_spots = load_map_spots()
    frost_session = requests.Session()
    frost_session.auth = (client_id, "")
    frost_session.headers.update({"User-Agent": USER_AGENT})
    all_frost_sources = load_all_frost_sources(frost_session)

    kyst_session = requests.Session()
    kyst_session.headers.update({"User-Agent": USER_AGENT})
    auth_cookie = login_kystverket(kyst_session)
    all_kyst_stations = load_all_kystverket_stations(kyst_session, auth_cookie)

    now_utc = datetime.now(UTC)
    payload = {
        "generatedAtUtc": iso_z(now_utc),
        "sources": {},
        "instantSources": {},
        "observationSpots": {},
    }

    for spec in STATION_SPECS:
        frost_resolved = resolve_frost_source(all_frost_sources, spec)
        kyst_resolved = resolve_kystverket_source(all_kyst_stations, spec)
        primary_lat = (
            (kyst_resolved or frost_resolved or {}).get("resolvedLat")
        )
        primary_lon = (
            (kyst_resolved or frost_resolved or {}).get("resolvedLon")
        )
        if primary_lat is None or primary_lon is None:
            continue
        spots_for_station = station_spots(spec, map_spots, primary_lat, primary_lon)
        primary_spot = spots_for_station[0]

        frost_payload = None
        if frost_resolved:
            selection = select_frost_series(frost_session, frost_resolved["sourceId"])
            raw_rows = fetch_frost_rows(frost_session, frost_resolved["sourceId"], selection, now_utc)
            frost_payload = {
                "name": spec.display_name,
                "provider": "Frost",
                "linkedSpot": primary_spot,
                "sourceId": frost_resolved["sourceId"],
                "officialName": frost_resolved["officialName"],
                "resolvedLat": round(frost_resolved["resolvedLat"], 6),
                "resolvedLon": round(frost_resolved["resolvedLon"], 6),
                "fineResolution": selection["fineResolution"],
                "hourlyResolution": selection["hourlyResolution"],
                "fineRows": raw_rows.get(selection["fineResolution"] or "", []),
                "hourlyRows": raw_rows.get(selection["hourlyResolution"] or "", []),
            }
            popup_rows = frost_payload["fineRows"] or frost_payload["hourlyRows"]
            payload["sources"][f"{spec.display_name}__{primary_spot}"] = {
                "name": spec.display_name,
                "provider": "Frost",
                "linkedSpot": primary_spot,
                "sourceId": frost_resolved["sourceId"],
                "officialName": frost_resolved["officialName"],
                "resolvedLat": round(frost_resolved["resolvedLat"], 6),
                "resolvedLon": round(frost_resolved["resolvedLon"], 6),
                "windResolution": selection["fineResolution"] or selection["hourlyResolution"],
                "gustResolution": (
                    (selection.get("fineGust") or {}).get("timeResolution")
                    or (selection.get("hourlyGust") or {}).get("timeResolution")
                ),
                "gustElementId": (
                    (selection.get("fineGust") or {}).get("elementId")
                    or (selection.get("hourlyGust") or {}).get("elementId")
                ),
                "latestTimeUtc": popup_rows[0]["timeUtc"] if popup_rows else None,
                "rows": popup_rows[:DISPLAY_MAX_ROWS],
            }

        kyst_payload = None
        if kyst_resolved:
            free_defs = fetch_kyst_measurements(kyst_session, auth_cookie, kyst_resolved["sourceId"], "free")
            free_numbers = kyst_measurement_numbers(free_defs)
            hour_defs = fetch_kyst_measurements(kyst_session, auth_cookie, kyst_resolved["sourceId"], "hour")
            hour_numbers = kyst_measurement_numbers(hour_defs)
            snapshot = fetch_kyst_snapshot(kyst_session, auth_cookie, kyst_resolved["sourceId"])
            speed_samples = fetch_kyst_log(
                kyst_session,
                auth_cookie,
                kyst_resolved["sourceId"],
                "free",
                free_numbers["windSpeed"],
                now_utc,
                FREE_LOG_MAX_SAMPLES,
            )
            dir_samples = fetch_kyst_log(
                kyst_session,
                auth_cookie,
                kyst_resolved["sourceId"],
                "free",
                free_numbers["windDir"],
                now_utc,
                FREE_LOG_MAX_SAMPLES,
            )
            gust_samples = fetch_kyst_log(
                kyst_session,
                auth_cookie,
                kyst_resolved["sourceId"],
                "free",
                free_numbers["windGust"],
                now_utc,
                FREE_LOG_MAX_SAMPLES,
            )
            hour_speed_samples = fetch_kyst_log(
                kyst_session,
                auth_cookie,
                kyst_resolved["sourceId"],
                "hour",
                hour_numbers["windSpeed"],
                now_utc,
                HOURLY_LOG_MAX_SAMPLES,
            )
            hour_dir_samples = fetch_kyst_log(
                kyst_session,
                auth_cookie,
                kyst_resolved["sourceId"],
                "hour",
                hour_numbers["windDir"],
                now_utc,
                HOURLY_LOG_MAX_SAMPLES,
            )
            hour_gust_samples = fetch_kyst_log(
                kyst_session,
                auth_cookie,
                kyst_resolved["sourceId"],
                "hour",
                hour_numbers["windGust"],
                now_utc,
                HOURLY_LOG_MAX_SAMPLES,
            )
            if snapshot:
                speed_samples = append_snapshot_sample(speed_samples, snapshot.get("sensorTimeUtc"), snapshot.get("windSpeedMs"))
                dir_samples = append_snapshot_sample(dir_samples, snapshot.get("sensorTimeUtc"), snapshot.get("windDirDeg"))
                gust_samples = append_snapshot_sample(gust_samples, snapshot.get("sensorTimeUtc"), snapshot.get("windGustMs"))
            kyst_payload = {
                "name": spec.display_name,
                "provider": "Kystverket",
                "linkedSpot": primary_spot,
                "sourceId": kyst_resolved["sourceId"],
                "officialName": kyst_resolved["officialName"],
                "resolvedLat": round(kyst_resolved["resolvedLat"], 6),
                "resolvedLon": round(kyst_resolved["resolvedLon"], 6),
                "speedSamples": speed_samples,
                "dirSamples": dir_samples,
                "gustSamples": gust_samples,
                "hourSpeedSamples": hour_speed_samples,
                "hourDirSamples": hour_dir_samples,
                "hourGustSamples": hour_gust_samples,
                "snapshot": snapshot,
            }
            if snapshot:
                payload["instantSources"][f"{spec.display_name}__{primary_spot}"] = {
                    "name": spec.display_name,
                    "provider": "Kystverket",
                    "linkedSpot": primary_spot,
                    "sourceId": kyst_resolved["sourceId"],
                    "officialName": kyst_resolved["officialName"],
                    "resolvedLat": round(kyst_resolved["resolvedLat"], 6),
                    "resolvedLon": round(kyst_resolved["resolvedLon"], 6),
                    "sensorTimeUtc": snapshot["sensorTimeUtc"],
                    "latestObservation": snapshot,
                }

        for spot_name in spots_for_station:
            column = build_station_column(spec, spot_name, now_utc, frost_payload, kyst_payload)
            if not column:
                continue
            payload["observationSpots"].setdefault(spot_name, []).append(column)

    order = {spec.display_name: index for index, spec in enumerate(STATION_SPECS)}
    for spot_name, columns in payload["observationSpots"].items():
        columns.sort(key=lambda column: order.get(column["name"], 10**9))

    return payload


def main() -> None:
    payload = build_payload()
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        handle.write(
            f"// Generated by surfapp/generate_web_live_wind_data.py at {payload['generatedAtUtc']}\n"
        )
        handle.write("window.LIVE_WIND_DATA = ")
        json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
        handle.write(";\n")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
