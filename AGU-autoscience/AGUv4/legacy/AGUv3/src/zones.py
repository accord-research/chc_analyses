"""zones.py — discover homogeneous forecast zones for Kenya+Somalia from rainfall alone (AGUv3).

The AGUv1/v2 lesson: "region" was an input (admin boxes, then literature-drawn boxes) when it
should be an output. This clusters CHIRPS cells into zones using two feature families jointly:

  1. seasonal-cycle SHAPE — each cell's standardized 12-month climatology (as AGUv0/seasons.py),
  2. interannual CO-VARIABILITY — the cell's loadings on the leading EOFs of monthly anomalies,
     so cells with identical climatology shape but decoupled year-to-year behavior (on/off the
     Walker subsidence branch) land in different zones. Zones are forecast units, not atlas units.

k is selected by STABILITY (year-bootstrap -> refeature -> recluster -> adjusted Rand vs the
full-data labels), not chosen — the zonation must not be a researcher-degrees-of-freedom knob.

Validation targets (stated in advance; the two known gradients are orthogonal, so latitude
banding cannot pass both):
  - Kenya: a MERIDIONAL boundary near ~38E (Lake Victoria / highlands vs eastern drylands),
  - Somalia: a ZONAL boundary near ~6-8N (north vs south-central).
Quantified by the correlation ratio (eta^2) of zone label vs lon and vs lat within each country.

Run in accord-chc after fetch_data.py.
"""
import warnings
from pathlib import Path
warnings.filterwarnings("ignore")

import numpy as np
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"
CLIM = (1991, 2020)
COARSEN = 5                      # 0.05 deg -> 0.25 deg
N_EOF = 5                        # co-variability loadings kept per cell
K_RANGE = range(2, 9)
N_BOOT = 20
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# country bboxes (lat_s, lat_n, lon_w, lon_e) for the orientation statistic only —
# NOT used anywhere in the clustering itself.
COUNTRY = {"Kenya": (-4.7, 5.0, 33.9, 41.9), "Somalia": (-1.7, 12.0, 41.0, 51.4)}


def load():
    da = xr.open_dataset(DATA / "kenya_somalia_chirps_monthly.nc")["precip"]
    da = da.coarsen(lat=COARSEN, lon=COARSEN, boundary="trim").mean()
    return da


def features(da, year_sel=None):
    """(cycle_z block, eof-loading block, good-cell mask, stacked coords) from monthly precip.
    year_sel: optional array of years (with repeats) for bootstrap resampling."""
    if year_sel is not None:
        pieces = [da.sel(time=da["time.year"] == y) for y in year_sel]
        da = xr.concat(pieces, dim="time")
    yrs = da["time"].dt.year
    clim = da.sel(time=(yrs >= CLIM[0]) & (yrs <= CLIM[1]))
    if clim.sizes["time"] == 0:                     # bootstrap sample missed the clim window
        clim = da
    cyc = clim.groupby("time.month").mean("time")   # (12, lat, lon)

    stack = cyc.stack(cell=("lat", "lon")).transpose("cell", "month")
    C = stack.values
    good = np.isfinite(C).all(axis=1) & (C.sum(axis=1) > 1e-3)

    # block 1: standardized cycle shape (timing/shape, not amount)
    X1 = C[good]
    X1 = (X1 - X1.mean(1, keepdims=True)) / (X1.std(1, keepdims=True) + 1e-6)

    # block 2: EOF loadings of standardized monthly anomalies
    anom = (da.groupby("time.month") - da.groupby("time.month").mean("time"))
    A = anom.stack(cell=("lat", "lon")).transpose("cell", "time").values[good]
    A = np.nan_to_num(A / (A.std(1, keepdims=True) + 1e-6))
    U, S, _ = np.linalg.svd(A, full_matrices=False)
    X2 = U[:, :N_EOF]

    z = lambda M: (M - M.mean(0)) / (M.std(0) + 1e-9)
    # equal-weight blocks: unit column variance, then scale by 1/sqrt(ndims)
    X = np.hstack([z(X1) / np.sqrt(X1.shape[1]), z(X2) / np.sqrt(X2.shape[1])])
    return X, good, stack.cell


