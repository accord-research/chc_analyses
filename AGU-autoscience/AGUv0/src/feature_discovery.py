"""
feature_discovery.py — discover and rank predictors per season and subgeography.

The screen in teleconnections.py ranks a FIXED list of textbook SST indices. This module goes
further: it treats predictor choice as a search and, for every (season, zone) target, ranks a
mixed pool of candidate features by *honest* leave-one-year-out (LOYO) cross-validated skill:

  - textbook SST indices (nino34, atl3, tna, tsa, atl_grad, iod_dmi, wvg2, wvg3)
  - a DATA-DRIVEN "SST projection" predictor: the pre-season SST covariance pattern with the
    target, refit on the training years INSIDE each CV fold (so discovery is cross-validated,
    not snooped), then projected onto the held-out year
  - PERSISTENCE: antecedent zone rainfall over the pre-season months (a non-SST covariate)

The winner per (season, zone) is the "discovered approach" for that place and time — different
seasons and subgeographies get different predictors, read straight off the hindcast archive.
The WVG is just one row in the pool; nothing privileges it.

Skill metric: LOYO cross-validated correlation between predicted and observed zone-mean
seasonal rainfall (deterministic), comparable across all predictors.

Outputs
  outputs/tables/features_leaderboard.csv     (season, band, predictor, cv_corr) full grid
  outputs/tables/features_best.md             best predictor per (season, band)
  outputs/figures/features_cv_skill_<BAND>.png  predictor x season CV-skill heatmap

Run in accord-chc after fetch_data.py.
"""
import warnings, csv, sys
from pathlib import Path
from itertools import product
warnings.filterwarnings("ignore")

import numpy as np
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import teleconnections as T
from areas import CHIRPS_FILE, suffix

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"
for d in (FIG, TAB):
    d.mkdir(parents=True, exist_ok=True)

TEXTBOOK = ["nino34", "atl3", "tna", "tsa", "atl_grad", "iod_dmi", "wvg2", "wvg3"]


def preseason_field(sst_anom, season_months):
    start = min(season_months)
    lead = [((start - 1 - k - 1) % 12) + 1 for k in range(3)]
    sub = sst_anom.sel(time=sst_anom["time.month"].isin(lead))
    yr = sub["time.year"] + xr.where(sub["time.month"] >= start, 1, 0)
    return sub.groupby(yr.rename("year")).mean("time")


def persistence_series(precip, season_months, s, n):
    """Antecedent zone rainfall over the 3 pre-season months (a non-SST covariate)."""
    start = min(season_months)
    lead = [((start - 1 - k - 1) % 12) + 1 for k in range(3)]
    band = precip.sel(lat=slice(s, n)).mean(["lat", "lon"])
    sub = band.sel(time=band["time.month"].isin(lead))
    yr = sub["time.year"] + xr.where(sub["time.month"] >= start, 1, 0)
    return sub.groupby(yr.rename("year")).sum("time")


def loyo_corr_scalar(pred, rain):
    """LOYO CV corr for a fixed scalar predictor series via per-fold linear regression."""
    yrs = np.intersect1d(pred.dropna("year").year, rain.dropna("year").year)
    if len(yrs) < 10:
        return np.nan
    x = pred.sel(year=yrs).values.astype(float)
    y = rain.sel(year=yrs).values.astype(float)
    preds = np.full(len(yrs), np.nan)
    for i in range(len(yrs)):
        tr = np.arange(len(yrs)) != i
        if np.std(x[tr]) == 0:
            continue
        b1, b0 = np.polyfit(x[tr], y[tr], 1)
        preds[i] = b0 + b1 * x[i]
    ok = np.isfinite(preds)
    if ok.sum() < 10 or np.std(preds[ok]) == 0:
        return np.nan
    return float(np.corrcoef(preds[ok], y[ok])[0, 1])


