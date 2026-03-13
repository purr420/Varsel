import os
import csv
import io
from datetime import datetime, timezone, timedelta
from typing import Optional
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin
import math
import shutil

import numpy as np
import pandas as pd
import pygrib
import requests
import pytz
import subprocess
from dotenv import load_dotenv
import re

load_dotenv()

# ---------------------------------------------------
#  Konfig
# ---------------------------------------------------

UTC = timezone.utc
OSLO_TZ = pytz.timezone("Europe/Oslo")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "data_cache")   # intern cache (beste format)
PUBLIC_DIR = os.path.join(BASE_DIR, "data_public") # lesbare CSV-er
LAST_RUN_FILE = os.path.join(CACHE_DIR, "fetch_all_last_run.txt")
DMI_API_KEY_EDR = "ae501bfc-112e-400e-89df-77a2a6b9af72"
DMI_API_KEY_STAC = "a4b09032-bca5-4255-ac85-6fea95a1e02c"
FROST_CLIENT_ID = os.getenv("FROST_CLIENT_ID")
NOAA_BASE_PROD = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/"
NOAA_LOOKBACK_DAYS = 5
NOAA_FORECAST_HOURS = range(36)
NOAA_LISTA_LAT = 58.0
NOAA_LISTA_LON = 6.5
NOAA_DOWNLOAD_ROOT = os.path.join(BASE_DIR, "downloads", "noaa")


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

# Ensure persistent directories exist
ensure_dir(CACHE_DIR)
ensure_dir(PUBLIC_DIR)
ensure_dir(NOAA_DOWNLOAD_ROOT)


def write_last_run_timestamp(dt: datetime) -> None:
    ensure_dir(CACHE_DIR)
    with open(LAST_RUN_FILE, "w", encoding="utf-8") as f:
        f.write(dt.astimezone(UTC).isoformat())


def load_existing_csv(path: str) -> tuple[list[str], list[dict]]:
    if not os.path.exists(path):
        return [], []
    metadata: list[str] = []
    data_lines: list[str] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                metadata.append(line.rstrip("\n"))
            else:
                data_lines.append(line)
    if not data_lines:
        return metadata, []
    reader = csv.DictReader(io.StringIO("".join(data_lines)))
    return metadata, list(reader)


def is_blank(value) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def prepare_entries(rows: list[dict], value_keys: list[str]) -> list[dict]:
    entries = []
    for row in rows:
        ts = row.get("time_utc")
        if not ts:
            continue
        dt = parse_iso_utc(str(ts))
        data = {key: row.get(key) for key in value_keys}
        entries.append({"dt": dt, "data": data})
    return entries


def prepare_new_entries(rows: list[dict], value_keys: list[str]) -> list[dict]:
    entries = []
    for row in rows:
        dt = row.get("time_utc")
        if dt is None:
            continue
        if isinstance(dt, datetime):
            dt_utc = dt.astimezone(UTC)
        else:
            dt_utc = parse_iso_utc(str(dt))
        data = {key: row.get(key) for key in value_keys}
        entries.append({"dt": dt_utc, "data": data})
    return entries


def merge_entries(
    new_entries: list[dict],
    existing_entries: list[dict],
    value_keys: list[str],
    history_hours: int = 3,
) -> list[dict]:
    def iso(dt: datetime) -> str:
        return dt.astimezone(UTC).isoformat()

    existing_map = {iso(entry["dt"]): entry for entry in existing_entries}
    new_map = {iso(entry["dt"]): entry for entry in new_entries}

    earliest_dt = min((entry["dt"] for entry in new_entries), default=None)

    merged: dict[str, dict] = {}
    for key, entry in new_map.items():
        merged_data = entry["data"].copy()
        if key in existing_map:
            old_data = existing_map[key]["data"]
            for field in value_keys:
                new_val = merged_data.get(field)
                if is_blank(new_val) and field in old_data and not is_blank(old_data.get(field)):
                    merged_data[field] = old_data[field]
        merged[key] = {"dt": entry["dt"], "data": merged_data}

    if earliest_dt is not None:
        cutoff = earliest_dt - timedelta(hours=history_hours)
        for key, entry in existing_map.items():
            if key in merged:
                continue
            dt = entry["dt"]
            if cutoff <= dt < earliest_dt:
                merged[key] = entry
    else:
        merged = existing_map

    return [merged[k] for k in sorted(merged.keys(), key=lambda x: merged[x]["dt"])]


def parse_meta_time(value) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.astimezone(UTC)
    try:
        return parse_iso_utc(str(value))
    except Exception:
        return None


ISO_TZ_RE = re.compile(r"([+-]\d{2}:\d{2})$")


def _normalize_iso_fraction(ts: str) -> str:
    """
    Ensure fractional seconds have max 6 digits so datetime.fromisoformat accepts string.
    """
    tz = ""
    match = ISO_TZ_RE.search(ts)
    if match:
        tz = match.group(1)
        ts = ts[: -len(tz)]
    if "." not in ts:
        return ts + tz
    base, rest = ts.split(".", 1)
    digits_match = re.match(r"(\d+)", rest)
    if not digits_match:
        return ts + tz
    digits = digits_match.group(1)
    if len(digits) > 6:
        digits = digits[:6]
    elif len(digits) < 6:
        digits = digits.ljust(6, "0")
    return f"{base}.{digits}{tz}"