def cluster(X, k, seed=0):
    return KMeans(n_clusters=k, n_init=10, random_state=seed).fit_predict(X)


def select_k(da, X0):
    """Stability selection: bootstrap years, refeature, recluster, ARI vs full-data labels."""
    years = np.unique(da["time.year"].values)
    rng = np.random.default_rng(0)
    rows = []
    for k in K_RANGE:
        L0 = cluster(X0, k)
        aris = []
        for b in range(N_BOOT):
            ysel = rng.choice(years, size=len(years), replace=True)
            Xb, gb, _ = features(da, year_sel=ysel)
            if Xb.shape[0] == X0.shape[0]:          # same good-cell set (should be)
                aris.append(adjusted_rand_score(L0, cluster(Xb, k, seed=b + 1)))
        rows.append(dict(k=k, ari=float(np.mean(aris)), ari_sd=float(np.std(aris)),
                         sil=float(silhouette_score(X0, L0, sample_size=3000, random_state=0))))
        print(f"k={k}  ARI={rows[-1]['ari']:.3f}±{rows[-1]['ari_sd']:.3f}  sil={rows[-1]['sil']:.3f}",
              flush=True)
    return rows


def peak_months(cyc):
    peaks = []
    for i in range(12):
        prev, nxt = cyc[(i - 1) % 12], cyc[(i + 1) % 12]
        if cyc[i] >= prev and cyc[i] >= nxt and cyc[i] > 0.15 * cyc.max():
            peaks.append(i)
    return peaks


def windows_for(cyc):
    """Bimodal-aware windows: one 3-month window per detected peak (best 3-window containing
    the peak). Fixes the v0 mode where a single >=70%-of-rain window spans both rainy seasons."""
    out = []
    for p in peak_months(cyc):
        best, bs = None, -1
        for s in [(p - 2) % 12, (p - 1) % 12, p]:
            idx = [(s + j) % 12 for j in range(3)]
            if p in idx and cyc[idx].sum() > bs:
                bs, best = cyc[idx].sum(), idx
        out.append(("".join(MONTHS[i][0] for i in best), best))
    return out


def eta2(lab, coord):
    """Correlation ratio: fraction of coordinate variance explained by zone membership."""
    gm = coord.mean()
    ssb = sum(len(c) * (c.mean() - gm) ** 2 for z in np.unique(lab) if len(c := coord[lab == z]))
    return float(ssb / ((coord - gm) ** 2).sum())


