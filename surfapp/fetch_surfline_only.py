import os
import csv
from datetime import datetime, timezone
import requests

UTC = timezone.utc

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "data_cache")
PUBLIC_DIR = os.path.join(BASE_DIR, "data_public")

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(PUBLIC_DIR, exist_ok=True)

CACHE_FILE = os.path.join(CACHE_DIR, "surfline_lista_cache.csv")
PUBLIC_FILE = os.path.join(PUBLIC_DIR, "surfline_lista_readable.csv")

SPOT_ID = "60521386c79046102c0e2cfd"  # Lista


def fetch_surfline():
    url = (
        "https://services.surfline.com/kbyg/spots/forecasts/wave"
        f"?spotId={SPOT_ID}&days=5"
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
        ),
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.surfline.com/",
    }

    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    wave_data = data.get("data", {}).get("wave", [])

    rows = []

    for entry in wave_data:
        ts = entry.get("timestamp")
        if ts is None:
            continue

        dt = datetime.fromtimestamp(ts, tz=UTC)

        # Always 6 swells (pad with empty dicts)
        swells = entry.get("swells", [])[:6]
        while len(swells) < 6:
            swells.append({})

        row = {"time_utc": dt.isoformat()}

        for i, sw in enumerate(swells, start=1):
            row[f"s{i}_h"] = sw.get("height")
            row[f"s{i}_p"] = sw.get("period")
            row[f"s{i}_dir"] = sw.get("direction")
            row[f"s{i}_dirMin"] = sw.get("directionMin")
            row[f"s{i}_impact"] = sw.get("impact")

        rows.append(row)

    return rows


def write_csvs(rows):

    # ------------------------------
    # CACHE CSV (identisk format)
    # ------------------------------
    cache_fields = [
        "time_utc",
        "s1_h","s1_p","s1_dir","s1_dirMin",
        "s2_h","s2_p","s2_dir","s2_dirMin",
        "s3_h","s3_p","s3_dir","s3_dirMin",
        "s4_h","s4_p","s4_dir","s4_dirMin",
        "s5_h","s5_p","s5_dir","s5_dirMin",
        "s6_h","s6_p","s6_dir","s6_dirMin",
        "s1_impact","s2_impact","s3_impact",
        "s4_impact","s5_impact","s6_impact",
    ]

    with open(CACHE_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cache_fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"[surfline] Cache skrevet: {CACHE_FILE}")

    # ------------------------------
    # READABLE CSV (samme format som original)
    # time_local legges til
    # ------------------------------

    public_fields = ["time_utc", "time_local"] + [
        f"s{i}_h" for i in range(1, 7)
    ] + [
        f"s{i}_p" for i in range(1, 7)
    ] + [
        f"s{i}_dir" for i in range(1, 7)
    ] + [
        f"s{i}_dirMin" for i in range(1, 7)
    ] + [
        f"s{i}_impact" for i in range(1, 7)
    ]

    with open(PUBLIC_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=public_fields)
        w.writeheader()

        for r in rows:
            dt_utc = datetime.fromisoformat(r["time_utc"])
            time_local = dt_utc.astimezone().strftime("%H:%M")

            out = {"time_utc": r["time_utc"], "time_local": time_local}
            for k in public_fields:
                if k in ("time_utc", "time_local"):
                    continue
                out[k] = r.get(k)
            w.writerow(out)

    print(f"[surfline] Readable skrevet: {PUBLIC_FILE}")


def main():
    rows = fetch_surfline()
    write_csvs(rows)


if __name__ == "__main__":
    main()