def parse_iso_utc(ts: str) -> datetime:
    """
    Parse ISO8601 med evt. 'Z' til aware UTC-datetime.
    """
    ts = ts.strip()
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError:
        norm = _normalize_iso_fraction(ts)
        dt = datetime.fromisoformat(norm)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(UTC)
    return dt


def to_oslo_hhmm(dt_utc: datetime) -> str:
    """
    Konverter UTC-datetime til Oslo-tid og formater HH:MM.
    """
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=UTC)
    dt_oslo = dt_utc.astimezone(OSLO_TZ)
    return dt_oslo.strftime("%H:%M")


def parse_http_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        dt = parsedate_to_datetime(date_str)
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(UTC)
    return dt


def noaa_run_id(date_str: str, run_str: str) -> str:
    return f"{date_str}_t{run_str}z"


def expected_noaa_run_dt(date_str: str, run_str: str) -> datetime:
    return datetime.strptime(f"{date_str}{run_str}", "%Y%m%d%H").replace(tzinfo=UTC)


def inspect_noaa_grib_identity(path: str) -> dict:
    with pygrib.open(path) as grbs:
        msg = grbs.message(1)
        return {
            "analDate": msg.analDate.replace(tzinfo=UTC),
            "validDate": msg.validDate.replace(tzinfo=UTC),
            "forecastTime": int(getattr(msg, "forecastTime", 0)),
        }


def get_existing_noaa_run_id() -> Optional[str]:
    path = os.path.join(PUBLIC_DIR, "noaa_lista_readable.csv")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("# NOAA run:"):
                    value = line.split(":", 1)[1].strip()
                    return value or None
    except OSError:
        return None
    return None


def list_recent_noaa_runs(lookback_days: int = NOAA_LOOKBACK_DAYS) -> list[dict]:
    now = datetime.now(UTC).date()
    runs = []
    for offset in range(lookback_days + 1):
        date_obj = now - timedelta(days=offset)
        date_str = date_obj.strftime("%Y%m%d")
        runs_url = urljoin(NOAA_BASE_PROD, f"gfs.{date_str}/")
        try:
            response = requests.get(runs_url, timeout=20)
            response.raise_for_status()
        except Exception:
            continue
        run_matches = sorted(set(re.findall(r'href="(\d{2})/"', response.text)))
        for run_str in run_matches:
            wave_base = urljoin(runs_url, f"{run_str}/wave/gridded/")
            f000_url = urljoin(wave_base, f"gfswave.t{run_str}z.arctic.9km.f000.grib2")
            try:
                head = requests.head(f000_url, timeout=20)
            except Exception:
                continue
            if head.status_code != 200:
                continue
            run_dt = expected_noaa_run_dt(date_str, run_str)
            runs.append(
                {
                    "date": date_str,
                    "run": run_str,
                    "run_dt": run_dt,
                    "run_id": noaa_run_id(date_str, run_str),
                    "wave_base": wave_base,
                }
            )
    runs.sort(key=lambda item: item["run_dt"])
    return runs


def download_noaa_run_files(run_meta: dict) -> list[str]:
    run_dir = os.path.join(NOAA_DOWNLOAD_ROOT, f"gfs.{run_meta['date']}", run_meta["run"])
    ensure_dir(run_dir)
    expected_dt = expected_noaa_run_dt(run_meta["date"], run_meta["run"])
    downloaded: list[str] = []

    for fh in NOAA_FORECAST_HOURS:
        fname = f"gfswave.t{run_meta['run']}z.arctic.9km.f{fh:03d}.grib2"
        path = os.path.join(run_dir, fname)
        if os.path.exists(path) and os.path.getsize(path) > 0:
            try:
                ident = inspect_noaa_grib_identity(path)
                if ident["analDate"] == expected_dt and ident["forecastTime"] == fh:
                    downloaded.append(path)
                    continue
            except Exception:
                pass
            try:
                os.remove(path)
            except OSError:
                pass

        url = urljoin(run_meta["wave_base"], fname)
        response = requests.get(url, stream=True, timeout=120)
        if response.status_code != 200:
            raise RuntimeError(f"Missing NOAA file: {url}")
        with open(path, "wb") as handle:
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    handle.write(chunk)

        ident = inspect_noaa_grib_identity(path)
        if ident["analDate"] != expected_dt or ident["forecastTime"] != fh:
            try:
                os.remove(path)
            except OSError:
                pass
            raise RuntimeError(f"GRIB identity mismatch for {path}")
        downloaded.append(path)

    return downloaded


