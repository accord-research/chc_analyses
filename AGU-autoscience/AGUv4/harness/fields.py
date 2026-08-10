"""fields.py — load the locked fixtures into the flat arrays everything else consumes.

One place converts CHIRPS from a (time, lat, lon) NetCDF into the (n_cell, n_col) matrix
plus coordinate vectors that discovery, scoring and the benchmarks all take. Doing it
once means the coarsening, the cell ordering and the month/year axes cannot drift
between the fast path, the slow path and the legacy arm.

Cached to outputs/cache/ keyed by the fixture sha256 (SPEC 15), so 1,200 null replicates
pay the NetCDF cost once.
"""
from __future__ import annotations

import hashlib
import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CACHE = ROOT / "outputs" / "cache"
CHIRPS = DATA / "chirps_v3_ea_monthly.nc"
COARSEN = 5                       # 0.05 deg -> 0.25 deg (SPEC 1.1)


@dataclass
class Field:
    monthly: np.ndarray           # (n_cell, n_col) mm/day
    lats: np.ndarray              # (n_cell,)
    lons: np.ndarray              # (n_cell,)
    month_of_col: np.ndarray      # (n_col,) 1..12
    year_of_col: np.ndarray       # (n_col,)
    years: np.ndarray             # unique season-year axis
    shape: tuple                  # (n_lat, n_lon) for un-flattening to a map
    lat_axis: np.ndarray
    lon_axis: np.ndarray


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_chirps(path=CHIRPS, coarsen=COARSEN, use_cache=True):
    CACHE.mkdir(parents=True, exist_ok=True)
    key = CACHE / f"chirps_{_sha(path)[:16]}_c{coarsen}.pkl"
    if use_cache and key.exists():
        with open(key, "rb") as f:
            return pickle.load(f)

    da = xr.open_dataset(path)["precip"]
    da = da.coarsen(lat=coarsen, lon=coarsen, boundary="trim").mean()
    da = da.transpose("lat", "lon", "time")
    vals = da.values.reshape(-1, da.sizes["time"])                  # (n_cell, n_col)
    lat_axis = da.lat.values
    lon_axis = da.lon.values
    lats = np.repeat(lat_axis, len(lon_axis))
    lons = np.tile(lon_axis, len(lat_axis))
    fld = Field(monthly=vals.astype(float), lats=lats, lons=lons,
                month_of_col=da["time.month"].values.astype(int),
                year_of_col=da["time.year"].values.astype(int),
                years=np.unique(da["time.year"].values).astype(int),
                shape=(len(lat_axis), len(lon_axis)),
                lat_axis=lat_axis, lon_axis=lon_axis)
    if use_cache:
        with open(key, "wb") as f:
            pickle.dump(fld, f, protocol=pickle.HIGHEST_PROTOCOL)
    return fld


def permute_field(fld, perm):
    """SPEC 14's null replicate: one permutation of the season-year index, applied
    identically to every cell of the rainfall field.

    Whole 12-month calendar-year blocks move together, so a permuted field is still a
    field of complete years and every cell is reordered the same way -- cross-cell
    correlation survives into the null, which is the point.

    Everything downstream then runs on the permuted field: the valid-cell mask, both
    feature blocks, the EOF basis, the bootstrap ARI curve, k, the partition, the annual
    cycles, the windows and the seasonal totals. That is what makes a null replicate a
    COMPLETE discovery run rather than a re-scoring of a fixed atlas. SPEC 14 proves the
    invariance only holds on the full record, not inside a fold, which is precisely why
    discovery cannot be cached across replicates.

    The SST predictors are never touched.
    """
    src_cols = {int(y): np.flatnonzero(fld.year_of_col == y) for y in fld.years}
    out = np.empty_like(fld.monthly)
    for i, y in enumerate(fld.years):
        dst = src_cols[int(y)]
        src = src_cols[int(fld.years[perm[i]])]
        if len(dst) != len(src):
            raise ValueError(f"year {y} has {len(dst)} months, donor has {len(src)}")
        out[:, dst] = fld.monthly[:, src]
    return out


def to_map(fld, cell_index, values, fill=np.nan):
    """Scatter per-cell values back onto the (lat, lon) grid for plotting."""
    flat = np.full(fld.monthly.shape[0], fill, dtype=float)
    flat[cell_index] = values
    return flat.reshape(fld.shape)
