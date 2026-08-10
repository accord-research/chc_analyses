# Can a machine draw its own forecast map?

### Discovering seasonal rainfall zones for the eastern Horn of Africa, and measuring whether the result is worth having

2026-08-10

---

## Introduction

Seasonal rainfall outlooks for the eastern Horn of Africa are built from three design choices: which sub-regions behave alike, which months are each region's rainy season, and which ocean index (at which lead) predicts that season. Those choices are usually made by people and reused for years. This work asks whether an algorithm can recover them from data — regions and seasons from the rainfall record alone; predictors from a fixed menu of sea-surface temperature indices — and whether the resulting atlas is worth issuing.

A prior analysis (AGUv3) showed that clustering rainfall structure can recover operational-looking zones, calendars, and teleconnection recipes, including published conditional rates for the March–May long rains. That work was largely in-sample. Here the same discovery machinery is placed inside a walk-forward design: every fit uses training years only; skill is scored out of sample as **RPSS** (how much better tercile forecasts are than climatology); and the headline claim must beat a null that reruns the procedure on year-scrambled rainfall, so selection among twenty index–lead combinations is paid for. Prior-work reproduction and one measured full-record leak sit in Appendix B.

**Roadmap.** Methods states the algorithm. Results gives the pre-registered USEFUL verdict for the whole atlas. Discovery describes the map and seasons. Product skill asks whether that atlas beats a single pooled outlook as something a forecast centre would issue. Same-target skill holds the predictand fixed, so only the partition can explain skill differences. March–May tests the long-rains claim under the selection-aware null. Expert overlap is descriptive. Limitations and appendices cover bounds, the `rx` research record, AGUv3, and regeneration checks.

**Data and terms.**

- **CHIRPS v3** — monthly satellite-and-gauge rainfall, 1981–2023, over 33–52°E, 5°S–12°N (coarsened to 0.25°).
- **ERSST v5** — sea-surface temperature; the only predictors considered are five indices built from it:
  - **Niño-3.4** — central-eastern equatorial Pacific (5°S–5°N, 170°W–120°W); El Niño / La Niña.
  - **Indian Ocean Dipole** — western Indian Ocean (50–70°E) minus eastern (90–110°E); often cited for the October–December short rains.
  - **West Pacific Gradient (WPG)** — west Pacific (130–150°E) minus Niño-3.4, each standardised first.
  - **Western-V Gradient (WVG)** — Niño-3.4 minus a V-shaped west Pacific box (5–20°N, 130–170°E), each standardised first; prescribed in Climate Hazards Center work for March–May.
  - **IWHG** — published fixed-weight combination of the Dipole, west Pacific box, and Niño-3.4.
- **Lead** — how far ahead of the rainy season the ocean is read (0, 1, 2, or 3 months).
- **Zone** — a set of grid cells the clustering groups together (an output, not an input).
- **Window** — a three-month rainy season detected from peaks in a zone's mean annual cycle (at most two per zone).
- **Fold** — one train/test split. Six expanding walk-forward folds; test years are never seen when their forecast is made.
- **RPSS** — Ranked Probability Skill Score of tercile probabilities versus equal-thirds climatology. Defined operationally in Methods; positive beats climatology, zero matches it, negative is worse.

Rainfall alone decides where the zones are and when their seasons fall. Ocean temperature decides what predicts each zone-season.

---

## Methods

Domain: monthly CHIRPS v3 over 33–52°E, 5°S–12°N, 1981–2023, coarsened to 0.25°. Predictors: the five ERSST indices above, at leads 0–3 months. Evaluation uses six expanding walk-forward folds: train on all years up to a cut, test on the next three or four. Everything below is fitted on the training years of the fold and applied unchanged to the test years.

### 1. Rainfall regions

Zone discovery uses rainfall only. No ocean index, coordinates, country boundary, or expert region enters the clustering.

For each valid land cell, two feature blocks are built from the training years:

