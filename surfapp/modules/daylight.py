import csv
from datetime import datetime
from pathlib import Path


DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "daylight.csv"


def load_daylight_table():
    """Loader dagslys-tabellen fra CSV og returnerer dict keyed på '1.01', '2.01', ..."""
    table = {}

    with open(DATA_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")

        for row in reader:
            key = row["Dato"].strip()  # f.eks "1.01"
            table[key] = {
                "date": key,
                "first_surf": row["Første surf"].strip(),
                "last_surf": row["Siste surf"].strip(),
            }

    return table


def nearest_day_key(date_key: str, table: dict) -> str:
    """
    Håndterer skuddår:
    Hvis dato_key ikke finnes (f.eks 29.02), returner nærmeste (28.02).
    """
    if date_key in table:
        return date_key

    # Finn nærmeste match
    # F.eks 29.02 → prøv 28.02 → 27.02
    day, month = map(int, date_key.split("."))

    for d in range(day - 1, 0, -1):
        candidate = f"{d}.{month:02d}"
        if candidate in table:
            return candidate

    # fallback (skulle aldri skje)
    return "1.01"


def pick_time_from_interval(interval: str, cloud: float) -> str:
    """Velger tidspunkt lineært basert på skydekke."""
    try:
        start_str, end_str = interval.split("-")
    except ValueError:
        return None

    start = datetime.strptime(start_str, "%H:%M")
    end = datetime.strptime(end_str, "%H:%M")

    if cloud is None:
        cloud = 50

    t = max(0, min(cloud, 100)) / 100.0
    delta = end - start
    chosen = start + t * delta
    return chosen.strftime("%H:%M")


def get_light_times(dt: datetime, cloud_cover: float, table=None):
    """
    dt: datetime.now() eller lignende (OSLO-tid)
    cloud_cover: 0–100 eller None

    Returnerer:
    {
        'first_light': '08:34',
        'last_light': '16:27'
    }
    """

    if table is None:
        table = load_daylight_table()

    key = dt.strftime("%-d.%m") if dt.strftime("%-d.%m") in table else dt.strftime("%d.%m")
    key = nearest_day_key(key, table)

    row = table[key]

    first_light = pick_time_from_interval(row["first_surf"], cloud_cover)
    last_light  = pick_time_from_interval(row["last_surf"], cloud_cover)

    return {
        "first_light": first_light,
        "last_light": last_light,
        "key_used": key,
    }