def pick_noaa_grid_point(f000_path: str) -> dict:
    with pygrib.open(f000_path) as grbs:
        lats, lons = grbs.message(1).latlons()
        swh = grbs.select(shortName="swh")[0].values

    target_lon = NOAA_LISTA_LON + 360 if (lons.max() > 180 and NOAA_LISTA_LON < 0) else NOAA_LISTA_LON
    lat1 = np.deg2rad(NOAA_LISTA_LAT)
    lon1 = np.deg2rad(target_lon)
    lat2 = np.deg2rad(lats)
    lon2 = np.deg2rad(lons)
    a = (
        np.sin((lat2 - lat1) / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    )
    d = 6371 * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    iy_raw, ix_raw = np.unravel_index(np.argmin(d), d.shape)
    raw_wet = math.isfinite(swh[iy_raw, ix_raw])
    ys, xs = np.where(np.isfinite(swh))
    k = np.argmin(d[ys, xs])
    iy_wet, ix_wet = int(ys[k]), int(xs[k])
    iy, ix = (iy_raw, ix_raw) if raw_wet else (iy_wet, ix_wet)

    return {
        "iy": int(iy),
        "ix": int(ix),
        "lat_used": float(lats[iy, ix]),
        "lon_used": float(lons[iy, ix]),
        "dist_km": float(d[iy, ix]),
    }


def build_noaa_lista_rows(run_meta: dict, files: list[str], chosen: dict) -> list[dict]:
    rows: list[dict] = []
    for path in files:
        with pygrib.open(path) as grbs:
            messages = list(grbs)
        gd = {(g.shortName, getattr(g, "level", None)): g for g in messages}
        iy = chosen["iy"]
        ix = chosen["ix"]
        valid_dt = messages[0].validDate.replace(tzinfo=UTC)

        def read_value(short_name: str, level: int) -> Optional[float]:
            msg = gd.get((short_name, level))
            if msg is None:
                return None
            value_raw = msg.values[iy, ix]
            if np.ma.is_masked(value_raw):
                return None
            value = float(value_raw)
            if math.isnan(value):
                return None
            return value

        rows.append(
            {
                "time_utc": valid_dt,
                "WW_Hs (m)": read_value("shww", 1),
                "WW_Tm01 (s)": read_value("mpww", 1),
                "WW_Dir (°)": read_value("wvdir", 1),
                "S1_Hs (m)": read_value("shts", 1),
                "S1_Tm01 (s)": read_value("mpts", 1),
                "S1_Dir (°)": read_value("swdir", 1),
                "S2_Hs (m)": read_value("shts", 2),
                "S2_Tm01 (s)": read_value("mpts", 2),
                "S2_Dir (°)": read_value("swdir", 2),
                "S3_Hs (m)": read_value("shts", 3),
                "S3_Tm01 (s)": read_value("mpts", 3),
                "S3_Dir (°)": read_value("swdir", 3),
            }
        )
    return rows


def cleanup_old_noaa_runs(active_run_meta: dict) -> None:
    active_date_dir = f"gfs.{active_run_meta['date']}"
    active_run_dir = active_run_meta["run"]

    for date_name in os.listdir(NOAA_DOWNLOAD_ROOT):
        date_path = os.path.join(NOAA_DOWNLOAD_ROOT, date_name)
        if not os.path.isdir(date_path):
            continue
        if date_name != active_date_dir:
            shutil.rmtree(date_path, ignore_errors=True)
            continue

        for run_name in os.listdir(date_path):
            run_path = os.path.join(date_path, run_name)
            if not os.path.isdir(run_path):
                continue
            if run_name != active_run_dir:
                shutil.rmtree(run_path, ignore_errors=True)

        if not os.listdir(date_path):
            shutil.rmtree(date_path, ignore_errors=True)


def fetch_dmi_stac_metadata(collection: str, api_key: str) -> Optional[dict]:
    """
    Hent metadata (modelRun + created) fra DMI STAC API for gitt kolleksjon.
    """
    url = f"https://dmigw.govcloud.dk/v1/forecastdata/collections/{collection}/items"
    params = {
        "limit": 1,
        "api-key": api_key,
    }
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        features = data.get("features") or []
        if not features:
            print(f"[{collection}] STAC: ingen features – hopper over.")
            return None
        props = features[0].get("properties", {})
        meta: dict[str, datetime] = {}
        model_run = props.get("modelRun")
        created = props.get("created")
        if model_run:
            meta["model_run"] = parse_iso_utc(model_run)
        if created:
            meta["created"] = parse_iso_utc(created)
        if not meta:
            print(f"[{collection}] STAC: mangler modelRun/created – hopper over.")
            return None
        return meta
    except requests.RequestException as exc:
        print(f"[{collection}] STAC-feil: {exc} – hopper over.")
        return None


def deg_to_compass(deg) -> str:
    """
    Konverter grader til 16-delt kompassretning.
    """
    if deg is None:
        return ""
    try:
        deg_val = float(deg)
    except (TypeError, ValueError):
        return ""

    dirs = [
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
    ]
    idx = round(deg_val / 22.5) % 16
    return dirs[idx]


def round1(value):
    """
    Avrund til 1 desimal, men håndter None.
    """
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return round(float(value), 1)
    return value


def write_cache_and_readable_csv(
    source_name: str,
    rows: list[dict],
    value_keys: list[str],
    metadata_lines: Optional[list[str]] = None,
    history_hours: int = 3,
    replace_existing: bool = False,
    convert_dir_to_compass: bool = True,
    dir_round_func=None,
    value_formatter=None,
) -> None:
    """
    Lagrer:
    - intern cache-CSV (UTC + full presisjon)
    - lesbar CSV (UTC, local HH:MM, verdier med 1 desimal)

    rows: liste av dict med minst:
        "time_utc": datetime (UTC)
        + verdier i value_keys
    """

    ensure_dir(CACHE_DIR)
    ensure_dir(PUBLIC_DIR)

    cache_path = os.path.join(CACHE_DIR, f"{source_name}_cache.csv")
    public_path = os.path.join(PUBLIC_DIR, f"{source_name}_readable.csv")

    if replace_existing:
        new_entries = prepare_new_entries(rows, value_keys)
        merged_entries = new_entries
        final_cache_metadata = metadata_lines or []
        final_public_metadata = metadata_lines or []
    else:
        cache_metadata_existing, cache_existing_rows = load_existing_csv(cache_path)
        public_metadata_existing, _ = load_existing_csv(public_path)

        existing_cache_entries = prepare_entries(cache_existing_rows, value_keys)
        new_entries = prepare_new_entries(rows, value_keys)
        merged_entries = merge_entries(
            new_entries, existing_cache_entries, value_keys, history_hours=history_hours
        )

        if not merged_entries:
            print(f"[{source_name}] Ingen data – hopper over.")
            return

        final_cache_metadata = metadata_lines if metadata_lines else cache_metadata_existing
        final_public_metadata = metadata_lines if metadata_lines else public_metadata_existing

    cache_fieldnames = ["time_utc"] + value_keys
    public_fieldnames = ["time_utc", "time_local"] + value_keys

    with open(cache_path, "w", newline="", encoding="utf-8") as f:
        for line in final_cache_metadata:
            if line.startswith("#"):
                f.write(f"{line}\n")
            else:
                f.write(f"# {line}\n")
        writer = csv.DictWriter(f, fieldnames=cache_fieldnames)
        writer.writeheader()

        for entry in merged_entries:
            dt_utc = entry["dt"].astimezone(UTC)
            ts = dt_utc.isoformat()
            row_out = {"time_utc": ts}
            for key in value_keys:
                row_out[key] = entry["data"].get(key)
            writer.writerow(row_out)

    with open(public_path, "w", newline="", encoding="utf-8") as f:
        for line in final_public_metadata:
            if line.startswith("#"):
                f.write(f"{line}\n")
            else:
                f.write(f"# {line}\n")
        writer = csv.DictWriter(f, fieldnames=public_fieldnames)
        writer.writeheader()

        for entry in merged_entries:
            dt_utc = entry["dt"]
            ts = dt_utc.astimezone(UTC).isoformat()
            lt = to_oslo_hhmm(dt_utc)

            row_out = {
                "time_utc": ts,
                "time_local": lt,
            }
            for key in value_keys:
                value = entry["data"].get(key)
                if value_formatter:
                    row_out[key] = value_formatter(key, value)
                    continue
                if key.endswith("_dir_deg") and convert_dir_to_compass:
                    row_out[key] = deg_to_compass(value)
                elif key.endswith("_dir_deg") and dir_round_func:
                    row_out[key] = dir_round_func(value)
                else:
                    row_out[key] = round1(value)
            writer.writerow(row_out)

    print(f"[{source_name}] Cache:   {cache_path}")
    print(f"[{source_name}] Lesbar:  {public_path}")


# ---------------------------------------------------
#  YR – vind, skydekke, nedbør
# ---------------------------------------------------

def fetch_yr_lista() -> tuple[list[dict], dict]:
    """
    Henter yr-data for Lista (locationforecast 2.0).
    Normaliserer til:
      - UTC-tid
      - m/s, grader, %, mm
    """
    # Bruk samme lat/lon som i yr_lista.py
    lat = 58.10917
    lon = 6.56667

    url = (
        "https://api.met.no/weatherapi/locationforecast/2.0/complete"
        f"?lat={lat}&lon={lon}"
    )
    headers = {
        "User-Agent": "varsel-app/1.0 github.com/purr420",
    }

    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    meta_time = (
        data.get("properties", {})
        .get("meta", {})
        .get("updated_at")
    )
    meta = {}
    if meta_time:
        meta["model_run"] = parse_iso_utc(meta_time)

    timeseries = data["properties"]["timeseries"]

    rows: list[dict] = []
    for ts in timeseries:
        t_utc = parse_iso_utc(ts["time"])
        details = ts["data"]["instant"]["details"]
        next_1h = ts["data"].get("next_1_hours", {}).get("details", {})

        row = {
            "time_utc": t_utc,
            # m/s:
            "wind_speed_ms": details.get("wind_speed"),
            # grader (ikke kompass-tekst):
            "wind_dir_deg": details.get("wind_from_direction"),
            # vindkast m/s:
            "gust_speed_ms": details.get("wind_speed_of_gust"),
            # skydekke %:
            "cloud_cover_pct": details.get("cloud_area_fraction"),
            # nedbør mm neste time:
            "precip_mm": next_1h.get("precipitation_amount"),
        }
        rows.append(row)

    return rows, meta


def fetch_surfline_lista() -> tuple[list[dict], list[str]]:
    """
    Hent surfline swell-forecast for Lista (3 første swells).
    """
    SPOT_ID = "60521386c79046102c0e2cfd"
    DAYS = 5
    url = f"https://services.surfline.com/kbyg/spots/forecasts/wave?spotId={SPOT_ID}&days={DAYS}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:128.0) "
            "Gecko/20100101 Firefox/128.0"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://www.surfline.com",
        "Referer": "https://www.surfline.com/",
        "Connection": "keep-alive",
    }

    try:
        cookies = {}
        access_token = os.getenv("SURFLINE_ACCESS_TOKEN")
        if access_token:
            cookies["access_token"] = access_token

        resp = requests.get(url, headers=headers, cookies=cookies, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"[surfline] Kunne ikke hente data: {exc}")
        return [], []

    wave_data = data.get("data", {}).get("wave", [])
    meta = data.get("associated", {})

    model_run_ts = meta.get("runInitializationTimestamp")
    model_run_dt = datetime.fromtimestamp(model_run_ts, tz=UTC) if model_run_ts else None
    meta_lines: list[str] = []
    if model_run_dt:
        meta_lines.append("Model run (UTC): " + model_run_dt.strftime("%Y-%m-%d %H:%M"))

    def one_decimal(x):
        try:
            return round(float(x), 1)
        except Exception:
            return None

    def three_decimal(x):
        try:
            return round(float(x), 3)
        except Exception:
            return None

    rows: list[dict] = []
    for hour in wave_data:
        ts = hour.get("timestamp")
        if ts is None:
            continue
        dt_utc = datetime.fromtimestamp(ts, tz=UTC)

        swells = hour.get("swells", []) or []
        swells = swells[:6] + [{}] * max(0, 6 - len(swells))

        row = {"time_utc": dt_utc}
        for i in range(6):
            sw = swells[i]
            row[f"s{i+1}_h"] = one_decimal(sw.get("height"))
            row[f"s{i+1}_p"] = one_decimal(sw.get("period"))
            row[f"s{i+1}_dir"] = one_decimal(sw.get("direction"))
            row[f"s{i+1}_dirMin"] = one_decimal(sw.get("directionMin"))
            row[f"s{i+1}_impact"] = three_decimal(sw.get("impact"))

        rows.append(row)

    return rows, meta_lines


