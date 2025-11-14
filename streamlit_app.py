import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Surf & Vær", layout="wide")

# --- Nærmeste hele time ---
now = datetime.now()
start_hour = now.replace(minute=0, second=0, microsecond=0)

def grader_til_kompass(grader):
    retninger = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
                 "S","SSW","SW","WSW","W","WNW","NW","NNW"]
    index = round(grader / 22.5) % 16
    return retninger[index]

# --- Placeholder data for 24 timer ---
hours = [start_hour + timedelta(hours=i) for i in range(24)]
rows = []

for dt in hours:
    rows.append([
        round(2 + dt.hour%3), grader_til_kompass((dt.hour*15)%360), round(6 + dt.hour%5),      # Swell
        round(2 + (dt.hour%3)*0.5), grader_til_kompass((dt.hour*20)%360), round(6 + dt.hour%5), # Vindbølger
        round(4 + dt.hour%12), grader_til_kompass((dt.hour*15)%360),                           # Vind Yr
        round(4 + dt.hour%12), grader_til_kompass((dt.hour*20)%360),                           # Vind DMI
        round(8 + dt.hour%5), round(20 + (dt.hour%5)*15)                                       # Vær
    ])

# --- MultiIndex kolonner ---
arrays = [
    ["Swell", "Swell", "Swell", 
     "Vindbølger", "Vindbølger", "Vindbølger",
     "Vind Yr", "Vind Yr",
     "Vind DMI", "Vind DMI",
     "Vær", "Vær"],
    ["Høyde (m)", "Retning", "Periode (s)",
     "Høyde (m)", "Retning", "Periode (s)",
     "Styrke (m/s)", "Retning",
     "Styrke (m/s)", "Retning",
     "Temp (°C)", "Skydekke (%)"]
]

columns = pd.MultiIndex.from_arrays(arrays)

df = pd.DataFrame(rows, columns=columns)

# --- Layout ---
st.title("Surf & Vær - Placeholder")

# --- Sticky footer ---
footer = """
**Sol opp/ned:** 08:04/17:14 | Surf fra 07:35-17:43 | Sjøtemperatur 12 °C 11. nov
"""
st.markdown(
    f"<div style='position:fixed; bottom:0; width:100%; background-color:black; color:white; padding:10px; font-weight:bold; z-index:999;'>{footer}</div>",
    unsafe_allow_html=True
)

# --- Tabell med scroll ---
st.subheader("Dagens timer")
st.dataframe(df.style.set_properties(**{'text-align': 'center'}), height=400)
