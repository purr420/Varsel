import os
import streamlit as st
from datetime import datetime, timedelta, date
from typing import Optional
import pytz
import csv
import json
import re
import subprocess
import sys
import shutil
import requests

from modules.daylight import load_daylight_table, get_light_times

OSLO_TZ = pytz.timezone("Europe/Oslo")
UTC = pytz.utc

# ---- Current time ----
now_utc = datetime.now(UTC)
now_oslo = now_utc.astimezone(OSLO_TZ)
today_date = now_oslo.date()

# Ensure Copernicus credential file exists on Streamlit Cloud
st.set_page_config(layout="wide")

# ---- Load daylight data ----
DAYLIGHT = load_daylight_table()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_CACHE_DIR = os.path.join(BASE_DIR, "data_cache")
DATA_PUBLIC_DIR = os.path.join(BASE_DIR, "data_public")
YR_CACHE_PATH = os.path.join(DATA_CACHE_DIR, "yr_lista_cache.csv")
FETCH_SCRIPT = os.path.join(BASE_DIR, "fetch_all.py")
FETCH_TIMESTAMP_PATH = os.path.join(DATA_CACHE_DIR, "fetch_all_last_run.txt")


def ensure_data_cache_dir():
    os.makedirs(DATA_CACHE_DIR, exist_ok=True)
    os.makedirs(DATA_PUBLIC_DIR, exist_ok=True)

ensure_data_cache_dir()


def read_last_fetch_time() -> Optional[datetime]:
    if not os.path.exists(FETCH_TIMESTAMP_PATH):
        return None
    try:
        with open(FETCH_TIMESTAMP_PATH, encoding="utf-8") as f:
            ts_str = f.read().strip()
    except OSError:
        return None
    if not ts_str:
        return None
    try:
        dt = datetime.fromisoformat(ts_str)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def write_last_fetch_time(dt: datetime) -> None:
    ensure_data_cache_dir()
    with open(FETCH_TIMESTAMP_PATH, "w", encoding="utf-8") as f:
        f.write(dt.astimezone(UTC).isoformat())


def ensure_recent_fetch(max_age_minutes: int = 15) -> Optional[datetime]:
    last = read_last_fetch_time()
    needs_fetch = last is None or (now_utc - last) > timedelta(minutes=max_age_minutes)
    if not needs_fetch:
        return last
    try:
        proc = subprocess.run(
            [sys.executable, FETCH_SCRIPT],
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "DISABLE_COPERNICUS_FETCH": "1"},
        )
        last = datetime.now(UTC)
        write_last_fetch_time(last)
    except subprocess.CalledProcessError as exc:
        err = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        st.warning(f"Kunne ikke oppdatere data automatisk: {err}")
    except Exception as exc:
        st.warning(f"Kunne ikke oppdatere data automatisk: {exc}")
    return read_last_fetch_time()


LAST_FETCH_UTC = ensure_recent_fetch()


def run_manual_fetch():
    try:
        subprocess.run(
            [sys.executable, FETCH_SCRIPT],
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "DISABLE_COPERNICUS_FETCH": "1"},
        )
        now = datetime.now(UTC)
        write_last_fetch_time(now)
        st.success(f"Data oppdatert {now.astimezone(OSLO_TZ).strftime('%H:%M')}")
        return True
    except subprocess.CalledProcessError as exc:
        err = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        st.warning(f"Kunne ikke oppdatere data: {err}")
    except Exception as exc:
        st.warning(f"Kunne ikke oppdatere data: {exc}")
    return False


def load_yr_cloud_rows():
    """
    Read cloud-cover rows from the cached YR file (UTC -> Oslo).
    """
    if not os.path.exists(YR_CACHE_PATH):
        return []

    rows = []
    with open(YR_CACHE_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(line for line in f if not line.startswith("#"))
        for row in reader:
            ts = row.get("time_utc")
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(ts)
            except ValueError:
                continue
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)

            cloud_str = row.get("cloud_cover_pct")
            cloud_val = None
            if cloud_str not in (None, ""):
                try:
                    cloud_val = float(cloud_str)
                except ValueError:
                    cloud_val = None

            rows.append(
                {
                    "time_oslo": dt.astimezone(OSLO_TZ),
                    "cloud_cover_pct": cloud_val,
                }
            )
    return rows


YR_CLOUD_ROWS = load_yr_cloud_rows()