# ---------------------------------------------------
#  DMI HAV – bølger + vind
# ---------------------------------------------------

def fetch_dmi_hav_lista() -> Optional[tuple[list[dict], dict]]:
    """
    Henter bølge/vind-data fra DMI (hav).
    """

    collection = "wam_nsb"
    lon = 6.5
    lat = 58.1

    stac_meta = fetch_dmi_stac_metadata(collection, DMI_API_KEY_STAC)

    parameters = [
        "wind-speed",
        "wind-dir",
        "significant-wave-height",
        "dominant-wave-period",
        "mean-wave-period",
        "mean-zerocrossing-period",
        "mean-wave-dir",
        "significant-windwave-height",
        "mean-windwave-period",
        "mean-windwave-dir",
        "significant-totalswell-height",
        "mean-totalswell-period",
        "mean-totalswell-dir",
        "benjamin-feir-index",
    ]

    url = f"https://dmigw.govcloud.dk/v1/forecastedr/collections/{collection}/position"
    params = {
        "coords": f"POINT({lon} {lat})",
        "crs": "crs84",
        "parameter-name": ",".join(parameters),
        "api-key": DMI_API_KEY_EDR,
        "f": "GeoJSON",
    }

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    value_map = {
        "wind_speed_ms": "wind-speed",
        "wind_dir_deg": "wind-dir",
        "hs_m": "significant-wave-height",
        "tp_s": "dominant-wave-period",
        "mean_wave_period_s": "mean-wave-period",
        "mean_zerocrossing_period_s": "mean-zerocrossing-period",
        "mean_wave_dir_deg": "mean-wave-dir",
        "windwave_hs_m": "significant-windwave-height",
        "windwave_tp_s": "mean-windwave-period",
        "windwave_dir_deg": "mean-windwave-dir",
        "swell_hs_m": "significant-totalswell-height",
        "swell_tp_s": "mean-totalswell-period",
        "swell_dir_deg": "mean-totalswell-dir",
        "benjamin_feir_index": "benjamin-feir-index",
    }

    rows: list[dict] = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        step = props.get("step")
        if not step:
            continue
        row = {"time_utc": parse_iso_utc(step)}
        for out_key, prop_key in value_map.items():
            row[out_key] = props.get(prop_key)
        rows.append(row)

    stac_meta = stac_meta or {}
    model_run_header = parse_http_date(resp.headers.get("date"))
    if model_run_header and not stac_meta.get("model_run"):
        stac_meta["model_run"] = model_run_header

    return rows, stac_meta


