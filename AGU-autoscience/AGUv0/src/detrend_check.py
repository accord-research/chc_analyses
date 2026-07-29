"""
detrend_check.py — does the shared warming trend inflate the headline correlations?

For the report's headline (country, season, band, predictor) cells, recompute the LOYO
cross-validated skill with and without **in-fold linear detrending** (fit the trend on the
training years for both predictor and rainfall, remove it from all years, then regress). A
result that survives detrending is interannual signal; one that collapses was riding the trend.

Addresses reviewer point O1 (no detrending; effective DOF overstated).

Output: outputs/tables/detrend_check.md  (raw vs detrended, all three countries)
Run in accord-chc after the obs pipeline.
"""
import warnings, sys
from pathlib import Path
warnings.filterwarnings("ignore")
import numpy as np
import xarray as xr
import deepscale

sys.path.insert(0, str(Path(__file__).resolve().parent))
import teleconnections as T  # load_sst, build_indices, monthly_anom, index_preseason_mean

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TAB = ROOT / "outputs" / "tables"

# (country, chirps file, [(season, (lat_s,lat_n), band_label, index_name), ...])
CASES = [
    ("Nigeria", "nigeria_chirps_monthly.nc", [
        ("JAS", (11, 14), "Sahel/North", "nino34"),
        ("JAS", (11, 14), "Sahel/North", "wvg2"),
        ("JAS", (8, 11), "Middle", "atl3"),
        ("JAS", (8, 11), "Middle", "atl_grad"),
        ("OND", (4, 14), "National", "iod_dmi"),
    ]),
    ("Ethiopia", "ethiopia_chirps_monthly.nc", [
        ("JAS", (10, 15), "Kiremt/North", "nino34"),
        ("JAS", (10, 15), "Kiremt/North", "wvg3"),
        ("OND", (3, 7), "South", "iod_dmi"),
        ("MAM", (3, 7), "South", "nino34"),
    ]),
    ("Kenya", "kenya_chirps_monthly.nc", [
        ("OND", (-5, 5), "National", "iod_dmi"),
        ("OND", (-5, -1), "South", "iod_dmi"),
        ("JAS", (-1, 2), "Central", "wvg3"),
        ("MAM", (-5, 5), "National", "nino34"),
    ]),
]
SEASON_MONTHS = {"MAM": [3, 4, 5], "JAS": [7, 8, 9], "OND": [10, 11, 12], "JJAS": [6, 7, 8, 9]}


def seasonal_rain(precip, months, s, n):
    band = precip.sel(lat=slice(s, n)).mean(["lat", "lon"])
    return deepscale.seasonal_reduce(band, months)


def loyo_corr(x, y, detrend):
    """LOYO CV corr of predictor x -> rainfall y; optional in-fold linear detrend of both."""
    yrs = np.intersect1d(x.dropna("year").year, y.dropna("year").year)
    xv = x.sel(year=yrs).values.astype(float)
    yv = y.sel(year=yrs).values.astype(float)
    t = np.arange(len(yrs), dtype=float)
    n = len(yrs)
    if n < 12:
        return np.nan
    pred = np.full(n, np.nan)
    for i in range(n):
        tr = np.arange(n) != i
        xt, yt, tt = xv.copy(), yv.copy(), t
        if detrend:
            for arr in (xt, yt):
                b1, b0 = np.polyfit(tt[tr], arr[tr], 1)
                arr -= (b0 + b1 * tt)   # remove trend fit on TRAIN from all years
        if np.std(xt[tr]) == 0:
            continue
        b1, b0 = np.polyfit(xt[tr], yt[tr], 1)
        pred[i] = b0 + b1 * xt[i]
        if detrend:
            pass  # yt already detrended; compare pred to detrended yt below
    ok = np.isfinite(pred)
    ycmp = yv.copy()
    if detrend:
        # for scoring, detrend y over the full record (comparison target)
        b1, b0 = np.polyfit(t, yv, 1); ycmp = yv - (b0 + b1 * t)
    if ok.sum() < 12 or np.std(pred[ok]) == 0:
        return np.nan
    return float(np.corrcoef(pred[ok], ycmp[ok])[0, 1])


def preseason_field(sst_anom, months):
    start = min(months)
    lead = [((start - 1 - k - 1) % 12) + 1 for k in range(3)]
    sub = sst_anom.sel(time=sst_anom["time.month"].isin(lead))
    yr = sub["time.year"] + xr.where(sub["time.month"] >= start, 1, 0)
    return sub.groupby(yr.rename("year")).mean("time")


