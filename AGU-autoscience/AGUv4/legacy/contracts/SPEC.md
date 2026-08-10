# SPEC.md — v3rx: the discovered forecast atlas

Status: **REVISION 3, APPROVED — then AMENDED. Archived under `legacy/contracts/`. Read `SPEC_AMENDMENT_1.md` alongside this file. The live entry point for readers is `../../README.md` + `../../REPORT.md`.**

> **Amendment 1 supersedes parts of this document.** Review of the v1 implementation found
> three defects: the legacy check verified the k=2 rates rather than the published k=3/k=4
> headline and promised an ARI=1 comparison against a label vector that does not exist;
> only one of the three §16 scorer-agreement links was actually run; and the null's
> calendar-year field permutation could splice a wrapping season across two donor years.
> Where this file and Amendment 1 disagree, **Amendment 1 governs**. The affected sections
> are §9.1 (Tier 1's ARI claim, Tier 2's headline check), §16 (all three links are now
> mandatory gates), and §14 (the null is now a complete-season target permutation with a
> shared per-fold support). Benchmarks `atlas-wf-v2` / `atlas-kf-v2` implement the amended
> contract; the v1 pair is retained as a pilot record.
Author: Claude, for Ezekiel Barnett · ACCORD · 2026-08-06
Predecessors: `chc_analyses/AGU-autoscience/AGUv3` (the scientific task), `v4zeek` (the harness)
Revision 2 applied Ezekiel's decisions on ERSST, k selection and permutation budget, and corrections A–E.
Revision 3 gives the primary claim a null and a decision rule, makes aggregate scoring fold-local and
matching-independent, replaces dirty-file counts with source-tree hashing, and restates the question.

---

## 0. The question, stated correctly, and what this document locks

**The question.** *Rainfall alone discovers the zones and their seasons. SST is required to select each zone-season's forecast recipe. Does that division of labour produce a stable, useful seasonal-forecast atlas?*

- **This phrasing is a correction, and the correction matters.** Revisions 1 and 2 asked whether "rainfall data alone" could produce a forecast atlas. That was wrong: rainfall alone cannot forecast anything here. Steps 1 and 2 of the pipeline — the partition and the rainy-season windows — use rainfall and nothing else. Step 3, choosing a predictor and a lead for each zone-season, is entirely SST-driven, and step 4 forecasts from SST. The claim under test is about the *division of labour*, not about a single data source.
- **What each half is asked to do:**
  - **Rainfall alone must define the forecast units.** The partition of all valid land cells, and each zone's rainy-season windows, come from the rainfall field and from no other input — not from SST, not from coordinates, not from country boundaries, not from expert regions.
  - **SST must supply the recipes.** For every discovered zone-window the procedure selects one index and one lead from a fixed candidate space, and fits a forecast.
- **An atlas** is that complete object: a partition covering every valid cell, each zone carrying its windows and its recipes.
- **"Useful"** means the complete atlas beats climatology by more than searching noise this hard produces anyway. It is one procedure-level RPSS on held-out years, adjudicated against a permutation null with a decision rule fixed in §10.6.
- **"Stable"** means the discovered objects agree across folds. It is measured separately, in §11, and is *never* inferred from skill.
- **This document fixes every choice that a result could otherwise be selected on.** Anything not fixed here is a bug in this document, not a degree of freedom.
- **The rx record is the audit trail.** Every run goes through `rx run exec` or `rx run benchmark`. Hypotheses are recorded before runs. Findings, retractions and dead ends are recorded as they occur.
- **The rx project objective still carries the revision-1 phrasing**, because rx offers no CLI to edit it after `rx init`. This section is the authoritative statement of the question; the divergence is recorded in `.rx/NOTES.md` rather than left to be discovered.
- **§20 records the decisions taken in review and what remains open.**

---

## 1. The record, the domain, and the spatial grid are fixed

### 1.1 Rainfall

| item | value |
|---|---|
| product | CHIRPS v3.0 monthly, native 0.05°, via `rosetta.fetch(product="obs/chirps-v3-monthly", variable="precip")` |
| spatial domain | 33–52°E, 5°S–12°N (`bbox = [-5.0, 12.0, 33.0, 52.0]`) |
| record | 1981–2023, 516 complete months, 43 season-years, no incomplete year |
| realised grid | lat 4.975°S–11.975°N (n=340), lon 33.025–51.975°E (n=380), step 0.05° |
| analysis grid | `coarsen(lat=5, lon=5, boundary="trim").mean()` → 0.25°, 68 × 76 = 5168 cells |
| valid land cells | 3564 (69.0% of the box), by the AGUv3 rule: finite 12-month climatology **and** annual total > 1e-3 mm/day |
| area weight | `cos(lat)`, range 0.9786–1.0000 over the valid cells |
| fixture file | `data/chirps_v3_ea_monthly.nc` |
| fixture bytes | 266,686,549 |
| fixture sha256 | `d7acf0304ba82789cfc431f7d917df2bb3a8950c678765dfd6b6b7e4e6096fa6` |

- **The valid-cell count reproduces AGUv3 exactly.** AGUv3's k=2 table reports 1144 + 2420 = 3564 cells; the inherited fixture yields 3564. This is why the legacy reproduction can be held to an *exact* tolerance on every CHIRPS-only quantity (`f:1`, `r:1`).
- **The valid-cell mask is recomputed inside every training fold**, from that fold's training years only, so it is fold-dependent and every weight in §10 is normalised per fold. The full-record mask (3564) is used only by the legacy reproduction, which reproduces AGUv3's full-record procedure.

### 1.2 Sea-surface temperature

| item | value |
|---|---|
| product | NOAA ERSST v5 monthly, 2°, via `rosetta.fetch(product="sst/ersst-v5", variable="sst")` |
| upstream source | `https://www.ncei.noaa.gov/pub/data/cmb/ersst/v5/netcdf/ersst.v5.{YYYY}{MM}.nc`, one NetCDF per month |
| requested belt | 40°S–40°N, 0–360°E (the AGUv0 belt; contains every index box in §7) |
| record | 1981–2023 |
| native units | `degree_C`, passed through unconverted (`units: C`, `target_units: C`) |
| native shape | `(time, lev, lat, lon)`; the size-1 `lev` dimension is squeezed by the fixture builder, matching AGUv3's `squeeze("zlev")` |
| longitude convention | 0–360 natively; asserted at load, not assumed |
| realised grid | lat 40°S–40°N (n=41), lon 0–358°E (n=180), step 2°; 516 months, none incomplete; 75.93% finite (the rest is land) |
| fixture file | `data/ersst_v5_monthly.nc` |
| fixture bytes | 15,246,450 |
| fixture sha256 | `a9c91583b92e71d24362cf092a038d947c8fd7764cf1c0c2846fbb81c6042916` |
| builder | `src/fetch_ersst.py`, run `r:5`; provenance at `outputs/ersst_provenance.json` |
| rosetta git sha | `f3ef32d986a9de29d36d1d164dce78c284a180f9` (**working tree dirty — see §20.1**) |
| rosetta catalog sha256 | `bd683de05c7218627b366c4971b3239bc7e52548283f777695ea465c00f9132e` |

- **`sst/ersst-v5` was restored to rosetta's catalog as a minimal additive change** (§20.1). It is the product name rosetta's own integration tests already expect, and all three of those tests pass against it.
- **The fixture is sanity-checked as an ocean index, not just as bytes.** Niño-3.4 built from it ranks 2016, 1998 and 1983 as the three warmest DJF seasons and 1989, 2000 and 2008 as the three coldest — the canonical super-El-Niños and La Niñas of the record. Verified in `probes/spec_check.py`.
- **ERSST v5's monthly files do not share a time encoding, and the fixture builder verifies rather than assumes.** 324 of the 516 files declare `minutes since <that month>` on a **360_day** calendar and decode to day 1; the remaining 192 declare `days since 1854-01-15` on a **gregorian** calendar and decode to day 15. Concatenated naively the axis mixes `cftime.Datetime360Day` with `pandas.Timestamp` and cannot even be differenced. Both encodings identify the correct (year, month), so `src/fetch_ersst.py` rebuilds the axis at the first of each month and then **refuses to write** unless the sequence is exactly 1981-01 … 2023-12, strictly increasing, without gaps or duplicates.
- **No scored run touches the network.** `src/fetch_ersst.py` and `src/fetch_fixtures.py` write the fixtures once; everything downstream reads local NetCDF.
- **Fetching ERSST on this machine requires an IPv4 preference, which lives in v3rx and not in rosetta.** This host's IPv6 route to `www.ncei.noaa.gov` is dead, and `urllib` has no Happy-Eyeballs fallback the way `curl` does: one 168 KB monthly file takes 0.85 s over IPv4 and ~180 s when IPv6 is tried first. `src/fetch_ersst.py` filters `socket.getaddrinfo` to `AF_INET` for its own process. This is a property of this network, not of the product, so rosetta's adapter is left alone.

