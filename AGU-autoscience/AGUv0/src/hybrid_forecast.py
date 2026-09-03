"""
hybrid_forecast.py — bridge the dynamical MME and the perfect-prognosis ceiling.

The pure dynamical MME (mme_search/mme_methods) had no real skill for Nigeria, yet the
observation-only ceiling shows the seasons ARE predictable from the ocean state. The diagnosis
was: GCMs forecast the *ocean state* (especially ENSO) far better than they forecast *rainfall*.
The hybrid tests that directly:

  take each GCM's FORECAST SST (the thing it does well), reduce it to the physically-relevant
  index for the zone (the basin the domain search selected), and feed that forecast index into
  the OBSERVATION-trained SST->rainfall relationship — instead of asking the model to forecast
  rainfall itself.

We compare, in the same metric (deterministic LOYO correlation of predicted vs observed
zone-mean rainfall):
  - ceiling(concurrent) : observed target-season SST index -> rainfall  (perfect model upper bound)
  - HYBRID              : MME-forecast target-season SST index -> rainfall
  - pure MME            : the dynamical CCA forecast (from mme_search) — near zero
and report how well the MME forecasts the SST index itself (corr of forecast vs observed index),
which is what limits the hybrid.

Outputs
  outputs/tables/hybrid_forecast.csv
  outputs/tables/hybrid_vs_mme.md
  outputs/figures/hybrid_forecast.png

Run in accord-chc after fetch_data.py (uses cached CHIRPS + ERSST; NMME SST via Rosetta).
"""
import warnings, csv, sys
from pathlib import Path

warnings.filterwarnings("ignore")
import numpy as np
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import acmaddl
import africas2s
sys.path.insert(0, str(Path(__file__).resolve().parent))
import teleconnections as T
from areas import AREA, BANDS, CHIRPS_FILE, LABEL, suffix

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"
for d in (FIG, TAB):
    d.mkdir(parents=True, exist_ok=True)

HIND = (1993, 2016)
MODELS = ["nmme/geoss2s", "nmme/cesm1", "nmme/ccsm4", "nmme/cansipsic4"]

# index chosen from the observation-only feature search (best driver per target), computed from
# each model's FORECAST SST. `spec` is a box (S,N,W,E) in 0-360, or a west-minus-east dipole.
# pure_MME_r is a reference from mme_search (nan where not looked up).
NINO34 = (-5, 5, 190, 240)
ATL3 = (-3, 3, 340, 360)
IOD = {"west": (-10, 10, 50, 70), "east": (-10, 0, 90, 110)}
# Atlantic interhemispheric gradient (TNA − TSA) — the classical Sahel driver (Giannini 2003,
# Rowell 2003), and an Atlantic index GCMs forecast poorly. Expressed as a west−east dipole.
ATL_GRAD = {"west": (5.5, 23.5, 302.5, 345), "east": (-20, 0, 330, 360)}
# Indices are the physically-appropriate / search-consistent driver per target (not a single
# convention): Sahel = Atlantic gradient (NOT nino34); Guinea/Middle = Atlantic Niño; E. African
# short rains = IOD; ENSO for Kiremt. MAM uses nino34 as an ENSO proxy (the season is low-skill
# regardless — see the benchmark).
#   (label, season, init_month, band_name, months, index_name, spec, pure_MME_r)
_TARGETS = {
    "nigeria": [
        ("JAS Sahel",    "JAS", 5, "North",    [7, 8, 9],   "atl_grad", ATL_GRAD, -0.02),
        ("JAS Middle",   "JAS", 5, "Middle",   [7, 8, 9],   "atl3",     ATL3,     -0.03),
        ("OND National", "OND", 8, "National", [10, 11, 12], "iod_dmi",  IOD,       0.01),
    ],
    # For E. Africa the rainfall-relevant drivers (ENSO for Kiremt, IOD for the short rains) are
    # ones GCMs forecast comparatively well — unlike Nigeria's Atlantic indices.
    "ethiopia": [
        ("JAS Kiremt (N)", "JAS", 5, "North", [7, 8, 9],   "nino34",  NINO34, float("nan")),
        ("MAM South",      "MAM", 2, "South", [3, 4, 5],    "nino34",  NINO34, float("nan")),
        ("OND South",      "OND", 8, "South", [10, 11, 12], "iod_dmi", IOD,    float("nan")),
    ],
    "kenya": [
        ("OND National", "OND", 8, "National", [10, 11, 12], "iod_dmi", IOD,    float("nan")),
        ("MAM National", "MAM", 2, "National", [3, 4, 5],    "nino34",  NINO34, float("nan")),
        ("OND South",    "OND", 8, "South",    [10, 11, 12], "iod_dmi", IOD,    float("nan")),
    ],
}[AREA]
TARGETS = [(lbl, s, im, BANDS[bn], mo, iname, spec, r)
           for (lbl, s, im, bn, mo, iname, spec, r) in _TARGETS]


