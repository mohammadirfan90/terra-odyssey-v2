"""Download and prepare Natural Earth 110m world countries GeoJSON for offline cartography."""

import json
import urllib.request
from pathlib import Path

URLS = [
    "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson",
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson",
]

def fetch_and_save():
    success = False
    for url in URLS:
        try:
            print(f"Downloading Natural Earth boundaries from {url}...")
            req = urllib.request.Request(url, headers={"User-Agent": "EarthTrendDetective/1.0"})
            with urllib.request.urlopen(req, timeout=20) as response:
                raw_json = response.read().decode("utf-8")
                data = json.loads(raw_json)
                feature_count = len(data.get("features", []))
                print(f"Successfully downloaded {feature_count} country features.")

                # Ensure ISO codes and clean properties
                normalized_features = []
                for f in data.get("features", []):
                    props = f.get("properties", {})
                    # Find ISO A3 code
                    iso_a3 = (
                        props.get("ISO3166-1-Alpha-3")
                        or props.get("ISO_A3")
                        or props.get("iso_a3")
                        or props.get("ADM0_A3")
                        or props.get("id")
                        or props.get("cca3")
                    )
                    name = (
                        props.get("name")
                        or props.get("ADMIN")
                        or props.get("NAME")
                        or props.get("NAME_EN")
                        or "Unknown"
                    )
                    if iso_a3 == "-99" or not iso_a3:
                        iso_a3 = name[:3].upper()

                    f["properties"]["id"] = iso_a3
                    f["properties"]["name"] = name
                    f["properties"]["type"] = "country"
                    normalized_features.append(f)

                # Add ocean basin features for marine exploration
                ocean_basins = [
                    {
                        "type": "Feature",
                        "properties": {"id": "BAY_OF_BENGAL", "name": "Bay of Bengal Basin", "type": "ocean_basin"},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[80.0, 5.0], [95.0, 5.0], [98.0, 10.0], [95.0, 22.0], [89.0, 22.5], [80.0, 16.0], [80.0, 5.0]]]
                        }
                    },
                    {
                        "type": "Feature",
                        "properties": {"id": "NORTH_ATLANTIC", "name": "North Atlantic Ocean", "type": "ocean_basin"},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[-80.0, 10.0], [-10.0, 10.0], [-10.0, 65.0], [-65.0, 65.0], [-80.0, 10.0]]]
                        }
                    },
                    {
                        "type": "Feature",
                        "properties": {"id": "INDIAN_OCEAN", "name": "Equatorial Indian Ocean", "type": "ocean_basin"},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[50.0, -20.0], [100.0, -20.0], [100.0, 10.0], [50.0, 10.0], [50.0, -20.0]]]
                        }
                    }
                ]
                normalized_features.extend(ocean_basins)

                data["features"] = normalized_features

                p1 = Path("frontend/public/offline/geojson/countries.json")
                p1.parent.mkdir(parents=True, exist_ok=True)
                p1.write_text(json.dumps(data), encoding="utf-8")

                p2 = Path("data/regions/countries.geojson")
                p2.parent.mkdir(parents=True, exist_ok=True)
                p2.write_text(json.dumps(data), encoding="utf-8")

                print(f"Saved complete world map with {len(normalized_features)} regions to {p1}")
                success = True
                break
        except Exception as e:
            print(f"Error fetching from {url}: {e}")

    return success

if __name__ == "__main__":
    fetch_and_save()
