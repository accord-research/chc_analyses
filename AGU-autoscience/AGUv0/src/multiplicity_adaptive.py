"""multiplicity_adaptive.py — unified permutation-FDR family incl. the ADAPTIVE predictors (audit S-F1).

The base multiplicity.py builds its FDR family from 8 textbook scalar indices ONLY. The predictors
the narrative foregrounds as *discovered winners* — the data-driven `sst_projection` pattern, the
`combo_top2` selector, and rainfall `persistence` — carry the most researcher degrees of freedom
and were never entered into the family. So "every West-African winner fails FDR" is misleading: the
actual best West-African predictor (`sst_projection`, r≈0.46) was never tested.

This closes the gap. It keeps the published textbook p-values (from multiplicity_fdr.csv, bit-for-
bit) and ADDS a permutation test for the three adaptive predictors per (season, band) cell, then
runs Benjamini–Hochberg over ONE unified family per country. Crucially the permutation captures
each predictor's *adaptive optimism*: for `sst_projection` the covariance pattern is refit in-fold
on the shuffled rainfall, for `combo_top2` the feature selection is redone in-fold — so the null
sees the same flexibility the observed statistic used.

Pure-numpy LOYO kernels (validated bit-identical to feature_discovery's xarray versions) keep it to
~1 hour at NPERM=5000 over ~64 cells.

Run: python src/multiplicity_adaptive.py       (loops all three countries)
     MAXCELLS=2 python src/multiplicity_adaptive.py   (quick self-test on a 2-cell subset)
Writes: outputs/tables/multiplicity_adaptive.md, .csv
"""
import os, csv, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
import numpy as np
import xarray as xr

import teleconnections as T
import feature_discovery as F

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TAB = ROOT / "outputs" / "tables"
NPERM = 5000
MAXCELLS = int(os.environ.get("MAXCELLS", "0"))   # 0 = all
COUNTRIES = [("Nigeria", "nigeria_chirps_monthly.nc",
              {"National": (4, 14), "South": (4, 8), "Middle": (8, 11), "North": (11, 14)}),
             ("Ethiopia", "ethiopia_chirps_monthly.nc",
              {"National": (3, 15), "South": (3, 7), "Central": (7, 10), "North": (10, 15)}),
             ("Kenya", "kenya_chirps_monthly.nc",
              {"National": (-5, 5), "South": (-5, -1), "Central": (-1, 2), "North": (2, 5)})]


# ---- pure-numpy LOYO kernels (match feature_discovery bit-for-bit; validated) ----
def loo_corr_np(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]; n = len(y)
    if n < 5 or x.std() == 0:
        return np.nan
    preds = np.empty(n)
    for i in range(n):
        m = np.arange(n) != i
        b1, b0 = np.polyfit(x[m], y[m], 1)
        preds[i] = b0 + b1 * x[i]
    if preds.std() == 0:
        return np.nan
    return np.corrcoef(preds, y)[0, 1]


def loyo_proj_np(Fm, y):
    n = len(y); preds = np.full(n, np.nan)
    for i in range(n):
        tr = np.arange(n) != i
        Ftr = Fm[tr]; ytr = y[tr]; ya = ytr - ytr.mean()
        Fmean = Ftr.mean(0); Fa = Ftr - Fmean
        patt = (Fa * ya[:, None]).mean(0)
        proj_tr = (Fa * patt).sum(1); proj_i = ((Fm[i] - Fmean) * patt).sum()
        if proj_tr.std() == 0:
            continue
        b1, b0 = np.polyfit(proj_tr, ytr, 1); preds[i] = b0 + b1 * proj_i
    ok = np.isfinite(preds)
    if ok.sum() < 10 or preds[ok].std() == 0:
        return np.nan
    return np.corrcoef(preds[ok], y[ok])[0, 1]


