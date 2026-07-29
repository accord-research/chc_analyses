"""
composites.py — what ocean state sets up drought vs flood, where and when?

For a set of (season, zone) targets, split the hindcast years into the driest tercile and
the wettest tercile of zone rainfall, and composite the *pre-season* SST anomaly field for
each group. The drought-setup map, the flood-setup map, and their difference show — directly
from the observational archive — the ocean configuration that precedes each outcome for each
region and season. This is descriptive (no forecast, no CV); it is the physical-hypothesis
generator that feeds feature_discovery.py.

Outputs
  outputs/figures/composite_<SEASON>_<BAND>.png   drought / flood / difference SST maps
  outputs/tables/composite_years.json             which years are in each composite

Run in accord-chc after fetch_data.py.
"""
import warnings, json, sys
from pathlib import Path
warnings.filterwarnings("ignore")

import numpy as np
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import teleconnections as T
from areas import AREA, CHIRPS_FILE, LABEL, suffix

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"
for d in (FIG, TAB):
    d.mkdir(parents=True, exist_ok=True)

# (season, band) targets spanning drought- and flood-relevant cases, per area
TARGETS = {
    "nigeria": [
        ("JAS", "North"),      # Sahel monsoon — food-security drought case
        ("JJAS", "Middle"),    # Middle Belt full monsoon
        ("AMJ", "South"),      # Guinea coast first rains
        ("OND", "National"),   # short rains — flood case
    ],
    "ethiopia": [
        ("JJAS", "North"),     # Kiremt highlands — the El Niño drought case
        ("JAS", "North"),      # Kiremt core
        ("MAM", "South"),      # southern long rains / Belg
        ("OND", "South"),      # southern short rains (GHA-type) — flood case
    ],
    "kenya": [
        ("OND", "National"),   # short rains — IOD-driven flood case
        ("MAM", "National"),   # long rains — the paradox
        ("OND", "South"),      # southern/coastal short rains
        ("MAM", "Central"),    # highland long rains
    ],
}[AREA]


def preseason_field(sst_anom, season_months):
    start = min(season_months)
    lead = [((start - 1 - k - 1) % 12) + 1 for k in range(3)]  # 3 months before season
    sub = sst_anom.sel(time=sst_anom["time.month"].isin(lead))
    # assign each obs to the season's year (pre-season months share the season year here,
    # since all leads < start for start > 3; early seasons handled by year shift)
    yr = sub["time.year"] + xr.where(sub["time.month"] >= start, 1, 0)
    return sub.groupby(yr.rename("year")).mean("time")


def main():
    sst = T.load_sst()
    sst_anom = T.monthly_anom(sst)
    ds = xr.open_dataset(ROOT / "data" / CHIRPS_FILE)
    precip = ds["precip"]

    years_record = {}
    for season, band in TARGETS:
        months = T.SEASONS[season]
        s, n = T.BANDS[band]
        rain = T.seasonal_sum(precip, months, s, n)          # (year,)
        field = preseason_field(sst_anom, months)            # (year, lat, lon)
        yrs = np.intersect1d(rain.year.values, field.year.values)
        rain = rain.sel(year=yrs); field = field.sel(year=yrs)

        n3 = max(3, len(yrs) // 3)
        order = rain.year.values[np.argsort(rain.values)]
        dry_years = [int(y) for y in order[:n3]]
        wet_years = [int(y) for y in order[-n3:]]
        years_record[f"{season}_{band}"] = {
            "dry": dry_years, "wet": wet_years,
            "dry_mean_mm": round(float(rain.sel(year=dry_years).mean()), 1),
            "wet_mean_mm": round(float(rain.sel(year=wet_years).mean()), 1),
        }

        dry_c = field.sel(year=dry_years).mean("year")
        wet_c = field.sel(year=wet_years).mean("year")
        diff = wet_c - dry_c

        fig, axes = plt.subplots(3, 1, figsize=(11, 11))
        for ax, dat, ttl, vlim in [
            (axes[0], dry_c, f"DROUGHT setup — pre-season SST anomaly before driest {season} {band} "
                             f"(n={n3}, {min(dry_years)}-{max(dry_years)})", 1.2),
            (axes[1], wet_c, f"FLOOD/WET setup — pre-season SST anomaly before wettest {season} {band}", 1.2),
            (axes[2], diff,  f"WET minus DRY SST anomaly (the discriminating pattern)", 1.0)]:
            dat.plot(ax=ax, cmap="RdBu_r", vmin=-vlim, vmax=vlim,
                     cbar_kwargs={"label": "SST anomaly (°C)"})
            ax.set_title(ttl, fontsize=10)
            ax.set_xlabel("lon (°E)"); ax.set_ylabel("lat")
        fig.suptitle(f"Ocean state preceding {season} rainfall extremes — {LABEL} {band} band\n"
                     f"(ERSST v5 pre-season 3-month anomaly, 1991-2023)", fontweight="bold")
        fig.tight_layout(rect=[0, 0, 1, 0.97])
        fig.savefig(FIG / suffix(f"composite_{season}_{band}","png"), dpi=140)
        plt.close(fig)
        print(f"[composite] {season} {band}: dry={dry_years} wet={wet_years}", flush=True)

    (TAB / suffix("composite_years","json")).write_text(json.dumps(years_record, indent=2))
    print("[composite] wrote composite_years.json and figures ->", FIG, flush=True)


if __name__ == "__main__":
    main()
