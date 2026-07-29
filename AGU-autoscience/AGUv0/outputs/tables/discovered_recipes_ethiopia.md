# Discovered forecast recipes — Ethiopia (observation-only, LOYO CV)

Best cross-validated predictor for each zone's natural forecast window. Skill = leave-one-year-out correlation of predicted vs observed zone-mean seasonal rainfall (1991–2023). The predictor is *searched*, not assumed.

| Zone | Window | Purpose | Best predictor | Driver family | CV skill | Runner-up |
|---|---|---|---|---|---|---|
| Northern highlands (Kiremt) | JJAS | main rains (Kiremt) | **sst_projection** | Data-driven SST | 0.29 | tsa (0.15) |
| Northern highlands (Kiremt) | JAS | Kiremt core | **wvg3** | Pacific gradient (WVG) | 0.46 | wvg2 (0.45) |
| Central (Belg+Kiremt) | MAM | Belg / spring rains | **sst_projection** | Data-driven SST | 0.09 | iod_dmi (-0.01) |
| Central (Belg+Kiremt) | JJAS | main rains | **tna** | Tropical Atlantic | 0.07 | tsa (-0.00) |
| South (bimodal, GHA-type) | MAM | long rains | **sst_projection** | Data-driven SST | 0.05 | iod_dmi (-0.04) |
| South (bimodal, GHA-type) | OND | short rains | **combo_top2** | Multi-feature | 0.56 | iod_dmi (0.56) |
| National overview | JJAS | whole-country main rains | **tsa** | Tropical Atlantic | 0.10 | sst_projection (0.10) |
| National overview | OND | whole-country short rains | **iod_dmi** | Indian Ocean | 0.48 | sst_projection (0.47) |

**Reading:** the winning approach differs by season and subgeography — a data-driven SST pattern for the monsoon core, the Indian Ocean / multi-feature combinations for the short rains, the Atlantic for the Guinea-coast summer, and rainfall persistence for the late northern season. No single index (WVG included) is best everywhere; that is the point.

