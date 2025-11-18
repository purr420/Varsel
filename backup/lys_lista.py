import pandas as pd
from datetime import datetime, timedelta

# --- KONFIG ---
# Navnet på inputfilen (CSV)
INPUT_FIL = "lys.csv"
# Navnet på resultatfilen
OUTPUT_FIL = "surfetider.csv"
# Formatet på tidene i CSV (f.eks. 08:27)
TID_FORMAT = "%H:%M"

# Les CSV
df = pd.read_csv(INPUT_FIL, sep=';')

def midtpunkt(tid1, tid2):
    """Returner tidspunktet midt mellom to klokkeslett."""
    t1 = datetime.strptime(tid1, TID_FORMAT)
    t2 = datetime.strptime(tid2, TID_FORMAT)
    midt = t1 + (t2 - t1) / 2
    return midt.strftime(TID_FORMAT)

# Beregn første og siste surf (overskyet)
første_surf_mid = []
siste_surf_mid = []

for i, rad in df.iterrows():
    b_lys = rad['B.lys']
    opp = rad['Opp']
    ned = rad['Ned']
    b_mørk = rad['B.mørk']

    # Midt mellom B.lys og Opp
    midt_morgen = midtpunkt(b_lys, opp)
    # Midt mellom Ned og B.mørk
    midt_kveld = midtpunkt(ned, b_mørk)

    første_surf_mid.append(f"{b_lys}-{midt_morgen}")
    siste_surf_mid.append(f"{midt_kveld}-{b_mørk}")

# Legg til kolonner
df['Første surf'] = første_surf_mid
df['Siste surf'] = siste_surf_mid

# Skriv til ny CSV
df.to_csv(OUTPUT_FIL, sep=';', index=False)

print(f"✅ Ferdig! Lagret til {OUTPUT_FIL}")
