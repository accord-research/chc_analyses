# Multiplicity control — permutation FDR over the feature leaderboard

Permutation test (5000 shuffles) per (season, band, textbook index) cell, then Benjamini–Hochberg FDR across all cells per country. Only cells that survive are defensible as more than best-of-search noise.

| Country | cells | survive q<0.05 | survive q<0.10 | strongest survivors (q<0.10) |
|---|---|---|---|---|
| Nigeria | 144 | 0 | 0 | — |
| Ethiopia | 208 | 10 | 12 | OND South·iod_dmi (r=+0.56, q=0.017); OND South·nino34 (r=+0.55, q=0.017); OND South·wvg2 (r=+0.49, q=0.024); OND South·wvg3 (r=+0.47, q=0.024); SON South·nino34 (r=+0.46, q=0.017) |
| Kenya | 160 | 27 | 35 | OND North·iod_dmi (r=+0.57, q=0.006); OND National·iod_dmi (r=+0.54, q=0.006); OND Central·iod_dmi (r=+0.52, q=0.006); OND South·iod_dmi (r=+0.51, q=0.006); OND National·nino34 (r=+0.50, q=0.009) |