def loyo_corr_projection(field, rain):
    """LOYO CV corr for the data-driven SST-projection predictor. The covariance pattern is
    recomputed on the training years within each fold (discovery is inside the CV)."""
    yrs = np.intersect1d(field.year.values, rain.dropna("year").year.values)
    if len(yrs) < 10:
        return np.nan
    F = field.sel(year=yrs)
    y = rain.sel(year=yrs).values.astype(float)
    n = len(yrs)
    preds = np.full(n, np.nan)
    for i in range(n):
        tr = np.arange(n) != i
        Ftr = F.isel(year=tr)
        ytr = y[tr]
        ya = ytr - ytr.mean()
        Ftr_mean = Ftr.mean("year")
        Fa = Ftr - Ftr_mean
        patt = (Fa * xr.DataArray(ya, coords={"year": Ftr.year}, dims="year")).mean("year")
        proj_tr = (Fa * patt).sum(["lat", "lon"]).values           # training projections
        proj_i = float(((F.isel(year=i) - Ftr_mean) * patt).sum(["lat", "lon"]))  # held-out
        if np.std(proj_tr) == 0:
            continue
        b1, b0 = np.polyfit(proj_tr, ytr, 1)
        preds[i] = b0 + b1 * proj_i
    ok = np.isfinite(preds)
    if ok.sum() < 10 or np.std(preds[ok]) == 0:
        return np.nan
    return float(np.corrcoef(preds[ok], y[ok])[0, 1])


def loyo_corr_combo(feature_series, rain, k=2):
    """CV-honest multi-feature predictor: inside each fold, screen the scalar features by
    training-year |corr|, take the top k, fit a k-way linear regression, predict the held-out
    year. Feature *selection and fitting both happen inside the fold* (no snooping). Tests
    whether combining predictors beats the best single one for a given season/subgeography."""
    yrs = None
    for s in feature_series.values():
        yy = s.dropna("year").year.values
        yrs = yy if yrs is None else np.intersect1d(yrs, yy)
    yrs = np.intersect1d(yrs, rain.dropna("year").year.values)
    if yrs is None or len(yrs) < 12:
        return np.nan
    names = list(feature_series)
    X = np.column_stack([feature_series[nm].sel(year=yrs).values.astype(float) for nm in names])
    y = rain.sel(year=yrs).values.astype(float)
    n = len(yrs)
    preds = np.full(n, np.nan)
    for i in range(n):
        tr = np.arange(n) != i
        Xtr, ytr = X[tr], y[tr]
        cors = []
        for j in range(X.shape[1]):
            xj = Xtr[:, j]
            cors.append(0.0 if np.std(xj) == 0 else abs(np.corrcoef(xj, ytr)[0, 1]))
        top = np.argsort(cors)[::-1][:k]
        A = np.column_stack([Xtr[:, top], np.ones(len(ytr))])
        coef, *_ = np.linalg.lstsq(A, ytr, rcond=None)
        preds[i] = np.dot(np.append(X[i, top], 1.0), coef)
    ok = np.isfinite(preds)
    if ok.sum() < 12 or np.std(preds[ok]) == 0:
        return np.nan
    return float(np.corrcoef(preds[ok], y[ok])[0, 1])


