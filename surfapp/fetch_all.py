import os
import csv
from datetime import datetime, timezone, timedelta

import requests
import pytz

# ---------------------------------------------------
#  Konfig
# ---------------------------------------------------

UTC = timezone.utc
OSLO_TZ = pytz.timezone("Europe/Oslo")

BASE_DIR = os.path.dirname(__file__)
CACHE_DIR = os.path.join(BASE_DIR, "data_cache")   # intern cache (beste format)
PUBLIC_DIR = os.path.join(BASE_DIR, "data_public") # lesbare CSV-er


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def parse_iso_utc(ts: str) -> datetime:
    """
    Parse ISO8601 med evt. 'Z' til aware UTC-datetime.
    """
    # Yr og MET bruker typisk 2024-11-18T12:00:00Z
    if ts.endswith("Z"):
        ts = ts.replace("Z", "+00:00")
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(UTC)
    return dt


def to_oslo_hhmm(dt_utc: datetime) -> str:
    """
    Konverter UTC-datetime til Oslo-tid og formater HH:MM.
    """
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=UTC)
    dt_oslo = dt_utc.astimezone(OSLO_TZ)
    return dt_oslo.strftime("%H:%M")


def deg_to_compass(deg) -> str:
    """
    Konverter grader til 16-delt kompassretning.
    """
    if deg is None:
        return ""
    try:
        deg_val = float(deg)
    except (TypeError, ValueError):
        return ""

    dirs = [
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
    ]
    idx = round(deg_val / 22.5) % 16
    return dirs[idx]


def round1(value):
    """
    Avrund til 1 desimal, men håndter None.
    """
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return round(float(value), 1)
    return value


def write_cache_and_readable_csv(
    source_name: str,
    rows: list[dict],
    value_keys: list[str],
) -> None:
    """
    Lagrer:
    - intern cache-CSV (UTC + full presisjon)
    - lesbar CSV (UTC, local HH:MM, verdier med 1 desimal)

    rows: liste av dict med minst:
        "time_utc": datetime (UTC)
        + verdier i value_keys
    """

    if not rows:
        print(f"[{source_name}] Ingen data – hopper over.")
        return

    ensure_dir(CACHE_DIR)
    ensure_dir(PUBLIC_DIR)

    # ---- Cache-fil ----
    cache_path = os.path.join(CACHE_DIR, f"{source_name}_cache.csv")
    cache_fieldnames = ["time_utc"] + value_keys

    with open(cache_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cache_fieldnames)
        writer.writeheader()

        for r in rows:
            dt_utc = r["time_utc"]
            if isinstance(dt_utc, datetime):
                ts = dt_utc.astimezone(UTC).isoformat()
            else:
                ts = str(dt_utc)

            row_out = {"time_utc": ts}
            for key in value_keys:
                row_out[key] = r.get(key)
            writer.writerow(row_out)

    # ---- Lesbar-fil ----
    public_path = os.path.join(PUBLIC_DIR, f"{source_name}_readable.csv")
    public_fieldnames = ["time_utc", "time_local"] + value_keys

    with open(public_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=public_fieldnames)
        writer.writeheader()

        for r in rows:
            dt_utc = r["time_utc"]
            if isinstance(dt_utc, datetime):
                ts = dt_utc.astimezone(UTC).isoformat()
                lt = to_oslo_hhmm(dt_utc)
            else:
                # fallback hvis noen gang er string
                dt_parsed = parse_iso_utc(str(dt_utc))
                ts = dt_parsed.astimezone(UTC).isoformat()
                lt = to_oslo_hhmm(dt_parsed)

            row_out = {
                "time_utc": ts,
                "time_local": lt,
            }
            for key in value_keys:
                value = r.get(key)
                if key.endswith("_dir_deg"):
                    row_out[key] = deg_to_compass(value)
                else:
                    row_out[key] = round1(value)
            writer.writerow(row_out)

    print(f"[{source_name}] Cache:   {cache_path}")
    print(f"[{source_name}] Lesbar:  {public_path}")


# ---------------------------------------------------
#  YR – vind, skydekke, nedbør
# ---------------------------------------------------

