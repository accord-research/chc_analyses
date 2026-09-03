"""methods.py — run one Config through its calibration method and score it (AGUv1).

Every config, whatever its predictor_source/method, is reduced to a common representation —
per-year cross-validated **tercile probabilities** + a **deterministic** CV series over the same
gridded predictand — and scored with the SAME four metrics, so cells are comparable.

  * field predictors (obs_sst_field / gcm_mos_sst / gcm_mos_precip) → `africas2s.seasonal_mme`
    (CPT-style CCA-MOS, or qm) under LOYO;
  * persistence (scalar) → a leave-one-year-out scalar→field regression, then deepscale terciles.
"""
from __future__ import annotations
import sys, warnings
from pathlib import Path
import numpy as np
import xarray as xr
warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import targets as T
import predictors as P
import africas2s
from africas2s.registry import get_metric
from africas2s.metrics.generalized_roc import _obs_to_categories
from africas2s.tercile import to_tercile_cv

METRIC_NAMES = ("generalized_roc", "rpss", "pearson_r", "hit_rate")


def hit_rate(tercile: xr.DataArray, obs: xr.DataArray) -> float:
    """Tercile categorical accuracy: fraction of (year,cell) where the argmax-probability tercile
    matches the observed tercile category (the 'realized accuracy' proxy)."""
    obs_t = obs.transpose("year", "lat", "lon")
    obs_cat = _obs_to_categories(obs_t.values)                 # (year,lat,lon) ints, -1 = missing
    fcat = tercile.transpose("year", "lat", "lon", "tercile").values.argmax(-1)
    valid = obs_cat >= 0
    return float((fcat[valid] == obs_cat[valid]).mean()) if valid.any() else float("nan")


def _metric(name, forecast, obs):
    try:
        return float(get_metric(name)().compute(forecast, obs))
    except Exception:
        return float("nan")


def _score(tercile: xr.DataArray, obs: xr.DataArray, deterministic: xr.DataArray | None) -> dict:
    s = {
        "generalized_roc": _metric("generalized_roc", tercile, obs),
        "rpss": _metric("rpss", tercile, obs),
        "hit_rate": hit_rate(tercile, obs),
    }
    if deterministic is not None:
        # anomaly Pearson: remove each cell's temporal mean first, so the score is temporal skill,
        # not spatial climatology contamination.
        da = (deterministic - deterministic.mean("year")).transpose("year", "lat", "lon").values.ravel()
        db = (obs - obs.mean("year")).transpose("year", "lat", "lon").values.ravel()
        ok = np.isfinite(da) & np.isfinite(db)
        s["pearson_r"] = float(np.corrcoef(da[ok], db[ok])[0, 1]) if ok.sum() > 3 and da[ok].std() > 0 else float("nan")
    else:
        s["pearson_r"] = float("nan")
    return s


def _det_from_result(res):
    """MME deterministic CV series (year,lat,lon) = mean over models of per_model_cv_hindcasts."""
    cvh = getattr(res, "per_model_cv_hindcasts", None)
    if not cvh:
        return None
    das = []
    for v in cvh.values():
        extra = [d for d in v.dims if d not in ("year", "lat", "lon")]
        das.append(v.mean(extra) if extra else v)
    return xr.concat(das, dim="_m").mean("_m")


