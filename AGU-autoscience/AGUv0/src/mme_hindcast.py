"""
mme_hindcast.py — a REAL multi-model dynamical ensemble forecast, scored against the
perfect-prognosis predictability ceiling.

Everything before this file was observation-only (perfect prognosis): observed pre-season SST
-> observed rainfall. This runs an actual seasonal forecast: fetch each GCM's seasonal
precipitation *hindcast* (NMME, via Rosetta), calibrate + combine them with DeepScale's
PyCPT-style multi-model orchestrator (`seasonal_mme`, CCA, leave-one-year-out CV), and score
the cross-validated tercile forecast. The point is the comparison:

    real MME skill  vs.  perfect-prognosis ceiling (feature_discovery.py)

A dynamical model must forecast the ocean state first (with error), so real MME skill is
expected to sit *below* the empirical ceiling. This quantifies that gap per zone/season.

Outputs
  outputs/tables/mme_skill.csv          per-config MME skill (RPSS, GROC, 2AFC, pearson)
  outputs/tables/mme_vs_ceiling.md      MME vs perfect-prognosis comparison
  outputs/figures/mme_vs_ceiling.png    bar chart of the gap

Run in accord-chc after fetch_data.py (needs CHIRPS cache; NMME fetched live, cached by Rosetta).
"""
import warnings, csv, sys
from pathlib import Path
warnings.filterwarnings("ignore")

import numpy as np
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import rosetta
import deepscale

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"
for d in (FIG, TAB):
    d.mkdir(parents=True, exist_ok=True)

HIND = (1993, 2016)
NIGERIA = [4.0, 14.0, 2.5, 15.0]
MODELS = ["nmme/geoss2s", "nmme/cesm1", "nmme/ccsm4", "nmme/cansipsic4"]

# configs: (label, season trigram, init 'YYYY-MM' month, band (lat_s,lat_n), months,
#           perfect-prognosis ceiling from feature_discovery best CV corr)
CONFIGS = [
    ("JAS Sudano-Sahel (May init)", "JAS", 5, (11, 14), [7, 8, 9], 0.23),
    ("JAS Middle Belt (May init)",  "JAS", 5, (8, 11),  [7, 8, 9], 0.36),
    ("OND Sudano-Sahel (Aug init)", "OND", 8, (11, 14), [10, 11, 12], 0.29),
    ("OND National (Aug init)",     "OND", 8, (4, 14),  [10, 11, 12], 0.24),
]


def fetch_gcm(product, target, init_month, region):
    init = f"{HIND[1]}-{init_month:02d}"
    g = rosetta.fetch(product=product, variable="precip", init=init, target=target,
                      region=region, hindcast=HIND, year_index=True,
                      verbose=False, progress=False)
    da = g[list(g.data_vars)[0]]
    return da  # (year, member, lat, lon)


def chirps_seasonal(months, grid):
    p = xr.open_dataset(DATA / "nigeria_chirps_monthly.nc")["precip"]
    seasonal = deepscale.seasonal_reduce(p, months).sel(year=slice(*HIND))
    return seasonal.interp(lat=grid.lat, lon=grid.lon)


def run_config(label, target, init_month, band, months, ceiling):
    region = [band[0], band[1], NIGERIA[2], NIGERIA[3]]
    models = {}
    for prod in MODELS:
        try:
            da = fetch_gcm(prod, target, init_month, region)
            models[prod.split("/")[-1].upper()] = da
        except Exception as e:
            print(f"  [skip {prod}] {type(e).__name__}: {e}", flush=True)
    if not models:
        return None
    grid = next(iter(models.values()))
    obs = chirps_seasonal(months, grid)
    last = int(obs.year.max())
    tracks = {"PRCP": {name: (da, da.sel(year=[last])) for name, da in models.items()}}
    try:
        res = deepscale.seasonal_mme(tracks, obs, method="cca", cv="loyo",
                                     forecast_year=last, verbose=False)
    except Exception as e:
        print(f"  [mme failed] {type(e).__name__}: {e}", flush=True)
        return None
    sc = res.skill_report.scores
    rec = dict(config=label, n_models=len(models),
               models="+".join(models.keys()),
               rpss=round(float(sc.get("rpss", np.nan)), 3),
               groc=round(float(sc.get("generalized_roc", np.nan)), 3),
               afc2=round(float(sc.get("2afc", np.nan)), 3),
               pearson=round(float(sc.get("pearson_r", np.nan)), 3),
               ceiling_corr=ceiling)
    print(f"  {label}: models={rec['models']}  RPSS={rec['rpss']} GROC={rec['groc']} "
          f"2AFC={rec['afc2']} r={rec['pearson']}  (ceiling r={ceiling})", flush=True)
    return rec


def main():
    rows = []
    for cfg in CONFIGS:
        print(f"[mme] {cfg[0]} ...", flush=True)
        r = run_config(*cfg)
        if r:
            rows.append(r)
    if not rows:
        print("no configs succeeded"); return

    with open(TAB / "mme_skill.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    md = ["# Real MME skill vs perfect-prognosis ceiling\n",
          "MME = NMME multi-model, DeepScale `seasonal_mme` CCA, leave-one-year-out CV, "
          "over 1993–2016. Ceiling = best observation-only CV correlation from "
          "`feature_discovery.py`. RPSS/GROC/2AFC are the standard RCOF probabilistic metrics; "
          "pearson r is the deterministic skill directly comparable to the ceiling.\n",
          "| Config | Models | MME RPSS | MME GROC | MME 2AFC | MME r | Ceiling r |",
          "|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['config']} | {r['n_models']} | {r['rpss']} | {r['groc']} | "
                  f"{r['afc2']} | {r['pearson']} | {r['ceiling_corr']} |")
    (TAB / "mme_vs_ceiling.md").write_text("\n".join(md) + "\n")

    # figure: GROC (skill>0.5) and deterministic r vs ceiling
    labels = [r["config"] for r in rows]
    x = np.arange(len(rows))
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].bar(x, [r["groc"] for r in rows], color="#4E79A7", edgecolor="black")
    axes[0].axhline(0.5, color="red", ls="--", lw=1, label="no-skill (GROC=0.5)")
    axes[0].set_title("Real MME probabilistic skill (GROC)"); axes[0].legend(fontsize=8)
    axes[0].set_ylabel("Generalized ROC")
    axes[1].bar(x - 0.2, [r["pearson"] for r in rows], width=0.4, color="#59A14F",
                edgecolor="black", label="real MME (dynamical)")
    axes[1].bar(x + 0.2, [r["ceiling_corr"] for r in rows], width=0.4, color="#111111",
                edgecolor="black", label="perfect-prognosis ceiling")
    axes[1].axhline(0, color="k", lw=0.6)
    axes[1].set_title("Deterministic skill: real MME vs ceiling"); axes[1].legend(fontsize=8)
    axes[1].set_ylabel("correlation")
    for ax in axes:
        ax.set_xticks(x); ax.set_xticklabels([l.replace(" (", "\n(") for l in labels],
                                             rotation=0, fontsize=7)
    fig.suptitle("Real multi-model dynamical forecast vs empirical predictability ceiling — Nigeria",
                 fontweight="bold")
    fig.tight_layout(); fig.savefig(FIG / "mme_vs_ceiling.png", dpi=150); plt.close(fig)
    print("\nwrote", TAB / "mme_vs_ceiling.md", "and", FIG / "mme_vs_ceiling.png")


if __name__ == "__main__":
    main()