# ---------------------------------------------------
#  DMI LAND – vind på land
# ---------------------------------------------------

def fetch_dmi_land_lista() -> Optional[tuple[list[dict], dict]]:
    """
    Henter vind-data fra DMI (land).
    """

    lon, lat = 6.56667, 58.10917
    collection = "harmonie_dini_sf"
    stac_meta = fetch_dmi_stac_metadata(collection, DMI_API_KEY_STAC)

    url = f"https://dmigw.govcloud.dk/v1/forecastedr/collections/{collection}/position"
    params = {
        "coords": f"POINT({lon} {lat})",
        "crs": "crs84",
        "parameter-name": "wind-speed-10m,wind-dir-10m,gust-wind-speed-10m,temperature-2m",
        "api-key": DMI_API_KEY_EDR,
        "f": "GeoJSON",
    }

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    rows: list[dict] = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        step = props.get("step")
        if not step:
            continue

        temp_k = props.get("temperature-2m")
        temp_c = temp_k - 273.15 if isinstance(temp_k, (int, float)) else None

        rows.append(
            {
                "time_utc": parse_iso_utc(step),
                "wind_speed_ms": props.get("wind-speed-10m"),
                "wind_dir_deg": props.get("wind-dir-10m"),
                "gust_speed_ms": props.get("gust-wind-speed-10m"),
                "temp_air_c": temp_c,
            }
        )

    stac_meta = stac_meta or {}
    model_run_header = parse_http_date(resp.headers.get("date"))
    if model_run_header and not stac_meta.get("model_run"):
        stac_meta["model_run"] = model_run_header

    return rows, stac_meta


