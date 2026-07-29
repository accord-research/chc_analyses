# AGU Autoscience — Nigeria as a testbed for automated seasonal-forecast design

**One-line thesis.** The Rosetta (data) + DeepScale (forecast/downscale) stack is a
*modular, config-driven experiment engine*. Because every forecasting choice — season
window, predictor domain, variable, transform, teleconnection index, downscaling method,
target resolution, lead time — is a swappable parameter rather than bespoke code, the
whole design space can be **searched automatically**. This directory demonstrates that
"autoscience" loop on **three contrasting countries — Nigeria, Ethiopia, and Kenya** (re-pointed by
one config entry, `AREA=`) — and lays the groundwork for an AGU abstract arguing that agentic tooling
over this stack can *diagnose* where region-and-season-specific SST-based seasonal skill appears to
exist, and why. The findings are cross-validated but configuration-specific and subject to
multiple-comparison caveats — a **diagnostic framework, not general laws** (see
[docs/14](docs/14_limitations_and_caveats.md)).

> Companion work in this repo:
> [`analyses/chc_ethiopia/`](../analyses/chc_ethiopia/) shows a single teleconnection
> (El Niño → Kiremt drought) worked end-to-end for one country/season, and
> [`forecast-replication/`](../forecast-replication/) shows operational RCOF pipelines
> (ICPAC GHACOF with the Western-V-Gradient index; AGRHYMET/ACMAD for West Africa). This
> directory generalizes both: instead of *replicating one configuration*, it *searches the
> space of configurations* and asks which one is best for a given place, season, and lead.

---

## The questions this program answers

Framed as an autoscience search, each is a dimension of the experiment matrix
([`config.yml`](config.yml), [`docs/04_experiment_design.md`](docs/04_experiment_design.md)):

1. **Natural seasonal partitions.** When during the year should Nigeria issue seasonal
   forecasts (each 3–6 months, so 2–4 windows/year), given that the country spans a
   bimodal Guinea coast and a unimodal Sahel? *Discovered from data, not assumed.*
2. **Which predictors — including ones we discover.** Rather than assume a driver, *search*
   a pool of candidate features per season and subgeography: textbook SST indices (ENSO,
   Atlantic Niño, the Atlantic interhemispheric gradient, IOD, a Western-V-Gradient-style
   Pacific index — treated as *one candidate, not a centerpiece*), **data-driven SST
   patterns**, and **non-SST covariates** (rainfall persistence; roadmap: SST EOFs, soil
   moisture, circulation). Rank them by honest cross-validated skill and characterize *what
   ocean state sets up drought vs. flood, where and when.*
3. **SST fields vs. featurized indices.** Does a full gridded-SST predictor domain (CCA)
   beat a small set of physically-motivated scalar indices (logistic/regression
   calibration), or vice versa — and where?
4. **Predictor/predictand domain sizing.** What is the right size and location of the SST
   predictor box and the rainfall predictand region? Does regional subsetting of the
   predictand add skill over a single national model?
5. **Downscaling method & resolution.** Which downscaling method (BCSD, quantile mapping,
   CCA, rank-analog, CorrDiff) transfers a coarse (~1°) forecast to fine (~0.05°) skillfully?
   How much *resolution* can we add while *retaining* skill — and where is added detail
   valuable even when skill is merely maintained?
6. **Lead-time behavior.** How does skill decay with lead? As the init date moves closer to
   the season, which updated predictors change the outlook — and does the update always
   improve it?

## What "skill" means here

Every configuration is scored with the same DeepScale verification suite under
leave-one-year-out (LOYO) cross-validation, so comparisons are apples-to-apples:
**RPSS**, **ROC area / GROC**, **Pearson/Spearman correlation**, **2AFC**, **Heidke**,
reliability, and spread–error. Skill is always reported as a *map* (it varies across the
country) and *conditionally* (dry-tail vs. overall), following the CHC Ethiopia lesson that
average skill can hide where a forecast is actually trustworthy.

