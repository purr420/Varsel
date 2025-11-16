import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz

# -----------------------------
# CONFIG
# -----------------------------

st.set_page_config(layout="wide")
st.title("Weather Table – Norwegian Date Separators & Clean Layout")

oslo_tz = pytz.timezone('Europe/Oslo')
now = datetime.now(oslo_tz)

# Norwegian weekday names (weekday(): Monday=0)
WEEKDAY_NO = ["Mandag", "Tirsdag", "Onsdag", "Torsdag",
              "Fredag", "Lørdag", "Søndag"]

# Norwegian month abbreviations
MONTHS_NO = ["jan", "feb", "mar", "apr", "mai", "jun",
             "jul", "aug", "sep", "okt", "nov", "des"]

# -----------------------------
# TIME ROWS GENERATION (48h sample for demo)
# -----------------------------

hours = []
for i in range(48):  # 48 hours ahead to ensure several day changes
    t = now + timedelta(hours=i)
    hours.append(t)

# -----------------------------
# TABLE HEADER STRUCTURE
# -----------------------------

header_row_1 = [
    ("Tid", 1, 2),
    ("Swell", 3, 1),
    ("Vindbølger", 3, 1),
    ("Periode", 1, 1),
    ("yr Vind(kast)", 2, 1),
    ("dmi Vind(kast)", 2, 1),
    ("Temperatur", 2, 1),
    ("Skydekke", 1, 2),
    ("Nedbør", 1, 2),
]

header_row_2 = [
    "Høyde", "Periode", "Retning",
    "Høyde", "Periode", "Retning",
    "dominant",
    "Styrke", "Retning",
    "Styrke", "Retning",
    "Land", "Hav",
]

# Total columns = 16 including Tid
total_columns = 16

# -----------------------------
# COLUMN ALIGNMENT RULES
# a:c,b:r,c:c,d:l,e:r,f:c,g:l,h:c,i:r,j:l,k:r,l:l, rest c
# Columns are 0-indexed (Tid = col 0)
# -----------------------------

ALIGN = {
    0: "center",   # Tid
    1: "right",
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
    12: "left",
}

def get_align(col):
    return ALIGN.get(col, "center")

# -----------------------------
# HTML + CSS START
# -----------------------------

html = f"""
<style>
.sticky-container {{
    max-height: 650px;
    overflow: auto;
    background: #f5f5f5;
}}

.table {{
    width: 100%;
    border-collapse: collapse;
    background: #fafafa;
}}

.table th,
.table td {{
    padding: 6px 8px;
    background: #fafafa;
}}

.table thead th {{
    position: sticky;
    top: 0;
    background: #e6e6e6; /* subtle darker header */
    z-index: 20;
    font-weight: bold;
}}

.table thead tr:nth-child(2) th {{
    top: 32px; /* second header row */
}}

.table td:first-child,
.table th:first-child {{
    position: sticky;
    left: 0;
    background: #e6e6e6; /* same for first column */
    z-index: 25;
    font-weight: bold;
}}

.separator-row td {{
    background: #fafafa !important;
    font-weight: bold;
    text-align: left !important;
    padding-left: 12px;
}}

</style>

<div class="sticky-container">
<table class="table">

<thead>
<tr>
"""

# First header row
for label, colspan, rowspan in header_row_1:
    html += f'<th colspan="{colspan}" rowspan="{rowspan}">{label}</th>'

html += "</tr><tr>"

# Second header row
for label in header_row_2:
    html += f"<th>{label}</th>"

html += "</tr></thead><tbody>"

# -----------------------------
# BUILD BODY WITH DAY SEPARATORS
# -----------------------------

current_day = hours[0].date()

for dt in hours:
    day = dt.date()

    if day != current_day:
        # INSERT SEPARATOR ROW

        day_index = (day - now.date()).days

        # Tomorrow → special case
        if day_index == 1:
            text = f"I morgen {day.day}. {MONTHS_NO[day.month-1]}"
        else:
            weekday = WEEKDAY_NO[day.weekday()]
            text = f"{weekday} {day.day}. {MONTHS_NO[day.month-1]}"

        # first column blank, columns 2–16 merged
        html += f"""
        <tr class="separator-row">
            <td></td>
            <td colspan="{total_columns - 1}">{text}</td>
        </tr>
        """

        current_day = day

    # NORMAL HOURLY ROW
    time_str = dt.strftime("%H")

    html += "<tr>"

    # First column
    html += f'<td style="text-align:center">{time_str}</td>'

    # Data columns (fake dashes)
    for col in range(1, total_columns):
        align = get_align(col)
        html += f'<td style="text-align:{align}">-</td>'

    html += "</tr>"

html += "</tbody></table></div>"

# -----------------------------
# RENDER
# -----------------------------

st.components.v1.html(html, height=700, scrolling=True)

