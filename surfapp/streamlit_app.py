import streamlit as st
from datetime import datetime, timedelta, date
import pytz

from modules.daylight import load_daylight_table, get_light_times

OSLO_TZ = pytz.timezone("Europe/Oslo")
UTC = pytz.utc

st.set_page_config(layout="wide")

# ---- Load daylight data ----
DAYLIGHT = load_daylight_table()

# ---- Current time ----
now_utc = datetime.now(UTC)
now_oslo = now_utc.astimezone(OSLO_TZ)

# ---- Light times for header (string versions) ----
light = get_light_times(now_utc, DAYLIGHT)

# ---------------------------------------------------
#  Helpers to work with daylight table per date
# ---------------------------------------------------

def get_light_oslo_for_date(d: date):
    """
    Return (first_light_oslo, last_light_oslo) as aware datetimes in Oslo time
    for the given calendar date d, using the UTC daylight table.
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

    first = parse_utc_to_oslo(row["First_surf_start_UTC"])
    last = parse_utc_to_oslo(row["Last_surf_end_UTC"])
    return first, last


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


# ---------------------------------------------------
#  HEADER
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
        (oppdatert {now_oslo.strftime("%H:%M %d.")} {month_no})
    </span>
</div>

<div class="header-line">
Lyst fra / til: <b>{light["first_light"]} / {light["last_light"]}</b>&nbsp;&nbsp;
Sol opp / ned: <b>{light["sunrise"]} / {light["sunset"]}</b>
</div>

<hr>
""",
    unsafe_allow_html=True
)


# ---------------------------------------------------
#  BUILD DAY BLOCKS (TODAY / I MORGEN / +1)
# ---------------------------------------------------

today_date = now_oslo.date()

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
    # - If the calendar day is tomorrow (today + 1) => "I morgen"
    # - Otherwise => Weekday + date
    if d == today_date and idx == 0 and not skip_today:
        label = None
    else:
        if d == today_date + timedelta(days=1):
            label = "I morgen"
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
    4: "right", 5: "center", 6: "left",
    7: "center", 8: "right", 9: "left",
    10: "right", 11: "left", 12: "center",
    13: "center", 14: "center", 15: "center",
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
        html += "<tr>"
        html += f"<td>{hour_str}</td>"
        for i in range(1, 16):
            html += f'<td style="text-align:{col_align(i)}">-</td>'
        html += "</tr>"

html += "</tbody></table></div>"

st.components.v1.html(html, height=700)