---

## Key findings (what the search actually found)

All results are real, on live CHIRPS-v3 + ERSST-v5 + NMME/C3S hindcasts via Rosetta, scored with
DeepScale under leave-one-year-out CV. **Read as a diagnostic framework, not general conclusions**
([docs/14](docs/14_limitations_and_caveats.md)): (i) these are *best-of-search* results over a large
space (~320 predictor comparisons per country), so they carry **winner's-curse / multiple-comparison
bias** that LOYO alone does not remove — only the strongest, mechanism-supported results (chiefly the
East African OND short rains) are robust; the rest are hypotheses; (ii) the perfect-prognosis
"benchmark" is the skill of a *statistical* SST→rainfall mapping, **not a theoretical ceiling** on
dynamical skill; (iii) at n ≈ 24–33 the 95% interval around r = 0 is ≈ ±0.4 and GROC gaps below ~0.1
are noise; (iv) all numbers are specific to *this* predictand/model configuration. Read the
qualitative, physically-anchored structure below, not the third decimal.

**1. Seasons are data-derived, and different per subgeography** ([docs/02](docs/02_seasonal_partition.md)).
k-means on the observed annual cycle recovers, without assuming a calendar, a **bimodal Guinea
coast** (May + October peaks around the "August break") transitioning north to a **unimodal
Sudano-Sahel** (single August/JAS peak). ⇒ 2–3 zone-staggered forecast windows/year: AMJ + SON/OND
for the south, JJAS/JAS for the north.

**2. Predictors are searched, not assumed — and the winner differs by season/zone**
([docs/03](docs/03_teleconnections.md), [docs/06](docs/06_feature_discovery.md)). Ranking a mixed
pool (textbook SST indices + a data-driven SST-projection pattern + rainfall persistence + a
multi-feature combo) by honest LOYO CV: the **data-driven SST pattern wins the core monsoon**
(CV corr 0.46 JJAS Middle Belt), the **Atlantic family** (ATL3, TNA−TSA) wins the Guinea/Middle
summer, **rainfall persistence** wins the northern late season, and a **multi-feature IOD +
persistence combo** wins the OND short rains. The Greater-Horn **Western-V-Gradient — included as
one candidate — never wins a recommended window.**

**3. Drought and flood have distinct, physical ocean setups** ([docs/07](docs/07_drought_flood_setups.md)).
Pre-season SST composites: **OND flood ← El Niño + warm Indian Ocean** (1997, 2019, 2023);
**JAS Sahel drought ← warm-Pacific-leaning** state (1997, 2011, 2004).

**4. Capstone — a different, data-derived recipe per zone × season** ([docs/09](docs/09_discovered_recipes.md)):
Middle-Belt/national JJAS monsoon → data-driven SST pattern (ceiling ~0.37–0.46); northern/national
OND → IOD + persistence combo (~0.24–0.29); Guinea-coast AMJ → ENSO; southern OND → IOD.

**5. The empirical predictability ceiling is real, but real dynamical forecasts don't reach it**
([docs/10](docs/10_real_mme_vs_ceiling.md)). Observation-only (perfect-prognosis) CV correlations
reach +0.23…+0.46, but a real NMME 4-model ensemble (CCA, LOYO) has **no usable skill** for JAS/OND
Nigeria (GROC 0.46–0.50, RPSS < 0). The gap between empirical predictability and dynamical
realization is the headline diagnostic.

**6. Searching the SST predictor domain recovers the right basin — but skill stays marginal**
([docs/11](docs/11_domain_and_method_search.md)). Teleconnection-CCA over swept SST domains: the
**Atlantic/Gulf-of-Guinea** wins the Middle-Belt monsoon, the **Pacific** wins the Sahel and OND
(ENSO → short rains, the only config with positive `r`). Domain choice moves GROC ~0.09 and never
picks the model's own precip — yet the best is only ~0.50–0.515.

