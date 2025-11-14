import streamlit as st
import streamlit.components.v1 as components

html = """
<style>

body {
    background: black;
    color: white;
    font-family: sans-serif;
}

.tablewrap {
    max-height: 800px;      /* Viktig! Ellers fungerer ikke sticky */
    overflow-y: scroll;
    overflow-x: auto;
    border: 1px solid #333;
}

/* Basic table layout */
table {
    width: 100%;
    border-collapse: collapse;
    background: black;
    color: white;
    table-layout: fixed;     /* Hindrer kuttede rader */
}

/* ---------- STICKY HEADER (FUNGERER 100%) ---------- */
thead th {
    position: sticky;
    top: 0;
    background: #000;
    z-index: 1000;           /* Viktig! Høyere enn sticky venstre kolonne */
    padding: 8px;
    border-bottom: 2px solid #444;
}

/* ---------- STICKY FØRSTE KOLONNE ---------- */
td:first-child,
th:first-child {
    position: sticky;
    left: 0;
    background: #000;
    z-index: 1500;           /* Må være høyere enn headeren */
    border-right: 2px solid #444;
    padding-left: 10px;
}

/* Cell styling */
td {
    padding: 6px 10px;
    border-bottom: 1px solid #333;
}

.dayheader {
    font-size: 1rem;
    font-weight: bold;
    padding: 12px 0;
    color: white;
}

</style>


<!-- ================= DAG 1 ================= -->

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


<!-- ================= DAG 2 ================= -->

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
<tr><td>09</td><td>1,2 m / 9,6 s / VSV</td><td>1,2 m / 6 s / NNV</td><td>9,8 s</td><td>4(8) NV</td><td>5(10) NNV</td><td>9°C</td><td>12°C</td><td>90 %</td><td></td></tr>
<tr><td>10</td><td>1,2 m / 9,6 s / VSV</td><td>1,2 m / 6 s / NNV</td><td>9,8 s</td><td>4(7) NNV</td><td>4(7) V</td><td>10°C</td><td>12°C</td><td>70 %</td><td></td></tr>
<tr><td>11</td><td>1,3 m / 9,3 s / VSV</td><td>1,0 m / 5 s / NNV</td><td>9,7 s</td><td>4(8) NV</td><td>5(10) NNV</td><td>11°C</td><td>12°C</td><td>100 %</td><td>0,5 mm</td></tr>
<tr><td>12</td><td>1,2 m / 9,2 s / SV</td><td>0,9 m / 5 s / NV</td><td>9,6 s</td><td>6(10) V</td><td>11(13) NV</td><td>11°C</td><td>12°C</td><td>100 %</td><td>0,9 mm</td></tr>
</tbody>
</table>
</div>
"""

components.html(html, height=1200, scrolling=True)
