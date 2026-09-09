"""Rolling Indian Ocean SST / IOD forecasts from ECMWF S2S, calibrated against NOAA OI SST.

One run = one ECMWF extended-range issuance. For that init we fetch the live
forecast and the 20-year on-the-fly reforecast suite keyed to the same calendar
day, reduce both to five lead windows, and calibrate each window against the
OISST that verified those same windows historically.

The calibration is a plain OLS fit per (window, pole) across the reforecast
years -- Funk's stated preference over quantile matching, "particularly
appropriate given climate change", since a linear fit extrapolates a warming
trend where a quantile map clamps to the historical range.

Both poles are carried as absolute temperatures (WIO, EIO) and calibrated
separately, exactly as asked; the dipole (DMI) is then formed from anomalies.

DMI is reported twice, as `dmi_calibrated` and `dmi_raw`. These are NOT two
climatologies. OLS with an intercept is mean-preserving, so
`calibrated - obs_clim == slope * (x0 - xbar)`: the observed climatology cancels
identically and carries no information beyond the slopes. The two columns are
the calibrated forecast and the uncalibrated model, and the gap between them is
the regression's AMPLITUDE correction -- the model under-disperses the west pole
(slope > 1) and over-disperses the east (slope < 1). Mean bias cancels on both
sides and is not what the difference shows.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr

import acmaddl
import africas2s as a2s

# Both DMI poles with margin; one box keeps it to a single request per fetch.
REGION = [-15, 15, 45, 115]
WINDOWS = dict(a2s.LEAD_WINDOWS_S2S)          # week1..week4, day1_30
POLES = ("wio", "eio")                        # absolute-temperature pole indices
KELVIN = 273.15
BASELINE_YEARS = 20                           # ECMWF files 20 on-the-fly reforecast years


# ----------------------------------------------------------------- data layer

def fetch_model(init, *, region=REGION, verbose=False):
    """The live forecast and its matching reforecast suite, both in degrees C.

    acmadDL declares S2S sst in kelvin; OISST is Celsius. Converting here keeps
    every downstream number in one unit and keeps absolute pole temperatures
    directly readable.
    """
    fcst = acmaddl.fetch(product="c3s/ecmwf-s2s", variable="sst", init=init,
                         region=region, verbose=verbose)["sst"] - KELVIN
    hcst = acmaddl.fetch(product="c3s/ecmwf-s2s", variable="sst", init=init,
                         region=region, reforecast=True, verbose=verbose)["sst"] - KELVIN
    return fcst, hcst


def window_valid_dates(init, window, year=None):
    """The calendar dates a lead window verifies over.

    S2S sst is filed with ``stepType="avg"`` over each 24 h period, so the field
    at step 24 is the mean over hours 0-24 from a 00Z init -- the calendar day OF
    the init, not the day after. cfgrib labels valid_time with the END of the
    period, which is one day late; taking that label at face value would offset
    every observed verification window by a day. Window day 1 is therefore the
    init day itself.

    A consequence worth stating: the day 1-30 window includes the init day, whose
    ocean state is already partly known at issue time.
    """
    init_ts = pd.Timestamp(init)
    if year is not None:
        # 29 Feb has no counterpart in a non-leap year; step back a day rather than raise.
        try:
            init_ts = init_ts.replace(year=int(year))
        except ValueError:
            init_ts = init_ts.replace(month=2, day=28, year=int(year))
    first, last = WINDOWS[window]
    return (init_ts + pd.Timedelta(days=first - 1),
            init_ts + pd.Timedelta(days=last - 1))


def fetch_observed_windows(init, years, *, region=REGION, verbose=False):
    """Observed OISST mean over each (year, window) the reforecasts verify against.

    Returns a DataArray (year, window, lat, lon) on the OISST grid.
    """
    y0, y1 = int(min(years)), int(max(years))
    # Windows can run past 31 Dec for a late-year init, so pull one extra year.
    obs = acmaddl.fetch(product="obs/oisst-v2-daily", variable="sst",
                        hindcast=(y0, y1 + 1), region=region, verbose=verbose)["sst"]
    per_window = []
    for window in WINDOWS:
        per_year = []
        for year in years:
            start, end = window_valid_dates(init, window, year=year)
            sel = obs.sel(time=slice(start, end))
            if sel.sizes.get("time", 0) == 0:
                raise ValueError(
                    f"OISST has no data for {window} of {year} "
                    f"({start.date()}..{end.date()}).")
            per_year.append(sel.mean("time"))
        per_window.append(xr.concat(per_year, dim=pd.Index(list(years), name="year")))
    # dtype=object, not pandas' inferred StringDtype: xarray cannot build an
    # index from the latter ("Cannot interpret '<StringDtype...>' as a data type").
    windows_idx = pd.Index(list(WINDOWS), name="window", dtype=object)
    return xr.concat(per_window, dim=windows_idx)


# ------------------------------------------------------------ index reduction

def pole_series(field, *, ensemble_mean=True):
    """Reduce a (…, lat, lon) field to the WIO and EIO box means.

    Area-averaging happens on each source's own grid, so no regridding is needed
    to compare a 1.5 deg model box mean with a 0.25 deg observed one.
    """
    if ensemble_mean and "member" in field.dims:
        field = field.mean("member")
    return {p: a2s.Index.named(p).reduce(field) for p in POLES}


# ------------------------------------------------------------------ calibration

def ols(x, y):
    """Least-squares slope/intercept of y on x, plus correlation and residual sd."""
    x = np.asarray(x, dtype="float64")
    y = np.asarray(y, dtype="float64")
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 3:
        raise ValueError(f"OLS needs at least 3 finite pairs, got {int(ok.sum())}.")
    x, y = x[ok], y[ok]
    slope, intercept = np.polyfit(x, y, 1)
    fitted = slope * x + intercept
    resid = y - fitted
    # n-2 degrees of freedom: a slope and an intercept were estimated.
    sd = float(np.sqrt((resid ** 2).sum() / max(len(x) - 2, 1)))
    r = float(np.corrcoef(x, y)[0, 1]) if len(x) > 1 else np.nan
    return dict(slope=float(slope), intercept=float(intercept), r=r, resid_sd=sd,
                n=int(len(x)), xbar=float(x.mean()),
                sxx=float(((x - x.mean()) ** 2).sum()), resid=resid)


def prediction_interval(fit, x0, *, level=0.80):
    """Half-width of a prediction interval for a new observation at ``x0``.

    Three things the naive ``z * resid_sd`` leaves out, all of which matter here:

    * with n=20 the reference distribution is t on n-2 df, not the normal;
    * a *prediction* interval carries the 1/n term for the uncertainty in the
      fitted mean, on top of the residual scatter;
    * the leverage term ``(x0 - xbar)^2 / Sxx`` grows without bound away from the
      training mean. This forecast sits 2-3 standard deviations above it in the
      western pole, so that term is doing real work rather than rounding.

    Ignoring all three understated the western interval by 20-28%.
    """
    from scipy import stats
    n = fit["n"]
    dof = max(n - 2, 1)
    leverage = 1.0 / n + (float(x0) - fit["xbar"]) ** 2 / fit["sxx"] if fit["sxx"] > 0 else 1.0 / n
    se = fit["resid_sd"] * np.sqrt(1.0 + leverage)
    tcrit = float(stats.t.ppf(0.5 + level / 2.0, dof))
    return float(tcrit * se), float(leverage)


def loyo_skill(x, y):
    """Leave-one-year-out correlation and RMSE of the calibrated hindcast.

    The in-sample fit always flatters itself -- the same years set the slope and
    then score it. Refitting without each year in turn is what says whether the
    calibration would have helped in a year it had not seen.
    """
    x = np.asarray(x, dtype="float64")
    y = np.asarray(y, dtype="float64")
    preds = np.full(len(x), np.nan)
    for i in range(len(x)):
        keep = np.ones(len(x), dtype=bool)
        keep[i] = False
        try:
            fit = ols(x[keep], y[keep])
        except ValueError:
            continue
        preds[i] = fit["slope"] * x[i] + fit["intercept"]
    ok = np.isfinite(preds) & np.isfinite(y)
    if ok.sum() < 3:
        return dict(r=np.nan, rmse=np.nan, n=int(ok.sum()))
    return dict(r=float(np.corrcoef(preds[ok], y[ok])[0, 1]),
                rmse=float(np.sqrt(np.mean((preds[ok] - y[ok]) ** 2))),
                n=int(ok.sum()))


def persistence_predictor(init, years, pole, *, region=REGION, days=30, verbose=False):
    """The observed pole temperature over the `days` before each init.

    SST is strongly autocorrelated, so "the ocean stays as it is" is a genuinely
    hard baseline. Without it a high correlation says almost nothing: a model
    that only reproduced persistence would score nearly as well. Skill is what
    the forecast adds *over* this.

    ``days`` is not innocuous and the default is deliberately the demanding one.
    A 14-day window -- the first thing tried here -- is the weakest of 7/14/30 at
    almost every horizon, i.e. the choice that most flatters the model. Thirty
    days is the harder and more natural comparison for a product whose flagship
    window is a 30-day mean, and it is what :func:`persistence_sensitivity`
    reports across. The window is inclusive of both endpoints.
    """
    y0, y1 = int(min(years)), int(max(years))
    obs = acmaddl.fetch(product="obs/oisst-v2-daily", variable="sst",
                        hindcast=(y0, y1 + 1), region=region, verbose=verbose)["sst"]
    vals = []
    for year in years:
        init_ts, _ = window_valid_dates(init, "week1", year=year)[0], None
        sel = obs.sel(time=slice(init_ts - pd.Timedelta(days=days), init_ts))
        vals.append(a2s.Index.named(pole).reduce(sel.mean("time")))
    return xr.concat(vals, dim=pd.Index(list(years), name="year"))


def calibrate_pole(hcst_idx, obs_idx, fcst_idx):
    """Fit obs on model across reforecast years, per window, and apply to the forecast."""
    rows = []
    for window in WINDOWS:
        x = hcst_idx.sel(window=window).values
        y = obs_idx.sel(window=window).values
        fit = ols(x, y)
        skill = loyo_skill(x, y)
        raw = float(fcst_idx.sel(window=window))
        ci80, leverage = prediction_interval(fit, raw, level=0.80)
        rows.append(dict(
            window=window, raw=raw,
            calibrated=fit["slope"] * raw + fit["intercept"],
            model_clim=float(np.nanmean(x)), obs_clim=float(np.nanmean(y)),
            slope=fit["slope"], intercept=fit["intercept"],
            fit_r=fit["r"], resid_sd=fit["resid_sd"],
            ci80=ci80, leverage=leverage,
            # how far outside the training range this forecast sits, in training sd
            z_vs_training=(raw - fit["xbar"]) / np.sqrt(fit["sxx"] / max(fit["n"] - 1, 1)),
            loyo_r=skill["r"], loyo_rmse=skill["rmse"], n_years=fit["n"],
        ))
    table = pd.DataFrame(rows).set_index("window")
    table.attrs["residuals"] = {w: ols(hcst_idx.sel(window=w).values,
                                       obs_idx.sel(window=w).values)["resid"] for w in WINDOWS}
    table.attrs["fits"] = {w: ols(hcst_idx.sel(window=w).values,
                                  obs_idx.sel(window=w).values) for w in WINDOWS}
    return table


def williams_test(r_my, r_py, r_mp, n):
    """Williams' t for two DEPENDENT correlations that share a variable.

    Model-vs-observed and persistence-vs-observed are not independent: they share
    the observed series, and the two predictors are themselves strongly
    correlated. Comparing them with anything that assumes independence overstates
    the evidence. Returns (t, p, df) for a two-sided test of r_my == r_py.

    With n=20 this is the difference between "the model beats persistence" and
    "the model beats persistence by more than twenty years can resolve".
    """
    from scipy import stats
    if not all(np.isfinite([r_my, r_py, r_mp])) or n < 5:
        return float("nan"), float("nan"), 0
    det = (1 - r_my ** 2 - r_py ** 2 - r_mp ** 2) + 2 * r_my * r_py * r_mp
    df = n - 3
    denom = (2 * ((n - 1) / df) * det
             + ((r_my + r_py) ** 2 / 4) * (1 - r_mp) ** 3)
    if denom <= 0:
        return float("nan"), float("nan"), df
    t = (r_my - r_py) * np.sqrt((n - 1) * (1 + r_mp) / denom)
    return float(t), float(2 * stats.t.sf(abs(t), df)), int(df)


def bootstrap_gain_ci(x_model, x_pers, y, *, level=0.80, n_boot=4000, seed=0):
    """Pairs-bootstrap CI for the correlation gain (model - persistence).

    Preferred over an analytic test for dependent correlations: those come in
    several formula variants that disagree at n=20, and the point here is only
    whether the gain is separable from sampling noise. Resampling the (model,
    persistence, observed) triples keeps the dependence between the two
    predictors intact, which is what makes the comparison hard in the first place.
    """
    rng = np.random.default_rng(seed)
    x_model = np.asarray(x_model, float); x_pers = np.asarray(x_pers, float)
    y = np.asarray(y, float)
    ok = np.isfinite(x_model) & np.isfinite(x_pers) & np.isfinite(y)
    xm, xp, yy = x_model[ok], x_pers[ok], y[ok]
    n = len(yy)
    if n < 5:
        return float("nan"), float("nan")
    gains = np.empty(n_boot)
    for b in range(n_boot):
        i = rng.integers(0, n, n)
        if np.std(xm[i]) == 0 or np.std(xp[i]) == 0 or np.std(yy[i]) == 0:
            gains[b] = np.nan; continue
        gains[b] = (np.corrcoef(xm[i], yy[i])[0, 1] - np.corrcoef(xp[i], yy[i])[0, 1])
    lo, hi = np.nanquantile(gains, [(1 - level) / 2, 1 - (1 - level) / 2])
    return float(lo), float(hi)


def persistence_sensitivity(init, years, hcst_idx, obs_idx, *, windows=(7, 14, 30), verbose=False):
    """LOYO skill of the model against persistence at several baseline lengths.

    The persistence window is a free parameter, and the headline claim turns on
    it: at 14 days the model beats persistence everywhere, at 30 days it does not
    in the west. Reporting the sweep is the honest form of the comparison.
    """
    rows = []
    for pole in POLES:
        for w in WINDOWS:
            y = obs_idx[pole].sel(window=w).values
            m = loyo_skill(hcst_idx[pole].sel(window=w).values, y)
            row = dict(pole=pole.upper(), window=w, model_r=m["r"], model_rmse=m["rmse"])
            x_model = hcst_idx[pole].sel(window=w).values
            for d in windows:
                x_pers = persistence_predictor(init, years, pole, days=d,
                                               verbose=verbose).values
                p = loyo_skill(x_pers, y)
                row[f"persist{d}_r"] = p["r"]
                row[f"gain{d}"] = m["r"] - p["r"]
                # significance of the DIFFERENCE, not of either correlation
                ok = np.isfinite(x_model) & np.isfinite(x_pers) & np.isfinite(y)
                r_mp = float(np.corrcoef(x_model[ok], x_pers[ok])[0, 1])
                _, pv, _ = williams_test(m["r"], p["r"], r_mp, int(ok.sum()))
                row[f"p{d}"] = pv
                lo, hi = bootstrap_gain_ci(x_model, x_pers, y)
                row[f"gain{d}_lo"] = lo
                row[f"gain{d}_hi"] = hi
            rows.append(row)
    return pd.DataFrame(rows).set_index(["pole", "window"])


def regrid_like(fine, target):
    """Put a fine observed grid onto the coarser model grid.

    Block-average first, then sample. Interpolating straight from 0.25 deg to
    1.5 deg would take point samples and throw away 35 of every 36 observed
    cells; averaging first means each model cell is compared against the mean of
    the ocean it actually covers.
    """
    def _factor(a, b):
        da = abs(float(a[1] - a[0]))
        db = abs(float(b[1] - b[0]))
        return max(int(round(db / da)), 1)

    fy = _factor(fine["lat"].values, target["lat"].values)
    fx = _factor(fine["lon"].values, target["lon"].values)
    if fy > 1 or fx > 1:
        fine = fine.coarsen(lat=fy, lon=fx, boundary="trim").mean()
    # Coarsening puts block centres off the model centres, so the outermost model
    # row and column fall outside the coarsened grid and are left NaN: those cells
    # are never calibrated. Extrapolating to fill them would invent a slope from
    # no overlapping observations, so they stay NaN and the maps simply do not
    # draw them (see make_maps.EXTENT).
    return fine.interp(lat=target["lat"], lon=target["lon"])


def calibrate_fields(hcst_w, obs_w, fcst_w, *, dim="year"):
    """Per-cell OLS of observed on forecast, fitted across the reforecast years.

    The box-mean slope cannot be reused per cell -- the model's bias is not
    spatially uniform, which is the whole reason for calibrating a field rather
    than scaling one number. Fitted independently at every cell and window.

    Returns a Dataset of slope, intercept, in-sample r, leave-one-year-out r,
    and the calibrated forecast field.
    """
    obs = regrid_like(obs_w, hcst_w)
    x = hcst_w.mean("member") if "member" in hcst_w.dims else hcst_w
    y = obs.transpose(*[d for d in x.dims if d in obs.dims])

    def _fit(xa, ya):
        xb, yb = xa.mean(dim), ya.mean(dim)
        cov = ((xa - xb) * (ya - yb)).mean(dim)
        var = ((xa - xb) ** 2).mean(dim)
        slope = cov / var
        return slope, yb - slope * xb, cov, var

    slope, intercept, cov, var = _fit(x, y)
    sd_y = y.std(dim)
    r = cov / np.sqrt(var * sd_y ** 2)

    # Leave-one-year-out, vectorised: refit with each year dropped and predict it.
    years = list(np.atleast_1d(x[dim].values))
    preds = []
    for yr in years:
        keep = x[dim] != yr
        s, i, _, _ = _fit(x.isel({dim: keep.values}), y.isel({dim: keep.values}))
        preds.append(s * x.sel({dim: yr}) + i)
    pred = xr.concat(preds, dim=x[dim])
    pb, yb2 = pred.mean(dim), y.mean(dim)
    loyo_r = (((pred - pb) * (y - yb2)).mean(dim)
              / np.sqrt(((pred - pb) ** 2).mean(dim) * ((y - yb2) ** 2).mean(dim)))

    fcst_mean = fcst_w.mean("member") if "member" in fcst_w.dims else fcst_w
    calibrated = slope * fcst_mean + intercept
    return xr.Dataset(dict(
        calibrated_sst=calibrated,
        raw_sst=fcst_mean,
        obs_climatology=y.mean(dim),
        slope=slope, intercept=intercept, fit_r=r, loyo_r=loyo_r,
    ))


def run(init, *, verbose=False):
    """End-to-end: one init in, calibrated poles + both DMI framings out."""
    fcst, hcst = fetch_model(init, verbose=verbose)
    years = [int(y) for y in np.atleast_1d(hcst["year"].values)]

    fcst_w = a2s.lead_window_reduce(fcst, WINDOWS)
    hcst_w = a2s.lead_window_reduce(hcst, WINDOWS)
    obs_w = fetch_observed_windows(init, years, verbose=verbose)

    fcst_idx = pole_series(fcst_w)
    hcst_idx = pole_series(hcst_w)
    obs_idx = pole_series(obs_w, ensemble_mean=False)

    tables = {p: calibrate_pole(hcst_idx[p], obs_idx[p], fcst_idx[p]) for p in POLES}

    # DMI: the calibrated forecast, and the uncalibrated model beside it.
    #
    # These are NOT two climatologies. OLS with an intercept is mean-preserving,
    # so `calibrated - obs_clim == slope * (x0 - xbar)` -- the observed
    # climatology cancels identically. Setting both slopes to 1 gives the raw
    # column. The gap between them is therefore the regression's amplitude
    # correction (west slope > 1, east slope < 1), not bias removal.
    W, E = tables["wio"], tables["eio"]
    dmi = pd.DataFrame({
        "dmi_calibrated": ((W["calibrated"] - W["obs_clim"]) - (E["calibrated"] - E["obs_clim"])),
        "dmi_raw": ((W["raw"] - W["model_clim"]) - (E["raw"] - E["model_clim"])),
    })

    # Pole residuals are NOT independent (corr runs -0.46..+0.20 by window), so
    # adding them in quadrature understates the difference -- by 19% at week 1.
    # Take the empirical sd of the residual difference instead, then inflate for
    # the same prediction-interval terms the poles get.
    from scipy import stats
    ci, corr = [], []
    for w in WINDOWS:
        rw, re_ = W.attrs["residuals"][w], E.attrs["residuals"][w]
        fw, fe = W.attrs["fits"][w], E.attrs["fits"][w]
        n = fw["n"]
        sd_diff = float(np.std(rw - re_, ddof=2))
        leverage = 0.5 * (float(W.loc[w, "leverage"]) + float(E.loc[w, "leverage"]))
        tcrit = float(stats.t.ppf(0.90, max(n - 2, 1)))
        ci.append(tcrit * sd_diff * np.sqrt(1.0 + leverage))
        corr.append(float(np.corrcoef(rw, re_)[0, 1]))
    dmi["ci80"] = ci
    dmi["pole_resid_corr"] = corr

    calib_fields = calibrate_fields(hcst_w, obs_w, fcst_w)
    return dict(init=init, years=years, poles=tables, dmi=dmi,
                calibrated_fields=calib_fields,
                fields=dict(forecast=fcst_w, reforecast=hcst_w, observed=obs_w))