**7. The best method is zone-specific, and not always CCA** ([docs/11](docs/11_domain_and_method_search.md)).
Across the full DeepScale registry (CCA, BCSD, QM, DQM, delta, rank-analog): **CCA** wins the Middle
Belt and OND, but **`delta` and `rank-analog`** win the **Sahel** (GROC 0.556/0.593, the strongest
real skill found). Pure distributional downscalers (BCSD/QM/DQM) ≈ climatology — they add
*resolution*, not calibration skill.

**8. The hybrid explains *why* the dynamical MME fails — the core result** ([docs/12](docs/12_hybrid_and_c3s.md)).
Feeding each model's *forecast SST* index into the observation-trained SST→rainfall link decomposes
the problem into *(is there a predictable link?)* × *(can the model forecast that SST?)*. The
**robust finding: the models forecast ENSO (corr 0.83) and the IOD (0.91) excellently but the
Atlantic Niño poorly (0.28)** — and for Nigeria the forecastable oceans (Pacific, Indian) teleconnect
only weakly, while the rainfall-controlling **Atlantic** is the one GCMs *can't* forecast. **The
forecastable ocean and the rainfall-relevant ocean are, for Nigeria, largely different oceans**, so
the binding constraint is Atlantic SST prediction — not the domain, the method, or (per the C3S
test, [docs/12](docs/12_hybrid_and_c3s.md)) the number of models.

**9. Three countries (Nigeria, Ethiopia, Kenya) — the framework as a per-region diagnostic**
([docs/13](docs/13_nigeria_vs_ethiopia.md)). Re-pointing the *same code* with one config entry
(`AREA=`, [src/areas.py](src/areas.py)) tests whether the Nigeria diagnosis generalizes. Run
identically, it *orders* the seasons consistently and points at *why*:
- **Skill realized** — *Ethiopia Kiremt & OND, Kenya OND short rains*: the driver is **ENSO / the
  IOD**, which GCMs forecast comparatively well → **dynamical skill** (OND MME GROC **0.70–0.73**,
  RPSS **+0.19–0.24**; hybrid +0.58…+0.75). Kenya's OND short rains have the highest benchmark
  examined (IOD ≈ **0.86**). This is the strongest, most defensible signal.
- **Skill limited** — *Nigeria monsoon*: a real statistical link, but to the **Atlantic**, which
  GCMs forecast less well → marginal MME skill for this configuration; not evidence of impossibility.
- **Low SST-based predictability** — *Ethiopia/Kenya MAM long rains*: the benchmark itself is ≈ 0
  (the East African "long-rains problem") — structurally low-skill, its controls (Congo/Walker
  winds, MJO) less SST-mediated; **low-predictability, not driverless**.
Along the way the framework *recovered* — as a consistency check with the literature — the
documented **WVG–East-Africa** relationship (well-ranked for Ethiopia's Kiremt and Kenya's JAS, not
for Nigeria), and El-Niño-associated Kiremt drought and positive-IOD-associated Greater-Horn floods.

**Bottom line for the AGU story.** The framework yields an automatically-computed, per-region
*diagnostic* — *how strong is the SST→rainfall link, and how forecastable is the driver?* — that
helps identify **where SST-based seasonal skill appears to exist, where it is limited, and why**.
This is a diagnostic lens, **not a general law**: the rankings are best-of-search over short records
and a single configuration, subject to winner's-curse and sampling caveats
([docs/14](docs/14_limitations_and_caveats.md)) — robust for the East African OND short rains,
suggestive elsewhere. The useful products are the observation-based recipes plus this map of where
dynamical skill does and doesn't appear, produced by re-pointing one config — the per-region
diagnostic the autoscience framework is built to deliver, and the argument the abstract makes.

**Tooling contribution.** The investigation also surfaced two Rosetta fixes (longitude-convention
under-selection; NetCDF round-trip), landed on an isolated `_autoscience` library branch with tests
— see [docs/08](docs/08_library_contributions.md) for the full register of reusable methods to
upstream.

---

