"""
lead_skill.py — how do skill AND accuracy change with forecast lead time, by region?

For a target season and zone, run the real NMME MME (CCA-MOS, LOYO) from a sequence of
initialization months, giving lead times of 1..6 months, and plot two DIFFERENT things:

  * SKILL vs lead   — skill SCORES relative to climatology: RPSS and generalized-ROC (GROC).
                      These answer "is the forecast better than climatology?"
  * ACCURACY vs lead — how OFTEN the forecast is right: the tercile HIT RATE (fraction of years
                      the most-likely predicted tercile matches the observed tercile) and 2AFC.
                      A forecast can be fairly accurate yet have little skill (climatology is also
                      accurate for a skewed predictand), so these are genuinely distinct.

Regions: the skillful East African OND short rains (Kenya national, Ethiopia south) plus a
West-African contrast (Nigeria JAS Middle Belt).

Outputs
  outputs/tables/lead_skill.csv
  outputs/figures/lead_skill_<region>.png   two panels: skill vs lead, accuracy vs lead
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
HIND = (1993, 2016)
MODELS = ["nmme/geoss2s", "nmme/cesm1", "nmme/ccsm4", "nmme/cansipsic4"]
SEASON_START = {"OND": 10, "JAS": 7, "MAM": 3}

# (region label, chirps file, season, band lat tuple, [init months -> leads 1..6])
CONFIGS = [
    ("Kenya OND (national)", "kenya_chirps_monthly.nc", "OND", (-5, 5), [9, 8, 7, 6, 5, 4]),
    ("Ethiopia OND (south)", "ethiopia_chirps_monthly.nc", "OND", (3, 7), [9, 8, 7, 6, 5, 4]),
    ("Nigeria JAS (Middle Belt)", "nigeria_chirps_monthly.nc", "JAS", (8, 11), [6, 5, 4, 3, 2, 1]),
]
BBOX_LON = {"kenya_chirps_monthly.nc": (34, 42), "ethiopia_chirps_monthly.nc": (33, 48),
            "nigeria_chirps_monthly.nc": (2.5, 15)}
SEASON_MONTHS = {"OND": [10, 11, 12], "JAS": [7, 8, 9], "MAM": [3, 4, 5]}


def lead_of(init_m, season):
    return (SEASON_START[season] - init_m) % 12


def chirps_zone(cf, months, band, coarsen=10):
    p = xr.open_dataset(DATA / cf)["precip"].sel(lat=slice(*band))
    seasonal = africas2s.seasonal_reduce(p, months).sel(year=slice(*HIND))
    return seasonal.coarsen(lat=coarsen, lon=coarsen, boundary="trim").mean()


def run_lead(cf, season, band, init_m):
    region = [band[0], band[1], *BBOX_LON[cf]]
    obs = chirps_zone(cf, SEASON_MONTHS[season], band)
    preds = {}
    for prod in MODELS:
        try:
            # degenerate_attempts>1: reject a zero-filled/truncated response and retry (the
            # robustness that used to live in the local safe_fetch wrapper, now in acmaddl.fetch).
            g = acmaddl.fetch(product=prod, variable="precip", init=f"{HIND[1]}-{init_m:02d}",
                              target=season, region=region, hindcast=HIND, year_index=True,
                              verbose=False, progress=False, max_retries=4, degenerate_attempts=6)
            preds[prod.split("/")[-1]] = g[list(g.data_vars)[0]]
        except Exception as e:
            print(f"      [drop {prod.split('/')[-1]}] {type(e).__name__}: {str(e)[:60]}", flush=True)
    if not preds:
        return None
    last = int(obs.year.max())
    tracks = {"PRCP": {k: (v, v.sel(year=[last])) for k, v in preds.items()}}
    # Uses deepscale's default "pooled" aggregation. (A degenerate-CCA-mode bug previously made the
    # pooled path emit a constant [0.5, 0, 0.5] tercile forecast — GROC exactly 0.500 — because one
    # model's blown-up leverage poisoned the MME-averaged leverage. Fixed in deepscale
    # methods/cca.py::_project_by_sv; pooled and cpt_per_model now agree to ~0.002.)
    res = africas2s.seasonal_mme(tracks, obs, method="cca", cv="loyo", forecast_year=last, verbose=False)
    sc = res.skill_report.scores
    # accuracy: hit rate from the CV tercile forecast, zone-averaged. Guard against years whose
    # tercile probabilities came back all-NaN (degenerate CV fold) — argmax over an all-NaN slice
    # raises and would otherwise kill the whole run.
    tc = res.tercile_cv.mean(["lat", "lon"])                 # (year, tercile)
    tc = tc.where(tc.notnull().all("tercile"), drop=True)
    if tc.year.size == 0:
        hit = float("nan")
    else:
        pred_terc = tc.argmax("tercile").values
        q = obs.mean(["lat", "lon"]) if {"lat", "lon"} <= set(obs.dims) else obs
        q33, q67 = q.quantile(1/3, "year"), q.quantile(2/3, "year")
        obs_terc = xr.where(q <= q33, 0, xr.where(q >= q67, 2, 1)).sel(year=tc.year).values
        hit = float((pred_terc == obs_terc).mean())
    return dict(rpss=float(sc.get("rpss", np.nan)), groc=float(sc.get("generalized_roc", np.nan)),
                pearson=float(sc.get("pearson_r", np.nan)), afc2=float(sc.get("2afc", np.nan)),
                hit_rate=hit)


def main():
    rows = []
    for label, cf, season, band, inits in CONFIGS:
        print(f"[lead] {label}", flush=True)
        recs = []
        for im in inits:
            lead = lead_of(im, season)
            try:
                r = run_lead(cf, season, band, im)
            except Exception as e:
                print(f"    init {im:02d} lead {lead}: SKIP ({type(e).__name__}: {str(e)[:60]})", flush=True)
                r = None
            if r:
                r.update(region=label, season=season, init_month=im, lead=lead)
                recs.append(r); rows.append(r)
                print(f"    init {im:02d} lead {lead}: GROC={r['groc']:.3f} RPSS={r['rpss']:.3f} "
                      f"hit={r['hit_rate']:.2f}", flush=True)
        if not recs:
            continue
        recs.sort(key=lambda r: r["lead"])
        L = [r["lead"] for r in recs]
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.6))
        a1.plot(L, [r["groc"] for r in recs], "-o", color="#4E79A7", label="GROC")
        a1.plot(L, [r["rpss"] for r in recs], "-s", color="#E15759", label="RPSS")
        a1.plot(L, [r["pearson"] for r in recs], "-^", color="#59A14F", label="corr (deterministic)")
        a1.axhline(0.5, color="#4E79A7", ls=":", lw=0.8); a1.axhline(0, color="k", lw=0.6)
        a1.set_title("SKILL vs lead (relative to climatology)"); a1.set_xlabel("lead time (months)")
        a1.set_ylabel("skill score"); a1.legend(fontsize=8); a1.invert_xaxis()
        a2.plot(L, [r["hit_rate"] for r in recs], "-o", color="#B07AA1", label="tercile hit rate")
        a2.plot(L, [r["afc2"] for r in recs], "-s", color="#9C755F", label="2AFC")
        a2.axhline(1/3, color="#B07AA1", ls=":", lw=0.8, label="random hit rate (1/3)")
        a2.axhline(0.5, color="#9C755F", ls=":", lw=0.8)
        a2.set_title("ACCURACY vs lead (how often it's right)"); a2.set_xlabel("lead time (months)")
        a2.set_ylabel("accuracy"); a2.legend(fontsize=8); a2.invert_xaxis()
        fig.suptitle(f"{label} — real NMME MME (CCA, LOYO): skill and accuracy vs forecast lead\n"
                     "(n≈24; skill = improvement over climatology, accuracy = fraction correct — different things)",
                     fontweight="bold")
        fig.tight_layout(rect=[0, 0, 1, 0.94])
        safe = label.split(" ")[0].lower()
        fig.savefig(FIG / f"lead_skill_{safe}.png", dpi=150); plt.close(fig)

    with open(TAB / "lead_skill.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["region", "season", "init_month", "lead", "rpss", "groc",
                                          "pearson", "afc2", "hit_rate"])
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(r[k], 3) if isinstance(r[k], float) else r[k]) for k in w.fieldnames})
    print("\nwrote lead_skill.csv + figures")


if __name__ == "__main__":
    main()
