# AGU Autoscience v1 — selecting a seasonal-forecast configuration by optimization over a design space

Given only a region's observed rainfall and a set of dynamical hindcasts, and no prior choice of
predictor, ocean domain, calibration, transform, EOF truncation, or lead, which operational forecast
configuration performs best? v1 states forecast design as an explicit parameter tensor and selects,
for each region's discovered rainy seasons, the configuration with the highest cross-validated
skill. Demonstrated on **Kenya and Somalia**.

## Pipeline

1. **Targets are derived** from each region's CHIRPS annual cycle (`targets.py`) — Kenya → MAM, OND;
   Somalia → MAM, SON.
2. **The search space is a tensor** (`searchspace.py`):
   `target × predictor_source × predictor_domain × transform × method × EOF-modes × lead` — 640
   configurations for the two regions.
3. **Every configuration is scored identically** under leave-one-year-out CV over a common
   1993–2016 period (n = 24), on GROC, RPSS, Pearson, and tercile hit-rate (`methods.py`, `driver.py`).
4. **Metric selection** (`metric_select.py`): pick the hindcast metric whose ranking best predicts
   realized accuracy.
5. **Outputs**: the best operational recipe per target (`recipes.py`), skill-vs-lead
   (`lead_cof.py`), the skill matrix (`report_figures.py`), and the `SHOWCASE.pdf` report.

## Predictor sources

| source | X (predictor) | role |
|---|---|---|
| `obs_sst_field` | observed pre-season SST field | perfect-prognosis reference |
| `gcm_mos_sst` | NMME forecast SST field | dynamical SST predictor |
| `gcm_mos_precip` | NMME forecast precipitation over the region | operational MOS |
| `persistence` | antecedent zone rainfall | baseline |

## Modules

| module | role |
|---|---|
| `searchspace.py` | the design tensor: axes, `Config`, enumeration |
| `targets.py` | seasonality → rainy-season targets (multi-region) |
| `predictors.py` | build each predictor source at a given lead/domain |
| `methods.py` | run a config under LOYO, score all four metrics |
| `driver.py` | enumerate → score → tidy results table |
| `metric_select.py` | choose the accuracy-predictive skill metric |
| `recipes.py` | best operational configuration per region/season |
| `lead_cof.py` | skill/accuracy vs lead for the selected configuration |
| `report_figures.py`, `render_showcase.py` | figures + the showcase PDF |

## Data

Rainfall: CHIRPS v3 monthly (`data/`, and the shared cache). Predictors: NOAA ERSSTv5 and the NMME
seasonal hindcasts, fetched through `rosetta`. Common analysis period 1993–2016 (n = 24). Skill is
cross-validated but configuration-specific and, at this sample size, noise-limited — see the
caveats in `SHOWCASE.md`.

## Next axes to promote

Downscaling resolution (currently native), the engineered operational indices (IWHG, West-Pacific
gradient) as predictor sources, a principal-component-regression calibration, and additional model
members. Somalia's short-rains domain resolves as SON here; a southern-Somalia domain would likely
recover the operational OND window.