def _scalar_loyo_field(x: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """LOYO scalar→field OLS. x:(n,), Y:(n,ncell) → deterministic preds (n,ncell)."""
    n = len(x)
    pred = np.full(Y.shape, np.nan)
    for i in range(n):
        tr = np.arange(n) != i
        xt = x[tr]
        if xt.std() == 0:
            continue
        for j in range(Y.shape[1]):
            yt = Y[tr, j]
            ok = np.isfinite(yt) & np.isfinite(xt)
            if ok.sum() < 5 or xt[ok].std() == 0:
                continue
            b1, b0 = np.polyfit(xt[ok], yt[ok], 1)
            pred[i, j] = b0 + b1 * x[i]
    return pred


def score_config(cfg) -> dict:
    """Build predictor+predictand for a Config, run its method under LOYO, return the 4 metrics."""
    tgt = _TARGETS[cfg.target]
    y = T.predictand(tgt)                          # (year,lat,lon), common hindcast years
    if cfg.transform == "std_anom":                # per-cell standardized anomaly (vs raw totals)
        y = (y - y.mean("year")) / y.std("year").where(lambda s: s > 0)
    last = int(y.year.max())

    # ── scalar predictors (persistence + engineered indices) → scalar-to-field LOYO regression ──
    scalar_x = None
    if cfg.predictor_source == "persistence":
        scalar_x = P.persistence(tgt, cfg.lead)
    elif cfg.predictor_source in ("obs_index", "gcm_index"):
        import indices as IDX
        if cfg.predictor_source == "obs_index":
            field = P.obs_sst_field(tgt, cfg.lead, "indo_pacific")
        else:                                   # forecast index from the (cached) NMME SST field
            tr = P.gcm_mos_sst(tgt, cfg.lead, "indo_pacific")
            if not tr:
                return {m: float("nan") for m in METRIC_NAMES}
            das = [v.mean([d for d in v.dims if d not in ("year", "lat", "lon")]) for v in tr.values()]
            field = xr.concat(das, dim="_m").mean("_m")
        scalar_x = IDX.index_from_field(field, cfg.predictor_domain)   # domain holds the index name
    if scalar_x is not None:
        yrs = np.intersect1d(scalar_x.dropna("year").year.values, y.year.values)
        y = y.sel(year=yrs); xv = scalar_x.sel(year=yrs).values.astype(float)
        if not np.isfinite(xv).any() or np.nanstd(xv) == 0:
            return {m: float("nan") for m in METRIC_NAMES}
        stack = y.stack(cell=("lat", "lon"))
        det = _scalar_loyo_field(xv, stack.values)
        det = xr.DataArray(det, coords=stack.coords, dims=stack.dims).unstack("cell").transpose("year", "lat", "lon")
        tercile = to_tercile_cv(det, y, method="cpt")
        return _score(tercile, y, det)

    # field predictors → seasonal_mme
    if cfg.predictor_source == "obs_sst_field":
        fld = P.obs_sst_field(tgt, cfg.lead, cfg.predictor_domain)
        if "member" not in fld.dims:                # perfect-prog: single deterministic "member"
            fld = fld.expand_dims(member=[0])
        tracks = {"PRED": {"OBS": (fld, fld.sel(year=[int(fld.year.max())]))}}
    elif cfg.predictor_source == "gcm_mos_sst":
        t = P.gcm_mos_sst(tgt, cfg.lead, cfg.predictor_domain)
        tracks = {"PRED": {k: (v, v.sel(year=[int(v.year.max())])) for k, v in t.items()}}
    elif cfg.predictor_source == "gcm_mos_precip":
        t = P.gcm_mos_precip(tgt, cfg.lead)
        tracks = {"PRED": {k: (v, v.sel(year=[int(v.year.max())])) for k, v in t.items()}}
    else:
        raise ValueError(cfg.predictor_source)
    if not tracks["PRED"]:
        return {m: float("nan") for m in METRIC_NAMES}

    # align obs years to predictor years
    pyears = None
    for _, (h, _f) in tracks["PRED"].items():
        pyears = h.year.values if pyears is None else np.intersect1d(pyears, h.year.values)
    y = y.sel(year=np.intersect1d(y.year.values, pyears))
    cpt_args = {"n_modes": cfg.eof_modes} if cfg.method == "cca" and cfg.eof_modes > 0 else None
    res = africas2s.seasonal_mme(tracks, y, method=cfg.method, cv="loyo", cpt_args=cpt_args,
                                 forecast_year=int(y.year.max()), verbose=False)
    return _score(res.tercile_cv, y, _det_from_result(res))


# target registry (name -> Target), built once
_TARGETS = {t.name: t for t in T.discover_targets()}


if __name__ == "__main__":
    import iridl_patch; iridl_patch.apply()
    from searchspace import Config
    tests = [
        Config("Kenya:OND", "obs_sst_field", "cca", 1),
        Config("Kenya:OND", "persistence", "regression", 1),
        Config("Kenya:OND", "gcm_mos_precip", "cca", 1),
    ]
    for c in tests:
        s = score_config(c)
        print(f"  {c.predictor_source:15s} L{c.lead}: " +
              "  ".join(f"{k}={s[k]:+.3f}" for k in METRIC_NAMES))
