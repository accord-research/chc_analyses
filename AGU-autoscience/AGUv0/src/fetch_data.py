"""
fetch_data.py — cache the raw fields the Nigeria autoscience analyses need.

Everything downstream (seasonal partition, teleconnection diagnostics, hindcast
harness) reads from the cached NetCDFs written here, so the slow OPeNDAP pulls
happen exactly once. Re-running skips any file that already exists.

Products (via Rosetta):
  - obs/chirps-v3-monthly  precip over Nigeria (0.05 deg)      -> nigeria_chirps_monthly.nc
  - obs/ersst-v5           sst over the tropical belt (2 deg)  -> ersst_monthly.nc

Run inside the `accord-chc` conda env (has rosetta + deepscale + netCDF4).
"""
import sys, time, warnings
from pathlib import Path
warnings.filterwarnings("ignore")

import acmaddl
sys.path.insert(0, str(Path(__file__).resolve().parent))
from areas import BBOX, CHIRPS_FILE, LABEL

DATA = Path(__file__).resolve().parent.parent / "data"
DATA.mkdir(exist_ok=True)
# Tropical SST belt for teleconnection boxes (Atlantic + Indian + Pacific).
# ERSST is natively 0-360; request that so Nino3.4 (190-240E) and Atlantic (300-360E)
# are both present. teleconnections.py works in the 0-360 convention to match.
SST_BELT = [-40.0, 40.0, 0.0, 360.0]

# 1991-2023 is a robust 33-yr window: it is the standard WMO-adjacent climatology span, the
# ERSST anomaly base (1991-2020), and long enough for stable teleconnection correlations.
# CHIRPS v3 monthly downloads one COG per month over the `http` adapter with a per-file
# throttle, so trimming the span and lowering the interval is what makes the pull tractable.
START, END = 1991, 2023
CHIRPS_REQUEST_INTERVAL = 0.5   # seconds between monthly-COG downloads (product default 3.0)


def _save(ds, path, var=None):
    # OPeNDAP datasets carry bounds vars (time_bnds/nbnds) + inherited encodings that collide
    # on write ("NetCDF: String match to name in use"). Rebuild a clean dataset holding only
    # the data var(s) on lat/lon/time, with all attrs/encoding stripped.
    import xarray as xr
    keep_coords = {"lat", "lon", "time"}
    data_vars = [v for v in ds.data_vars if not any(
        k in str(v).lower() for k in ("bnds", "bounds", "spatial_ref"))]
    if var:
        data_vars = [var]
    clean = xr.Dataset()
    for v in data_vars:
        da = ds[v]
        for c in list(da.coords):
            if c not in keep_coords:
                da = da.drop_vars(c)
        da.attrs = {}
        da.encoding = {}
        clean[v] = da
    for c in list(clean.coords):
        clean[c].attrs = {}
        clean[c].encoding = {}
    clean.to_netcdf(path, engine="netcdf4")
    print(f"  wrote {path}  ({path.stat().st_size/1e6:.1f} MB)", flush=True)


def fetch_chirps():
    """Single fetch of the monthly record. The http adapter downloads one COG per month
    serially; lowering request_interval from the 3.0s product default is what makes the
    ~400-file pull tractable. Rosetta caches the raw result, so a re-run is instant."""
    out = DATA / CHIRPS_FILE
    if out.exists():
        print(f"[skip] {out.name} exists", flush=True)
        return
    n_months = (END - START + 1) * 12
    print(f"[chirps] fetching CHIRPS v3 monthly {LABEL} {START}-{END} "
          f"(~{n_months} monthly COGs, interval={CHIRPS_REQUEST_INTERVAL}s) ...", flush=True)
    t = time.time()
    ds = acmaddl.fetch(product="obs/chirps-v3-monthly", variable="precip",
                       region=BBOX, hindcast=(START, END),
                       request_interval=CHIRPS_REQUEST_INTERVAL,
                       verbose=False, progress=True)
    print(f"[chirps] done in {time.time()-t:.0f}s  dims={dict(ds.sizes)}", flush=True)
    _save(ds, out, var="precip")


def fetch_ersst():
    out = DATA / "ersst_monthly.nc"
    if out.exists():
        print(f"[skip] {out.name} exists", flush=True)
        return
    print(f"[ersst] fetching ERSST v5 monthly tropical belt {START}-{END} ...", flush=True)
    t = time.time()
    ds = acmaddl.fetch(product="obs/ersst-v5", variable="sst",
                       region=SST_BELT, hindcast=(START, END),
                       verbose=False, progress=False)
    print(f"[ersst] done in {time.time()-t:.0f}s  dims={dict(ds.sizes)}", flush=True)
    _save(ds, out)


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "chirps"):
        try:
            fetch_chirps()
        except Exception as e:
            print(f"[chirps] FAILED: {type(e).__name__}: {e}", flush=True)
    if which in ("all", "ersst"):
        try:
            fetch_ersst()
        except Exception as e:
            print(f"[ersst] FAILED: {type(e).__name__}: {e}", flush=True)
    print("=== fetch_data complete ===", flush=True)
