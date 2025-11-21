import os
import csv
import io
import json
import base64
import binascii
from datetime import datetime, timezone, timedelta
from typing import Optional
from email.utils import parsedate_to_datetime

import pandas as pd
import requests
import pytz
import subprocess
import xarray as xr
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
COPERNICUS_LAT = 58.10
COPERNICUS_LON = 6.56
COPERNICUS_FORECAST_HOURS = 132
COPERNICUS_DATASET = "cmems_mod_nws_wav_anfc_0.027deg_PT1H-i"
COPERNICUS_RAW_FILE = os.path.join(CACHE_DIR, "copernicus_lista_raw.nc")
COPERNICUS_PUBLIC_FILE = os.path.join(PUBLIC_DIR, "copernicus_lista_readable.csv")
COPERNICUS_TOKEN_PATH = os.path.expanduser(
    "~/.config/copernicusmarine/cmems-api-token.json"
)
COPERNICUS_CREDENTIALS_PATH = os.path.expanduser(
    "~/.copernicusmarine/.copernicusmarine-credentials"
)


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def write_last_run_timestamp(dt: datetime) -> None:
    ensure_dir(CACHE_DIR)
    with open(LAST_RUN_FILE, "w", encoding="utf-8") as f:
        f.write(dt.astimezone(UTC).isoformat())


