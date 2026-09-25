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
the regression's AMPLITUDE correction. The east is consistently shrunk (slope
0.7 or so in every run to date); the west has been stretched in some runs and
shrunk in others, so the sign there is not a fixed property of the model. Mean
bias cancels on both sides and is not what the difference shows.
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
# The tendency calibration needs the init-day value as well as the scored
# windows, since the model contributes only the change away from it.
TENDENCY_WINDOWS = dict(WINDOWS, day1=(1, 1))
KELVIN = 273.15
BASELINE_START = 2006                         # first reforecast year
BASELINE_YEARS = 20                           # ECMWF files 20 on-the-fly reforecast years


# ----------------------------------------------------------------- data layer

def latest_usable_init(today=None, *, back=30, verbose=False):
    """The most recent issuance that has a reforecast suite.

    ECMWF files extended-range reforecasts on **odd calendar days of the month**.
    Confirmed by probe on 2026-09-17: Friday the 11th, Sunday the 13th and Tuesday
    the 15th all have a 20-year suite; Saturday the 12th and Wednesday the 16th
    have none.

    An earlier version of this function asserted Monday/Thursday issuances with a
    roughly one-week lag. That was wrong on both counts -- it was inferred from
    four dates that happened to be consistent with it, and it would have skipped
    every odd-numbered Friday, Sunday and Tuesday, i.e. most valid inits. Chris
    Funk supplied the actual rule.

    Note an odd day is necessary but not sufficient: the 31st of one month is
    followed by the 1st, so consecutive odd days occur, and a given odd day can
    still be missing. This probes rather than assumes, cheaply (a 4x4 degree box)
    rather than pulling the suite.
    """
    today = pd.Timestamp(today or pd.Timestamp.today().normalize())
    tried = []
    for d in pd.date_range(today - pd.Timedelta(days=back), today)[::-1]:
        if d.day % 2 == 0:
            continue
        init = d.strftime("%Y-%m-%d")
        tried.append(init)
        try:
            acmaddl.fetch(product="c3s/ecmwf-s2s", variable="sst", init=init,
                          region=[-2, 2, 50, 54], reforecast=True, verbose=False)
            if verbose:
                print(f"[iod] latest usable init: {init}")
            return init
        except Exception:
            continue
    raise RuntimeError(
        f"No odd-day issuance in the last {back} days has a reforecast suite "
        f"(tried {', '.join(tried[:8])}...).")


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


def _require_full_window(sel, start, end, what):
    """Fail unless every calendar day of the window is present.

    Averaging a partly-covered window silently returns the mean of whatever days
    happen to be there. A seven-day mean built from one day has already reached a
    published table this way, so absence is an error, not a smaller sample.
    """
    want = pd.date_range(start, end, freq="D")
    have = pd.DatetimeIndex(np.atleast_1d(sel["time"].values)).normalize()
    missing = want.difference(have)
    if len(missing):
        raise ValueError(
            f"{what} needs {len(want)} days ({pd.Timestamp(start).date()}.."
            f"{pd.Timestamp(end).date()}) but {len(missing)} are absent, first "
            f"{missing[0].date()}; observations reach "
            f"{pd.Timestamp(have.max()).date() if len(have) else 'none'}.")


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
            _require_full_window(sel, start, end, f"{window} of {year}")
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
        init_ts = window_valid_dates(init, "week1", year=year)[0]
        start = init_ts - pd.Timedelta(days=days)
        sel = obs.sel(time=slice(start, init_ts))
        _require_full_window(sel, start, init_ts, f"persistence anchor for {year}")
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


