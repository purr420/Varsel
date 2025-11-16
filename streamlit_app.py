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
    text-align: center;
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
    top: 40px;
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
.day-separator {{
    background: #e0e0e0 !important;
    font-weight: bold;
}}
.day-separator td {{
    background: #e0e0e0 !important;
    text-align: left !important;
    padding-left: 12px;
}}
</style>

<div class="sticky-table-container">
<table class="sticky-table">

<thead>
<tr class="header-top">
    <th rowspan="2">Tid</th>
    <th colspan="3">Swell</th>
    <th colspan="3">Vindbølger</th>
    <th>Periode</th>
    <th colspan="2">yr Vind(kast)</th>
    <th colspan="2">dmi Vind(kast)</th>
    <th colspan="2">Temperatur</th>
    <th rowspan="2">Skydekke</th>
    <th rowspan="2">Nedbør</th>
</tr>

<tr class="header-sub">
    <th>Høyde</th>
    <th>Periode</th>
    <th>Retning</th>
    <th>Høyde</th>
    <th>Periode</th>
    <th>Retning</th>
    <th>dominant</th>
    <th>Styrke</th>
    <th>Retning</th>
    <th>Styrke</th>
    <th>Retning</th>
    <th>Land</th>
    <th>Hav</th>
</tr>
</thead>

<tbody>
"""

# ----------------------------------------
# Alignment rules (index-based)
# ----------------------------------------
ALIGN = {
    1: "center",
    2: "right",
    3: "center",
    4: "left",
    5: "right",
    6: "center",
    7: "left",
    8: "center",
    9: "right",
    10: "left",
    11: "right",
    12: "left",
}

def col_align(i):
    return ALIGN.get(i, "center")

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