---

## 2. The environment is pinned to the `pycpt` conda environment

| package | version |
|---|---|
| python | 3.12.7 (`/opt/homebrew/Caskroom/miniforge/base/envs/pycpt/bin/python`) |
| numpy | 2.1.2 |
| xarray | 2026.7.0 |
| scipy | 1.14.1 |
| scikit-learn | 1.9.0 |
| netCDF4 | 1.7.2 |
| matplotlib | 3.9.2 |
| cartopy | 0.24.0 |
| rosetta | local editable checkout, `~/Developer/ACCORD/rosetta`, branch `feat/region-helper-and-cds-guard` |
| deepscale | local editable checkout, `~/Developer/ACCORD/deepscale`, branch `feat/index-ergonomics-and-registry` |
| platform | macOS 26.5.1, x86_64 |

**Both library checkouts are dirty, so neither a git sha nor a dirty-file count identifies the code that ran.** A sha ignores uncommitted edits entirely, and a count is unchanged by editing a line inside an already-modified file. Both are therefore rejected as drift detectors. What is pinned instead is **content**:

| library | HEAD | source files hashed | `tree_sha256` | `diff_sha256` |
|---|---|---:|---|---|
| rosetta | `f3ef32d986a9de29d36d1d164dce78c284a180f9` | 23 under `src/` | `eaf3e99ba5339af25ec93704247c3c871aa119eae2d0dac07b0cf305ecb60e3f` | `4352516999e804e4d51453fb1469c58fa1c3d1001cf40c915238e39191bc2f0c` |
| deepscale | `c0452442fae052bba2d1dd7177eac83f11781dae` | 56 under `src/` | `29d3d83e47b94515e33d5ed5fff3983ecd6bb6446f3c09d70c82cd4e8a5c04d0` | `acceb96c7491a3e3a7d1eb7a3b72e357b9fc9b543e363a6cf47978615ffcdef0` |

- **`tree_sha256` is a hash over the sorted `(relative path, file sha256)` manifest of every source file under `src/`**, tracked or untracked, excluding `__pycache__` and compiled artefacts. One scalar therefore detects any edit, addition or deletion anywhere in the library's source. The per-file map is stored in full — 79 files across the two libraries — so a mismatch localises to the exact file.
- **`diff_sha256` hashes `git diff HEAD` over the whole repository**, which additionally catches edits outside `src/`.
- **The uncommitted diffs themselves are deliberately not copied into this project.** The instruction on the rosetta checkout was not to absorb its unrelated work in progress, and the per-file hash map detects drift precisely without duplicating anyone's WIP. The one library change this project depends on is preserved separately at `legacy/patches/rosetta-ersst-v5.patch`.
- **`outputs/env.json` holds all of it and exists** — written by `src/record_env.py` (`r:10`), 12,067 bytes. It is split into `asserted`, which contains only content hashes, and `recorded`, which contains provenance that legitimately varies (write timestamp, interpreter path, package versions) and is never asserted.
- **`probes/spec_check.py` re-asserts every hash in `asserted` against the live trees on every run**, and every production run will do the same before it computes anything. A mismatch aborts rather than silently re-defining a locked benchmark.
- **What this still cannot do is reconstruct the environment from git alone**, because the changes are uncommitted upstream. Drift is now detectable to the byte and localisable to the file; reproduction on another machine would need those branches merged. The limitation is carried into §18.9.
- **All research code runs as `conda run -n pycpt python ...` inside `rx run exec` or `rx run benchmark`.** No research command is issued through raw Bash.

---

## 3. The outer folds and the inner folds are fixed

- **The outer protocol is walk-forward with 6 folds, inherited unchanged from `bench.make_folds`.** On the 43-year record it gives:

| fold | train years | n train | test years | n test |
|---|---|---:|---|---:|
| 0 | 1981–2001 | 21 | 2002–2004 | 3 |
| 1 | 1981–2004 | 24 | 2005–2008 | 4 |
| 2 | 1981–2008 | 28 | 2009–2012 | 4 |
| 3 | 1981–2012 | 32 | 2013–2015 | 3 |
| 4 | 1981–2015 | 35 | 2016–2019 | 4 |
| 5 | 1981–2019 | 39 | 2020–2023 | 4 |
|  |  |  | **total** | **22** |

- **Walk-forward is the primary protocol because the atlas is an operational product.** A zone map fitted partly on future years is not something a forecast centre could have issued.
- **K-fold with 6 folds is reported alongside walk-forward for every real (non-permuted) result** — contiguous blocks of 8,7,7,7,7,7 years, all 43 scored. **Permutation nulls run under walk-forward only**, which is what makes the budget in §15 come out at its stated size. The k-fold column never adjudicates a claim.
- **Fold 0 trains its discovery on 21 years.** This is a genuine weakness of the procedure and is reported per fold rather than dropped.
- **The inner protocol is leave-one-year-out (LOYO) over the training years of the outer fold.** It selects predictor and lead, and it supplies the forecast spread. It never sees an outer test year.
- **Per-window year coverage is trimmed once per window, not per cell.** A season-year whose deepest predictor window (max lead + width 2) falls before the SST record starts is dropped for that window, for every zone, so every candidate in that window sees an identical sample. This is `probes/grid_sweep.precompute`'s existing rule, inherited rather than rederived.

---

## 4. Zone discovery is specified completely, and runs inside the training fold

Zone discovery uses **rainfall only**. No SST, no coordinates, no country boundaries, no expert region enters the clustering.

**Input.** The 0.25° coarsened monthly precipitation field, restricted to the training years of the outer fold.

**Valid-cell mask.** A cell is valid when its 12-month climatology over the training years is finite in every month and its annual total exceeds 1e-3. Recomputed per fold.

**Feature block 1 — the standardised climatological cycle shape.**
- The 12-month mean climatology per cell over the training years.
- `X1 = (C - C.mean(1)) / (C.std(1) + 1e-6)` — timing and shape, deliberately not amount.

**Feature block 2 — loadings on the leading five EOFs of monthly anomalies.**
- `anom = da.groupby("time.month") - da.groupby("time.month").mean("time")` over the training years.
- `A = nan_to_num(A / (A.std(1) + 1e-6))`, then `U, S, _ = svd(A, full_matrices=False)`, keep `X2 = U[:, :5]`.
- Interannual co-variability, so two cells with the same seasonal shape but decoupled year-to-year behaviour separate.

**Block weighting.** Standardise each column of each block to unit variance, then scale block *b* by `1/sqrt(n_columns_b)`: `X = hstack([z(X1)/sqrt(12), z(X2)/sqrt(5)])`. Total dimension 17.

**Clustering.** `sklearn.cluster.KMeans(n_clusters=k, n_init=10, random_state=0)` for k = 2…8.