def fetch_yr_lista() -> list[dict]:
    """
    Henter yr-data for Lista (locationforecast 2.0).
    Normaliserer til:
      - UTC-tid
      - m/s, grader, %, mm
    """
    # Bruk samme lat/lon som i yr_lista.py
    lat = 58.10917
    lon = 6.56667

    url = (
        "https://api.met.no/weatherapi/locationforecast/2.0/complete"
        f"?lat={lat}&lon={lon}"
    )
    headers = {
        "User-Agent": "varsel-app/1.0 github.com/purr420",
    }

    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    timeseries = data["properties"]["timeseries"]

    rows: list[dict] = []
    for ts in timeseries:
        t_utc = parse_iso_utc(ts["time"])
        details = ts["data"]["instant"]["details"]
        next_1h = ts["data"].get("next_1_hours", {}).get("details", {})

        row = {
            "time_utc": t_utc,
            # m/s:
            "wind_speed_ms": details.get("wind_speed"),
            # grader (ikke kompass-tekst):
            "wind_dir_deg": details.get("wind_from_direction"),
            # vindkast m/s:
            "gust_speed_ms": details.get("wind_speed_of_gust"),
            # skydekke %:
            "cloud_cover_pct": details.get("cloud_area_fraction"),
            # nedbør mm neste time:
            "precip_mm": next_1h.get("precipitation_amount"),
        }
        rows.append(row)

    return rows


# ---------------------------------------------------
#  DMI HAV – bølger + vind
# ---------------------------------------------------

def fetch_dmi_hav_lista() -> list[dict]:
    """
    Henter bølge/vind-data fra DMI (hav).
    """

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
        "benjamin-feir-index",
    ]

    url = f"https://dmigw.govcloud.dk/v1/forecastedr/collections/{collection}/position"
    params = {
        "coords": f"POINT({lon} {lat})",
        "crs": "crs84",
        "parameter-name": ",".join(parameters),
        "api-key": api_key,
        "f": "GeoJSON",
    }

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    value_map = {
        "wind_speed_ms": "wind-speed",
        "wind_dir_deg": "wind-dir",
        "hs_m": "significant-wave-height",
        "tp_s": "dominant-wave-period",
        "mean_wave_period_s": "mean-wave-period",
        "mean_zerocrossing_period_s": "mean-zerocrossing-period",
        "mean_wave_dir_deg": "mean-wave-dir",
        "windwave_hs_m": "significant-windwave-height",
        "windwave_tp_s": "mean-windwave-period",
        "windwave_dir_deg": "mean-windwave-dir",
        "swell_hs_m": "significant-totalswell-height",
        "swell_tp_s": "mean-totalswell-period",
        "swell_dir_deg": "mean-totalswell-dir",
        "benjamin_feir_index": "benjamin-feir-index",
    }

    rows: list[dict] = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        step = props.get("step")
        if not step:
            continue
        row = {"time_utc": parse_iso_utc(step)}
        for out_key, prop_key in value_map.items():
            row[out_key] = props.get(prop_key)
        rows.append(row)

    return rows


# ---------------------------------------------------
#  DMI LAND – vind på land
# ---------------------------------------------------

def fetch_dmi_land_lista() -> list[dict]:
    """
    Henter vind-data fra DMI (land).
    """

    lon, lat = 6.56667, 58.10917
    url = "https://dmigw.govcloud.dk/v1/forecastedr/collections/harmonie_dini_sf/position"
    params = {
        "coords": f"POINT({lon} {lat})",
        "crs": "crs84",
        "parameter-name": "wind-speed-10m,wind-dir-10m,gust-wind-speed-10m,temperature-2m",
        "api-key": "ae501bfc-112e-400e-89df-77a2a6b9af72",
        "f": "GeoJSON",
    }

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    rows: list[dict] = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        step = props.get("step")
        if not step:
            continue

        temp_k = props.get("temperature-2m")
        temp_c = temp_k - 273.15 if isinstance(temp_k, (int, float)) else None

        rows.append(
            {
                "time_utc": parse_iso_utc(step),
                "wind_speed_ms": props.get("wind-speed-10m"),
                "wind_dir_deg": props.get("wind-dir-10m"),
                "gust_speed_ms": props.get("gust-wind-speed-10m"),
                "temp_air_c": temp_c,
            }
        )

    return rows


# ---------------------------------------------------
#  MET (hav / sjøtemperatur eller bølger)
# ---------------------------------------------------

def fetch_met_lista() -> list[dict]:
    """
    Henter MET-data fra met_lista.py (sannsynligvis bølger eller sjøtemp).
    Fra filen din ser det ut som du henter en enkel verdi (f.eks. sjøtemperatur).
    """

    lat = 58.09
    lon = 6.52
    url = f"https://api.met.no/weatherapi/oceanforecast/2.0/complete?lat={lat}&lon={lon}"
    headers = {"User-Agent": "post@kurios.no"}

    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    rows: list[dict] = []
    timeseries = data.get("properties", {}).get("timeseries", [])
    for entry in timeseries:
        t_iso = entry.get("time")
        if not t_iso:
            continue
        details = entry.get("data", {}).get("instant", {}).get("details", {})
        rows.append(
            {
                "time_utc": parse_iso_utc(t_iso),
                "sea_temp_c": details.get("sea_water_temperature"),
            }
        )

    return rows


