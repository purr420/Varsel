import pandas as pd
from datetime import datetime, time
import pytz
import os

OSLO_TZ = pytz.timezone("Europe/Oslo")
UTC = pytz.utc

DATA_PATH = os.path.join(
    os.path.dirname(__file__), 
    "..", 
    "data", 
    "daylight_2025_UTC.csv"
)


def load_daylight_table():
    """Load the UTC daylight table as DataFrame."""
    df = pd.read_csv(DATA_PATH)
    df["Dato"] = df["Dato"].astype(str).str.strip()
    return df


def parse_utc(date_str, clock_str):
    """Convert UTC HH:MM on given date to datetime."""
    day, month = map(int, date_str.split("."))
    h, m = map(int, clock_str.split(":"))
    dt = datetime(2025, month, day, h, m, tzinfo=UTC)
    return dt


def format_local(dt):
    if dt is None:
        return "--:--"
    return dt.astimezone(OSLO_TZ).strftime("%H:%M")


def get_light_times(now_utc, table):
    """
    now_utc = timezone-aware UTC datetime.
    table   = loaded daylight UTC table.
    """

    oslo_now = now_utc.astimezone(OSLO_TZ)
    date_key = oslo_now.strftime("%-d.%m") if os.name != "nt" else oslo_now.strftime("%d.%m")

    row = table.loc[table["Dato"] == date_key]

    if row.empty:
        return {
            "sunrise": "--:--",
            "sunset": "--:--",
            "first_light": "--:--",
            "last_light": "--:--",
        }

    row = row.iloc[0]

    # Convert all UTC times to aware datetime objects
    sunrise_utc = parse_utc(date_key, row["Sunrise_UTC"])
    sunset_utc = parse_utc(date_key, row["Sunset_UTC"])
    first_surf_start_utc = parse_utc(date_key, row["First_surf_start_UTC"])
    last_surf_end_utc = parse_utc(date_key, row["Last_surf_end_UTC"])

    return {
        "sunrise": format_local(sunrise_utc),
        "sunset": format_local(sunset_utc),
        "first_light": format_local(first_surf_start_utc),
        "last_light": format_local(last_surf_end_utc),
    }