**k selection — the pre-specified stability rule.**
- For each k: cluster the full training data for reference labels `L0`.
- Draw 20 year-bootstrap resamples of the training years (`numpy.random.default_rng(0)`, `choice(years, size=len(years), replace=True)`), rebuild both feature blocks from each resample, recluster with `random_state = b+1`, and take the adjusted Rand index against `L0`.
- **Select the largest k in 2…8 whose mean bootstrap ARI is at least τ = 0.90. If no k reaches τ, select `argmax` ARI.**
- **τ = 0.90 is fixed here and never revisited.** It carries prior methodological provenance: AGUv3's own `hierarchy.py` uses "≥ 0.9 bootstrap ARI" as its stability bar, so this rule invents no new threshold. What it changes is the *direction* of the tie-break — largest qualifying k rather than most stable k — which removes the coarseness bias AGUv3 documents in its own README. On AGUv3's published curve (0.949, 0.901, 0.723, 0.580, 0.693, 0.569, 0.662 for k = 2…8) it selects **k = 3**.
- **The complete k = 2…8 hierarchy is reported for every fold and every arm, regardless of which k is selected** — mean ARI, its standard deviation, the silhouette, the cell counts, the centroids, the discovered windows and the zone map at each level. Selection determines what the atlas benchmark scores; it never determines what is shown.

**Deterministic labelling.** Zones are relabelled west→east by centroid longitude, as AGUv3 does. This is cosmetic; §11 uses Hungarian matching for cross-fold alignment, not this ordering.

**What is fitted on training years only:** the valid-cell mask, both feature blocks, the column standardisation, the EOF basis, the bootstrap ARI curve, the selected k and the k-means centroids. The resulting cell→zone map is applied unchanged to the test years.

---

## 5. The rainy-season detector is fixed and bimodal-aware

Applied to each zone's area-weighted mean annual cycle in **mm/month** (the 12-month climatology multiplied by `DAYS_PER_MONTH = [31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]`), over the training years of the fold.

**Peak detection** (AGUv3 `peak_months`, unchanged): month *i* is a peak when `cyc[i] >= cyc[i-1]` and `cyc[i] >= cyc[i+1]` (circular) and `cyc[i] > 0.15 * cyc.max()`.

**Window construction** (AGUv3 `windows_for`, unchanged): for each peak *p*, the 3-month window with the largest total among starts `{p-2, p-1, p}` that contains *p*.

**Three additions, fixed here because AGUv3's code leaves them undefined:**
- **Plateau handling.** `>=` on both sides makes a flat pair yield two adjacent peaks. After detection, circularly adjacent peaks are merged keeping the higher month; exact ties keep the earlier month. Windows identical after construction are de-duplicated.
- **Year-wrap-safe season labelling.** A window whose months wrap the calendar boundary (e.g. NDJ) is labelled by the year of its **last** month, matching `bench.build_target` and `bench.Context`. AGUv3 does not do this — its `groupby("time.year").sum()` adds November and December of year Y to January of year Y, which is not a season. This is a **legacy defect**, reproduced verbatim in the legacy reproduction (§9.1) and corrected everywhere else. Its magnitude is reported.
- **A cap of two windows per zone.** If more than two peaks survive merging, the two with the largest 3-month totals are kept. This bounds the weight bookkeeping of §10 and is fixed before any skill is computed.

---

## 6. Discovery is a function of the training years alone — the invariance that §14 depends on

Stated here once, because three later sections rely on it:

- Everything in §4 and §5 — mask, features, EOF basis, ARI curve, k, partition, annual cycles, windows — is computed from the training years of the outer fold and from nothing else.
- Nothing in §4 or §5 reads SST, test-year rainfall, or any conditional mask.
- Therefore, for a fixed (fold, permutation), discovery is identical across the three condition families of §8. §14 uses this.

---

## 7. The five predictors, the four leads, and their leak status are specified completely

**Index boxes** (AGUv1 `indices.py`, unchanged; lat_s, lat_n, lon_w, lon_e in 0–360 longitude):

| box | bounds |
|---|---|
| `nino34` | −5, 5, 190, 240 |
| `iod_w` | −10, 10, 50, 70 |
| `iod_e` | −10, 0, 90, 110 |
| `wpac` | −5, 5, 130, 150 |
| `wv` | 5, 20, 130, 170 |

Each box value is the `cos(lat)`-weighted area mean of the monthly SST anomaly over the box, against a fixed 1991–2020 per-calendar-month base (`bench.CLIM_BASE`).

**Index definitions** (AGUv3 `search.make_index`, unchanged):

| index | definition | contains a fitted constant? |
|---|---|---|
| Niño-3.4 | `nino34` | no |
| IOD | `iod_w − iod_e` | no (difference of like units) |
| WPG | `z(wpac) − z(nino34)` | **yes — two means and two standard deviations** |
| WVG | `z(nino34) − z(wv)` | **yes — two means and two standard deviations** |
| IWHG | `12 + 323·IOD − 193·wpac + 94·nino34` | no (published fixed coefficients) |

**Leads.** L ∈ {0, 1, 2, 3}. The predictor is the 2-month mean ending L+1 months before the target window starts. This is AGUv3's convention and it is *identical* to the inherited `bench.Context.preseason(box, year, gap=L, width=2)`; the equivalence is asserted by a test, not assumed.

**Averaging width is fixed at 2 months** and is not a search axis, because AGUv3's recipe space is width 2 and adding the axis would change what the legacy reproduction reproduces.

**The fixed 1991–2020 anomaly base is provably not a leak, which is why the inherited `bench.load_sst` is used unchanged.** Subtracting a per-calendar-month constant shifts each box series by a quantity that does not vary across years. For Niño-3.4, IOD and IWHG the model is a per-fold refitted linear regression and a constant predictor shift is absorbed exactly by the refitted intercept. For WPG and WVG the per-fold `z(·)` removes both mean and scale, so the base cancels. No index's year-to-year structure depends on the base, and no test-year value reaches a train-fitted quantity through it.

**WPG and WVG carry the one leak this project measures directly.** Fitting their standardisation on the full record lets test-year SST set the mean and scale of a training-time predictor. v4zeek's verification gate caught this (`f:6`). §9 turns it into a controlled one-variable comparison.

---

## 8. The conditional families and their thresholds are specified completely

| family | which test years are scored |
|---|---|
| MAM / all years | every test year |
| MAM / La Niña | test years where `nino34(gap 0, width 2) < mean_train − 0.5 · sd_train` |
| MAM / negative WVG | test years where `WVG(gap 0, width 2) < 33.33rd percentile of the training values` |

- **Thresholds are fitted on training years only**, and the conditioning predictor is fixed at gap 0, width 2 for every cell regardless of that cell's own lead, so conditioning is not a second searchable knob. These are `grid_sweep.condition_mask`'s exact definitions, inherited unchanged.
- **The selector is unconditional.** Predictor and lead are chosen by inner LOYO over *all* training years; conditioning applies at evaluation only. Fixed here because it is what lets the three families share one discovery-and-selection pass (§14) and because it prevents the condition becoming a selection axis.
- **MAM is evaluated for every zone, whether or not the detector discovered it.** The question "is MAM conditionally predictable" must not be answerable only where the detector happened to find MAM. Whether each zone discovered MAM is reported alongside.
- **MAM is not required to beat OND.** Each family is judged against its own full-pipeline permutation null and nothing else.
- **Coverage failures are handled by §12, not by silent dropping.**

---

## 9. Three distinct objects separate legacy reproduction from leakage measurement

The previous revision conflated them: a full-record legacy procedure has no training years, so an arm that "differs only in using training years" cannot exist. Replaced by three objects.

### 9.1 Legacy reproduction — a provenance check, not part of any subtraction

- Reproduces AGUv3's `zones.py`, `hierarchy.py`, `wvg_by_zone.py` and `search.py` exactly: the same CHIRPS and ERSST fixtures, the same index boxes, the same years (1981–2023 for the zonation, 1982–2023 for the tensor), the same seeds (`default_rng(0)` for the bootstrap and for the 1000 permutations; `random_state=0` for k-means).
- Retains **all** of AGUv3's full-record behaviour: full-record WPG/WVG standardisation, full-record predictand z-scoring, full-record quantile thresholds, full-record La Niña threshold, full-record zonation, the 1991–2020 climatology window, max-ARI k selection, and the NDJ labelling defect of §5.
- **It has no train/test split and produces no out-of-sample number.** Its only job is to establish that this codebase computes what AGUv3 computed. It is **not** an operand in the leakage subtraction.
- Reproduction targets, from `legacy/AGUv3/outputs/tables/`:

