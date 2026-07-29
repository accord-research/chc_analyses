"""indices.py — the engineered SST indices used operationally for the eastern Horn (AGUv1 extension).

These are the hand-built scalar predictors the operational centres (UCSB CHC / FEWS NET) use, added
so the search can test them against the discovered SST-field CCA:

  nino34  — Niño-3.4 SST anomaly (ENSO)
  iod     — Indian Ocean Dipole = west (WIO) minus east (EIO) SST
  wpg     — West-Pacific gradient = std(equatorial West-Pacific SST) − std(Niño-3.4)
  wvg     — Western-V gradient    = std(Niño-3.4) − std(NW-subtropical-Pacific SST)
  iwhg    — Indo-warm-pool heating gradient, SST estimate (Funk et al.):
            12 + 323·IOD − 193·WestPac + 94·Niño34   (an approximation of the ERA5-heating index)

Each is computed from a seasonal-mean SST **anomaly** field (year, lat, lon) that spans the
indo-Pacific — so both the observed field and an NMME forecast field yield the same index, giving a
perfect-prognosis (`obs_index`) and an operational forecast (`gcm_index`) variant with no extra
fetches. Box definitions follow the standard/operational conventions; WVG and IWHG are documented
approximations. Longitudes are 0–360.
"""
from __future__ import annotations
import numpy as np
import xarray as xr

INDEX_NAMES = ("nino34", "iod", "wpg", "wvg", "iwhg")

_BOX = {  # (lat_s, lat_n, lon_w, lon_e)
    "nino34": (-5, 5, 190, 240),
    "iod_w":  (-10, 10, 50, 70),
    "iod_e":  (-10, 0, 90, 110),
    "wpac":   (-5, 5, 130, 150),
    "wv":     (5, 20, 130, 170),
}


def _box_mean(field: xr.DataArray, name: str) -> xr.DataArray:
    s, n, w, e = _BOX[name]
    sub = field.sel(lat=slice(s, n), lon=slice(w, e))
    wgt = np.cos(np.deg2rad(sub.lat))
    return sub.weighted(wgt).mean(["lat", "lon"])


def _z(a: xr.DataArray) -> xr.DataArray:
    sd = a.std("year")
    return (a - a.mean("year")) / sd.where(sd > 0)


def index_from_field(field: xr.DataArray, name: str) -> xr.DataArray:
    """Scalar index series (year,) from a seasonal SST field. The field is anomalized per cell first,
    so an absolute (GCM) or anomaly (obs) field gives the same interannual index."""
    an = field - field.mean("year")
    n34 = _box_mean(an, "nino34")
    iod = _box_mean(an, "iod_w") - _box_mean(an, "iod_e")
    wpac = _box_mean(an, "wpac")
    if name == "nino34":
        return n34
    if name == "iod":
        return iod
    if name == "wpg":
        return _z(wpac) - _z(n34)
    if name == "wvg":
        return _z(n34) - _z(_box_mean(an, "wv"))
    if name == "iwhg":
        return 12 + 323 * iod - 193 * wpac + 94 * n34
    raise ValueError(name)
