import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Surf & Vær", layout="wide")

# --- Placeholder data ---
hours = [datetime.now() + timedelta(hours=i) for i in range(24)]
data = []

for dt in hours:
    data.append({
        "Tid": dt.strftime("%H:%M"),
        # Hav
        "Swell høyde (m)": round(2 + (dt.hour % 3), 1),
        "Swell retning": f"{(dt.hour*15)%360}°",
        "Swell periode (s)": 6 + (dt.hour % 5),
        "Vindbølger høyde (m)": round(2 + (dt.hour%3)*0.5,1),
        "Vindbølger retning": f"{(dt.hour*20)%360}°",
        "Vindbølger periode (s)": 6 + (dt.hour%5),
        "Dominant periode (s)": 8 + (dt.hour%3),
        "Havtemp (°C)": 12.5,
        # Vind
        "Vind retning Yr": f"{(dt.hour*15)%360}°",
        "Vind styrke Yr (m/s)": 4 + (dt.hour%12),
        "Vind retning DMI": f"{(dt.hour*20)%360}°",
        "Vind styrke DMI (m/s)": 4 + (dt.hour%12),
        # Vær
        "Temp (°C)": 8 + (dt.hour%5),
        "Skydekke (%)": 20 + (dt.hour%5)*15
    })

df = pd.DataFrame(data)

# --- Midnattsskille / daglig overskrift ---
df["Dato"] = df["Tid"].apply(lambda x: datetime.strptime(x,"%H:%M").date())
df["Dag"] = df["Tid"].apply(lambda x: datetime.strptime(x,"%H:%M").strftime("%A %d. %b"))

# --- Layout ---
st.title("Surf & Vær - Placeholder")

# Sticky nederst
footer = """
**Sol opp/ned:** 08:04/17:14  
**Surf fra:** 07:35-17:43  
**Sjøtemperatur:** 12.5 °C 11. nov
"""
st.markdown(f"<div style='position:fixed; bottom:0; width:100%; background-color:#f0f0f0; padding:10px;'>{footer}</div>", unsafe_allow_html=True)

# --- Tabell med scroll ---
st.subheader("Dagens timer")
st.dataframe(df.style.set_properties(**{'text-align': 'center'}), height=300)

# Alternativ: gruppering etter dag
# for dag, group in df.groupby("Dag"):
#     st.subheader(dag)
#     st.dataframe(group.drop(columns=["Dag","Dato"]).style.set_properties(**{'text-align': 'center'}), height=300)
