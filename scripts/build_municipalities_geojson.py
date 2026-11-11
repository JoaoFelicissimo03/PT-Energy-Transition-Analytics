"""Build the simplified mainland municipality boundaries used by the dashboard map.

Source: Carta Administrativa Oficial de Portugal (CAOP, Direção-Geral do Território),
converted to GeoJSON (latitude/longitude) in https://github.com/nmota/caop_GeoJSON.

The full file is about 36 MB. This script simplifies the shapes (about 150 m tolerance),
rounds the coordinates and keeps only the fields the app needs, which brings it to well
under 1 MB. Run it once from the project root:

    python scripts/build_municipalities_geojson.py

An already downloaded copy can be passed with --source path/to/ContinenteConcelhos.geojson.
"""
import argparse
import json
import unicodedata
from pathlib import Path

import requests
from shapely import make_valid, set_precision
from shapely.geometry import mapping, shape

SOURCE_URL = (
    "https://raw.githubusercontent.com/nmota/caop_GeoJSON/master/"
    "geograficas/ContinenteConcelhos.geojson"
)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = PROJECT_ROOT / "data" / "reference" / "municipalities_mainland.geojson"
TOLERANCE_DEGREES = 0.0015
DECIMALS = 4


def name_key(name):
    """Upper case, no accents, single spaces: the key used to join names from different sources."""
    plain = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    return " ".join(plain.upper().replace("-", " ").split())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", help="Local copy of ContinenteConcelhos.geojson")
    args = parser.parse_args()

    if args.source:
        raw = Path(args.source).read_text(encoding="utf-8-sig")
    else:
        response = requests.get(SOURCE_URL, timeout=120)
        response.raise_for_status()
        raw = response.content.decode("utf-8-sig")
    source = json.loads(raw)

    features = []
    for feature in source["features"]:
        props = feature["properties"]
        geometry = shape(feature["geometry"]).simplify(TOLERANCE_DEGREES, preserve_topology=True)
        # Snap to a 0.0001 degree grid; set_precision keeps the shapes valid while rounding
        geometry = make_valid(set_precision(geometry, 10 ** -DECIMALS))
        geometry = mapping(geometry)
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "key": name_key(props["Concelho"]),
                    "municipality": props["Concelho"].title(),
                    "district": props["Distrito"].title(),
                    "dico": props["DICO"],
                },
                "geometry": geometry,
            }
        )

    keys = [f["properties"]["key"] for f in features]
    assert len(keys) == len(set(keys)), "Two municipalities share the same name key"

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"Saved {len(features)} municipalities to {OUTPUT.relative_to(PROJECT_ROOT)} "
          f"({OUTPUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
