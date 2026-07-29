"""
downscale_frontier.py — how fine can we downscale while PRESERVING forecast skill?

For a region with real forecast skill (the East African OND short rains), take the coarse (~1°)
NMME precip forecast and downscale it to progressively finer target grids — 1.0°, 0.5°, 0.25°,
0.1°, 0.05° (≈ 110, 55, 28, 11, 5.5 km near the equator) — with several DeepScale methods, and
verify the cross-validated skill against CHIRPS at each resolution. This shows:

  * at what resolution the verified skill deteriorates (the resolution/skill frontier), and
  * which downscaling method preserves skill best as resolution increases.

Skill = leave-one-year-out generalized-ROC (GROC), spatially averaged, at each target grid.
A coarse forecast interpolated to a fine grid inherits the coarse skill only where the fine-scale
signal is predictable; where it is not, GROC falls toward 0.5.

Outputs
  outputs/tables/downscale_frontier.csv
  outputs/figures/downscale_frontier_<region>.png   GROC vs resolution (deg + km), per method
"""
import warnings, csv, sys
from pathlib import Path
warnings.filterwarnings("ignore")
import numpy as np
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import rosetta
import deepscale

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"
HIND = (1993, 2016)
MODELS = ["nmme/geoss2s", "nmme/cesm1", "nmme/ccsm4", "nmme/cansipsic4"]
METHODS = ["delta", "bcsd", "qm", "cca", "rank-analog"]
RES_DEG = [1.0, 0.5, 0.25, 0.1, 0.05]          # target resolutions
COARSEN = {1.0: 20, 0.5: 10, 0.25: 5, 0.1: 2, 0.05: 1}   # CHIRPS 0.05deg -> res

# (region, chirps file, season, band, lon box, representative lat for km)
CONFIGS = [
    ("Kenya OND", "kenya_chirps_monthly.nc", "OND", (-5, 5), (34, 42), 0.0),
    ("Ethiopia OND (south)", "ethiopia_chirps_monthly.nc", "OND", (3, 7), (33, 48), 5.0),
    # Nigeria JAS Middle Belt — low-skill contrast: where there's no coarse-scale skill to begin
    # with, no target resolution can preserve any (GROC should hug 0.5 at every resolution).
    ("Nigeria JAS (Middle Belt)", "nigeria_chirps_monthly.nc", "JAS", (8, 11), (2.5, 15), 9.5),
]
SEASON_MONTHS = {"OND": [10, 11, 12], "JAS": [7, 8, 9]}


def km_of(deg, lat):
    return deg * 111.32 * np.cos(np.deg2rad(lat))          # lon spacing in km at that latitude


def chirps_at(cf, months, band, lonbox, factor):
    p = xr.open_dataset(DATA / cf)["precip"].sel(lat=slice(*band), lon=slice(*lonbox))
    seasonal = deepscale.seasonal_reduce(p, months).sel(year=slice(*HIND))
    if factor > 1:
        seasonal = seasonal.coarsen(lat=factor, lon=factor, boundary="trim").mean()
    return seasonal


def gcm_pooled(cf, season, band, lonbox):
    """Fetch each NMME model and pool them into one (year, member, lat, lon) predictor.

    The pooling (unique member ids, common grid, shared years, concat) is now
    deepscale.pool_ensembles; only the model fetch loop is consumer-specific.
    """
    region = [band[0], band[1], *lonbox]
    das = []
    for prod in MODELS:
        try:
            g = rosetta.fetch(product=prod, variable="precip", init=f"{HIND[1]}-08",
                              target=season, region=region, hindcast=HIND, year_index=True,
                              verbose=False, progress=False, max_retries=4, degenerate_attempts=6)
            das.append(g[list(g.data_vars)[0]])
        except Exception as e:
            print(f"  [drop {prod.split('/')[-1]}] {type(e).__name__}: {str(e)[:60]}", flush=True)
    if not das:
        return None
    return deepscale.pool_ensembles(das)


def main():
    rows = []
    for label, cf, season, band, lonbox, lat0 in CONFIGS:
        print(f"[frontier] {label}", flush=True)
        gcm = gcm_pooled(cf, season, band, lonbox)
        if gcm is None:
            print("  no gcm"); continue
        for res in RES_DEG:
            obs = chirps_at(cf, SEASON_MONTHS[season], band, lonbox, COARSEN[res])
            for m in METHODS:
                try:
                    r = deepscale.optimize(gcm, obs, methods=[m], primary_metric="generalized_roc",
                                           verbose=False, progress=False)
                    g = float(r.score)
                except Exception as e:
                    g = np.nan
                rows.append(dict(region=label, method=m, res_deg=res, res_km=round(km_of(res, lat0), 1),
                                 groc=round(g, 3)))
            best = max((x for x in rows if x["region"] == label and x["res_deg"] == res),
                       key=lambda x: (x["groc"] if np.isfinite(x["groc"]) else -9))
            print(f"    {res}deg (~{km_of(res, lat0):.0f}km): best {best['method']} GROC={best['groc']}", flush=True)

        # figure
        fig, ax = plt.subplots(figsize=(9, 5.2))
        colors = {"delta": "#4E79A7", "bcsd": "#F28E2B", "qm": "#E15759", "cca": "#111111", "rank-analog": "#59A14F"}
        for m in METHODS:
            sub = sorted([x for x in rows if x["region"] == label and x["method"] == m], key=lambda x: -x["res_deg"])
            ax.plot([x["res_deg"] for x in sub], [x["groc"] for x in sub], "-o",
                    color=colors.get(m, "#888"), label=m)
        ax.axhline(0.5, color="red", ls="--", lw=1, label="no-skill (GROC=0.5)")
        ax.set_xscale("log"); ax.set_xticks(RES_DEG); ax.set_xticklabels([str(r) for r in RES_DEG])
        ax.invert_xaxis()
        ax.set_xlabel("target resolution (degrees)"); ax.set_ylabel("LOYO GROC at that resolution")
        # secondary km axis
        sec = ax.secondary_xaxis("top", functions=(lambda d: d, lambda d: d))
        sec.set_xticks(RES_DEG); sec.set_xticklabels([f"{km_of(r, lat0):.0f} km" for r in RES_DEG])
        ax.set_title(f"{label} — downscaling skill vs resolution (this configuration, n≈24)\n"
                     "how fine can we go while preserving forecast skill, and which method preserves best?")
        ax.legend(fontsize=8); ax.grid(alpha=0.3)
        fig.tight_layout(); fig.savefig(FIG / f"downscale_frontier_{label.split()[0].lower()}.png", dpi=150)
        plt.close(fig)

    with open(TAB / "downscale_frontier.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["region", "method", "res_deg", "res_km", "groc"])
        w.writeheader(); w.writerows(rows)
    print("\nwrote downscale_frontier.csv + figures")


if __name__ == "__main__":
    main()
