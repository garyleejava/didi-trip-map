#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"

KEY="${AMAP_KEY:-${1:-}}"
if [[ -z "$KEY" ]]; then
  echo "Usage: AMAP_KEY=<key> bash scripts/run_all.sh" >&2
  exit 1
fi

mkdir -p outputs

$PY scripts/01_parse_pdfs.py \
  --input-dir data/input \
  --ocr-file outputs/ocr.txt \
  --out outputs/trips.csv \
  --xlsx outputs/trips.xlsx

$PY scripts/02_geocode.py \
  --key "$KEY" \
  --input outputs/trips.csv \
  --output outputs/locations_raw.csv \
  --summary outputs/geocode_summary.json

$PY scripts/03_apply_overrides.py \
  --input outputs/locations_raw.csv \
  --output outputs/locations.csv \
  --overrides overrides/user_overrides.py

$PY scripts/04_build_map.py \
  --key "$KEY" \
  --trips outputs/trips.csv \
  --locations outputs/locations.csv \
  --output outputs/trip-map.html

echo "Done: outputs/trip-map.html"