def observed_anchor(init, years, pole, *, region=REGION, days=30, live_year=None, verbose=False):
    """Observed pole SST over the ``days`` ending at each year's init.

    The state of the ocean at issue time, measured rather than modelled. Used as
    the anchor predictor in :func:`calibrate_pole_tendency`; identical in
    construction to the persistence baseline, so the tendency fit nests
    persistence as the special case where the model term carries no weight.
    """
    y0, y1 = int(min(years)), int(max(years))
    obs = acmaddl.fetch(product="obs/oisst-v2-daily", variable="sst",
                        hindcast=(y0, max(y1, live_year or y1) + 1),
                        region=region, verbose=verbose)["sst"]
    out = {}
    for year in list(years) + ([live_year] if live_year else []):
        start, _ = window_valid_dates(init, "week1", year=year)
        anchor_from = start - pd.Timedelta(days=days)
        sel = obs.sel(time=slice(anchor_from, start))
        _require_full_window(sel, anchor_from, start, f"observed anchor for {year}")
        out[int(year)] = float(a2s.Index.named(pole).reduce(sel.mean("time")))
    return out


def _ols2(X, y):
    """Two-predictor least squares with an intercept.

    Returns the coefficients, the residual sd, the sample size, the residuals and
    the coefficient standard errors. The standard errors matter here: the
    tendency weight is the coefficient under question, and its own uncertainty
    settles whether twenty years constrain it far better than comparing the
    estimate across two initialisations does.
    """
    X = np.asarray(X, float); y = np.asarray(y, float)
    ok = np.isfinite(y) & np.isfinite(X).all(axis=1)
    X, y = X[ok], y[ok]
    A = np.column_stack([np.ones(len(X)), X])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    resid = y - A @ coef
    dof = max(len(y) - A.shape[1], 1)
    sigma2 = float((resid ** 2).sum() / dof)
    try:
        se = np.sqrt(np.diag(sigma2 * np.linalg.inv(A.T @ A)))
    except np.linalg.LinAlgError:
        se = np.full(A.shape[1], np.nan)
    return coef, float(np.sqrt(sigma2)), int(len(y)), resid, se


def calibrate_pole_tendency(init, years, hcst_idx, fcst_idx, obs_idx, pole, *,
                            anchor_days=30, live_year=None, verbose=False):
    """Alternative calibration: observed anchor + the model's forecast CHANGE.

    The standing method regresses observed absolute SST on *model absolute* SST,
    so the model's own bias enters the predictor and the fit responds by shrinking
    it -- a slope near 0.7 in the eastern box, which verification shows has made
    the forecast worse in every window so far.

    This fits instead

        observed(window) ~ a + b * observed(at issue) + c * [model(window) - model(day 1)]

    The level comes from the *observation*, which carries no model bias, and the
    model supplies only the tendency -- the thing a dynamical model is better at
    than absolute temperature. It is autocorrelation-aware by construction: the
    anchor is the persistence predictor, so the fit nests persistence at c = 0 and
    can only improve on it in-sample.

    One structural caveat on the tendency weight. The anchor is a 31-day observed
    mean ending at the init, while the tendency is measured from the model's
    init-day value, so `c` has to absorb the offset between those two references
    on top of carrying the model's forecast change. At short lead the tendency
    predictor also has very little year-to-year variance, which inflates the
    coefficient and trades it off against `b` -- on the 13 September
    initialisation `c` reached 4.15 in the east while `b` fell to 0.72. Read `c`
    with its standard error, not on its own.

    Reported alongside the standing calibration, not in place of it.
    """
    anchor = observed_anchor(init, years, pole, days=anchor_days,
                             live_year=live_year, verbose=verbose)
    # All three indices are (window, ...) DataArrays as returned by pole_series,
    # selected the same way. They must carry a "day1" window in addition to the
    # scored ones -- see TENDENCY_WINDOWS -- because the model contributes only
    # the change from the init day.
    day1_h = hcst_idx.sel(window="day1"); day1_f = float(fcst_idx.sel(window="day1"))
    rows = []
    for w in WINDOWS:
        x1 = np.array([anchor[int(y)] for y in years])
        x2 = hcst_idx.sel(window=w).values - day1_h.values   # model tendency, per year
        y = obs_idx.sel(window=w).values
        coef, sd, n, resid, se = _ols2(np.column_stack([x1, x2]), y)
        x1_new = anchor[int(live_year)]
        x2_new = float(fcst_idx.sel(window=w)) - day1_f
        pred = coef[0] + coef[1] * x1_new + coef[2] * x2_new
        # leave-one-year-out
        preds = np.full(len(y), np.nan)
        for i in range(len(y)):
            k = np.ones(len(y), bool); k[i] = False
            c2, *_ = _ols2(np.column_stack([x1[k], x2[k]]), y[k])
            preds[i] = c2[0] + c2[1] * x1[i] + c2[2] * x2[i]
        good = np.isfinite(preds) & np.isfinite(y)
        rows.append(dict(window=w, predicted=pred,
                         b_anchor=coef[1], c_tendency=coef[2],
                         b_se=float(se[1]), c_se=float(se[2]),
                         c_t=float(coef[2] / se[2]) if se[2] else np.nan,
                         resid_sd=sd, n=n,
                         loyo_r=float(np.corrcoef(preds[good], y[good])[0, 1]),
                         loyo_rmse=float(np.sqrt(np.mean((preds[good] - y[good]) ** 2)))))
    return pd.DataFrame(rows).set_index("window")