def main():
    for d in (FIG, TAB):
        d.mkdir(parents=True, exist_ok=True)
    da = load()
    print("coarsened field", dict(da.sizes), flush=True)
    X, good, cells = features(da)
    print(f"{good.sum()} land cells, {X.shape[1]} features", flush=True)

    stab = select_k(da, X)
    best = max(stab, key=lambda r: r["ari"])["k"]
    print(f"selected k={best} by stability", flush=True)

    lab = cluster(X, best)
    # stable relabel west->east by centroid longitude
    lons = np.array([c[1] for c in cells.values])[good]
    lats = np.array([c[0] for c in cells.values])[good]
    order = {z: i for i, z in enumerate(sorted(np.unique(lab), key=lambda z: lons[lab == z].mean()))}
    lab = np.array([order[z] for z in lab])

    full = np.full(len(cells), np.nan)
    full[good] = lab
    zones = xr.DataArray(full, coords={"cell": cells}, dims="cell").unstack("cell").rename("zone")
    zones.to_netcdf(DATA / "zones.nc")

    # ---- orientation statistic per country ----
    orient = []
    for name, (s, n, w, e) in COUNTRY.items():
        m = (lats >= s) & (lats <= n) & (lons >= w) & (lons <= e)
        orient.append(dict(country=name, eta2_lon=round(eta2(lab[m], lons[m]), 3),
                           eta2_lat=round(eta2(lab[m], lats[m]), 3),
                           organized_by="LON (meridional boundaries)"
                           if eta2(lab[m], lons[m]) > eta2(lab[m], lats[m])
                           else "LAT (zonal boundaries)"))

    # ---- per-zone summary + windows ----
    clim = da.sel(time=(da["time.year"] >= CLIM[0]) & (da["time.year"] <= CLIM[1]))
    cyc_field = clim.groupby("time.month").mean("time")
    dpm = xr.DataArray([31,28.25,31,30,31,30,31,31,30,31,30,31],
                       coords={"month": np.arange(1, 13)}, dims="month")
    rows = []
    fig, ax = plt.subplots(figsize=(9, 5))
    cmap = plt.cm.viridis(np.linspace(0, 0.9, best))
    for z in range(best):
        mask = zones == z
        zc = (cyc_field * dpm).where(mask).mean(["lat", "lon"]).values
        wins = windows_for(zc)
        regime = "bimodal" if len(peak_months(zc)) >= 2 else "unimodal"
        rows.append(dict(zone=z, cells=int(mask.sum()),
                         cen_lat=round(float(lats[lab == z].mean()), 2),
                         cen_lon=round(float(lons[lab == z].mean()), 2),
                         annual_mm=round(float(zc.sum())), regime=regime,
                         windows=" + ".join(w for w, _ in wins)))
        ax.plot(range(1, 13), zc, "-o", color=cmap[z],
                label=f"z{z} ({rows[-1]['cen_lat']}N,{rows[-1]['cen_lon']}E, {regime}, {rows[-1]['windows']})")
    ax.set_xticks(range(1, 13)); ax.set_xticklabels(MONTHS)
    ax.set_ylabel("mm/month"); ax.legend(fontsize=7); ax.grid(alpha=0.3)
    ax.set_title(f"Annual cycle by discovered zone (k={best}, CHIRPS {CLIM[0]}-{CLIM[1]})")
    fig.tight_layout(); fig.savefig(FIG / "annual_cycles.png", dpi=150); plt.close(fig)

    # ---- zone map with borders ----
    import cartopy.crs as ccrs, cartopy.feature as cfeature
    fig = plt.figure(figsize=(8, 7))
    ax = plt.axes(projection=ccrs.PlateCarree())
    zones.plot(ax=ax, cmap="viridis", levels=np.arange(-0.5, best + 0.5),
               transform=ccrs.PlateCarree(), cbar_kwargs={"label": "zone (west->east)"})
    ax.add_feature(cfeature.BORDERS, lw=0.8); ax.add_feature(cfeature.COASTLINE, lw=0.8)
    ax.axvline(38, color="r", ls=":", lw=1); ax.axhline(7, color="r", ls=":", lw=1)
    ax.set_title(f"Discovered forecast zones, k={best} (red dots: the expected ~38E / ~7N splits)")
    fig.tight_layout(); fig.savefig(FIG / "zone_map.png", dpi=150); plt.close(fig)

    # ---- stability figure ----
    fig, ax = plt.subplots(figsize=(6, 4))
    ks = [r["k"] for r in stab]
    ax.errorbar(ks, [r["ari"] for r in stab], yerr=[r["ari_sd"] for r in stab], marker="o", label="bootstrap ARI")
    ax.plot(ks, [r["sil"] for r in stab], marker="s", ls="--", label="silhouette")
    ax.axvline(best, color="r", ls=":"); ax.set_xlabel("k"); ax.legend(); ax.grid(alpha=0.3)
    ax.set_title("Zone-count stability selection")
    fig.tight_layout(); fig.savefig(FIG / "stability.png", dpi=150); plt.close(fig)

    # ---- tables ----
    md = ["# Discovered zones (AGUv3)", "",
          f"k = {best} selected by year-bootstrap stability (ARI), {N_BOOT} resamples.", "",
          "| " + " | ".join(rows[0].keys()) + " |", "|" + "---|" * len(rows[0])]
    md += ["| " + " | ".join(str(v) for v in r.values()) + " |" for r in rows]
    md += ["", "## Orientation (eta^2 of zone label vs coordinate, within-country)", "",
           "| country | eta2_lon | eta2_lat | organized by |", "|---|---|---|---|"]
    md += [f"| {o['country']} | {o['eta2_lon']} | {o['eta2_lat']} | {o['organized_by']} |" for o in orient]
    md += ["", "| k | ARI | sd | silhouette |", "|---|---|---|---|"]
    md += [f"| {r['k']} | {r['ari']:.3f} | {r['ari_sd']:.3f} | {r['sil']:.3f} |" for r in stab]
    (TAB / "zones_summary.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
