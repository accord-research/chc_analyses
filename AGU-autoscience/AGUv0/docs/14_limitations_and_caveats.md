# Limitations, caveats, and how to read these results

This study is best understood as a **framework for diagnosing where SST-based seasonal skill
appears to exist and why** — not as a source of operational skill estimates or general laws. The
rankings it produces are empirical and configuration-specific. This document states the
methodological limits explicitly and softens the scientific claims to what the evidence supports.
It reflects (and adopts) multiple rounds of expert-reviewer critique of earlier, over-confident drafts.

### Audit-response revision (2026-07, expert-panel scientific audit)

An independent two-lens audit (statistical-multiplicity + physical-oceanography) drove the following
concrete changes; each has a reproducible script and output table:

- **Multiplicity family now includes the adaptive predictors** (`src/multiplicity_adaptive.py` →
  `multiplicity_adaptive.md`). The base FDR family was 8 textbook indices only; the *discovered*
  winners (`sst_projection`, `combo_top2`, `persistence`) are now permutation-tested (with in-fold
  pattern/selection refit, so the null carries their optimism) and folded into one BH family per
  country. This lets "does the actual best predictor survive FDR?" be answered, rather than testing
  only the weaker textbook indices and asserting the cell was null.
- **Survivor counts de-duplicated** (`src/multiplicity_dedup.py` → `multiplicity_dedup.md`). The
  `National` band is the mean of its sub-bands, `wvg2`/`wvg3` are functions of Niño3.4, and
  Niño3.4/IOD co-vary in OND; the raw "27 (Kenya) / 10 (Ethiopia)" survivors are **~3 independent
  signals each**. The flagship q is robust to de-duplication (it does not inflate).
- **Trend-robust q** (`src/multiplicity_detrend.py` → `multiplicity_detrend.md`). Permutation-FDR
  recomputed on in-fold-detrended residuals: the East-African OND/IOD flagship *strengthens*
  (Kenya q 0.006→0.004), the trend-riding MAM cells drop out.
- **Genuinely out-of-sample block** (`src/heldout_genuine.py` → `heldout_genuine.md`). The search is
  re-run on train (1991–2009) with a **train-only climatology**, and the *train-discovered* winners
  are scored on 2010–2023 with bootstrap CIs. East-African OND holds (CI excludes 0); Nigeria's
  high-train winners collapse; the earlier "comes back stronger" claim is dropped (within noise at
  n = 14).
- **Two physical caveats added** (below, §8): the **boreal-summer IOD predictability barrier** and
  **ENSO–IOD collinearity**.
- **MME GROC confidence intervals** (`src/mme_ci.py`): a year-block bootstrap of the domain-search
  GROC. *Pending re-run* — the NMME source server (CCSR/Columbia OPeNDAP) was returning 502 during
  the revision; the point estimates already show sub-0.1 gaps that §3's noise floor calls
  indistinguishable.

### What the earlier revision changed (in response to review)

- **Split the "benchmark" into lead vs. concurrent.** The hybrid now reports the **lead**
  predictability (pre-season SST → rain — the realistic bar, e.g. OND IOD ≈ 0.5) as the headline,
  and labels the concurrent target-season value (≈ 0.85 for IOD) as a partly-diagnostic upper
  reference. The taxonomy scatter's y-axis is now **lead** predictability, not concurrent.
- **Ran a detrending check** (`src/detrend_check.py`, in-fold linear detrend): East African OND/IOD
  survives (even strengthens, e.g. Kenya OND 0.54→0.57); Ethiopian Kiremt survives; the weak **MAM
  apparent signals collapse to ≈ 0** (Ethiopia MAM nino34 −0.30→−0.01), confirming low predictability;
  Nigeria's Atlantic textbook indices are largely trend-robust under proper in-fold detrending.
- **Fixed the hybrid's index choice:** the Sahel now uses the **Atlantic interhemispheric gradient**
  (its classical driver), not Niño3.4; other targets use the physically-appropriate driver.
- **Foregrounded RPSS with GROC** and de-saturated the domain/method heatmaps; the narrative now
  states the domain/method "winners" are within the noise floor and that SST-CCA barely beats the
  precip-MOS baseline.
- **Flagged the decorative-zones issue** (below) and softened the composite / "El Niño years" wording.

Now **done** (see the audit-response section above): formal FDR/permutation control (incl. the
adaptive predictors), a de-duplicated survivor count, a trend-robust q, and a genuine out-of-sample
block. Still **not** done (recommended next): nested CV; wiring the clustered/gridded zones into the
forecast targets; a common analysis period for obs vs. MME; and the MME-GROC bootstrap CIs (script
ready, pending the NMME server).

## 1. Search multiplicity / winner's curse — the main methodological limit

