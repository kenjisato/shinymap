#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${ROOT_DIR}/data"
RAW_GEOJSON="${DATA_DIR}/prefectures.geojson"
SOURCE_URL="https://raw.githubusercontent.com/piuccio/open-data-jp-prefectures-geojson/master/output/prefectures.geojson"

mkdir -p "${DATA_DIR}"
echo "Downloading prefecture GeoJSON..."
curl -L "${SOURCE_URL}" -o "${RAW_GEOJSON}"

echo "Converting to SVG paths..."
python3 "${ROOT_DIR}/scripts/geojson_to_svg_paths.py" "${RAW_GEOJSON}" --width 960 --epsilon 0.8 --min-area 30

echo "Rebuilding web assets..."
(cd "${ROOT_DIR}/www" && npm run build)

echo "Geometry refresh complete."
