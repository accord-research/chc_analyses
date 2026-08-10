"""orient.py — Phase 0 orientation: what is inherited, what exists, what is missing.

This probe writes nothing and scores nothing. It answers four questions that SPEC.md
has to answer before any research code is written:

  1. Does the inherited v4zeek harness import and pass its own calendar test here?
  2. What is actually inside the CHIRPS v3 fixture — domain, years, grid, land cells?
  3. Which SST fixtures exist in this project, and which are missing?
  4. What is the pinned environment?

Archived under legacy/probes/ after Phase 0; not on the regeneration path.
Run: rx run exec -e e:1 -- conda run -n pycpt python legacy/probes/orient.py
"""
from __future__ import annotations

import hashlib
import importlib
import platform
import subprocess
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT))

CHIRPS = DATA / "chirps_v3_ea_monthly.nc"
DOMAIN = (-5.0, 12.0, 33.0, 52.0)      # lat_s, lat_n, lon_w, lon_e — the AGUv3 domain
COARSEN = 5                            # 0.05 deg -> 0.25 deg, as AGUv3/src/zones.py
CLIM = (1991, 2020)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rule(title):
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}", flush=True)


# ── 1. inherited harness ──────────────────────────────────────────────────────
rule("1. INHERITED HARNESS")
import bench            # noqa: E402
import batched          # noqa: E402

for name, mod in (("bench", bench), ("batched", batched)):
    p = Path(mod.__file__)
    print(f"  {name:8s} {p.name:12s} sha256={sha256(p)[:16]}  {p.stat().st_size:6d} B")
for extra in ("candidates/climatology.py", "tests/test_wrap.py", "probes/grid_sweep.py"):
    p = ROOT / extra
    print(f"  {'copied':8s} {extra:24s} sha256={sha256(p)[:16]}")

print("\n  symbols required by SPEC:")
for sym in ("Context", "make_folds", "build_target", "build_synthetic", "load_sst",
            "evaluate", "OutOfSampleRPSS", "CLIM_BASE", "DAYS_PER_MONTH"):
    print(f"    bench.{sym:18s} {'OK' if hasattr(bench, sym) else 'MISSING'}")
for sym in ("score_block_dynamic", "_detrend_rows"):
    print(f"    batched.{sym:16s} {'OK' if hasattr(batched, sym) else 'MISSING'}")

print("\n  calendar test (tests/test_wrap.py):", flush=True)
rc = subprocess.run([sys.executable, str(ROOT / "tests" / "test_wrap.py")],
                    capture_output=True, text=True)
print("    " + "\n    ".join(rc.stdout.strip().splitlines()))
print(f"    exit={rc.returncode}")

# ── 2. the CHIRPS fixture ─────────────────────────────────────────────────────
rule("2. CHIRPS v3 FIXTURE")
if not CHIRPS.exists():
    print(f"  MISSING {CHIRPS}")
else:
    print(f"  path   {CHIRPS.relative_to(ROOT)}")
    print(f"  bytes  {CHIRPS.stat().st_size}")
    print(f"  sha256 {sha256(CHIRPS)}")
    da = xr.open_dataset(CHIRPS)["precip"]
    print(f"  dims   {dict(da.sizes)}")
    print(f"  lat    {float(da.lat.min()):.4f} .. {float(da.lat.max()):.4f}  "
          f"(n={da.sizes['lat']}, step={float(da.lat[1] - da.lat[0]):.4f})")
    print(f"  lon    {float(da.lon.min()):.4f} .. {float(da.lon.max()):.4f}  "
          f"(n={da.sizes['lon']}, step={float(da.lon[1] - da.lon[0]):.4f})")
    yrs = np.unique(da["time.year"].values)
    print(f"  years  {yrs.min()}..{yrs.max()}  ({len(yrs)} years, {da.sizes['time']} months)")
    months_per_year = {int(y): int((da["time.year"].values == y).sum()) for y in yrs}
    short = {y: m for y, m in months_per_year.items() if m != 12}
    print(f"  incomplete years: {short if short else 'none'}")

    co = da.coarsen(lat=COARSEN, lon=COARSEN, boundary="trim").mean()
    print(f"\n  coarsened x{COARSEN} -> {dict(co.sizes)}  "
          f"(lat step {float(co.lat[1] - co.lat[0]):.3f})")
    clim = co.sel(time=(co["time.year"] >= CLIM[0]) & (co["time.year"] <= CLIM[1]))
    cyc = clim.groupby("time.month").mean("time")
    stack = cyc.stack(cell=("lat", "lon")).transpose("cell", "month")
    C = stack.values
    good = np.isfinite(C).all(axis=1) & (C.sum(axis=1) > 1e-3)
    print(f"  cells total {C.shape[0]}, valid land cells {int(good.sum())} "
          f"({good.mean():.1%})   [AGUv3 reported 1144+2420 = 3564 at k=2]")
    lat_g = np.array([c[0] for c in stack.cell.values])[good]
    print(f"  cos(lat) weight range {np.cos(np.deg2rad(lat_g)).min():.4f} .. "
          f"{np.cos(np.deg2rad(lat_g)).max():.4f}")

# ── 3. SST fixtures ───────────────────────────────────────────────────────────
rule("3. SST FIXTURES IN THIS PROJECT")
found = sorted(DATA.glob("*.nc"))
for f in found:
    print(f"  {f.name:34s} {f.stat().st_size / 1e6:8.1f} MB")
if not any("sst" in f.name for f in found):
    print("  NO SST FIXTURE PRESENT.")
print("\n  rosetta catalog check for an ERSST product:")
try:
    import rosetta
    cat = Path(rosetta.__file__).parent / "catalog.yaml"
    keys = [ln.split(":")[0] for ln in cat.read_text().splitlines()
            if ln and not ln[0].isspace() and ln.rstrip().endswith(":")]
    hits = [k for k in keys if "ersst" in k.lower()]
    print(f"    catalog has {len(keys)} products; ersst matches: {hits if hits else 'NONE'}")
    print(f"    obs/* products: {[k for k in keys if k.startswith('obs/')]}")
except Exception as e:
    print(f"    rosetta import failed: {type(e).__name__}: {e}")

# ── 4. environment ────────────────────────────────────────────────────────────
rule("4. ENVIRONMENT")
print(f"  python      {platform.python_version()}  ({sys.executable})")
print(f"  platform    {platform.platform()}  {platform.machine()}")
for m in ("numpy", "xarray", "scipy", "sklearn", "netCDF4", "matplotlib",
          "cartopy", "rosetta", "deepscale"):
    try:
        mod = importlib.import_module(m)
        print(f"  {m:11s} {getattr(mod, '__version__', '?'):12s} {mod.__file__}")
    except Exception as e:
        print(f"  {m:11s} UNAVAILABLE ({type(e).__name__})")
try:
    from deepscale.metrics.rpss import _cpt_boundaries
    v = np.arange(30, dtype=float)
    print(f"  deepscale._cpt_boundaries(arange(30)) = {_cpt_boundaries(v)}")
except Exception as e:
    print(f"  deepscale._cpt_boundaries UNAVAILABLE: {type(e).__name__}: {e}")

print("\norientation complete", flush=True)
