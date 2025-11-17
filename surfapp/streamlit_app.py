import streamlit as st
from datetime import datetime, timedelta
import pytz

from modules.daylight import load_daylight_table, get_light_times

OSLO_TZ = pytz.timezone("Europe/Oslo")
UTC = pytz.utc

st.set_page_config(layout="wide")

# ---------------------------------------------------
# LOAD DAYLIGHT DATA
# ---------------------------------------------------
DAYLIGHT = load_daylight_table()

now_utc = datetime.now(UTC)
now_oslo = now_utc.astimezone(OSLO_TZ)

light = get_light_times(now_utc, DAYLIGHT)


# ---------------------------------------------------
# HEADER
# ---------------------------------------------------
MONTHS_NO = ["jan", "feb", "mar", "apr", "mai", "jun",
             "jul", "aug", "sep", "okt", "nov", "des"]
month_no = MONTHS_NO[now_oslo.month - 1]

st.markdown(
    f"""
<style>
.header-title {{
    font-size: 42px;
    font-weight: 800;
    line-height: 1.05;
    margin-bottom: 8px;
}}

.header-sub {{
    font-size: 26px;
    font-weight: 500;
    line-height: 1.0;
    margin-top: 0px;
    margin-bottom: 4px;
}}

.header-updated {{
    font-size: 15px;
    opacity: 0.75;
    margin-left: 8px;
}}

.header-line {{
    font-size: 15px;
    opacity: 0.80;
    margin-top: 10px;
    margin-bottom: 4px;
}}
</style>

<div class="header-title">Varselet</div>

<div class="header-sub">
    for Lista
    <span class="header-updated">
        (oppdatert {now_oslo.strftime("%H:%M %d.")} {month_no})
    </span>
</div>

<div class="header-line">
Lyst fra / til: <b>{light["first_light"]} / {light["last_light"]}</b> &nbsp;&nbsp;
Sol opp / ned: <b>{light["sunrise"]} / {light["sunset"]}</b>
</div>

<hr>
""",
    unsafe_allow_html=True
)

# ---------------------------------------------------
# TIME LOGIC — BUILD TIMELINE
# ---------------------------------------------------

def to_dt_today(hhmm):
    if hhmm == "--:--":
        return None
    h, m = map(int, hhmm.split(":"))
    return now_oslo.replace(hour=h, minute=m, second=0, microsecond=0)


# Convert today's first/last light to datetime
first_light = to_dt_today(light["first_light"])
last_light = to_dt_today(light["last_light"])

# Rounding rules:
def floor_to_hour(dt):
    return dt.replace(minute=0, second=0, microsecond=0)

def ceil_to_hour(dt):
    if dt.minute > 0 or dt.second > 0:
        return dt.replace(minute=0, second=0) + timedelta(hours=1)
    return dt.replace(minute=0, second=0)

# Today:
first_light_floor = floor_to_hour(first_light)
last_light_floor = ceil_to_hour(last_light)

# Dark threshold = 1h after rounded last light
dark_threshold = last_light_floor + timedelta(hours=1)

# Tomorrow:
tomorrow = now_oslo.date() + timedelta(days=1)

# Format date key for daylight CSV
try:
    date_key_tomorrow = tomorrow.strftime("%-d.%m")   # Linux/macOS
except:
    date_key_tomorrow = tomorrow.strftime("%d.%m")    # Windows fallback

row_tom = DAYLIGHT.loc[DAYLIGHT["Dato"] == date_key_tomorrow]


if row_tom.empty:
    # fallback (should never happen)
    first_light_tomorrow = now_oslo.replace(hour=8, minute=0)
else:
    h, m = map(int, row_tom.iloc[0]["First_surf_start_UTC"].split(":"))
    dt_utc = datetime(2025, tomorrow.month, tomorrow.day, h, m, tzinfo=UTC)
    first_light_tomorrow = dt_utc.astimezone(OSLO_TZ)

# NEW RULE:
# Tomorrow starts = floor(first_light) − 2 hours
first_light_tomorrow_floor = floor_to_hour(first_light_tomorrow)
tomorrow_start = first_light_tomorrow_floor - timedelta(hours=2)


# ---------------------------------------------------
# BUILD LIST OF ROW DATETIMES
# ---------------------------------------------------
rows = []