# How far back the observed record is pulled when rebuilding a prior-only
# seasonal cycle. Held at the first reforecast year so this shares the observed
# fetch the rest of the pipeline already caches; reaching further back made the
# OPeNDAP retrieval slow enough to stall. The cost is that the earliest years
# have too little history to build a cycle from and go unscored, so compare
# against a baseline restricted to the same years -- see arima_vs_model.
ARIMA_CLIM_START = BASELINE_START


def daily_box_series(pole, years, *, region=REGION, end=None, start=None, verbose=False):
    """Daily observed box-mean SST, and its day-of-year anomaly.

    The anomaly is what ARIMA is fitted on: removing the seasonal cycle leaves an
    approximately stationary series, which is the assumption the model needs.

    `start` pulls the record back before the first scored year. arima_skill needs
    that: rebuilding the seasonal cycle from data preceding each year's init
    leaves the earliest years with too little history to do it. It is currently
    held at the first reforecast year to share the cached observed fetch, so the
    first three years go unscored; scoring all twenty would mean reaching further
    back, which made the retrieval slow enough to stall.
    """
    # Must be a raw (absolute-temperature) index. The anomaly-transform twins
    # wtio/setio cover the same boxes, and passing one here removes the seasonal
    # cycle twice: doy_climatology then fits the residual cycle of an anomaly,
    # and the forecast comes back on a scale that is neither absolute nor this
    # analysis' anomaly. Skill scores survive it -- prediction and observation
    # shift together -- but any published temperature does not.
    if getattr(a2s.Index.named(pole), "transform", "raw") != "raw":
        raise ValueError(
            f"daily_box_series needs a raw index; {pole!r} is an anomaly index. "
            f"Use {'wio' if pole == 'wtio' else 'eio'!r} for the pole boxes.")
    y0 = int(start) if start is not None else int(min(years))
    y1 = int(pd.Timestamp(end).year) if end is not None else int(max(years))
    obs = acmaddl.fetch(product="obs/oisst-v2-daily", variable="sst",
                        hindcast=(y0, y1), region=region, verbose=verbose)["sst"]
    series = a2s.Index.named(pole).reduce(obs)          # (time,) box mean
    clim = a2s.doy_climatology(series, smooth=31)       # smoothed annual cycle
    anom = a2s.doy_anomaly(series, clim)
    return series, clim, anom


