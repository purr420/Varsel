import streamlit as st
from datetime import datetime, timedelta
import pytz

from modules.daylight import get_light_times, load_daylight_table

st.set_page_config(layout="wide")


# ---- 1. Last inn dagslys-tabell ----
DAYLIGHT_TABLE = load_daylight_table()

# ---- 2. Nåtid i Oslo ----
oslo = pytz.timezone("Europe/Oslo")
now = datetime.now(oslo)

# ---- 3. Dummy skydekke (API senere) ----
cloud_cover = None  # None = antas 50%

# ---- 4. Beregn lys ----
light = get_light_times(now, cloud_cover, DAYLIGHT_TABLE)
first_light = light["first_light"]
last_light = light["last_light"]


# ---- 5. UI HEADER ----
st.markdown(f"""
# Varselet  
### for Lista  

<small>Oppdatert {now.strftime("%H:%M %d.%m")}</small>

---

**Første lys:** {first_light}  
**Siste lys:** {last_light}

""", unsafe_allow_html=True)



# ---------------------------------------------------
# 6. TABELLKODEN (LIMT INN UENDRET FRA TIDLIGERE)
# ---------------------------------------------------

# Bygg radliste
start = now - timedelta(hours=2)
rows = []
for i in range(36):
    rows.append({"hour": start.strftime("%H"), "datetime": start})
    start += timedelta(hours=1)

# Alignment
ALIGN = {
    1: "right", 2: "center", 3: "left",
    4: "right", 5: "center", 6: "left",
    7: "center", 8: "right", 9: "left",
    10: "right", 11: "left", 12: "center",
    13: "center", 14: "center", 15: "center",
}
def col_align(i): return ALIGN.get(i, "center")

# HTML kode (samme som før)
html = f"""
<style>
/* Full width */
.reportview-container .main .block-container {{
    max-width: 100% !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
}}

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

.sticky-table thead tr:first-child th:first-child {{
    z-index: 30 !important;
}}

.day-separator td:first-child {{
    background: #ececec !important;
}}
.day-separator td[colspan] {{
    background: #f7f7f7 !important;
    text-align: left;
    padding-left: 12px;
    font-weight: bold;
}}

@media (min-width: 768px) {{
    .sticky-table thead th[rowspan] {{
        top: 0 !important;
        z-index: 12 !important;
    }}
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
    <th style="text-align:{col_align(3)}"> </th>
    <th style="text-align:{col_align(4)}">(m)</th>
    <th style="text-align:{col_align(5)}">(s)</th>
    <th style="text-align:{col_align(6)}"> </th>
    <th style="text-align:{col_align(7)}">(s)</th>
    <th style="text-align:{col_align(8)}">(m/s)</th>
    <th style="text-align:{col_align(9)}"> </th>
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

# Insert rows
last_date = None
MONTH_NO = ["jan","feb","mar","apr","mai","jun","jul","aug","sep","okt","nov","des"]
WEEKDAY_NO = ["Mandag","Tirsdag","Onsdag","Torsdag","Fredag","Lørdag","Søndag"]

for r in rows:
    dt = r["datetime"]
    this_date = dt.date()

    if last_date and this_date != last_date:
        day = dt.day
        month = MONTH_NO[dt.month - 1]
        weekday = WEEKDAY_NO[dt.weekday()]
        html += f"""
        <tr class="day-separator">
            <td></td>
            <td colspan="15">{weekday} {day}. {month}</td>
        </tr>
        """
    last_date = this_date

    html += "<tr>"
    html += f"<td>{r['hour']}</td>"
    for i in range(1, 16):
        html += f'<td style="text-align:{col_align(i)}">-</td>'
    html += "</tr>"

html += "</tbody></table></div>"

# Render HTML
st.components.v1.html(html, height=700)