## Directory layout

```
AGU-autoscience/
├── README.md                      ← you are here
├── AUTOSCIENCE_REPORT.ipynb       ← notebook report: story + full abstract + inline plots (+ .html)
├── ABSTRACT.md                    ← draft AGU abstract (+ plain-language + extended)
├── APPROACH.md                    ← the autoscience method: search loop, scoring, provenance
├── EXPERIMENT_LOG.md              ← append-only run log (per repo convention)
├── config.yml                     ← the Nigeria experiment matrix (single source of truth)
├── docs/
│   ├── 01_nigeria_climate_background.md   ← WAM climatology, regimes, drivers (lit-grounded)
│   ├── 02_seasonal_partition.md           ← method + results: discovering the seasons
│   ├── 03_teleconnections.md              ← method + results: SST index ↔ rainfall diagnostics
│   ├── 04_experiment_design.md            ← the full experiment matrix & scoring protocol
│   ├── 05_downscaling_plan.md             ← downscaling methods, resolution/skill tradeoff
│   ├── 06_feature_discovery.md            ← searching for predictors (data-driven + covariates)
│   ├── 07_drought_flood_setups.md         ← what ocean state sets up drought/flood, where
│   ├── 08_library_contributions.md        ← reusable methods to upstream into rosetta/deepscale
│   ├── 09_discovered_recipes.md           ← CAPSTONE: best recipe per zone × season
│   ├── 10_real_mme_vs_ceiling.md          ← real NMME forecast skill vs predictability ceiling
│   ├── 11_domain_and_method_search.md     ← search SST domain + method axes (real MME)
│   ├── 12_hybrid_and_c3s.md               ← hybrid stat-dynamical forecast; +C3S models
│   ├── 13_nigeria_vs_ethiopia.md          ← SAME harness, 3 countries: the diagnostic ordering
│   └── 14_limitations_and_caveats.md      ← multiplicity/winner's-curse, benchmark≠ceiling, softened claims
├── src/
│   ├── areas.py                   ← region config (nigeria/ethiopia); AREA=... selector
│   ├── fetch_data.py              ← cache CHIRPS + ERSST (+ NMME) via Rosetta  [runnable]
│   ├── seasons.py                 ← seasonal-partition discovery                [runnable]
│   ├── teleconnections.py         ← SST-index ↔ rainfall diagnostics            [runnable]
│   ├── feature_discovery.py       ← searched predictor leaderboard (LOYO CV)     [runnable]
│   ├── composites.py              ← drought/flood pre-season SST setups          [runnable]
│   ├── synthesize_recipes.py      ← capstone: best recipe per zone × season      [runnable]
│   ├── demo_hindcast_logit.py     ← ONE real cross-validated skill result       [runnable]
│   ├── mme_hindcast.py            ← REAL NMME multi-model forecast vs ceiling    [runnable]
│   ├── mme_search.py              ← search SST predictor domain (CCA MME)        [runnable]
│   ├── mme_methods.py             ← search method registry (CCA/BCSD/QM/…)       [runnable]
│   ├── hybrid_forecast.py         ← model SST forecast → obs-trained link        [runnable]
│   ├── mme_c3s.py                 ← NMME+C3S expanded ensemble (CDS)             [runnable]
│   ├── detrend_check.py           ← raw vs in-fold-detrended LOYO robustness      [runnable]
│   ├── report_figures.py          ← synthesis figures for the notebook report     [runnable]
│   ├── build_report.py            ← assemble AUTOSCIENCE_REPORT.ipynb             [runnable]
│   ├── hindcast.py                ← config-driven hindcast harness (DeepScale)  [scaffold]
│   └── plotting.py                ← shared figure helpers
├── data/                          ← cached NetCDF (gitignored; rebuilt by fetch_data.py)
└── outputs/
    ├── figures/                   ← generated figures
    └── tables/                    ← generated skill/summary tables
```

## How to run

