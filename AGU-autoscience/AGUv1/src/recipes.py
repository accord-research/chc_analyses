"""recipes.py — the discovered best operational forecast configuration per region/season (AGUv1).

The central output: given only a region's observed rainfall and the dynamical hindcasts, and no
prior choice of predictor, domain, transform, calibration, EOF truncation, or lead, the search
returns — for each discovered rainy season — the *realizable* (GCM-based) configuration with the
highest cross-validated skill under the selection metric. Reported alongside its skill on all
metrics and the perfect-prognosis obs-SST reference, so the selection is auditable.

Reads `outputs/tables/search_results.csv`; writes `outputs/tables/best_recipes.{md,csv}`.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from metric_select import main as select_metric

TAB = Path(__file__).resolve().parents[1] / "outputs" / "tables"
REALIZABLE = ("gcm_mos_precip", "gcm_mos_sst", "gcm_index")   # real forecasts; obs_* are diagnostic
METRICS = ["generalized_roc", "rpss", "pearson_r", "hit_rate"]
_SRC = {"gcm_mos_precip": "NMME precip-MOS", "gcm_mos_sst": "NMME SST-MOS",
        "gcm_index": "NMME forecast index"}


def _recipe(row) -> str:
    parts = [_SRC.get(row["predictor_source"], row["predictor_source"])]
    if row["predictor_source"] == "gcm_mos_sst":
        parts.append(f"{row['predictor_domain']} SST")
    if row["predictor_source"] == "gcm_index":
        parts.append(f"{str(row['predictor_domain']).upper()} index")
        parts.append(f"lead {int(row['lead'])}")
        return ", ".join(parts)
    parts.append(f"{row['method'].upper()}")
    if row["method"] == "cca":
        parts.append(f"{int(row['eof_modes'])} EOF modes")
    parts.append(f"{row['transform']}")
    parts.append(f"lead {int(row['lead'])}")
    return ", ".join(parts)


def main():
    metric = select_metric()
    df = pd.read_csv(TAB / "search_results.csv")

    rows = []
    for tname in sorted(df["target"].unique()):
        g = df[df["target"] == tname]
        real = g[g["predictor_source"].isin(REALIZABLE)].dropna(subset=[metric])
        if not len(real):
            continue
        best = real.loc[real[metric].idxmax()]
        ceil = g[g["predictor_source"] == "obs_sst_field"][metric].max()
        rows.append(dict(target=tname, recipe=_recipe(best),
                         **{m: round(float(best[m]), 3) for m in METRICS},
                         obs_sst_reference=round(float(ceil), 3) if np.isfinite(ceil) else np.nan,
                         **{f"cfg_{k}": best[k] for k in
                            ("predictor_source", "predictor_domain", "method", "transform", "eof_modes", "lead")}))

    out = pd.DataFrame(rows)
    md = ["# Discovered best operational forecast configuration, per region/season (AGUv1)", "",
          f"For each auto-detected rainy season, the highest-{metric} **realizable** (GCM-based) "
          "configuration found by the search, with its skill on all four metrics. `obs-SST "
          "reference` is the best perfect-prognosis observed-SST score for the same target — a "
          "diagnostic reference, not an achievable forecast.", "",
          "| region/season | best operational recipe | GROC | RPSS | Pearson | hit-rate | obs-SST ref |",
          "|---|---|---:|---:|---:|---:|---:|"]
    for r in rows:
        md.append(f"| {r['target']} | {r['recipe']} | {r['generalized_roc']} | {r['rpss']} | "
                  f"{r['pearson_r']} | {r['hit_rate']} | {r['obs_sst_reference']} |")
    md += ["", "The recipe differs by season and region: the search selects predictor source, SST "
           "domain, calibration, EOF truncation, transform, and lead independently for each target, "
           "which is the point — the best operational approach is not one fixed method but a "
           "per-target choice. Skill is cross-validated but configuration-specific and, at n≈24, "
           "noise-limited (see caveats)."]
    (TAB / "best_recipes.md").write_text("\n".join(md) + "\n")
    out.to_csv(TAB / "best_recipes.csv", index=False)
    print("\n".join(md))


if __name__ == "__main__":
    main()
