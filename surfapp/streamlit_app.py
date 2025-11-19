import streamlit as st
from datetime import datetime, timedelta, date
from typing import Optional
import pytz
import csv
import os
import json
import subprocess
import sys

from modules.daylight import load_daylight_table, get_light_times

OSLO_TZ = pytz.timezone("Europe/Oslo")
UTC = pytz.utc

# ---- Current time ----
now_utc = datetime.now(UTC)
now_oslo = now_utc.astimezone(OSLO_TZ)
today_date = now_oslo.date()

st.set_page_config(layout="wide")

# ---- Load daylight data ----
DAYLIGHT = load_daylight_table()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_CACHE_DIR = os.path.join(BASE_DIR, "data_cache")
YR_CACHE_PATH = os.path.join(DATA_CACHE_DIR, "yr_lista_cache.csv")
CLOUD_FREEZE_PATH = os.path.join(DATA_CACHE_DIR, "cloud_freeze.json")
FETCH_SCRIPT = os.path.join(BASE_DIR, "fetch_all.py")
FETCH_TIMESTAMP_PATH = os.path.join(DATA_CACHE_DIR, "fetch_all_last_run.txt")


def ensure_data_cache_dir():
    os.makedirs(DATA_CACHE_DIR, exist_ok=True)


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


def load_cloud_freeze():
    if not os.path.exists(CLOUD_FREEZE_PATH):
        return {}
    try:
        with open(CLOUD_FREEZE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_cloud_freeze(data: dict):
    ensure_data_cache_dir()
    with open(CLOUD_FREEZE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def prune_cloud_freeze(data: dict) -> dict:
    today = now_oslo.date()
    pruned = {}
    for key, value in data.items():
        try:
            key_date = date.fromisoformat(key)
        except ValueError:
            continue
        if key_date >= today:
            pruned[key] = value
    if pruned != data:
        save_cloud_freeze(pruned)
    return pruned


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
CLOUD_FREEZE = prune_cloud_freeze(load_cloud_freeze())


def read_model_run_from_cache(filename: str) -> Optional[str]:
    path = os.path.join(DATA_CACHE_DIR, filename)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.startswith("# Model run"):
                    return line.strip("# \n")
    except OSError:
        return None
    return None

def try_parse_float(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return value


def load_cache_by_hour(filename):
    """
    Load a cache CSV into a dict keyed by local Oslo hour.
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
            dt_oslo = dt.astimezone(OSLO_TZ).replace(minute=0, second=0, microsecond=0)

            parsed = {}
            for key, val in row.items():
                if key == "time_utc":
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


MODEL_RUN_INFO = {
    "dmi_hav": read_model_run_from_cache("dmi_hav_lista_cache.csv"),
    "dmi_land": read_model_run_from_cache("dmi_land_lista_cache.csv"),
    "yr": read_model_run_from_cache("yr_lista_cache.csv"),
}


YR_DATA = load_cache_by_hour("yr_lista_cache.csv")
DMI_HAV_DATA = load_cache_by_hour("dmi_hav_lista_cache.csv")
DMI_LAND_DATA = load_cache_by_hour("dmi_land_lista_cache.csv")
MET_DATA = load_cache_by_hour("met_lista_cache.csv")
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

def get_light_oslo_for_date(d: date, cloud_override: Optional[float] = None):
    """
    Return interpolated (first_light_oslo, last_light_oslo) using daylight table
    bounds blended with cloud cover near each window midpoint.

    cloud_override = fixed weight (0..1) to bypass forecast data (e.g. header 50%).
    """
    # Table key is d(d).mm, e.g. "1.01", "18.11"
    date_key = f"{d.day}.{d.month:02d}".lstrip("0")
    row = DAYLIGHT.loc[DAYLIGHT["Dato"].astype(str).str.strip() == date_key]

    if row.empty:
        return None, None

    row = row.iloc[0]
    date_store_key = d.isoformat()

    def parse_utc_to_oslo(clock_str: str):
        if not isinstance(clock_str, str) or ":" not in clock_str:
            return None
        h, m = map(int, clock_str.split(":"))
        dt_utc = datetime(d.year, d.month, d.day, h, m, tzinfo=UTC)
        return dt_utc.astimezone(OSLO_TZ)

    first_light_early = parse_utc_to_oslo(row["First_surf_start_UTC"])
    first_light_late = parse_utc_to_oslo(row["First_surf_end_UTC"])
    last_light_early = parse_utc_to_oslo(row["Last_surf_start_UTC"])
    last_light_late = parse_utc_to_oslo(row["Last_surf_end_UTC"])

    if not all([first_light_early, first_light_late, last_light_early, last_light_late]):
        return None, None

    # Midpoints for cloud sampling
    midpoint_first = first_light_early + (first_light_late - first_light_early) / 2
    midpoint_last = last_light_early + (last_light_late - last_light_early) / 2

    def resolve_weight(slot: str, midpoint: datetime) -> float:
        if cloud_override is not None:
            return max(0.0, min(1.0, cloud_override))

        freeze_entry = CLOUD_FREEZE.get(date_store_key, {})
        stored = freeze_entry.get(slot)
        has_passed = d <= now_oslo.date() and now_oslo >= midpoint

        if has_passed and stored is not None:
            return stored

        cloud_pct = cloud_pct_for_time(midpoint)
        weight = max(0.0, min(1.0, cloud_pct / 100.0))

        if has_passed:
            freeze_entry = CLOUD_FREEZE.setdefault(date_store_key, {})
            freeze_entry[slot] = weight
            save_cloud_freeze(CLOUD_FREEZE)

        return weight

    w_first = resolve_weight("first", midpoint_first)
    w_last = resolve_weight("last", midpoint_last)

    usable_first = first_light_early + (first_light_late - first_light_early) * w_first
    usable_last = last_light_late - (last_light_late - last_light_early) * w_last

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


# ---------------------------------------------------
#  HEADER
# ---------------------------------------------------

MONTHS_NO = ["jan", "feb", "mar", "apr", "mai", "jun",
             "jul", "aug", "sep", "okt", "nov", "des"]
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
Sjøtemp {fmt_decimal(LINDESNES_LATEST[0]) if LINDESNES_LATEST else "--"} °C målt ved Lindesnes {LINDESNES_LATEST[1] if LINDESNES_LATEST and LINDESNES_LATEST[1] else "--"}
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

# Prepare three days: base, base+1, base+2
days = [base_day + timedelta(days=i) for i in range(3)]

# Build blocks: each has a label and a list of hourly datetimes
day_blocks = []

now_floor = now_oslo.replace(minute=0, second=0, microsecond=0)

for idx, d in enumerate(days):
    day_start, day_end = compute_day_window(d)

    # Special handling for the first block:
    # - If it's really "today" and we did NOT skip today,
    #   we start at max(day_start, now - 2h)
    if idx == 0 and (d == today_date) and not skip_today:
        candidate_start = now_floor - timedelta(hours=2)
        if candidate_start < day_start:
            start_time = day_start
        else:
            start_time = candidate_start
    else:
        # For all other days we always start at the daylight-based day_start
        start_time = day_start

    # Build the list of hours for this day
    hours = []
    t = start_time
    while t <= day_end:
        if t.tzinfo is None:
            t = t.replace(tzinfo=OSLO_TZ)
        if t.date() == d:
            hours.append(t)
        t += timedelta(hours=1)

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
            WEEKDAY_NO = ["Mandag", "Tirsdag", "Onsdag",
                          "Torsdag", "Fredag", "Lørdag", "Søndag"]
            weekday = WEEKDAY_NO[d.weekday()]
            month_name = MONTHS_NO[d.month - 1]
            label = f"{weekday} {d.day}. {month_name}"


    day_blocks.append({"label": label, "hours": hours})


# ---------------------------------------------------
#  TABLE RENDERING
# ---------------------------------------------------

ALIGN = {
    1: "right", 2: "center", 3: "left",
    4: "center",
    5: "right", 6: "center", 7: "left",
    8: "right", 9: "left",
    10: "right", 11: "left",
    12: "center", 13: "center",
    14: "center", 15: "center",
}

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
    min-width: 60px;
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
.day-separator td[colspan] {{
    background: #f7f7f7 !important;
    text-align: left;
    padding-left: 12px;
    font-weight: normal;
    font-size: 15px;
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
    margin-top: 16px;
    color: #333;
    font-size: 15px;
    opacity: 0.8;
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
    <th colspan="3">Dønning (dmi)</th>
    <th>P.dom.</th>
    <th colspan="3">Vindbølger (dmi)</th>
    <th colspan="2">Vind (yr)</th>
    <th colspan="2">Vind (dmi)</th>
    <th colspan="2">Temp (°C)</th>
    <th>Skydekke</th>
    <th>Nedbør</th>
</tr>

<tr class="header-sub">
    <th style="text-align:{col_align(1)}">(m)</th>
    <th style="text-align:{col_align(2)}">(s)</th>
    <th style="text-align:{col_align(3)}"></th>
    <th style="text-align:{col_align(4)}">(s)</th>
    <th style="text-align:{col_align(5)}">(m)</th>
    <th style="text-align:{col_align(6)}">(s)</th>
    <th style="text-align:{col_align(7)}"></th>
    <th style="text-align:{col_align(8)}">(m/s)</th>
    <th style="text-align:{col_align(9)}"></th>
    <th style="text-align:{col_align(10)}">(m/s)</th>
    <th style="text-align:{col_align(11)}"></th>
    <th style="text-align:{col_align(12)}">Luft</th>
    <th style="text-align:{col_align(13)}">Sjø</th>
    <th style="text-align:{col_align(14)}">(%)</th>
    <th style="text-align:{col_align(15)}">(mm)</th>
</tr>
</thead>

<tbody>
"""
# Insert blocks and rows
for block in day_blocks:
    label = block["label"]
    hours = block["hours"]

    if label:
        html += f"""
        <tr class="day-separator">
            <td></td>
            <td colspan="15">{label}</td>
        </tr>
        """

    for dt in hours:
        hour_str = dt.strftime("%H")
        dt_key = dt.replace(minute=0, second=0, microsecond=0)
        yr_row = YR_DATA.get(dt_key)
        dmi_hav_row = DMI_HAV_DATA.get(dt_key)
        dmi_land_row = DMI_LAND_DATA.get(dt_key)
        met_row = MET_DATA.get(dt_key)

        cells = [
            fmt_decimal(get_val(dmi_hav_row, "swell_hs_m")),
            fmt_decimal(get_val(dmi_hav_row, "swell_tp_s")),
            deg_to_arrow(get_val(dmi_hav_row, "swell_dir_deg")),
            fmt_decimal(get_val(dmi_hav_row, "tp_s")),
            fmt_decimal(get_val(dmi_hav_row, "windwave_hs_m")),
            fmt_decimal(get_val(dmi_hav_row, "windwave_tp_s")),
            deg_to_arrow(get_val(dmi_hav_row, "windwave_dir_deg")),
            fmt_wind(get_val(yr_row, "wind_speed_ms"), get_val(yr_row, "gust_speed_ms")),
            deg_to_arrow(get_val(yr_row, "wind_dir_deg")),
            fmt_wind(get_val(dmi_land_row, "wind_speed_ms"), get_val(dmi_land_row, "gust_speed_ms")),
            deg_to_arrow(get_val(dmi_land_row, "wind_dir_deg")),
            fmt_integer(get_val(dmi_land_row, "temp_air_c")),
        fmt_integer(get_val(met_row, "sea_temp_c")),
            fmt_integer(get_val(yr_row, "cloud_cover_pct")),
            fmt_decimal(get_val(yr_row, "precip_mm")),
        ]

        html += "<tr>"
        html += f"<td>{hour_str}</td>"
        for i, value in enumerate(cells, start=1):
            html += f'<td style="text-align:{col_align(i)}">{value}</td>'
        html += "</tr>"

html += "</tbody></table></div>"

footer_lines = []
if MODEL_RUN_INFO["dmi_hav"]:
    footer_lines.append(f"dmi_hav (WAM NSB): {MODEL_RUN_INFO['dmi_hav']}")
if MODEL_RUN_INFO["dmi_land"]:
    footer_lines.append(f"dmi_land (HARMONIE Dini SF): {MODEL_RUN_INFO['dmi_land']}")
if MODEL_RUN_INFO["yr"]:
    footer_lines.append(f"yr (Locationforecast v2): {MODEL_RUN_INFO['yr']}")

if footer_lines:
    html += '<div class="model-run-wrapper">'
    for line in footer_lines:
        html += f"<div>{line}</div>"
    html += "</div>"

st.components.v1.html(html, height=780 + 24 * len(footer_lines))
