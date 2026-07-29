# Discovered forecast recipes — Nigeria (observation-only, LOYO CV)

Best cross-validated predictor for each zone's natural forecast window. Skill = leave-one-year-out correlation of predicted vs observed zone-mean seasonal rainfall (1991–2023). The predictor is *searched*, not assumed.

| Zone | Window | Purpose | Best predictor | Driver family | CV skill | Runner-up |
|---|---|---|---|---|---|---|
| Guinea coast (South, bimodal) | AMJ | first rains (long-rains onset) | **nino34** | ENSO / Pacific | 0.20 | sst_projection (0.19) |
| Guinea coast (South, bimodal) | OND | second rains | **iod_dmi** | Indian Ocean | 0.10 | combo_top2 (0.03) |
| Middle Belt (transitional) | JJAS | full monsoon | **sst_projection** | Data-driven SST | 0.46 | atl3 (0.37) |
| Sudano-Sahel (North, unimodal) | JAS | monsoon core (PRESASS window) | **sst_projection** | Data-driven SST | 0.23 | wvg2 (0.21) |
| Sudano-Sahel (North, unimodal) | OND | short rains / late season | **combo_top2** | Multi-feature | 0.29 | persistence (0.18) |
| National overview | JJAS | whole-country monsoon | **sst_projection** | Data-driven SST | 0.37 | atl3 (0.32) |
| National overview | OND | whole-country short rains | **combo_top2** | Multi-feature | 0.24 | persistence (0.17) |

**Reading:** the winning approach differs by season and subgeography — a data-driven SST pattern for the monsoon core, the Indian Ocean / multi-feature combinations for the short rains, the Atlantic for the Guinea-coast summer, and rainfall persistence for the late northern season. No single index (WVG included) is best everywhere; that is the point.