1. **Cycle shape.** The 12-month mean climatology, standardised within the cell so that timing matters and absolute amount does not.
2. **Interannual co-variability.** Loadings on the leading five EOFs of monthly anomalies, so cells with similar calendars but decoupled year-to-year behaviour can separate.

The two blocks are column-standardised, weighted equally by block, and concatenated (17 dimensions). Cells are partitioned with k-means for each candidate \(k \in \{2,\ldots,8\}\).

**Choosing \(k\).** For each \(k\), cluster the full training set, then redraw 20 year-bootstrap resamples, rebuild the features, recluster, and measure the adjusted Rand index (ARI) against the full-training labels. Select the **largest** \(k\) whose mean bootstrap ARI is at least 0.90. If none reach 0.90, take the \(k\) with maximum ARI. The threshold is fixed in advance; the full \(k = 2\ldots 8\) curve is always reported.

The resulting cell→zone map is applied to the test years without refitting.

### 2. Rainy seasons

For each zone, form the area-weighted mean annual cycle (mm/month) over the training years. Months that are local maxima above 15% of the cycle maximum are peaks. Each peak becomes the three-month window of largest total that contains it. At most two windows are kept per zone (the two with largest totals). Windows that wrap the calendar (e.g. November–January) are labelled by the year of their last month.

### 3. Predictor and lead

For each zone-season, evaluate all five indices at all four leads (twenty combinations). On the training years, fit a linear regression from the index to the zone's seasonal rainfall total, convert the prediction to tercile probabilities using training-only tercile edges, and retain the combination with highest training skill. Test years are never used to choose.

### 4. Forecast and score

Issue tercile probabilities for every zone-season on every test year. Score with area-weighted RPSS against equal-thirds climatology: each zone carries its share of domain area, divided evenly between its rainy seasons. No zone-season is dropped for weak skill.

### 5. Null and decision rule

Maximising over twenty index–lead combinations can produce positive scores under no true ocean–rain relationship. To account for that selection, scramble the rainfall years 200 times (complete seasons, not calendar years that straddle New Year), and rerun the identical procedure on each scramble. The observed-data atlas is judged **USEFUL** only if both criteria fixed before the run hold: RPSS > 0, and better than the scrambled runs at \(p ≤ 0.05\).

**Provenance.** Every scientific command was run through `rx` (`rx run exec` or `rx run benchmark`), which records code state, stdout/stderr, experiment attachment, and leaderboard metrics. How to read that record is Appendix A.

---

## Results

To evaluate whether the algorithm finds meaningful rain regions and seasons, we scored the maps it produced — and the rainy seasons it derived for each region — on a forecasting task. For each zone-season, an ocean index predicts next season's rainfall category (dry / normal / wet thirds). Skill is RPSS: how much better those forecasts are than climatology (always one-third for each category). Positive means better than that baseline; zero means no better; negative means worse.

For each zone-season the procedure evaluates twenty index-and-lead combinations and retains the best on the training years. Maximising over that discrete search space can yield spuriously positive out-of-sample scores under the null of no ocean–rain relationship. To account for that selection, we scramble the rainfall years 200 times — destroying any real temporal alignment with the ocean indices — and rerun the identical procedure on each scramble. The observed-data result counts as useful only if it clears both criteria fixed before the run: RPSS above zero, and better than the scrambled runs at \(p ≤ 0.05\).

| what was measured | value |
|---|---:|
| Skill of the whole map on held-out years (RPSS) | **+0.2044** |
| Typical skill when years are scrambled | −0.0574 |
| Best skill among 200 scrambled runs | +0.0782 |
| Chance of a result this good when years are scrambled (\(p\)) | **0.0050** |
| Pre-set verdict | **USEFUL** |

The observed-data result beat not only the mean scramble but the best of all 200, so \(p\) sits at its floor of \(1/201\) — the permutation estimator counts the observed run among the draws. RPSS > 0 alone would not suffice, because selecting the maximum of twenty combinations can produce positive scores under noise. A small \(p\) alone would not suffice either: a procedure can be distinguishable from the null and still forecast worse than climatology.

