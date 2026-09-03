"""predictors.py — build the X (predictor) for each `predictor_source` × lead (AGUv1).

Four predictor constructions, all sharing the common hindcast period so configs are comparable:

  obs_sst_field  — observed pre-season ERSST field (perfect-prognosis; AGUv0's route)
  gcm_mos_sst    — NMME *forecast* SST field over a domain (dynamical SST predictor)
  gcm_mos_precip — NMME *forecast* precip over the target region (operational MOS, the WMO default)
  persistence    — antecedent zone-mean rainfall (non-SST scalar baseline)

Lead convention: `lead=L` means predictor information available ~L months before the season starts.
  * GCM sources: initialization month = season_start − L.
  * obs SST / persistence: the 3-month window ending L months before season start.

NMME fetches go through rosetta; under the CCSR outage `common/iridl_patch.apply()` re-points them to
the IRI Data Library (3 models). ERSST + CHIRPS come from the AGUv0 local cache.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import targets as T

HIND = (1993, 2016)                     # common period, n=24 (NMME hindcast range)
MODELS = ["nmme/cesm1", "nmme/ccsm4", "nmme/cansipsic4"]   # IRIDL-backed set
CLIM = (1991, 2020)
_ERSST = Path(__file__).resolve().parents[1].parent / "AGUv0" / "data" / "ersst_monthly.nc"

# SST predictor domains (lat_s, lat_n, lon_w, lon_e), lon in 0..360
SST_DOMAINS = {
    "indo_pacific": (-30, 30, 40, 300),
    "indian":       (-30, 30, 40, 120),
    "pacific":      (-30, 30, 120, 290),
    "global_trop":  (-30, 30, 0, 360),
}


def season_code(target: T.Target) -> str:
    return "".join(T._MONTH_ABBR[m] for m in target.months)


def init_month(target: T.Target, lead: int) -> int:
    return ((target.start_month - lead - 1) % 12) + 1


def _preseason_window(target: T.Target, lead: int) -> list[int]:
    """3 calendar months ending `lead` months before the season's first month."""
    end = (target.start_month - 1 - lead - 1) % 12 + 1     # last month of the predictor window
    return [((end - 1 - k) % 12) + 1 for k in range(2, -1, -1)]


# ─────────────────────────── observed ERSST field (perfect-prog) ───────────────────────────
def _load_ersst():
    ds = xr.open_dataset(_ERSST)
    sst = ds["sst"]
    if "zlev" in sst.dims:
        sst = sst.squeeze("zlev")
    lon360 = xr.where(sst.lon < 0, sst.lon + 360, sst.lon)
    return sst.assign_coords(lon=lon360).sortby("lon").sortby("lat")


def _monthly_anom(sst):
    clim = sst.sel(time=slice(f"{CLIM[0]}-01", f"{CLIM[1]}-12")).groupby("time.month").mean("time")
    return sst.groupby("time.month") - clim


def obs_sst_field(target: T.Target, lead: int, domain="indo_pacific", coarsen=2) -> xr.DataArray:
    """Observed pre-season SST anomaly field over the domain, seasonal-mean per year (year,lat,lon)."""
    sst = _load_ersst()
    b = SST_DOMAINS[domain]
    sst = sst.sel(lat=slice(b[0], b[1]), lon=slice(b[2], b[3]))
    an = _monthly_anom(sst)
    months = _preseason_window(target, lead)
    sub = an.sel(time=an["time.month"].isin(months))
    # assign each record to the season YEAR (predictor precedes the target season within the same yr)
    yr = sub["time.year"]
    fld = sub.groupby(yr.rename("year")).mean("time")
    fld = fld.sel(year=slice(*HIND))
    if coarsen > 1:
        fld = fld.coarsen(lat=coarsen, lon=coarsen, boundary="trim").mean()
    return fld.where(np.isfinite(fld))


# ─────────────────────────── NMME forecast fields (via rosetta / IRIDL) ───────────────────────────
def _fetch(model, variable, target, lead, region):
    import acmaddl
    g = acmaddl.fetch(product=model, variable=variable, init=f"{HIND[1]}-{init_month(target, lead):02d}",
                      target=season_code(target), region=list(region), hindcast=HIND,
                      year_index=True, verbose=False, progress=False)
    return g[list(g.data_vars)[0]]


def gcm_mos_sst(target: T.Target, lead: int, domain="indo_pacific", coarsen=2) -> dict:
    """Per-model NMME forecast SST field over the domain → predictor tracks for seasonal_mme."""
    b = SST_DOMAINS[domain]
    tracks = {}
    for m in MODELS:
        try:
            da = _fetch(m, "sst", target, lead, b).where(lambda d: d < 100)
            if coarsen > 1:
                da = da.coarsen(lat=coarsen, lon=coarsen, boundary="trim").mean()
            tracks[m.split("/")[-1].upper()] = da
        except Exception as e:
            print(f"    [skip {m} sst] {type(e).__name__}: {str(e)[:60]}")
    return tracks


def gcm_mos_precip(target: T.Target, lead: int, coarsen=4) -> dict:
    """Per-model NMME forecast precip over the target region → predictor tracks (operational MOS)."""
    tracks = {}
    for m in MODELS:
        try:
            da = _fetch(m, "precip", target, lead, target.bbox)
            if coarsen > 1:
                da = da.coarsen(lat=coarsen, lon=coarsen, boundary="trim").mean()
            tracks[m.split("/")[-1].upper()] = da
        except Exception as e:
            print(f"    [skip {m} precip] {type(e).__name__}: {str(e)[:60]}")
    return tracks


# ─────────────────────────── persistence (scalar) ───────────────────────────
def persistence(target: T.Target, lead: int) -> xr.DataArray:
    """Antecedent zone-mean rainfall over the pre-season window (year,)."""
    p = T.load_precip(target.bbox, target.chirps).mean(["lat", "lon"])
    months = _preseason_window(target, lead)
    sub = p.sel(time=p["time.month"].isin(months))
    ser = sub.groupby("time.year").sum("time").rename(year="year") if "time" in sub.dims else sub
    ser = sub.groupby(sub["time.year"].rename("year")).mean("time")
    return ser.sel(year=slice(*HIND))


if __name__ == "__main__":
    import iridl_patch  # noqa
    tgt = T.discover_targets()[1]   # Kenya:OND
    print("target:", tgt.name, "code:", season_code(tgt))
    for L in (0, 3):
        print(f"  lead {L}: init month {init_month(tgt, L)}, preseason window {_preseason_window(tgt, L)}")
    f = obs_sst_field(tgt, 1)
    print("obs_sst_field OND L1:", dict(f.sizes), "finite frac",
          float(np.isfinite(f).mean()))
    per = persistence(tgt, 1)
    print("persistence OND L1:", dict(per.sizes), "mean", float(per.mean()))