def main():
    sst = T.load_sst()
    idx = T.build_indices(sst)
    sst_anom = T.monthly_anom(sst)
    ds = xr.open_dataset(ROOT / "data" / CHIRPS_FILE)
    precip = ds["precip"]

    rows = []
    for season, band in product(T.SEASONS, list(T.BANDS)):
        months = T.SEASONS[season]
        s, n = T.BANDS[band]
        rain = T.seasonal_sum(precip, months, s, n)
        scalar_pool = {}
        # textbook indices
        for ik in TEXTBOOK:
            pre = T.index_preseason_mean(idx[ik], months)
            scalar_pool[ik] = pre
            rows.append(dict(season=season, band=band, predictor=ik,
                             cv_corr=loyo_corr_scalar(pre, rain)))
        # persistence
        per = persistence_series(precip, months, s, n)
        scalar_pool["persistence"] = per
        rows.append(dict(season=season, band=band, predictor="persistence",
                         cv_corr=loyo_corr_scalar(per, rain)))
        # data-driven SST projection (discovery inside CV)
        field = preseason_field(sst_anom, months)
        rows.append(dict(season=season, band=band, predictor="sst_projection",
                         cv_corr=loyo_corr_projection(field, rain)))
        # CV-honest multi-feature combination (selection + fit inside the fold)
        rows.append(dict(season=season, band=band, predictor="combo_top2",
                         cv_corr=loyo_corr_combo(scalar_pool, rain, k=2)))
        print(f"[features] scored {season} {band}", flush=True)

    with open(TAB / suffix("features_leaderboard","csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["season", "band", "predictor", "cv_corr"])
        w.writeheader()
        for r in rows:
            rr = dict(r); rr["cv_corr"] = None if rr["cv_corr"] is None or (isinstance(rr["cv_corr"], float) and np.isnan(rr["cv_corr"])) else round(rr["cv_corr"], 3)
            w.writerow(rr)

    # best predictor per (season, band)
    preds_all = TEXTBOOK + ["persistence", "sst_projection", "combo_top2"]
    md = ["| season | band | best predictor | CV corr | runner-up | CV corr |",
          "|---|---|---|---|---|---|"]
    for season, band in product(T.SEASONS, list(T.BANDS)):
        sub = [r for r in rows if r["season"] == season and r["band"] == band
               and r["cv_corr"] is not None and np.isfinite(r["cv_corr"])]
        sub.sort(key=lambda r: -r["cv_corr"])
        if len(sub) >= 2:
            md.append(f"| {season} | {band} | {sub[0]['predictor']} | {sub[0]['cv_corr']:.2f} "
                      f"| {sub[1]['predictor']} | {sub[1]['cv_corr']:.2f} |")
    (TAB / suffix("features_best","md")).write_text("\n".join(md) + "\n")

    # heatmaps predictor x season per band
    for band in ["National", "South", "North"]:
        M = np.full((len(preds_all), len(T.SEASONS)), np.nan)
        for i, p in enumerate(preds_all):
            for j, season in enumerate(T.SEASONS):
                v = [r["cv_corr"] for r in rows if r["band"] == band and r["predictor"] == p
                     and r["season"] == season and r["cv_corr"] is not None]
                M[i, j] = v[0] if v and np.isfinite(v[0]) else np.nan
        fig, ax = plt.subplots(figsize=(9, 5.5))
        im = ax.imshow(M, cmap="RdBu_r", vmin=-0.6, vmax=0.6, aspect="auto")
        ax.set_xticks(range(len(T.SEASONS))); ax.set_xticklabels(list(T.SEASONS), rotation=45)
        ax.set_yticks(range(len(preds_all))); ax.set_yticklabels(preds_all)
        for i in range(len(preds_all)):
            for j in range(len(T.SEASONS)):
                if np.isfinite(M[i, j]):
                    ax.text(j, i, f"{M[i,j]:.2f}", ha="center", va="center", fontsize=7,
                            color="white" if abs(M[i, j]) > 0.4 else "black")
        fig.colorbar(im, label="LOYO cross-validated correlation")
        ax.set_title(f"Predictor skill leaderboard — {band} Nigeria\n"
                     "(honest LOYO CV; sst_projection = data-driven pattern, discovery in-fold)")
        fig.tight_layout(); fig.savefig(FIG / suffix(f"features_cv_skill_{band}","png"), dpi=150)
        plt.close(fig)

    print("\n=== BEST PREDICTOR PER SEASON x BAND (LOYO CV corr) ===")
    print("\n".join(md))
    print("\ntables ->", TAB, "\nfigures ->", FIG)


if __name__ == "__main__":
    main()
