"""fetch_data.py — wide Kenya+Somalia CHIRPS field for AGUv3 zone discovery.

The AGUv2 eHorn file (38-50.5E, 4.5S-8.5N) is clipped: it excludes western Kenya
(<38E) and northern Somalia (>8.5N), so neither of the two validation gradients
(Kenya's meridional ~38E split, Somalia's zonal ~6-8N split) is in frame. This
fetches the full two-country window once, via the same rosetta product/cache the
v2 fetch used.
"""
from pathlib import Path
import acmaddl

OUT = Path(__file__).resolve().parents[1] / "data" / "kenya_somalia_chirps_monthly.nc"

# lat_s, lat_n, lon_w, lon_e — covers all of Kenya (33.9-41.9E, 4.7S-5.5N) and
# Somalia (41-51.4E, 1.6S-12N) with a small margin.
REGION = [-5.0, 12.0, 33.0, 52.0]

ds = acmaddl.fetch(
    product="obs/chirps-v3-monthly",
    variable="precip",
    region=REGION,
    hindcast=(1981, 2023),
    request_interval=0.3,
)
ds = ds.to_dataset(name="precip") if not hasattr(ds, "data_vars") else ds
ds.to_netcdf(OUT)
print("wrote", OUT, dict(ds.sizes))
