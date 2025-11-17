import streamlit as st
from datetime import datetime, timedelta
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

# ---- Light times ----
light = get_light_times(now_utc, DAYLIGHT)


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
    margin-bottom: 8px;
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



# ---------------------------------------------------
#  TIME ROWS FOR TABLE
# ---------------------------------------------------
start = now_oslo - timedelta(hours=2)
rows = []

for i in range(36):
    rows.append({"hour": start.strftime("%H"), "datetime": start})
    start += timedelta(hours=1)


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

last_date = None
MONTH_NO = ["jan","feb","mar","apr","mai","jun","jul","aug","sep","okt","nov","des"]
WEEKDAY_NO = ["Mandag","Tirsdag","Onsdag","Torsdag","Fredag","Lørdag","Søndag"]

for r in rows:
    dt = r["datetime"]
    this_date = dt.date()

    if last_date and this_date != last_date:
        weekday = WEEKDAY_NO[dt.weekday()]
        month = MONTH_NO[dt.month - 1]
        html += f"""
        <tr class="day-separator">
            <td></td>
            <td colspan="15">{weekday} {dt.day}. {month}</td>
        </tr>
        """
    last_date = this_date

    html += "<tr>"
    html += f"<td>{r['hour']}</td>"
    for i in range(1, 16):
        html += f'<td style="text-align:{col_align(i)}">-</td>'
    html += "</tr>"

html += "</tbody></table></div>"

st.components.v1.html(html, height=700)
