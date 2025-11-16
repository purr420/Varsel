import streamlit as st
from datetime import datetime, timedelta
import pytz

st.title("Weather Table – Day Separator + Clean Style")

# Get current Oslo time
oslo_tz = pytz.timezone('Europe/Oslo')
now = datetime.now(oslo_tz)
current_hour = now.hour

# Start 2 hours before current hour
start_hour = (current_hour - 2) % 24

# Norwegian weekday + month names
WEEKDAY_NO = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag", "Lørdag", "Søndag"]
MONTH_NO = ["jan", "feb", "mar", "apr", "mai", "jun",
            "jul", "aug", "sep", "okt", "nov", "des"]

# Build enough rows to cover day change
rows = []
current_datetime = now - timedelta(hours=2)

for i in range(36):
    hour_str = current_datetime.strftime("%H")
    rows.append({
        "hour": hour_str,
        "datetime": current_datetime
    })
    current_datetime += timedelta(hours=1)

# ----------------------------------------
# Alignment rules (index-based)
# ----------------------------------------
ALIGN = {
    1: "right",   # Høyde (first data column after Tid)
    2: "center",
    3: "left",
    4: "right",
    5: "center",
    6: "left",
    7: "center",
    8: "right",
    9: "left",
    10: "right",
    11: "left",
    12: "center",
    13: "center",
    14: "center",
    15: "center",
}

def col_align(i):
    return ALIGN.get(i, "center")

# ---------------------------------------------
# HTML + CSS TABLE
# ---------------------------------------------
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
    top: 36px;  /* fixed row height to prevent gap */
}}

/* Sticky first column */
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

/* Day separator row */
.day-separator td:first-child {{
    background: #ececec !important;  /* same as first column */
}}
.day-separator td[colspan] {{
    background: #f7f7f7 !important;  /* same as table cells */
    text-align: left;
    padding-left: 12px;
    font-weight: bold;
}}

/* Fix rowspan header alignment on desktop */
@media (min-width: 768px) {{
    .sticky-table thead th[rowspan] {{
        top: 0 !important;
        z-index: 12 !important;  /* above second row, but below corner cell */
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

# ----------------------------------------
# INSERT ROWS + DAY CHANGE SEPARATORS
# ----------------------------------------
last_date = None

for r in rows:
    dt = r["datetime"]
    this_date = dt.date()

    if last_date is not None and this_date != last_date:

        # Determine label
        day_diff = (this_date - now.date()).days
        day = dt.day
        month = MONTH_NO[dt.month - 1]
        weekday = WEEKDAY_NO[dt.weekday()]

        if day_diff == 1:
            label = f"I morgen {day}. {month}"
        else:
            label = f"{weekday} {day}. {month}"

        html += f"""
        <tr class="day-separator">
            <td></td>
            <td colspan="15">{label}</td>
        </tr>
        """

    last_date = this_date

    # Normal row
    html += "<tr>"
    html += f"<td>{r['hour']}</td>"

    # Data columns with alignment
    for i in range(1, 16):
        align = col_align(i)
        html += f'<td style="text-align:{align}">-</td>'

    html += "</tr>"

html += """
</tbody>
</table>
</div>
"""

# Debug
st.write(f"**Oslo:** {now.strftime('%H:%M %d.%m.%Y')}")

# Render table
st.components.v1.html(html, height=700)
