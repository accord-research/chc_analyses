"""hierarchy.py — examine the stable zonation hierarchy beyond the max-ARI level (AGUv3).

Max-ARI selection has a known coarseness bias (fewer clusters are trivially more stable), and
k=2 and k=3 both clear a >=0.9 bootstrap-ARI bar here. So this renders the k=3 and k=4 levels
as supplementary structure — maps, per-country orientation, per-zone windows, and the WVG
dry-tail evaluation — without changing the pre-stated k=2 selection. The questions at the
finer levels: does northern Somalia split out (the zonal ~6-8N boundary), and does a purer
eastern core recover the AGUv2 hand-box MAM dry-tail rates (0.79 / 0.77)?
"""
import warnings
from pathlib import Path
warnings.filterwarnings("ignore")

import numpy as np
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import zones as Z
import wvg_by_zone as W

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"
LEVELS = (3, 4)


def zone_da(lab, good, cells):
    full = np.full(len(cells), np.nan)
    full[good] = lab
    return xr.DataArray(full, coords={"cell": cells}, dims="cell").unstack("cell").rename("zone")


def main():
    da = Z.load()
    X, good, cells = Z.features(da)
    lons = np.array([c[1] for c in cells.values])[good]
    lats = np.array([c[0] for c in cells.values])[good]
    boxes = W._monthly_box_anoms()
    clim = da.sel(time=(da["time.year"] >= Z.CLIM[0]) & (da["time.year"] <= Z.CLIM[1]))
    cyc_field = clim.groupby("time.month").mean("time")
    dpm = xr.DataArray([31,28.25,31,30,31,30,31,31,30,31,30,31],
                       coords={"month": np.arange(1, 13)}, dims="month")

    import cartopy.crs as ccrs, cartopy.feature as cfeature
    md = ["# Zonation hierarchy (AGUv3 supplement)", "",
          "k=2 is the pre-stated max-ARI selection; k=3 also clears ARI>=0.9. Finer levels below.", ""]

    for k in LEVELS:
        lab = Z.cluster(X, k)
        order = {z: i for i, z in enumerate(sorted(np.unique(lab), key=lambda z: lons[lab == z].mean()))}
        lab = np.array([order[z] for z in lab])
        zd = zone_da(lab, good, cells)
        zd.to_netcdf(ROOT / "data" / f"zones_k{k}.nc")

        fig = plt.figure(figsize=(8, 7))
        ax = plt.axes(projection=ccrs.PlateCarree())
        zd.plot(ax=ax, cmap="viridis", levels=np.arange(-0.5, k + 0.5),
                transform=ccrs.PlateCarree(), cbar_kwargs={"label": "zone (west->east)"})
        ax.add_feature(cfeature.BORDERS, lw=0.8); ax.add_feature(cfeature.COASTLINE, lw=0.8)
        ax.axvline(38, color="r", ls=":", lw=1); ax.axhline(7, color="r", ls=":", lw=1)
        ax.set_title(f"Zonation at k={k}")
        fig.tight_layout(); fig.savefig(FIG / f"zone_map_k{k}.png", dpi=150); plt.close(fig)

        md += [f"## k = {k}", "", "| country | eta2_lon | eta2_lat | organized by |", "|---|---|---|---|"]
        for name, (s, n, w, e) in Z.COUNTRY.items():
            m = (lats >= s) & (lats <= n) & (lons >= w) & (lons <= e)
            el, ea = Z.eta2(lab[m], lons[m]), Z.eta2(lab[m], lats[m])
            md.append(f"| {name} | {el:.3f} | {ea:.3f} | {'LON' if el > ea else 'LAT'} |")
        md.append("")

        hdr_done = False
        for zi in range(k):
            mask = zd == zi
            zc = (cyc_field * dpm).where(mask).mean(["lat", "lon"]).values
            wins = Z.windows_for(zc)
            cand = {wl: idx for wl, idx in wins}
            cand.setdefault("MAM", [2, 3, 4]); cand.setdefault("OND", [9, 10, 11])
            zrain = da.where(mask).mean(["lat", "lon"])
            for wlab, widx in cand.items():
                sub = zrain.sel(time=zrain["time.month"].isin([i + 1 for i in widx]))
                tot = sub.groupby("time.year").sum("time")
                yrs = tot.year.values; yrs = yrs[(yrs >= 1982) & (yrs <= 2023)]
                y = tot.sel(year=yrs).values.astype(float); y = (y - y.mean()) / y.std()
                n34 = W._preseason(boxes["nino34"], widx[0], yrs)
                wv = W._preseason(boxes["wv"], widx[0], yrs)
                zf = lambda a: (a - a.mean()) / a.std()
                x = zf(n34) - zf(wv); dry_score = -x
                below_m = (y < 0).astype(int)
                from sklearn.metrics import roc_auc_score
                strong = dry_score > np.quantile(dry_score, 2 / 3)
                lanina = zf(n34) < -0.5; joint = strong & lanina
                pred = W._loyo_pred(x, y); ok = np.isfinite(pred)
                row = dict(zone=zi, cells=int(mask.sum().item()),
                           cen=f"{lats[lab == zi].mean():.1f}N,{lons[lab == zi].mean():.1f}E",
                           window=wlab, disc="y" if wlab in {wl for wl, _ in wins} else "-",
                           sym=f"{np.corrcoef(pred[ok], y[ok])[0, 1]:+.2f}",
                           droc=f"{roc_auc_score(below_m, dry_score):.2f}",
                           pclim=f"{below_m.mean():.2f}", pneg=f"{below_m[strong].mean():.2f}",
                           pnegla=f"{below_m[joint].mean():.2f}(n={joint.sum()})" if joint.sum() >= 3 else "-")
                if not hdr_done:
                    md += ["| " + " | ".join(row.keys()) + " |", "|" + "---|" * len(row)]
                    hdr_done = True
                md.append("| " + " | ".join(str(v) for v in row.values()) + " |")
                print(k, row, flush=True)
        md.append("")

    (TAB / "hierarchy.md").write_text("\n".join(md) + "\n")
    print("wrote", TAB / "hierarchy.md")


if __name__ == "__main__":
    main()
