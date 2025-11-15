import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz

st.title("Weather Table - Høyde Cell Sticky Behavior Fixed")

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

# Create custom HTML table with sticky functionality
html_table = f"""
<style>
.sticky-table-container {{
    max-height: 600px;
    overflow: auto;
    border: 1px solid #ddd;
    margin: 10px 0;
}}

.sticky-table {{
    width: 100%;
    border-collapse: collapse;
    background: white;
}}

.sticky-table th,
.sticky-table td {{
    border: 1px solid #ddd;
    padding: 8px;
    text-align: center;
    vertical-align: middle;
    min-width: 60px;
    background: #f8f9fa;
}}

/* First header row */
.sticky-table thead tr:first-child th {{
    position: sticky;
    top: 0;
    background: #f8f9fa;
    font-weight: bold;
    z-index: 15;
}}

/* SECOND HEADER ROW - FIXED (affects Høyde and all other cells in row 2) */
.sticky-table thead tr:nth-child(2) th {{
    position: sticky;
    top: 40px;
    background: #f8f9fa;
    font-weight: bold;
    z-index: 16; /* FIX: must be higher than first row (15) */
}}

/* Sticky first column */
.sticky-table td:first-child,
.sticky-table th:first-child {{
    position: sticky;
    left: 0;
    background: #f8f9fa;
    font-weight: bold;
    border-right: 2px solid #999;
    z-index: 20;
}}

/* Tid header - MAX sticky */
.sticky-table thead th:first-child {{
    position: sticky !important;
    top: 0 !important;
    left: 0 !important;
    background: #f8f9fa !important;
    border-right: 2px solid #999;
    z-index: 100 !important;
    font-weight: bold !important;
}}
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
st.write(f"**Høyde cell fixed:** z-index raised to 16 for correct sticky behavior")

st.components.v1.html(html_table, height=650)
