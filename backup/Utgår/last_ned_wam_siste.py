import requests
import xarray as xr
import pandas as pd
import os

API_KEY = "a4b09032-bca5-4255-ac85-6fea95a1e02c"
LAT, LON = 58.1092, 6.56624
COLLECTION = "wam_nsb"
LIMIT = 5000  # hent så mange som mulig

bbox = f"{LON-0.05},{LAT-0.05},{LON+0.05},{LAT+0.05}"
url = f"https://dmigw.govcloud.dk/v1/forecastdata/collections/{COLLECTION}/items"
params = {"bbox": bbox, "limit": LIMIT, "api-key": API_KEY}

print("Henter tilgjengelige filer fra API ...")
resp = requests.get(url, params=params)
resp.raise_for_status()
data = resp.json()

# Sjekk at vi faktisk fikk noe
if not data["features"]:
    raise ValueError("Ingen data funnet – prøv å øke bbox eller sjekk API-nøkkel.")

# Finn siste modellkjøring
model_runs = [f["properties"]["modelRun"] for f in data["features"]]
latest_model_run = max(model_runs)
print("Siste modellkjøring:", latest_model_run)

# Filtrer til bare den kjøringen
latest_features = [
    f for f in data["features"] if f["properties"]["modelRun"] == latest_model_run
]

files_to_download = [f["asset"]["data"]["href"] for f in latest_features]
print(f"Antall filer i siste modellkjøring: {len(files_to_download)}")

# Last ned filer
for href in files_to_download:
    filename = href.split("/")[-1]
    if not os.path.exists(filename):
        print(f"Laster ned {filename}...")
        r = requests.get(href)
        with open(filename, "wb") as f:
            f.write(r.content)
    else:
        print(f"{filename} finnes allerede, hopper over.")

# Les GRIB og hent nærmeste punkt
all_ds = []
for href in files_to_download:
    filename = href.split("/")[-1]
    ds = xr.open_dataset(filename, engine="cfgrib")
    point = ds.sel(latitude=LAT, longitude=LON, method="nearest")
    all_ds.append(point)

# Slå sammen alle timeserier
full_ds = xr.concat(all_ds, dim="time")

# Lag DataFrame og lagre
df = full_ds.to_dataframe().reset_index()
df.to_csv("Lista_fyr_wam_siste.csv", index=False)
print("✅ Ferdig! Data skrevet til Lista_fyr_wam_siste.csv")