```bash
conda activate accord-chc          # has rosetta + deepscale (editable) + xarray/netCDF4
cd AGU-autoscience

python src/fetch_data.py all       # one-time cache: ERSST (~6s) + CHIRPS (~18min, see below)
python src/seasons.py              # -> outputs/figures/seasons_*, docs/02 results
python src/teleconnections.py      # -> outputs/figures/teleconn_*, docs/03 results
python src/feature_discovery.py    # -> predictor leaderboard per season/zone, docs/06 results
python src/composites.py           # -> drought/flood SST setups, docs/07 results
python src/synthesize_recipes.py   # -> capstone: best recipe per zone × season, docs/09
python src/demo_hindcast_logit.py [index]  # -> ONE real LOYO-cross-validated skill map
python src/mme_hindcast.py         # -> REAL NMME multi-model forecast skill vs the ceiling
python src/mme_search.py           # -> best SST predictor domain per season/zone (CCA MME)
python src/mme_methods.py          # -> best method (CCA/BCSD/QM/delta/rank-analog/…) per cell
python src/hybrid_forecast.py      # -> hybrid: model SST forecast → obs-trained link, docs/12
python src/mme_c3s.py              # -> NMME+C3S expanded ensemble (needs CDS), docs/12
python src/hindcast.py <config_key>  # a single GCM hindcast configuration (compute-bound)
```

**Second country (same code).** Every script above is region-parameterized via
[`src/areas.py`](src/areas.py); prefix with `AREA=ethiopia` to run the whole pipeline for Ethiopia
(outputs get `_ethiopia` suffixes; Nigeria's files are untouched). E.g.
`AREA=ethiopia python src/fetch_data.py chirps` then `AREA=ethiopia python src/hybrid_forecast.py`.
Adding a third country is one entry in `areas.py`. See [docs/13](docs/13_nigeria_vs_ethiopia.md).

**Fetch note.** `obs/ersst-v5` returns the whole tropical belt in seconds; `obs/chirps-v3-monthly`
downloads one COG per month serially (~3 s each), so the 1991–2023 record is ~18 min — it is
linear in months, not stuck. Rosetta caches the raw result, so re-runs are instant. See
[`EXPERIMENT_LOG.md`](EXPERIMENT_LOG.md) for the fetch gotchas (longitude convention, NetCDF
write conflict) and their fixes in [`src/fetch_data.py`](src/fetch_data.py).

`fetch_data.py` writes to `data/` and every other script reads from that cache, so the
network is touched once. See [`APPROACH.md`](APPROACH.md) for how the individual scripts
compose into the automated search loop.

## Status

**Landed (real data, real numbers, all findings above):** season discovery, teleconnection
diagnostics, the feature-discovery leaderboard, drought/flood composites, the discovered-recipes
capstone, the perfect-prognosis ceiling, a logit CV skill result, the real NMME MME vs. ceiling,
the **SST-predictor-domain search**, the **method search across the full DeepScale registry**, the
**hybrid statistical-dynamical decomposition**, and the **NMME+C3S expansion** — all on live
CHIRPS-v3, ERSST-v5, and NMME/C3S hindcasts via Rosetta, scored with DeepScale.

**Scaffolded / next levers (see [docs/12](docs/12_hybrid_and_c3s.md) synthesis):** the *exhaustive*
joint sweep over the full matrix (all zones × seasons × leads × domains × methods × resolutions);
the downscaling resolution/skill frontier ([docs/05](docs/05_downscaling_plan.md)); a lead-time
sweep; and — the physically-indicated priority — an Atlantic-focused predictability study, since
the hybrid localized the binding constraint to the models' Atlantic SST forecast. The
config-driven harness ([`hindcast.py`](src/hindcast.py), [`config.yml`](config.yml)) is the chassis
an agentic runner would drive for the joint sweep.

The [`EXPERIMENT_LOG.md`](EXPERIMENT_LOG.md) records every run with dates and outcomes (append-only,
per repo convention); this README's **Key findings** section is the standing synthesis.
