import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Surf & Vær", layout="wide")

# --- Nærmeste hele time ---
now = datetime.now()
start_hour = now.replace(minute=0, second=0, microsecond=0)

# --- Funksjon for kompassretning ---
def grader_til_kompass(grader):
    retninger = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
                 "S","SSW","SW","WSW","W","WNW","NW","NNW"]
    index = round(grader / 22.5) % 16
    return retninger[index]

# --- Placeholder data for 24 timer ---
hours = [start_hour + timedelta(hours=i) for i in range(24)]
data = []

for dt in hours:
    swell_h = round(2 + dt.hour%3)
    swell_r = grader_til_kompass((dt.hour*15)%360)
    swell_p = round(6 + dt.hour%5)
    
    vindb_h = round(2 + (dt.hour%3)*0.5)
    vindb_r = grader_til_kompass((dt.hour*20)%360)
    vindb_p = round(6 + dt.hour%5)
    
    vind_yr_s = round(4 + dt.hour%12)
    vind_yr_r = grader_til_kompass((dt.hour*15)%360)
    
    vind_dmi_s = round(4 + dt.hour%12)
    vind_dmi_r = grader_til_kompass((dt.hour*20)%360)
    
    temp = round(8 + dt.hour%5)
    sky = round(20 + (dt.hour%5)*15)
    
    data.append({
        # Swell
        "Swell Høyde (m)": swell_h,
        "Swell Retning": swell_r,
        "Swell Periode (s)": swell_p,
        # Vindbølger
        "Vindb Høyde (m)": round(vindb_h),
        "Vindb Retning": vindb_r,
        "Vindb Periode (s)": vindb_p,
        # Vind Yr
        "Vind Yr Styrke (m/s)": vind_yr_s,
        "Vind Yr Retning": vind_yr_r,
        # Vind DMI
        "Vind DMI Styrke (m/s)": vind_dmi_s,
        "Vind DMI Retning": vind_dmi_r,
        # Vær
        "Temp (°C)": temp,
        "Skydekke (%)": sky
    })

df = pd.DataFrame(data)

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

# --- Kolonnegrupper (etasjer) ---
st.subheader("Dagens timer")
st.markdown("**Swell**")
st.dataframe(df[["Swell Høyde (m)", "Swell Retning", "Swell Periode (s)"]].style.set_properties(**{'text-align': 'center'}), height=150)

st.markdown("**Vindbølger**")
st.dataframe(df[["Vindb Høyde (m)", "Vindb Retning", "Vindb Periode (s)"]].style.set_properties(**{'text-align': 'center'}), height=150)

st.markdown("**Vind Yr**")
st.dataframe(df[["Vind Yr Styrke (m/s)", "Vind Yr Retning"]].style.set_properties(**{'text-align': 'center'}), height=100)

st.markdown("**Vind DMI**")
st.dataframe(df[["Vind DMI Styrke (m/s)", "Vind DMI Retning"]].style.set_properties(**{'text-align': 'center'}), height=100)

st.markdown("**Vær**")
st.dataframe(df[["Temp (°C)", "Skydekke (%)"]].style.set_properties(**{'text-align': 'center'}), height=100)