def read_metadata_from_cache(filename: str) -> Optional[dict]:
    path = os.path.join(DATA_CACHE_DIR, filename)
    if not os.path.exists(path):
        return None

    metadata: dict[str, datetime | str] = {}

    def parse_value(raw: str):
        raw = raw.strip()
        try:
            dt = datetime.fromisoformat(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            else:
                dt = dt.astimezone(UTC)
            return dt
        except ValueError:
            return raw

    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.startswith("# Model run"):
                    metadata["model_run"] = parse_value(line.split(":", 1)[1])
                elif line.startswith("# Created"):
                    metadata["created"] = parse_value(line.split(":", 1)[1])
    except OSError:
        return None

    return metadata or None

def try_parse_float(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return value


def load_cache_by_hour(filename):
    """
    Load a cache CSV into a dict keyed by UTC hour.
    """
    path = os.path.join(DATA_CACHE_DIR, filename)
    data = {}
    if not os.path.exists(path):
        return data

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(line for line in f if not line.startswith("#"))
        for row in reader:
            ts = row.get("time_utc")
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(ts)
            except ValueError:
                continue
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            dt_utc = dt.astimezone(UTC).replace(minute=0, second=0, microsecond=0)

            parsed = {}
            for key, val in row.items():
                if key == "time_utc":
                    continue
                parsed[key] = try_parse_float(val)
            data[dt_utc] = parsed
    return data


def get_nearest_row(data: dict, target: datetime, max_hours: int = 3):
    """
    Return the row whose key is closest to target within max_hours; otherwise None.
    """
    if not data:
        return None
    closest = None
    closest_delta = None
    for key in data.keys():
        delta = abs((key - target).total_seconds())
        if closest_delta is None or delta < closest_delta:
            closest_delta = delta
            closest = key
    if closest is None:
        return None
    if closest_delta is not None and closest_delta <= max_hours * 3600:
        return data.get(closest)
    return None


def fetch_observasjoner_lista_live():
    """
    Hent siste ~6 timer vindobservasjoner (Lista fyr) fra Frost direkte.
    Bruker FROST_CLIENT_ID fra env eller st.secrets.
    """
    client_id = os.getenv("FROST_CLIENT_ID")
    if not client_id:
        try:
            client_id = st.secrets["FROST_CLIENT_ID"]
        except Exception:
            client_id = None
    if not client_id:
        return None

    base = "https://frost.met.no/observations/v0.jsonld"
    source = "SN42160"  # Lista Fyr
    elements = "wind_speed,wind_from_direction,max(wind_speed_of_gust PT10M)"

    now = datetime.now(UTC)
    start = now - timedelta(hours=6)

    start_z = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_z = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    url = f"{base}?sources={source}&elements={elements}&referencetime={start_z}/{end_z}"

    try:
        resp = requests.get(url, auth=(client_id, ""), timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None

    obs_map = {}
    for entry in data.get("data", []):
        ts = entry.get("referenceTime")
        if not ts:
            continue
        try:
            dt = parse_iso_dt(ts)
        except Exception:
            continue
        obs = entry.get("observations", [])
        vals = {o.get("elementId"): o.get("value") for o in obs}
        wind = vals.get("wind_speed")
        deg = vals.get("wind_from_direction")
        gust = vals.get("max(wind_speed_of_gust PT10M)")
        obs_map[dt.astimezone(UTC).replace(microsecond=0)] = {
            "wind_speed_ms": wind,
            "wind_dir_deg": deg,
            "gust_speed_ms": gust,
            "wind_dir_compass": deg_to_compass(deg),
        }

    return obs_map or None


def load_observasjoner_lista_data():
    live = fetch_observasjoner_lista_live()
    if live:
        return live
    return load_cache_by_hour("observasjoner_lista_cache.csv")


def parse_iso_dt(ts: str) -> datetime:
    ts = ts.strip()
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(UTC)
    return dt


def load_copernicus_public():
    path = os.path.join(DATA_PUBLIC_DIR, "copernicus_lista_readable.csv")
    data = {}
    if not os.path.exists(path):
        return data

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(line for line in f if not line.startswith("#"))
        for row in reader:
            ts = row.get("time_utc")
            if not ts:
                continue
            try:
                dt = parse_iso_dt(ts)
            except ValueError:
                continue
            dt_oslo = dt.astimezone(OSLO_TZ).replace(minute=0, second=0, microsecond=0)
            parsed = {}
            for key, val in row.items():
                if key in ("time_utc", "time_local"):
                    continue
                parsed[key] = try_parse_float(val)
            data[dt_oslo] = parsed
    return data
def deg_to_compass(deg):
    if deg is None:
        return "-"
    try:
        val = float(deg)
    except (TypeError, ValueError):
        return "-"
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = round(val / 22.5) % 16
    return dirs[idx]


def fmt_decimal(value):
    if value is None or isinstance(value, str) and not value.strip():
        return "-"
    try:
        return f"{float(value):.1f}".replace(".", ",")
    except (TypeError, ValueError):
        return "-"


def fmt_integer(value):
    if value is None or (isinstance(value, str) and not value.strip()):
        return "-"
    try:
        return str(int(round(float(value))))
    except (TypeError, ValueError):
        return "-"


def fmt_wind(speed, gust):
    if speed is None and gust is None:
        return "-"
    s = fmt_integer(speed)
    g = fmt_integer(gust)
    if g == "-":
        return s
    return f"{s}({g})"
ARROWS = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]


def deg_to_arrow(deg):
    if deg is None:
        return "-"
    try:
        val = float(deg)
    except (TypeError, ValueError):
        return "-"
    rotation = (val + 180) % 360
    return f'<span class="dir-arrow" style="transform: rotate({rotation}deg);">↑</span>'


def get_val(row, key):
    if not row:
        return None
    return row.get(key)


def to_float(value) -> Optional[float]:
    if value in (None, "", "-"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


CELL_COLORS = {
    "gust": [
        (5, "#d1ffd2"),
        (8, "#f7ffcc"),
        (16, "#ffefc2"),
    ],
    "gust_high": "#ffb3b3",
}


def style_wave_height(raw) -> str:
    val = to_float(raw)
    if val is None:
        return ""
    if val > 1.8:
        return "font-weight:bold;"
    if val < 0.8:
        return "opacity: 0.5;"
    return ""


def style_period(raw) -> str:
    val = to_float(raw)
    if val is None:
        return ""
    if val > 7:
        return "font-weight:bold;"
    if val < 6:
        return "opacity: 0.5;"
    return ""


def style_gust(raw) -> str:
    val = to_float(raw)
    if val is None:
        return ""

    # Bruk samme avrunding som vises i tabellen (fmt_integer)
    shown = round(val)  # dette matcher fmt_integer()

    if shown < 6:
        color = CELL_COLORS["gust"][0][1]
    elif shown < 9:
        color = CELL_COLORS["gust"][1][1]
    elif shown < 17:
        color = CELL_COLORS["gust"][2][1]
    else:
        color = CELL_COLORS["gust_high"]

    return f"background-color:{color};"


def classify_direction(deg: float) -> str:
    """
    Klassifiserer vindretning (grader) i 'very_good', 'good' eller 'bad'
    basert på definerte kompassintervaller.
    """
    if deg is None:
        return "bad"
    try:
        d = float(deg) % 360
    except (TypeError, ValueError):
        return "bad"

    if d >= 337.5 or d <= 90:
        return "very_good"
    if 135 <= d <= 270:
        return "bad"
    return "good"


def style_wind_combined(row) -> str:
    gust = to_float(get_val(row, "gust_speed_ms"))
    speed = to_float(get_val(row, "wind_speed_ms"))
    val = gust if gust is not None else speed
    if val is None:
        return ""

    direction = classify_direction(get_val(row, "wind_dir_deg"))
    shown = round(val)

    if shown < 6:
        color = CELL_COLORS["gust"][0][1]  # green
    elif 6 <= shown <= 9:
        if direction == "very_good":
            color = CELL_COLORS["gust"][0][1]  # green
        elif direction == "good":
            color = CELL_COLORS["gust"][1][1]  # yellow
        else:
            color = CELL_COLORS["gust"][2][1]  # orange-ish
    elif 9 < shown <= 17:
        if direction == "very_good":
            color = CELL_COLORS["gust"][1][1]  # yellow
        elif direction == "good":
            color = CELL_COLORS["gust"][2][1]  # orange-ish
        else:
            color = CELL_COLORS["gust_high"]   # red
    else:  # > 17
        if direction == "very_good":
            color = CELL_COLORS["gust"][2][1]  # orange-ish
        else:
            color = CELL_COLORS["gust_high"]   # red

    return f"background-color:{color};"



MODEL_METADATA = {
    "dmi_hav": read_metadata_from_cache("dmi_hav_lista_cache.csv") or {},
    "dmi_land": read_metadata_from_cache("dmi_land_lista_cache.csv") or {},
    "yr": read_metadata_from_cache("yr_lista_cache.csv") or {},
    "copernicus": read_metadata_from_cache("copernicus_lista_cache.csv") or {},
    "observasjoner_lista": read_metadata_from_cache("observasjoner_lista_cache.csv") or {},
}


def format_run_display(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        month = MONTHS_EN[value.month - 1]
        return f"{value.day}. {month} {value.strftime('%H:%M')}"
    if isinstance(value, str) and value:
        return value
    return None


def format_dmi_metadata(label: str, meta: dict) -> Optional[str]:
    run_display = format_run_display(meta.get("model_run"))
    if not run_display:
        return None
    line = f"{label}: Run (UTC) {run_display}"
    created = meta.get("created")
    if isinstance(created, datetime):
        line += f" Created {created.strftime('%H:%M')}"
    elif isinstance(created, str) and created:
        line += f" Created {created}"
    return line


def format_yr_metadata(meta: dict) -> Optional[str]:
    run_display = format_run_display(meta.get("model_run"))
    if not run_display:
        return None
    return f"Yr (Locationforecast v2): Run (UTC) {run_display}"


def format_copernicus_metadata(meta: dict) -> Optional[str]:
    run_display = format_run_display(meta.get("model_run"))
    if not run_display:
        return None
    return f"Copernicus (CMEMS): Run (UTC) {run_display}"


YR_DATA = load_cache_by_hour("yr_lista_cache.csv")
DMI_HAV_DATA = load_cache_by_hour("dmi_hav_lista_cache.csv")
DMI_LAND_DATA = load_cache_by_hour("dmi_land_lista_cache.csv")
OBS_LISTA_DATA = load_observasjoner_lista_data()
MET_DATA = load_cache_by_hour("met_lista_cache.csv")
COP_DATA = load_copernicus_public()
def load_lindesnes_latest():
    path = os.path.join(DATA_CACHE_DIR, "lindesnes_fyr_cache.csv")
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            rows = list(csv.DictReader(line for line in f if not line.startswith("#")))
    except OSError:
        return None
    if not rows:
        return None
    row = rows[-1]
    temp = row.get("sea_temp_c")
    label = row.get("obs_date_label")
    return temp, label


LINDESNES_LATEST = load_lindesnes_latest()


def format_obs_label(label: Optional[str]) -> str:
    if not label:
        return "--"
    m = re.match(r"(\d+)\.\s*([A-Za-zæøåÆØÅ]+)", label)
    if m:
        day = m.group(1)
        month = m.group(2).rstrip(".")
        return f"{day}. {month}"
    return label


def cloud_pct_for_time(target_oslo: datetime) -> float:
    """
    Return cloud cover percentage for the cached forecast nearest to target_oslo.
    Fallback to 50 if no usable data.
    """
    if not YR_CLOUD_ROWS:
        return 50.0

    best_row = None
    best_diff = None
    for row in YR_CLOUD_ROWS:
        diff = abs((row["time_oslo"] - target_oslo).total_seconds())
        if best_diff is None or diff < best_diff:
            best_diff = diff
            best_row = row

    if not best_row:
        return 50.0

    cloud = best_row.get("cloud_cover_pct")
    if cloud is None:
        return 50.0
    return max(0.0, min(100.0, cloud))

# ---- Light times for header (string versions) ----
light = get_light_times(now_utc, DAYLIGHT)

# ---------------------------------------------------
#  Helpers to work with daylight table per date
# ---------------------------------------------------

def midpoint_dt(a: datetime, b: datetime) -> datetime:
    if a is None:
        return b
    if b is None:
        return a
    return a + (b - a) / 2


def hour_before(dt: datetime) -> datetime:
    base = dt.replace(minute=0, second=0, microsecond=0)
    if dt.minute == 0 and dt.second == 0:
        base -= timedelta(hours=1)
    return base


def hour_after(dt: datetime) -> datetime:
    base = dt.replace(minute=0, second=0, microsecond=0)
    return base + timedelta(hours=1 if dt.minute > 0 or dt.second > 0 else 1)


def get_weather_for_hour(dt_oslo: datetime) -> tuple[float, float]:
    dt_key = dt_oslo.astimezone(OSLO_TZ).replace(minute=0, second=0, microsecond=0)
    row = YR_DATA.get(dt_key)
    cloud = to_float(get_val(row, "cloud_cover_pct"))
    precip = to_float(get_val(row, "precip_mm"))
    cloud = 0.0 if cloud is None else max(0.0, min(100.0, cloud))
    precip = 0.0 if precip is None else max(0.0, precip)
    return cloud, precip


def get_light_oslo_for_date(d: date, cloud_override: Optional[float] = None):
    """
    Return adjusted (first_light_oslo, last_light_oslo) using daylight table
    with cloud/precipitation-based rules.
    """
    # Table key is d(d).mm, e.g. "1.01", "18.11"
    date_key = f"{d.day}.{d.month:02d}".lstrip("0")
    row = DAYLIGHT.loc[DAYLIGHT["Dato"].astype(str).str.strip() == date_key]

    if row.empty:
        return None, None

    row = row.iloc[0]

    def parse_utc_to_oslo(clock_str: str):
        if not isinstance(clock_str, str) or ":" not in clock_str:
            return None
        h, m = map(int, clock_str.split(":"))
        dt_utc = datetime(d.year, d.month, d.day, h, m, tzinfo=UTC)
        return dt_utc.astimezone(OSLO_TZ)

    sunrise_oslo = parse_utc_to_oslo(row["Sunrise_UTC"])
    sunset_oslo = parse_utc_to_oslo(row["Sunset_UTC"])
    first_light_early = parse_utc_to_oslo(row["First_surf_start_UTC"])
    first_light_late = parse_utc_to_oslo(row["First_surf_end_UTC"])
    last_light_early = parse_utc_to_oslo(row["Last_surf_start_UTC"])
    last_light_late = parse_utc_to_oslo(row["Last_surf_end_UTC"])

    if not all([first_light_early, first_light_late, last_light_early, last_light_late, sunrise_oslo, sunset_oslo]):
        return None, None

    if cloud_override is not None:
        morning_cloud = max(0.0, min(100.0, cloud_override * 100.0))
        evening_cloud = morning_cloud
        morning_precip = 0.0
        evening_precip = 0.0
    else:
        morning_hour = hour_before(sunrise_oslo)
        evening_hour = hour_after(sunset_oslo)
        morning_cloud, morning_precip = get_weather_for_hour(morning_hour)
        evening_cloud, evening_precip = get_weather_for_hour(evening_hour)

    if morning_cloud <= 50:
        usable_first = first_light_early
    else:
        usable_first = midpoint_dt(first_light_early, first_light_late)

    if morning_precip > 0:
        if morning_precip <= 2:
            usable_first = first_light_late
        else:
            usable_first = midpoint_dt(first_light_late, sunrise_oslo)

    if evening_cloud <= 50:
        usable_last = last_light_late
    else:
        usable_last = midpoint_dt(last_light_late, last_light_early)

    if evening_precip > 0:
        if evening_precip <= 2:
            usable_last = last_light_early
        else:
            usable_last = midpoint_dt(sunset_oslo, last_light_early)

    return usable_first, usable_last


def compute_day_window(d: date):
    """
    For a given day d, compute the local (Oslo) start and end datetimes
    for the forecast table based on first/last light.

    - Day starts at: floor(first_light_hour) - 2 hours
    - Day ends at: ceil(last_light_hour) (one full hour after if there are minutes)
    """
    first_light, last_light = get_light_oslo_for_date(d)
    if first_light is None or last_light is None:
        # Fallback: full day if we have no data
        day_start = datetime(d.year, d.month, d.day, 0, 0, tzinfo=OSLO_TZ)
        day_end = datetime(d.year, d.month, d.day, 23, 0, tzinfo=OSLO_TZ)
        return day_start, day_end

    # Floor first light to full hour, then subtract 2 hours
    first_floor = first_light.replace(minute=0, second=0, microsecond=0)
    day_start = first_floor - timedelta(hours=2)
    if day_start.date() < d:
        # If subtraction crosses midnight, clamp to this date at 00
        day_start = datetime(d.year, d.month, d.day, 0, 0, tzinfo=OSLO_TZ)

    # Last hour shown: one full hour after if there are minutes > 0
    last_hour = last_light.hour + (1 if last_light.minute > 0 else 0)
    if last_hour > 23:
        last_hour = 23
    day_end = datetime(d.year, d.month, d.day, last_hour, 0, tzinfo=OSLO_TZ)

    return day_start, day_end


def format_oslo(dt, fallback="--:--"):
    if dt is None:
        return fallback
    return dt.astimezone(OSLO_TZ).strftime("%H:%M")


usable_first_today, usable_last_today = get_light_oslo_for_date(now_oslo.date())
header_first_light = format_oslo(usable_first_today, light["first_light"])
header_last_light = format_oslo(usable_last_today, light["last_light"])
tomorrow_date = today_date + timedelta(days=1)
usable_first_tomorrow, usable_last_tomorrow = get_light_oslo_for_date(tomorrow_date)

# Manual refresh button (fetch_all without Copernicus)
# (Manual refresh button removed)

# ---------------------------------------------------
#  HEADER
# ---------------------------------------------------

MONTHS_NO = ["jan", "feb", "mar", "apr", "mai", "jun",
             "jul", "aug", "sep", "okt", "nov", "des"]
MONTHS_EN = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]
month_no = MONTHS_NO[now_oslo.month - 1]
if LAST_FETCH_UTC:
    last_fetch_oslo = LAST_FETCH_UTC.astimezone(OSLO_TZ)
    header_updated_text = (
        f"(oppdatert {last_fetch_oslo.strftime('%H:%M %d.')} "
        f"{MONTHS_NO[last_fetch_oslo.month - 1]})"
    )
else:
    header_updated_text = (
        f"(oppdatert {now_oslo.strftime('%H:%M %d.')} {month_no})"
    )

st.markdown(
    f"""
<style>
.header-title {{
    font-size: 42px;
    font-weight: 800;
    line-height: 1.0;
    margin-bottom: 10px;
}}

.header-sub {{
    font-size: 26px;
    font-weight: 500;
    line-height: 1.0;
    margin-top: 2px;
    margin-bottom: 4px;
}}

.header-updated {{
    font-size: 15px;
    opacity: 0.75;
    margin-left: 6px;
}}

.header-line {{
    font-size: 15px;
    opacity: 0.75;
    margin-top: 10px;
}}
</style>

<div class="header-title">Varselet</div>

<div class="header-sub">
    for Lista
    <span class="header-updated">
        {header_updated_text}
    </span>
</div>

<div class="header-line">
I dag {today_date.day}. {month_no} Lyst fra / til: <b>{header_first_light} / {header_last_light}</b>
</div>
<div class="header-line">
I morgen {tomorrow_date.day}. {MONTHS_NO[tomorrow_date.month - 1]} Lyst fra / til: <b>{format_oslo(usable_first_tomorrow, "--:--")} / {format_oslo(usable_last_tomorrow, "--:--")}</b>
</div>
<div class="header-line">
Sjø: <b>{fmt_decimal(LINDESNES_LATEST[0]) if LINDESNES_LATEST else "--"} °C</b> (Lindesnes fyr) målt {format_obs_label(LINDESNES_LATEST[1]) if LINDESNES_LATEST and LINDESNES_LATEST[1] else "--"}
</div>

<hr>
""",
    unsafe_allow_html=True
)


# ---------------------------------------------------
#  BUILD DAY BLOCKS (TODAY / I MORGEN / +1)
# ---------------------------------------------------

# Light window for "calendar today" (for skip logic)
first_today, last_today = get_light_oslo_for_date(today_date)

# Decide if we skip today (more than 1 hour after last light)
skip_today = False
if last_today is not None:
    if now_oslo > (last_today + timedelta(hours=1)):
        skip_today = True

# Base day: today (normal) or tomorrow (if we skip today)
base_day = today_date if not skip_today else today_date + timedelta(days=1)

# Determine how far to show based on DMI HAV data (fallback to 3 days)
last_dmi_hav_dt_utc = max(DMI_HAV_DATA.keys()) if DMI_HAV_DATA else None
default_end_date = base_day + timedelta(days=2)
if last_dmi_hav_dt_utc:
    last_dmi_hav_dt_oslo = last_dmi_hav_dt_utc.astimezone(OSLO_TZ)
    max_end_date = max(default_end_date, last_dmi_hav_dt_oslo.date())
else:
    max_end_date = default_end_date

# Build list of days until max_end_date (inclusive)
days: list[date] = []
d = base_day
while d <= max_end_date:
    days.append(d)
    d += timedelta(days=1)

# Build blocks: each has a label and a list of hourly datetimes
day_blocks = []

now_floor = now_oslo.replace(minute=0, second=0, microsecond=0)

for idx, d in enumerate(days):
    day_start, day_end = compute_day_window(d)

    #
    # Correct start-time logic:
    #  - If today and first block → start at (now - 2h)
    #  - Else → use daylight-based day_start
    #
    if d == today_date and idx == 0 and not skip_today:
        two_hours_back = now_oslo - timedelta(hours=2)
        start_time = two_hours_back.replace(minute=0, second=0, microsecond=0)
    else:
        start_time = day_start

    # Align end of forecast to last DMI HAV timestamp if present
    if last_dmi_hav_dt_utc:
        last_oslo = last_dmi_hav_dt_utc.astimezone(OSLO_TZ)
        if d == last_oslo.date():
            day_end = last_oslo

    # Ensure far-out days include at least 6,9,12,15,18 (and 21 if sunset > 18),
    # except the final forecast day (which may end earlier if data ends).
    is_last_day = d == days[-1]
    if idx >= 2 and not is_last_day:
        _, last_light = get_light_oslo_for_date(d)
        min_hour = 18
        if last_light and (last_light.hour > 18 or (last_light.hour == 18 and last_light.minute > 0)):
            min_hour = 21
        min_dt = datetime(d.year, d.month, d.day, min_hour, 0, tzinfo=OSLO_TZ)
        if day_end < min_dt:
            day_end = min_dt

    # Build the list of hours for this day
    hours: list[datetime] = []

    # First two displayed days => full hours
    if idx <= 1:
        t = start_time
        while t <= day_end:
            if t.tzinfo is None:
                t = t.replace(tzinfo=OSLO_TZ)
            if t.date() == d:
                hours.append(t)
            t += timedelta(hours=1)
    else:
        # Days after "tomorrow": only specific 3-hour slots
        _, last_light = get_light_oslo_for_date(d)
        slots = [6, 9, 12, 15, 18]
        if last_light and (last_light.hour > 18 or (last_light.hour == 18 and last_light.minute > 0)):
            slots.append(21)
        for hr in slots:
            dt_candidate = datetime(d.year, d.month, d.day, hr, 0, tzinfo=OSLO_TZ)
            if dt_candidate < start_time or dt_candidate > day_end:
                continue
            hours.append(dt_candidate)

    if not hours:
        continue

       # Label logic:
    # - Never label the block that is "today" when it's the first block
    # - If the calendar day is tomorrow => "I morgen 18. nov"
    # - Otherwise => Weekday + date
    if d == today_date and idx == 0 and not skip_today:
        label = None
    else:
        if d == today_date + timedelta(days=1):
            month_name = MONTHS_NO[d.month - 1]
            label = f"I morgen {d.day}. {month_name}"
        else:
            WEEKDAY_FULL = ["Mandag", "Tirsdag", "Onsdag",
                            "Torsdag", "Fredag", "Lørdag", "Søndag"]
            weekday = WEEKDAY_FULL[d.weekday()]
            month_name = MONTHS_NO[d.month - 1]
            label = f"{weekday} {d.day}. {month_name}"


    day_blocks.append({"label": label, "hours": hours})


# ---------------------------------------------------
#  TABLE RENDERING
# ---------------------------------------------------

ALIGN = {
    1: "right", 2: "center", 3: "left",   # Dønning (new)
    4: "right", 5: "left",                # Vind (new)
    6: "right", 7: "center", 8: "left",   # Dønning (DMI)
    9: "center",                          # P.dom.
    10: "right", 11: "center", 12: "left",# Vindbølger (DMI)
    13: "right", 14: "center", 15: "left",# Vindbølger (CMEMS)
    16: "right", 17: "center", 18: "left",# Swell (CMEMS)
    19: "right", 20: "center", 21: "left",# 2nd Swell (CMEMS)
    22: "right", 23: "left",              # Vind (Yr)
    24: "right", 25: "left",              # Vind (DMI)
    26: "right", 27: "left",              # Vind (målt)
    28: "right", 29: "center",            # Temp (°C)
    30: "center", 31: "center",           # Sky/Nedbør
}
DATA_COLUMNS = len(ALIGN)

def col_align(i):
    return ALIGN.get(i, "center")


html = f"""
<style>

.sticky-table-container {{
    max-height: 650px;
    overflow: auto;
    border-radius: 6px;
    background: #f4f4f4;
}}

.sticky-table {{
    width: 100%;
    border-collapse: collapse;
    background: #f7f7f7;
}}

.sticky-table th,
.sticky-table td {{
    padding: 8px;
    vertical-align: middle;
    min-width: 40px;
    background: #f7f7f7;
    border: none;
}}

/* Soften all header cells */
.sticky-table th {{
    font-weight: normal;
    opacity: 1;
}}

/* Units row like (m), (s), (%) */
.header-sub th {{
    font-weight: normal;
    opacity: 1;
}}


/* Header rows */
.header-top {{
    background: #ececec !important;
}}
.header-sub {{
    background: #ececec !important;
}}

/* Sticky header rows */
.sticky-table thead th {{
    position: sticky;
    background: #ececec;
    z-index: 10;
}}
.sticky-table thead tr:first-child th {{
    top: 0;
}}
.sticky-table thead tr:nth-child(2) th {{
    top: 36px;
}}

/* Sticky first column */
.sticky-table td:first-child,
.sticky-table th:first-child {{
    position: sticky;
    left: 0;
    background: #ececec;
    z-index: 20;
    font-weight: normal;
    text-align: center;
}}

.sticky-table thead tr:first-child th:first-child {{
    z-index: 30 !important;
}}

/* Day separator row */
.day-separator td:first-child {{
    background: #ececec !important;
}}
.day-separator td {{
    font-size: 14px;
}}
.day-separator td[colspan] {{
    background: #f7f7f7 !important;
    text-align: left;
    padding-left: 12px;
    font-weight: normal;
}}

/* Fix rowspan header alignment on desktop */
@media (min-width: 768px) {{
    .sticky-table thead th[rowspan] {{
        top: 0 !important;
        z-index: 12 !important;
    }}
}}

.dir-arrow {{
    display: inline-block;
    font-size: 16px;
}}

.model-run-wrapper {{
    color: grey !important;
    opacity: 0.75 !important;
    position: relative;
    z-index: 50;
    background: transparent;
}}
.model-run-wrapper div {{
    margin-bottom: 4px;
}}

</style>

<div class="sticky-table-container">
<table class="sticky-table">

<thead>
<tr class="header-top">
    <th rowspan="2">Tid</th>
    <th colspan="3">Dønning</th>
    <th colspan="2">Vind</th>
    <th colspan="3">Dønning (DMI)</th>
    <th>P.dom.</th>
    <th colspan="3">Vindbølger (DMI)</th>
    <th colspan="3">Vindbølger (CMEMS)</th>
    <th colspan="3">Swell (CMEMS)</th>
    <th colspan="3">2nd Swell (CMEMS)</th>
    <th colspan="2">Vind (Yr)</th>
    <th colspan="2">Vind (DMI)</th>
    <th colspan="2">Vind (målt)</th>
    <th colspan="2">Temp (°C)</th>
    <th>Skydekke</th>
    <th>Nedbør</th>
</tr>

<tr class="header-sub">
    <th style="text-align:{col_align(1)}">(m)</th>
    <th style="text-align:{col_align(2)}">(s)</th>
    <th style="text-align:{col_align(3)}"></th>
    <th style="text-align:{col_align(4)}">(m/s)</th>
    <th style="text-align:{col_align(5)}"></th>
    <th style="text-align:{col_align(6)}">(m)</th>
    <th style="text-align:{col_align(7)}">(s)</th>
    <th style="text-align:{col_align(8)}"></th>
    <th style="text-align:{col_align(9)}">(s)</th>
    <th style="text-align:{col_align(10)}">(m)</th>
    <th style="text-align:{col_align(11)}">(s)</th>
    <th style="text-align:{col_align(12)}"></th>
    <th style="text-align:{col_align(13)}">(m)</th>
    <th style="text-align:{col_align(14)}">(s)</th>
    <th style="text-align:{col_align(15)}"></th>
    <th style="text-align:{col_align(16)}">(m)</th>
    <th style="text-align:{col_align(17)}">(s)</th>
    <th style="text-align:{col_align(18)}"></th>
    <th style="text-align:{col_align(19)}">(m)</th>
    <th style="text-align:{col_align(20)}">(s)</th>
    <th style="text-align:{col_align(21)}"></th>
    <th style="text-align:{col_align(22)}">(m/s)</th>
    <th style="text-align:{col_align(23)}"></th>
    <th style="text-align:{col_align(24)}">(m/s)</th>
    <th style="text-align:{col_align(25)}"></th>
    <th style="text-align:{col_align(26)}">(m/s)</th>
    <th style="text-align:{col_align(27)}"></th>
    <th style="text-align:{col_align(28)}">Luft</th>
    <th style="text-align:{col_align(29)}">Sjø</th>
    <th style="text-align:{col_align(30)}">(%)</th>
    <th style="text-align:{col_align(31)}">(mm)</th>
</tr>
</thead>

<tbody>
"""
# Insert blocks and rows
for block in day_blocks:
    label = block["label"]
    hours = block["hours"]

    if label:
        WEEKDAY_ABBR = ["Man", "Tir", "Ons", "Tor", "Fre", "Lør", "Søn"]
        day_prefix = WEEKDAY_ABBR[d.weekday()]
        html += f"""
        <tr class="day-separator">
            <td>{day_prefix}</td>
            <td colspan="{DATA_COLUMNS}">{label}</td>
        </tr>
        """

    for dt in hours:
        hour_str = dt.strftime("%H")
        # Build UTC key deterministically to avoid pytz DST quirks across environments
        dt_key_utc = datetime(
            dt.year, dt.month, dt.day, dt.hour, 0, 0, tzinfo=OSLO_TZ
        ).astimezone(UTC).replace(minute=0, second=0, microsecond=0)

        # Yr: prefer exact hour; if missing, allow nearest within 1h to avoid blanks
        yr_row = YR_DATA.get(dt_key_utc) or get_nearest_row(YR_DATA, dt_key_utc, max_hours=1)

        # Others are hourly in UTC -> exact match only
        dmi_hav_row = DMI_HAV_DATA.get(dt_key_utc)
        dmi_land_row = DMI_LAND_DATA.get(dt_key_utc)
        wind_row = dmi_land_row if dmi_land_row else dmi_hav_row
        met_row = MET_DATA.get(dt_key_utc)
        cop_row = COP_DATA.get(dt_key_utc)
        obs_row = OBS_LISTA_DATA.get(dt_key_utc)

        # Wind (measured in past, Yr in future)
        if dt_key_utc <= now_utc:
            wind_mix_row = obs_row if obs_row else yr_row
        else:
            wind_mix_row = yr_row if yr_row else obs_row
        wind_mix_style = style_wind_combined(wind_mix_row) if wind_mix_row else ""

        cells = [
            {
                "value": fmt_decimal(get_val(dmi_hav_row, "swell_hs_m")),
                "style": style_wave_height(get_val(dmi_hav_row, "swell_hs_m")),
            },
            {
                "value": fmt_integer(get_val(dmi_hav_row, "swell_tp_s")),
                "style": style_period(get_val(dmi_hav_row, "swell_tp_s")),
            },
            {"value": deg_to_arrow(get_val(dmi_hav_row, "swell_dir_deg")), "style": ""},
            {
                "value": fmt_wind(get_val(wind_mix_row, "wind_speed_ms"), get_val(wind_mix_row, "gust_speed_ms")),
                "style": wind_mix_style,
            },
            {"value": deg_to_arrow(get_val(wind_mix_row, "wind_dir_deg")), "style": wind_mix_style},
            {
                "value": fmt_decimal(get_val(dmi_hav_row, "swell_hs_m")),
                "style": style_wave_height(get_val(dmi_hav_row, "swell_hs_m")),
            },
            {
                "value": fmt_decimal(get_val(dmi_hav_row, "swell_tp_s")),
                "style": style_period(get_val(dmi_hav_row, "swell_tp_s")),
            },
            {"value": deg_to_arrow(get_val(dmi_hav_row, "swell_dir_deg")), "style": ""},
            {
                "value": fmt_decimal(get_val(dmi_hav_row, "tp_s")),
                "style": style_period(get_val(dmi_hav_row, "tp_s")),
            },
            {
                "value": fmt_decimal(get_val(dmi_hav_row, "windwave_hs_m")),
                "style": style_wave_height(get_val(dmi_hav_row, "windwave_hs_m")),
            },
            {
                "value": fmt_decimal(get_val(dmi_hav_row, "windwave_tp_s")),
                "style": style_period(get_val(dmi_hav_row, "windwave_tp_s")),
            },
            {"value": deg_to_arrow(get_val(dmi_hav_row, "windwave_dir_deg")), "style": ""},
            {
                "value": fmt_decimal(get_val(cop_row, "WW_Hs (m)")),
                "style": style_wave_height(get_val(cop_row, "WW_Hs (m)")),
            },
            {
                "value": fmt_decimal(get_val(cop_row, "WW_Tm01 (s)")),
                "style": style_period(get_val(cop_row, "WW_Tm01 (s)")),
            },
            {"value": deg_to_arrow(get_val(cop_row, "WW_Dir (°)")), "style": ""},
            {
                "value": fmt_decimal(get_val(cop_row, "S1_Hs (m)")),
                "style": style_wave_height(get_val(cop_row, "S1_Hs (m)")),
            },
            {
                "value": fmt_decimal(get_val(cop_row, "S1_Tm01 (s)")),
                "style": style_period(get_val(cop_row, "S1_Tm01 (s)")),
            },
            {"value": deg_to_arrow(get_val(cop_row, "S1_Dir (°)")), "style": ""},
            {
                "value": fmt_decimal(get_val(cop_row, "S2_Hs (m)")),
                "style": style_wave_height(get_val(cop_row, "S2_Hs (m)")),
            },
            {
                "value": fmt_decimal(get_val(cop_row, "S2_Tm01 (s)")),
                "style": style_period(get_val(cop_row, "S2_Tm01 (s)")),
            },
            {"value": deg_to_arrow(get_val(cop_row, "S2_Dir (°)")), "style": ""},
            {
                "value": fmt_wind(get_val(yr_row, "wind_speed_ms"), get_val(yr_row, "gust_speed_ms")),
                "style": style_gust(get_val(yr_row, "gust_speed_ms")),
            },
            {"value": deg_to_arrow(get_val(yr_row, "wind_dir_deg")), "style": ""},
            {
                "value": fmt_wind(get_val(wind_row, "wind_speed_ms"), get_val(wind_row, "gust_speed_ms")),
                "style": style_gust(get_val(wind_row, "gust_speed_ms")),
            },
            {"value": deg_to_arrow(get_val(wind_row, "wind_dir_deg")), "style": ""},
            {
                "value": fmt_wind(get_val(obs_row, "wind_speed_ms"), get_val(obs_row, "gust_speed_ms")),
                "style": style_gust(get_val(obs_row, "gust_speed_ms")),
            },
            {"value": deg_to_arrow(get_val(obs_row, "wind_dir_deg")), "style": ""},
            {"value": fmt_integer(get_val(dmi_land_row, "temp_air_c")), "style": ""},
            {"value": fmt_integer(get_val(met_row, "sea_temp_c")), "style": ""},
            {"value": fmt_integer(get_val(yr_row, "cloud_cover_pct")), "style": ""},
            {"value": fmt_decimal(get_val(yr_row, "precip_mm")), "style": ""},
        ]

        html += "<tr>"
        html += f"<td>{hour_str}</td>"
        for i, cell in enumerate(cells, start=1):
            style = cell.get("style") or ""
            style_attr = f"text-align:{col_align(i)};"
            if style:
                style_attr += style
            html += f'<td style="{style_attr}">{cell["value"]}</td>'
        html += "</tr>"

html += "</tbody></table></div>"

footer_lines = []
line = format_dmi_metadata("DMI (WAM NSB)", MODEL_METADATA["dmi_hav"])
if line:
    footer_lines.append(line)
line = format_copernicus_metadata(MODEL_METADATA["copernicus"])
if line:
    footer_lines.append(line)
line = format_dmi_metadata("DMI (HARMONIE Dini SF)", MODEL_METADATA["dmi_land"])
if line:
    footer_lines.append(line)
line = format_yr_metadata(MODEL_METADATA["yr"])
if line:
    footer_lines.append(line)

if footer_lines:
    html += '<div class="model-run-wrapper">'
    for line in footer_lines:
        html += f"<div>{line}</div>"
    html += "</div>"

st.components.v1.html(html, height=780 + 24 * len(footer_lines))
