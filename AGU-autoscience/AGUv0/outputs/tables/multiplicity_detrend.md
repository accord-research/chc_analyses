# Trend-robust multiplicity — permutation FDR on detrended residuals (audit S-F3)

Both predictor and rainfall are linearly detrended vs year before the leave-one-out statistic and the 5000-shuffle permutation, so the null is exchangeable and the q is the **trend-robust** one. Compared against the raw-series q from `multiplicity_fdr.csv`.

| Country | cells | survive q<0.05 (detrended) | survive q<0.10 (detrended) | flagship OND·IOD: r_dt, q_dt (q_raw) |
|---|---|---|---|---|
| Nigeria | 144 | 0 | 0 | — |
| Ethiopia | 208 | 14 | 15 | South: r=+0.55, q=0.010 (raw 0.0166) |
| Kenya | 160 | 33 | 42 | National: r=+0.53, q=0.004 (raw 0.0064) |

**Reading.** The East-African OND·IOD flagship survives detrending — the headline signal is interannual, not a shared-warming artifact — while trend-riding cells (e.g. the MAM ENSO 'signals' that `detrend_check.md` already flagged) drop out. Reporting the detrended q as the headline removes the anti-conservative-null concern for the flagship.
