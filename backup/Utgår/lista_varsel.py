import xarray as xr
import pandas as pd
import os
import re

# --- Punkt ute i havet ---
LAT, LON = 58.09, 6.52

# --- Finn alle GRIB-filer i mappen ---
grib_files = [f for f in os.listdir(".") if f.endswith(".grib")]

# --- Finn siste modellkjøring basert på start-tid i filnavn ---
start_times = []
pattern = re.compile(r"WAM_NSB_SF_(\d{4}-\d{2}-\d{2}T\d{6}Z)_")
for f in grib_files:
    match = pattern.search(f)
    if match:
        start_times.append(match.group(1))

latest_run = max(start_times)
print("Siste modellkjøring:", latest_run)

# --- Filene som tilhører siste modellkjøring ---
latest_files = [f for f in grib_files if latest_run in f]
latest_files.sort()
print(f"Filer som brukes: {len(latest_files)}")

# --- Les filene og hent punkt-data ---
all_ds = []
for filename in latest_files:
    print("Laster:", filename)
    ds = xr.open_dataset(filename, engine="cfgrib")
    point = ds.sel(latitude=LAT, longitude=LON, method="nearest")
    all_ds.append(point)

# Slå sammen alle timeserier
full_ds = xr.concat(all_ds, dim="time")

# Lag DataFrame og skriv til CSV
df = full_ds.to_dataframe().reset_index()
df.to_csv("Havpunkt_wam_siste.csv", index=False)

print("Ferdig! Data skrevet til Havpunkt_wam_siste.csv")