def arima_window_forecast(anom, clim, init, *, order=(1, 0, 1), windows=None, verbose=False):
    """Statistical forecast of each lead window from the observed series alone.

    Fitted on the DAILY anomaly series up to (and including) the init day, then
    projected forward and averaged onto the same windows the model uses. The
    seasonal cycle is added back so the result is an absolute temperature
    comparable with every other column.

    This is the reference point the persistence baseline approximates crudely.
    Persistence holds the current anomaly flat; an AR model lets it decay toward
    climatology at a fitted rate, which for SST is the physically sensible
    behaviour and a materially harder benchmark at longer leads.

    Fitted on thousands of daily points rather than twenty annual ones, so it does
    not carry the n=20 fragility of the regression-based columns. The seasonal
    cycle passed in as `clim` must itself be built only from data preceding
    `init`; see arima_skill, where reusing a whole-record climatology across
    historical years was found to flatter the scores by 0.01-0.05 C RMSE.
    """
    from statsmodels.tsa.arima.model import ARIMA
    windows = dict(windows or WINDOWS)
    init_ts = pd.Timestamp(init)
    # Train to the day BEFORE the init. statsmodels' forecast(steps=h)[0] is the
    # step after the last training observation, and window day 1 is the init day
    # itself (window_valid_dates), so training through the init day would put the
    # day-2 value in the day-1 slot. Ending a day earlier lines the two up and
    # matches what is actually known at a 00Z issuance, whose own daily mean is
    # not yet complete.
    hist = anom.sel(time=slice(None, init_ts - pd.Timedelta(days=1))).dropna("time")
    if hist.sizes.get("time", 0) < 400:
        raise ValueError(f"ARIMA needs a longer history; got {hist.sizes.get('time', 0)} days.")
    fit = ARIMA(hist.values, order=order, trend="n").fit()
    horizon = max(b for _, b in windows.values())
    pred = np.asarray(fit.forecast(steps=horizon))      # anomaly, days 1..horizon
    dates = pd.date_range(init_ts, periods=horizon, freq="D")
    doy = dates.dayofyear
    seasonal = np.array([float(clim.sel(dayofyear=min(d, int(clim.dayofyear.max())))) for d in doy])
    absolute = pred + seasonal
    out = {}
    for w, (a, b) in windows.items():
        out[w] = float(np.mean(absolute[a - 1:b]))
    return out, fit


def arima_skill(pole, years, init, *, order=(1, 0, 1), region=REGION,
                prior_only=True, verbose=False):
    """Score the ARIMA forecast against observations across the reforecast years.

    For each year the model is refitted on data ending at that year's init, so
    every score is a true out-of-sample forecast.

    `prior_only` controls the seasonal cycle. The ARIMA fit always respects the
    init date, but the day-of-year climatology removed beforehand does not unless
    it is rebuilt per year: a climatology spanning the whole record lets a 2010
    forecast borrow the mean seasonal cycle of 2011-2026.

    Rebuilding it per year removes that look-ahead but is not a clean correction,
    and the difference between the two settings should not be read as the size of
    the leakage. A cycle built from data ending at the init has one fewer year of
    samples for days after the init than for days before it, and the forecast
    window lies entirely on the short side; with a warming record behind it, the
    seasonal term added back is too cool. Measured mean error is more negative
    under prior_only in every window (to -0.16 C in the east), and removing that
    bias recovers the whole RMSE difference in the west and about half of it in
    the east. The two effects are confounded, so both settings are reported
    rather than one being called correct.
    """
    series, clim, anom = daily_box_series(pole, list(years) + [pd.Timestamp(init).year],
                                          region=region, end=init,
                                          start=(ARIMA_CLIM_START if prior_only else None),
                                          verbose=verbose)
    rows, skipped, unconverged = [], [], []
    for year in years:
        yr_init = window_valid_dates(init, "week1", year=year)[0]
        if prior_only:
            # Rebuild the cycle from data preceding this year's init only. Needs a
            # few years to be stable, so the earliest years are skipped rather
            # than scored off a one- or two-year cycle.
            past = series.sel(time=slice(None, yr_init))
            if past.sizes.get("time", 0) < 3 * 365:
                skipped.append((int(year), "insufficient history for a prior-only cycle"))
                continue
            clim_y = a2s.doy_climatology(past, smooth=31)
            anom_y = a2s.doy_anomaly(past, clim_y)
        else:
            clim_y, anom_y = clim, anom
        try:
            pred, fit = arima_window_forecast(anom_y, clim_y, yr_init, order=order)
        except ValueError as exc:
            # Too little history for this year; every other failure is a bug and
            # should surface rather than silently shrink the sample.
            skipped.append((int(year), str(exc)))
            continue
        if not getattr(fit, "mle_retvals", {}).get("converged", True):
            unconverged.append(int(year))
        row = dict(year=int(year))
        for w in WINDOWS:
            s, e = window_valid_dates(init, w, year=year)
            sel_w = series.sel(time=slice(s, e))
            _require_full_window(sel_w, s, e, f"{w} of {year}")
            obs_w = float(sel_w.mean())
            row[f"{w}_pred"] = pred[w]
            row[f"{w}_obs"] = obs_w
        rows.append(row)
    df = pd.DataFrame(rows).set_index("year")
    skill = {}
    for w in WINDOWS:
        p, o = df[f"{w}_pred"].values, df[f"{w}_obs"].values
        ok = np.isfinite(p) & np.isfinite(o)
        skill[w] = dict(r=float(np.corrcoef(p[ok], o[ok])[0, 1]),
                        rmse=float(np.sqrt(np.mean((p[ok] - o[ok]) ** 2))),
                        bias=float(np.mean(p[ok] - o[ok])), n=int(ok.sum()))
    out = pd.DataFrame(skill).T
    # Carried so callers can report why the sample is what it is, and how many
    # fits the optimiser did not converge on, rather than inferring it from n.
    out.attrs["skipped"] = skipped
    out.attrs["unconverged"] = unconverged
    df.attrs["skipped"] = skipped
    df.attrs["unconverged"] = unconverged
    return out, df