The workflow searches many axes at once — season × zone × predictor × method × predictor domain ×
lead — and then elevates the best-scoring configurations. **Leave-one-year-out (LOYO)
cross-validation is necessary but does not, by itself, remove multiple-comparisons bias.** The
maximum over many cross-validated scores is upward-biased: some "winners" are the top of a noisy
distribution, not real signal.

- *Scale of the search.* The feature screen alone is ≈ 10 predictors × 8 seasons × 4 bands ≈ **320
  LOYO correlations per country**. At n ≈ 33 the per-comparison two-sided p < 0.05 threshold is
  |r| ≈ 0.34; a family-wise (Bonferroni) or false-discovery-rate–adjusted threshold is
  **substantially higher (~0.5+)**.
- *Implication.* Only the **strongest** results plausibly survive multiplicity: the East African
  **OND short-rains** IOD relationships (ceilings ~0.5–0.57; real MME GROC ~0.70–0.73; hybrid
  ~0.7) and, more marginally, the **Kiremt** ENSO/WVG signal (~0.46, hybrid 0.58). Mid-range
  "winners" (|r| ~ 0.2–0.35) should be read as **suggestive / hypothesis-generating, not
  established**.
- *Mitigations used here:* LOYO CV; discovery-inside-the-fold for the data-driven SST pattern (no
  snooping); physical-mechanism screening; and cross-checks across three quasi-independent lines
  (the observation-only screen, the drought/flood composites, and the real dynamical MME).
- *Mitigations now applied (audit-response revision):* formal FDR / permutation control over a
  unified family that includes the adaptive predictors, a de-duplicated survivor count (~3
  independent East-African signals, not 27/10), a trend-robust (detrended-residual) q, and a
  genuine train/test held-out block. *Still recommended:* nested cross-validation.

## 2. The "benchmark" is not a theoretical ceiling on dynamical skill

Earlier text called the perfect-prognosis score a "ceiling." **It is not.** It is the LOYO skill of
a *statistical mapping from observed SST to observed rainfall* — an **empirical benchmark of
SST-based statistical predictability**, not an upper bound on what a dynamical system can do.

- A dynamical model could in principle **exceed** it: it uses full 3-D evolving fields, coupled
  dynamics, land–atmosphere feedbacks, and information beyond the chosen SST indices.
- The benchmark can also be **inflated** — by the same multiplicity issue (it is itself a best-of
  search), and, in the hybrid comparison, by using *concurrent-season* rather than *lead* SST.
- We therefore call it a **perfect-prognosis benchmark** and use it as a *reference point*, not a
  *limit*.

## 3. Sampling noise (n ≈ 24–33 years)

The hindcast records are short. At n ≈ 24 the 95% sampling interval around r = 0 is roughly ±0.4,
and GROC differences below ~0.1 are within noise. **Read the structure and the physics, not the
third decimal.** Only a few results here clear that bar (see §1).

## 3b. Predictand: discovered zones are diagnostic; forecasts use latitude bands

`seasons.py` clusters the annual cycle into homogeneous zones and maps them, but **no downstream
module consumes those zones** — the teleconnection screen, feature search, composites, MME, and
hybrid all use the **latitude `BANDS`** in `areas.py`. So "discovers homogeneous zones … the
precondition for per-region forecasting" oversells: the forecasts run on latitude-band means.
This matters most for **Ethiopia**, where a band at ~7–10°N over 33–48°E blends the western Kiremt
highlands (JJAS peak) with the eastern Somali/Ogaden lowlands (bimodal, dry summer) — regimes of
opposite phase and sometimes opposite teleconnection sign, diluting the signal. Wiring the
clustered (or gridded) zones into the forecast targets is a needed revision.

## 3c. Sample-window mismatch

Observation-only benchmarks/leaderboards are over 1991–2023 (n = 33); the MME and hybrid are over
1993–2016 (n = 24). A `Ceiling`/benchmark value in one table may be a different sample from the MME
value in the same row. Everything should be put on a common period.

## 4. Single configuration — results are not general

Every number is specific to the choices made: **CHIRPS zonal-mean predictands** at coarse
resolution; a **4-model NMME ensemble** (+2 C3S in one test); **CCA-MOS** calibration with limited
bias treatment; fixed init months; and **1993–2016**. Different predictand definitions, model sets,
bias correction, model coupling, higher resolution, or regionalization could change the skill —
especially for West Africa, where documented studies show improvement with better bias treatment,
coupling, or downscaling.

## 5. Softened scientific claims, aligned with the literature

