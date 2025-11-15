import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz

st.title("Custom HTML Table with Time-Based Rows")

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

# Add tomorrow's date row
tomorrow = current_time + timedelta(days=1)
tomorrow_str = tomorrow.strftime("%A %d. %b")  # e.g., "Monday 16. nov"

# Add the tomorrow row (will be handled specially in HTML)
tomorrow_row_data = [tomorrow_str] + ["-"] * 15
data.append(tomorrow_row_data)

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
    min-width: 60px;
}}

/* Sticky header */
.sticky-table thead th {{
    position: sticky;
    top: 0;
    background: #f8f9fa;
    z-index: 10;
    font-weight: bold;
}}

/* Sticky first column */
.sticky-table td:first-child,
.sticky-table th:first-child {{
    position: sticky;
    left: 0;
    background: #f8f9fa;
    z-index: 20;
    font-weight: bold;
}}

/* Corner cell (header + first column) */
.sticky-table thead th:first-child {{
    z-index: 30;
    background: #e9ecef;
}}

/* Tomorrow row styling */
.tomorrow-row {{
    background: #e3f2fd !important;
    font-weight: bold;
}}

.tomorrow-row td {{
    background: #e3f2fd !important;
    text-align: left;
    padding: 12px;
}}
</style>

<div class="sticky-table-container">
<table class="sticky-table">
<thead>
<tr>
"""

# Add header row
for col in columns:
    html_table += f"<th>{col}</th>"

html_table += """
</tr>
</thead>
<tbody>
"""

# Add time rows (all but the last row which is tomorrow)
for i, row in enumerate(data[:-1]):
    html_table += "<tr>"
    for j, cell in enumerate(row):
        html_table += f"<td>{cell}</td>"
    html_table += "</tr>"

# Add tomorrow row with merged cells
html_table += f"""
<tr class="tomorrow-row">
    <td colspan="16">{tomorrow_str}</td>
</tr>
"""

html_table += """
</tbody>
</table>
</div>
"""

# Display some info about the current setup
st.write(f"**Current Oslo time:** {current_time.strftime('%H:%M')} on {current_time.strftime('%A %d. %b')}")
st.write(f"**Time range:** Starting from {start_hour:02d}:00 (2 hours before current hour)")
st.write(f"**Tomorrow:** {tomorrow_str}")

st.components.v1.html(html_table, height=650)
