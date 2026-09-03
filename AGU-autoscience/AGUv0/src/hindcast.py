"""
hindcast.py — config-driven hindcast-skill harness (the autoscience evaluator).

Given an experiment key from config.yml, this builds ONE forecast/downscale configuration,
runs it through Rosetta (data) + DeepScale (calibrate/downscale/ensemble), scores it under
leave-one-year-out cross-validation with DeepScale's skill suite, and returns a skill record.
An automated search layer (grid / greedy / agent) calls run_config() repeatedly with
different dicts; this file is the function it optimizes over.

STATUS: scaffold. The data/normalize/score control flow is written against the real
Rosetta + DeepScale APIs and is designed to run per-config; the exhaustive sweep across the
matrix is the compute-bound step meant to be driven by the search layer. Blocks that require
a full multi-model download + PyCPT-style CCA are marked TODO and raise NotImplementedError
so a partial run fails loudly rather than silently faking a number.

Usage:
    python src/hindcast.py jas_sahel_may
    python src/hindcast.py --list
"""
import sys, json, warnings, datetime as dt
from pathlib import Path
warnings.filterwarnings("ignore")

import numpy as np
import xarray as xr
import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TAB = ROOT / "outputs" / "tables"
TAB.mkdir(parents=True, exist_ok=True)
CONFIG = yaml.safe_load((ROOT / "config.yml").read_text())


# --------------------------------------------------------------------------- helpers
def zone_extent(zone_name):
    if zone_name in (None, "national"):
        e = CONFIG["region"]["predictand_extent"]
    else:
        e = CONFIG["region"]["zones"][zone_name]
        nat = CONFIG["region"]["predictand_extent"]
        e = {"south": e["south"], "north": e["north"], "west": nat["west"], "east": nat["east"]}
    return [e["south"], e["north"], e["west"], e["east"]]


def load_config(key):
    exp = CONFIG["experiments"][key].copy()
    exp["_key"] = key
    return exp


# --------------------------------------------------------------------------- the evaluator
def run_config(exp, calibration="objective_avg", downscale_method=None,
               target_res=None, verbose=True):
    """Build -> run -> score one configuration. Returns a skill record dict."""
    import acmaddl

    key = exp.get("_key", "adhoc")
    season = exp["season"]
    region = zone_extent(exp.get("zone"))
    hind = tuple(CONFIG["hindcast_period"])
    init_month = exp.get("init_month")

    rec = {
        "config_key": key, "label": exp.get("label", key),
        "zone": exp.get("zone", "national"), "season": season["name"],
        "init_month": init_month, "calibration": calibration,
        "downscale_method": downscale_method, "target_res": target_res,
        "hindcast_period": list(hind), "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
    }

    # ---- 1. predictand (observations) — real fetch ----
    if verbose:
        print(f"[{key}] fetching CHIRPS predictand {region} {hind} ...", flush=True)
    obs = acmaddl.fetch(product=CONFIG["observations"], variable="precip",
                        region=region, hindcast=hind, verbose=False, progress=False)
    obs_season = _season_sum(obs["precip"], season["months"])   # (year, lat, lon)
    rec["n_years"] = int(obs_season.sizes.get("year", 0))

    # ---- 2. predictors + calibration ----
    # The real sweep fetches each GCM's seasonal hindcast+forecast and/or SST fields, puts
    # them on the obs grid, and calls the chosen DeepScale calibrator. That download is the
    # heavy step; wire in per calibration method:
    #
    #   cca         -> africas2s.pipelines.seasonal_mme(models, obs, cpt_args=...)
    #   ereg        -> africas2s.calibrate(model_hindcasts, obs, method="ereg", ...)
    #   logit       -> africas2s.calibrate(index_series, obs, method="logit", forecast=...)
    #   objective_avg -> equal-weight mean of {cca, ereg, logit} tercile probs (GHACOF recipe)
    #
    raise NotImplementedError(
        f"[{key}] calibration='{calibration}' needs the multi-model GCM download + PyCPT/"
        "DeepScale calibration wired in. The observation-only predictor screen "
        "(src/teleconnections.py) and the season discovery (src/seasons.py) run today; this "
        "GCM-calibration + skill step is the compute-bound stage for the search layer. "
        "See docs/04_experiment_design.md sec.3 (staged search).")

    # ---- 3. downscaling (axes K, L) ----  [reached once calibration is wired]
    # if downscale_method:
    #     fcst = africas2s.downscale(coarse_fcst, obs, method=downscale_method,
    #                                regrid_to=target_res)

    # ---- 4. score under LOYO ----
    # report = africas2s.skill(fcst, obs_season, metrics=CONFIG["skill"]["metrics"], cv="loyo")
    # rec["skill"] = _summarize(report)
    # return rec


def _season_sum(da, months):
    sel = da.sel(time=da["time.month"].isin(months))
    return sel.groupby("time.year").sum("time")


def _summarize(report):
    """Reduce a DeepScale SkillReport to zone-mean + fraction-above-floor scalars + map path."""
    floor_m = CONFIG["skill"]["skill_floor_metric"]
    floor_v = CONFIG["skill"]["skill_floor_value"]
    out = {}
    # report exposes per-metric fields (maps); reduce to scalars
    for m in CONFIG["skill"]["metrics"]:
        field = getattr(report, m, None)
        if field is not None:
            out[m + "_mean"] = float(np.nanmean(np.asarray(field)))
    fm = getattr(report, floor_m, None)
    if fm is not None:
        out["frac_above_floor"] = float((np.asarray(fm) > floor_v).mean())
    return out


def main(argv):
    if not argv or argv[0] == "--list":
        print("Available experiment keys:")
        for k, v in CONFIG["experiments"].items():
            print(f"  {k:22s} {v.get('label','')}")
        return
    key = argv[0]
    exp = load_config(key)
    try:
        rec = run_config(exp)
        out = TAB / f"skill_{key}.json"
        out.write_text(json.dumps(rec, indent=2))
        print(json.dumps(rec, indent=2))
        print("wrote", out)
    except NotImplementedError as e:
        print("SCAFFOLD:", e)


if __name__ == "__main__":
    main(sys.argv[1:])
