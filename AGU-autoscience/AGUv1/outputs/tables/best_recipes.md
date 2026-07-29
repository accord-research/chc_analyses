# Discovered best operational forecast configuration, per region/season (AGUv1)

For each auto-detected rainy season, the highest-pearson_r **realizable** (GCM-based) configuration found by the search, with its skill on all four metrics. `obs-SST reference` is the best perfect-prognosis observed-SST score for the same target — a diagnostic reference, not an achievable forecast.

| region/season | best operational recipe | GROC | RPSS | Pearson | hit-rate | obs-SST ref |
|---|---|---:|---:|---:|---:|---:|
| Kenya:MAM | NMME precip-MOS, QM, std_anom, lead 0 | 0.64 | 0.075 | 0.358 | 0.356 | 0.17 |
| Kenya:OND | NMME forecast index, IOD index, lead 0 | 0.743 | 0.258 | 0.66 | 0.541 | 0.483 |
| Somalia:MAM | NMME precip-MOS, QM, std_anom, lead 3 | 0.58 | 0.004 | 0.324 | 0.347 | 0.14 |
| Somalia:SON | NMME precip-MOS, CCA, 8 EOF modes, raw, lead 0 | 0.679 | 0.131 | 0.641 | 0.472 | 0.474 |

The recipe differs by season and region: the search selects predictor source, SST domain, calibration, EOF truncation, transform, and lead independently for each target, which is the point — the best operational approach is not one fixed method but a per-target choice. Skill is cross-validated but configuration-specific and, at n≈24, noise-limited (see caveats).
