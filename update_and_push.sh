#!/bin/bash
cd "$(dirname "$0")"

# Activate venv
source venv/bin/activate

# Run fetch_all
python3 surfapp/fetch_all.py

# Add only public data files
git add surfapp/data_public/

# Commit with timestamp
git commit -m "Auto-update Copernicus & forecast $(date -u +"%Y-%m-%d %H:%M UTC")" || true

# Push
git push origin v2