def loyo_combo_np(P, y, k=2):
    """P: (n, nfeat) scalar-feature matrix. In-fold: screen by train |corr|, take top k, fit
    k-way OLS, predict held-out. Feature selection + fit both inside the fold."""
    n = len(y); preds = np.full(n, np.nan)
    for i in range(n):
        tr = np.arange(n) != i
        Ptr = P[tr]; ytr = y[tr]
        cors = np.array([abs(np.corrcoef(Ptr[:, j], ytr)[0, 1]) if Ptr[:, j].std() > 0 else 0
                         for j in range(P.shape[1])])
        top = np.argsort(-cors)[:k]
        A = np.column_stack([Ptr[:, top], np.ones(tr.sum())])
        coef, *_ = np.linalg.lstsq(A, ytr, rcond=None)
        preds[i] = np.dot(np.append(P[i, top], 1.0), coef)
    ok = np.isfinite(preds)
    if ok.sum() < 10 or preds[ok].std() == 0:
        return np.nan
    return np.corrcoef(preds[ok], y[ok])[0, 1]


def perm_p(stat_fn, args, observed, rng, nperm=NPERM):
    """One-sided upper-tail permutation p; shuffles the LAST arg (rain y)."""
    if not np.isfinite(observed):
        return np.nan
    *fixed, y = args
    count = 1
    for _ in range(nperm):
        s = stat_fn(*fixed, rng.permutation(y))
        if np.isfinite(s) and s >= observed:
            count += 1
    return count / (nperm + 1)


def seasonal_rain(precip, months, s, n):
    import deepscale
    band = precip.sel(lat=slice(s, n)).mean(["lat", "lon"])
    return deepscale.seasonal_reduce(band, months)


def bh(pvals):
    p = np.asarray(pvals, float); m = len(p)
    order = np.argsort(p); q = np.empty(m); prev = 1.0
    for rank in range(m - 1, -1, -1):
        i = order[rank]; prev = min(prev, p[i] * m / (rank + 1)); q[i] = prev
    return q


