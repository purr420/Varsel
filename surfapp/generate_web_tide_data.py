import json
import math
import os
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

import requests


UTC = timezone.utc
OSLO = ZoneInfo("Europe/Oslo")
USER_AGENT = "varsel-app/1.0 github.com/purr420"
KARTVERKET_STATIONLIST_URL = (
    "https://vannstand.kartverket.no/tideapi.php"
    "?tide_request=stationlist&type=perm&lang=en"
)
KARTVERKET_LOCATIONDATA_URL = "https://vannstand.kartverket.no/tideapi.php"
DMI_DKSS_POSITION_ENDPOINTS = (
    (
        "opendataapi.dmi.dk",
        "https://opendataapi.dmi.dk/v1/forecastedr/collections/dkss_nsbs/position",
    ),
    (
        "dmigw.govcloud.dk",
        "https://dmigw.govcloud.dk/v1/forecastedr/collections/dkss_nsbs/position",
    ),
)
DMI_API_KEY_EDR = os.getenv("DMI_API_KEY_EDR", "ae501bfc-112e-400e-89df-77a2a6b9af72")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(BASE_DIR, "..", "web", "tide-data.js")
DAY_COUNT = 5
DMI_TIMEOUT_SECONDS = 20
DMI_MAX_ATTEMPTS = 3
DMI_RETRY_BASE_SECONDS = 1.2
DMI_REQUEST_SPACING_SECONDS = 0.35


@dataclass(frozen=True)
class DkssPoint:
    source_name: str
    lat: float
    lon: float


@dataclass(frozen=True)
class SpotConfig:
    name: str
    lat: float
    lon: float
    tide_station_override: Optional[str] = None
    dkss_point: Optional[DkssPoint] = None


@dataclass(frozen=True)
class TideStation:
    name: str
    code: str
    lat: float
    lon: float


SPOTS = [
    SpotConfig(
        "Lista",
        58.006104,
        6.468337,
        dkss_point=DkssPoint("Lista DKSS gridpunkt", 58.090000, 6.560000),
    ),
    SpotConfig(
        "Pigsty/Piggy",
        58.767823,
        5.288713,
        tide_station_override="SBG",
        dkss_point=DkssPoint("Jaeren DKSS gridpunkt", 58.751998, 5.471719),
    ),
    SpotConfig(
        "Saltstein",
        58.770031,
        9.792522,
        dkss_point=DkssPoint("Saltstein DKSS gridpunkt", 58.967206, 9.809798),
    ),
    SpotConfig("Ervika", 62.222712, 4.966103),
    SpotConfig("Alnes Lighthouse (Godoy)", 62.506226, 5.702142),
    SpotConfig("Hustadvika Gjestegard", 62.992319, 7.028400),
    SpotConfig("Unstad Beach", 68.277434, 13.221921),
    SpotConfig("Persfjord", 70.450232, 31.046501),
    SpotConfig(
        "Mandal / Sjosanden",
        57.874278,
        7.313109,
        dkss_point=DkssPoint("Sjosanden DKSS testpunkt", 58.011000, 7.455000),
    ),
]


