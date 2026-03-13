#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

BRANCH="$(git branch --show-current)"
if [[ -z "${BRANCH}" ]]; then
  echo "Could not determine current git branch"
  exit 1
fi

COMMIT_MESSAGE="${1:-Update surfapp NOAA data for Streamlit}"

TARGETS=(
  "surfapp/publish_streamlit_git.sh"
  "surfapp/update_and_publish.sh"
  "surfapp/fetch_all.py"
  "surfapp/streamlit_app.py"
  "surfapp/data_cache/fetch_all_last_run.txt"
  "surfapp/data_cache/dmi_hav_lista_cache.csv"
  "surfapp/data_cache/dmi_land_lista_cache.csv"
  "surfapp/data_cache/dmi_partitions_lista_raw.csv"
  "surfapp/data_cache/lindesnes_fyr_cache.csv"
  "surfapp/data_cache/met_lista_cache.csv"
  "surfapp/data_cache/noaa_lista_cache.csv"
  "surfapp/data_cache/observasjoner_lista_cache.csv"
  "surfapp/data_cache/surfline_lista_cache.csv"
  "surfapp/data_cache/yr_lista_cache.csv"
  "surfapp/data_public/dmi_hav_lista_readable.csv"
  "surfapp/data_public/dmi_land_lista_readable.csv"
  "surfapp/data_public/dmi_partitions_lista_readable.csv"
  "surfapp/data_public/lindesnes_fyr_readable.csv"
  "surfapp/data_public/met_lista_readable.csv"
  "surfapp/data_public/noaa_lista_readable.csv"
  "surfapp/data_public/observasjoner_lista_readable.csv"
  "surfapp/data_public/surfline_lista_readable.csv"
  "surfapp/data_public/yr_lista_readable.csv"
)

git add -- "${TARGETS[@]}"

if git diff --cached --quiet; then
  echo "No staged changes for Streamlit publish"
  exit 0
fi

git commit -m "${COMMIT_MESSAGE}"
git push origin "${BRANCH}"

echo "Published to origin/${BRANCH}"