# ---------------------------------------------------
#  Observasjoner – Lista fyr (Frost)
# ---------------------------------------------------

def fetch_observasjoner_lista() -> Optional[list[dict]]:
    """
    Henter siste ~6 timer vindobservasjoner fra Frost (Lista fyr).
    """
    if not FROST_CLIENT_ID:
        print("[obs_lista] Mangler FROST_CLIENT_ID – hopper over.")
        return None

    base = "https://frost.met.no/observations/v0.jsonld"
    source = "SN42160"  # Lista Fyr
    elements = "wind_speed,wind_from_direction,max(wind_speed_of_gust PT10M)"

    now = datetime.now(UTC)
    start = now - timedelta(hours=6)
    start_z = start.isoformat().replace("+00:00", "Z")
    end_z = now.isoformat().replace("+00:00", "Z")

    url = f"{base}?sources={source}&elements={elements}&referencetime={start_z}/{end_z}"

    try:
        r = requests.get(url, auth=(FROST_CLIENT_ID, ""), timeout=20)
        r.raise_for_status()
        data = r.json()
    except requests.RequestException as exc:
        print(f"[obs_lista] ❌ Frost-feil: {exc}")
        return None
    except ValueError:
        print("[obs_lista] ❌ Ugyldig JSON fra Frost.")
        return None

    entries = []
    for entry in data.get("data", []):
        ts = entry.get("referenceTime")
        obs = entry.get("observations", [])
        vals = {o.get("elementId"): o.get("value") for o in obs}
        wind = vals.get("wind_speed")
        deg = vals.get("wind_from_direction")
        gust = vals.get("max(wind_speed_of_gust PT10M)")

        if ts is None:
            continue
        try:
            dt = parse_iso_utc(ts)
        except Exception:
            continue

        entries.append(
            {
                "time_utc": dt,
                "wind_speed_ms": wind,
                "wind_dir_deg": deg,
                "gust_speed_ms": gust,
                "wind_dir_compass": deg_to_compass(deg),
            }
        )

    entries.sort(key=lambda x: x["time_utc"])
    return entries


# ---------------------------------------------------
#  MET (hav / sjøtemperatur eller bølger)
# ---------------------------------------------------

def fetch_met_lista() -> tuple[list[dict], dict]:
    """
    Henter MET-data fra met_lista.py (sannsynligvis bølger eller sjøtemp).
    Fra filen din ser det ut som du henter en enkel verdi (f.eks. sjøtemperatur).
    """

    lat = 58.09
    lon = 6.52
    url = f"https://api.met.no/weatherapi/oceanforecast/2.0/complete?lat={lat}&lon={lon}"
    headers = {"User-Agent": "post@kurios.no"}

    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    meta_time = (
        data.get("properties", {})
        .get("meta", {})
        .get("updated_at")
    )
    meta = {}
    if meta_time:
        meta["model_run"] = parse_iso_utc(meta_time)

    rows: list[dict] = []
    timeseries = data.get("properties", {}).get("timeseries", [])
    for entry in timeseries:
        t_iso = entry.get("time")
        if not t_iso:
            continue
        details = entry.get("data", {}).get("instant", {}).get("details", {})
        rows.append(
            {
                "time_utc": parse_iso_utc(t_iso),
                "sea_temp_c": details.get("sea_water_temperature"),
            }
        )

    return rows, meta


# ---------------------------------------------------
#  NOAA – bølger
# ---------------------------------------------------

