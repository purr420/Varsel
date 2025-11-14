import streamlit as st

st.set_page_config(layout="wide")

st.markdown("## Varselet")

# ——— CSS FOR ALLE TABELLER ———
st.markdown("""
<style>

.tablewrap {
    margin-bottom: 40px;
    overflow-x: auto;
}

/* Base table styling */
table {
    width: 100%;
    border-collapse: collapse;
    background: black;
    color: white;
    font-size: 0.9rem;
}

/* DAY HEADER ROW (sticky row 1) */
.dayheader {
    position: sticky;
    top: 0;
    background: #111;
    color: white;
    font-weight: 600;
    z-index: 5;
    border-bottom: 2px solid #444;
}

/* COLUMN HEADER ROW (sticky row 2) */
.colheader th {
    position: sticky;
    top: 34px; /* height of dayheader row */
    background: black;
    color: white;
    z-index: 6;
    padding: 6px 10px;
    border-bottom: 2px solid #444;
}

/* Standard cell styling */
td {
    padding: 6px 10px;
    border-bottom: 1px solid #333;
}

/* STICKY FIRST COLUMN (header + cells) */
th:first-child,
td:first-child {
    position: sticky;
    left: 0;
    background: black;
    z-index: 7;
    border-right: 2px solid #444;
}

/* Vertical separators */
td:nth-child(4), th:nth-child(4) { border-right: 2px solid #444; }
td:nth-child(6), th:nth-child(6) { border-right: 2px solid #444; }

</style>
""", unsafe_allow_html=True)



# ——— TABLE GENERATOR FUNCTION ———

def make_table(day_header, rows):
    html = """
    <div class="tablewrap">
    <table>
    <thead>
        <tr class="dayheader"><td colspan="10">""" + day_header + """</td></tr>

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
    """
    for r in rows:
        html += "<tr>"
        for c in r:
            html += f"<td>{c}</td>"
        html += "</tr>"

    html += "</tbody></table></div>"
    return html



# ——— TABLE 1: I DAG ———

today_header = (
"I dag 14. nov – Første lys 07:52 – Sol opp 08:15 – Sol ned 16:32 – "
"Siste lys 17:01 – Sjøtemp Lindesnes fyr 12,4°C (målt 14. nov)"
)

today_rows = [
    ["16", "1,2 m / 9,6 s / VSV", "1,2 m / 6 s / NNV", "9,8 s", "4(7) NNV", "4(7) V", "10°C", "12°C", "0 %", ""],
    ["17", "1,3 m / 9,3 s / VSV", "1,0 m / 5 s / NNV", "9,7 s", "4(8) NV", "5(10) NNV", "10°C", "12°C", "10 %", ""],
    ["18", "1,2 m / 9,2 s / SV",  "0,9 m / 5 s / NV",  "9,6 s", "6(10) V", "11(13) NV", "10°C", "12°C", "40 %", ""],
]

st.markdown(make_table(today_header, today_rows), unsafe_allow_html=True)



# ——— TABLE 2: I MORGEN ———

tomorrow_header = (
"I morgen 15. nov – Første lys 07:55 – Sol opp 08:19 – Sol ned 16:29 – "
"Siste lys 16:55"
)

tomorrow_rows = [
    ["06", "1,2 m / 9,6 s / VSV", "1,2 m / 6 s / NNV", "9,8 s", "4(7) NNV", "4(7) V", "7°C", "12°C", "100 %", "0,9 mm"],
    ["07", "1,3 m / 9,3 s / VSV", "1,0 m / 5 s / NNV", "9,7 s", "4(8) NV", "5(10) NNV", "7°C", "12°C", "100 %", "1,1 mm"],
    ["08", "1,2 m / 9,2 s / SV",  "0,9 m / 5 s / NV",  "9,6 s", "4(7) NNV", "4(7) V", "8°C", "12°C", "100 %", "0,3 mm"],
    ["09", "1,2 m / 9,6 s / VSV", "1,2 m / 6 s / NNV", "9,8 s", "4(8) NV", "5(10) NNV", "9°C", "12°C", "90 %", ""],
    ["10", "1,2 m / 9,6 s / VSV", "1,2 m / 6 s / NNV", "9,8 s", "4(7) NNV", "4(7) V", "10°C", "12°C", "70 %", ""],
    ["11", "1,3 m / 9,3 s / VSV", "1,0 m / 5 s / NNV", "9,7 s", "4(8) NV", "5(10) NNV", "11°C", "12°C", "100 %", "0,5 mm"],
    ["12", "1,2 m / 9,2 s / SV",  "0,9 m / 5 s / NV",  "9,6 s", "6(10) V", "11(13) NV", "11°C", "12°C", "100 %", "0,9 mm"],
]

st.markdown(make_table(tomorrow_header, tomorrow_rows), unsafe_allow_html=True)
