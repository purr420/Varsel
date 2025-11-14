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
    width: 98%;
    margin: 20px auto 40px auto;
    overflow-x: auto;
    overflow-y: auto;
    max-height: 700px;
    border: 1px solid #333;
}

/* TABLE */
table {
    width: 100%;
    border-collapse: collapse;
    background: black;
    color: white;
    text-align: center;
    table-layout: auto;
}

/* Sticky header */
thead th {
    position: sticky;
    top: 0;
    background: #000;
    padding: 8px 12px;
    z-index: 10;
    border-bottom: 2px solid #444;
    font-size: 0.8rem;
    text-align: center;
}

/* Rows */
td {
    padding: 8px 12px;
    border-bottom: 1px solid #333;
    white-space: nowrap;
}

/* Dag header */
.dayheader {
    font-size: 0.9rem;
    font-weight: normal;
    padding: 16px 0;
    margin-bottom: 8px;
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
    <th>Dønning s</th>
    <th>Dønning retning</th>
    <th>Vindbølger m</th>
    <th>Vindbølger s</th>
    <th>Vindbølger retning</th>
    <th>P.dom.</th>
    <th>yr Vind</th>
    <th>yr Retning</th>
    <th>dmi Vind</th>
    <th>dmi Retning</th>
    <th>Land</th>
    <th>Sjø</th>
    <th>Skydekke</th>
    <th>Nedbør</th>
</tr>
</thead>
<tbody>
<tr><td>16</td><td>1,2 m</td><td>9,6 s</td><td>VSV</td><td>1,2 m</td><td>6 s</td><td>NNV</td><td>9,8 s</td><td>4(7)</td><td>NNV</td><td>4(7)</td><td>V</td><td>10°C</td><td>12°C</td><td>0 %</td><td></td></tr>
<tr><td>17</td><td>1,3 m</td><td>9,3 s</td><td>VSV</td><td>1,0 m</td><td>5 s</td><td>NNV</td><td>9,7 s</td><td>4(8)</td><td>NV</td><td>5(10)</td><td>NNV</td><td>10°C</td><td>12°C</td><td>10 %</td><td></td></tr>
<tr><td>18</td><td>1,2 m</td><td>9,2 s</td><td>SV</td><td>0,9 m</td><td>5 s</td><td>NV</td><td>9,6 s</td><td>6(10)</td><td>V</td><td>11(13)</td><td>NV</td><td>10°C</td><td>12°C</td><td>40 %</td><td></td></tr>
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
    <th>Dønning s</th>
    <th>Dønning retning</th>
    <th>Vindbølger m</th>
    <th>Vindbølger s</th>
    <th>Vindbølger retning</th>
    <th>P.dom.</th>
    <th>yr Vind</th>
    <th>yr Retning</th>
    <th>dmi Vind</th>
    <th>dmi Retning</th>
    <th>Land</th>
    <th>Sjø</th>
    <th>Skydekke</th>
    <th>Nedbør</th>
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

components.html(html, height=1600, scrolling=True)
