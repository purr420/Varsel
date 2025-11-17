import streamlit as st
from datetime import datetime, timedelta
import pytz

from modules.daylight import load_daylight_table, get_light_times

OSLO_TZ = pytz.timezone("Europe/Oslo")
UTC = pytz.utc

st.set_page_config(layout="wide")

# --------------------------------------------------
# LOAD DAYLIGHT TABLE
# --------------------------------------------------
DAYLIGHT = load_daylight_table()

now_utc = datetime.now(UTC)
now_oslo = now_utc.astimezone(OSLO_TZ)

light = get_light_times(now_utc, DAYLIGHT)


# --------------------------------------------------
# HEADER
# --------------------------------------------------
MONTHS_NO = ["jan", "feb", "mar", "apr", "mai", "jun",
             "jul", "aug", "sep", "okt", "nov", "des"]
month_no = MONTHS_NO[now_oslo.month - 1]

st.markdown(
    f"""
<style>
.header-title {{
    font-size: 42px;
    font-weight: 800;
    line-height: 1.0;
    margin-bottom: 14px;
}}

.header-sub {{
    font-size: 26px;
    font-weight: 500;
    line-height: 1.0;
    margin-top: -2px;
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


# --------------------------------------------------
# LIGHT-TIME PARSING
# --------------------------------------------------
def parse_today(hhmm: str):
    if hhmm == "--:--":
        return None
    h, m = map(int, hhmm.split(":"))
    return now_oslo.replace(hour=h, minute=m, second=0, microsecond=0)


first_light = parse_today(light["first_light"])
last_light = parse_today(light["last_light"])


def ceil_hour(dt):
    if dt is None:
        return None
    if dt.minute > 0 or dt.second > 0:
        return dt.replace(minute=0, second=0) + timedelta(hours=1)
    return dt.replace(minute=0, second=0)


first_light_floor = ceil_hour(first_light)
last_light_floor = ceil_hour(last_light)

dark_threshold = last_light_floor + timedelta(hours=1)

# Load tomorrow's first light from table:
tomorrow = now_oslo.date() + timedelta(days=1)

# Windows safe formatter
date_key_tomorrow = tomorrow.strftime("%-d.%m") if st.runtime.exists() == False else tomorrow.strftime("%d.%m")

row_t = DAYLIGHT.loc[DAYLIGHT["Dato"] == date_key_tomorrow]

if row_t.empty:
    first_light_tomorrow = now_oslo.replace(hour=8, minute=0)
else:
    h, m = map(int, row_t.iloc[0]["First_surf_start_UTC"].split(":"))
    dt_utc = datetime(2025, tomorrow.month, tomorrow.day, h, m, tzinfo=UTC)
    first_light_tomorrow = dt_utc.astimezone(OSLO_TZ)

first_light_tomorrow_floor = ceil_hour(first_light_tomorrow)
tomorrow_start = first_light_tomorrow_floor - timedelta(hours=2)


# --------------------------------------------------
# BUILD TIME ROWS
# --------------------------------------------------
rows = []

# CASE 1: BEFORE dark-threshold → show remainder of today
if now_oslo < dark_threshold:

    # Start today at now−2h
    start_today = (now_oslo - timedelta(hours=2)).replace(minute=0, second=0)
    t = start_today

    while t <= last_light_floor:
        rows.append(t)
        t += timedelta(hours=1)

    rows.append("SEP")  # day separator

    # Add tomorrow (24 hours from tomorrow_start)
    t = tomorrow_start
    end_t = tomorrow_start + timedelta(hours=24)
    while t < end_t:
        rows.append(t)
        t += timedelta(hours=1)

# CASE 2: AFTER dark → skip today entirely
else:
    rows.append("SEP")
    t = tomorrow_start
    end_t = tomorrow_start + timedelta(hours=24)
    while t < end_t:
        rows.append(t)
        t += timedelta(hours=1)


# --------------------------------------------------
# TABLE RENDERING
# --------------------------------------------------

ALIGN = {
    1: "right", 2: "center", 3: "left",
    4: "right", 5: "center", 6: "left",
    7: "center", 8: "right", 9: "left",
    10: "right", 11: "left", 12: "center",
    13: "center", 14: "center", 15: "center",
}
def col_align(i): return ALIGN.get(i, "center")

MONTH_NO = ["jan","feb","mar","apr","mai","jun","jul","aug","sep","okt","nov","des"]
WEEKDAY_NO = ["Mandag","Tirsdag","Onsdag","Torsdag","Fredag","Lørdag","Søndag"]

def format_day(dt):
    return f"{WEEKDAY_NO[dt.weekday()]} {dt.day}. {MONTH_NO[dt.month-1]}"


# CSS + table start
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
    <th style="text-align:{col_align(1)}">(m)</th>
    <th style="text-align:{col_align(2)}">(s)</th>
    <th style="text-align:{col_align(3)}"></th>
    <th style="text-align:{col_align(4)}">(m)</th>
    <th style="text-align:{col_align(5)}">(s)</th>
    <th style="text-align:{col_align(6)}"></th>
    <th style="text-align:{col_align(7)}">(s)</th>
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

# INSERT ROWS
last_date = None

for item in rows:

    if item == "SEP":
        # Find the next real datetime
        idx = rows.index("SEP")
        next_dt = next(x for x in rows[idx+1:] if isinstance(x, datetime))
        html += f"""
        <tr class="day-separator">
            <td></td>
            <td colspan="15">{format_day(next_dt)}</td>
        </tr>
        """
        continue

    dt = item
    hour = dt.strftime("%H")

    # Date separator if needed
    if last_date and dt.date() != last_date:
        html += f"""
        <tr class="day-separator">
            <td></td>
            <td colspan="15">{format_day(dt)}</td>
        </tr>
        """

    last_date = dt.date()

    # print row
    html += "<tr>"
    html += f"<td>{hour}</td>"
    for _ in range(15):
        html += "<td>-</td>"
    html += "</tr>"

html += "</tbody></table></div>"

st.components.v1.html(html, height=700)