def fetch_noaa_lista() -> bool:
    runs = list_recent_noaa_runs()
    if not runs:
        print("[noaa] Fant ingen tilgjengelige NOAA-runs.")
        return False

    latest_run = runs[-1]
    existing_run_id = get_existing_noaa_run_id()
    if existing_run_id == latest_run["run_id"]:
        print(f"[noaa] Siste NOAA-run finnes allerede lokalt: {existing_run_id}")
        cleanup_old_noaa_runs(latest_run)
        return False

    try:
        files = download_noaa_run_files(latest_run)
        chosen = pick_noaa_grid_point(files[0])
        rows_for_merge = build_noaa_lista_rows(latest_run, files, chosen)
    except Exception as exc:
        print(f"[noaa] ❌ Feil ved henting av NOAA-data: {exc}")
        return False

    value_keys = [
        "WW_Hs (m)",
        "WW_Tm01 (s)",
        "WW_Dir (°)",
        "S1_Hs (m)",
        "S1_Tm01 (s)",
        "S1_Dir (°)",
        "S2_Hs (m)",
        "S2_Tm01 (s)",
        "S2_Dir (°)",
        "S3_Hs (m)",
        "S3_Tm01 (s)",
        "S3_Dir (°)",
    ]
    meta_lines = [
        "Model run (UTC): " + latest_run["run_dt"].strftime("%Y-%m-%d %H:%M"),
        f"NOAA run: {latest_run['run_id']}",
        f"Grid point (lat,lon): {chosen['lat_used']:.4f}, {chosen['lon_used']:.4f}",
        f"Distance to target (km): {chosen['dist_km']:.2f}",
        f"Forecast steps: {len(rows_for_merge)}",
        "Dataset: NOAA GFS Wave Arctic 9km",
    ]

    write_cache_and_readable_csv(
        "noaa_lista",
        rows_for_merge,
        value_keys,
        metadata_lines=meta_lines,
        history_hours=0,
        replace_existing=True,
    )
    cleanup_old_noaa_runs(latest_run)
    print(f"[noaa] Aktiv run: {latest_run['run_id']}")
    print(f"[noaa] Download root: {NOAA_DOWNLOAD_ROOT}")
    return True
# ---------------------------------------------------
#  Lindesnes fyr – observasjon sjøtemperatur
# ---------------------------------------------------

def fetch_lindesnes_fyr() -> list[dict]:
    """
    Skraper Lindesnes fyr-siden for sjøtemperatur + dato/klokkeslett.

    Nåværende lindesnes_fyr.py parse'r HTML med BeautifulSoup.
    Her lager vi en enklere variant som du kan tilpasse.

    Vi returnerer en liste med én rad:
      {
        "time_utc": datetime(…, tzinfo=UTC),
        "sea_temp_c": ...,
      }
    """

    url = "https://lindesnesfyr.no/vaeret-pa-fyret/"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    from bs4 import BeautifulSoup
    import re

    soup = BeautifulSoup(resp.text, "html.parser")

    title = soup.find("span", class_="title", string=lambda x: x and "Sjøtemperatur" in x)
    if not title:
        return []

    value_span = title.find_next("span", class_="descr")
    sjotemp_str = value_span.get_text(strip=True) if value_span else None

    sea_temp_c = None
    if sjotemp_str:
        m = re.search(r"([\d,\,\.]+)", sjotemp_str)
        if m:
            sea_temp_c = float(m.group(1).replace(",", "."))

    # Forsøk å hente dato fra tekstinnholdet (samme som det opprinnelige skriptet gjorde)
    all_text = soup.get_text(separator="\n", strip=True)
    date_match = re.search(r"(\d{1,2})\.\s*([A-Za-zæøåÆØÅ]+)\s*(\d{4})", all_text)
    obs_dt_oslo = datetime.now(OSLO_TZ)
    obs_date_label = None

    if date_match:
        day = int(date_match.group(1))
        month_name = date_match.group(2).lower()
        year = int(date_match.group(3))

        month_map = {
            "januar": (1, "jan."),
            "februar": (2, "feb."),
            "mars": (3, "mar."),
            "april": (4, "apr."),
            "mai": (5, "mai."),
            "juni": (6, "jun."),
            "juli": (7, "jul."),
            "august": (8, "aug."),
            "september": (9, "sep."),
            "oktober": (10, "okt."),
            "november": (11, "nov."),
            "desember": (12, "des."),
        }

        month_info = month_map.get(month_name)
        if month_info:
            month, month_short = month_info
            local_dt = datetime(year, month, day)
            obs_dt_oslo = OSLO_TZ.localize(local_dt)
            obs_date_label = f"{day}.{month_short}"

    return [
        {
            "time_utc": obs_dt_oslo.astimezone(UTC),
            "sea_temp_raw": sjotemp_str,
            "sea_temp_c": sea_temp_c,
            "obs_date_label": obs_date_label,
        }
    ]


# ---------------------------------------------------
#  Observasjoner Lista – skrives til cache og lesbar CSV
# ---------------------------------------------------

def write_observasjoner_lista(entries: list[dict]) -> None:
    if not entries:
        print("[obs_lista] Ingen observasjoner å skrive.")
        return

    value_keys = [
        "wind_speed_ms",
        "gust_speed_ms",
        "wind_dir_deg",
        "wind_dir_compass",
    ]
    metadata = ["Observasjoner: Lista fyr (Frost)"]

    write_cache_and_readable_csv(
        "observasjoner_lista",
        entries,
        value_keys,
        metadata_lines=metadata,
        history_hours=6,
        replace_existing=True,
    )


def run_step(name: str, fn) -> None:
    try:
        fn()
    except Exception as exc:
        print(f"[{name}] ❌ Steg feilet: {exc}")


# ---------------------------------------------------
#  MAIN – kjør alle fetch + skriv CSV
# ---------------------------------------------------

