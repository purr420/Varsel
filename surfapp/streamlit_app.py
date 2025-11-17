import streamlit as st
from datetime import datetime
from modules.daylight import get_light_times, load_daylight_table

st.set_page_config(layout="wide")

# ---- Last inn tabellen én gang ----
DAYLIGHT_TABLE = load_daylight_table()

# ---- Nåtid i OSLO ----
now = datetime.now()  # du legger inn timezone senere

# ---- Dummy skydekke (du henter fra API senere) ----
cloud_cover = None  # None = antas 50%

# ---- Hent lys ----
light = get_light_times(now, cloud_cover, DAYLIGHT_TABLE)

first_light = light["first_light"]
last_light = light["last_light"]

# ---- UI HEADER ----

st.markdown(f"""
# Varselet  
### for Lista

<small>Oppdatert {now.strftime("%H:%M %d.%m")}</small>

---

**Første lys:** {first_light}  
**Siste lys:** {last_light}

""", unsafe_allow_html=True)
