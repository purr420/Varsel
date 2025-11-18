import requests
from datetime import datetime, timedelta, timezone

# Koordinater for Lista fyr
LAT = 58.10917
LON = 6.56667

# Met.no API
URL = f"https://api.met.no/weatherapi/locationforecast/2.0/complete?lat={LAT}&lon={LON}"
HEADERS = {"User-Agent": "PythonScript/1.0 (petter@example.com)"}

# Hent data fra API
resp = requests.get(URL, headers=HEADERS)
resp.raise_for_status()
data = resp.json()

timeseries = data["properties"]["timeseries"]

# Nå-tid UTC
now = datetime.now(timezone.utc)
today_end = datetime(now.year, now.month, now.day, 23, 59, tzinfo=timezone.utc)

# Hele morgendagen
tomorrow = now + timedelta(days=1)
tomorrow_start = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, tzinfo=timezone.utc)
tomorrow_end = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 23, 59, tzinfo=timezone.utc)

def wind_dir_from_deg(deg):
    """Konverter grader til kompassretning med 16 punkter"""
    dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
            "S","SSW","SW","WSW","W","WNW","NW","NNW"]
    idx = round(deg / 22.5) % 16
    return dirs[idx]

def extract_hour_data(ts):
    """Hent ønskede detaljer fra en timeseriepost"""
    instant = ts["data"]["instant"]["details"]
    precipitation = ts.get("data", {}).get("next_1_hours", {}).get("details", {}).get("precipitation_amount", 0)
    wind_deg = instant.get("wind_from_direction")
    return {
        "time": ts["time"],
        "wind_speed": instant.get("wind_speed"),
        "wind_direction": wind_dir_from_deg(wind_deg) if wind_deg is not None else None,
        "gusts": instant.get("wind_speed_of_gust"),
        "cloud_cover": instant.get("cloud_area_fraction"),
        "precipitation": precipitation
    }

# Filtrer timer for i dag + hele morgendagen
selected_hours = []
for ts in timeseries:
    ts_time = datetime.fromisoformat(ts["time"].replace("Z", "+00:00"))
    if now <= ts_time <= today_end or tomorrow_start <= ts_time <= tomorrow_end:
        selected_hours.append(extract_hour_data(ts))

# Print resultat
print("Tid (UTC) | Vind (m/s) | Retning | Gusts (m/s) | Skydekke (%) | Nedbør (mm)")
print("-"*80)
for hour in selected_hours:
    print(f"{hour['time']} | {hour['wind_speed']} | {hour['wind_direction']} | {hour['gusts']} | {hour['cloud_cover']} | {hour['precipitation']}")
