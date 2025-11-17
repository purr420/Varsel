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

# ---- Light times for header ----
light = get_light_times(now_utc, DAYLIGHT)

# ---------------------------------------------------
#  Helpers
# ---------------------------------------------------

def get_light_oslo_for_date(d: date):
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
    first_light, last_light = get_light_oslo_for_date(d)
    if first_light is None or last_light is None:
        return (
            datetime(d.year, d.month, d.day, 0, 0, tzinfo=OSLO_TZ),
            datetime(d.year, d.month, d.day, 23, 0, tzinfo=OSLO_TZ),
        )

    first_floor = first_light.replace(minute=0, second=0, microsecond=0)
    day_start = first_floor - timedelta(hours=2)
    if day_start.date() < d:
        day_start = datetime(d.year, d.month, d.day, 0, 0, tzinfo=OSLO_TZ)

    last_hour = last_light.hour + (1 if last_light.minute > 0 else 0)
    if last_hour > 23:
        last_hour = 23

    day_end = datetime(d.year, d.month, d.day, last_hour, 0, tzinfo=OSLO_TZ)
    return day_start, day_end

# ---------------------------------------------------
#  HEADER
# ---------------------------------------------------

MONTHS_NO = ["jan","feb","mar","apr","mai","jun","jul","aug","sep","okt","nov","des"]
month_no = MONTHS_NO[now_oslo.month - 1]

st.markdown(
    f"""
<style>
.header-title {{
    font-size: 42px;
    font-weight: 800;
    margin-bottom: 10px;
}}
.header-sub {{
    font-size: 26px;
    margin-top: 2px;
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
    for Lista <span class="header-updated">(oppdatert {now_oslo.strftime("%H:%M %d.")} {month_no})</span>
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
#  BUILD DAY BLOCKS
# ---------------------------------------------------

today_date = now_oslo.date()
first_today, last_today = get_light_oslo_for_date(today_date)

skip_today = False
if last_today is not None and now_oslo > (last_today + timedelta(hours=1)):
    skip_today = True

base_day = today_date if not skip_today else today_date + timedelta(days=1)
days = [base_day + timedelta(days=i) for i in range(3)]

day_blocks = []
now_floor = now_oslo.replace(minute=0, second=0, microsecond=0)

MONTHS_NO = ["jan","feb","mar","apr","mai","jun","jul","aug","sep","okt","nov","des"]
WEEKDAY_NO = ["Mandag","Tirsdag","Onsdag","Torsdag","Fredag","Lørdag","Søndag"]

for idx, d in enumerate(days):
    day_start, day_end = compute_day_window(d)

    if idx == 0 and (d == today_date) and not skip_today:
        cand = now_floor - timedelta(hours=2)
        start_time = max(cand, day_start)
    else:
        start_time = day_start

    hours = []
    t = start_time
    while t <= day_end:
        if t.date() == d:
            hours.append(t)
        t += timedelta(hours=1)

    if not hours:
        continue

    if d == today_date and idx == 0 and not skip_today:
        label = None
    else:
        if d == today_date + timedelta(days=1):
            label = "I morgen"
        else:
            label = f"{WEEKDAY_NO[d.weekday()]} {d.day}. {MONTHS_NO[d.month-1]}"

    day_blocks.append({"label": label, "hours": hours})

# ---------------------------------------------------
#  TABLE
# ---------------------------------------------------

ALIGN = {
    1:"right",2:"center",3:"left",
    4:"right",5:"center",6:"left",
    7:"center",8:"right",9:"left",
    10:"right",11:"left",12:"center",
    13:"center",14:"center",15:"center"
}
def col_align(i): return ALIGN.get(i,"center")

html = f"""
<style>

.sticky-table-container {{
    max-height: 650px;
    overflow: auto;
}}

.sticky-table {{
    width: 100%;
    border-collapse: collapse;
}}

/* General cells */
.sticky-table th,
.sticky-table td {{
    padding: 8px;
    min-width: 60px;
    background: #f7f7f7;
    border: none;
    vertical-align: middle;
}}

/* Header weights */
.sticky-table thead th {{
    font-weight: 500;
}}
.header-top th {{
    font-weight: 600;
}}
.header-sub th {{
    font-weight: 400;
}}

/* Sticky header */
.sticky-table thead th {{
    position: sticky;
    background: #ececec;
    z-index: 10;
}}
.sticky-table thead tr:first-child th {{ top: 0; }}
.sticky-table thead tr:nth-child(2) th {{ top: 36px; }}

/* Sticky first column: center aligned, NOT bold */
.sticky-table td:first-child,
.sticky-table th:first-child {{
    position: sticky;
    left: 0;
    background: #ececec;
    z-index: 20;
    text-align: center;
    font-weight: 400;
}}

/* Day separator: 15px, NOT bold */
.day-separator td[colspan] {{
    background: #f7f7f7;
    padding-left: 12px;
    font-size: 15px;
    font-weight: 400;
    text-align: left;
}}

</style>

<div class="sticky-table-container"><table class="sticky-table">

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

# Insert day blocks
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
        html += "<tr>"
        html += f"<td>{dt.strftime('%H')}</td>"
        for i in range(1,16):
            html += f'<td style="text-align:{col_align(i)}">-</td>'
        html += "</tr>"

html += "</tbody></table></div>"

st.components.v1.html(html, height=700)