def box_mean(da, box):
    s, n, w, e = box
    sub = da.sel(lat=slice(s, n))
    if e > 360:
        sub = xr.concat([sub.sel(lon=slice(w, 360)), sub.sel(lon=slice(0, e - 360))], dim="lon")
    else:
        sub = sub.sel(lon=slice(w, e))
    return sub.mean(["lat", "lon"])


def compute_index(da, spec):
    """spec is a box (S,N,W,E) or a dipole dict {west:box, east:box} -> west - east."""
    if isinstance(spec, dict):
        return box_mean(da, spec["west"]) - box_mean(da, spec["east"])
    return box_mean(da, spec)


def spec_region(spec):
    if isinstance(spec, dict):
        boxes = [spec["west"], spec["east"]]
        s = min(b[0] for b in boxes); n = max(b[1] for b in boxes)
        w = min(b[2] for b in boxes); e = max(b[3] for b in boxes)
        return [s, n, w, e]
    return [spec[0], spec[1], spec[2], spec[3]]


def model_forecast_index(target, init_m, spec):
    """MME-mean of each model's ensemble-mean forecast SST index, per year."""
    region = spec_region(spec)
    series = []
    for prod in MODELS:
        try:
            g = acmaddl.fetch(product=prod, variable="sst", init=f"{HIND[1]}-{init_m:02d}",
                              target=target, region=region, hindcast=HIND, year_index=True,
                              verbose=False, progress=False)
            da = g[list(g.data_vars)[0]]
            da = da.where(da < 100)                                 # mask land fill
            series.append(compute_index(da.mean("member"), spec))  # ens-mean -> index (year,)
        except Exception as ex:
            print(f"  [skip {prod}] {type(ex).__name__}", flush=True)
    if not series:
        return None
    mme = xr.concat(series, dim="m").mean("m")
    return mme - mme.mean("year")                          # anomaly


def obs_index(spec, months):
    """Observed target-season (CONCURRENT) SST index anomaly per year from cached ERSST."""
    sst = T.load_sst()
    an = T.monthly_anom(sst)
    seas = africas2s.seasonal_reduce(an, months, how="mean")
    return compute_index(seas, spec)  # (year, lat, lon) -> (year,)


def obs_index_lead(spec, months):
    """Observed PRE-SEASON (lead) SST index anomaly per year — the 3 months before the season.
    This is the realistic lead predictor (SST known in advance), unlike the concurrent obs_index."""
    sst = T.load_sst()
    an = T.monthly_anom(sst)
    start = min(months)
    lead = [((start - 1 - k - 1) % 12) + 1 for k in range(3)]
    sub = an.sel(time=an["time.month"].isin(lead))
    yr = sub["time.year"] + xr.where(sub["time.month"] >= start, 1, 0)
    field = sub.groupby(yr.rename("year")).mean("time")
    return compute_index(field, spec)


def chirps_zone_mean(months, band):
    p = xr.open_dataset(DATA / CHIRPS_FILE)["precip"].sel(lat=slice(*band)).mean(["lat", "lon"])
    return africas2s.seasonal_reduce(p, months)


def loyo_reg_corr(pred, rain):
    yrs = np.intersect1d(pred.dropna("year").year, rain.dropna("year").year)
    x = pred.sel(year=yrs).values.astype(float)
    y = rain.sel(year=yrs).values.astype(float)
    n = len(yrs)
    if n < 12:
        return np.nan
    out = np.full(n, np.nan)
    for i in range(n):
        tr = np.arange(n) != i
        if np.std(x[tr]) == 0:
            continue
        b1, b0 = np.polyfit(x[tr], y[tr], 1)
        out[i] = b0 + b1 * x[i]
    ok = np.isfinite(out)
    return float(np.corrcoef(out[ok], y[ok])[0, 1]) if ok.sum() >= 12 and np.std(out[ok]) else np.nan


def plain_corr(a, b):
    yrs = np.intersect1d(a.dropna("year").year, b.dropna("year").year)
    x, y = a.sel(year=yrs).values, b.sel(year=yrs).values
    return float(np.corrcoef(x, y)[0, 1])


