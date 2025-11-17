def interpolate_time(interval_str, cloud_cover):
    """
    interval_str = "08:27-08:52"
    cloud_cover: None = 50%
    """

    a_str, b_str = interval_str.split("-")
    a = parse_time(a_str)
    b = parse_time(b_str)

    # Rett opp hvis intervallet er snudd i CSV eller parsing
    if b < a:
        a, b = b, a

    # cloud_cover mangler → 50 %
    if cloud_cover is None:
        frac = 0.5
    else:
        frac = min(max(cloud_cover / 100, 0), 1)

    # ved 0% = tidligste
    # ved 100% = seneste
    delta = (b.hour*60 + b.minute) - (a.hour*60 + a.minute)
    m = (a.hour*60 + a.minute) + delta * frac

    h = int(m // 60)
    mi = int(m % 60)
    return f"{h:02d}:{mi:02d}"