# CASE 1 — Before dark_threshold → show remaining of today
if now_oslo < dark_threshold:

    start_today = floor_to_hour(now_oslo - timedelta(hours=2))
    t = start_today

    # Show until the rounded last light
    while t <= last_light_floor:
        rows.append(t)
        t += timedelta(hours=1)

    # Separator
    rows.append("SEP")

    # Add tomorrow hours
    t = tomorrow_start
    end_tomorrow = tomorrow_start + timedelta(hours=24)
    while t < end_tomorrow:
        rows.append(t)
        t += timedelta(hours=1)

# CASE 2 — After dark_threshold → skip today, start tomorrow
else:
    rows.append("SEP")
    t = tomorrow_start
    end_tomorrow = tomorrow_start + timedelta(hours=24)
    while t < end_tomorrow:
        rows.append(t)
        t += timedelta(hours=1)


# ---------------------------------------------------
# TABLE RENDERING
# ---------------------------------------------------

ALIGN = {
    1: "right", 2: "center", 3: "left",
    4: "right", 5: "center", 6: "left",
    7: "center", 8: "right", 9: "left",
    10: "right", 11: "left", 12: "center",
    13: "center", 14: "center", 15: "center",
}

def col_align(i):
    return ALIGN.get(i, "center")

MONTH_NO = ["jan","feb","mar","apr","mai","jun","jul","aug","sep","okt","nov","des"]
WEEKDAY_NO = ["Mandag","Tirsdag","Onsdag","Torsdag","Fredag","Lørdag","Søndag"]

def format_day(dt):
    return f"{WEEKDAY_NO[dt.weekday()]} {dt.day}. {MONTH_NO[dt.month - 1]}"

html_rows = ""
last_date = None

# Build all rows
for i, item in enumerate(rows):

    # === DAY SEPARATOR ===
    if item == "SEP":
        # Find next actual datetime
        next_dt = next(x for x in rows[i+1:] if x != "SEP")

        html_rows += f"""
        <tr class="day-separator">
            <td></td>
            <td colspan="15">{format_day(next_dt)}</td>
        </tr>
        """

        # Prevent double-separator
        last_date = next_dt.date()
        continue

    # === NORMAL ROW ===
    dt = item
    this_date = dt.date()

    # Date changed → insert separator
    if last_date and this_date != last_date:
        html_rows += f"""
        <tr class="day-separator">
            <td></td>
            <td colspan="15">{format_day(dt)}</td>
        </tr>
        """

    last_date = this_date

    hour_str = dt.strftime("%H")
    html_rows += "<tr>"
    html_rows += f"<td>{hour_str}</td>"
    for j in range(1, 16):
        html_rows += f'<td style="text-align:{col_align(j)}">-</td>'
    html_rows += "</tr>"


# ---------------------------------------------------
# TABLE HTML SHELL
# ---------------------------------------------------

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

.header-top {{
    background: #ececec !important;
}}
.header-sub {{
    background: #ececec !important;
}}

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

.sticky-table td:first-child,
.sticky-table th:first-child {{
    position: sticky;
    left: 0;
    background: #ececec;
    z-index: 20;
    font-weight: bold;
}}

.day-separator td[colspan] {{
    background: #f7f7f7 !important;
    text-align: left;
    padding-left: 12px;
    font-weight: bold;
}}

</style>

<div class="sticky-table-container">
<table class="sticky-table">

<thead>
<tr class="header-top">
    <th rowspan="2">Tid</th>
    <th colspan="3">Swell</th>
    <th colspan="3">Vindbølger</th>
    <th>P.dom.</th>
    <th colspan="2">Vind (yr)</th>
    <th colspan="2">Vind (dmi)</th>
    <th colspan="2">Temp (°C)</th>
    <th>Skydekke</th>
    <th>Nedbør</th>
</tr>

<tr class="header-sub">
    <th>(m)</th><th>(s)</th><th></th>
    <th>(m)</th><th>(s)</th><th></th>
    <th>(s)</th>
    <th>(m/s)</th><th></th>
    <th>(m/s)</th><th></th>
    <th>Luft</th><th>Sjø</th>
    <th>(%)</th><th>(mm)</th>
</tr>
</thead>

<tbody>
{html_rows}
</tbody></table></div>
"""

st.components.v1.html(html, height=700)