This \(p\)-value accounts for selection over predictors and lead times. It does not account for zone discovery: zoning uses only rainfall, never the ocean indices or the score, and every zone found is retained. Whether the partition itself improves skill is addressed under Same-target skill, and answered more modestly there.

---

## Discovery

**Question:** What rainfall regions and seasons does the procedure produce, and do they stay the same across folds?

The stability rule selected **two zones in all six folds**. Mean bootstrap ARI for \(k = 2\) is above 0.90 everywhere; for \(k = 3\) it sits at 0.881–0.895 and never clears the bar.

| fold | zones chosen | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 2 | 0.938 | 0.881 | 0.761 | 0.654 | 0.618 | 0.585 | 0.558 |
| 1 | 2 | 0.937 | 0.895 | 0.719 | 0.610 | 0.601 | 0.568 | 0.579 |
| 2 | 2 | 0.949 | 0.893 | 0.805 | 0.629 | 0.649 | 0.599 | 0.636 |
| 3 | 2 | 0.941 | 0.891 | 0.763 | 0.601 | 0.680 | 0.654 | 0.665 |
| 4 | 2 | 0.939 | 0.893 | 0.767 | 0.645 | 0.736 | 0.628 | 0.625 |
| 5 | 2 | 0.946 | 0.895 | 0.719 | 0.602 | 0.636 | 0.615 | 0.615 |

The two zones are a wet highland west and a dry east. The west has rainy seasons in May–July and July–September. The east has March–May (long rains) and October–December (short rains). Neither the split nor the seasons were supplied.

The map is stable across folds. Pairwise agreement averages 0.9675 (1.0 = identical) and never falls below 0.9425. Only 1.2% of grid cells ever change zone between any pair of folds. Both zones appear in every fold.

| zone | folds present | cell agreement | centre drift lat/lon | same season | same predictor | skill | years scored |
|---|---:|---:|---|---:|---:|---:|---:|
| 0 | 6/6 | 0.975 | 0.02° / 0.05° | 0.67 | 1.00 | +0.1660 | 40 |
| 1 | 6/6 | 0.988 | 0.01° / 0.03° | 1.00 | 1.00 | +0.2122 | 44 |

A pre-registered test — whether stabler zones forecast better — could not be run: with two zones there are two points, and a correlation of two points is uninformative. That hypothesis is untested, not unsupported. The specification anticipated three to eight zones; two is below that range. Testing it would require a finer map (which would abandon the fixed \(k\) rule) or a larger domain.

Figures: `outputs/figures/zone_maps_by_fold.png`, `outputs/figures/annual_cycles_by_fold.png`, `outputs/figures/switch_map.png`, `outputs/figures/ari_matrix.png`.

---

## Product skill

**Question:** As a forecast product a centre might issue — one outlook per zone-season covering the domain — does the discovered map beat a single pooled region?

Four arms cover the same geography with the same total weight:

- **Climatology** — equal thirds every year (must score exactly zero; check that scoring is not broken).
- **One pooled region** — whole domain as a single zone.
- **Discovered zones, one shared recipe** — machine map, but every zone forced to the same ocean predictor.
- **Discovered zones, own recipe each** — the full procedure.

| way of covering the ground | walk-forward | k-fold |
|---|---:|---:|
| climatology (the check) | +0.0000 | +0.0000 |
| one pooled region | −0.0168 | −0.0066 |
| discovered zones, one shared recipe | +0.1928 | +0.0781 |
| discovered zones, own recipe each | +0.2044 | +0.0781 |

Paired differences on the same 200 scrambles:

| comparison | difference | \(p\) |
|---|---:|---:|
| discovered zones vs one pooled region | +0.2212 | 0.0050 |
| own recipe each vs one shared recipe | +0.0116 | 0.1244 |

Splitting the domain in two is worth a large skill gain. Giving each zone its own predictor is not. The map does the work, not per-zone predictor choice.

Two weighting rules were fixed before the run, and both are reported. Each gives a zone the same share of domain area; they differ in how that share is divided between the zone's two rainy seasons. The headline rule splits it evenly. The alternative splits it in proportion to each season's rainfall total. The full procedure — discovered zones, own recipe each — scores both ways:

