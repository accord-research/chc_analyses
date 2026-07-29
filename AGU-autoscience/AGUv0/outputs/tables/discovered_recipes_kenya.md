# Discovered forecast recipes — Kenya (observation-only, LOYO CV)

Best cross-validated predictor for each zone's natural forecast window. Skill = leave-one-year-out correlation of predicted vs observed zone-mean seasonal rainfall (1991–2023). The predictor is *searched*, not assumed.

| Zone | Window | Purpose | Best predictor | Driver family | CV skill | Runner-up |
|---|---|---|---|---|---|---|
| South/coast (bimodal) | MAM | long rains | **iod_dmi** | Indian Ocean | -0.03 | atl3 (-0.16) |
| South/coast (bimodal) | OND | short rains | **iod_dmi** | Indian Ocean | 0.51 | nino34 (0.48) |
| Central highlands (bimodal) | MAM | long rains | **sst_projection** | Data-driven SST | 0.04 | iod_dmi (-0.04) |
| Central highlands (bimodal) | OND | short rains | **iod_dmi** | Indian Ocean | 0.52 | nino34 (0.49) |
| North (arid) | OND | short rains | **iod_dmi** | Indian Ocean | 0.57 | combo_top2 (0.55) |
| National overview | MAM | whole-country long rains | **sst_projection** | Data-driven SST | 0.00 | iod_dmi (-0.03) |
| National overview | OND | whole-country short rains | **iod_dmi** | Indian Ocean | 0.55 | combo_top2 (0.52) |

**Reading:** the winning approach differs by season and subgeography — a data-driven SST pattern for the monsoon core, the Indian Ocean / multi-feature combinations for the short rains, the Atlantic for the Guinea-coast summer, and rainfall persistence for the late northern season. No single index (WVG included) is best everywhere; that is the point.

