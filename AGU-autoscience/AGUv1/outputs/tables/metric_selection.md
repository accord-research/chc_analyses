# Metric selection — which hindcast metric best predicts realized accuracy (AGUv1)

Realized accuracy = `hit_rate` (tercile categorical accuracy). For each candidate ranking metric: **rank agreement** = mean within-target Spearman vs accuracy; **selection value** = the accuracy actually realized by picking that metric's top config (mean over targets).

| ranking metric | rank agreement vs accuracy | realized hit-rate of its argmax |
|---|---:|---:|
| `generalized_roc` | 0.936 | 0.419 |
| `rpss` | 0.784 | 0.421 |
| `pearson_r` | 0.883 | 0.429 |

**Recommended selection metric for this region: `pearson_r`** — it best identifies configurations that are actually accurate out-of-sample here. Config selection in `lead_cof.py` uses this metric.
