"""
zones_vs_bands.py — do the discovered k-means zones give cleaner skill than latitude bands?

The reviewer flagged that the forecasts use latitude-band predictands, not the clustered zones,
which blends anti-phased regimes (worst for Ethiopia: western Kiremt highlands vs. eastern
Somali/Ogaden lowlands). This wires the saved k-means zones in as predictands and compares, for
each country's key (season, driver) targets, the LOYO cross-validated skill of:
  * the best discovered ZONE mean   vs.
  * the latitude BAND mean (what the rest of the study used).

Outputs
  outputs/tables/zones_vs_bands.md
  outputs/figures/zones_vs_bands.png   zone maps + zone-vs-band skill bars
"""
import warnings, sys
from pathlib import Path
warnings.filterwarnings("ignore")
import numpy as np
import xarray as xr
import deepscale
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import teleconnections as T

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"
SEASON_MONTHS = {"MAM": [3, 4, 5], "JAS": [7, 8, 9], "OND": [10, 11, 12], "JJAS": [6, 7, 8, 9]}

# (country, chirps, zones file, [(label, season, index, band lat tuple), ...])
CFG = [
    ("Nigeria", "nigeria_chirps_monthly.nc", "zones.nc", [
        ("JAS monsoon", "JAS", "atl3", (8, 11)),
        ("OND short rains", "OND", "iod_dmi", (4, 14))]),
    ("Ethiopia", "ethiopia_chirps_monthly.nc", "zones_ethiopia.nc", [
        ("Kiremt (JAS)", "JAS", "wvg3", (10, 15)),
        ("OND short rains", "OND", "iod_dmi", (3, 7))]),
    ("Kenya", "kenya_chirps_monthly.nc", "zones_kenya.nc", [
        ("OND short rains", "OND", "iod_dmi", (-5, 5)),
        ("MAM long rains", "MAM", "nino34", (-5, 5))]),
]


from deepscale.metrics import loo_corr as _loo_corr


def loo_corr(x, y):
    """LOO CV correlation of predictor `x` vs predictand `y`, aligned on shared finite years.

    Year-alignment is the consumer-specific data prep; the closed-form leave-one-out correlation
    is deepscale.metrics.loo_corr (min_finite=12 keeps this study's 12-year floor)."""
    yrs = np.intersect1d(x.dropna("year").year, y.dropna("year").year)
    xv = x.sel(year=yrs).values.astype(float)
    yv = y.sel(year=yrs).values.astype(float)
    return _loo_corr(xv, yv, min_finite=12)


def zone_season_rain(precip, zones, zid, months):
    mask = zones == zid
    z = precip.where(mask)
    band = z.mean(["lat", "lon"])
    return deepscale.seasonal_reduce(band, months)


def band_season_rain(precip, band, months):
    b = precip.sel(lat=slice(*band)).mean(["lat", "lon"])
    return deepscale.seasonal_reduce(b, months)


def main():
    sst = T.load_sst(); idx = T.build_indices(sst)
    md = ["# Discovered zones vs. latitude bands as predictands (LOYO CV skill)\n",
          "For each country's key (season, driver) target: best discovered-ZONE skill vs. the "
          "latitude-BAND skill the study used. Where the zone beats the band, the band was "
          "diluting the signal by blending regimes.\n",
          "| Country | Target | Index | best zone (lat) | **zone LOO r** | band LOO r |",
          "|---|---|---|---|---|---|"]
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    for col, (country, cf, zf, targets) in enumerate(CFG):
        precip = xr.open_dataset(DATA / cf)["precip"]
        zones = xr.open_dataset(DATA / zf)["zone"]
        # zone map
        ax = axes[0, col]
        zones.plot(ax=ax, cmap="viridis", add_colorbar=False, levels=[-.5, .5, 1.5, 2.5, 3.5])
        ax.set_title(f"{country} — discovered zones"); ax.set_xlabel(""); ax.set_ylabel("")
        # skill bars
        ax2 = axes[1, col]
        labels, zvals, bvals = [], [], []
        for tlabel, season, ik, band in targets:
            months = SEASON_MONTHS[season]
            pre = T.index_preseason_mean(idx[ik], months)
            band_r = loo_corr(pre, band_season_rain(precip, band, months))
            # best zone
            zres = []
            band_mean = float(band_season_rain(precip, band, months).mean())
            for zid in range(4):
                ncells = int((zones == zid).sum())
                zr = zone_season_rain(precip, zones, zid, months)
                # require a non-trivial zone (enough cells) with substantial wet-season rainfall,
                # so we don't pick up spurious correlations from small/dry zones
                if ncells < 60 or float(zr.mean()) < 0.4 * band_mean:
                    continue
                latc = float(zones.lat.broadcast_like(zones).where(zones == zid).mean())
                zres.append((zid, latc, loo_corr(pre, zr)))
            zres = [z for z in zres if np.isfinite(z[2])]
            if not zres:
                continue
            bestz = max(zres, key=lambda z: abs(z[2]))
            labels.append(f"{tlabel}\n({ik})"); zvals.append(bestz[2]); bvals.append(band_r)
            md.append(f"| {country} | {tlabel} | {ik} | zone {bestz[0]} (~{bestz[1]:.1f}°N) | "
                      f"**{bestz[2]:+.2f}** | {band_r:+.2f} |")
        x = np.arange(len(labels)); w = 0.38
        ax2.bar(x - w/2, zvals, w, color="#59A14F", edgecolor="k", label="best discovered zone")
        ax2.bar(x + w/2, bvals, w, color="#B07AA1", edgecolor="k", label="latitude band")
        ax2.axhline(0, color="k", lw=0.6); ax2.set_xticks(x); ax2.set_xticklabels(labels, fontsize=8)
        ax2.set_ylim(-0.2, 0.7); ax2.set_ylabel("LOO CV correlation")
        if col == 0:
            ax2.legend(fontsize=8)
    fig.suptitle("Predictand definition: discovered k-means zones vs. latitude bands (LOYO CV skill)\n"
                 "where the green (zone) bar exceeds the purple (band) bar, latitude bands were diluting the signal",
                 fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(FIG / "zones_vs_bands.png", dpi=150); plt.close(fig)
    (TAB / "zones_vs_bands.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    print("\nwrote zones_vs_bands.{md,png}")


if __name__ == "__main__":
    main()
