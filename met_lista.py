#!/usr/bin/env python3
"""
Script: met_lista_temperature.py
Beskrivelse: Henter kun havtemperatur fra MET Oceanforecast API for Lista fyr.
Forfatter: Petter
User-Agent: post@kurios.no (krav fra MET)
"""

import requests
from datetime import datetime

# Koordinater for Lista fyr
lat = 58.09
lon = 6.52

# MET Oceanforecast API URL
url = f"https://api.met.no/weatherapi/oceanforecast/2.0/complete?lat={lat}&lon={lon}"

headers = {
    "User-Agent": "post@kurios.no"
}

try:
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()
except requests.exceptions.RequestException as e:
    print("❌ Feil ved API-kall:", e)
    exit(1)
except ValueError as e:
    print("❌ Kunne ikke tolke JSON:", e)
    exit(1)

# Sjekk at riktig nøkkel finnes
if "properties" not in data or "timeseries" not in data["properties"]:
    print("❌ Fant ikke 'properties/timeseries' i responsen.")
    exit(1)

timeseries = data["properties"]["timeseries"]

# Print overskrift
print(f"{'Tid (UTC)':>20} | {'Water Temperature':>20}")

# Gå gjennom hver timestep og hent temperatur
for entry in timeseries:
    t_iso = entry["time"]
    t = datetime.fromisoformat(t_iso.replace("Z", "+00:00"))
    
    temperature = entry["data"].get("instant", {}).get("details", {}).get("sea_water_temperature", 0)
    
    print(f"{t.strftime('%Y-%m-%d %H:%M'):>20} | {temperature:>20.1f}")
