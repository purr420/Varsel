#!/usr/bin/env python3
"""
Fetch NOAA WW3 (GFS-Wave) swell partitions for Lista.

Grid: global.0p25  (this grid has SWELL/SWPER/SWDIR with levels 1–3)
Subset: small box around South Norway (can be expanded later)
Output: JSON with Hs/Tm/Dir for S1, S2, S3 every 3h from 3–120h.
"""

import io
import json
import math
import tempfile
from datetime import datetime

import pygrib
import requests

# ------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------

# Target location: Lista
LAT_TARGET = 58.10
LON_TARGET = 6.60

# Subset box (in degrees, global grid uses 0–360° lon)
# Covers South Norway; easy to expand later if you want more spots
LAT_MIN = 55.0
LAT_MAX = 62.0
LON_MIN = 0.0
LON_MAX = 20.0

# Forecast hours (3-hour steps until 120h)
FORECAST_HOURS = list(range(3, 121, 3))

# NOAA NOMADS endpoint (gfswave filter)
BASE_URL = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfswave.pl"

# Model run date/cycle
# You can later auto-detect latest cycle; for now keep this simple
DATE = datetime.utcnow().strftime("%Y%m%d")
CYCLE = "00"  # "00", "06", "12", "18"

# Output JSON file
OUTFILE = "noaa_ww3_lista.json"


# ------------------------------------------------------------
# Helper: download subset GRIB in-memory
# ------------------------------------------------------------
def download_grib(fhour: int) -> io.BytesIO:
    params = {
        # Use GLOBAL 0.25° grid (this has swell partitions)
        "file": f"gfswave.t{CYCLE}z.global.0p25.f{fhour:03d}.grib2",

        # VARIABLES (use var_ prefix)
        "var_HTSGW": "on",  # total significant wave height
        "var_PERPW": "on",  # peak wave period (bulk)
        "var_DIRPW": "on",  # peak wave direction (bulk)

        # LEVELS (swell partitions 1,2,3)
        "all_lev": "on",
        "lev_1_in_sequence": "on",
        "lev_2_in_sequence": "on",
        "lev_3_in_sequence": "on",

        # GEOGRAPHIC SUBSET
        "leftlon": LON_MIN,
        "rightlon": LON_MAX,
        "toplat": LAT_MAX,
        "bottomlat": LAT_MIN,

        # DIRECTORY FOR THIS RUN
        "dir": f"/gfs.{DATE}/{CYCLE}/wave/gridded",
    }

    url = BASE_URL
    req = requests.Request("GET", url, params=params).prepare()
    print("REQUEST:", req.url)

    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    return io.BytesIO(r.content)


# ------------------------------------------------------------
# Helper: find nearest grid index for Lista in a GRIB message
# ------------------------------------------------------------
def nearest_index_ocean(g, lat0, lon0):
    """
    Find nearest ocean grid point (not masked).
    g is a pygrib message; we use g.values + g.latlons().
    """
    lats, lons = g.latlons()
    vals = g.values

    best_i = best_j = None
    best_dist = 1e30

    n_i, n_j = lats.shape

    for i in range(n_i):
        for j in range(n_j):
            if hasattr(vals[i, j], "mask") and vals[i, j].mask:
                continue  # land point
            d = (lats[i, j] - lat0) ** 2 + (lons[i, j] - lon0) ** 2
            if d < best_dist:
                best_dist = d
                best_i, best_j = i, j

    return best_i, best_j


def safe_val(arr):
    try:
        return float(arr)
    except Exception:
        return None


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    output = []

    grid_found = False
    i_idx = j_idx = None

    for fh in FORECAST_HOURS:
        print(f"\nFetching f{fh:03d}…")

        buf = download_grib(fh)

        # pygrib expects a real file, so write buffer to temp file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(buf.getvalue())
            tmp_path = tmp.name

        grbs = pygrib.open(tmp_path)

        # Determine nearest gridpoint once (from first SWELL field)
        if not grid_found:
            for g in grbs:
                if g.name == "Significant height of combined wind waves and swell":
                    i_idx, j_idx = nearest_index_ocean(g, LAT_TARGET, LON_TARGET)
                    lats, lons = g.latlons()
                    grid_found = True
                    print(
                        f"Nearest OCEAN point: (i={i_idx}, j={j_idx}) "
                        f"lat={lats[i_idx, j_idx]:.3f}, lon={lons[i_idx, j_idx]:.3f}"
                    )
                    break
            grbs.seek(0)  # rewind

        bulk_h = None   # HTSGW
        bulk_tm = None  # PERPW
        bulk_dir = None # DIRPW

        for g in grbs:
            name = g.name
            if name == "Significant height of combined wind waves and swell":  # HTSGW
                bulk_h = safe_val(g.values[i_idx, j_idx])
            elif name == "Primary wave mean period":  # PERPW
                bulk_tm = safe_val(g.values[i_idx, j_idx])
            elif name == "Primary wave direction":  # DIRPW
                bulk_dir = safe_val(g.values[i_idx, j_idx])

        grbs.close()

        record = {
            "forecast_hour": fh,
            "Hs": bulk_h,
            "Tm": bulk_tm,
            "Dir": bulk_dir,
        }

        print(
            f"  BULK: Hs={bulk_h}  Tm={bulk_tm}  Dir={bulk_dir}"
        )

        output.append(record)

    # Save JSON
    with open(OUTFILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved {len(output)} records → {OUTFILE}")


if __name__ == "__main__":
    main()
