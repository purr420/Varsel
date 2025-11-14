import streamlit as st
import streamlit.components.v1 as components

html = """
<style>

body {
    background: black;
    color: white;
    font-family: sans-serif;
}

/* Wrapper */
.tablewrap {
    max-height: 600px;
    overflow-y: auto;
    overflow-x: auto;
    border: 1px solid #333;
}

/* TABLE */
table {
    width: 100%;
    border-collapse: collapse;
    background: black;
    color: white;
}

/* Sticky column header */
thead tr th {
    position: sticky;
    top: 0;
    background: #000;
    padding: 8px;
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
}

/* Day header, NOT sticky */
.dayheader {
    font-size: 1.1rem;
    font-weight: bold;
    padding: 10px 0;
    margin-top: 20px;
    color: white;
}

</style>

<div class="dayheader">
I dag 14. nov – Første lys 07:52 – Sol opp 08:15 – Sol ned 16:32 – Siste lys 17:01 – Sjøtemp Lindesnes fyr 12,4°C
</div>

<div class="tablewrap">
<table>
<thead>
<tr>
    <th>Tid</th>
    <th>Dønning</th>
    <th>Vindbølger</th>
    <th>P.dom.</th>
    <th>yr Vind(kast) m/s</th>
    <th>dmi Vind(kast) m/s</th>
    <th>Land</th>
    <th>Sjø</th>
    <th>Skydekke</th>
    <th>Nedbør</th>
</tr>
</thead>

<tbody>
<tr><td>16</td><td>1,2 m / 9,6 s / VSV</td><td>1,2 m / 6 s / NNV</td><td>9,8 s</td><td>4(7) NNV</td><td>4(7) V</td><td>10°C</td><td>12°C</td><td>0 %</td><td></td></tr>
<tr><td>17</td><td>1,3 m / 9,3 s / VSV</td><td>1,0 m / 5 s / NNV</td><td>9,7 s</td><td>4(8) NV</td><td>5(10) NNV</td><td>10°C</td><td>12°C</td><td>10 %</td><td></td></tr>
<tr><td>18</td><td>1,2 m / 9,2 s / SV</td><td>0,9 m / 5 s / NV</td><td>9,6 s</td><td>6(10) V</td><td>11(13) NV</td><td>10°C</td><td>12°C</td><td>40 %</td><td></td></tr>
</tbody>
</table>
</div>


<div class="dayheader">
I morgen 15. nov – Første lys 07:55 – Sol opp 08:19 – Sol ned 16:29 – Siste lys 16:55
</div>

<div class="tablewrap">
<table>
<thead>
<tr>
    <th>Tid</th>
    <th>Dønning</th>
    <th>Vindbølger</th>
    <th>P.dom.</th>
    <th>yr Vind(kast) m/s</th>
    <th>dmi Vind(kast) m/s</th>
    <th>Land</th>
    <th>Sjø</th>
    <th>Skydekke</th>
    <th>Nedbør</th>
</tr>
</thead>

<tbody>
<tr><td>06</td><td>1,2 m / 9,6 s / VSV</td><td>1,2 m / 6 s / NNV</td><td>9,8 s</td><td>4(7) NNV</td><td>4(7) V</td><td>7°C</td><td>12°C</td><td>100 %</td><td>0,9 mm</td></tr>
<tr><td>07</td><td>1,3 m / 9,3 s / VSV</td><td>1,0 m / 5 s / NNV</td><td>9,7 s</td><td>4(8) NV</td><td>5(10) NNV</td><td>7°C</td><td>12°C</td><td>100 %</td><td>1,1 mm</td></tr>
<tr><td>08</td><td>1,2 m / 9,2 s / SV</td><td>0,9 m / 5 s / NV</td><td>9,6 s</td><td>4(7) NNV</td><td>4(7) V</td><td>8°C</td><td>12°C</td><td>100 %</td><td>0,3 mm</td></tr>
</tbody>

</table>
</div>
"""

components.html(html, height=900, scrolling=True)
