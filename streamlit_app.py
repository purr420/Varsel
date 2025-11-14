import streamlit as st
import streamlit.components.v1 as components

html = """
<style>
body {
    background: black;
    color: white;
    font-family: sans-serif;
    margin:0;
    padding:0;
}

.tablewrap {
    width: 100%;
    overflow-x: auto;
    border: 1px solid #333;
}

/* TABLE */
table {
    width: 100%;
    border-collapse: collapse;
    background: black;
    color: white;
    text-align: center;
}

/* Sticky header */
thead th {
    position: sticky;
    top: 0;
    background: #000;
    padding: 6px 10px;
    z-index: 10;
    border-bottom: 2px solid #444;
}

/* Sticky first column */
td:first-child, th:first-child {
    position: sticky;
    left: 0;
    background: #000;
    z-index: 20;
    border-right: 2px solid #444;
}

/* Rows */
td {
    padding: 6px 10px;
    border-bottom: 1px solid #333;
    text-align: center;
    white-space: nowrap;
}

.dayheader {
    font-size: 0.9rem;
    font-weight: normal;
    padding: 4px 0;
    color: white;
}
</style>

<!-- ===================== I DAG ===================== -->
<div class="dayheader">
I dag 14. nov – Første lys 07:52 – Sol opp 08:15 – Sol ned 16:32 – Siste lys 17:01 – Sjøtemp Lindesnes fyr 12,4°C
</div>

<div class="tablewrap">
<table>
<thead>
<tr>
    <th rowspan="2">Tid</th>
    <th colspan="3">Dønning</th>
    <th colspan="3">Vindbølger</th>
    <th rowspan="2">P.dom.</th>
    <th colspan="2">yr Vind(kast) m/s</th>
    <th colspan="2">dmi Vind(kast) m/s</th>
    <th rowspan="2">Land</th>
    <th rowspan="2">Sjø</th>
    <th rowspan="2">Skydekke</th>
    <th rowspan="2">Nedbør</th>
</tr>
<tr>
    <th>m</th><th>s</th><th>retning</th>
    <th>m</th><th>s</th><th>retning</th>
    <th>Vind</th><th>Kast</th>
    <th>Vind</th><th>Kast</th>
</tr>
</thead>

<tbody>
<tr><td>16</td><td>1,2 m</td><td>9,6 s</td><td>VSV</td><td>1,2 m</td><td>6 s</td><td>NNV</td><td>9,8 s</td><td>4(7)</td><td>NNV</td><td>4(7)</td><td>V</td><td>10°C</td><td>12°C</td><td>0 %</td><td></td></tr>
<tr><td>17</td><td>1,3 m</td><td>9,3 s</td><td>VSV</td><td>1,0 m</td><td>5 s</td><td>NNV</td><td>9,7 s</td><td>4(8)</td><td>NV</td><td>5(10)</td><td>NNV</td><td>10°C</td><td>12°C</td><td>10 %</td><td></td></tr>
<tr><td>18</td><td>1,2 m</td><td>9,2 s</td><td>SV</td><td>0,9 m</td><td>5 s</td><td>NV</td><td>9,6 s</td><td>6(10)</td><td>V</td><td>11(13)</td><td>NV</td><td>10°C</td><td>12°C</td><td>40 %</td><td></td></tr>
</tbody>
</table>
</div>

<!-- ===================== I MORGEN ===================== -->
<div class="dayheader">
I morgen 15. nov – Første lys 07:55 – Sol opp 08:19 – Sol ned 16:29 – Siste lys 16:55
</div>

<div class="tablewrap">
<table>
<thead>
<tr>
    <th rowspan="2">Tid</th>
    <th colspan="3">Dønning</th>
    <th colspan="3">Vindbølger</th>
    <th rowspan="2">P.dom.</th>
    <th colspan="2">yr Vind(kast) m/s</th>
    <th colspan="2">dmi Vind(kast) m/s</th>
    <th rowspan="2">Land</th>
    <th rowspan="2">Sjø</th>
    <th rowspan="2">Skydekke</th>
    <th rowspan="2">Nedbør</th>
</tr>
<tr>
    <th>m</th><th>s</th><th>retning</th>
    <th>m</th><th>s</th><th>retning</th>
    <th>Vind</th><th>Kast</th>
    <th>Vind</th><th>Kast</th>
</tr>
</thead>

<tbody>
<tr><td>06</td><td>1,2 m</td><td>9,6 s</td><td>VSV</td><td>1,2 m</td><td>6 s</td><td>NNV</td><td>9,8 s</td><td>4(7)</td><td>NNV</td><td>4(7)</td><td>V</td><td>7°C</td><td>12°C</td><td>100 %</td><td>0,9 mm</td></tr>
<tr><td>07</td><td>1,3 m</td><td>9,3 s</td><td>VSV</td><td>1,0 m</td><td>5 s</td><td>NNV</td><td>9,7 s</td><td>4(8)</td><td>NV</td><td>5(10)</td><td>NNV</td><td>7°C</td><td>12°C</td><td>100 %</td><td>1,1 mm</td></tr>
<tr><td>08</td><td>1,2 m</td><td>9,2 s</td><td>SV</td><td>0,9 m</td><td>5 s</td><td>NV</td><td>9,6 s</td><td>4(7)</td><td>NNV</td><td>4(7)</td><td>V</td><td>8°C</td><td>12°C</td><td>100 %</td><td>0,3 mm</td></tr>
<tr><td>09</td><td>1,2 m</td><td>9,6 s</td><td>VSV</td><td>1,2 m</td><td>6 s</td><td>NNV</td><td>9,8 s</td><td>4(8)</td><td>NV</td><td>5(10)</td><td>NNV</td><td>9°C</td><td>12°C</td><td>90 %</td><td></td></tr>
<tr><td>10</td><td>1,2 m</td><td>9,6 s</td><td>VSV</td><td>1,2 m</td><td>6 s</td><td>NNV</td><td>9,8 s</td><td>4(7)</td><td>NNV</td><td>4(7)</td><td>V</td><td>10°C</td><td>12°C</td><td>70 %</td><td></td></tr>
<tr><td>11</td><td>1,3 m</td><td>9,3 s</td><td>VSV</td><td>1,0 m</td><td>5 s</td><td>NNV</td><td>9,7 s</td><td>4(8)</td><td>NV</td><td>5(10)</td><td>NNV</td><td>11°C</td><td>12°C</td><td>100 %</td><td>0,5 mm</td></tr>
<tr><td>12</td><td>1,2 m</td><td>9,2 s</td><td>SV</td><td>0,9 m</td><td>5 s</td><td>NV</td><td>9,6 s</td><td>6(10)</td><td>V</td><td>11(13)</td><td>NV</td><td>11°C</td><td>12°C</td><td>100 %</td><td>0,9 mm</td></tr>
</tbody>
</table>
</div>
"""

components.html(html, height=1400, scrolling=True)