| Region / season | What the earlier draft said | What the evidence supports |
|---|---|---|
| **Nigeria / West Africa monsoon** | "dynamical forecasting cannot work / total failure" | For *this* ensemble and predictand, skill is **marginal** and the rainfall-relevant **Atlantic signal is hard for the system to exploit** — consistent with known West-African-monsoon forecast biases and mixed Atlantic/ENSO/circulation controls. **Not** a universal impossibility; better bias treatment, coupling, or regionalization may help. |
| **East African OND short rains** | "the season works" | **Comparatively high, robust predictability** tied to the **IOD and ENSO** — consistent with the established literature. The strongest, most defensible result here. |
| **East African MAM long rains** | "no seasonal-lead driver at all" | **Structurally low SST-based predictability** — but **not driverless**. The controlling processes (Congo/Walker zonal winds, the MJO, Gulf-of-Guinea/Sahel circulation) are **less SST-mediated and harder to predict at seasonal lead**. Describe as low-predictability, not driver-free. |
| **Ethiopia Kiremt** | (broadly as stated) | Skill is tied **primarily to ENSO**, with the **IOD adding independent regional influence** in some northern settings; operational Ethiopian seasonal forecasts have **modest but positive** skill. Our ENSO/IOD hybrid result is consistent with this. |
| **WVG "rediscovery"** | "the framework rediscovered, without being told, that the WVG belongs to East Africa" | The WVG–East-Africa relationship is **already documented** (Funk et al.). Our result that it ranks well for Kiremt/East-African rains and poorly for Nigeria is a **consistency check with the literature, not a novel discovery**. |

## 6. What is, and is not, being claimed

- **Is:** a modular, uniformly-scored framework that runs identically across regions and produces
  physically-interpretable, cross-validated predictor rankings and a *real-forecast-vs-benchmark*
  comparison — useful for **diagnosing where SST-based seasonal skill appears to exist and why**.
- **Is not:** general laws, operational skill estimates, or proofs of impossibility. Treat the
  strong, mechanism-supported, multiplicity-surviving results (East African OND short rains) as
  robust; treat the rest as **hypotheses for confirmatory, multiplicity-controlled testing**.

## 7. The "criterion," restated conservatively

The organizing question — *does the rainfall-relevant ocean coincide with the ocean GCMs forecast
well, and is that ocean's link to rainfall strong at seasonal lead?* — is best used as a
**diagnostic lens**, not a law. It correctly *orders* the cases seen here (East African short rains
> Ethiopian Kiremt > West African monsoon ≈ East African long rains) and points to *why* skill is
or isn't realized, which is its value. Whether it generalizes requires more regions, more models,
multiplicity control, and out-of-sample confirmation.

## 8. Physical-oceanography caveats (audit lens 2)

- **Boreal-summer IOD predictability barrier.** The Indian Ocean has a well-documented spring/summer
  predictability barrier, so a *June*-initialized OND-IOD forecast is materially harder than a
  September one. Any high IOD *forecast* skill (e.g. the ~0.9 forecast-vs-observed IOD figure in the
  hybrid) most likely reflects verification of an already-mature, late-summer-initialized IOD and/or
  shared-trend inflation, **not** genuine long-lead skill. The "skill does not decay with lead / a
  June forecast ≈ September" reading is the MME's *realized* GROC (noisy at n ≈ 24); a defensible
  long-lead-driver claim needs the IOD forecast skill decomposed **by initialization month**
  (Jun/Jul/Aug/Sep → OND) and detrended.
- **ENSO–IOD collinearity / attribution ambiguity.** IOD is named the OND "winner" over Niño3.4 on
  small correlation gaps, and the wet-OND analog years (1997, 2019, 2023) are exactly when strong
  +IOD and El Niño co-occur; the blind training-block search even picks an ENSO-family index for the
  same cells. At n ≈ 24–33, IOD-specific vs ENSO-forced-via-IOD vs shared variance is not cleanly
  separable. The IOD-primary framing follows the literature and is kept, but as a physically-
  motivated attribution, **not** a demonstrated statistical separation.
- **Minor.** (i) For an ENSO *relative-strength* question under a warming tropical mean, RONI
  (L'Heureux et al. 2024; already in `deepscale.Index.named`) is the cleaner index than fixed-base
  Niño3.4 — matters only where ENSO is elevated in the story, since IOD is primary for East-African
  OND. (ii) The ocean-state screen is **ERSST surface only**; the leading real-forecast precursors
  are subsurface (Indian-Ocean heat content / thermocline; Pacific warm-water volume) — fine for a
  diagnostic screen, not for a genuine forecast argument. (iii) The 4-model NMME set (GEOSS2S +
  CESM1 + CCSM4 + CANSIPSIC4) was chosen to stay IRI-free — an infrastructure choice, not an
  oceanographic sampling design, and thin for estimating ocean-index forecast spread; this is not
  disclosed in the showcase.
