from datetime import datetime, time


# ---------------------------------------------------------
# 1. Read daylight table (you plug your full table here)
# ---------------------------------------------------------

def load_daylight_table():
    """
    Return dict with keys like '1.01' and values:
    {
        "first_surf": "08:27-08:52",
        "last_surf": "16:19-16:45"
    }
    """
    # ⬇️ MINIMAL DEMO – du fyller inn hele tabellen senere
    return {
        "1.01": {"first_surf": "08:27-08:52", "last_surf": "16:19-16:45"},
        "2.01": {"first_surf": "08:27-08:52", "last_surf": "16:20-16:46"},
    }


# ---------------------------------------------------------
# Helper: parse "08:27" → time object
# ---------------------------------------------------------

def parse_time(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


# ---------------------------------------------------------
# Helper: interpolate between times with cloud cover
# ---------------------------------------------------------

def interpolate_time(interval_str: str, cloud_cover):
    """
    interval_str = "08:27-08:52"
    cloud_cover in % (None = assume 50%)
    """

    a_str, b_str = interval_str.split("-")
    a = parse_time(a_str)
    b = parse_time(b_str)

    # Fix reversed intervals (safety)
    if (b.hour, b.minute) < (a.hour, a.minute):
        a, b = b, a

    # Cloud cover fraction
    if cloud_cover is None:
        frac = 0.5   # assume 50%
    else:
        frac = min(max(cloud_cover / 100, 0), 1)

    # Convert to minutes from midnight
    a_min = a.hour * 60 + a.minute
    b_min = b.hour * 60 + b.minute

    delta = b_min - a_min
    result_min = a_min + delta * frac

    hh = int(result_min // 60)
    mm = int(result_min % 60)

    return f"{hh:02d}:{mm:02d}"


# ---------------------------------------------------------
# 3. MAIN FUNCTION used from streamlit_app.py
# ---------------------------------------------------------

def get_light_times(now: datetime, cloud_cover, daylight_table):
    """
    now → datetime.now()
    cloud_cover → % or None
    daylight_table → from load_daylight_table()
    """

    key = now.strftime("%-d.%m")  # 1.01 → Linux/Mac
    # On Windows: "%#d.%m"

    if key not in daylight_table:
        # fallback – choose nearest date
        return {"first_light": "--:--", "last_light": "--:--"}

    row = daylight_table[key]

    first_interval = row["first_surf"]
    last_interval = row["last_surf"]

    first_light = interpolate_time(first_interval, cloud_cover)
    last_light = interpolate_time(last_interval, cloud_cover)

    return {
        "first_light": first_light,
        "last_light": last_light,
    }