| quantity | target |
|---|---|
| k selected by max-ARI | 2 |
| ARI curve, k = 2…8 | 0.949, 0.901, 0.723, 0.580, 0.693, 0.569, 0.662 |
| silhouette, k = 2…8 | 0.323, 0.315, 0.322, 0.348, 0.346, 0.322, 0.330 |
| k=2 cell counts | 1144, 2420 |
| k=3 cell counts | 877, 1112, 1575 |
| k=4 cell counts | 450, 847, 731, 1536 |
| k=4 centroids | (8.9N, 35.3E), (−0.4N, 37.0E), (7.1N, 38.7E), (5.3N, 44.0E) |
| k=4 discovered windows | z0 JJA; z1 MAM+NDJ; z2 MJJ+JAS; z3 MAM+SON |
| orientation η² at k=4 | Kenya 0.523 lon / 0.120 lat; Somalia 0.101 lon / 0.212 lat |
| tensor size | 520 cells (13 zone-windows × 5 indices × 4 leads × 2 modes) |
| tensor survivors at BH α=0.10 | 79 |
| eastern zone MAM conditional rates | P(dry \| −WVG) = 0.79, P(dry \| −WVG ∧ La Niña) = 0.77, n = 13 |
| best surviving recipe per zone-window | z1/NDJ iod L0; z1/OND iod L0; z2/JAS wpg L0; z2/OND iwhg L0; z3/SON nino34 L0; z3/OND nino34 L0; z2/MJJ iod L3 |

- **Tolerances are two-tier, because only the CHIRPS fixture is byte-verified against the legacy run.**
  - **Tier 1, CHIRPS-only — exact.** Zone labels agree cell-for-cell (ARI = 1.000 against a stored reference label vector); cell counts exact; centroids within 0.05°; ARI and silhouette within 0.005; discovered window month-sets exactly equal; η² within 0.005.
  - **Tier 2, CHIRPS+ERSST — strict but not exact.** `sym_corr`, `dry_roc` and every `p_dry_*` within 0.01 (published to 2 dp); tensor `stat` within 0.01; survivor count 79 ± 3; and **all 7 "best surviving config per zone-window" rows select the identical (index, lead, mode)**.
- **A Tier 1 failure stops the project.** A Tier 2 failure stops it pending an ERSST fixture investigation, and the investigation is reported whatever it finds.

### 9.2 The leaky out-of-sample arm

- The full §3–§8 out-of-sample procedure — outer walk-forward folds, train-fitted zonation, train-fitted windows, train-fitted selection, train-fitted regression, train-fitted tercile edges, train-fitted conditional thresholds — with **one deviation**: WPG and WVG are standardised over the full record.
- Scored by the primary atlas benchmark of §10.

### 9.3 The clean out-of-sample arm

- Byte-identical to §9.2 except that WPG and WVG are standardised on the training years of each fold (`grid_sweep.compose`, inherited unchanged).

### 9.4 What the subtraction means, and what it does not

- **The measured normalisation leak is `RPSS(clean) − RPSS(leaky)`**, computed on the primary atlas benchmark and on every secondary benchmark, and reported per zone-window as well as pooled. The two arms differ in exactly one variable, so the difference is attributable.
- **The legacy reproduction is not an operand.** It is reported separately as provenance.
- **The leak can only bite where it applies.** The number of zone-windows whose selected index is WPG or WVG, and the number of test years whose `neg_wvg` membership changes between the arms, are both reported; a small difference with few affected cells means something different from a small difference with many.
- **AGUv3 carries six leaks; this subtraction isolates one.** The full accounting, stated so the report cannot overclaim:

| # | leak in AGUv3 | where it is addressed |
|---|---|---|
| 1 | WPG/WVG standardised on the full record | **§9.3 − §9.2, the controlled subtraction** |
| 2 | Predictand z-scored on the full record, so `dry = y < 0` uses a full-record median | the OOS procedure (§10) |
| 3 | `strong = dry_score > quantile(dry_score, 2/3)` uses a full-record quantile | the OOS procedure |
| 4 | La Niña threshold `z(n34) < −0.5` uses full-record z | the OOS procedure (§8) |
| 5 | The zonation itself is fitted on the full record | the OOS procedure (§4) |
| 6 | No out-of-sample split at all; LOYO refits only the regression line | the OOS procedure (§3) |

- **Leaks 2–6 are not individually decomposed**, and the report says so. What is reported is the qualitative descent from the legacy numbers to the clean out-of-sample numbers, labelled as the combined effect of all six plus the change of estimand.

---

## 10. The primary benchmark scores the complete zonal product

**What it measures.** The utility of the complete forecast atlas over the fixed geographic domain of §1. Discovered zones are **forecast units**, not internal modelling partitions.

