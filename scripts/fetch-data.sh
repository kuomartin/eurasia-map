#!/bin/sh
# Download source data into data/ (not tracked in git).
set -e
cd "$(dirname "$0")/.."
mkdir -p data
curl -sL -A "eurasia-map" -o data/afro.svg "https://commons.wikimedia.org/wiki/Special:FilePath/Afro-Eurasia_location_map_with_borders.svg"
curl -sL -o data/regions.zip "https://naciscdn.org/naturalearth/50m/physical/ne_50m_geography_regions_polys.zip"
curl -sL -o data/land.zip "https://naciscdn.org/naturalearth/10m/physical/ne_10m_land.zip"
curl -sL -o data/rivers50m.geojson "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_rivers_lake_centerlines.geojson"
unzip -o -q data/regions.zip -d data/regions
unzip -o -q data/land.zip -d data/land
rm data/regions.zip data/land.zip