def parse_iso_utc(ts: str) -> datetime:
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def iso_z(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def load_existing_payload() -> dict:
    if not os.path.exists(OUTPUT_PATH):
        return {}
    try:
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        marker = "window.TIDE_DATA = "
        if marker not in content:
            return {}
        json_text = content.split(marker, 1)[1].rsplit(";", 1)[0].strip()
        return json.loads(json_text)
    except Exception:
        return {}


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


def local_day_bounds(day_count: int) -> tuple[datetime, datetime]:
    now_local = datetime.now(OSLO)
    start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = start_local + timedelta(days=day_count)
    return start_local.astimezone(UTC), end_local.astimezone(UTC)


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
        stations.append(
            TideStation(
                name=loc.attrib["name"],
                code=loc.attrib["code"],
                lat=float(loc.attrib["latitude"]),
                lon=float(loc.attrib["longitude"]),
            )
        )
    return stations


def station_for_spot(spot: SpotConfig, stations: list[TideStation]) -> tuple[TideStation, float]:
    if spot.tide_station_override:
        for station in stations:
            if station.code == spot.tide_station_override:
                return station, haversine_km(spot.lat, spot.lon, station.lat, station.lon)

    ranked = sorted(
        (
            (haversine_km(spot.lat, spot.lon, station.lat, station.lon), station)
            for station in stations
        ),
        key=lambda item: item[0],
    )
    return ranked[0][1], ranked[0][0]


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
        "refcode": "cd",
        "interval": "10",
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
        predictions[parse_iso_utc(ts)] = float(value_cm) / 100.0
    return predictions


def fetch_kartverket_tide_events(
    station: TideStation,
    start_dt: datetime,
    end_dt: datetime,
) -> list[dict]:
    params = {
        "tide_request": "locationdata",
        "lat": f"{station.lat:.6f}",
        "lon": f"{station.lon:.6f}",
        "fromtime": start_dt.strftime("%Y-%m-%dT%H:%M"),
        "totime": end_dt.strftime("%Y-%m-%dT%H:%M"),
        "datatype": "tab",
        "refcode": "cd",
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
        return []

    events = []
    for waterlevel in root.findall(".//waterlevel"):
        value_cm = waterlevel.attrib.get("value")
        ts = waterlevel.attrib.get("time")
        flag = waterlevel.attrib.get("flag")
        if not value_cm or not ts or flag not in {"high", "low"}:
            continue
        events.append(
            {
                "time": parse_iso_utc(ts),
                "kind": flag,
                "astronomical": float(value_cm) / 100.0,
            }
        )
    return events


def nearest_astronomical_value(
    astronomical_rows: dict[datetime, float],
    target_dt: datetime,
) -> Optional[float]:
    best_dt = None
    best_delta = None
    for dt, value in astronomical_rows.items():
        delta = abs((dt - target_dt).total_seconds())
        if best_delta is None or delta < best_delta:
            best_delta = delta
            best_dt = dt
    if best_dt is None or best_delta is None or best_delta > 31 * 60:
        return None
    return astronomical_rows[best_dt]


def reuse_existing_dkss_payload(
    existing_payload: dict,
    spot_name: str,
    start_dt: datetime,
    end_dt: datetime,
) -> Optional[dict]:
    existing_spot = (existing_payload.get("spots") or {}).get(spot_name) or {}
    existing_dkss = existing_spot.get("dkss")
    if not existing_dkss:
        return None

    filtered_rows = []
    last_time = None
    for row in existing_dkss.get("rows") or []:
        time_utc = row.get("timeUtc")
        if not time_utc:
            continue
        dt = parse_iso_utc(time_utc)
        if dt < start_dt or dt > end_dt:
            continue
        filtered_rows.append(row)
        last_time = time_utc

    if not filtered_rows:
        return None

    reused = dict(existing_dkss)
    reused["rows"] = filtered_rows
    reused["throughUtc"] = last_time
    reused["reusedFromExisting"] = True
    return reused


def fetch_dmi_dkss_position_rows(
    lat: float,
    lon: float,
    start_dt: datetime,
    end_dt: datetime,
) -> tuple[dict[datetime, float], Optional[float], Optional[float], str]:
    params = {
        "coords": f"POINT({lon:.6f} {lat:.6f})",
        "crs": "crs84",
        "parameter-name": "sea-mean-deviation",
        "datetime": f"{iso_z(start_dt)}/{iso_z(end_dt)}",
        "api-key": DMI_API_KEY_EDR,
        "f": "GeoJSON",
    }
    endpoint_errors: list[str] = []

    for endpoint_host, endpoint_url in DMI_DKSS_POSITION_ENDPOINTS:
        data = None
        last_exc: Optional[requests.RequestException] = None
        for attempt in range(1, DMI_MAX_ATTEMPTS + 1):
            try:
                resp = requests.get(
                    endpoint_url,
                    params=params,
                    headers={"User-Agent": USER_AGENT},
                    timeout=DMI_TIMEOUT_SECONDS,
                )
                resp.raise_for_status()
                data = resp.json()
                break
            except requests.RequestException as exc:
                last_exc = exc
                if attempt >= DMI_MAX_ATTEMPTS:
                    break
                time.sleep(DMI_RETRY_BASE_SECONDS * attempt)

        if data is None:
            if last_exc is not None:
                endpoint_errors.append(f"{endpoint_host}: {last_exc}")
            continue

        rows: dict[datetime, float] = {}
        used_lat = None
        used_lon = None
        for feature in data.get("features") or []:
            geometry = feature.get("geometry") or {}
            coords = geometry.get("coordinates") or []
            props = feature.get("properties") or {}
            value = props.get("sea-mean-deviation")
            step = props.get("step")
            if len(coords) >= 2 and used_lat is None and used_lon is None:
                used_lon = float(coords[0])
                used_lat = float(coords[1])
            if value is None or not step:
                continue
            rows[parse_iso_utc(step)] = float(value)
        return rows, used_lat, used_lon, endpoint_host

    message = "; ".join(endpoint_errors) if endpoint_errors else "Unknown DKSS request failure"
    raise requests.RequestException(message)


def build_payload() -> dict:
    existing_payload = load_existing_payload()
    stations = fetch_station_list()
    start_dt, end_dt = local_day_bounds(DAY_COUNT)
    payload = {
        "generatedAtUtc": iso_z(datetime.now(UTC)),
        "startUtc": iso_z(start_dt),
        "endUtc": iso_z(end_dt),
        "dayCount": DAY_COUNT,
        "spots": {},
    }

    for spot in SPOTS:
        station, station_distance_km = station_for_spot(spot, stations)
        astronomical = fetch_kartverket_predictions(station, start_dt, end_dt)
        events = fetch_kartverket_tide_events(station, start_dt, end_dt)

        series = []
        for dt in sorted(astronomical):
            if dt < start_dt or dt > end_dt:
                continue
            series.append(
                {
                    "timeUtc": iso_z(dt),
                    "astronomical": round(astronomical[dt], 3),
                }
            )

        spot_payload = {
            "spotLat": round(spot.lat, 6),
            "spotLon": round(spot.lon, 6),
            "stationName": station.name,
            "stationCode": station.code,
            "stationLat": round(station.lat, 6),
            "stationLon": round(station.lon, 6),
            "stationDistanceKm": round(station_distance_km, 1),
            "rows": series,
            "events": [
                {
                    "timeUtc": iso_z(event["time"]),
                    "kind": event["kind"],
                    "astronomical": round(event["astronomical"], 3),
                }
                for event in events
            ],
        }

        if spot.dkss_point:
            try:
                dkss_rows, used_lat, used_lon, endpoint_host = fetch_dmi_dkss_position_rows(
                    spot.dkss_point.lat,
                    spot.dkss_point.lon,
                    start_dt,
                    end_dt,
                )
                dkss_payload_rows = []
                last_dkss_time = None
                for dt in sorted(dkss_rows):
                    if dt < start_dt or dt > end_dt:
                        continue
                    deviation = float(dkss_rows[dt])
                    row = {
                        "timeUtc": iso_z(dt),
                        "deviation": round(deviation, 3),
                    }
                    astronomical_value = nearest_astronomical_value(astronomical, dt)
                    if astronomical_value is not None:
                        row["total"] = round(astronomical_value + deviation, 3)
                    dkss_payload_rows.append(row)
                    last_dkss_time = dt

                spot_payload["dkss"] = {
                    "sourceName": spot.dkss_point.source_name,
                    "endpointHost": endpoint_host,
                    "requestLat": round(spot.dkss_point.lat, 6),
                    "requestLon": round(spot.dkss_point.lon, 6),
                    "usedLat": round(used_lat, 6) if used_lat is not None else None,
                    "usedLon": round(used_lon, 6) if used_lon is not None else None,
                    "distanceKm": (
                        round(
                            haversine_km(
                                spot.dkss_point.lat,
                                spot.dkss_point.lon,
                                used_lat,
                                used_lon,
                            ),
                            1,
                        )
                        if used_lat is not None and used_lon is not None
                        else None
                    ),
                    "throughUtc": iso_z(last_dkss_time) if last_dkss_time else None,
                    "rows": dkss_payload_rows,
                }
                time.sleep(DMI_REQUEST_SPACING_SECONDS)
            except requests.RequestException as exc:
                reused = reuse_existing_dkss_payload(
                    existing_payload,
                    spot.name,
                    start_dt,
                    end_dt,
                )
                if reused is not None:
                    spot_payload["dkss"] = reused
                print(f"[WARN] DKSS fallback for {spot.name}: {exc}")

        payload["spots"][spot.name] = spot_payload

    return payload


def main() -> None:
    payload = build_payload()
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(f"// Generated by surfapp/generate_web_tide_data.py at {payload['generatedAtUtc']}\n")
        f.write("window.TIDE_DATA = ")
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
