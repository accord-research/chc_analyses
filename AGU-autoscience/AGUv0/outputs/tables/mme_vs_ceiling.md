# Real MME skill vs perfect-prognosis ceiling

MME = NMME multi-model, DeepScale `seasonal_mme` CCA, leave-one-year-out CV, over 1993–2016. Ceiling = best observation-only CV correlation from `feature_discovery.py`. RPSS/GROC/2AFC are the standard RCOF probabilistic metrics; pearson r is the deterministic skill directly comparable to the ceiling.

| Config | Models | MME RPSS | MME GROC | MME 2AFC | MME r | Ceiling r |
|---|---|---|---|---|---|---|
| JAS Sudano-Sahel (May init) | 4 | -0.055 | 0.494 | 0.487 | -0.029 | 0.23 |
| JAS Middle Belt (May init) | 4 | -0.042 | 0.499 | 0.488 | -0.027 | 0.36 |
| OND Sudano-Sahel (Aug init) | 4 | -0.11 | 0.45 | 0.447 | -0.156 | 0.29 |
| OND National (Aug init) | 4 | -0.07 | 0.473 | 0.46 | -0.116 | 0.24 |
