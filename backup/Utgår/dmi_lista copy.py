#!/usr/bin/env python3
import requests
import csv
import math

# -------------------------------
# Configuration
# -------------------------------
api_key = "ae501bfc-112e-400e-89df-77a2a6b9af72"
collection = "wam_nsb"
lon = 6.5
lat = 58.1

parameters = [
    "wind-speed",
    "wind-dir",
    "significant-wave-height",
    "dominant-wave-period",
    "mean-wave-period",
    "mean-zerocrossing-period",
    "mean-wave-dir",
    "significant-windwave-height",
    "mean-windwave-period",
    "mean-windwave-dir",
    "significant-totalswell-height",
    "mean-totalswell-period",
    "mean-totalswell-dir",
    "benjamin-feir-index"
]

# -------------------------------
# Helper functions
# -------------------------------
def deg_to_compass(deg):
    """Convert degrees to nearest 16-point compass direction."""
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    ix = round(deg / 22.5) % 16
    return dirs[ix]

def round_value(val):
    """Round float to 1 decimal, keep None as is."""
    return round(val, 1) if isinstance(val, (float, int)) else val

# -------------------------------
# Build request URL
# -------------------------------
base_url = f"https://dmigw.govcloud.dk/v1/forecastedr/collections/{collection}/position"
coords = f"POINT({lon} {lat})"
param_str = ",".join(parameters)
url = f"{base_url}?coords={coords}&crs=crs84&parameter-name={param_str}&api-key={api_key}&f=GeoJSON"

print("Requesting URL:", url)

# -------------------------------
# Fetch data
# -------------------------------
resp = requests.get(url)
resp.raise_for_status()
data = resp.json()

features = data.get("features", [])
if not features:
    print("No data returned.")
    exit()

# -------------------------------
# Save CSV
# -------------------------------
csv_filename = f"{collection}_{lon}_{lat}.csv"
fieldnames = ["step"] + parameters

with open(csv_filename, mode="w", newline='', encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for feat in features:
        props = feat.get("properties", {})
        row = {"step": props.get("step")}
        for p in parameters:
            val = props.get(p)
            val = round_value(val)
            if "dir" in p and val is not None:  # convert directions to compass
                val = deg_to_compass(val)
            row[p] = val
        writer.writerow(row)

print(f"Saved {len(features)} rows to {csv_filename}")

# -------------------------------
# Print first 5 lines of CSV
# -------------------------------
with open(csv_filename, mode="r", encoding="utf-8") as csvfile:
    for i, line in enumerate(csvfile):
        print(line.strip())
        if i >= 4:
            break
