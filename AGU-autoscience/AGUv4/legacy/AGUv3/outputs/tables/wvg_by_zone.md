# WVG dry-tail skill by discovered zone (AGUv3)

Pre-season WVG = z(Nino3.4) - z(WesternV) over the 2 months before each window. `sym_corr` = the symmetric all-years LOYO metric (hides the signal); `p_dry_negwvg` = P(below-median | strong-negative WVG); `p_dry_negwvg_lanina` adds the La-Nina condition. AGUv2 hand-box eHorn reference for MAM: (0.79, 0.77).

| zone | window | discovered | n | sym_corr | dry_roc | p_dry_clim | p_dry_negwvg | p_dry_negwvg_lanina | n_joint |
|---|---|---|---|---|---|---|---|---|---|
| 0 | JAS | True | 42 | 0.47 | 0.23 | 0.5 | 0.21 | 0.25 | 12 |
| 0 | MAM | False | 42 | -0.28 | 0.67 | 0.55 | 0.71 | 0.69 | 13 |
| 0 | OND | False | 42 | 0.05 | 0.52 | 0.6 | 0.64 | 0.78 | 9 |
| 1 | MAM | True | 42 | -0.62 | 0.62 | 0.52 | 0.71 | 0.69 | 13 |
| 1 | OND | True | 42 | 0.27 | 0.74 | 0.64 | 0.86 | 1.0 | 9 |
