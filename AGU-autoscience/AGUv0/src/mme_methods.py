"""
mme_methods.py — search the METHOD axis across the full DeepScale registry.

Not limited to the ICPAC calibration trio (CCA/eReg/logit): this compares every method the
tools expose for mapping a coarse GCM precip forecast to CHIRPS rainfall — CCA, BCSD, quantile
mapping (QM/DQM), delta, rank-analog — plus a climatology baseline, head-to-head, by
leave-one-year-out CV skill (via `africas2s.optimize`, which runs the CV internally). CorrDiff
(diffusion ML) is omitted here (needs trained weights); it is the natural add-on.

For each (target zone/season) and method, we report the CV skill averaged across the NMME
models — the ranking that answers "which method extracts the most skill here?" This complements
the predictor-domain sweep (mme_search.py): domain = which ocean; method = how to calibrate.

Outputs
  outputs/tables/mme_method_search.csv    CV skill per (target, method, metric)
  outputs/tables/mme_method_best.md        best method per target
  outputs/figures/mme_method_search.png    skill heatmap target x method

Run in accord-chc after fetch_data.py (NMME precip fetched live via Rosetta, cached).
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

HIND = (1993, 2016)
MODELS = ["nmme/geoss2s", "nmme/cesm1", "nmme/ccsm4", "nmme/cansipsic4"]
METHODS = ["climatology", "cca", "bcsd", "qm", "dqm", "delta", "rank-analog"]

sys.path.insert(0, str(Path(__file__).resolve().parent))
from areas import AREA, BBOX, BANDS, CHIRPS_FILE, LABEL, suffix
import csv as _csv

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


def _ceiling_for(season, band_name):
    path = TAB / suffix("features_leaderboard", "csv")
    if not path.exists():
        return float("nan")
    best = float("nan")
    with open(path) as f:
        for r in _csv.DictReader(f):
            if r["season"] == season and r["band"] == band_name and r["cv_corr"] not in ("", "None"):
                v = float(r["cv_corr"]); best = v if (best != best or v > best) else best
    return round(best, 2)


TARGETS = [(lbl, s, im, BANDS[bn], mo, _ceiling_for(s, bn)) for (lbl, s, im, bn, mo) in _TARGETS]


def fetch_precip(model, target, init_month, region):
    g = acmaddl.fetch(product=model, variable="precip", init=f"{HIND[1]}-{init_month:02d}",
                      target=target, region=region, hindcast=HIND, year_index=True,
                      verbose=False, progress=False)
    return g[list(g.data_vars)[0]]


def chirps_zone(months, band, coarsen=5):
    ds = xr.open_dataset(DATA / CHIRPS_FILE)
    p = ds["precip"].sel(lat=slice(*band))
    seasonal = africas2s.seasonal_reduce(p, months).sel(year=slice(*HIND))
    return seasonal.coarsen(lat=coarsen, lon=coarsen, boundary="trim").mean()


def method_skill(gcm, obs, method, metric):
    """LOYO CV skill of one method on one model, via optimize (CV runs internally)."""
    r = africas2s.optimize(gcm, obs, methods=[method], primary_metric=metric,
                           verbose=False, progress=False)
    return float(r.score)


def main():
    rows = []
    for label, season, init_m, band, months, ceiling in TARGETS:
        obs = chirps_zone(months, band)
        region = [band[0], band[1], BBOX[2], BBOX[3]]
        gcms = {}
        for prod in MODELS:
            try:
                gcms[prod.split("/")[-1].upper()] = fetch_precip(prod, season, init_m, region)
            except Exception as e:
                print(f"  [skip {prod}] {type(e).__name__}", flush=True)
        for method in METHODS:
            for metric in ["generalized_roc", "rpss"]:
                scores = []
                for name, gcm in gcms.items():
                    try:
                        scores.append(method_skill(gcm, obs, method, metric))
                    except Exception as e:
                        print(f"    [fail {label}/{method}/{name}/{metric}] {type(e).__name__}: "
                              f"{str(e)[:60]}", flush=True)
                if scores:
                    rows.append(dict(target=label, method=method, metric=metric,
                                     mean=round(float(np.mean(scores)), 3),
                                     best=round(float(np.max(scores)), 3),
                                     n=len(scores), ceiling=ceiling))
            groc = next((r["mean"] for r in rows if r["target"] == label and r["method"] == method
                         and r["metric"] == "generalized_roc"), np.nan)
            print(f"  {label:13s} {method:12s} mean GROC={groc}", flush=True)

    with open(TAB / suffix("mme_method_search","csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    # best method per target (by mean GROC)
    md = ["# Best calibration/downscaling method per target (full DeepScale registry)\n",
          "CV skill (LOYO) averaged across NMME models, via `africas2s.optimize`. GROC>0.5 = skill.\n",
          "| Target | Best method | mean GROC | best-model GROC | mean RPSS | Ceiling r |",
          "|---|---|---|---|---|---|"]
    targets = list(dict.fromkeys(r["target"] for r in rows))
    for t in targets:
        gr = [r for r in rows if r["target"] == t and r["metric"] == "generalized_roc"]
        best = max(gr, key=lambda r: r["mean"])
        rp = next((r["mean"] for r in rows if r["target"] == t and r["method"] == best["method"]
                   and r["metric"] == "rpss"), np.nan)
        md.append(f"| {t} | **{best['method']}** | {best['mean']:.3f} | {best['best']:.3f} "
                  f"| {rp} | {best['ceiling']} |")
    (TAB / suffix("mme_method_best","md")).write_text("\n".join(md) + "\n")

    # heatmap GROC target x method
    M = np.full((len(targets), len(METHODS)), np.nan)
    for i, t in enumerate(targets):
        for j, m in enumerate(METHODS):
            v = [r["mean"] for r in rows if r["target"] == t and r["method"] == m
                 and r["metric"] == "generalized_roc"]
            if v:
                M[i, j] = v[0]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    im = ax.imshow(M, cmap="RdBu_r", vmin=0.30, vmax=0.75, aspect="auto")
    ax.set_xticks(range(len(METHODS))); ax.set_xticklabels(METHODS, rotation=30, ha="right")
    ax.set_yticks(range(len(targets))); ax.set_yticklabels(targets)
    for i in range(len(targets)):
        for j in range(len(METHODS)):
            if np.isfinite(M[i, j]):
                ax.text(j, i, f"{M[i,j]:.2f}", ha="center", va="center", fontsize=8,
                        color="white" if abs(M[i, j] - 0.5) > 0.08 else "black")
    fig.colorbar(im, label="mean CV GROC across models (0.5 = no skill)")
    ax.set_title("Method skill by calibration/downscaling method (precip MOS, LOYO) — this config\n"
                 "GROC spread is within the ~0.1 noise floor; RPSS stays NEGATIVE (worse than\n"
                 "climatology) for these cells — GROC alone is not usable skill (see docs/14).")
    fig.tight_layout(); fig.savefig(FIG / suffix("mme_method_search","png"), dpi=150); plt.close(fig)
    print("\nwrote", TAB / suffix("mme_method_best","md"), "and", FIG / suffix("mme_method_search","png"))


if __name__ == "__main__":
    main()