def interval_coverage(init, years, *, level=0.80, region=REGION, verbose=False):
    """How often the truth lands inside its own prediction interval.

    Four verified windows cannot settle whether an 80% interval is honest --
    four of four inside has a 41% chance even for a badly wrong interval. This
    refits leave-one-year-out across the reforecast years, builds the interval
    the held-out year would have been given, and checks whether that year's
    observation fell inside it. The report quotes the pooled figure, so it must
    be produced here rather than by hand.
    """
    fcst, hcst = fetch_model(init, verbose=verbose)
    hcst_w = a2s.lead_window_reduce(hcst, WINDOWS)
    obs_w = fetch_observed_windows(init, years, verbose=verbose)
    x_all = pole_series(hcst_w)
    y_all = pole_series(obs_w, ensemble_mean=False)

    rows = []
    for pole in POLES:
        for w in WINDOWS:
            x = x_all[pole].sel(window=w).values.astype(float)
            y = y_all[pole].sel(window=w).values.astype(float)
            inside = 0
            for i in range(len(y)):
                k = np.ones(len(y), bool); k[i] = False
                fit = ols(x[k], y[k])
                pred = fit["intercept"] + fit["slope"] * x[i]
                half, _ = prediction_interval(fit, x[i], level=level)
                if abs(y[i] - pred) <= half:
                    inside += 1
            rows.append(dict(pole=pole.upper(), window=w, n=len(y),
                             inside=inside, coverage=inside / len(y)))
    out = pd.DataFrame(rows).set_index(["pole", "window"])
    out.attrs["pooled"] = float(out["inside"].sum() / out["n"].sum())
    out.attrs["level"] = level
    return out


