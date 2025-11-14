import streamlit as st

st.set_page_config(layout="wide")
st.markdown("## Varselet")

#---------------- CSS ----------------
st.markdown("""
<style>

.tablewrap {
    margin-bottom: 40px;
    overflow-x: auto;
}

/* Base table */
table {
    width: 100%;
    border-collapse: collapse;
    background: black;
    color: white;
    font-size: 0.9rem;
}

/* ---- STICKY DAY HEADER (first row) ---- */
thead .dayheader th {
    position: sticky;
    top: 0;
    background: #111;
    color: white;
    font-weight: 600;
    padding: 8px 10px;
    z-index: 10;
    border-bottom: 2px solid #444;
}

/* ---- STICKY COLUMN HEADER (second row) ---- */
thead .colheader th {
    position: sticky;
    top: 36px; /* height of dayheader row */
    background: black;
    color: white;
    padding: 6px 10px;
    border-bottom: 2px solid #444;
    z-index: 9;
}

/* Table cells */
td {
    padding: 6px 10px;
    border-bottom: 1px solid #333;
}

/* Sticky first column */
th:first-child,
td:first-child {
    position: sticky;
    left: 0;
    background: black;
    z-index: 11;
    border-right: 2px solid #444;
}

/* Vertical separators */
td:nth-child(4), th:nth-child(4) { border-right: 2px solid #444; }
td:nth-child(6), th:nth-child(6) { border-right: 2px solid #444; }

</style>
""", unsafe_allow_html=True)


#------------- RENDERING FUNCTION -------------
def render_day_table(day_header_text, rows):
    html = f"""
    <div class="tablewrap">
    <table>
        <thead>
            <tr class="dayheader">
                <th colspan="10">{day_header_text}</th>
            </tr>
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
        html += "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"

    html += "</tbody></table></div>"
    st.markdown(html, unsafe_allow_html=True)



#------------- DAG 1 -------------
render_day_table(
    "I dag 14. nov – Første lys 07:52 – Sol opp 08:15 – Sol ned 16:32 – Siste lys 17:01 – Sjøtemp Lindesnes fyr 12,4°C (målt 14. nov)",
    [
        ["16","1,2 m / 9,6 s / VSV","1,2 m / 6 s / NNV","9,8 s","4(7) NNV","4(7) V","10°C","12°C","0 %",""],
        ["17","1,3 m / 9,3 s / VSV","1,0 m / 5 s / NNV","9,7 s","4(8) NV","5(10) NNV","10°C","12°C","10 %",""],
        ["18","1,2 m / 9,2 s / SV","0,9 m / 5 s / NV","9,6 s","6(10) V","11(13) NV","10°C","12°C","40 %",""]
    ]
)


#------------- DAG 2 -------------
render_day_table(
    "I morgen 15. nov – Første lys 07:55 – Sol opp 08:19 – Sol ned 16:29 – Siste lys 16:55",
    [
        ["06","1,2 m / 9,6 s / VSV","1,2 m / 6 s / NNV","9,8 s","4(7) NNV","4(7) V","7°C","12°C","100 %","0,9 mm"],
        ["07","1,3 m / 9,3 s / VSV","1,0 m / 5 s / NNV","9,7 s","4(8) NV","5(10) NNV","7°C","12°C","100 %","1,1 mm"],
        ["08","1,2 m / 9,2 s / SV","0,9 m / 5 s / NV","9,6 s","4(7) NNV","4(7) V","8°C","12°C","100 %","0,3 mm"],
        ["09","1,2 m / 9,6 s / VSV","1,2 m / 6 s / NNV","9,8 s","4(8) NV","5(10) NNV","9°C","12°C","90 %",""],
        ["10","1,2 m / 9,6 s / VSV","1,2 m / 6 s / NNV","9,8 s","4(7) NNV","4(7) V","10°C","12°C","70 %",""],
        ["11","1,3 m / 9,3 s / VSV","1,0 m / 5 s / NNV","9,7 s","4(8) NV","5(10) NNV","11°C","12°C","100 %","0,5 mm"],
        ["12","1,2 m / 9,2 s / SV","0,9 m / 5 s / NV","9,6 s","6(10) V","11(13) NV","11°C","12°C","100 %","0,9 mm"]
    ]
)
