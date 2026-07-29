"""
demo_hindcast_logit.py — one REAL end-to-end, cross-validated skill result.

This turns the "featurized-index" calibration path (axis E-(ii), method=logit) from scaffold
into a genuine number, using only cached observations — no GCM download. It fits DeepScale's
logistic index calibration from a pre-season SST index to CHIRPS tercile occurrence, under
leave-one-year-out (LOYO) cross-validation, and scores the held-out forecasts.

It is deliberately a single configuration (JAS, Sudano-Sahel band, one index), not the full
matrix search — a proof that the loop closes on real data and real skill. The multi-model
CCA/ereg paths in hindcast.py are the compute-bound extension.

Outputs
  outputs/figures/demo_logit_skill_map.png   per-cell skill of the index->tercile forecast
  outputs/tables/demo_logit_skill.json       headline CV skill scalars

Run in accord-chc after fetch_data.py (needs CHIRPS + ERSST cache).
"""
import warnings, json, sys
from pathlib import Path
warnings.filterwarnings("ignore")

import numpy as np
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import teleconnections as T   # reuse SST-index construction

import deepscale

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"
for d in (FIG, TAB):
    d.mkdir(parents=True, exist_ok=True)

SEASON_MONTHS = [7, 8, 9]      # JAS
BAND = (11, 14)                # Sudano-Sahel
COARSEN = 10                   # 0.05deg -> 0.5deg for a fast, stable demo
INDEX = sys.argv[1] if len(sys.argv) > 1 else "nino34"   # CLI: which SST index to calibrate


def obs_terciles_series():
    ds = xr.open_dataset(DATA / "nigeria_chirps_monthly.nc")
    p = ds["precip"].sel(lat=slice(*BAND))
    p = p.coarsen(lat=COARSEN, lon=COARSEN, boundary="trim").mean()
    sel = p.sel(time=p["time.month"].isin(SEASON_MONTHS))
    seasonal = sel.groupby("time.year").sum("time")   # (year, lat, lon)
    return seasonal


def index_series():
    sst = T.load_sst()
    idx = T.build_indices(sst)[INDEX]
    pre = T.index_preseason_mean(idx, SEASON_MONTHS)  # (year,)
    return pre


def main():
    obs = obs_terciles_series()
    idx = index_series()
    yrs = np.intersect1d(obs.year.values, idx.year.values)
    obs = obs.sel(year=yrs)
    idx = idx.sel(year=yrs)
    n = len(yrs)
    print(f"[demo] {n} years {int(yrs.min())}-{int(yrs.max())}, obs grid {dict(obs.sizes)}", flush=True)

    # observed tercile category per year/cell (0,1,2) from the sample terciles
    q33 = obs.quantile(1/3, "year"); q67 = obs.quantile(2/3, "year")
    obs_cat = xr.where(obs <= q33, 0, xr.where(obs >= q67, 2, 1))

    # LOYO: leave out each year, fit logit on the rest, predict the held-out year's probs
    probs = []
    for i, y in enumerate(yrs):
        train_years = [int(z) for z in yrs if z != y]
        hind = idx.sel(year=train_years)
        obs_train = obs.sel(year=train_years)
        fcst_val = float(idx.sel(year=int(y)).values)
        p = deepscale.calibrate(hind, obs_train, method="logit", forecast=fcst_val)
        probs.append(p.assign_coords(year=int(y)))
    probs = xr.concat(probs, dim="year").transpose("year", "tercile", "lat", "lon")

    # --- skill: ranked probability skill score (RPSS) vs climatology, per cell ---
    # observed cumulative tercile (one-hot) and forecast cumulative
    obs_oh = xr.concat([(obs_cat == k) for k in range(3)], dim="tercile").transpose("year", "tercile", "lat", "lon").astype(float)
    def rps(fp):
        fc = fp.cumsum("tercile"); oc = obs_oh.cumsum("tercile")
        return ((fc - oc) ** 2).sum("tercile").mean("year")
    rps_fcst = rps(probs)
    clim = xr.zeros_like(probs) + 1/3
    rps_clim = rps(clim)
    rpss = 1 - rps_fcst / rps_clim

    # --- also: correlation of P(below) with observed below occurrence (interpretable) ---
    p_below = probs.isel(tercile=0)
    o_below = (obs_cat == 0).astype(float)
    pb = (p_below - p_below.mean("year")); ob = (o_below - o_below.mean("year"))
    corr_below = (pb * ob).mean("year") / (pb.std("year") * ob.std("year") + 1e-9)

    rec = {
        "config": f"JAS Sudano-Sahel, logit on {INDEX}, LOYO, {int(yrs.min())}-{int(yrs.max())}",
        "n_years": int(n),
        "grid": dict(obs.sizes),
        "rpss_mean": round(float(rpss.mean()), 3),
        "rpss_frac_positive": round(float((rpss > 0).mean()), 3),
        "corr_below_mean": round(float(corr_below.mean()), 3),
    }
    (TAB / f"demo_logit_skill_{INDEX}.json").write_text(json.dumps(rec, indent=2))
    print("[demo] skill record:", json.dumps(rec, indent=2), flush=True)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    rpss.plot(ax=axes[0], cmap="RdBu_r", vmin=-0.5, vmax=0.5,
              cbar_kwargs={"label": "RPSS"})
    axes[0].set_title(f"RPSS: logit({INDEX}) -> JAS Sudano-Sahel terciles (LOYO)")
    corr_below.plot(ax=axes[1], cmap="RdBu_r", vmin=-0.8, vmax=0.8,
                    cbar_kwargs={"label": "corr(P_below, obs below)"})
    axes[1].set_title("Below-normal probability skill")
    fig.tight_layout(); fig.savefig(FIG / f"demo_logit_skill_map_{INDEX}.png", dpi=150)
    print("[demo] wrote", FIG / f"demo_logit_skill_map_{INDEX}.png", flush=True)


if __name__ == "__main__":
    main()