def dispersion(init, years, *, region=REGION, verbose=False):
    """Model spread against observed spread, and the slope it implies.

    Explains the calibration slopes rather than just reporting them. Least
    squares sets slope = r * sd(obs) / sd(model), so a model whose year-to-year
    spread exceeds the observed spread is shrunk by construction. The eastern
    box runs about 20% wide, which is where its 0.72 slope comes from, and that
    makes the eastern problem one of amplitude rather than offset.
    """
    fcst, hcst = fetch_model(init, verbose=verbose)
    hcst_w = a2s.lead_window_reduce(hcst, WINDOWS)
    obs_w = fetch_observed_windows(init, years, verbose=verbose)
    x_all = pole_series(hcst_w)
    y_all = pole_series(obs_w, ensemble_mean=False)

    rows = []
    for pole in POLES:
        for w in WINDOWS:
            x = x_all[pole].sel(window=w).values.astype(float)
            y = y_all[pole].sel(window=w).values.astype(float)
            sx, sy = float(x.std(ddof=1)), float(y.std(ddof=1))
            r = float(np.corrcoef(x, y)[0, 1])
            rows.append(dict(pole=pole.upper(), window=w, mean_bias=float(x.mean() - y.mean()),
                             sd_model=sx, sd_obs=sy, spread_ratio=sx / sy, corr=r,
                             implied_slope=r * sy / sx))
    return pd.DataFrame(rows).set_index(["pole", "window"])


def verify(init, window, *, outputs="outputs", region=REGION, cache=True, verbose=False):
    """Score a past issuance against the OISST that has since verified it.

    Reads the published tables for `init` rather than recomputing the forecast,
    so what is scored is exactly what was issued. The observed climatology is
    recovered from those same tables (calibrated - anomaly) instead of being
    rebuilt here: an independently constructed climatology is the one thing that
    has silently broken this comparison before, and it cannot drift if it is
    never built twice.

    Returns a one-row frame per pole plus the dipole, with the calibrated and raw
    forecasts, the observation, and the error of each.
    """
    init = str(pd.Timestamp(init).date())
    idx = pd.read_csv(f"{outputs}/indices_{init}.csv")
    idx = idx[idx["window"] == window].set_index("index")
    dmi = pd.read_csv(f"{outputs}/dmi_{init}.csv").set_index("window").loc[window]

    start, end = window_valid_dates(init, window)
    if pd.Timestamp(end) >= pd.Timestamp.utcnow().tz_localize(None).normalize():
        raise ValueError(f"{window} of {init} verifies to {end}; not yet complete.")
    # Same hindcast span the training path uses, so this shares its cached copy.
    # Asking for the single verifying year instead creates a second cache entry
    # that no other call refreshes, and a stale one produced exactly the
    # partly-covered window _require_full_window now rejects.
    y0 = int(min(BASELINE_START, pd.Timestamp(start).year))
    obs = acmaddl.fetch(product="obs/oisst-v2-daily", variable="sst",
                        hindcast=(y0, pd.Timestamp(end).year + 1),
                        region=region, cache=cache, verbose=verbose)["sst"]
    sel = obs.sel(time=slice(start, end))
    # OISST trails real time by a day or two, and a cached copy trails further.
    # Without this check a partly-covered window is averaged over whatever days
    # happen to be present and returned as if it were the full mean -- a single
    # day has already been scored here as a seven-day verification. Refuse
    # instead; a stale cache is fixed with cache=False.
    _require_full_window(sel, start, end, f"{window} of {init}")
    obs_w = sel.mean("time")

    rows = []
    for pole, key in (("wio", "WIO"), ("eio", "EIO")):
        r = idx.loc[key]
        clim = float(r["calibrated_C"]) - float(r["anomaly_C"])   # never rebuilt
        observed = float(a2s.Index.named(pole).reduce(obs_w))
        rows.append(dict(index=key, calibrated=float(r["calibrated_C"]),
                         raw=float(r["raw_C"]), observed=observed,
                         obs_anomaly=observed - clim,
                         err_calibrated=float(r["calibrated_C"]) - observed,
                         err_raw=float(r["raw_C"]) - observed, ci80=float(r["ci80"])))
    w, e = rows[0], rows[1]
    obs_dmi = w["obs_anomaly"] - e["obs_anomaly"]
    rows.append(dict(index="DMI", calibrated=float(dmi["dmi_calibrated"]),
                     raw=float(dmi["dmi_raw"]), observed=obs_dmi, obs_anomaly=obs_dmi,
                     err_calibrated=float(dmi["dmi_calibrated"]) - obs_dmi,
                     err_raw=float(dmi["dmi_raw"]) - obs_dmi, ci80=float(dmi["ci80"])))
    out = pd.DataFrame(rows).set_index("index")
    out.attrs["window"] = window; out.attrs["init"] = init
    out.attrs["valid"] = (str(start.date()), str(end.date()))
    return out


