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


def round1(value):
    """
    Avrund til 1 desimal, men håndter None.
    """
    if value is None:
        return ""
    try:
        return round(float(value), 1)
    except (TypeError, ValueError):
        return ""


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
                row_out[key] = round1(r.get(key))
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
    lat = 58.1
    lon = 6.6

    url = (
        "https://api.met.no/weatherapi/locationforecast/2.0/compact"
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
    Denne funksjonen er et skjelett – plugg inn parsing
    fra din gamle dmi_hav_lista.py.

    Du vil typisk ha noe sånt:
      - loop over features/times
      - hente "forecast-time" / liknende felt
      - verdier for wave/wind-parametere.

    Output per rad:
      {
        "time_utc": datetime(…, tzinfo=UTC),
        "wind_speed_ms": ...,
        "wind_dir_deg": ...,
        "hs_m": ...,
        "tp_s": ...,
        "windwave_hs_m": ...,
        ...
      }
    """

    # TODO: bytt ut med endpoint og logikk fra din nåværende dmi_hav_lista.py
    # Eksempel *struktur* (ikke endelig kode):
    #
    # base_url = "https://dmigw.govcloud.dk/v1/forecastedr/collections/dmi_ps_wave_position"
    # params = {...}
    # headers = {"X-Gravitee-Api-Key": "..."}
    # resp = requests.get(base_url, params=params, headers=headers, timeout=20)
    # resp.raise_for_status()
    # js = resp.json()
    #
    # rows = []
    # for feat in js["features"]:
    #     props = feat["properties"]
    #     t_utc = parse_iso_utc(props["time"])  # eller tilsvarende felt
    #     rows.append({
    #         "time_utc": t_utc,
    #         "wind_speed_ms": props.get("wind-speed"),
    #         "wind_dir_deg": props.get("wind-dir"),
    #         "hs_m": props.get("significant-wave-height"),
    #         "tp_s": props.get("dominant-wave-period"),
    #         "mwdir_deg": props.get("mean-wave-dir"),
    #         "windwave_hs_m": props.get("significant-windwave-height"),
    #         # legg til flere etter behov
    #     })
    #
    # return rows

    # Midlertidig: returner tom liste så skriptet kjører
    return []


# ---------------------------------------------------
#  DMI LAND – vind på land
# ---------------------------------------------------

def fetch_dmi_land_lista() -> list[dict]:
    """
    Henter vind-data fra DMI (land).
    Bruk strukturen fra dmi_land_lista.py, men behold grader i stedet for kompass.

    Ønsket output per rad:
      {
        "time_utc": datetime(…, tzinfo=UTC),
        "wind_speed_ms": ...,
        "wind_dir_deg": ...,
        "gust_speed_ms": ...,
        "temp_air_c": ...,
      }
    """

    # TODO: implementer med din eksisterende URL / API-nøkkel.
    # Se i dmi_land_lista.py: du har allerede logikk for å hente wspeed, wdir, gust, temp.
    #
    # Eksempel-skisse:
    #
    # url = "https://dmigw.govcloud.dk/v1/forecastedr/collections/...land..."
    # headers = {"X-Gravitee-Api-Key": "..."}
    # resp = requests.get(url, headers=headers, timeout=20)
    # resp.raise_for_status()
    # js = resp.json()
    #
    # rows = []
    # for step in js["features"]:
    #     props = step["properties"]
    #     t_utc = parse_iso_utc(props["time"])
    #     rows.append({
    #         "time_utc": t_utc,
    #         "wind_speed_ms": props.get("wind-speed"),
    #         "wind_dir_deg": props.get("wind-dir"),
    #         "gust_speed_ms": props.get("wind-speed-10m_gust"),
    #         "temp_air_c": props.get("air-temperature"),
    #     })
    #
    # return rows

    return []


# ---------------------------------------------------
#  MET (hav / sjøtemperatur eller bølger)
# ---------------------------------------------------

def fetch_met_lista() -> list[dict]:
    """
    Henter MET-data fra met_lista.py (sannsynligvis bølger eller sjøtemp).
    Fra filen din ser det ut som du henter en enkel verdi (f.eks. sjøtemperatur).

    Her definerer vi en generisk struktur:
      {
        "time_utc": datetime(…, tzinfo=UTC),
        "sea_temp_c": ...,
        ...
      }
    """

    # TODO: plugg inn endpoint og parsing fra met_lista.py.
    # Eksempel hvis MET gir timeserier:
    #
    # url = "https://...met.no/...api..."
    # headers = {"User-Agent": "..."}
    # resp = requests.get(url, headers=headers, timeout=15)
    # resp.raise_for_status()
    # js = resp.json()
    #
    # rows = []
    # for ts in js["properties"]["timeseries"]:
    #     t_utc = parse_iso_utc(ts["time"])
    #     details = ts["data"]["instant"]["details"]
    #     rows.append({
    #         "time_utc": t_utc,
    #         "sea_temp_c": details.get("sea_water_temperature"),
    #     })
    #
    # return rows

    return []


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

    soup = BeautifulSoup(resp.text, "html.parser")

    # Sjøtemperatur (samme logikk som i skriptet ditt)
    title = soup.find("span", class_="title", string=lambda x: x and "Sjøtemperatur" in x)
    if not title:
        return []

    value_span = title.find_next("span", class_="descr")
    sjotemp_str = value_span.get_text(strip=True) if value_span else None

    # Grov parsing av tall, f.eks. "8,3 °C" -> 8.3
    sea_temp_c = None
    if sjotemp_str:
        import re
        m = re.search(r"([\d,\.]+)", sjotemp_str)
        if m:
            sea_temp_c = float(m.group(1).replace(",", "."))

    # Dato: her bør du kopiere ferdig logikk fra lindesnes_fyr.py
    # Nå antar vi "nå" som tidspunkt hvis vi ikke klarer å parse
    obs_dt_oslo = datetime.now(OSLO_TZ)

    row = {
        "time_utc": obs_dt_oslo.astimezone(UTC),
        "sea_temp_c": sea_temp_c,
    }
    return [row]


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
                "mwdir_deg",
                "windwave_hs_m",
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
            ["sea_temp_c"],
        )


if __name__ == "__main__":
    main()
