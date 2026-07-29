"""
areas.py — region configuration so the whole pipeline is one harness, re-pointed by AREA.

Select the study area with the AREA environment variable (default "nigeria"):
    AREA=ethiopia python src/seasons.py

Everything downstream reads bbox / bands / CHIRPS cache / output suffix from here, which is the
concrete demonstration of the "modular, config-driven" thesis: extending the analysis to a new
country is a config entry, not a code rewrite. SST index boxes are global and live in
teleconnections.py (unchanged across areas).
"""
import os

AREAS = {
    "nigeria": {
        "label": "Nigeria",
        # [lat_s, lat_n, lon_w, lon_e]
        "bbox": [4.0, 14.0, 2.5, 15.0],
        "chirps": "nigeria_chirps_monthly.nc",
        # latitude-band proxies for homogeneous zones (S->N); refined by seasons.py clustering
        "bands": {"National": (4, 14), "South": (4, 8), "Middle": (8, 11), "North": (11, 14)},
    },
    "ethiopia": {
        "label": "Ethiopia",
        # Ethiopia spans ~3-15N, 33-48E; complex terrain, N/W Kiremt highlands vs S/SE bimodal
        "bbox": [3.0, 15.0, 33.0, 48.0],
        "chirps": "ethiopia_chirps_monthly.nc",
        # S->N proxy zones: southern (bimodal MAM+OND, GHA-type) -> central (Belg+Kiremt)
        # -> northern (Kiremt-dominated). Data-driven zones come from seasons.py.
        "bands": {"National": (3, 15), "South": (3, 7), "Central": (7, 10), "North": (10, 15)},
    },
    "kenya": {
        "label": "Kenya",
        # Kenya straddles the equator (~-5..5N, 34..42E); canonical Greater-Horn bimodal
        # MAM long-rains + OND short-rains, with a JJAS component in the west (L. Victoria).
        "bbox": [-5.0, 5.0, 34.0, 42.0],
        "chirps": "kenya_chirps_monthly.nc",
        # S->N proxy zones: southern (coast/Tsavo) -> central (highlands, equatorial)
        # -> northern (arid Turkana/Mandera). Data-driven zones come from seasons.py.
        "bands": {"National": (-5, 5), "South": (-5, -1), "Central": (-1, 2), "North": (2, 5)},
    },
}

AREA = os.environ.get("AREA", "nigeria").lower()
if AREA not in AREAS:
    raise SystemExit(f"AREA={AREA!r} not in {list(AREAS)}")

CFG = AREAS[AREA]
LABEL = CFG["label"]
BBOX = CFG["bbox"]
BANDS = CFG["bands"]
CHIRPS_FILE = CFG["chirps"]


def suffix(name, ext):
    """Area-suffixed output name, e.g. suffix('seasons_zone_map', 'png') for ethiopia
    -> 'seasons_zone_map_ethiopia.png'. Nigeria keeps unsuffixed names for back-compat."""
    return f"{name}.{ext}" if AREA == "nigeria" else f"{name}_{AREA}.{ext}"
