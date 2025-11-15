import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz

st.title("Weather Table - Høyde Cell Sticky Behavior Fixed (targeted)")

# Get current Oslo time (UTC+1 in winter, UTC+2 in summer)
oslo_tz = pytz.timezone('Europe/Oslo')
current_time = datetime.now(oslo_tz)
current_hour = current_time.hour

# Start time: 2 hours before current hour
start_hour = (current_hour - 2) % 24

# Create header row with letters a-p (16 columns)
columns = [chr(ord('a') + i) for i in range(16)]

# Create time-based rows (24 hours starting from 2 hours before current)
data = []
times = []

for i in range(24):
    hour = (start_hour + i) % 24
    time_str = f"{hour:02d}"
    times.append(time_str)
    
    row = [time_str]  # First column: time
    row.extend(["-"] * 15)  # Rest of columns filled with dashes
    data.append(row)

# NOTE: Use a normal (non-f) triple-quoted string so { } in CSS/HTML don't break Python f-string parsing
html_table = """
<style>
/* --- Container & base table --- */
.sticky-table-container {
    max-height: 600px;
    overflow: auto;
    border: 1px solid #ddd;
    margin: 10px 0;
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
    vertical-align: middle;
    min-width: 60px;
    background: #f8f9fa;
}

/* --- Force explicit header heights so 'top' aligns exactly --- */
.sticky-table thead tr:first-child th {
    position: sticky;
    top: 0;
    height: 40px;                 /* explicit first header height */
    line-height: 24px;
    background: #f8f9fa;
    font-weight: bold;
    z-index: 15;
}

.sticky-table thead tr:nth-child(2) th {
    position: sticky;
    top: 40px;                    /* must match first header height */
    height: 40px;                 /* explicit second header height */
    line-height: 24px;
    background: #f8f9fa;
    font-weight: bold;
    z-index: 16;                  /* keeps entire second row above first row */
}

/* --- Sticky first column --- */
.sticky-table td:first-child,
.sticky-table th:first-child {
    position: sticky;
    left: 0;
    background: #f8f9fa;
    font-weight: bold;
    border-right: 2px solid #999;
    z-index: 20;
}

/* --- Tid header - MAX sticky (corner) --- */
.sticky-table thead th:first-child {
    position: sticky !important;
    top: 0 !important;
    left: 0 !important;
    background: #f8f9fa !important;
    border-right: 2px solid #999;
    z-index: 100 !important;
    font-weight: bold !important;
}

/* --- >>> TARGETED FIX: Høyde cell (second header row, first TH in that row) --- */
/* This selector targets the first <th> inside the second <tr> of the thead,
   which in your markup is the "Høyde" cell. */
.sticky-table thead tr:nth-child(2) th:first-child {
    /* ensure sticky and exact top */
    position: sticky;
    top: 40px;                    /* same as other second-row headers */
    z-index: 250 !important;      /* HIGHER than parent colspan (15) and other headers */

    /* border and background to match adjacent header cells */
    background: #f8f9fa !important;
    border-right: 1px solid #ddd !important;
    border-left: 1px solid #ddd !important;
    box-shadow: 0 1px 0 0 rgba(0,0,0,0.02); /* hide thin seam on some browsers */

    /* keep visual identical to the cell to its right */
    font-weight: bold;
    text-align: center;
}

/* --- Slight safety for adjacent cells so borders align --- */
.sticky-table thead tr:nth-child(2) th + th {
    border-left: 1px solid #ddd;
}

/* --- Small tweak: ensure collapsed borders don't show odd hairlines --- */
.sticky-table td, .sticky-table th {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* optional: ensure body rows have white background so stacked headers look clean */
.sticky-table tbody td {
    background: #ffffff;
}
</style>

<div class="sticky-table-container">
<table class="sticky-table">
<thead>
<tr>
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

# Add all time rows
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

# Display some info about the current setup
st.write(f"**Current Oslo time:** {current_time.strftime('%H:%M')} on {current_time.strftime('%A %d. %b')}")
st.write(f"**Time range:** Starting from {start_hour:02d}:00 (2 hours before current hour)")
st.write(f"**Targeted fix applied:** Høyde cell now has individual z-index, borders and box-shadow to eliminate seam/jump")

st.components.v1.html(html_table, height=650)