| way of dividing a zone's weight between its seasons | walk-forward | k-fold |
|---|---:|---:|
| evenly | +0.2044 | +0.0781 |
| in proportion to each season's rainfall | +0.1900 | +0.0695 |

The alternative was not run against the scramble null and carries no verdict of its own. It establishes that the headline is not an artefact of the split rule.

This is not yet proof that zoning models rainfall better. The arms forecast different things: a two-zone map issues more seasonal outlooks, at seasons suited to each regime; a one-zone map issues fewer, at seasons suited to a highland–lowland average. Part of the gap is better regionalisation; part is a different product. The next section holds the predictand fixed.

Per-zone detail: `outputs/atlas_per_zone.json`.

---

## Same-target skill

**Question:** When every arm predicts the same rainfall total, does zoning still help?

Here zones are internal machinery only. Predictions are recombined into one regional average (or scored at every grid cell). Any difference is attributable to the partition, not to which seasons each map chose to issue.

| test | season | one pooled region | using discovered zones | difference |
|---|---|---:|---:|---:|
| one regional total | MAM | +0.0555 | +0.1160 | **+0.0605** |
| one regional total | OND | +0.3053 | +0.3071 | **+0.0019** |
| every grid cell scored | MAM | −0.0005 | +0.0060 | **+0.0065** |
| every grid cell scored | OND | +0.1819 | +0.1744 | **−0.0074** |

Zoning helps March–May by about six hundredths of RPSS on the regional total, and does essentially nothing for October–December. On the short rains the difference is +0.0019 on one test and slightly negative on the other.

So the large margin under Product skill is mostly about what each map chooses to forecast. Once the target is held fixed, this work agrees with the earlier finding that partitioning a fixed predictand fails to beat pooling it by much. A forecaster can still prefer the discovered map as a product; a modeller should not read it as a clearly better statistical model of East African rainfall. Both readings are consistent.

---

## March–May long rains

**Question:** Does March–May skill — including under La Niña or negative Western-V gradient conditions — clear a selection-aware null?

Earlier work reported strong conditional dry-tail rates for the long rains. This section tests MAM under RPSS with the scramble null that pays for searching twenty index–lead combinations. Three year sets are pre-registered: all MAM years; La Niña years only; negative-gradient years only. Membership in the conditional sets is decided from training data alone. MAM is scored for every zone whether or not the season detector found a MAM window there.

| map used | years scored | skill | \(p\) | clears? |
|---|---|---:|---:|---|
| one pooled region | all years | +0.0555 | 0.1592 | no |
| one pooled region | La Niña only | +0.0910 | 0.1592 | no |
| one pooled region | negative gradient only | +0.0573 | 0.2090 | no |
| zones, one shared recipe | all years | +0.0368 | 0.1990 | no |
| zones, one shared recipe | La Niña only | +0.0625 | 0.2239 | no |
| zones, one shared recipe | negative gradient only | +0.0382 | 0.2438 | no |
| zones, own recipe each | all years | +0.0431 | 0.1393 | no |
| zones, own recipe each | La Niña only | +0.0370 | 0.2338 | no |
| zones, own recipe each | negative gradient only | +0.0199 | 0.3035 | no |

None of the nine combinations clears \(p ≤ 0.05\). The smallest \(p\) is 0.1393. Several skill values are positive — conditioning on La Niña lifts the point estimate — and none survives the cost of the predictor–lead search. Under this evaluation design, the long rains remain unpredictable.

---

## Expert overlap

**Question:** Does the discovered eastern zone coincide with hand-drawn eastern-Horn boxes?

These comparisons are descriptive. Expert regions are not ground truth. Agreement is reassuring; disagreement would not be evidence of error.

| hand-drawn expert region | machine zone | share of the expert box inside it |
|---|---:|---:|
| AGUv2 eastern-Horn box | 1 | 92.1% |
| reviewer south-central Somalia | 1 | 99.8% |

