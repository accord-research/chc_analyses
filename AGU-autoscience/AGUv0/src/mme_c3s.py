"""
mme_c3s.py — does adding the C3S models (ECMWF SEAS5, ...) to the NMME ensemble help?

Re-runs the precip MME (CCA over the model's precip, seasonal_mme, LOYO) for the best target
configs with an expanded model set: the 4 NMME models plus C3S seasonal models fetched via CDS.
Compares NMME-only vs NMME+C3S skill. C3S fetches go through the CDS queue (~tens of seconds of
latency each), so this is deliberately scoped to a few models and the three headline targets.

Outputs
  outputs/tables/mme_c3s.csv        NMME-only vs NMME+C3S skill per target
  outputs/tables/mme_c3s.md

Run in accord-chc (needs ~/.cdsapirc with accepted C3S licenses).
"""
import warnings, csv, sys
from pathlib import Path

warnings.filterwarnings("ignore")
import numpy as np
import xarray as xr
import acmaddl
import africas2s

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TAB = ROOT / "outputs" / "tables"
TAB.mkdir(parents=True, exist_ok=True)

HIND = (1993, 2016)
NMME = ["nmme/geoss2s", "nmme/cesm1", "nmme/ccsm4", "nmme/cansipsic4"]
C3S = ["c3s/ecmwf", "c3s/meteofrance"]           # SEAS5 + Météo-France (add ukmo/dwd/cmcc if desired)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from areas import AREA, BBOX, BANDS, CHIRPS_FILE, LABEL, suffix

_TARGETS = {
    "nigeria": [
        ("JAS Sahel", "JAS", 5, "North", [7, 8, 9]),
        ("JAS Middle", "JAS", 5, "Middle", [7, 8, 9]),
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
TARGETS = [(lbl, s, im, BANDS[bn], mo) for (lbl, s, im, bn, mo) in _TARGETS]


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


def mme_groc(models, obs):
    last = int(obs.year.max())
    yrs = set(obs.year.values.tolist())
    tracks = {"PRCP": {}}
    for name, da in models.items():
        # align to obs years; keep only models covering the period
        common = sorted(yrs & set(da.year.values.tolist()))
        if len(common) < 20:
            continue
        d = da.sel(year=common)
        tracks["PRCP"][name] = (d, d.sel(year=[max(common)]))
    if not tracks["PRCP"]:
        return None, 0
    res = africas2s.seasonal_mme(tracks, obs, method="cca", cv="loyo",
                                 forecast_year=last, verbose=False)
    sc = res.skill_report.scores
    return dict(groc=float(sc.get("generalized_roc", np.nan)),
                rpss=float(sc.get("rpss", np.nan)),
                pearson=float(sc.get("pearson_r", np.nan))), len(tracks["PRCP"])


def main():
    rows = []
    for label, season, init_m, band, months in TARGETS:
        obs = chirps_zone(months, band)
        region = [band[0], band[1], BBOX[2], BBOX[3]]
        nmme_models = {}
        for prod in NMME:
            try:
                nmme_models[prod.split("/")[-1].upper()] = fetch_precip(prod, season, init_m, region)
            except Exception as e:
                print(f"  [skip {prod}] {type(e).__name__}", flush=True)
        c3s_models = {}
        for prod in C3S:
            try:
                print(f"  fetching {prod} (CDS, slow) ...", flush=True)
                c3s_models[prod.split("/")[-1].upper()] = fetch_precip(prod, season, init_m, region)
            except Exception as e:
                print(f"  [skip {prod}] {type(e).__name__}: {str(e)[:80]}", flush=True)

        sk_nmme, n1 = mme_groc(nmme_models, obs)
        sk_all, n2 = mme_groc({**nmme_models, **c3s_models}, obs)
        rec = dict(target=label,
                   nmme_n=n1, nmme_groc=round(sk_nmme["groc"], 3) if sk_nmme else None,
                   nmme_r=round(sk_nmme["pearson"], 3) if sk_nmme else None,
                   all_n=n2, all_groc=round(sk_all["groc"], 3) if sk_all else None,
                   all_r=round(sk_all["pearson"], 3) if sk_all else None)
        rows.append(rec)
        print(f"  {label}: NMME({n1}) GROC={rec['nmme_groc']} -> NMME+C3S({n2}) GROC={rec['all_groc']}",
              flush=True)

    with open(TAB / suffix("mme_c3s","csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    md = ["# Does adding C3S models help? NMME vs NMME+C3S (precip CCA MME, LOYO)\n",
          "| Target | NMME models | NMME GROC | NMME r | +C3S models | NMME+C3S GROC | NMME+C3S r |",
          "|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['target']} | {r['nmme_n']} | {r['nmme_groc']} | {r['nmme_r']} | "
                  f"{r['all_n']} | {r['all_groc']} | {r['all_r']} |")
    (TAB / suffix("mme_c3s","md")).write_text("\n".join(md) + "\n")
    print("\nwrote", TAB / suffix("mme_c3s","md"))


if __name__ == "__main__":
    main()
