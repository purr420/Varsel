import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.markdown("## Varselet")

# --- Placeholder data ---
data_idag = [
    ["16", "1,2 m / 9,6 s / VSV", "1,2 m / 6 s / NNV", "9,8 s",
     "4(7) NNV", "4(7) V", "10°C", "12°C", "0 %", ""],
    ["17", "1,3 m / 9,3 s / VSV", "1,0 m / 5 s / NNV", "9,7 s",
     "4(8) NV", "5(10) NNV", "10°C", "12°C", "10 %", ""],
    ["18", "1,2 m / 9,2 s / SV", "0,9 m / 5 s / NV", "9,6 s",
     "6(10) V", "11(13) NV", "10°C", "12°C", "40 %", ""],
]

columns = [
    "Tid", "Dønning", "Vindbølger", "P.dom.",
    "yr Vind(kast) m/s", "dmi Vind(kast) m/s",
    "Land", "Sjø", "Skydekke", "Nedbør"
]

df_idag = pd.DataFrame(data_idag, columns=columns)

# --- Custom CSS for sticky columns + gridlines ---
st.markdown("""
<style>
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
}

thead th {
    position: sticky;
    top: 0;
    background: #ffffff;
    z-index: 3;
    border-bottom: 2px solid #ccc;
}

tbody td, thead th {
    padding: 6px 10px;
    border-bottom: 1px solid #eee;
}

/* Sticky first column */
tbody td:first-child,
thead th:first-child {
    position: sticky;
    left: 0;
    background: #ffffff;
    z-index: 2;
    border-right: 2px solid #ccc;
}

/* Vertical lines after Tid, P.dom., dmi Vind(kast) */
tbody td:nth-child(1),
thead th:nth-child(1) {
    border-right: 2px solid #ccc;
}

tbody td:nth-child(4),
thead th:nth-child(4) {
    border-right: 2px solid #ccc;
}

tbody td:nth-child(6),
thead th:nth-child(6) {
    border-right: 2px solid #ccc;
}

</style>
""", unsafe_allow_html=True)


# Wrapper div so Streamlit doesn't override the sticky formatting
st.markdown("<div style='overflow-x: auto;'>", unsafe_allow_html=True)
st.write(df_idag.to_html(escape=False, index=False), unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