**The procedure, per outer fold.**
1. Discover the partition of all valid land cells from the training years' rainfall only (§4).
2. Discover each zone's rainy-season windows from the training years only (§5).
3. For each zone-window, search 5 indices × 4 leads by inner LOYO on the training years, selecting on mean squared error of the LOYO prediction (v4zeek's `search_zones` criterion, inherited).
4. Fit the regression, the residual spread and the tercile boundaries on the training years.
5. Apply the train-discovered masks, windows and recipes to the held-out years.
6. **Forecast every discovered zone-window.** No zone or season is dropped because it scored badly.

**The forecast for one zone-window-test-year.**
- Aggregate rainfall over the train-discovered zone mask, `cos(lat)`-weighted, summed over the window's months in mm.
- Regress that series on the standardised selected index over training years; predict the test year; spread is the standard deviation of the inner-LOYO residuals.
- Convert to below/near/above probabilities through a Gaussian predictive distribution against the **train-fitted** tercile boundaries (`deepscale.metrics.rpss._cpt_boundaries` on the training years).
- Compute RPS of the forecast and RPS of the equal-thirds climatology through the inherited `rpss_oos` metric.

**The pooling rule — every valid cell contributes exactly once.**
- For fold *f*, zone *z*, window *m*: `A(f,z)` is the sum of `cos(lat)` over the zone's cells, `A_total(f)` the sum over all cells valid in that fold, `W(f,z)` the number of windows zone *z* discovered (1 or 2).
- `ω(f,z,m) = A(f,z) / A_total(f) / W(f,z)`, so `Σ_{z,m} ω(f,z,m) = 1` for every fold.
- **Bimodal zones split their weight equally across their two windows.** Fixed in advance: the zone's annual forecast utility is shared between its rainy seasons, and equal split stops the detector's window count from inflating or deflating a zone's contribution.
- **A rainfall-share alternative is pre-registered as a reported variant, not chosen after the fact:** `ω_rain(f,z,m) = A(f,z)/A_total(f) × (window mm / that zone's total window mm)`. Both are always reported; equal split is primary.

**The single procedure-level score.**

```
RPSS_atlas = 1 − Σ_f Σ_{z,m} ω(f,z,m) Σ_{t∈test(f)} RPS_forecast(z,m,t)
                 ────────────────────────────────────────────────────
                 Σ_f Σ_{z,m} ω(f,z,m) Σ_{t∈test(f)} RPS_climatology(z,m,t)
```

- Losses are pooled, never averaged as ratios of ratios. Each fold contributes in proportion to its number of test years.

**Aggregate scoring is fold-local and matching-independent, and this is a hard requirement.**
- The indices `z` and `m` above range over the zones and windows *fold `f` itself discovered*. Nothing in the formula asks whether fold `f`'s zone 2 is "the same zone" as fold `g`'s zone 2. There is no correspondence to establish, so §11's Hungarian matching, its reference frame, its tracks and its orphans **have no effect on any score in this section, in §13, or in §14**.
- The weights `ω(f,z,m)` are computed inside fold `f` from fold `f`'s own valid-cell mask and sum to 1 within that fold. Cross-fold pooling is a sum of already-fold-normalised weighted losses.
- **Every forecast the atlas issues enters the pooled sums. There is no minimum-year threshold on the aggregate**, no exclusion and no renormalisation. A zone-window whose condition leaves it one scored test year contributes that one year's loss to both the numerator and the denominator. `MIN_SCORED` applies only to the descriptive per-track results of §11 — see §12.
- The consequence is deliberate: **the aggregate is a property of the atlas, and the matching is a property of the analyst.** If §11's reference frame were changed tomorrow, not one number in §10 would move.

### 10.6 The decision rule for the primary claim

The claim "the discovered atlas is useful" is adjudicated here and nowhere else.

- **The object scored is the complete discovered-window atlas** — every zone, every window the detector found, under the `zones-specific` arm. Not the MAM subset, not a season chosen afterwards.
- **The null is the same 1,200 permutation runs of §14.** Each of the 200 paired replicates already re-runs discovery for all 6 folds; scoring the complete atlas from those runs is an additional *scoring* pass over work that is already being done. **It adds no discovery runs.**
- Each replicate yields one pooled `RPSS_atlas` across its 6 folds, giving a null of 200 values.
- **One-sided p = (1 + #{null ≥ real}) / 201.**
- **The atlas is declared USEFUL if and only if `RPSS_atlas > 0` AND `p ≤ 0.05`.** Both conditions, fixed here, evaluated on the primary walk-forward protocol.
- **Why both conditions.** A positive RPSS alone is not evidence, because a procedure that searches zones, k values, windows, indices and leads produces a positive best number on noise with high probability — that is the failure mode the whole v4zeek line of work exists to avoid. A small p alone is not usefulness either: a procedure can be reliably distinguishable from its own null while still forecasting worse than climatology. The claim needs both.
- **The k-fold column does not adjudicate.** It is reported alongside, as everywhere else.
- **Two secondary decisions are pre-specified here because they are free from the same 200 replicates**, and neither may be substituted for the primary one:
  - **`zones-specific` versus `pooled`.** Both are scored on the same permutations, so the paired difference `RPSS(zones-specific) − RPSS(pooled)` has its own paired null. Reported with a one-sided p by the same formula. This is the "does discovering the partition buy anything as a product" question.
  - **`zones-specific` versus `zones-shared`.** Same construction. This is the "does zone-specific recipe selection buy anything over one shared recipe" question.
- **Arm cost, stated so the budget claim is honest.** `zones-shared` shares its discovery with `zones-specific` and differs only in selection, so it costs scoring only. `pooled` is k = 1: it needs no k-means and no bootstrap ARI curve, only window detection on a single annual cycle, which is a small fraction of a discovery run. `climatology` needs no discovery and its null is definitionally zero. So the three comparison arms ride on the same 1,200 runs, and §15's budget already covers them.

**The four compared arms, all scored by the identical rule over the identical domain.**

| arm | what it is |
|---|---|
| `climatology` | equal thirds for every zone-window-year. **Must score 0.0000.** Harness gate. |
| `pooled` | k = 1: the whole valid domain is one zone, with its own discovered windows and one recipe. |
| `zones-shared` | discovered zones, one (index, lead) chosen once for all zones by pooled inner LOYO, applied per zone. |
| `zones-specific` | discovered zones with zone-specific index and lead. The headline arm. |

**What RPSS_atlas compares, stated explicitly.**
- **It compares complete forecast products, not identical predictands.** The four arms discover different partitions, and therefore different numbers and identities of forecast windows. A unimodal pooled arm may issue one seasonal forecast covering the whole domain; a k=5 bimodal atlas may issue nine. They are not forecasting the same random variable, and the score is not a paired comparison of the same predictand.
- **What is held identical across arms** is the thing the question is about:
  - the geographic domain, and the fact that every valid cell carries weight exactly once;
  - the total spatial weight per fold, which is 1 for every arm;
  - the two-window cap of §5;
  - that **every issued window is scored**, with no window removed for scoring badly;
  - the fold split, the tercile convention, the climatology reference and the metric.
- **Limitation, recorded in advance and repeated in the report:** a difference between arms can reflect *both* the quality of the zonation *and* the forecast opportunities each atlas generates. An atlas that discovers a second rainy season in a large zone is scored on that second season, and that changes the score whether or not the zonation is better. This benchmark deliberately measures the product, so this is a property of the question rather than a defect — but it means the primary comparison is **not** a controlled test of zonation alone. **Secondary benchmark A (§13) is the controlled test**, because it holds the predictand fixed.

**Reporting.** Every zone-window is reported separately: RPSS, scored-year count, weight, selected index and lead, and the fold it came from. The aggregate never hides a failed zone.

**Registration.** `atlas-wf-v1` (walk-forward, primary) and `atlas-kf-v1` (k-fold, reported alongside). Metric `rpss_atlas`, direction `max`. Locked: `harness/atlas_bench.py`, `bench.py`, `batched.py`, and the two fixture files.

---

## 11. Cross-fold matching is defined, including when folds select different k

Hungarian matching aligns only `min(k_a, k_b)` zones. Everything below is fixed here rather than left to implementation.

**Nothing in this section reaches any score.** Matching, the reference frame, tracks, orphans and `MIN_SCORED` exist to describe how the discovered objects behave across folds. The aggregate atlas score of §10, the secondary benchmarks of §13 and the permutation nulls of §14 are all fold-local and never consult a track identity. This was violated in revision 2, where the coverage rule pooled by track; §12 now fixes it.

**The reference frame.**
- **R is the partition discovered on fold 5's training years, 1981–2019, with the k selected there.**
- Walk-forward training sets are nested, so fold 5's training set is the superset of every other fold's, which makes it the most reliable frame available. It excludes 2020–2023, so the reference frame never sees fold 5's own test years.
- R is used **only** for descriptive stability bookkeeping. No forecast, no selection and no score depends on it.

**Matching.**
- For each fold *f*, build the cell-overlap matrix between fold *f*'s zones and R's zones over cells valid in both, and solve `scipy.optimize.linear_sum_assignment` maximising total overlap. Deterministic.
- Matching is **one-to-one by construction**. **Tracks therefore never split and never merge.** Each fold contributes at most one zone to each track, and each of that fold's zones belongs to at most one track.

**Tracks, orphans and absences.**
- **A track** is one reference zone plus its matched zone in every fold where a match exists. Tracks are indexed by reference zone, so there are exactly `k_R` tracks.
- **When `k_f > k_R`, the unmatched zones of fold *f* are orphans.** They are retained, labelled `f{f}-orphan{j}`, and reported individually in every table with their cell count, centroid, windows, selected recipe, weight and skill. They are never dropped and never merged into a track.
- **When `k_f < k_R`, the unmatched reference zones are absences** for fold *f*. The track records an absence for that fold.
- **Two fold-level stability metrics come straight out of this and are reported as first-class numbers:**
  - `orphan_area(f)` = the fraction of fold *f*'s valid area sitting in orphan zones;
  - `absence_rate(f)` = the fraction of reference zones with no match in fold *f*.

**How each stability metric handles the three cases.**

| metric | folds used | orphans | absences |
|---|---|---|---|
| pairwise ARI (fold *a* vs fold *b*) | all 6, all 15 pairs | included — ARI needs no matching | n/a |
| per-cell switch frequency map | all 6 | included | n/a |
| selected k per fold, full k=2…8 hierarchy | all 6 | n/a | n/a |
| track centroid variation | the folds where the track has a match | excluded (reported separately) | skipped |
| track boundary variation | the folds where the track has a match | excluded (reported separately) | skipped |
| track window agreement | the folds where the track has a match | excluded (reported separately) | skipped |
| track predictor-identity and predictor-region agreement | the folds where the track has a match | excluded (reported separately) | skipped |
| track lead agreement | the folds where the track has a match | excluded (reported separately) | skipped |
| `orphan_area`, `absence_rate` | all 6 | this *is* the metric | this *is* the metric |

- **The matching-free metrics carry the headline stability claim**, so the story never rests on the choice of reference frame. Mean pairwise ARI over the 15 fold pairs and the per-cell switch map are computed without any matching at all.

**Minimum fold coverage, and the two thresholds that are easy to confuse.**
- **A track enters the H1 test only if it has a match in at least 4 of the 6 folds.** Fixed in advance. Tracks below that bar are reported in full — every metric, every fold — and the number excluded is stated.
- **`MIN_SCORED = 8` is a different bar for a different object.** It gates whether a track's *pooled skill* is reported as a per-track number (§12). A track can clear the 4-fold bar and fail the 8-year bar, or the reverse. Both are reported.
- **Neither bar touches the aggregate atlas score.** See §10 and §12.

**Predictor-region groups** (fixed): `{nino34}` Pacific-ENSO, `{iod}` Indian-dipole, `{wpg, wvg}` Pacific-gradient, `{iwhg}` composite.

**The preregistered hypothesis.**
- **H1: cross-fold stability predicts held-out zonal skill.**
- Test statistic: Spearman ρ between each qualifying track's mean pairwise aligned-label agreement and its pooled held-out RPSS.
- One-sided, ρ > 0, α = 0.05.
- **The null is built by exact enumeration when tractable.** Let *n* be the number of qualifying tracks. Enumerate all distinct permutations of the stability-score vector — `n!` divided by the product of the factorials of any tied-score multiplicities — whenever that count is ≤ 200,000, which covers *n* ≤ 8 (8! = 40,320; 9! = 362,880). Otherwise draw 10,000 Monte Carlo permutations with `default_rng(1)`.
- The report states which null was used, the exact denominator, and *n*.
- **Orphan zones are excluded from H1** because they have no cross-fold agreement to score. Their weight and their skill are reported separately.
- **If `orphan_area(f)` exceeds 0.20 in any fold, H1's result is reported as unreliable.** Fixed in advance, because a large orphan fraction means the track structure does not describe the atlas.
- **n will be small — plausibly 3 to 8 — and the power is low.** This is stated in the report whatever the outcome. H1 is a hypothesis, not an assumption; a null result is reported as a null result.

**Expert overlap is descriptive only.** The AGUv2 hand-drawn eastern-Horn box (38–50.5°E, 4.5°S–8.5°N), the reviewer's south-central Somalia box (42–48°E, 1–6°N), the ~38°E Kenya split and the ~7°N Somalia split are reported as overlap fractions and η² statistics. **They are not ground truth and they determine nothing.**

---

## 12. Coverage is fold-local; MIN_SCORED gates only the descriptive per-track tables

Two different objects are at stake and revision 2 conflated them. They are separated here.

### 12.1 The aggregate atlas score has no minimum-year threshold at all

- Within fold *f*, every discovered `(zone, window)` that issues at least one scored forecast contributes its losses to the pooled numerator and denominator of §10, weighted by `ω(f,z,m)`.
- **No zone-window is excluded for having few scored years. No weight is renormalised. No track identity is consulted.** The aggregate is exactly what the atlas produced in that fold.
- A `(zone, window)` for which a condition leaves **zero** test years in fold *f* contributes nothing, because there is no loss to contribute. That is an empty set, not an exclusion rule, and it is reported as coverage rather than hidden.
- **Fold-local coverage, reported next to every score and never suppressed:**

```
coverage(c) = (1/6) Σ_f  Σ_{(z,m) with ≥1 scored test year in family c}  ω(f,z,m)
```

  Each inner sum is over fold *f*'s own discovered zone-windows and its own weights, so `coverage` is matching-independent. For the complete-atlas family it is 1 by construction whenever every discovered zone-window is forecast, which §10 requires. For the conditional families it will be below 1, and by how much is a result.
- **A family with `coverage < 0.5` is reported as UNAVAILABLE for a headline claim.** Its RPSS, its coverage and its null are all still printed; it is simply not adjudicated pass/fail. Fixed in advance.

### 12.2 MIN_SCORED = 8 gates the descriptive per-track skill numbers only

- **The object it gates** is a *track's pooled skill*: one zone track's losses summed over the folds where that track has a match. This is the number §11's H1 correlates against stability, and the number the per-track table reports.
- **The bar is 8 pooled test years across folds, never per fold.** A single walk-forward fold offers 3 or 4 test years, so a per-fold bar would empty every table.
- **A track or orphan below the bar is retained as an explicit unscored failure.** It appears in the per-track table with `scored_years = n` and `status = unscored (n < 8)`, together with its weight, its selected recipe and its fold membership. It is never omitted and its weight is never redistributed.
- **A track below the bar is excluded from H1**, because a skill estimate on fewer than 8 years is not a quantity worth correlating. The count of such exclusions is reported.
- **None of this changes a single aggregate number.** A track dropped from H1 for having 5 scored years still contributed all 5 of those years to `RPSS_atlas`.

### 12.3 Why the split matters

- The complete-atlas commitment is about the *product*: every zone the procedure discovered is forecast, and every forecast it issued is scored. §12.1 delivers that literally.
- The per-track tables are about *description*: how a recurring zone behaves across folds. A threshold there suppresses a misleadingly noisy estimate; the same threshold applied to the aggregate would silently shrink the atlas.
- Revision 2 pooled coverage by matched track, which made the headline score depend on the analyst's choice of reference frame. That is now impossible.

---

## 13. Two secondary benchmarks answer different questions and do not replace the primary one

### Secondary A — the fixed regional area-mean (the controlled test of zonation)

- The predictand is one fixed number per year: the `cos(lat)`-weighted, month-summed area mean over **all** valid cells of the 33–52°E, 5°S–12°N domain, for a fixed window.
- Discovered zones are **modelling partitions**: each zone gets its own recipe, zone predictions are combined in the continuous domain, and the aggregate is converted to tercile probabilities using inner-LOYO residual spread — v4zeek's `candidates/search_zones.py` contract, inherited.
- Fixed windows: **MAM and OND**, scored separately.
- **Because the predictand is identical across arms, this is the controlled comparison that §10 is not**, and it is the direct re-test of v4zeek's `f:19` ("partitioning the predictand does not beat pooling it out of sample") with the new discovery algorithm. Whether it agrees or disagrees, it is reported.
- Registration: `fixedmean-mam-v1`, `fixedmean-ond-v1`.

### Secondary B — the fixed gridded field

- Every candidate emits below/near/above probabilities on the common 0.25° valid-cell grid. A zonal candidate broadcasts its zone forecast to every cell in that zone; a cell whose zone discovered no window overlapping the scored window receives equal thirds.
- Scoring: RPS per cell against that cell's **own** train-fitted tercile boundaries of its own seasonal total, pooled with `cos(lat)` weights, referenced against the equal-thirds climatology — one area-weighted gridded RPSS.
- Fixed windows: **MAM and OND**, scored separately and pooled.
- Registration: `grid-mam-v1`, `grid-ond-v1`.

- **Neither secondary benchmark may be substituted for the primary result**, and the report keeps them in separate sections.

---

## 14. Permutation semantics are defined, and only provably invariant work is shared

**One replicate = one permutation π of the season-year index**, drawn from `numpy.random.default_rng(4242)` and applied identically to every cell of the rainfall field, so cross-cell correlation survives into the null. SST predictors are never permuted.

**What is re-run inside every replicate, and why.**
- The valid-cell mask, both feature blocks, the EOF basis, the bootstrap ARI curve, the selected k, the k-means partition, the per-zone annual cycle, and the discovered windows.
- **These are data-dependent discovery steps that respond to π.** The naïve argument that a joint year permutation leaves discovery unchanged holds only on the *full* record: for `A' = A P`, `A'A'^T = A A^T`, so the EOF loadings and the per-cell climatology are invariant. Inside a fold that argument fails, because the training set is a set of year *indices* and π changes which actual rainfall years land on those indices. The fold-restricted climatology and covariance therefore move, and **no discovery result is cached across replicates.**
- Predictor and lead selection, the regression fit, the residual spread, the tercile boundaries and the conditional thresholds are also re-fitted in every replicate.

**What is shared, with the proof.**
- **Every scoring family shares one discovery-and-selection pass per (fold, replicate).** Proof: by §6, discovery is a function of the training years alone. By §8, the selector is unconditional, so selection, fitting and thresholds are functions of the training years alone as well. A family changes only which forecasts and which test years enter the final pooling. Hence for a fixed (fold, π) every family consumes an identical trained atlas, and only the last step differs.
- **Budget: 6 folds × 200 permutations = 1,200 complete discovery runs, each scored four ways.**

| scoring family | what it pools | adjudicates |
|---|---|---|
| `atlas/all-windows` | every discovered zone-window, every test year | **the primary usefulness claim, §10.6** |
| `MAM/all` | zone-windows whose months are {3,4,5}, every test year | §8 |
| `MAM/lanina` | the same, La Niña test years only | §8 |
| `MAM/neg_wvg` | the same, negative-WVG test years only | §8 |

- **Adding `atlas/all-windows` added scoring, not discovery.** The 1,200 runs are unchanged; a fourth pooling pass runs over forecasts those runs already produced.
- **The 200 permutations are the same draws for every family and every arm**, which makes all family and arm comparisons **paired**. The pairing is stated wherever a comparison is reported.
- The coarsened rainfall field, the SST box series and the per-window year-coverage mask are permutation-invariant and are computed once.
- **No other sharing is permitted.** Any future cache requires a proof of the same form, written into this file as an amendment with a new benchmark version.

**What the null pays for.** Because discovery is re-run, the null pays for the zone search, the k search, the window search, the predictor search and the lead search together. It does not pay for choices fixed in this document (τ, the feature blocks, the box definitions, the pooling rule) — correctly, since those are not searched.

**Adjudication.** Every family is decided against its own null by one-sided `p = (1 + #{null ≥ real}) / 201`. The primary family `atlas/all-windows` additionally requires `RPSS_atlas > 0` (§10.6). The three MAM families are subject to the coverage rule of §12.1.

**The null is fold-local, like the score.** Each replicate re-runs discovery independently in each fold and pools by §10's fold-local rule, so no null value depends on cross-fold matching either.

---

## 15. The compute budget, the parallelism and the restart contract are design requirements

| item | budget |
|---|---|
| complete discovery runs, real | 6 folds × 4 arms × 2 leak arms = 48 |
| complete discovery runs, null | **6 folds × 200 replicates = 1,200**, each scored for **4 families** |
| family scores produced by the null | 1,200 × 4 = 4,800 |
| k-means fits per discovery run | 7 k-values × (1 reference + 20 bootstrap) = 147 |
| SVDs per discovery run | 1 + 20 bootstrap re-featurisations = 21, each on ≈3564 × (n_train × 12) |
| wall-clock ceiling | **4 CPU-hours** for the full null under `multiprocessing` over (fold, replicate) |

- **Vectorisation.** The inner LOYO selection over 5 indices × 4 leads × all zone-windows uses `batched.score_block_dynamic`, inherited unchanged.
- **Caching.** The coarsened field, the SST box series and the per-window coverage mask are memoised to `outputs/cache/`, keyed by fixture sha256.
- **Parallel execution.** `multiprocessing.Pool` over (fold, replicate) pairs. Each worker is deterministic given its key; no worker consumes a shared RNG stream.
- **Checkpointing and restartability.** Every completed `(arm, fold, replicate, family)` result is appended as one JSON line to `outputs/atlas_null.jsonl` with its key. A restart reads the file, skips completed keys and continues. Killing the runner loses at most one replicate.
- **Progress is logged every 10 replicates** with elapsed time and projected completion.

---

## 16. Numerical tolerances are fixed here

| comparison | tolerance | action on failure |
|---|---|---|
| batched scorer vs per-cell fast scorer | \|Δ RPSS\| ≤ 1e-8 | abort the sweep |
| per-cell fast scorer vs locked `bench.evaluate` | \|Δ RPSS\| ≤ 1e-8 | abort the sweep |
| atlas fast path vs atlas slow reference | \|Δ RPSS_atlas\| ≤ 1e-8 | abort the sweep |
| candidate probability rows sum to 1 | ≤ 1e-6 | reject the candidate |
| `climatology` arm RPSS | \|RPSS\| ≤ 1e-12 | abort everything; the harness is broken |
| k-means determinism on repeat | identical labels | abort; the seed is not controlling |
| Hungarian matching determinism on repeat | identical assignment | abort |
| legacy reproduction Tier 1 (CHIRPS-only) | see §9.1 | stop the project |
| legacy reproduction Tier 2 (CHIRPS+ERSST) | see §9.1 | stop pending fixture investigation |

- **Every optimised path is checked against a slow reference on sampled folds and sampled permutation replicates on every production run**, not once at development time. The sample is 16 cells for the scorer chain (v4zeek's `verify`) plus 3 randomly chosen (fold, replicate) pairs re-scored end to end by a naïve loop implementation of §10.
- **This gate has already earned its place three times in v4zeek** — it caught the WPG/WVG standardisation leak, a year-wrap error and a fold-compounding detrend bug. None would have crashed; all three would have produced plausible numbers.

---

## 17. Three harness gates must pass before any scientific number is read

1. **The climatology gate.** `candidates/climatology.py` scores exactly 0.0000 on every benchmark, both protocols, every shuffle seed.
2. **The synthetic-signal gate.** `bench.build_synthetic` plants a known Niño-3.4 dependence and the harness must recover it. Additionally a **synthetic zonal target** is built here: a two-zone field with a known and different index driving each zone, which the atlas pipeline must recover as two zones with the correct two recipes.
3. **The shuffle gate.** Shuffling season-year labels removes positive skill: pooled atlas RPSS at or below zero within Monte-Carlo noise, on at least 4 seeds.

A failure on any of the three stops the analysis. Inherited from v4zeek unchanged except for the new zonal synthetic target.

---

## 18. Everything is reported, including everything that fails

`REPORT.md` has these sections, in this order, and none may be omitted:

1. **The legacy reproduction** — §9.1 against every target, both tiers, pass or fail, labelled as provenance and not as a result.
2. **The measured leakage** — `clean − leaky` (§9.3 − §9.2) on every benchmark, pooled and per zone-window, with the count of affected cells; then the six-leak accounting of §9.4 and the qualitative legacy → clean descent, explicitly not decomposed.
3. **The discovered zone atlas** — per fold: the complete k = 2…8 hierarchy, the selected k, ARI curve with standard deviations, silhouettes, zone maps at every level, cell counts, centroids, annual-cycle plots, discovered windows, selected index and lead per zone-window.
4. **Fold stability** — every metric in §11, the 6 × 6 ARI matrix, the per-cell switch map, `orphan_area` and `absence_rate` per fold, the full track table including tracks below the 4-fold bar and tracks below the 8-year bar, the H1 test with its *n*, its null construction and its power, and an explicit statement that nothing in this section fed any score.
5. **Complete zonal-product skill** — the primary usefulness verdict first: `RPSS_atlas`, its 200-replicate null, its p, and the USEFUL / NOT USEFUL call under §10.6's two-condition rule, stated whichever way it comes out. Then the four arms, both protocols, both weighting rules, the two paired arm-comparison tests, the §10 statement that products rather than predictands are compared, **and the full per-fold zone-window table with every zone present and no minimum-year threshold applied**.
6. **Fixed-target and gridded diagnostics** — secondary benchmarks A and B, kept separate, with A identified as the controlled zonation test.
7. **Conditional MAM results** — the three families, each against its own paired null, each with its coverage, each unscored zone listed, and the count of zones that did and did not discover MAM.
8. **Descriptive expert overlap** — the AGUv2 box, the reviewer's box, the ~38°E and ~7°N splits, labelled descriptive.
9. **Limitations** — at minimum: fold 0 trains on 21 years; n = 22 walk-forward test years; the track count is small; predictors are perfect-prognosis observed SST, not forecasts; the two-window cap; τ = 0.90 is provenance-backed but still a threshold; the reference frame for matching is fold 5; **§10's product-versus-predictand limitation**; ERSST fixture provenance including its dual-calendar rebuild; and **the dirty rosetta and deepscale checkouts of §2**, which mean the environment is drift-detectable but not git-reconstructible.

**Standing commitments.**
- No selector, k rule, metric, weighting rule, matching rule or reported variant is ever chosen because it performed better on outer test years.
- Every discovered zone, orphan, season, protocol and negative outcome is preserved and reported.
- A new benchmark version is registered rather than an existing benchmark modified.
- Retractions and dead ends are recorded in rx as they happen and surfaced in the report.

---

## 19. The deliverables and the single regeneration command

| deliverable | path |
|---|---|
| this specification | `legacy/contracts/SPEC.md` |
| specification checks (69, all passing) | `probes/spec_check.py` |
| pinned environment and fixture hashes | `outputs/env.json`, `outputs/ersst_provenance.json`, §1 and §2 above |
| ERSSTv5 fixture builder | `src/fetch_ersst.py` |
| rosetta ERSST patch, kept out of v3rx's rx history | `legacy/patches/rosetta-ersst-v5.patch` |
| legacy reproduction | `legacy/reproduce_agu3.py` |
| leaky and clean out-of-sample arms | `harness/oos_arms.py` |
| locked atlas benchmark | `harness/atlas_bench.py` (+ `atlas-wf-v1`, `atlas-kf-v1`) |
| fixed-target secondary benchmark | `harness/fixedmean_bench.py` |
| gridded secondary benchmark | `harness/grid_bench.py` |
| slow and vectorised scorers with agreement tests | `harness/atlas_score.py`, `harness/atlas_score_slow.py`, `tests/test_scorer_agreement.py` |
| restartable production runner | `run_atlas.py` (checkpoint `outputs/atlas_null.jsonl`) |
| machine-readable outputs | `outputs/*.json`, `outputs/*.jsonl` |
| zone maps and annual-cycle plots | `outputs/figures/` |
| one command regenerating everything | `./regenerate.sh` |
| the report | `REPORT.md` |

- **`./regenerate.sh` runs every step through rx**, in order: fixtures → gates → legacy reproduction → leaky arm → clean arm → real atlas → null sweep → stability → secondaries → figures → report. It is restartable and skips completed work.
- Inherited unchanged from v4zeek and re-hashed here: `bench.py` (`154c06d5…`), `batched.py` (`ec592999…`), `candidates/climatology.py` (`ebbf6660…`), `tests/test_wrap.py` (`3a7c0d4e…`), `probes/grid_sweep.py` (`943e1d67…`).

---

## 20. Decisions taken in review, and what remains open

### 20.1 ERSSTv5 — approved, implemented as `sst/ersst-v5`, tested, and pinned

- **A minimal additive entry for `sst/ersst-v5` was appended to `~/Developer/ACCORD/rosetta/src/rosetta/catalog.yaml`.** It uses the existing `http` adapter, the NCEI monthly NetCDF archive (`https://www.ncei.noaa.gov/pub/data/cmb/ersst/v5/netcdf/ersst.v5.{YYYY}{MM}.nc`), native `degree_C` passed through unconverted, and the 0–360 longitude convention the index boxes of §7 require.
- **The rosetta checkout's unrelated uncommitted work was not touched.** The edit is a pure append after the last product. `catalog.yaml`'s three pre-existing diff hunks (at lines 311, 394 and 478) are unmodified, and the new hunk is the fourth, at the end of the file. Nothing was staged, committed or reverted in that repository, and the change is kept out of v3rx's rx history.
- **The patch is preserved at `legacy/patches/rosetta-ersst-v5.patch`**, so the environment is reconstructible without depending on that working tree.
- **rosetta's three existing ERSST integration tests pass against the restored entry**, run verbatim from `rosetta/tests/test_integration.py`:

| test | result |
|---|---|
| `test_fetch_ersst_v5_east_africa_recent` | PASS (2.1 s) |
| `test_fetch_ersst_v5_multiyear_timeseries` | PASS (3.9 s) |
| `test_fetch_ersst_v5_west_pacific_historical` | PASS (1.6 s) |

- **Two environment adjustments were needed to run them, neither of which changes rosetta or the tests:** `pytest` is not installed in the `pycpt` environment, so a minimal shim supplied `mark`, `fixture` and `param`; and the IPv4 preference described in §1.2 was installed in the driver process. Both are recorded here because a future re-run needs them.
- **Pinned:** rosetta HEAD `f3ef32d986a9de29d36d1d164dce78c284a180f9`, `catalog.yaml` sha256 `bd683de05c7218627b366c4971b3239bc7e52548283f777695ea465c00f9132e`, fixture sha256 `a9c91583b92e71d24362cf092a038d947c8fd7764cf1c0c2846fbb81c6042916`.

### 20.2 k selection — τ = 0.90, largest qualifying k, full hierarchy always reported

- Rule: **largest k in 2…8 with mean bootstrap ARI ≥ 0.90, otherwise argmax ARI.** Selects k = 3 on the published curve.
- Provenance: 0.90 is AGUv3's own stability bar, so no new threshold is invented; only the tie-break direction changes.
- **The complete k = 2…8 hierarchy is always reported**, regardless of the selected k (§4, §18.3).

### 20.3 Permutations — 1,200 shared discovery runs, paired across families

- **6 folds × 200 paired permutations = 1,200 complete discovery runs.**
- The three families share discovery, window detection, predictor selection, fitting and thresholds; only final test-year scoring differs (§6, §14).
- The same 200 draws serve all three families, so family comparisons are paired and are labelled as such.

### 20.4 Fixture and library shas — filled

- Every slot §1.1, §1.2 and §2 asked for is filled and machine-verified. `probes/spec_check.py` re-asserts all of them and **69 of 69 specification checks pass** (`r:8`).
- What that probe checks, so the list is auditable: both fixture hashes and byte counts; the CHIRPS domain, month completeness, coarsened grid and 3564-cell count; the ERSST month sequence, longitude convention, index-box coverage and Niño-3.4 plausibility; both library shas and the catalog hash; the five inherited-file hashes; the full walk-forward and k-fold fold tables; the Context-versus-AGUv3 lead equivalence over all 12 window starts and 4 leads; the anomaly-base leak-neutrality argument of §7; that exactly `{wpg, wvg}` respond to the standardisation change; that τ = 0.90 selects k = 3 while max-ARI selects k = 2; the §14 permutation-invariance argument in both directions; that the §10 weights sum to 1 for every k and window count; Hungarian determinism, one-to-one-ness and the enumeration cap; the §12 coverage arithmetic; the season detector's plateau and wrap behaviour; the internal consistency of the §9.1 legacy targets; and the §14–15 budget arithmetic.

### 20.5 Revision 3 corrections

- **The primary claim now has a null and a decision rule (§10.6).** The complete discovered-window atlas is scored on the same 1,200 permutation runs as a fourth pooling family; useful means `RPSS_atlas > 0` **and** `p ≤ 0.05`. Two paired arm comparisons ride on the same replicates. No discovery run was added.
- **Aggregate scoring is fold-local and matching-independent (§10, §12.1).** Revision 2's coverage rule pooled by matched track, which let the analyst's reference frame move the headline number. The aggregate now applies no minimum-year threshold, renormalises nothing, and never consults a track identity; `MIN_SCORED` gates only the descriptive per-track tables and H1 (§12.2).
- **Dirty-file counts are replaced by source-tree hashing (§2).** `outputs/env.json` now exists and records a per-file sha256 map over all 79 source files in the two libraries, a `tree_sha256` scalar per library, and a `diff_sha256` over each repository's full working diff.
- **The question is restated (§0).** Rainfall alone discovers zones and seasons; SST is required to select forecast recipes. The earlier "rainfall alone produces an atlas" phrasing was wrong and is retracted here.

### 20.6 Two things remain imperfect, and are recorded rather than fixed

- **The library checkouts are dirty upstream.** §2's content hashing detects drift to the byte and localises it to the file, which is what revision 3 was asked for, but it cannot reconstruct the environment from git alone because the changes are uncommitted in repositories this project does not own. Carried into §18.9.
- **The rx project objective still reads with revision 1's phrasing**, because `rx init` fixes it and no CLI edits it. §0 is authoritative and the divergence is noted in `.rx/NOTES.md`.

### 20.7 Nothing else is open

- All other choices in this document are locked. A change to any of them after registration requires a new benchmark version and an amendment recorded here.

---

*End of specification. No benchmark is registered and no scientific experiment is run until this document is approved.*