# ---------------------------------------------------
#  Lindesnes fyr – observasjon sjøtemperatur
# ---------------------------------------------------

def fetch_lindesnes_fyr() -> list[dict]:
    """
    Skraper Lindesnes fyr-siden for sjøtemperatur + dato/klokkeslett.

    Nåværende lindesnes_fyr.py parse'r HTML med BeautifulSoup.
    Her lager vi en enklere variant som du kan tilpasse.

    Vi returnerer en liste med én rad:
      {
        "time_utc": datetime(…, tzinfo=UTC),
        "sea_temp_c": ...,
      }
    """

    url = "https://lindesnesfyr.no/vaeret-pa-fyret/"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    from bs4 import BeautifulSoup
    import re

    soup = BeautifulSoup(resp.text, "html.parser")

    title = soup.find("span", class_="title", string=lambda x: x and "Sjøtemperatur" in x)
    if not title:
        return []

    value_span = title.find_next("span", class_="descr")
    sjotemp_str = value_span.get_text(strip=True) if value_span else None

    sea_temp_c = None
    if sjotemp_str:
        m = re.search(r"([\d,\,\.]+)", sjotemp_str)
        if m:
            sea_temp_c = float(m.group(1).replace(",", "."))

    # Forsøk å hente dato fra tekstinnholdet (samme som det opprinnelige skriptet gjorde)
    all_text = soup.get_text(separator="\n", strip=True)
    date_match = re.search(r"(\d{1,2})\.\s*([A-Za-zæøåÆØÅ]+)\s*(\d{4})", all_text)
    obs_dt_oslo = datetime.now(OSLO_TZ)
    obs_date_label = None

    if date_match:
        day = int(date_match.group(1))
        month_name = date_match.group(2).lower()
        year = int(date_match.group(3))

        month_map = {
            "januar": (1, "jan."),
            "februar": (2, "feb."),
            "mars": (3, "mar."),
            "april": (4, "apr."),
            "mai": (5, "mai."),
            "juni": (6, "jun."),
            "juli": (7, "jul."),
            "august": (8, "aug."),
            "september": (9, "sep."),
            "oktober": (10, "okt."),
            "november": (11, "nov."),
            "desember": (12, "des."),
        }

        month_info = month_map.get(month_name)
        if month_info:
            month, month_short = month_info
            local_dt = datetime(year, month, day)
            obs_dt_oslo = OSLO_TZ.localize(local_dt)
            obs_date_label = f"{day}.{month_short}"

    return [
        {
            "time_utc": obs_dt_oslo.astimezone(UTC),
            "sea_temp_raw": sjotemp_str,
            "sea_temp_c": sea_temp_c,
            "obs_date_label": obs_date_label,
        }
    ]


# ---------------------------------------------------
#  MAIN – kjør alle fetch + skriv CSV
# ---------------------------------------------------

def main():
    # 1) YR
    yr_rows = fetch_yr_lista()
    write_cache_and_readable_csv(
        "yr_lista",
        yr_rows,
        ["wind_speed_ms", "wind_dir_deg", "gust_speed_ms", "cloud_cover_pct", "precip_mm"],
    )

    # 2) DMI HAV
    dmi_hav_rows = fetch_dmi_hav_lista()
    if dmi_hav_rows:
        # Tilpass value_keys til det du faktisk returnerer
        write_cache_and_readable_csv(
            "dmi_hav_lista",
            dmi_hav_rows,
            [
                "wind_speed_ms",
                "wind_dir_deg",
                "hs_m",
                "tp_s",
                "mean_wave_period_s",
                "mean_zerocrossing_period_s",
                "mean_wave_dir_deg",
                "windwave_hs_m",
                "windwave_tp_s",
                "windwave_dir_deg",
                "swell_hs_m",
                "swell_tp_s",
                "swell_dir_deg",
                "benjamin_feir_index",
            ],
        )

    # 3) DMI LAND
    dmi_land_rows = fetch_dmi_land_lista()
    if dmi_land_rows:
        write_cache_and_readable_csv(
            "dmi_land_lista",
            dmi_land_rows,
            ["wind_speed_ms", "wind_dir_deg", "gust_speed_ms", "temp_air_c"],
        )

    # 4) MET
    met_rows = fetch_met_lista()
    if met_rows:
        write_cache_and_readable_csv(
            "met_lista",
            met_rows,
            ["sea_temp_c"],
        )

    # 5) Lindesnes fyr
    lind_rows = fetch_lindesnes_fyr()
    if lind_rows:
        write_cache_and_readable_csv(
            "lindesnes_fyr",
            lind_rows,
            ["sea_temp_raw", "sea_temp_c", "obs_date_label"],
        )


if __name__ == "__main__":
    main()
