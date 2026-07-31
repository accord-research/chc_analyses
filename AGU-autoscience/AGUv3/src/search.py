"""search.py — tensor search over discovered zones (AGUv3).

The v1 search ran predictor_source x domain x transform x method x eof x lead over FIXED country
boxes with a symmetric metric — and mislabeled the eastern Horn. This re-runs the searchable part
with the two v2/v3 corrections wired in as axes:

  zone (discovered, k=4)  x  window (discovered per zone, + MAM/OND candidates)
  x  index (nino34, iod, wpg, wvg, iwhg — AGUv1 definitions)  x  lead (0-3 months)
  x  evaluation mode (symmetric Pearson | dry-tail AUC)

All cells share one permutation null (1000 year-shuffles) and one Benjamini-Hochberg family —
including, implicitly, the zonation itself, since zones enter only through this family. This is
the obs-index (perfect-prognosis) slice of the v1 tensor. The gcm_index / MOS / CCA-field axes
are deferred until the CCSR restoration settles in the local libraries.

Lead L means the 2-month index window ends L+1 months before the season starts
(L=0 reproduces the v2 convention: Jan-Feb before MAM).
"""
import warnings
from pathlib import Path
warnings.filterwarnings("ignore")

import numpy as np
import xarray as xr

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import zones as Z

ROOT = Path(__file__).resolve().parents[1]
ERSST = ROOT.parent / "AGUv0" / "data" / "ersst_monthly.nc"
TAB = ROOT / "outputs" / "tables"

INDEX_NAMES = ("nino34", "iod", "wpg", "wvg", "iwhg")
_BOX = {"nino34": (-5, 5, 190, 240), "iod_w": (-10, 10, 50, 70), "iod_e": (-10, 0, 90, 110),
        "wpac": (-5, 5, 130, 150), "wv": (5, 20, 130, 170)}          # AGUv1 indices.py
LEADS = (0, 1, 2, 3)
N_PERM = 1000
FDR_ALPHA = 0.10
YEARS = np.arange(1982, 2024)


def monthly_boxes():
    ds = xr.open_dataset(ERSST); sst = ds["sst"]
    if "zlev" in sst.dims:
        sst = sst.squeeze("zlev")
    lon = xr.where(sst.lon < 0, sst.lon + 360, sst.lon)
    sst = sst.assign_coords(lon=lon).sortby("lon").sortby("lat")
    clim = sst.sel(time=slice(f"{Z.CLIM[0]}-01", f"{Z.CLIM[1]}-12")).groupby("time.month").mean("time")
    an = sst.groupby("time.month") - clim
    out = {}
    for name, (s, n, w, e) in _BOX.items():
        sub = an.sel(lat=slice(s, n), lon=slice(w, e))
        out[name] = sub.weighted(np.cos(np.deg2rad(sub.lat))).mean(["lat", "lon"])
    return out


def pre_window(series, start, lead, years):
    """2-month mean of `series` ending lead+1 months before month index `start` (0-based)."""
    vals = []
    for y in years:
        acc = []
        for off in (2 + lead, 1 + lead):
            m = (start - off) % 12
            yy = y - 1 if m > start else y
            acc.append(float(series.sel(time=f"{yy}-{m + 1:02d}").mean()))
        vals.append(np.mean(acc))
    return np.array(vals)


def make_index(boxes, name, start, lead, years):
    b = {k: pre_window(v, start, lead, years) for k, v in boxes.items()}
    z = lambda a: (a - a.mean()) / a.std()
    iod = b["iod_w"] - b["iod_e"]
    if name == "nino34": return b["nino34"]
    if name == "iod": return iod
    if name == "wpg": return z(b["wpac"]) - z(b["nino34"])
    if name == "wvg": return z(b["nino34"]) - z(b["wv"])
    if name == "iwhg": return 12 + 323 * iod - 193 * b["wpac"] + 94 * b["nino34"]