def main():
    rows = []
    for label, season, init_m, band, months, iname, box, mme_r in TARGETS:
        rain = chirps_zone_mean(months, band)
        oidx = obs_index(box, months)
        fidx = model_forecast_index(season, init_m, box)
        if fidx is None:
            continue
        sst_fcst_skill = plain_corr(fidx, oidx)          # how well MME forecasts the index (concurrent)
        ceiling = loyo_reg_corr(oidx, rain)              # concurrent obs index -> rain (perfect-SST ref)
        lead = loyo_reg_corr(obs_index_lead(box, months), rain)  # PRE-SEASON obs index -> rain (lead predictability)
        hybrid = loyo_reg_corr(fidx, rain)               # forecast index -> rain
        rows.append(dict(target=label, index=iname,
                         sst_fcst_skill=round(sst_fcst_skill, 3),
                         lead_predictability=round(lead, 3),
                         ceiling_concurrent=round(ceiling, 3),
                         hybrid=round(hybrid, 3),
                         pure_mme_r=mme_r))
        print(f"  {label:13s} idx={iname:8s} corr(fcstSST,obsSST)={sst_fcst_skill:+.2f}  "
              f"LEAD={lead:+.2f}  concurrent-ref={ceiling:+.2f}  HYBRID={hybrid:+.2f}", flush=True)

    with open(TAB / suffix("hybrid_forecast","csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    md = ["# Hybrid statistical–dynamical forecast vs. a perfect-SST reference\n",
          "Deterministic LOYO correlation of predicted vs. observed zone-mean seasonal rainfall. "
          "**Important:** the reference column is a *perfect-SST-forecast* reference — the "
          "*concurrent* target-season SST index vs. rainfall (i.e. skill if the season's SST were "
          "known exactly). It is **not** the lead-time predictability, and for within-season-coupled "
          "indices like the IOD it is partly diagnostic (near-tautological). The **lead** "
          "predictability (pre-season SST known in advance) is the lower feature-search value "
          "(e.g. OND IOD ≈ 0.5, not the ≈0.85 shown here). n≈24 — read structure, not decimals.\n",
          "| Target | Index | corr(forecast SST, obs SST) | **Lead predictability** (pre-season SST→rain) | Perfect-SST ref (concurrent) | **HYBRID** (forecast SST→rain) | Pure MME |",
          "|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['target']} | {r['index']} | {r['sst_fcst_skill']:+.2f} | "
                  f"**{r['lead_predictability']:+.2f}** | {r['ceiling_concurrent']:+.2f} "
                  f"| **{r['hybrid']:+.2f}** | {r['pure_mme_r']:+.2f} |")
    (TAB / suffix("hybrid_vs_mme","md")).write_text("\n".join(md) + "\n")

    # figure: r for reference / hybrid / pure MME per target
    labels = [r["target"] for r in rows]
    x = np.arange(len(rows)); w = 0.26
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(x - w, [r["ceiling_concurrent"] for r in rows], w, color="#555555", edgecolor="black",
           label="perfect-SST ref (CONCURRENT SST→rain; not lead predictability)")
    ax.bar(x,     [r["hybrid"] for r in rows],             w, color="#F28E2B", edgecolor="black", label="HYBRID (forecast SST→rain)")
    ax.bar(x + w, [r["pure_mme_r"] for r in rows],         w, color="#59A14F", edgecolor="black", label="pure MME (dynamical)")
    ax.axhline(0, color="k", lw=0.7)
    for i, r in enumerate(rows):
        ax.text(i, max(r["ceiling_concurrent"], r["hybrid"]) + 0.02,
                f"SST fcst r={r['sst_fcst_skill']:+.2f}", ha="center", fontsize=7, color="#333")
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_ylabel("LOYO correlation (predicted vs observed rainfall)")
    ax.set_title("Hybrid: feeding the model's SST forecast into the obs-trained link (this configuration)\n"
                 "dark bar = PERFECT-SST reference (concurrent, an upper bound / partly diagnostic for IOD),\n"
                 "not the lead predictability. n≈24 — rainfall bars near 0 are within sampling noise.")
    ax.legend(fontsize=7.5)
    fig.tight_layout(); fig.savefig(FIG / suffix("hybrid_forecast","png"), dpi=150); plt.close(fig)
    print("\nwrote", TAB / suffix("hybrid_vs_mme","md"), "and", FIG / suffix("hybrid_forecast","png"))


if __name__ == "__main__":
    main()
