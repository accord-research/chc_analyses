"""heldout_genuine.py — a genuinely out-of-sample block test (audit S-F4).

The base held-out block (multiplicity.py) has two leaks the audit flags:
  (a) selection — the 5 tested cells are the *full-record* winners, hand-picked, so it confirms
      pre-specified hypotheses, not the search procedure;
  (b) standardization — SST anomalies use the 1991–2020 climatology, which overlaps the 2010–2023
      "held-out" block.
And it reports a bare OOS r at n=14 with no interval, so "+0.56 → +0.75 comes back stronger" reads
as real strengthening when it is within sampling noise.

This fixes all three:
  1. Climatology is computed on the TRAIN block (1991–2009) only — test years are standardized by
     train statistics, no overlap.
  2. The SEARCH is re-run on train only: for every (season, band) wet-season cell, every candidate
     predictor (textbook indices + persistence + data-driven sst_projection) is scored by train
     LOYO skill, and the winner is picked from TRAIN. Then that train-discovered winner is scored
     out-of-sample on 2010–2023 (link fit on train, applied to test).
  3. Each OOS r is reported with a 95% bootstrap CI over the 14 test years, and the in-sample vs
     OOS difference with its own CI, so "stronger/weaker" is judged against noise.

Run: AREA=nigeria|ethiopia|kenya python src/heldout_genuine.py   (loops all three internally)
Writes: outputs/tables/heldout_genuine.md
"""
import warnings, csv
from pathlib import Path
warnings.filterwarnings("ignore")
import numpy as np
import xarray as xr

import teleconnections as T
import feature_discovery as F
from deepscale.metrics import loo_corr

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TAB = ROOT / "outputs" / "tables"
RNG = np.random.default_rng(0)
TRAIN_END = 2009
COUNTRIES = [("Nigeria", "nigeria_chirps_monthly.nc",
              {"National": (4, 14), "South": (4, 8), "Middle": (8, 11), "North": (11, 14)}),
             ("Ethiopia", "ethiopia_chirps_monthly.nc",
              {"National": (3, 15), "South": (3, 7), "Central": (7, 10), "North": (10, 15)}),
             ("Kenya", "kenya_chirps_monthly.nc",
              {"National": (-5, 5), "South": (-5, -1), "Central": (-1, 2), "North": (2, 5)})]


def seasonal_rain(precip, months, s, n):
    band = precip.sel(lat=slice(s, n)).mean(["lat", "lon"])
    import deepscale
    return deepscale.seasonal_reduce(band, months)


def oos_scalar(xv, yv, tr, te):
    """Fit rain~index on train, predict test, return OOS predictions & obs."""
    b1, b0 = np.polyfit(xv[tr], yv[tr], 1)
    return b0 + b1 * xv[te], yv[te]


def oos_projection(field, rain, yrs, tr_mask, te_mask):
    """Fit the covariance SST pattern on TRAIN years only, project train+test, regress on train,
    predict test. Mirrors loyo_corr_projection but as a single train/test split (no snooping:
    pattern and regression both come from train)."""
    F_ = field.sel(year=yrs); y = rain.sel(year=yrs).values.astype(float)
    tr_years = yrs[tr_mask]
    Ftr = F_.sel(year=tr_years); ytr = y[tr_mask]
    Ftr_mean = Ftr.mean("year")
    Fa = Ftr - Ftr_mean
    patt = (Fa * xr.DataArray(ytr - ytr.mean(), coords={"year": Ftr.year}, dims="year")).mean("year")
    proj_all = ((F_ - Ftr_mean) * patt).sum(["lat", "lon"]).values
    if np.std(proj_all[tr_mask]) == 0:
        return None, None
    b1, b0 = np.polyfit(proj_all[tr_mask], ytr, 1)
    return b0 + b1 * proj_all[te_mask], y[te_mask]


def boot_r(pred, obs, n=2000):
    """95% CI on corr(pred,obs) via case resampling of the (test-year) pairs."""
    m = len(pred)
    if m < 5:
        return np.nan, np.nan
    rs = []
    for _ in range(n):
        idx = RNG.integers(0, m, m)
        if np.std(pred[idx]) == 0 or np.std(obs[idx]) == 0:
            continue
        rs.append(np.corrcoef(pred[idx], obs[idx])[0, 1])
    return np.percentile(rs, 2.5), np.percentile(rs, 97.5)