def auc_from_ranks(dry, ranks):
    n1 = dry.sum(); n0 = len(dry) - n1
    if n1 == 0 or n0 == 0: return np.nan
    return (ranks[dry.astype(bool)].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def bh(pvals):
    p = np.asarray(pvals); n = len(p); order = np.argsort(p)
    q = np.empty(n); prev = 1.0
    for rank in range(n - 1, -1, -1):
        i = order[rank]
        prev = min(prev, p[i] * n / (rank + 1)); q[i] = prev
    return q


def main():
    da = Z.load()
    zones = xr.open_dataset(ROOT / "data" / "zones_k4.nc")["zone"]
    boxes = monthly_boxes()
    clim = da.sel(time=(da["time.year"] >= Z.CLIM[0]) & (da["time.year"] <= Z.CLIM[1]))
    cyc_field = clim.groupby("time.month").mean("time")
    dpm = xr.DataArray([31,28.25,31,30,31,30,31,31,30,31,30,31],
                       coords={"month": np.arange(1, 13)}, dims="month")

    rng = np.random.default_rng(0)
    perms = np.array([rng.permutation(len(YEARS)) for _ in range(N_PERM)])

    rows = []
    for zi in range(int(zones.max()) + 1):
        mask = zones == zi
        zc = (cyc_field * dpm).where(mask).mean(["lat", "lon"]).values
        cand = {wl: idx for wl, idx in Z.windows_for(zc)}
        cand.setdefault("MAM", [2, 3, 4]); cand.setdefault("OND", [9, 10, 11])
        zrain = da.where(mask).mean(["lat", "lon"])
        for wlab, widx in cand.items():
            sub = zrain.sel(time=zrain["time.month"].isin([i + 1 for i in widx]))
            tot = sub.groupby("time.year").sum("time")
            y = tot.sel(year=YEARS).values.astype(float)
            y = (y - y.mean()) / y.std()
            dry = (y < 0).astype(int)
            yz = (y - y.mean()) / y.std()
            for name in INDEX_NAMES:
                for lead in LEADS:
                    x = make_index(boxes, name, widx[0], lead, YEARS)
                    xz = (x - x.mean()) / x.std()
                    ranks = np.argsort(np.argsort(-x)) + 1.0     # rank of -x: high rank = low index
                    r = float(np.mean(xz * yz))
                    auc = auc_from_ranks(dry, ranks)             # dry discrimination by NEGATIVE index
                    # shared permutation null (two-sided on both metrics)
                    null_r = np.abs((yz[perms] @ xz) / len(YEARS))
                    null_auc = np.abs(np.array([auc_from_ranks(dry[p], ranks) for p in perms]) - 0.5)
                    p_r = (1 + (null_r >= abs(r)).sum()) / (N_PERM + 1)
                    p_a = (1 + (null_auc >= abs(auc - 0.5)).sum()) / (N_PERM + 1)
                    base = dict(zone=zi, window=wlab, index=name, lead=lead)
                    rows.append(dict(base, mode="sym", stat=round(r, 2), p=p_r))
                    rows.append(dict(base, mode="dry_tail", stat=round(auc, 2), p=p_a))
        print(f"zone {zi} done", flush=True)

    q = bh([r["p"] for r in rows])
    for r, qi in zip(rows, q):
        r["q"] = round(float(qi), 3)
    surv = sorted([r for r in rows if r["q"] <= FDR_ALPHA], key=lambda r: r["q"])

    hdr = ["zone", "window", "index", "lead", "mode", "stat", "p", "q"]
    md = ["# Tensor search over discovered zones (AGUv3)", "",
          f"{len(rows)} cells: zone(4) x window(discovered + MAM/OND) x index(5) x lead(0-3) x "
          f"mode(sym Pearson | dry-tail AUC). One shared permutation null ({N_PERM} year-shuffles), "
          f"one BH family, alpha={FDR_ALPHA}. `stat` for dry_tail is AUC of the NEGATIVE index for "
          "below-median rainfall (0.5 = no skill; <0.5 means dry risk sits on the positive side). "
          "Perfect-prognosis obs indices; gcm_index/MOS/CCA axes deferred.", "",
          f"**{len(surv)} / {len(rows)} cells survive FDR.**", "",
          "| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    md += ["| " + " | ".join(str(r[h]) for h in hdr) + " |" for r in surv]
    md += ["", "## Best surviving config per zone-window (the discovered recipe)", "",
           "| zone | window | recipe | stat | q |", "|---|---|---|---|---|"]
    seen = set()
    for r in surv:
        key = (r["zone"], r["window"])
        if key in seen: continue
        seen.add(key)
        md.append(f"| {r['zone']} | {r['window']} | {r['index']} lead-{r['lead']} ({r['mode']}) "
                  f"| {r['stat']} | {r['q']} |")
    TAB.mkdir(parents=True, exist_ok=True)
    (TAB / "search_results.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[:14]))
    print(f"... wrote {TAB / 'search_results.md'} ({len(surv)} survivors)")


if __name__ == "__main__":
    main()
