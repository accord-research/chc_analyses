"""targets.py — seasonality → rainy-season anomaly targets (AGUv1, critique #2 step 1).

The forecast targets are *derived*, not assumed: we read the region's climatological annual cycle
from CHIRPS, detect its wet windows, and emit each as a 3-month **rainy-season anomaly** target.
For Kenya this recovers the bimodal MAM ("long rains") and OND ("short rains") seasons. Everything
downstream (the search, the lead/COF analysis) is organized around these discovered targets.

The predictand for a target is the coarsened gridded seasonal rainfall over the region (so CCA and
downscaling are meaningful, unlike v0's zonal means). Uses the CHIRPS cache from AGUv0.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import xarray as xr
import africas2s

# Region config: bbox (lat_s, lat_n, lon_w, lon_e) + the cached CHIRPS monthly file for each.
_V1 = Path(__file__).resolve().parents[1]
REGIONS = {
    "Kenya":   dict(bbox=(-5.0, 5.0, 34.0, 42.0), chirps=_V1.parent / "AGUv0" / "data" / "kenya_chirps_monthly.nc"),
    "Somalia": dict(bbox=(-2.0, 12.0, 41.0, 51.0), chirps=_V1 / "data" / "somalia_chirps_monthly.nc"),
}
KENYA_BBOX = REGIONS["Kenya"]["bbox"]   # back-compat
_MONTH_ABBR = ["", "J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]


@dataclass(frozen=True)
class Target:
    name: str               # e.g. "Kenya:OND"
    months: tuple           # (10, 11, 12)
    bbox: tuple             # predictand region
    label: str              # human season label, e.g. "OND short rains"
    region: str = "Kenya"   # region key into REGIONS (chooses the CHIRPS file)

    @property
    def start_month(self) -> int:
        return self.months[0]

    @property
    def chirps(self) -> Path:
        return REGIONS[self.region]["chirps"]


def load_precip(bbox=KENYA_BBOX, chirps=None) -> xr.DataArray:
    ds = xr.open_dataset(chirps if chirps is not None else REGIONS["Kenya"]["chirps"])
    return ds["precip"].sel(lat=slice(bbox[0], bbox[1]), lon=slice(bbox[2], bbox[3]))


def annual_cycle(precip: xr.DataArray) -> np.ndarray:
    """12-value climatological monthly mean rainfall over the domain (mm/month)."""
    dom = precip.mean(["lat", "lon"])
    clim = dom.groupby("time.month").mean("time")
    return clim.reindex(month=range(1, 13)).values


def detect_seasons(cycle: np.ndarray, min_frac: float = 0.55) -> list[tuple[int, int, int]]:
    """Detect wet 3-month windows from the annual cycle. Returns list of (start,mid,end) month
    triples centered on circular local maxima whose peak exceeds `min_frac` of the annual max.
    Robust to bimodality (Kenya) and unimodality."""
    c = np.asarray(cycle, float)
    thr = min_frac * np.nanmax(c)
    peaks = []
    for m in range(12):                       # circular local maxima above threshold
        prev, nxt = c[(m - 1) % 12], c[(m + 1) % 12]
        if c[m] >= prev and c[m] >= nxt and c[m] >= thr:
            peaks.append(m)
    # merge adjacent/near-duplicate peaks (keep the higher), enforce >=3 months apart
    peaks = sorted(peaks, key=lambda m: -c[m])
    kept = []
    for m in peaks:
        if all(min((m - k) % 12, (k - m) % 12) >= 3 for k in kept):
            kept.append(m)
    seasons = []
    for m in sorted(kept):
        mid = m + 1                            # month index (1-12)
        tri = tuple(((mid - 2 + i) % 12) + 1 for i in range(3))  # 3-month window centered on peak
        seasons.append(tri)
    return seasons


def discover_targets(regions=None) -> list[Target]:
    """Auto-detect each region's rainy-season targets from its CHIRPS annual cycle. Skips a region
    whose CHIRPS file is not yet present (e.g. a still-downloading fetch)."""
    out = []
    for region in (regions or list(REGIONS)):
        cfg = REGIONS[region]
        if not Path(cfg["chirps"]).exists():
            continue
        cyc = annual_cycle(load_precip(cfg["bbox"], cfg["chirps"]))
        for tri in detect_seasons(cyc):
            name_abbr = "".join(_MONTH_ABBR[m] for m in tri)
            season = "short rains" if 10 in tri or 11 in tri else ("long rains" if 3 in tri or 4 in tri else "rains")
            out.append(Target(name=f"{region}:{name_abbr}", months=tri, bbox=cfg["bbox"],
                              label=f"{name_abbr} {season}", region=region))
    return out


def predictand(target: Target, coarsen: int = 10, hindcast=(1993, 2016)) -> xr.DataArray:
    """Coarsened gridded seasonal rainfall total for the target's region & months, sliced to the
    common hindcast period (so obs- and GCM-predictor configs share years)."""
    p = load_precip(target.bbox, target.chirps)
    seasonal = africas2s.seasonal_reduce(p, list(target.months))         # (year, lat, lon)
    seasonal = seasonal.sel(year=slice(*hindcast))
    return seasonal.coarsen(lat=coarsen, lon=coarsen, boundary="trim").mean()


def predictand_anomaly(target: Target, **kw) -> xr.DataArray:
    """Standardized rainy-season anomaly (the 'rainy-season anomaly' target framing)."""
    s = predictand(target, **kw)
    return (s - s.mean("year")) / s.std("year")


if __name__ == "__main__":
    cyc = annual_cycle(load_precip())
    print("Kenya annual cycle (mm/month):")
    print("  " + "  ".join(f"{_MONTH_ABBR[m]}:{cyc[m-1]:.0f}" for m in range(1, 13)))
    tgts = discover_targets()
    print(f"\ndiscovered {len(tgts)} targets:")
    for t in tgts:
        print(f"  {t.name:12s} months={t.months} — {t.label}")
        pa = predictand(t)
        print(f"     predictand grid {dict(pa.sizes)}, mean {float(pa.mean()):.1f} mm")
