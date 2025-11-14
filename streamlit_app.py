import streamlit as st

st.markdown("""
<style>

.tablewrap {
    margin-bottom: 40px;
    overflow-x: auto;
    position: relative;
}

/* Base table */
table {
    width: 100%;
    border-collapse: collapse;
    background: black;
    color: white;
    font-size: 0.9rem;
}

/* --- Sticky header row --- */
thead tr.colheader th {
    position: sticky !important;
    top: 0 !important;
    background: #000 !important;
    z-index: 50 !important;
    padding: 8px 10px;
    border-bottom: 2px solid #444;
}

/* Sticky first column */
td:first-child,
th:first-child {
    position: sticky !important;
    left: 0 !important;
    background: #000 !important;
    z-index: 60 !important;
    border-right: 2px solid #444;
}

/* Table cells */
td {
    padding: 6px 10px;
    border-bottom: 1px solid #333;
}

.dayheader {
    font-size: 1rem;
    font-weight: bold;
    padding: 10px 0;
    color: white;
    background: black;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------
#       DAG 1
# ---------------------------

st.markdown('<div class="dayheader">I dag 14. nov – Første lys 07:52 – Sol opp 08:15 – Sol ned 16:32 – Siste lys 17:01 – Sjøtemp Lindesnes fyr 12,4°C (målt 14. nov)</div>', unsafe_allow_html=True)

st.markdown("""
<div class="tablewrap">
<table>
    <thead>
        <tr class="colheader">
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
        <tr>
            <td>16</td><td>1,2 m / 9,6 s / VSV</td><td>1,2 m / 6 s / NNV</td><td>9,8 s</td><td>4(7) NNV</td><td>4(7) V</td><td>10°C</td><td>12°C</td><td>0 %</td><td></td>
        </tr>
        <tr>
            <td>17</td><td>1,3 m / 9,3 s / VSV</td><td>1,0 m / 5 s / NNV</td><td>9,7 s</td><td>4(8) NV</td><td>5(10) NNV</td><td>10°C</td><td>12°C</td><td>10 %</td><td></td>
        </tr>
        <tr>
            <td>18</td><td>1,2 m / 9,2 s / SV</td><td>0,9 m / 5 s / NV</td><td>9,6 s</td><td>6(10) V</td><td>11(13) NV</td><td>10°C</td><td>12°C</td><td>40 %</td><td></td>
        </tr>
    </tbody>
</table>
</div>
""", unsafe_allow_html=True)



# ---------------------------
#       DAG 2
# ---------------------------

st.markdown('<div class="dayheader">I morgen 15. nov – Første lys 07:55 – Sol opp 08:19 – Sol ned 16:29 – Siste lys 16:55</div>', unsafe_allow_html=True)

st.markdown("""
<div class="tablewrap">
<table>
    <thead>
        <tr class="colheader">
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
        <tr>
            <td>06</td><td>1,2 m / 9,6 s / VSV</td><td>1,2 m / 6 s / NNV</td><td>9,8 s</td><td>4(7) NNV</td><td>4(7) V</td><td>7°C</td><td>12°C</td><td>100 %</td><td>0,9 mm</td>
        </tr>
        <tr>
            <td>07</td><td>1,3 m / 9,3 s / VSV</td><td>1,0 m / 5 s / NNV</td><td>9,7 s</td><td>4(8) NV</td><td>5(10) NNV</td><td>7°C</td><td>12°C</td><td>100 %</td><td>1,1 mm</td>
        </tr>
        <tr>
            <td>08</td><td>1,2 m / 9,2 s / SV</td><td>0,9 m / 5 s / NV</td><td>9,6 s</td><td>4(7) NNV</td><td>4(7) V</td><td>8°C</td><td>12°C</td><td>100 %</td><td>0,3 mm</td>
        </tr>
        <tr>
            <td>09</td><td>1,2 m / 9,6 s / VSV</td><td>1,2 m / 6 s / NNV</td><td>9,8 s</td><td>4(8) NV</td><td>5(10) NNV</td><td>9°C</td><td>12°C</td><td>90 %</td><td></td>
        </tr>
        <tr>
            <td>10</td><td>1,2 m / 9,6 s / VSV</td><td>1,2 m / 6 s / NNV</td><td>9,8 s</td><td>4(7) NNV</td><td>4(7) V</td><td>10°C</td><td>12°C</td><td>70 %</td><td></td>
        </tr>
        <tr>
            <td>11</td><td>1,3 m / 9,3 s / VSV</td><td>1,0 m / 5 s / NNV</td><td>9,7 s</td><td>4(8) NV</td><td>5(10) NNV</td><td>11°C</td><td>12°C</td><td>100 %</td><td>0,5 mm</td>
        </tr>
        <tr>
            <td>12</td><td>1,2 m / 9,2 s / SV</td><td>0,9 m / 5 s / NV</td><td>9,6 s</td><td>6(10) V</td><td>11(13) NV</td><td>11°C</td><td>12°C</td><td>100 %</td><td>0,9 mm</td>
        </tr>
    </tbody>
</table>
</div>
""", unsafe_allow_html=True)
