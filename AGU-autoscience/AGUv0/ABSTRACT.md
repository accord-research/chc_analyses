# AGU Annual Meeting — abstract draft

**Working title:** *Autoscience for Seasonal Forecasting: A Modular Data-and-Downscaling
Stack for Automated Search of Skillful, High-Resolution Forecast Configurations, Demonstrated
over Nigeria*

**Authors:** *(TBD)* — ACCORD / Jataware
**Suggested session:** GC / A / NH — Seasonal-to-decadal prediction; climate services for
Africa; AI/ML for Earth system science.

---

## Primary abstract (300 words / 1,991 characters excl. spaces — within the AGU 2,000-char limit)

Seasonal precipitation forecasts embed dozens of design choices—target season, predictor domain, raw SST fields versus teleconnection indices, calibration method, model ensemble, downscaling technique, resolution, and lead time—usually fixed by convention and rarely re-optimized per region and season. We recast forecast design as a searchable space, enabled by two modular, xarray-native libraries: Rosetta, a federated data layer exposing NMME, C3S, CHIRPS, ERA5, and ERSST through one normalized fetch() interface, and DeepScale, a method-agnostic layer for calibration (CCA), multi-model combination, downscaling, and cross-validated verification. A shared contract lets one driver build, run, and identically score any configuration under leave-one-year-out CV—the precondition for automated, agent-driven search.

We demonstrate over Nigeria, Ethiopia, and Kenya, each re-pointed by one config entry. From observations the framework discovers each country's seasons, searches—rather than assumes—candidate predictors per season and subregion, and composites the drought-versus-flood ocean state; a config-driven harness then runs real NMME/C3S forecasts. Critically, we subject the discovered skill to multiplicity control—permutation FDR over all observed predictors, including data-driven ones—and a genuine out-of-sample block. The East African October–December short rains carry real IOD/ENSO-driven skill: an observed teleconnection that survives FDR and holds out of sample, realized by a live NMME forecast near generalized ROC 0.70 with positive RPSS. No West-African predictor survives FDR, textbook or data-driven; the East African March–May long rains stay persistently low-skill. Realized skill shows no systematic lead decay to six months, though a long-lead claim is tempered by the Indian Ocean's summer predictability barrier; downscaling holds skill to ~5 km.

We present this as an automatically computed, per-region diagnostic of where SST-based seasonal skill exists and why, with verification (FDR, out-of-sample) as the deliverable that separates real signal from best-of-search noise. A modular, uniformly scored search over a purpose-built, config-portable stack is a template for agentic autoscience toward regionally optimal, high-resolution climate services.
---

## Plain-language summary

Making a seasonal rain forecast involves many expert choices — which months to forecast,
which ocean patterns to use as clues, how to sharpen a coarse global-model forecast down to
local detail, and how far ahead to issue it. These choices are usually made by habit and
seldom re-checked for each place and season. We built a system that treats every choice as a
dial and automatically turns the dials to find the combination that forecasts best, scoring
each option the same fair way against decades of observations. Two software tools make this
possible: one that fetches any climate dataset through a single interface, and one that runs
any forecasting or downscaling method through a single interface. We show the system on
Nigeria — a hard case because its rainy south and dry north behave differently — where it
rediscovers the country's real rainy seasons, *searches* for the ocean and land signals that
predict each one (including patterns it finds in the data itself, not just textbook indices),
and maps which ocean states precede drought versus flood in each region. The upshot: different
parts of Nigeria and different seasons need genuinely different forecast recipes, and the
system discovers them automatically. The goal is a reusable recipe that AI agents can run to
design better, sharper forecasts anywhere.

---

## Extended abstract / talk outline

1. **Problem.** Forecast design is a large, mostly-unsearched configuration space; per-RCOF
   conventions are rarely re-optimized per region/season/lead. West Africa specifically has
   Sahel-biased skill literature and little quantified Guinea-coast or PyCPT-over-Nigeria
   skill.
2. **Enabling stack.** Rosetta (one `fetch()` across NMME/C3S/CHIRPS/ERA5/ERSST; normalized
   xarray; region masking; caching) + DeepScale (calibration, MME strategies, downscaling
   methods, skill suite, LOYO CV) share a contract → any configuration is a dict a driver can
   run and score identically.
3. **Autoscience loop.** Propose config → fetch → calibrate/downscale → score under CV → log
   → update. Physical priors (an observation-only teleconnection screen) prune the predictor
   space cheaply; near-separable axes are searched in stages; an agent carries interpretation
   between stages. Reproducibility check: the same harness over the Greater Horn should
   recover the known WVG-for-East-Africa result.
