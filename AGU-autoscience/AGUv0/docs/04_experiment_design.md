# Experiment design — the Nigeria autoscience matrix

This is the intellectual core of the directory: the definition of the *search space* of
forecast/downscale configurations, the *scoring* that makes any two points in that space
comparable, and the *search strategy* an agentic runner uses to explore it. Everything in
[`config.yml`](../config.yml) is an axis of this matrix.

The premise: a seasonal-forecast "configuration" is a point in a high-dimensional space of
choices that today are made by hand, per RCOF, per season, mostly by convention. Because
Rosetta + DeepScale expose every one of those choices as a parameter with a stable API, we
can (a) enumerate the space, (b) score each point identically under cross-validation, and
(c) let a search procedure — grid, greedy, or agent-driven — find the skill-maximizing (or
resolution-maximizing-subject-to-skill) configuration for each place, season, and lead.

---

## 1. The axes of the search space

| # | Axis | Values explored | Rosetta/DeepScale knob |
|---|------|-----------------|------------------------|
| A | **Target season** | Discovered partitions (see [`02_seasonal_partition.md`](02_seasonal_partition.md)); candidates: MAM, AMJ, JJA, **JAS**, JJAS, ASO, SON, OND | `target=`, `seasonal=` |
| B | **Init month / lead** | For each season, every init 0–5 months ahead (e.g. JAS from May/Apr/Mar/Feb inits → lead 1–5) | `init=`, `lead_low/high` |
| C | **Predictand region** | National; vs. subset by discovered homogeneous zone (Guinea coast / Middle Belt / Sudan-Sahel); vs. per-pixel | `region=` (bbox, shapefile, or zone geometry) |
| D | **Predictand transform** | none, Gamma, empirical-quantile; anomaly vs. total (`tailoring`) | `cpt_args.transform_predictand`, `tailoring` |
| E | **Predictor type** | **(i) gridded SST field** (CCA over an SST domain) vs. **(ii) featurized indices** (scalar teleconnection indices → logistic/regression) vs. **(iii) both, combined** | `deepscale.calibrate(method=…)`, `Index` |
| F | **Predictor domain** | SST-box size/location: global-tropical, Atlantic-only, Pacific-only, Indian-only, and the union; box sizing swept | `region=` on the SST fetch; `predictor_extent` |
| G | **Candidate feature pool (searched, not assumed)** | textbook indices (Niño3.4, ATL3, TNA, TSA, TNA−TSA gradient, IOD/DMI, WVG 2/3-box) **+ data-driven SST-projection patterns + non-SST covariates (rainfall persistence; roadmap: SST EOFs, soil moisture, circulation)** | `deepscale.Index.named/custom`, `src/feature_discovery.py` |
| H | **Model / MME** | Single GCM vs. multi-model; NMME (SPEAR, CCSM4, GEOS-S2S, CanSIPS, CFSv2) and C3S (ECMWF-SEAS5, Météo-France, DWD, CMCC, UKMO, …) | `models:` list, `deepscale.ensemble(strategy=…)` |
| I | **Calibration method** | CCA, ensemble regression (`ereg`), logistic index (`logit`), and their equal-weight objective average (the GHACOF recipe) | `deepscale.calibrate`, `seasonal_mme` |
| J | **MME strategy** | uniform, skill-weighted, drop-worst, BMA | `deepscale.ensemble(strategy=…)` |
| K | **Downscaling method** | BCSD, quantile mapping (QM/DQM), delta, CCA, **rank-analog**, CorrDiff (ML) | `deepscale.downscale(method=…)` |
| L | **Target resolution** | coarse native (~1°) → 0.25° → 0.1° → **0.05°** (CHIRPS grid) | `regrid_to=`, `grid_res=` |

A single evaluated configuration is a choice on every axis, e.g.:

```
season=JAS, init=May (lead 2), predictand=Sudan-Sahel zone, transform=Gamma/Anomaly,
predictor=indices{ATL3, TNA-TSA, Niño3.4}, calib=logit, MME=uniform(SPEAR,ECMWF,CFSv2),
downscale=rank-analog → 0.05°
```

## 2. Scoring — how any two configurations are compared

Every configuration is evaluated **identically** so the search is fair:

- **Cross-validation:** leave-one-year-out (LOYO) over the hindcast period (default
  1993–2016, extensible to 1981–2020 where data allow). No configuration ever sees its own
  verification year.
- **Metrics (DeepScale `skill()`):** RPSS (tercile), ROC area & GROC, Pearson & Spearman
  correlation of the deterministic anomaly, 2AFC, Heidke skill score, reliability slope,
  and spread–error ratio.
- **Reported as a map, not a scalar.** Skill varies strongly across Nigeria; the primary
  output of each config is a per-pixel skill field, summarized by (i) zone-averaged skill
  and (ii) fraction of the country exceeding a skill floor (e.g. GROC > 0.5).
- **Conditional skill.** Following the CHC Ethiopia finding that dry-tail skill can exceed
  overall skill, each config also reports skill conditioned on the below-normal tercile —
  the operationally decisive quantity for drought early warning.
