"""
mme_search.py — search the PREDICTOR-DOMAIN axis of a real dynamical MME forecast.

Upgrades mme_hindcast.py from "each model's own precip over the target zone" (MOS) to a proper
teleconnection CCA: the predictor is each GCM's *forecast SST field* over a chosen tropical
domain, linked by CCA to observed CHIRPS rainfall over the target zone (different grids). We
sweep the SST bounding region — global-tropical, Pacific, Atlantic, Indian, Gulf-of-Guinea —
plus a precip-MOS baseline, and score each config's multi-model LOYO skill. This answers
"which bounding region for tropical SST is best, and does an SST predictor close the gap to the
perfect-prognosis ceiling?"

Method here is CCA (the only seasonal-calibration method seasonal_mme supports); the CCA-vs-eReg
-vs-logit-vs-objective-average method search is the companion step (mme_methods.py).

Outputs
  outputs/tables/mme_domain_search.csv      skill per (target, predictor domain)
  outputs/tables/mme_domain_best.md          best domain per target vs ceiling
  outputs/figures/mme_domain_search.png      GROC heatmap target x domain

Run in accord-chc after fetch_data.py (NMME fetched live via Rosetta, cached).
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

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"
for d in (FIG, TAB):
    d.mkdir(parents=True, exist_ok=True)

import csv as _csv
sys.path.insert(0, str(Path(__file__).resolve().parent))
from areas import AREA, BBOX, BANDS, CHIRPS_FILE, LABEL, suffix

HIND = (1993, 2016)
MODELS = ["nmme/geoss2s", "nmme/cesm1", "nmme/ccsm4", "nmme/cansipsic4"]

# SST predictor domains (lon in any convention; rosetta R2 fix handles it). "precip_mos" is the
# baseline: the model's own precip over the target zone (no teleconnection).
DOMAINS = {
    "global_tropical": [-30, 30, 0, 360],
    "pacific":         [-30, 30, 120, 280],
    "atlantic":        [-30, 30, -70, 20],
    "indian":          [-25, 25, 30, 120],
    "gulf_guinea":     [-15, 15, -40, 15],
    "precip_mos":      None,
}

# (label, season, init_month, band_name, months) per area; ceiling looked up from leaderboard
_TARGETS = {
    "nigeria": [
        ("JAS Middle", "JAS", 5, "Middle", [7, 8, 9]),
        ("JAS Sahel", "JAS", 5, "North", [7, 8, 9]),
        ("OND National", "OND", 8, "National", [10, 11, 12]),
    ],
    "ethiopia": [
        ("JAS Kiremt (North)", "JAS", 5, "North", [7, 8, 9]),
        ("MAM South (long rains)", "MAM", 2, "South", [3, 4, 5]),
        ("OND South (short rains)", "OND", 8, "South", [10, 11, 12]),
    ],
    "kenya": [
        ("OND National (short rains)", "OND", 8, "National", [10, 11, 12]),
        ("MAM National (long rains)", "MAM", 2, "National", [3, 4, 5]),
        ("OND South (short rains)", "OND", 8, "South", [10, 11, 12]),
    ],
}[AREA]


def ceiling_for(season, band_name):
    """Perfect-prognosis ceiling = best obs-only CV corr for this (season, band) from
    feature_discovery's leaderboard (area-suffixed). Falls back to nan if unavailable."""
    path = TAB / suffix("features_leaderboard", "csv")
    if not path.exists():
        return float("nan")
    best = float("nan")
    with open(path) as f:
        for r in _csv.DictReader(f):
            if r["season"] == season and r["band"] == band_name and r["cv_corr"] not in ("", "None"):
                v = float(r["cv_corr"])
                best = v if (best != best or v > best) else best
    return round(best, 2)


# build runtime targets: (label, season, init, band_tuple, months, ceiling)
TARGETS = [(lbl, s, im, BANDS[bn], mo, ceiling_for(s, bn))
           for (lbl, s, im, bn, mo) in _TARGETS]


def fetch_sst(model, target, init_month, box):
    g = acmaddl.fetch(product=model, variable="sst", init=f"{HIND[1]}-{init_month:02d}",
                      target=target, region=box, hindcast=HIND, year_index=True,
                      verbose=False, progress=False)
    da = g[list(g.data_vars)[0]]
    return da.where(da < 100)  # mask 1e15 land fill -> NaN (values are degC)


def fetch_precip(model, target, init_month, region):
    g = acmaddl.fetch(product=model, variable="precip", init=f"{HIND[1]}-{init_month:02d}",
                      target=target, region=region, hindcast=HIND, year_index=True,
                      verbose=False, progress=False)
    return g[list(g.data_vars)[0]]


