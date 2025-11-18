import requests
import json
import csv
from datetime import datetime

# Coordinates for Lista lighthouse
lon, lat = 6.56667, 58.10917

params = {
    "coords": f"POINT({lon} {lat})",
    "crs": "crs84",
    "parameter-name": "wind-speed-10m,wind-dir-10m,gust-wind-speed-10m,temperature-2m",
    "api-key": "ae501bfc-112e-400e-89df-77a2a6b9af72",
    "f": "GeoJSON"
}

url = "https://dmigw.govcloud.dk/v1/forecastedr/collections/harmonie_dini_sf/position"

print("Requesting URL:", f"{url}?{params}")
resp = requests.get(url, params=params)
try:
    resp.raise_for_status()
    data = resp.json()
except requests.HTTPError as e:
    print("Error fetching data:", e)
    exit(1)

features = data.get("features", [])
csv_file = "dmi_land_lista.csv"

with open(csv_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    # Only one timestamp column now, named step_UTC
    writer.writerow(["step_UTC","wind-speed-10m","wind-dir-10m-compass","gust-wind-speed-10m","temperature-C"])
    
    for feat in features:
        prop = feat["properties"]
        # Convert ISO timestamp to readable format, keep it in UTC
        step_utc = datetime.fromisoformat(prop["step"].replace("Z","+00:00")).strftime("%Y-%m-%d %H:%M:%S")
        
        wspeed = round(prop["wind-speed-10m"])
        wdir = round(prop["wind-dir-10m"])
        gust = round(prop["gust-wind-speed-10m"])
        temp_c = round(prop["temperature-2m"] - 273.15, 1)
        
        # Convert wind direction to compass
        dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
        idx = round(wdir / 22.5) % 16
        wcompass = dirs[idx]

        writer.writerow([step_utc, wspeed, wcompass, gust, temp_c])

print(f"Saved {len(features)} rows to {csv_file}")