Within-country orientation (\(\eta^2\)): Kenya and Somalia both split more east–west than north–south (Kenya 0.097 vs 0.015; Somalia 0.090 vs 0.065), consistent with a highland-versus-drylands divide in Kenya. This section decides nothing about skill.

---

## Limitations

- **Twenty-two test years.** Walk-forward scores three or four years per fold. Every skill number rests on that sample.
- **Earliest fold.** The first expanding window trains on twenty-one years; its map is the least informed.
- **Stability-vs-skill untested.** Only two zones; the planned correlation could not be run.
- **Observed SST, not forecast SST.** Operational skill is (can a model forecast the index) × (does the index predict rainfall). Only the second factor is measured here.
- **At most two rainy seasons per zone.** A three-season regime would be truncated.
- **The 0.90 ARI threshold is still a threshold.** \(k = 3\) scores 0.881–0.895 in every fold. A slightly different bar would yield a different map.
- **Product skill ≠ same-target skill.** The large product margin is not a controlled test of the zoning model.
- **ERSST was refetched.** Ocean-dependent AGUv3 numbers reproduce, but the bytes are not the original archive copy.
- **Supporting libraries have uncommitted local changes.** File hashes are recorded; the environment is not rebuildable from version control alone.

---

## Appendix A — Research record (`rx`)

Every scientific command ran through **`rx`** (free-form `rx run exec` or locked `rx run benchmark`). The narrative here is a summary; the audit trail is `.rx/` locally, with a committed spine in `RESEARCH_LOG.md`.

| id | role |
|---|---|
| `e:1` | Orient; write SPEC (concluded) |
| `e:2` | v1 implementation under SPEC rev 3 (concluded; pilot) |
| `e:3` | Amendment-1 correction; holds the headline leaderboards (concluded) |

Headline number: `atlas-wf-v2` arm `zones-specific` (`rpss_atlas = 0.204416`), judged against the paired null. Same-target controls are `fixedmean-*-v2` / `grid-*-v2`. Cross-cutting reads: `a:1` (zonation gain vs controlled test), `a:2` (H1 untestable). Pre-result contracts: `legacy/contracts/`. Orient: `rx status` from this directory; regenerate: `./regenerate.sh` (defaults to `e:3`). See `README.md`.

---

## Appendix B — Prior work (AGUv3): what it did, why this design differs, and one measured leak

### What AGUv3 did

AGUv3 asked whether forecast zones, rainy seasons, and teleconnection recipes for the eastern Horn could be recovered from rainfall structure alone. Public summary: `SHOWCASE.md` in the AGUv3 project. On the same CHIRPS domain and ERSST indices, it ran four scripts:

1. **`zones.py`** — k-means on cycle shape + anomaly EOF loadings; \(k\) by year-bootstrap ARI; rainy-season windows from cycle peaks.
2. **`hierarchy.py`** — also report \(k = 3\) and \(k = 4\).
3. **`wvg_by_zone.py`** — Western-V Gradient scored with leave-one-year-out correlation and dry-tail / La Niña–conditional rates.
4. **`search.py`** — tensor search  
   \(\text{zone}(k{=}4) \times \text{window} \times \text{index}(5) \times \text{lead}(0\text{–}3) \times \text{mode}(\text{symmetric} \mid \text{dry-tail})\)  
   = 520 cells, one permutation null (1,000 shuffles), Benjamini–Hochberg at \(\alpha = 0.10\).

Published claims: eastern-zone MAM dry-tail rates **0.79** under strong-negative WVG and **0.77** with La Niña (\(n = 13\)) at \(k = 3\) and \(k = 4\); **79 of 520** cells survive FDR; best recipes match documented drivers. AGUv3 did not use walk-forward RPSS or a USEFUL gate.

### Why this project changes the evaluation

AGUv3 fitted zonation, thresholds, and several index normalisations on the full record and reported in-sample / leave-one-year-out statistics. That design can recover operational structure and still not answer whether an atlas is worth issuing out of sample. This project keeps the discovery machinery, puts every fit inside the training fold, scores with RPSS, and judges skill against season-scrambled nulls.