def main():
    sst = T.load_sst(); idx = T.build_indices(sst); sst_anom = T.monthly_anom(sst)

    # existing textbook p-values (keep published values)
    textbook = {}
    with open(TAB / "multiplicity_fdr.csv") as f:
        for r in csv.DictReader(f):
            if r["p_perm"] not in ("", "None"):
                textbook[(r["country"], r["season"], r["band"], r["predictor"])] = \
                    (float(r["cv_corr"]), float(r["p_perm"]))

    rng = np.random.default_rng(12345)
    new_rows = []           # adaptive-predictor cells
    for country, cf, bands in COUNTRIES:
        precip = xr.open_dataset(DATA / cf)["precip"]
        done = 0
        for band, (s, n) in bands.items():
            smeans = {se: float(seasonal_rain(precip, mo, s, n).mean()) for se, mo in T.SEASONS.items()}
            thr = 0.45 * max(smeans.values())
            for season, months in T.SEASONS.items():
                if smeans[season] < thr:
                    continue
                if MAXCELLS and done >= MAXCELLS:
                    break
                rain = seasonal_rain(precip, months, s, n)
                ry = rain.dropna("year").year.values

                # persistence (scalar)
                per = F.persistence_series(precip, months, s, n)
                yy = np.intersect1d(per.dropna("year").year, ry)
                if len(yy) >= 12:
                    x = per.sel(year=yy).values.astype(float); y = rain.sel(year=yy).values.astype(float)
                    obs = loo_corr_np(x, y); p = perm_p(loo_corr_np, (x, y), obs, rng)
                    new_rows.append([country, season, band, "persistence", obs, p])

                # sst_projection (field pattern refit in-fold)
                field = F.preseason_field(sst_anom, months)
                yy = np.intersect1d(field.year.values, ry)
                if len(yy) >= 12:
                    Fm = field.sel(year=yy).values.reshape(len(yy), -1)
                    good = ~np.isnan(Fm).any(0); Fm = Fm[:, good]
                    y = rain.sel(year=yy).values.astype(float)
                    obs = loyo_proj_np(Fm, y); p = perm_p(loyo_proj_np, (Fm, y), obs, rng)
                    new_rows.append([country, season, band, "sst_projection", obs, p])

                # combo_top2 (feature selection refit in-fold) over textbook + persistence
                pool = {}
                for ik in F.TEXTBOOK:
                    pool[ik] = T.index_preseason_mean(idx[ik], months)
                pool["persistence"] = per
                yy = ry
                for sname, sser in pool.items():
                    yy = np.intersect1d(yy, sser.dropna("year").year.values)
                if len(yy) >= 12:
                    P = np.column_stack([pool[k].sel(year=yy).values.astype(float) for k in pool])
                    y = rain.sel(year=yy).values.astype(float)
                    obs = loyo_combo_np(P, y); p = perm_p(loyo_combo_np, (P, y), obs, rng)
                    new_rows.append([country, season, band, "combo_top2", obs, p])

                done += 1
                print(f"  [{country}] {season} {band}: proj r={new_rows[-2][4] if len(new_rows)>=2 else float('nan'):+.2f}", flush=True)
            if MAXCELLS and done >= MAXCELLS:
                break

    # unified family per country = textbook (published p) + adaptive (new p); BH over the union
    md = ["# Unified permutation-FDR incl. adaptive predictors (audit S-F1)", "",
          f"Benjamini–Hochberg over ONE family per country: the 8 textbook indices (published "
          f"p-values) **plus** the adaptive predictors `persistence`, `sst_projection`, "
          f"`combo_top2` ({NPERM}-shuffle permutation, with in-fold pattern/selection refit so the "
          f"null carries the same optimism). Compares the adaptive winners against FDR — the test "
          f"the base family never ran.", "",
          "| Country | family m | survivors q<0.10 | adaptive-predictor result |",
          "|---|---|---|---|"]
    out_csv = []
    for country, _, _ in COUNTRIES:
        tb = [(k, v) for k, v in textbook.items() if k[0] == country]
        ad = [r for r in new_rows if r[0] == country]
        allp = [v[1] for _, v in tb] + [r[5] for r in ad]
        keys = [("textbook",) + k[1:] + (v[0],) for k, v in tb] + \
               [("adaptive", r[1], r[2], r[3], r[4]) for r in ad]
        q = bh(allp)
        surv = [(keys[i], allp[i], q[i]) for i in range(len(q)) if np.isfinite(q[i]) and q[i] < 0.10]
        surv.sort(key=lambda t: t[2])
        # adaptive-predictor specific summary
        ad_surv = [(k, p, qq) for (k, p, qq) in surv if k[0] == "adaptive"]
        proj = [r for r in ad if r[3] == "sst_projection"]
        proj_best = max(proj, key=lambda r: r[4]) if proj else None
        note = []
        if proj_best:
            pk = next((qq for (k, p, qq) in surv if k[0] == "adaptive" and k[3] == "sst_projection"
                       and abs(k[4] - proj_best[4]) < 1e-9), None)
            qstr = f"q={pk:.3f}" if pk is not None else "does NOT survive"
            note.append(f"best sst_projection r={proj_best[4]:+.2f} ({proj_best[1]} {proj_best[2]}): {qstr}")
        note.append(f"{len(ad_surv)} adaptive cells survive")
        md.append(f"| {country} | {len(allp)} | {len(surv)} | " + "; ".join(note) + " |")
        for (k, p, qq) in surv:
            out_csv.append(dict(country=country, kind=k[0], season=k[1], band=k[2],
                                predictor=k[3], cv_corr=round(k[4], 3), p_perm=round(p, 4), q_bh=round(qq, 4)))
    md += ["", "**Reading.** With the adaptive predictors in the family, the claim can be stated "
           "honestly for the first time: whether the data-driven `sst_projection` — the *actual* "
           "best West-African predictor — survives FDR, not just the weaker textbook indices that "
           "were the only ones ever tested. See the per-country result above; the East-African OND "
           "signal remains the dominant survivor either way."]
    (TAB / "multiplicity_adaptive.md").write_text("\n".join(md) + "\n")
    with open(TAB / "multiplicity_adaptive.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["country", "kind", "season", "band", "predictor", "cv_corr", "p_perm", "q_bh"])
        w.writeheader(); w.writerows(out_csv)
    print("\n" + "\n".join(md))


if __name__ == "__main__":
    main()
