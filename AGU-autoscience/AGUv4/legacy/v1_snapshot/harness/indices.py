"""indices.py — SPEC 7 (predictors and leads) and SPEC 8 (conditional families).

The ocean side of the pipeline. Two things matter here and both are inherited rather
than rewritten:

  - the year-wrap arithmetic lives in `bench.Context`, which tests/test_wrap.py pins and
    probes/spec_check.py has shown reproduces AGUv3's lead convention exactly over all
    12 window starts and 4 leads. This module builds the (year, month) grids that
    Context expects from the single ERSST belt fixture, and then uses Context unchanged;

  - `compose` is grid_sweep.compose's discipline: every fitted constant inside an index
    comes from the training years of the fold it is used in.

WPG and WVG are the only two indices with a fitted constant, which is what makes SPEC
9.2 vs 9.3 a one-variable comparison.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import bench  # noqa: E402

DATA = ROOT / "data"
ERSST = DATA / "ersst_v5_monthly.nc"

# SPEC 7: AGUv1 index boxes, 0-360 longitude, (lat_s, lat_n, lon_w, lon_e)
BOXES = {"nino34": (-5, 5, 190, 240),
         "iod_w": (-10, 10, 50, 70),
         "iod_e": (-10, 0, 90, 110),
         "wpac": (-5, 5, 130, 150),
         "wv": (5, 20, 130, 170)}

INDEX_NAMES = ("nino34", "iod", "wpg", "wvg", "iwhg")
LEADS = (0, 1, 2, 3)
WIDTH = 2
CONDITIONS = ("all", "lanina", "neg_wvg")
COND_GAP, COND_WIDTH = 0, 2
DAYS_PER_MONTH = np.array([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])

_SST_CACHE = None


def load_boxes(path=ERSST):
    """Per-box monthly SST anomalies as (year, month) grids, keyed by box name.

    Same structure and the same fixed 1991-2020 base as bench.load_sst, so the returned
    dict drops straight into bench.Context. SPEC 7 proves the fixed base is leak-neutral
    under a per-fold refitted model, which is why it is kept.
    """
    global _SST_CACHE
    if _SST_CACHE is not None:
        return _SST_CACHE
    da = xr.open_dataset(path)["sst"]
    if float(da.lon.min()) < 0:
        raise SystemExit("ERSST fixture is not on the 0-360 longitude convention")
    da = da.sortby("lat").sortby("lon")
    out = {}
    for name, (s, n, w, e) in BOXES.items():
        sub = da.sel(lat=slice(s, n), lon=slice(w, e))
        if sub.sizes["lat"] == 0 or sub.sizes["lon"] == 0:
            raise SystemExit(f"index box {name} selects no cells")
        series = sub.weighted(np.cos(np.deg2rad(sub.lat))).mean(["lat", "lon"])
        base = series.sel(time=slice(f"{bench.CLIM_BASE[0]}-01", f"{bench.CLIM_BASE[1]}-12"))
        clim = base.groupby("time.month").mean("time")
        anom = series.groupby("time.month") - clim
        anom = anom.assign_coords(year=anom["time.year"], month=anom["time.month"])
        out[name] = anom.set_index(time=["year", "month"]).unstack("time")
    _SST_CACHE = out
    return out


def raw_components(sst, months, years, gap, width=WIDTH):
    """The five raw box series at one (window, lead), one value per season-year."""
    ctx = bench.Context(sst, months, years, years, years, np.zeros(len(years)))
    return {b: ctx.feature(b, gap=gap, width=width, years=years) for b in BOXES}


def compose(name, comp, tr):
    """SPEC 7 index definitions. `tr` indexes the training years; every fitted constant
    inside the index comes from those years alone. Pass the full index set for the
    deliberately-leaky arm of SPEC 9.2."""
    def z(v):
        m, s = np.nanmean(v[tr]), np.nanstd(v[tr])
        return (v - m) / s if s > 0 else v * 0.0

    if name == "nino34":
        return comp["nino34"]
    if name == "iod":
        return comp["iod_w"] - comp["iod_e"]
    if name == "wpg":
        return z(comp["wpac"]) - z(comp["nino34"])
    if name == "wvg":
        return z(comp["nino34"]) - z(comp["wv"])
    if name == "iwhg":
        return (12 + 323 * (comp["iod_w"] - comp["iod_e"])
                - 193 * comp["wpac"] + 94 * comp["nino34"])
    raise ValueError(name)


def condition_mask(cname, comp0, tr, te):
    """SPEC 8. Boolean mask over the TEST indices `te`; thresholds fitted on TRAIN only.
    `comp0` is the raw component dict at the fixed conditioning lead (gap 0, width 2)."""
    if cname == "all":
        return np.ones(len(te), dtype=bool)
    if cname == "lanina":
        v = comp0["nino34"]
        m, sd = np.nanmean(v[tr]), np.nanstd(v[tr])
        return v[te] < (m - 0.5 * sd)
    if cname == "neg_wvg":
        v = compose("wvg", comp0, tr)
        return v[te] < np.nanpercentile(v[tr], 100.0 / 3.0)
    raise ValueError(cname)


# ── the predictand side: a zone-window's seasonal total ───────────────────────
def season_totals(monthly, month_of_col, year_of_col, cells, weights, months, years):
    """Area-weighted zone rainfall in mm, summed over `months`, one value per season-year.

    A window is labelled by the year of its LAST month, matching bench.build_target and
    bench.Context. SPEC 5 records that AGUv3 does not do this and that the difference is
    a legacy defect reproduced only in the legacy arm.

    Returns (values, ok) where ok marks season-years with every month present.
    """
    w = weights
    series = (monthly[cells] * w[:, None]).sum(0) / w.sum()          # mm/day per column
    mm = series * DAYS_PER_MONTH[month_of_col - 1]                   # mm/month

    wraps = months[0] > months[-1]
    roll = [m for m in months if m > months[-1]] if wraps else []
    label = np.where(np.isin(month_of_col, roll), year_of_col + 1, year_of_col)
    keep = np.isin(month_of_col, months)

    vals = np.full(len(years), np.nan)
    ok = np.zeros(len(years), dtype=bool)
    for i, y in enumerate(years):
        sel = keep & (label == y)
        if sel.sum() == len(months) and np.isfinite(mm[sel]).all():
            vals[i] = mm[sel].sum()
            ok[i] = True
    return vals, ok


def coverage_mask(sst, months, years, leads=LEADS, width=WIDTH):
    """SPEC 3: drop season-years whose deepest predictor window falls before the SST
    record, once per window so every candidate in that window sees an identical sample."""
    finite = np.ones(len(years), dtype=bool)
    for gap in leads:
        comp = raw_components(sst, months, years, gap, width)
        for v in comp.values():
            finite &= np.isfinite(v)
    return finite
