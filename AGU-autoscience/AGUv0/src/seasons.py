"""
seasons.py — discover Nigeria's natural seasonal partitions from observed rainfall.

Reads cached CHIRPS-v3 monthly (data/nigeria_chirps_monthly.nc) and derives, from data
alone (no assumed calendar):

  1. the per-pixel mean annual cycle (1991-2020 climatology),
  2. a rainfall-regime diagnostic (unimodal vs bimodal) via harmonic analysis,
  3. homogeneous rainfall zones by clustering standardized annual cycles,
  4. candidate seasonal-forecast windows (3-6 contiguous months) per zone.

Outputs
  outputs/figures/seasons_annual_cycle.png   annual cycle per zone
  outputs/figures/seasons_regime_map.png     bimodality index map
  outputs/figures/seasons_zone_map.png       homogeneous-zone map
  outputs/tables/seasons_summary.csv         per-zone stats + proposed windows
  outputs/tables/seasons_summary.md          markdown table for docs/02

Run in the accord-chc env after fetch_data.py.
"""
import warnings, json
from pathlib import Path
warnings.filterwarnings("ignore")

import sys
import numpy as np
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from areas import CHIRPS_FILE, LABEL, suffix

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"
for d in (FIG, TAB):
    d.mkdir(parents=True, exist_ok=True)

CLIM = (1991, 2020)
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load_climatology():
    ds = xr.open_dataset(DATA / CHIRPS_FILE)
    da = ds["precip"]
    # subset to climatology window
    yrs = da["time"].dt.year
    da = da.sel(time=(yrs >= CLIM[0]) & (yrs <= CLIM[1]))
    # mean annual cycle: (month, lat, lon), units mm/day -> convert to mm/month approx
    clim = da.groupby("time.month").mean("time")
    # days per month (approx) to get monthly totals
    dpm = xr.DataArray([31,28.25,31,30,31,30,31,31,30,31,30,31],
                       coords={"month": np.arange(1, 13)}, dims="month")
    clim_mm = clim * dpm
    return clim_mm  # (month, lat, lon), mm/month


def bimodality_index(clim):
    """Ratio of the semi-annual (2nd) to annual (1st) Fourier harmonic amplitude.
    High -> two peaks per year (bimodal); low -> single peak (unimodal)."""
    x = clim.transpose("month", "lat", "lon").values  # (12, ny, nx)
    n = 12
    t = np.arange(n)
    # complex Fourier coefficients for k=1 and k=2
    def amp(k):
        c = np.tensordot(np.exp(-2j*np.pi*k*t/n), x, axes=([0],[0])) * (2.0/n)
        return np.abs(c)
    a1 = amp(1)
    a2 = amp(2)
    bi = a2 / (a1 + 1e-6)
    return xr.DataArray(bi, coords={"lat": clim.lat, "lon": clim.lon}, dims=["lat", "lon"])


def peak_months(cycle):
    """Return indices (0-based months) of local maxima in a 12-month cyclic series."""
    peaks = []
    for i in range(12):
        prev, nxt = cycle[(i-1) % 12], cycle[(i+1) % 12]
        if cycle[i] >= prev and cycle[i] >= nxt and cycle[i] > 0.15 * cycle.max():
            peaks.append(i)
    return peaks


def cluster_zones(clim, k=4):
    """K-means on standardized annual cycles -> homogeneous rainfall zones."""
    stack = clim.stack(cell=("lat", "lon")).transpose("cell", "month")
    vals = stack.values  # (ncell, 12)
    good = np.isfinite(vals).all(axis=1) & (vals.sum(axis=1) > 0)
    X = vals[good]
    # standardize each cell's cycle (shape of the season, not amount)
    Xs = (X - X.mean(1, keepdims=True)) / (X.std(1, keepdims=True) + 1e-6)
    try:
        from sklearn.cluster import KMeans
        km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(Xs)
        lab = km.labels_
    except Exception:
        # fallback: order by latitude of peak month
        lab = np.digitize(X.argmax(1), bins=np.quantile(X.argmax(1), np.linspace(0, 1, k+1)[1:-1]))
    labels = np.full(vals.shape[0], np.nan)
    labels[good] = lab
    lab_da = xr.DataArray(labels, coords={"cell": stack.cell}, dims="cell").unstack("cell")
    # order zones south->north by mean latitude for stable labeling
    lat2d = lab_da.lat.broadcast_like(lab_da)
    uniq = np.unique(labels[np.isfinite(labels)])
    mean_lat = {z: float(lat2d.where(lab_da == z).mean()) for z in uniq}
    ranking = {old: new for new, old in enumerate(sorted(uniq, key=lambda z: mean_lat[z]))}
    remap = np.full_like(labels, np.nan)
    for old, new in ranking.items():
        remap[labels == old] = new
    return xr.DataArray(remap, coords={"cell": stack.cell}, dims="cell").unstack("cell")