- **Resolution/skill frontier.** For downscaling axes (K, L), the score is two-dimensional:
  *effective resolution added* vs. *skill retained*. A config that adds detail while merely
  holding skill constant is still valuable (sharper, decision-relevant maps); a config that
  claims resolution it cannot verify is penalized. See
  [`05_downscaling_plan.md`](05_downscaling_plan.md).

Selection objective (per season × zone × lead):

```
maximize   zone-averaged GROC (or RPSS)      # primary skill
subject to reliability slope ∈ [0.8, 1.2]    # not overconfident
then       maximize effective resolution      # tie-break toward sharper products
```

## 3. Search strategy (why this is "autoscience")

The matrix is combinatorially large (A×B×…×L ≈ 10^5–10^6 nominal points), but it is not
searched blindly. The stack makes three things cheap that are usually expensive, and that
is what enables automation:

1. **Uniform interface → uniform scoring.** Because `fetch()` and `calibrate()`/`downscale()`
   have stable signatures, a driver can construct, run, and score any config from a dict —
   no per-experiment code. The harness ([`src/hindcast.py`](../src/hindcast.py)) takes a
   config key and returns a skill record; the search layer just proposes config dicts.
2. **Factorization.** Most axes are near-separable. The search is staged:
   - **Stage 1 — seasons (A):** discover partitions from observed climatology (done offline,
     [`seasons.py`](../src/seasons.py)); this fixes the small set of target windows.
   - **Stage 2 — predictors (E–G):** for each season/zone, rank teleconnection indices and
     SST domains by *observed* predictive correlation *before* running any GCM calibration —
     a cheap screen that prunes axes F/G by orders of magnitude.
   - **Stage 3 — calibration & MME (H–J):** run CCA / ereg / logit / objective-average on
     the surviving predictors; pick per zone.
   - **Stage 4 — downscaling (K–L):** apply the resolution/skill frontier to the winning
     coarse forecast.
   - **Stage 5 — lead sweep (B):** repeat Stages 2–4 across init months to map skill-vs-lead
     and identify which predictor updates move the outlook.
3. **Agent-in-the-loop.** An agent proposes the next configuration to try from prior scores
   (e.g. "index screen says ATL3 dominates for the Guinea coast in AMJ — try an
   Atlantic-only SST domain and a logit-on-ATL3 config, compare to national CCA"), reads the
   skill record, and updates. This is Bayesian-optimization-flavored search with a physical
   prior, and it is exactly the loop the AGU abstract argues the stack was built to support.

## 4. The six headline experiments (mapped to the user's questions)

| Experiment | Axes varied | Question answered | Output |
|---|---|---|---|
| **E1 — Seasons** | A | *When to forecast?* Natural partitions of the Nigerian year | Zone map + season calendar |
| **E2 — Predictors** | E,F,G | *SST field vs. indices? Which teleconnections?* | Index-skill ranking per season/zone |
| **E2b — Feature discovery** | E,G,+ | *What OTHER predictors work? Which per season/zone?* | Cross-validated predictor leaderboard; discovered features beat textbook indices ([`06`](06_feature_discovery.md)) |
| **E2c — Drought/flood setups** | — | *What ocean state sets up drought/flood, where?* | Pre-season SST composites per season/zone ([`07`](07_drought_flood_setups.md)) |
| **E3 — Domain sizing** | C,F | *How big should predictor/predictand domains be? Does regional subsetting help?* | Skill vs. domain-size curves |
| **E4 — Calibration/MME** | H,I,J | *Which method & model combination?* | Method×model skill matrix |
| **E5 — Downscaling** | K,L | *Which method? How much resolution at what skill cost?* | Resolution/skill frontier |
| **E6 — Lead time** | B | *How does skill decay? Which updates help?* | Skill-vs-lead curves; update-attribution |

Each experiment is a *slice* of the matrix holding the other axes at a sensible default, so
the results are interpretable one axis at a time before the joint search in §3.

## 5. Data inventory (all via Rosetta)

| Role | Product(s) | Notes |
|---|---|---|
| Predictand (obs) | `obs/chirps-v3-monthly`, `-dekad`, `-daily` | 0.05°, 1981–present; the verification truth |
| Predictor SST (obs) | `obs/ersst-v5`, `obs/era5` (SST) | teleconnection indices & CCA training |
| Forecast GCMs | `nmme/{spear,ccsm4,geoss2s,cansipsic4,cfsv2}`, `c3s/{ecmwf,meteofrance,dwd,cmcc,ukmo,...}` | precip + SST; monthly seasonal |
| Sub-seasonal (lead studies) | `c3s/ecmwf-s2s`, `chc/chirps-gefs-*` | for the near-term end of the lead sweep |
| Reanalysis cross-check | `obs/era5` | observation-only teleconnection validation |

## 6. What makes this a *methods* contribution, not just a Nigeria study

Nigeria is the worked example, but the deliverable is the **procedure**: a config-driven,
uniformly-scored search over forecast/downscale space that is portable to any country and
season by changing `config.yml`. The same harness that discovered Nigeria's seasons and
ranked its teleconnections runs unchanged for the GHA (where it should recover the known
WVG-for-East-Africa result) or the Sahel band — which is the reproducibility claim the AGU
abstract rests on.