def main():
    def step_yr():
        yr_rows, yr_meta = fetch_yr_lista()
        meta_lines = []
        if yr_meta.get("model_run"):
            meta_lines.append(
                "Model run (UTC): "
                + yr_meta["model_run"].astimezone(UTC).strftime("%Y-%m-%d %H:%M")
            )
        write_cache_and_readable_csv(
            "yr_lista",
            yr_rows,
            ["wind_speed_ms", "wind_dir_deg", "gust_speed_ms", "cloud_cover_pct", "precip_mm"],
            metadata_lines=meta_lines,
            history_hours=24,
        )

    def step_surfline():
        surf_rows, surf_meta = fetch_surfline_lista()
        if surf_rows:
            write_cache_and_readable_csv(
                "surfline_lista",
                surf_rows,
                [
                    "s1_h",
                    "s1_p",
                    "s1_dir",
                    "s1_dirMin",
                    "s2_h",
                    "s2_p",
                    "s2_dir",
                    "s2_dirMin",
                    "s3_h",
                    "s3_p",
                    "s3_dir",
                    "s3_dirMin",
                    "s4_h",
                    "s4_p",
                    "s4_dir",
                    "s4_dirMin",
                    "s5_h",
                    "s5_p",
                    "s5_dir",
                    "s5_dirMin",
                    "s6_h",
                    "s6_p",
                    "s6_dir",
                    "s6_dirMin",
                    "s1_impact",
                    "s2_impact",
                    "s3_impact",
                    "s4_impact",
                    "s5_impact",
                    "s6_impact",
                ],
                metadata_lines=surf_meta,
                history_hours=120,
                convert_dir_to_compass=False,
                dir_round_func=lambda v: round(v, 1) if isinstance(v, (int, float)) else None,
                value_formatter=lambda k, v: v,
            )

    def step_dmi_hav():
        dmi_hav_result = fetch_dmi_hav_lista()
        if dmi_hav_result:
            dmi_hav_rows, dmi_hav_meta = dmi_hav_result
            if dmi_hav_rows:
                meta_lines = []
                if dmi_hav_meta.get("model_run"):
                    meta_lines.append(
                        "Model run (UTC): "
                        + dmi_hav_meta["model_run"].astimezone(UTC).strftime("%Y-%m-%d %H:%M")
                    )
                if dmi_hav_meta.get("created"):
                    meta_lines.append(
                        "Created (UTC): "
                        + dmi_hav_meta["created"].astimezone(UTC).strftime("%Y-%m-%d %H:%M")
                    )
                write_cache_and_readable_csv(
                    "dmi_hav_lista",
                    dmi_hav_rows,
                    [
                        "wind_speed_ms",
                        "wind_dir_deg",
                        "hs_m",
                        "tp_s",
                        "mean_wave_period_s",
                        "mean_zerocrossing_period_s",
                        "mean_wave_dir_deg",
                        "windwave_hs_m",
                        "windwave_tp_s",
                        "windwave_dir_deg",
                        "swell_hs_m",
                        "swell_tp_s",
                        "swell_dir_deg",
                        "benjamin_feir_index",
                    ],
                    metadata_lines=meta_lines,
                )

    def step_dmi_land():
        dmi_land_result = fetch_dmi_land_lista()
        if dmi_land_result:
            dmi_land_rows, dmi_land_meta = dmi_land_result
            if dmi_land_rows:
                meta_lines = []
                if dmi_land_meta.get("model_run"):
                    meta_lines.append(
                        "Model run (UTC): "
                        + dmi_land_meta["model_run"].astimezone(UTC).strftime("%Y-%m-%d %H:%M")
                    )
                if dmi_land_meta.get("created"):
                    meta_lines.append(
                        "Created (UTC): "
                        + dmi_land_meta["created"].astimezone(UTC).strftime("%Y-%m-%d %H:%M")
                    )
                write_cache_and_readable_csv(
                    "dmi_land_lista",
                    dmi_land_rows,
                    ["wind_speed_ms", "wind_dir_deg", "gust_speed_ms", "temp_air_c"],
                    metadata_lines=meta_lines,
                )

    def step_met():
        met_rows, met_meta = fetch_met_lista()
        if met_rows:
            meta_lines = []
            if met_meta.get("model_run"):
                meta_lines.append(
                    "Model run (UTC): "
                    + met_meta["model_run"].astimezone(UTC).strftime("%Y-%m-%d %H:%M")
                )
            write_cache_and_readable_csv(
                "met_lista",
                met_rows,
                ["sea_temp_c"],
                metadata_lines=meta_lines,
            )

    def step_lindesnes():
        lind_rows = fetch_lindesnes_fyr()
        if lind_rows:
            write_cache_and_readable_csv(
                "lindesnes_fyr",
                lind_rows,
                ["sea_temp_raw", "sea_temp_c", "obs_date_label"],
            )

    def step_observasjoner():
        obs_rows = fetch_observasjoner_lista()
        if obs_rows:
            write_observasjoner_lista(obs_rows)

    run_step("yr_lista", step_yr)
    run_step("surfline_lista", step_surfline)
    run_step("dmi_hav_lista", step_dmi_hav)
    run_step("dmi_land_lista", step_dmi_land)
    run_step("met_lista", step_met)
    run_step("lindesnes_fyr", step_lindesnes)
    run_step("observasjoner_lista", step_observasjoner)
    run_step("noaa_lista", fetch_noaa_lista)


if __name__ == "__main__":
    main()
    write_last_run_timestamp(datetime.now(UTC))
