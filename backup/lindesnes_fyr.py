import requests
from bs4 import BeautifulSoup
import re

url = "https://lindesnesfyr.no/vaeret-pa-fyret/"

resp = requests.get(url)
resp.raise_for_status()

soup = BeautifulSoup(resp.text, "html.parser")

# --- Sjøtemperatur ---
title = soup.find("span", class_="title", string=lambda x: x and "Sjøtemperatur" in x)
if title:
    value_span = title.find_next("span", class_="descr")
    sjotemp = value_span.get_text(strip=True) if value_span else None
else:
    sjotemp = None

print("Sjøtemperatur:", sjotemp)

# --- Dato ---
all_text = soup.get_text(separator="\n", strip=True)

m = re.search(r"(\d{1,2})\.\s*([A-Za-zæøåÆØÅ]+)\s*\d{4}", all_text)
if m:
    dag = m.group(1)
    mnd_navn = m.group(2).lower()

    # Forkortelser
    mnd_map_kort = {
        "januar": "jan.",
        "februar": "feb.",
        "mars": "mar.",
        "april": "apr.",
        "mai": "mai.",
        "juni": "jun.",
        "juli": "jul.",
        "august": "aug.",
        "september": "sep.",
        "oktober": "okt.",
        "november": "nov.",
        "desember": "des."
    }

    dato = f"{dag}.{mnd_map_kort[mnd_navn]}"
    print("Dato:", dato)
else:
    print("Fant ikke dato")
