#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "${SCRIPT_DIR}"
python3 fetch_all.py
python3 fetch_tides_norway.py
"${SCRIPT_DIR}/publish_streamlit_git.sh" "${1:-Update surfapp data for Streamlit}"
