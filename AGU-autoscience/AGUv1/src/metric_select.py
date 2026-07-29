"""select.py — pick the hindcast skill metric most predictive of realized accuracy (AGUv1).

The WMO/operational question: of the skill scores we could rank configs by, *which one, over the
hindcast, best predicts realized tercile accuracy for this region?* We treat `hit_rate` (tercile
categorical accuracy) as the realized-accuracy target and ask, for each candidate ranking metric:

  1. rank agreement — Spearman correlation between the metric and hit_rate across configs;
  2. selection value — if you pick the argmax-metric config, what hit_rate do you actually realize?
     (averaged over targets; the honest "does ranking by this metric choose accurate forecasts?")

The metric that wins both is the recommended selection metric. Reads `outputs/tables/search_results.csv`.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

TAB = Path(__file__).resolve().parents[1] / "outputs" / "tables"
RANKING_METRICS = ["generalized_roc", "rpss", "pearson_r"]   # candidates to rank by
ACCURACY = "hit_rate"


def _spearman(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 4:
        return np.nan
    ar, br = pd.Series(a[ok]).rank().values, pd.Series(b[ok]).rank().values
    return float(np.corrcoef(ar, br)[0, 1])


def main():
    df = pd.read_csv(TAB / "search_results.csv")
    targets = sorted(df["target"].unique())

    rows = []
    for m in RANKING_METRICS:
        # rank agreement, pooled within-target (so it's temporal-config skill, not target scale)
        sps = [_spearman(g[m], g[ACCURACY]) for _, g in df.groupby("target") if g[m].notna().sum() >= 4]
        rank_agree = float(np.nanmean(sps)) if sps else np.nan
        # selection value: argmax-m config per target -> its realized hit_rate
        realized = []
        for t in targets:
            g = df[df["target"] == t].dropna(subset=[m, ACCURACY])
            if len(g):
                realized.append(g.loc[g[m].idxmax(), ACCURACY])
        rows.append(dict(metric=m, rank_agreement_vs_accuracy=round(rank_agree, 3),
                         realized_hit_rate_of_argmax=round(float(np.mean(realized)), 3) if realized else np.nan))

    sel = pd.DataFrame(rows)
    # recommend: highest realized accuracy of its argmax, tie-broken by rank agreement
    sel["_score"] = sel["realized_hit_rate_of_argmax"].fillna(-1) + 0.001 * sel["rank_agreement_vs_accuracy"].fillna(-1)
    best = sel.sort_values("_score", ascending=False).iloc[0]["metric"]

    md = ["# Metric selection — which hindcast metric best predicts realized accuracy (AGUv1)", "",
          f"Realized accuracy = `{ACCURACY}` (tercile categorical accuracy). For each candidate ranking "
          "metric: **rank agreement** = mean within-target Spearman vs accuracy; **selection value** = "
          "the accuracy actually realized by picking that metric's top config (mean over targets).", "",
          "| ranking metric | rank agreement vs accuracy | realized hit-rate of its argmax |",
          "|---|---:|---:|"]
    for _, r in sel.iterrows():
        md.append(f"| `{r['metric']}` | {r['rank_agreement_vs_accuracy']} | {r['realized_hit_rate_of_argmax']} |")
    md += ["", f"**Recommended selection metric for this region: `{best}`** — it best identifies "
           "configurations that are actually accurate out-of-sample here. Config selection in "
           "`lead_cof.py` uses this metric."]
    (TAB / "metric_selection.md").write_text("\n".join(md) + "\n")
    sel.drop(columns="_score").to_csv(TAB / "metric_selection.csv", index=False)
    print("\n".join(md))
    return best


if __name__ == "__main__":
    main()
