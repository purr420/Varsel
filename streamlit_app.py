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
    max-height: 600px;
    overflow-y: auto;
    overflow-x: auto;
    border: 1px solid #333;
}

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

td {
    padding: 6px 10px;
    border-bottom: 1px solid #333;
    text-align: center;
}

.dayheader {
    font-size: 1.1rem;
    font-weight: bold;
    padding: 10px 0;
    margin-top: 20px;
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
    <th>Tid</th>
    <th>Dønning H</th><th>Dønning P</th><th>Dønning R</th>
    <th>Vindbølger H</th><th>Vindbølger P</th><th>Vindbølger R</th>
    <th>P.dom.</th>
    <th>yr Vind (m/s)</th><th>yr Retning</th>
    <th>dmi Vind (m/s)</th><th>dmi Retning</th>
    <th>Land</th><th>Sjø</th><th>Skydekke</th><th>Nedbør</th>
</tr>
</thead>

<tbody>
<tr><td>16</td><td>1,2</td><td>9,6</td><td>VSV</td><td>1,2</td><td>6</td><td>NNV</td><td>4,7</td><td>4</td><td>NNV</td><td>4</td><td>V</td><td>10°C</td><td>12°C</td><td>0 %</td><td></td></tr>
<tr><td>17</td><td>1,3</td><td>9,3</td><td>VSV</td><td>1,0</td><td>5</td><td>NNV</td><td>4,8</td><td>5</td><td>NNV</td><td>5</td><td>V</td><td>10°C</td><td>12°C</td><td>10 %</td><td></td></tr>
<tr><td>18</td><td>1,2</td><td>9,2</td><td>SV</td><td>0,9</td><td>5</td><td>NV</td><td>6,10</td><td>11</td><td>NV</td><td>11</td><td>V</td><td>10°C</td><td>12°C</td><td>40 %</td><td></td></tr>
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
    <th>Tid</th>
    <th>Dønning H</th><th>Dønning P</th><th>Dønning R</th>
    <th>Vindbølger H</th><th>Vindbølger P</th><th>Vindbølger R</th>
    <th>P.dom.</th>
    <th>yr Vind (m/s)</th><th>yr Retning</th>
    <th>dmi Vind (m/s)</th><th>dmi Retning</th>
    <th>Land</th><th>Sjø</th><th>Skydekke</th><th>Nedbør</th>
</tr>
</thead>

<tbody>
<tr><td>06</td><td>1,2</td><td>9,6</td><td>VSV</td><td>1,2</td><td>6</td><td>NNV</td><td>4,7</td><td>4</td><td>NNV</td><td>4</td><td>V</td><td>7°C</td><td>12°C</td><td>100 %</td><td>0,9 mm</td></tr>
<tr><td>07</td><td>1,3</td><td>9,3</td><td>VSV</td><td>1,0</td><td>5</td><td>NNV</td><td>4,8</td><td>5</td><td>NNV</td><td>5</td><td>V</td><td>7°C</td><td>12°C</td><td>100 %</td><td>1,1 mm</td></tr>
<tr><td>08</td><td>1,2</td><td>9,2</td><td>SV</td><td>0,9</td><td>5</td><td>NV</td><td>4,7</td><td>4</td><td>NNV</td><td>4</td><td>V</td><td>8°C</td><td>12°C</td><td>100 %</td><td>0,3 mm</td></tr>
<tr><td>09</td><td>1,2</td><td>9,6</td><td>VSV</td><td>1,2</td><td>6</td><td>NNV</td><td>4,8</td><td>5</td><td>NNV</td><td>5</td><td>V</td><td>9°C</td><td>12°C</td><td>90 %</td><td></td></tr>
<tr><td>10</td><td>1,2</td><td>9,6</td><td>VSV</td><td>1,2</td><td>6</td><td>NNV</td><td>4,7</td><td>4</td><td>NNV</td><td>4</td><td>V</td><td>10°C</td><td>12°C</td><td>70 %</td><td></td></tr>
<tr><td>11</td><td>1,3</td><td>9,3</td><td>VSV</td><td>1,0</td><td>5</td><td>NNV</td><td>4,8</td><td>5</td><td>NNV</td><td>5</td><td>V</td><td>11°C</td><td>12°C</td><td>100 %</td><td>0,5 mm</td></tr>
<tr><td>12</td><td>1,2</td><td>9,2</td><td>SV</td><td>0,9</td><td>5</td><td>NV</td><td>6,10</td><td>11</td><td>NV</td><td>11</td><td>V</td><td>11°C</td><td>12°C</td><td>100 %</td><td>0,9 mm</td></tr>
</tbody>
</table>
</div>
"""

components.html(html, height=1200, scrolling=True)