def ensure_copernicus_auth() -> bool:
    """Ensure either token JSON or legacy credential file is available."""

    token_exists = os.path.exists(COPERNICUS_TOKEN_PATH)
    cred_exists = os.path.exists(COPERNICUS_CREDENTIALS_PATH)
    if token_exists or cred_exists:
        return True

    raw_payload = os.getenv("COPERNICUS_TOKEN_JSON")
    fallback_b64 = os.getenv("COPERNICUS_TOKEN_JSON_B64") or os.getenv(
        "COPERNICUS_TOKEN_JSON_BASE64"
    )

    def try_decode(value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        stripped = value.strip()
        try:
            decoded = base64.b64decode(stripped, validate=True)
            return decoded.decode("utf-8")
        except (binascii.Error, UnicodeDecodeError):
            return value

    payload = None
    if raw_payload:
        payload = try_decode(raw_payload)
    if (not payload) and fallback_b64:
        payload = try_decode(fallback_b64)

    if not payload:
        print(
            "[copernicus] Fant ikke token eller credentials i miljøet – hopper over."
        )
        return False

    stripped = payload.strip()
    looks_json = stripped.startswith("{") or stripped.startswith("[")
    looks_credentials = "username=" in stripped or stripped.startswith("[credentials]")

    if looks_json:
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            print("[copernicus] ❌ Token-JSON kunne ikke parses – hopper over.")
            return False
        token_dir = os.path.dirname(COPERNICUS_TOKEN_PATH)
        os.makedirs(token_dir, exist_ok=True)
        try:
            with open(COPERNICUS_TOKEN_PATH, "w", encoding="utf-8") as f:
                json.dump(parsed, f)
        except OSError as exc:
            print(f"[copernicus] ❌ Kunne ikke skrive token-fil: {exc}")
            return False
        return True

    if looks_credentials:
        cred_dir = os.path.dirname(COPERNICUS_CREDENTIALS_PATH)
        os.makedirs(cred_dir, exist_ok=True)
        try:
            with open(COPERNICUS_CREDENTIALS_PATH, "w", encoding="utf-8") as f:
                f.write(stripped)
        except OSError as exc:
            print(f"[copernicus] ❌ Kunne ikke skrive credentials-fil: {exc}")
            return False
        return True

    print("[copernicus] ❌ Ukjent token-format – hopper over.")
    return False


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
                if key.endswith("_dir_deg"):
                    row_out[key] = deg_to_compass(value)
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
#  Copernicus – bølger
# ---------------------------------------------------

def fetch_copernicus_lista() -> bool:
    ensure_dir(CACHE_DIR)
    ensure_dir(PUBLIC_DIR)
    if not ensure_copernicus_auth():
        return False
    for path in (COPERNICUS_RAW_FILE, COPERNICUS_PUBLIC_FILE):
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass

    now = datetime.now(UTC)
    run_hour = 0 if now.hour < 12 else 12
    run_time = datetime(now.year, now.month, now.day, run_hour, tzinfo=UTC)
    desired_start = run_time - timedelta(hours=12)
    desired_end = run_time + timedelta(hours=120)

    start_str = desired_start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = desired_end.strftime("%Y-%m-%dT%H:%M:%SZ")

    cmd = [
        "copernicusmarine",
        "subset",
        "--dataset-id",
        COPERNICUS_DATASET,
        "--variable",
        "VHM0",
        "--variable",
        "VTPK",
        "--variable",
        "VTM02",
        "--variable",
        "VTM10",
        "--variable",
        "VPED",
        "--variable",
        "VHM0_WW",
        "--variable",
        "VTM01_WW",
        "--variable",
        "VMDR_WW",
        "--variable",
        "VHM0_SW1",
        "--variable",
        "VTM01_SW1",
        "--variable",
        "VMDR_SW1",
        "--variable",
        "VHM0_SW2",
        "--variable",
        "VTM01_SW2",
        "--variable",
        "VMDR_SW2",
        "--minimum-longitude",
        str(COPERNICUS_LON - 0.02),
        "--maximum-longitude",
        str(COPERNICUS_LON + 0.02),
        "--minimum-latitude",
        str(COPERNICUS_LAT - 0.02),
        "--maximum-latitude",
        str(COPERNICUS_LAT + 0.02),
        "--start-datetime",
        start_str,
        "--end-datetime",
        end_str,
        "--output-filename",
        COPERNICUS_RAW_FILE,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        print("[copernicus] Fant ikke 'copernicusmarine' CLI – installer den før kjøring.")
        return False
    except subprocess.CalledProcessError as exc:
        err = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        print(f"[copernicus] ❌ Feil ved nedlasting: {err}")
        return False

    try:
        ds = xr.open_dataset(COPERNICUS_RAW_FILE)
        pt = ds.sel(latitude=COPERNICUS_LAT, longitude=COPERNICUS_LON, method="nearest")
    except Exception as exc:
        print(f"[copernicus] ❌ Kunne ikke åpne/velge punkt: {exc}")
        try:
            ds.close()
        except Exception:
            pass
        return False

    times = pd.to_datetime(pt["time"].values).tz_localize(UTC)

    times = pd.to_datetime(pt["time"].values).tz_localize(UTC)
    value_keys = [
        "Total_Hs (m)",
        "Total_Tp (s)",
        "Total_Tm02 (s)",
        "Total_Tm10 (s)",
        "Total_Dir (°)",
        "Total_Dir_Compass",
        "WW_Hs (m)",
        "WW_Tm01 (s)",
        "WW_Dir (°)",
        "WW_Dir_Compass",
        "S1_Hs (m)",
        "S1_Tm01 (s)",
        "S1_Dir (°)",
        "S1_Dir_Compass",
        "S2_Hs (m)",
        "S2_Tm01 (s)",
        "S2_Dir (°)",
        "S2_Dir_Compass",
    ]

    rows_for_merge: list[dict] = []
    for idx, dt in enumerate(times):
        data = {
            "time_utc": dt.to_pydatetime(),
            "Total_Hs (m)": float(pt["VHM0"].values[idx].round(1)),
            "Total_Tp (s)": float(pt["VTPK"].values[idx].round(1)),
            "Total_Tm02 (s)": float(pt["VTM02"].values[idx].round(1)),
            "Total_Tm10 (s)": float(pt["VTM10"].values[idx].round(1)),
            "Total_Dir (°)": float(pt["VPED"].values[idx].round(0)),
            "Total_Dir_Compass": deg_to_compass(pt["VPED"].values[idx]),
            "WW_Hs (m)": float(pt["VHM0_WW"].values[idx].round(1)),
            "WW_Tm01 (s)": float(pt["VTM01_WW"].values[idx].round(1)),
            "WW_Dir (°)": float(pt["VMDR_WW"].values[idx].round(0)),
            "WW_Dir_Compass": deg_to_compass(pt["VMDR_WW"].values[idx]),
            "S1_Hs (m)": float(pt["VHM0_SW1"].values[idx].round(1)),
            "S1_Tm01 (s)": float(pt["VTM01_SW1"].values[idx].round(1)),
            "S1_Dir (°)": float(pt["VMDR_SW1"].values[idx].round(0)),
            "S1_Dir_Compass": deg_to_compass(pt["VMDR_SW1"].values[idx]),
            "S2_Hs (m)": float(pt["VHM0_SW2"].values[idx].round(1)),
            "S2_Tm01 (s)": float(pt["VTM01_SW2"].values[idx].round(1)),
            "S2_Dir (°)": float(pt["VMDR_SW2"].values[idx].round(0)),
            "S2_Dir_Compass": deg_to_compass(pt["VMDR_SW2"].values[idx]),
        }
        rows_for_merge.append(data)

    actual_lat = float(pt["latitude"].values)
    actual_lon = float(pt["longitude"].values)

    meta_lines: list[str] = [
        "Model run (UTC): " + run_time.strftime("%Y-%m-%d %H:%M"),
        "Hindcast window (UTC): "
        + desired_start.strftime("%Y-%m-%d %H:%M")
        + " -> "
        + run_time.strftime("%Y-%m-%d %H:%M"),
        "Forecast window (UTC): "
        + run_time.strftime("%Y-%m-%d %H:%M")
        + " -> "
        + desired_end.strftime("%Y-%m-%d %H:%M"),
    ]
    meta_lines.append(f"Grid point (lat,lon): {actual_lat:.4f}, {actual_lon:.4f}")
    meta_lines.append(f"Dataset: {COPERNICUS_DATASET}")

    ds.close()

    write_cache_and_readable_csv(
        "copernicus_lista",
        rows_for_merge,
        value_keys,
        metadata_lines=meta_lines,
        history_hours=3,
        replace_existing=True,
    )

    print(f"[copernicus] Raw: {COPERNICUS_RAW_FILE}")
    print(f"[copernicus] Lesbar: {COPERNICUS_PUBLIC_FILE}")
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
#  MAIN – kjør alle fetch + skriv CSV
# ---------------------------------------------------

def main():
    # 1) YR
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
    )

    # 2) DMI HAV
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

    # 3) DMI LAND
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

    # 4) MET
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

    # 5) Lindesnes fyr
    lind_rows = fetch_lindesnes_fyr()
    if lind_rows:
        write_cache_and_readable_csv(
            "lindesnes_fyr",
            lind_rows,
            ["sea_temp_raw", "sea_temp_c", "obs_date_label"],
        )

    # 6) Copernicus
    fetch_copernicus_lista()


if __name__ == "__main__":
    main()
    write_last_run_timestamp(datetime.now(UTC))