def chirps_zone(months, band, coarsen=10):
    ds = xr.open_dataset(DATA / CHIRPS_FILE)
    p = ds["precip"].sel(lat=slice(*band))
    seasonal = africas2s.seasonal_reduce(p, months).sel(year=slice(*HIND))
    return seasonal.coarsen(lat=coarsen, lon=coarsen, boundary="trim").mean()


def mme_skill(predictors, obs):
    last = int(obs.year.max())
    tracks = {"PRED": {name: (da, da.sel(year=[last])) for name, da in predictors.items()}}
    res = africas2s.seasonal_mme(tracks, obs, method="cca", cv="loyo",
                                 forecast_year=last, verbose=False)
    sc = res.skill_report.scores
    return dict(rpss=float(sc.get("rpss", np.nan)),
                groc=float(sc.get("generalized_roc", np.nan)),
                afc2=float(sc.get("2afc", np.nan)),
                pearson=float(sc.get("pearson_r", np.nan)))


def main():
    rows = []
    for label, season, init_m, band, months, ceiling in TARGETS:
        obs = chirps_zone(months, band)
        zone_region = [band[0], band[1], BBOX[2], BBOX[3]]
        for dname, box in DOMAINS.items():
            preds = {}
            for prod in MODELS:
                name = prod.split("/")[-1].upper()
                try:
                    if dname == "precip_mos":
                        preds[name] = fetch_precip(prod, season, init_m, zone_region)
                    else:
                        preds[name] = fetch_sst(prod, season, init_m, box)
                except Exception as e:
                    print(f"  [skip {name}/{dname}] {type(e).__name__}: {e}", flush=True)
            if not preds:
                continue
            try:
                sk = mme_skill(preds, obs)
            except Exception as e:
                print(f"  [mme fail {label}/{dname}] {type(e).__name__}: {e}", flush=True)
                continue
            rec = dict(target=label, domain=dname, n_models=len(preds), ceiling=ceiling, **sk)
            rows.append(rec)
            print(f"  {label:13s} {dname:16s} GROC={sk['groc']:.3f} RPSS={sk['rpss']:.3f} "
                  f"r={sk['pearson']:+.3f}  (ceiling {ceiling})", flush=True)

    with open(TAB / suffix("mme_domain_search","csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    # best domain per target
    md = ["# Best SST predictor domain per target (real MME, CCA, LOYO)\n",
          "| Target | Best domain | GROC | RPSS | r | Ceiling r | precip-MOS GROC |",
          "|---|---|---|---|---|---|---|"]
    targets = list(dict.fromkeys(r["target"] for r in rows))
    for t in targets:
        sub = [r for r in rows if r["target"] == t]
        best = max(sub, key=lambda r: r["groc"])
        mos = next((r["groc"] for r in sub if r["domain"] == "precip_mos"), float("nan"))
        md.append(f"| {t} | **{best['domain']}** | {best['groc']:.3f} | {best['rpss']:.3f} "
                  f"| {best['pearson']:+.3f} | {best['ceiling']} | {mos:.3f} |")
    (TAB / suffix("mme_domain_best","md")).write_text("\n".join(md) + "\n")

    # heatmap GROC (target x domain)
    doms = list(DOMAINS.keys())
    M = np.full((len(targets), len(doms)), np.nan)
    for i, t in enumerate(targets):
        for j, d in enumerate(doms):
            v = [r["groc"] for r in rows if r["target"] == t and r["domain"] == d]
            if v:
                M[i, j] = v[0]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    im = ax.imshow(M, cmap="RdBu_r", vmin=0.30, vmax=0.75, aspect="auto")
    ax.set_xticks(range(len(doms))); ax.set_xticklabels(doms, rotation=30, ha="right")
    ax.set_yticks(range(len(targets))); ax.set_yticklabels(targets)
    for i in range(len(targets)):
        for j in range(len(doms)):
            if np.isfinite(M[i, j]):
                ax.text(j, i, f"{M[i,j]:.2f}", ha="center", va="center", fontsize=8,
                        color="white" if abs(M[i, j] - 0.5) > 0.08 else "black")
    fig.colorbar(im, label="GROC (0.5 = no skill)")
    ax.set_title("Real MME skill by SST predictor domain (CCA, LOYO) — this configuration\n"
                 "Spread across domains is usually within the ~0.1 GROC noise floor; the best cell is\n"
                 "often NOT robust, and SST-CCA barely beats the precip-MOS baseline (see docs/14).")
    fig.tight_layout(); fig.savefig(FIG / suffix("mme_domain_search","png"), dpi=150); plt.close(fig)
    print("\nwrote", TAB / suffix("mme_domain_best","md"))


if __name__ == "__main__":
    main()
