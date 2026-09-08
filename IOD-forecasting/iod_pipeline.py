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
Because the init is a fixed calendar day, each climatology is just the 20-year
mean of that window -- so we report DMI against BOTH a model climatology (the
reforecast's own, which absorbs the model's lead-dependent bias) and an observed
one (OISST, anchored to what the ocean actually did).
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
    every downstream number in one unit and makes the deck's ~29 C thresholds
    directly readable.
    """
    fcst = acmaddl.fetch(product="c3s/ecmwf-s2s", variable="sst", init=init,
                         region=region, verbose=verbose)["sst"] - KELVIN
    hcst = acmaddl.fetch(product="c3s/ecmwf-s2s", variable="sst", init=init,
                         region=region, reforecast=True, verbose=verbose)["sst"] - KELVIN
    return fcst, hcst


def window_valid_dates(init, window, year=None):
    """The calendar dates a lead window verifies over.

    Window days are 1-based and inclusive: day 1 is the first full forecast day,
    i.e. the day after the 00Z issuance.
    """
    init_ts = pd.Timestamp(init)
    if year is not None:
        init_ts = init_ts.replace(year=int(year))
    first, last = WINDOWS[window]
    return (init_ts + pd.Timedelta(days=first),
            init_ts + pd.Timedelta(days=last))


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
    return dict(slope=float(slope), intercept=float(intercept), r=r, resid_sd=sd, n=int(len(x)))


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


def persistence_predictor(init, years, pole, *, region=REGION, days=14, verbose=False):
    """The observed pole temperature over the `days` before each init.

    SST is strongly autocorrelated, so "the ocean stays as it is" is a genuinely
    hard baseline. Without it a high correlation says almost nothing: a model
    that only reproduced persistence would score nearly as well. Skill is what
    the forecast adds *over* this.
    """
    y0, y1 = int(min(years)), int(max(years))
    obs = acmaddl.fetch(product="obs/oisst-v2-daily", variable="sst",
                        hindcast=(y0, y1 + 1), region=region, verbose=verbose)["sst"]
    vals = []
    for year in years:
        init_ts = pd.Timestamp(init).replace(year=int(year))
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
        rows.append(dict(
            window=window, raw=raw,
            calibrated=fit["slope"] * raw + fit["intercept"],
            model_clim=float(np.nanmean(x)), obs_clim=float(np.nanmean(y)),
            slope=fit["slope"], intercept=fit["intercept"],
            fit_r=fit["r"], resid_sd=fit["resid_sd"],
            loyo_r=skill["r"], loyo_rmse=skill["rmse"], n_years=fit["n"],
        ))
    return pd.DataFrame(rows).set_index("window")


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

    # DMI is a difference of anomalies, so it inherits its baseline. Report both:
    #   observed  -- calibrated poles against the OISST climatology (what the ocean does)
    #   model     -- raw poles against the reforecast climatology (what this model does)
    dmi = pd.DataFrame({
        "dmi_obs_clim": ((tables["wio"]["calibrated"] - tables["wio"]["obs_clim"])
                         - (tables["eio"]["calibrated"] - tables["eio"]["obs_clim"])),
        "dmi_model_clim": ((tables["wio"]["raw"] - tables["wio"]["model_clim"])
                           - (tables["eio"]["raw"] - tables["eio"]["model_clim"])),
    })
    # Independent pole errors add in quadrature.
    dmi["ci80_halfwidth"] = 1.2816 * np.sqrt(
        tables["wio"]["resid_sd"] ** 2 + tables["eio"]["resid_sd"] ** 2)
    calib_fields = calibrate_fields(hcst_w, obs_w, fcst_w)
    return dict(init=init, years=years, poles=tables, dmi=dmi,
                calibrated_fields=calib_fields,
                fields=dict(forecast=fcst_w, reforecast=hcst_w, observed=obs_w))