def propose_windows(cycle):
    """Given a 12-month cycle, propose 3-6 month contiguous forecast windows covering
    the wet season(s). Returns list of (label, month_indices)."""
    total = cycle.sum()
    windows = []
    # find best contiguous window of length L (3..6) maximizing captured rainfall fraction
    best_by_len = {}
    for L in range(3, 7):
        best, bestsum = None, -1
        for s in range(12):
            idx = [(s+j) % 12 for j in range(L)]
            ssum = cycle[idx].sum()
            if ssum > bestsum:
                bestsum, best = ssum, idx
        best_by_len[L] = (best, bestsum/total)
    # pick the shortest window capturing >=70% of annual rainfall (parsimonious season)
    chosen = None
    for L in range(3, 7):
        idx, frac = best_by_len[L]
        if frac >= 0.70:
            chosen = (L, idx, frac)
            break
    if chosen is None:
        L = 6
        idx, frac = best_by_len[6]
        chosen = (L, idx, frac)
    lab = "".join(MONTHS[i][0] for i in chosen[1])
    windows.append((lab, chosen[1], chosen[2]))
    return windows, best_by_len


def main():
    clim = load_climatology()
    print("loaded climatology", dict(clim.sizes), flush=True)

    bi = bimodality_index(clim)
    zones = cluster_zones(clim, k=4)
    # persist the discovered zone labels so downstream analyses can use zone masks (not just
    # latitude bands) as predictands — addresses the anti-phased-regime blending limitation.
    zones.rename("zone").to_netcdf(DATA / suffix("zones", "nc"))

    # ---- per-zone annual cycle + proposed windows ----
    rows = []
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = plt.cm.viridis(np.linspace(0, 0.9, 4))
    for z in range(4):
        mask = zones == z
        if int(mask.sum()) == 0:
            continue
        zc = clim.where(mask).mean(["lat", "lon"]).values  # 12
        latc = float(clim.lat.broadcast_like(zones).where(mask).mean())
        annual = float(zc.sum())
        peaks = peak_months(zc)
        regime = "bimodal" if len(peaks) >= 2 else "unimodal"
        wins, _ = propose_windows(zc)
        wlab, widx, wfrac = wins[0]
        ax.plot(np.arange(1, 13), zc, "-o", color=colors[z],
                label=f"Zone {z} (~{latc:.1f}°N, {annual:.0f} mm/yr, {regime})")
        rows.append(dict(zone=z, mean_lat=round(latc, 2), annual_mm=round(annual, 0),
                         regime=regime, peak_months=";".join(MONTHS[p] for p in peaks),
                         bimodality=round(float(bi.where(mask).mean()), 3),
                         proposed_window=wlab,
                         window_months=";".join(MONTHS[i] for i in widx),
                         rain_frac_captured=round(wfrac, 2)))
    ax.set_xticks(range(1, 13)); ax.set_xticklabels(MONTHS)
    ax.set_ylabel("Rainfall (mm/month)"); ax.set_xlabel("Month")
    ax.set_title(f"{LABEL} mean annual rainfall cycle by homogeneous zone (CHIRPS v3, 1991-2020)")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(FIG / suffix("seasons_annual_cycle","png"), dpi=150)
    plt.close(fig)

    # ---- regime (bimodality) map ----
    fig, ax = plt.subplots(figsize=(7, 6))
    bi.plot(ax=ax, cmap="RdYlBu_r", cbar_kwargs={"label": "Bimodality index (a2/a1)"})
    ax.set_title("Rainfall regime: bimodality index\n(high = double rainy season, low = single)")
    fig.tight_layout(); fig.savefig(FIG / suffix("seasons_regime_map","png"), dpi=150)
    plt.close(fig)

    # ---- zone map ----
    fig, ax = plt.subplots(figsize=(7, 6))
    zones.plot(ax=ax, cmap="viridis", levels=[-0.5, 0.5, 1.5, 2.5, 3.5],
               cbar_kwargs={"label": "Zone (0=south … 3=north)"})
    ax.set_title("Homogeneous rainfall zones (k-means on annual cycle)")
    fig.tight_layout(); fig.savefig(FIG / suffix("seasons_zone_map","png"), dpi=150)
    plt.close(fig)

    # ---- tables ----
    import csv
    with open(TAB / suffix("seasons_summary","csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    hdr = list(rows[0].keys())
    md = ["| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    for r in rows:
        md.append("| " + " | ".join(str(r[h]) for h in hdr) + " |")
    (TAB / suffix("seasons_summary","md")).write_text("\n".join(md) + "\n")

    print("\n=== SEASONAL PARTITION RESULTS ===")
    for r in rows:
        print(r)
    print("\nfigures ->", FIG)
    print("tables  ->", TAB)


if __name__ == "__main__":
    main()