def arima_forecast_dipole(init, years, *, order=(1, 0, 1), region=REGION, verbose=False):
    """ARIMA pole forecasts and dipole, on the same baseline as the main tables.

    arima_window_forecast returns absolute temperature against a smoothed
    day-of-year cycle. The reported anomalies everywhere else are departures from
    the 2006-2025 mean of the SAME calendar window, which is a different
    quantity; differencing the two baselines moved the dipole by up to 0.13 C.
    This builds the anomaly against the window climatology the Results table
    uses, so the three methods can be listed in one column.
    """
    obs_w = fetch_observed_windows(init, years, verbose=verbose)
    obs_idx = pole_series(obs_w, ensemble_mean=False)
    out = {}
    for pole in POLES:
        series, clim, anom = daily_box_series(pole, list(years) + [pd.Timestamp(init).year],
                                              end=init, verbose=verbose)
        pred, _ = arima_window_forecast(anom, clim, init, order=order)
        rows = {}
        for w in WINDOWS:
            window_clim = float(obs_idx[pole].sel(window=w).mean("year"))
            rows[w] = dict(absolute=pred[w], clim=window_clim,
                           anomaly=pred[w] - window_clim)
        out[pole] = rows
    out["dmi"] = {w: out["wio"][w]["anomaly"] - out["eio"][w]["anomaly"] for w in WINDOWS}
    return out


def arima_vs_model(pole, years, init, *, order=(1, 0, 1), region=REGION, verbose=False):
    """ARIMA against the standing calibration, scored on identical years.

    Rebuilding the seasonal cycle from data preceding each year's init leaves the
    earliest years unscorable, so the ARIMA column covers fewer years than the
    twenty the regression is fitted on. Comparing the two as published would then
    mix a difference in method with a difference in sample. Both are therefore
    scored here on the intersection: the regression is refitted leave-one-year-out
    on the full twenty, as it is in the forecast, but only the common years are
    scored.
    """
    sk, df = arima_skill(pole, years, init, order=order, region=region,
                         prior_only=True, verbose=verbose)
    common = sorted(int(y) for y in df.index)

    fcst, hcst = fetch_model(init, verbose=verbose)
    hcst_w = a2s.lead_window_reduce(hcst, WINDOWS)
    obs_w = fetch_observed_windows(init, years, verbose=verbose)
    x_all = pole_series(hcst_w)[pole]
    y_all = pole_series(obs_w, ensemble_mean=False)[pole]

    rows = []
    for w in WINDOWS:
        x = x_all.sel(window=w).values.astype(float)
        y = y_all.sel(window=w).values.astype(float)
        yr = np.array([int(v) for v in np.atleast_1d(x_all["year"].values)])
        pred = np.full(len(y), np.nan)
        for i in range(len(y)):                      # leave-one-year-out, all 20
            k = np.ones(len(y), bool); k[i] = False
            fit = ols(x[k], y[k])
            pred[i] = fit["intercept"] + fit["slope"] * x[i]
        m = np.isin(yr, common) & np.isfinite(pred) & np.isfinite(y)
        a = df.loc[common]
        ap, ao = a[f"{w}_pred"].values, a[f"{w}_obs"].values
        rows.append(dict(
            window=w, n=int(m.sum()),
            model_r=float(np.corrcoef(pred[m], y[m])[0, 1]),
            model_rmse=float(np.sqrt(np.mean((pred[m] - y[m]) ** 2))),
            arima_r=float(np.corrcoef(ap, ao)[0, 1]),
            arima_rmse=float(np.sqrt(np.mean((ap - ao) ** 2)))))
    out = pd.DataFrame(rows).set_index("window")
    out["rmse_diff"] = out["arima_rmse"] - out["model_rmse"]
    out.attrs["years"] = common
    return out


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