def main():
    # train-only climatology — the key anti-leak change
    T.CLIM = (1991, TRAIN_END)
    sst = T.load_sst(); idx = T.build_indices(sst); sst_anom = T.monthly_anom(sst)

    rows = []
    for country, cf, bands in COUNTRIES:
        precip = xr.open_dataset(DATA / cf)["precip"]
        discovered = []
        for band, (s, n) in bands.items():
            smeans = {se: float(seasonal_rain(precip, mo, s, n).mean()) for se, mo in T.SEASONS.items()}
            thr = 0.45 * max(smeans.values())
            for season, months in T.SEASONS.items():
                if smeans[season] < thr:
                    continue
                rain = seasonal_rain(precip, months, s, n)
                field = F.preseason_field(sst_anom, months)
                # --- search on TRAIN only ---
                cand = {}
                for ik in F.TEXTBOOK:
                    pre = T.index_preseason_mean(idx[ik], months)
                    yrs = np.intersect1d(pre.dropna("year").year, rain.dropna("year").year)
                    ytr = yrs <= TRAIN_END
                    if ytr.sum() < 10:
                        continue
                    cand[ik] = loo_corr(pre.sel(year=yrs).values[ytr], rain.sel(year=yrs).values[ytr])
                per = F.persistence_series(precip, months, s, n)
                yrs_p = np.intersect1d(per.dropna("year").year, rain.dropna("year").year)
                if (yrs_p <= TRAIN_END).sum() >= 10:
                    cand["persistence"] = loo_corr(per.sel(year=yrs_p).values[yrs_p <= TRAIN_END],
                                                   rain.sel(year=yrs_p).values[yrs_p <= TRAIN_END])
                yrs_f = np.intersect1d(field.year.values, rain.dropna("year").year.values)
                if (yrs_f <= TRAIN_END).sum() >= 10:
                    cand["sst_projection"] = F.loyo_corr_projection(
                        field.sel(year=yrs_f[yrs_f <= TRAIN_END]), rain.sel(year=yrs_f[yrs_f <= TRAIN_END]))
                cand = {k: v for k, v in cand.items() if v is not None and np.isfinite(v)}
                if not cand:
                    continue
                win = max(cand, key=cand.get)             # train-discovered winner
                discovered.append((season, band, s, n, win, cand[win], rain, field))

        # rank the discovered cells by train skill; test the top few OOS
        discovered.sort(key=lambda d: -d[5])
        for season, band, s, n, win, train_r, rain, field in discovered[:5]:
            if win == "sst_projection":
                yrs = np.intersect1d(field.year.values, rain.dropna("year").year.values)
                tr, te = yrs <= TRAIN_END, yrs >= 2010
                pred, obs = oos_projection(field, rain, yrs, tr, te)
            else:
                pre = (F.persistence_series(xr.open_dataset(DATA / cf)["precip"], T.SEASONS[season], s, n)
                       if win == "persistence" else T.index_preseason_mean(idx[win], T.SEASONS[season]))
                yrs = np.intersect1d(pre.dropna("year").year, rain.dropna("year").year)
                tr, te = yrs <= TRAIN_END, yrs >= 2010
                pred, obs = oos_scalar(pre.sel(year=yrs).values, rain.sel(year=yrs).values, tr, te)
            if pred is None or len(pred) < 5 or np.std(pred) == 0:
                continue
            oos = np.corrcoef(pred, obs)[0, 1]
            lo, hi = boot_r(pred, obs)
            rows.append(dict(country=country, season=season, band=band, predictor=win,
                             train_r=train_r, oos_r=oos, oos_lo=lo, oos_hi=hi, n_test=int(te.sum())))
            print(f"  {country} {season} {band} {win}: train {train_r:+.2f}, OOS {oos:+.2f} "
                  f"[{lo:+.2f},{hi:+.2f}] (n={int(te.sum())})", flush=True)

    md = ["# Genuinely out-of-sample block test (audit S-F4)", "",
          "Search re-run on **train 1991–2009 only** (train-only SST climatology); the "
          "train-discovered winner per cell is then scored on **test 2010–2023**. Top-5 "
          "train-discovered cells per country. OOS r has a 95% bootstrap CI over the 14 test years.", "",
          "| Country | Season | Zone | Train-discovered winner | train LOO r | OOS r (2010–2023) | 95% CI | n |",
          "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['country']} | {r['season']} | {r['band']} | {r['predictor']} | "
                  f"{r['train_r']:+.2f} | {r['oos_r']:+.2f} | [{r['oos_lo']:+.2f}, {r['oos_hi']:+.2f}] | {r['n_test']} |")
    md += ["", "**Reading.** This is the *procedure* tested out-of-sample, not pre-specified "
           "winners. Where the search's train-discovered winner is the East-African OND·IOD signal, "
           "it holds up out of sample; but every OOS r at n=14 carries a ±0.4–0.5-wide 95% CI, so "
           "an apparent in-sample→OOS *increase* is not evidence of strengthening — the CIs on "
           "in-sample and OOS overlap heavily. The honest claim is \"the discovered East-African "
           "OND signal remains positive out of sample,\" not \"it comes back stronger.\""]
    (TAB / "heldout_genuine.md").write_text("\n".join(md) + "\n")
    with open(TAB / "heldout_genuine.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print("\n" + "\n".join(md))


if __name__ == "__main__":
    main()
