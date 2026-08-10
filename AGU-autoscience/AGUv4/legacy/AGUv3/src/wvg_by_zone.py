"""wvg_by_zone.py — asymmetric WVG evaluation per discovered zone (AGUv3).

For each zone from zones.py and each of its discovered rainy-season windows (plus MAM and OND as
common candidates for cross-zone comparability), evaluate the pre-season Western-V Gradient the
way AGUv2 established: report the symmetric all-years LOYO correlation (the metric that hides the
signal) AND the dry-tail / La-Nina-conditional metrics (the ones that recover it).

Index machinery follows AGUv2/src/recover.py (same boxes, same ERSST, same conventions).
Pre-season = the 2 calendar months immediately before the window, year-wrap-safe.

Acceptance criteria (stated in advance):
  - the eastern (eHorn-like) zones reproduce ~0.75-0.8 dry-tail conditional rates for MAM,
  - the western-Kenya zone shows a WEAK/no dry-tail MAM signal (the confirming contrast).
"""
import warnings
from pathlib import Path
warnings.filterwarnings("ignore")

import numpy as np
import xarray as xr
from sklearn.metrics import roc_auc_score

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from zones import load, windows_for, peak_months, MONTHS, CLIM

ROOT = Path(__file__).resolve().parents[1]
ERSST = ROOT.parent / "AGUv0" / "data" / "ersst_monthly.nc"
TAB = ROOT / "outputs" / "tables"

BOX = {"nino34": (-5, 5, 190, 240), "wv": (5, 20, 130, 170)}   # as AGUv2
V2_REFERENCE = {"MAM": (0.79, 0.77)}   # hand-box eHorn (P(dry|-WVG), P(dry|-WVG&LaNina)) for comparison


def _monthly_box_anoms():
    ds = xr.open_dataset(ERSST); sst = ds["sst"]
    if "zlev" in sst.dims:
        sst = sst.squeeze("zlev")
    lon = xr.where(sst.lon < 0, sst.lon + 360, sst.lon)
    sst = sst.assign_coords(lon=lon).sortby("lon").sortby("lat")
    clim = sst.sel(time=slice(f"{CLIM[0]}-01", f"{CLIM[1]}-12")).groupby("time.month").mean("time")
    an = sst.groupby("time.month") - clim
    out = {}
    for name, (s, n, w, e) in BOX.items():
        sub = an.sel(lat=slice(s, n), lon=slice(w, e))
        out[name] = sub.weighted(np.cos(np.deg2rad(sub.lat))).mean(["lat", "lon"])
    return out


def _preseason(series, window_start, years):
    """Mean of `series` over the 2 months before month index `window_start` (0-based),
    labeled to the window's year (months that wrap into the prior calendar year shift +1)."""
    vals = []
    for y in years:
        acc = []
        for off in (2, 1):
            m = (window_start - off) % 12
            yy = y - 1 if m > window_start else y
            v = series.sel(time=f"{yy}-{m + 1:02d}")
            acc.append(float(v.mean()))          # 1-element time slice -> scalar
        vals.append(np.mean(acc))
    return np.array(vals)


def _loyo_pred(x, y):
    n = len(x); pred = np.full(n, np.nan)
    for i in range(n):
        m = np.arange(n) != i
        if x[m].std() == 0: continue
        b1, b0 = np.polyfit(x[m], y[m], 1); pred[i] = b0 + b1 * x[i]
    return pred


def main():
    da = load()
    zones = xr.open_dataset(ROOT / "data" / "zones.nc")["zone"]
    boxes = _monthly_box_anoms()

    dpm_clim = da.sel(time=(da["time.year"] >= CLIM[0]) & (da["time.year"] <= CLIM[1]))
    cyc_field = dpm_clim.groupby("time.month").mean("time")

    nz = int(zones.max()) + 1
    rows = []
    for zi in range(nz):
        mask = zones == zi
        zc = cyc_field.where(mask).mean(["lat", "lon"]).values
        wins = windows_for(zc)
        cand = {w: idx for w, idx in wins}
        cand.setdefault("MAM", [2, 3, 4]); cand.setdefault("OND", [9, 10, 11])
        zrain = da.where(mask).mean(["lat", "lon"])

        for wlab, widx in cand.items():
            start = widx[0]
            sub = zrain.sel(time=zrain["time.month"].isin([i + 1 for i in widx]))
            # label windows by the year of their first month (windows here don't wrap)
            tot = sub.groupby("time.year").sum("time")
            yrs = tot.year.values
            yrs = yrs[(yrs >= 1982) & (yrs <= 2023)]           # need prior-year pre-season SSTs
            y = tot.sel(year=yrs).values.astype(float)
            y = (y - y.mean()) / y.std()

            n34 = _preseason(boxes["nino34"], start, yrs)
            wv = _preseason(boxes["wv"], start, yrs)
            z = lambda a: (a - a.mean()) / a.std()
            x = z(n34) - z(wv)                                  # WVG
            dry_score = -x                                      # strong-negative WVG -> dry
            below_m = (y < 0).astype(int)

            pred = _loyo_pred(x, y); ok = np.isfinite(pred)
            strong = dry_score > np.quantile(dry_score, 2 / 3)
            lanina = z(n34) < -0.5
            joint = strong & lanina
            rows.append(dict(
                zone=zi, window=wlab, discovered=wlab in {w for w, _ in wins},
                n=len(yrs),
                sym_corr=round(float(np.corrcoef(pred[ok], y[ok])[0, 1]), 2),
                dry_roc=round(float(roc_auc_score(below_m, dry_score)), 2),
                p_dry_clim=round(float(below_m.mean()), 2),
                p_dry_negwvg=round(float(below_m[strong].mean()), 2),
                p_dry_negwvg_lanina=round(float(below_m[joint].mean()), 2) if joint.sum() >= 3 else None,
                n_joint=int(joint.sum())))
            print(rows[-1], flush=True)

    TAB.mkdir(parents=True, exist_ok=True)
    hdr = list(rows[0].keys())
    md = ["# WVG dry-tail skill by discovered zone (AGUv3)", "",
          "Pre-season WVG = z(Nino3.4) - z(WesternV) over the 2 months before each window. "
          "`sym_corr` = the symmetric all-years LOYO metric (hides the signal); `p_dry_negwvg` = "
          "P(below-median | strong-negative WVG); `p_dry_negwvg_lanina` adds the La-Nina condition. "
          f"AGUv2 hand-box eHorn reference for MAM: {V2_REFERENCE['MAM']}.", "",
          "| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    md += ["| " + " | ".join("-" if r[h] is None else str(r[h]) for h in hdr) + " |" for r in rows]
    (TAB / "wvg_by_zone.md").write_text("\n".join(md) + "\n")
    print("wrote", TAB / "wvg_by_zone.md")


if __name__ == "__main__":
    main()
