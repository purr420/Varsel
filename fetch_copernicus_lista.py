#!/usr/bin/env python3
import os
import subprocess
import xarray as xr
import pandas as pd
from datetime import datetime, timedelta, timezone

# ============================================================
# SETTINGS
# ============================================================

LAT = 58.10
LON = 6.56

# Forecast length to match DMI WAM
FORECAST_HOURS = 66   # DMI WAM max horizon

# Output files
RAW_FILE = "cache_lista_raw.nc"
CSV_FILE = "lista_readable.csv"

# Dataset ID
DATASET = "cmems_mod_nws_wav_anfc_0.027deg_PT1H-i"


# ============================================================
# HELPER: compass conversion
# ============================================================

def deg_to_compass(val):
    dirs = ["N","NØ","Ø","SØ","S","SV","V","NV"]
    i = int((float(val) % 360) / 45)
    return dirs[i]


# ============================================================
# STEP 1 — Download Copernicus data (nearest grid point)
# ============================================================

def download_raw_nc():
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    end = now + timedelta(hours=FORECAST_HOURS)

    cmd = [
        "copernicusmarine", "subset",
        "--dataset-id", DATASET,

        # Total sea state
        "--variable", "VHM0",
        "--variable", "VTPK",
        "--variable", "VTM02",
        "--variable", "VTM10",
        "--variable", "VPED",

        # Wind sea
        "--variable", "VHM0_WW",
        "--variable", "VTM01_WW",
        "--variable", "VMDR_WW",

        # Primary swell
        "--variable", "VHM0_SW1",
        "--variable", "VTM01_SW1",
        "--variable", "VMDR_SW1",

        # Secondary swell
        "--variable", "VHM0_SW2",
        "--variable", "VTM01_SW2",
        "--variable", "VMDR_SW2",

        "--minimum-longitude", str(LON - 0.02),
        "--maximum-longitude", str(LON + 0.02),
        "--minimum-latitude",  str(LAT - 0.02),
        "--maximum-latitude",  str(LAT + 0.02),

        "--start-datetime", now.strftime("%Y-%m-%dT%H:00:00"),
        "--end-datetime",   end.strftime("%Y-%m-%dT%H:00:00"),

        "--output-filename", RAW_FILE,
    ]

    print("Downloading Copernicus data…")
    subprocess.run(cmd, check=True)
    print(f"✔ Raw file saved as: {RAW_FILE}")


# ============================================================
# STEP 2 — Convert .nc to readable CSV
# ============================================================

def convert_to_readable_csv():
    print("Reading:", RAW_FILE)
    ds = xr.open_dataset(RAW_FILE)

    # Pick nearest point (no interpolation)
    pt = ds.sel(latitude=LAT, longitude=LON, method="nearest")

    df = pd.DataFrame({
        "time_utc": pd.to_datetime(pt["time"].values),

        "Total_Hs (m)":      pt["VHM0"].values.round(1),
        "Total_Tp (s)":      pt["VTPK"].values.round(1),
        "Total_Tm02 (s)":    pt["VTM02"].values.round(1),
        "Total_Tm10 (s)":    pt["VTM10"].values.round(1),
        "Total_Dir (°)":     pt["VPED"].values.round(0),
        "Total_Dir_Compass": [deg_to_compass(v) for v in pt["VPED"].values],

        "WW_Hs (m)":         pt["VHM0_WW"].values.round(1),
        "WW_Tm01 (s)":       pt["VTM01_WW"].values.round(1),
        "WW_Dir (°)":        pt["VMDR_WW"].values.round(0),
        "WW_Dir_Compass":    [deg_to_compass(v) for v in pt["VMDR_WW"].values],

        "S1_Hs (m)":         pt["VHM0_SW1"].values.round(1),
        "S1_Tm01 (s)":       pt["VTM01_SW1"].values.round(1),
        "S1_Dir (°)":        pt["VMDR_SW1"].values.round(0),
        "S1_Dir_Compass":    [deg_to_compass(v) for v in pt["VMDR_SW1"].values],

        "S2_Hs (m)":         pt["VHM0_SW2"].values.round(1),
        "S2_Tm01 (s)":       pt["VTM01_SW2"].values.round(1),
        "S2_Dir (°)":        pt["VMDR_SW2"].values.round(0),
        "S2_Dir_Compass":    [deg_to_compass(v) for v in pt["VMDR_SW2"].values],
    })

    df.to_csv(CSV_FILE, sep=";", index=False)
    print(f"✔ Readable CSV written: {CSV_FILE}")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    download_raw_nc()
    convert_to_readable_csv()
