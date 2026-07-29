# Unified permutation-FDR incl. adaptive predictors (audit S-F1)

Benjamini–Hochberg over ONE family per country: the 8 textbook indices (published p-values) **plus** the adaptive predictors `persistence`, `sst_projection`, `combo_top2` (5000-shuffle permutation, with in-fold pattern/selection refit so the null carries the same optimism). Compares the adaptive winners against FDR — the test the base family never ran.

| Country | family m | survivors q<0.10 | adaptive-predictor result |
|---|---|---|---|
| Nigeria | 198 | 0 | best sst_projection r=+0.46 (JJAS Middle): does NOT survive; 0 adaptive cells survive |
| Ethiopia | 286 | 14 | best sst_projection r=+0.53 (OND South): q=0.025; 2 adaptive cells survive |
| Kenya | 220 | 48 | best sst_projection r=+0.46 (OND North): q=0.024; 13 adaptive cells survive |

**Reading.** With the adaptive predictors in the family, the claim can be stated honestly for the first time: whether the data-driven `sst_projection` — the *actual* best West-African predictor — survives FDR, not just the weaker textbook indices that were the only ones ever tested. See the per-country result above; the East-African OND signal remains the dominant survivor either way.