### Exact reproduction

Reproduction does not reimplement AGUv3. It runs the four pinned scripts from `legacy/AGUv3/src/` unmodified against the fixtures locked here, and diffs the emitted markdown tables against `legacy/AGUv3/outputs/tables/`.

| tier | depends on | tolerance | result |
|---|---|---|---|
| 1 | CHIRPS only | exact / stated numeric tolerance | **14 / 14** |
| 2 | CHIRPS + ERSST | 0.01 on statistics; survivors within ±3 | **10 / 10** |

Matched: zone cell counts at \(k = 2,3,4\); ARI curves; discovered windows; all 22 hierarchy statistics (max \(\lvert\Delta\rvert = 0.000\)); eastern MAM rates **0.79 / 0.77** at \(k = 3\) and \(k = 4\); 520-cell tensor with **79** FDR survivors; all **7** best-per-zone-window recipes. Not compared: a cell-by-cell zone-label vector (AGUv3 never committed `data/`). At \(k = 2\) the eastern MAM rates are 0.71 / 0.69 — not the published headline.

Command: `python legacy/reproduce_agu3.py`. Record: `outputs/legacy_reproduction.json`.

### One measured leak

Two of the five indices — the West Pacific Gradient and the Western-V Gradient — are differences of standardised SST series. Standardisation estimates a mean and a standard deviation. Estimating those from all years, including years later treated as test, lets future ocean data set the scale of the predictor.

Two otherwise identical out-of-sample runs differ only in whether WPG and WVG are standardised on the full record or on training years alone. Niño-3.4, IOD, and IWHG have no fitted scale of that form, so they cannot respond to the change.

| fold protocol | train-only standardisation | full-record standardisation | difference |
|---|---:|---:|---:|
| walk-forward | +0.2044 | +0.2083 | **−0.0039** |
| k-fold | +0.0781 | +0.0786 | **−0.0006** |

The leak flatters skill by about four thousandths of RPSS. AGUv3 carried six full-record issues; this subtraction isolates one. The other five (full-record median, threshold, La Niña definition, map on all years, no held-out test) are removed together by the out-of-sample design and are not separated from one another.

---

## Appendix C — How to check any of this

Everything regenerates with `./regenerate.sh`. Every step is an `rx` run (Appendix A). The environment record `outputs/env.json` is one of the files each benchmark locks, so the script verifies it against the registered hash rather than rewriting it; a rewrite would stamp a fresh timestamp into a locked input and every submission would then be refused.

After a runner change, all 600 scrambled-data rows rematched with largest difference \(0\). An earlier scramble shuffled calendar years and broke seasons that straddle New Year (e.g. November–January); the replacement shuffles complete seasons. That defect is recorded as dead-end `f:15`.

Five score implementations are checked along three links: the batched scorer against the per-cell scorer, the per-cell scorer against the locked evaluator, and the fast atlas scorer against its slow reference. Every link agrees to \(1.3\times10^{-15}\) or better, against a required tolerance of \(10^{-8}\).

| check that had to pass first | result |
|---|---|
| equal-thirds forecast scores zero | exactly 0 |
| planted ocean signal recovered | RPSS +0.2937 |
| synthetic two-zone map recovered | boundary agreement 1.0000 |
| synthetic driving index identified per zone | correct in both zones |
| shuffling years removes skill | mean −0.0870 over 4 shuffles |

| input | fingerprint |
|---|---|
| chirps_v3 | 266,686,549 bytes, sha256 `d7acf0304ba82789cfc4…` |
| ersst_v5 | 15,246,450 bytes, sha256 `a9c91583b92e71d24362…` |
| deepscale | 56 source files, tree hash `29d3d83e47b94515e33d…` |
| rosetta | 23 source files, tree hash `eaf3e99ba5339af25ec9…` |

Pre-result contracts: `legacy/contracts/` (written before results). Research log: `RESEARCH_LOG.md` (snapshot of `.rx/NOTES.md`; see Appendix A).