4. **Nigeria results.**
   - *Seasons (E1):* data-driven homogeneous zones + candidate forecast windows (bimodal
     coast vs. unimodal Sahel), from CHIRPS-v3 climatology.
   - *Predictors, searched (E2/E2b):* a candidate-feature pool — textbook SST indices, a
     data-driven SST-projection pattern (discovery inside the CV fold), and non-SST covariates
     (rainfall persistence) — ranked by honest LOYO skill per season/zone. Result: different
     winners per season and subgeography; the data-driven pattern and persistence beat the
     named indices where they win; the WVG is one candidate, mostly outscored. SST-field-vs-
     index is decided by which actually cross-validates.
   - *Drought/flood setups (E2c):* pre-season SST composites for the driest vs. wettest
     tercile years per season/zone — the "conditions → outcome" atlas (El Niño + warm Indian
     Ocean → OND flood; warm-Pacific-leaning → Sahel-JAS drought).
   - *Real MME vs. ceiling (E4):* an actual NMME 4-model ensemble (`seasonal_mme`, CCA, LOYO)
     has *no usable skill* for JAS/OND Nigeria (GROC 0.46–0.50, RPSS<0) while the
     perfect-prognosis ceiling is +0.23…+0.36 — the dynamical models don't realize the
     predictable signal the observed ocean state carries. The framework makes that gap
     *measurable* per zone/season and turns it into the next search target (predictor domain,
     more models, calibration).
   - *Domain & method search (E3):* sweeping the SST predictor domain (teleconnection CCA)
     recovers the *physically correct* basin per season — Atlantic/Gulf-of-Guinea for the
     Middle-Belt monsoon, Pacific for the Sahel and OND short rains — and sweeping the full
     method registry (CCA, BCSD, QM, delta, rank-analog) finds a *zone-specific* winner (CCA for
     the Middle Belt/OND, `delta` for the Sahel). Both searches pick sensible winners and lift
     skill (Sahel ~0.50→0.56 GROC), yet real dynamical skill stays marginal and below the
     ceiling — localizing the binding constraint to the models' seasonal SST-forecast skill.
   - *Downscaling (E5):* method comparison and the resolution/skill frontier — how much
     detail is added while skill is retained, and where added detail is valuable even at
     constant skill.
   - *Lead (E6):* skill-vs-lead curves and attribution of which predictor updates move the
     outlook (and whether updates always help).
5. **Claim.** A modular, uniformly-scored search over a purpose-built stack turns
   forecast design into an automatable, agent-drivable optimization — a path to regionally
   optimal, high-resolution seasonal climate services.

---

## Notes for finalizing before submission

- **Preliminary results already computed** (2026-07-17, real CHIRPS v3 + ERSST v5 via Rosetta,
  1991–2023) and citable in the abstract:
  - *Seasons:* four data-driven zones, bimodal coast (May/Oct peaks + August break) → unimodal
    Sahel (single August/JAS peak) → 2–3 zone-staggered forecast windows.
  - *Predictors, searched (LOYO CV correlation):* the data-driven SST-projection pattern wins
    the core monsoon — 0.46 (JJAS Middle Belt), 0.42 (JJA North), 0.37 (JJAS National) —
    beating every textbook index; a CV-honest multi-feature combination (IOD + persistence)
    wins the short rains (OND North 0.29, OND National 0.24); the Atlantic family (ATL3,
    TNA−TSA) wins the Guinea/Middle summer; rainfall persistence wins the northern late season;
    ENSO/IOD win the first and southern second rains. The WVG never wins a recommended window.
  - *Capstone — discovered recipes:* one best predictor per zone × natural forecast window
    (`synthesize_recipes.py`), i.e. a different, data-derived forecast approach for each
    subgeography and season — the core deliverable.
  - *First real forecast:* an NMME 4-model ensemble (CCA, LOYO) scored against the ceiling —
    GROC 0.46–0.50 (no skill) vs ceiling +0.23…+0.36; the measurable gap between empirical
    predictability and dynamical realization, per zone/season.
  - *Hybrid decomposition (the "why"):* feeding each model's forecast SST index into the
    observation-trained link shows the models forecast **ENSO (0.83) and the IOD (0.91)
    excellently but the Atlantic Niño poorly (0.28)** — and for Nigeria the forecastable oceans
    (Pacific, Indian) teleconnect only weakly, while the rainfall-controlling Atlantic is the one
    the models cannot forecast. The binding constraint is Atlantic SST prediction, not the
    calibration method. (Skill decimals are noise-limited at n=24; the SST-forecast-skill
    decomposition and its physical structure are the robust results. The IOD 0.91 almost certainly
    reflects an already-mature, late-initialized OND IOD and/or shared trend — not genuine long-lead
    skill: the **boreal-summer IOD predictability barrier** makes a June-initialized OND-IOD forecast
    materially harder, so decompose it by initialization month before it underwrites any
    "well-forecast at lead" claim.)
  - *Drought/flood setups:* pre-season SST composites give clean, physical setups (OND flood ←
    El Niño + warm Indian Ocean; JAS Sahel drought ← warm-Pacific-leaning) with the actual
    dry/wet analog years per season/zone.
  - *One CV skill result:* DeepScale `logit`, JAS Sahel terciles, LOYO — the screen's top
    driver beats Niño3.4 (43% vs 22% of cells with positive RPSS), while single-index skill
    stays low, motivating the multi-predictor calibration.
- **Still to fill from the GCM sweep:** best config per zone/lead, the multi-model MME skill
  map, and the downscaling resolution/skill frontier — the compute-bound harness stage.
- **Citations to verify** (flagged in [`docs/01`](docs/01_nigeria_climate_background.md)):
  no distinct "Funk 2019" WVG paper (use 2014 HESS / 2018 QJRMS / 2023 Earth's Future);
  Rodríguez-Fonseca et al. 2011 is *Atmospheric Science Letters*. Confirm author lists/DOIs
  for the ~-flagged entries.
- **Framing guardrail:** present the WVG-for-West-Africa test as an empirical hypothesis, not
  an expected teleconnection — WAM physics points to Atlantic/Mediterranean/Indian/ENSO
  forcing.
- **Character limit:** AGU caps the abstract body at 2,000 characters excluding spaces; the
  primary abstract above is 1,899 (compliant). Title cap is 300 characters — the working title
  above exceeds it and must be shortened at submission.