def loyo_proj_corr(field, rain, detrend):
    """LOYO CV corr for the data-driven sst_projection predictor, optional in-fold detrend of
    the SST field (per cell) and rainfall."""
    yrs = np.intersect1d(field.year.values, rain.dropna("year").year.values)
    F = field.sel(year=yrs); yv = rain.sel(year=yrs).values.astype(float)
    n = len(yrs); t = np.arange(n, dtype=float)
    Fv = F.transpose("year", "lat", "lon").values  # (n, ny, nx)
    if detrend:
        yb1, yb0 = np.polyfit(t, yv, 1); yv = yv - (yb0 + yb1 * t)
        A = np.vstack([t, np.ones(n)]).T
        coef, *_ = np.linalg.lstsq(A, Fv.reshape(n, -1), rcond=None)
        Fv = (Fv.reshape(n, -1) - A @ coef).reshape(Fv.shape)
    pred = np.full(n, np.nan)
    for i in range(n):
        tr = np.arange(n) != i
        Xtr = Fv[tr]; ytr = yv[tr]
        patt = np.nanmean(Xtr * (ytr - ytr.mean())[:, None, None], axis=0)
        proj_tr = np.nansum(Xtr * patt, axis=(1, 2))
        proj_i = np.nansum(Fv[i] * patt)
        if np.std(proj_tr) == 0:
            continue
        b1, b0 = np.polyfit(proj_tr, ytr, 1); pred[i] = b0 + b1 * proj_i
    ok = np.isfinite(pred)
    return float(np.corrcoef(pred[ok], yv[ok])[0, 1]) if ok.sum() >= 12 and np.std(pred[ok]) else np.nan


def main():
    sst = T.load_sst()
    idx = T.build_indices(sst)
    sst_anom = T.monthly_anom(sst)
    rows = []
    for country, cf, cases in CASES:
        ds = xr.open_dataset(DATA / cf)
        precip = ds["precip"]
        for season, (s, n), band, iname in cases:
            months = SEASON_MONTHS[season]
            rain = seasonal_rain(precip, months, s, n)
            pre = T.index_preseason_mean(idx[iname], months)
            r_raw = loyo_corr(pre, rain, detrend=False)
            r_det = loyo_corr(pre, rain, detrend=True)
            rows.append((country, season, band, iname, r_raw, r_det))
            print(f"  {country:9s} {season} {band:13s} {iname:9s}  raw={r_raw:+.2f}  detrended={r_det:+.2f}", flush=True)
        # the data-driven sst_projection (reviewer flagged as most trend-exposed), once per country's monsoon cell
        season, (s, n), band = cases[0][0], cases[0][1], cases[0][2]
        months = SEASON_MONTHS[season]
        rain = seasonal_rain(precip, months, s, n)
        field = preseason_field(sst_anom, months)
        pr_raw = loyo_proj_corr(field, rain, detrend=False)
        pr_det = loyo_proj_corr(field, rain, detrend=True)
        rows.append((country, season, band, "sst_projection", pr_raw, pr_det))
        print(f"  {country:9s} {season} {band:13s} sst_projn  raw={pr_raw:+.2f}  detrended={pr_det:+.2f}", flush=True)

    md = ["# Raw vs. in-fold-detrended LOYO skill (headline cells)\n",
          "LOYO cross-validated correlation of a pre-season SST index with zone-mean seasonal "
          "rainfall, without and with in-fold linear detrending of both series. Survives detrending "
          "= interannual signal; collapses = rode the shared warming trend.\n",
          "| Country | Season | Band | Index | r (raw) | r (detrended) |",
          "|---|---|---|---|---|---|"]
    for c, se, b, i, rr, rd in rows:
        flag = "  ⚠" if (np.isfinite(rr) and np.isfinite(rd) and abs(rr) - abs(rd) > 0.10) else ""
        md.append(f"| {c} | {se} | {b} | {i} | {rr:+.2f} | {rd:+.2f}{flag} |")
    md.append("\n⚠ = |r| drops by >0.10 under detrending (trend-inflated).\n")
    (TAB / "detrend_check.md").write_text("\n".join(md) + "\n")
    print("\nwrote", TAB / "detrend_check.md")


if __name__ == "__main__":
    main()
