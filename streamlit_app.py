import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

st.title("Weather Table - Perfect Sticky Headers (Colspan Bug Fixed)")

# Get current Oslo time
oslo_tz = pytz.timezone('Europe/Oslo')
current_time = datetime.now(oslo_tz)
current_hour = current_time.hour

# Start 2 hours before current hour
start_hour = (current_hour - 2) % 24

# Build 24-hour rows
data = []
for i in range(24):
    hour = (start_hour + i) % 24
    row = [f"{hour:02d}"] + ["-"] * 15
    data.append(row)


# --- HTML + CSS (no f-string because of { }) ---
html_table = """
<style>

.sticky-table-container {
    max-height: 600px;
    overflow: auto;
    border: 1px solid #ccc;
}

.sticky-table {
    width: 100%;
    border-collapse: collapse;
    background: white;
}

.sticky-table th,
.sticky-table td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: center;
    min-width: 60px;
    background: #ffffff;
}

/* ------------------------------
   FIX: FORCE EXPLICIT HEADER HEIGHTS
--------------------------------*/
.sticky-table thead tr:first-child th {
    position: sticky;
    top: 0;
    height: 40px;
    background: #f8f9fa;
    font-weight: bold;
    z-index: 20;
}

.sticky-table thead tr:nth-child(2) th {
    position: sticky;
    top: 40px;
    height: 40px;
    background: #f8f9fa;
    z-index: 25;
    font-weight: bold;
}

/* ------------------------------
   FIX: STICKY FIRST COLUMN
--------------------------------*/
.sticky-table th:first-child,
.sticky-table td:first-child {
    position: sticky;
    left: 0;
    background: #f8f9fa;
    font-weight: bold;
    border-right: 2px solid #aaa;
    z-index: 30;
}

/* ------------------------------
   FIX: NO MORE COLSPAN → VISUALLY MERGE
--------------------------------*/

/* 3-column block parent (label cell) */
.merge-parent {
    background: #f0f0f0;
    font-weight: bold;
    text-align: center;
    border-right: none;
}

/* Fake merged cells */
.merge-child {
    background: #f0f0f0;
    border-left: none;
    border-right: none;
}

/* Make the grouped block visually one */
.group-right-border {
    border-right: 1px solid #ddd !important;
}

</style>


<div class="sticky-table-container">
<table class="sticky-table">

<thead>

<!-- ROW 1 – NO COLSPAN -->
<tr>
    <th rowspan="2">Tid</th>

    <!-- Swell (3 columns merged visually) -->
    <th class="merge-parent">Swell</th>
    <th class="merge-child"></th>
    <th class="merge-child group-right-border"></th>

    <!-- Vindbølger (3 columns merged visually) -->
    <th class="merge-parent">Vindbølger</th>
    <th class="merge-child"></th>
    <th class="merge-child group-right-border"></th>

    <th rowspan="1">Periode</th>

    <!-- yr Vind(kast) -->
    <th class="merge-parent">yr Vind</th>
    <th class="merge-child group-right-border"></th>

    <!-- dmi Vind(kast) -->
    <th class="merge-parent">dmi Vind</th>
    <th class="merge-child group-right-border"></th>

    <!-- Temperatur (2 columns) -->
    <th class="merge-parent">Temperatur</th>
    <th class="merge-child group-right-border"></th>

    <th rowspan="2">Skydekke</th>
    <th rowspan="2">Nedbør</th>
</tr>

<!-- ROW 2 – SUBHEADERS (all sticky) -->
<tr>
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

# Add data rows
for row in data:
    html_table += "<tr>"
    for cell in row:
        html_table += f"<td>{cell}</td>"
    html_table += "</tr>"

html_table += """
</tbody>
</table>
</div>
"""

# Display info
st.write(f"**Current Oslo time:** {current_time.strftime('%H:%M — %A %d.%m')}")

st.components.v1.html(html_table, height=650)
