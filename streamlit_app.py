import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

st.title("Weather Table - Sticky Headers + Fixed Høyde Behavior")

# Get current Oslo time
oslo_tz = pytz.timezone('Europe/Oslo')
current_time = datetime.now(oslo_tz)
current_hour = current_time.hour

# Start 2 hours before current hour
start_hour = (current_hour - 2) % 24

# Build data rows
data = []
for i in range(24):
    hour = (start_hour + i) % 24
    row = [f"{hour:02d}"] + ["-"] * 15
    data.append(row)

# ---------------------------------------------
# HTML + CSS TABLE
# ---------------------------------------------
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

/* Make all header cells sticky */
.sticky-table thead th {{
    position: sticky;
    background: #f8f9fa;
    font-weight: bold;
    z-index: 10;
}}

/* First header row sticks at top */
.sticky-table thead tr:first-child th {{
    top: 0;
}}

/* Second header row sticks under first */
.sticky-table thead tr:nth-child(2) th {{
    top: 40px;
}}

/* Sticky first column for ALL rows */
.sticky-table td:first-child,
.sticky-table th:first-child {{
    position: sticky;
    left: 0;
    background: #f8f9fa;
    font-weight: bold;
    border-right: 2px solid #999;
    z-index: 20;
}}

/* FIX 1: Only the top-left corner gets highest z-index */
.sticky-table thead tr:first-child th:first-child {{
    z-index: 30 !important;
}}

/* FIX 2: Prevent "Høyde" from acting like the corner sticky */
.sticky-table thead tr:nth-child(2) th:first-child {{
    left: auto !important;
    z-index: 12 !important;
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

# Add data rows
for row in data:
    html_table += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"

html_table += """
</tbody>
</table>
</div>
"""

# Display debug info
st.write(
    f"**Oslo time:** {current_time.strftime('%H:%M')} — "
    f"{current_time.strftime('%A %d.%m')}"
)
st.write(f"**Start hour:** {start_hour:02d}")

# Render table
st.components.v1.html(html_table, height=650)
