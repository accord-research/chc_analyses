# Nigeria vs. Ethiopia vs. Kenya — the same harness, three countries, a validated criterion

Extending the analysis across countries is not replication; it is the **test of the framework's
central diagnostic**. The whole pipeline is re-pointed by one config entry
([`src/areas.py`](../src/areas.py), `AREA=ethiopia`/`kenya`) — the concrete demonstration of the
"modular, config-driven" thesis — and the countries are chosen to span the range of cases that
should matter. §1–5 develop the Nigeria↔Ethiopia contrast; **§6 adds Kenya**, which completes a
clean three-case taxonomy of *when dynamical seasonal forecasting can work*.

## The hypothesis this comparison tests

The Nigeria study ended on one sharp finding ([`docs/12`](12_hybrid_and_c3s.md)): dynamical
seasonal skill was capped because **the ocean that controls Nigerian rainfall (the Atlantic) is
the one GCMs forecast worst**, while the oceans they forecast well (Pacific ENSO, Indian Ocean)
teleconnect only weakly to Nigeria. The forecastable ocean and the rainfall-relevant ocean were
*different oceans*.

**Ethiopia should be the mirror image.** East African rainfall — the Kiremt monsoon and
especially the Greater-Horn short rains — is controlled by **ENSO and the Indian Ocean Dipole**,
the very drivers GCMs forecast *well*, and it is the region the **Western-V-Gradient index was
designed for** (Funk et al.). So the prediction is:

| | Nigeria | Ethiopia (hypothesis) |
|---|---|---|
| Rainfall-relevant ocean | Atlantic (+ Indian for OND) | Pacific (ENSO) + Indian (IOD) |
| Do GCMs forecast it well? | **No** (Atlantic cold-tongue problem) | **Yes** (ENSO/IOD are forecastable) |
| WVG (E-Africa index) in the feature search | never wins | **should win** for the relevant seasons |
| Expected real dynamical MME skill | none | **some** — relevant = forecastable |
| Expected hybrid behavior | fails (bottleneck = Atlantic forecast) | **works** (bottleneck removed) |

If this holds, the framework has done something more than describe two countries: it has
produced a *portable, mechanistic criterion* — "does the rainfall-relevant ocean coincide with
the forecastable ocean?" — that predicts **where dynamical seasonal forecasting can work at
all**. That criterion, computed automatically per region, is the AGU contribution.

## 1. Seasons

Two structurally different regimes, both recovered from data by the same clustering
([`seasons_annual_cycle_ethiopia.png`](../outputs/figures/seasons_annual_cycle_ethiopia.png)):

- **Nigeria:** a monotonic *latitude* gradient — bimodal Guinea coast (May + Oct, August break)
  → unimodal Sudano-Sahel (single August peak).
- **Ethiopia:** a *terrain*-driven, anti-phased structure — a **unimodal Kiremt highland
  monsoon** (Zone 2, ~11°N, sharp single **August** peak, JJAS) coexisting with a **bimodal
  south** (Zone 0, ~6°N, **April + October** peaks and a *dry summer*) — the classic
  Greater-Horn MAM long-rains + OND short-rains regime. The southern dry season falls exactly
  when the highlands are wettest.

So the forecast calendars differ fundamentally: Nigeria's seasons shift smoothly with latitude;
Ethiopia's are two near-opposite annual cycles in one country (highland JJAS vs. southern
MAM/OND). Same discovery code, no assumptions — the partition is data-driven for both.

## 2. Predictors — **the WVG wins for Ethiopia** (and loses for Nigeria)

The hypothesis is confirmed cleanly. Best cross-validated predictors
([`features_best_ethiopia.md`](../outputs/tables/features_best_ethiopia.md) vs the Nigeria
leaderboard):

| Season / zone | Nigeria best (CV corr) | Ethiopia best (CV corr) |
|---|---|---|
| Monsoon core (JAS North) | data-driven SST pattern (0.23) | **WVG-3box (0.46)**, WVG-2box (0.45) |
| Monsoon (JAS National) | ATL3 / atl_grad (~0.29) | **WVG-3box (0.40)** |
| Short rains (OND South/Nat.) | IOD + persistence combo (0.24–0.29) | **IOD / combo (0.48–0.56)** |
| Second/short rains (SON South) | — | **Niño3.4 (0.46)**, IOD (0.45) |

Two things stand out. **First, the Western-V-Gradient — the East-Africa index that never won a
recommended window for Nigeria — is the top predictor for Ethiopia's Kiremt monsoon** (0.46),
exactly the region and season Funk et al. built it for. The autoscience search, run identically
for both countries, *rediscovered* that regional specialization rather than assuming it.
**Second, Ethiopia's ceilings are markedly higher** (0.40–0.56 vs Nigeria's 0.23–0.46) and are
carried by **ENSO, the IOD, and the Pacific WVG** — all Pacific/Indian drivers. Nigeria's were
carried by the Atlantic. The rainfall-relevant ocean is different, and — crucially — Ethiopia's
is the *forecastable* one.

## 3. Drought / flood setups

The pre-season SST composites recover the canonical East African teleconnections
([`composite_years_ethiopia.json`](../outputs/tables/composite_years_ethiopia.json)):

- **Kiremt (JAS/JJAS North) drought ← El Niño.** The driest Kiremt years composite is
  **1997, 2002, 2009, 2015, 2023** — every one a major El Niño; the wettest are La Niña years
  (2000, 2010, 2020, 2021). This is the FEWS-NET/CHC "El Niño → poor Kiremt" signal
  (cf. [`analyses/chc_ethiopia`](../../analyses/chc_ethiopia)), here reproduced automatically.
- **Southern short rains (OND South) flood ← positive IOD / El Niño.** The wettest OND-south
  years are **1997, 2019, 2023, 2015, 2006, 2011** — the strong positive-IOD years that flood the
  Greater Horn; the driest are negative-IOD/La-Niña years (2010, 2016, 2021).

Contrast with Nigeria, where the OND flood setup was also El Niño + warm Indian Ocean but the
*monsoon* driver was the (poorly-forecast) Atlantic. For Ethiopia, **both** the drought driver
(ENSO) and the flood driver (IOD) are oceans the models forecast well — which sets up §4–5.

## 4. Real dynamical skill: the MME *works* for Ethiopia's short rains

Same NMME 4-model CCA MME, same LOYO, run with `AREA=ethiopia`
([`mme_domain_best_ethiopia.md`](../outputs/tables/mme_domain_best_ethiopia.md)):

| Target | Best SST domain | GROC | RPSS | r | Ceiling r |
|---|---|---|---|---|---|
| OND South (short rains) | **Indian** | **0.734** | **+0.236** | **+0.546** | 0.56 |
| JAS Kiremt (North) | global-tropical | 0.535 | −0.02 | +0.06 | 0.46 |
| MAM South (long rains) | Pacific | 0.550 | −0.02 | +0.11 | 0.05 |

**For the OND short rains the dynamical MME has real, robust skill** — GROC 0.734, a *positive*
RPSS (+0.236), and deterministic r +0.55 (n=24, well beyond noise) — and the domain search
correctly selects the **Indian Ocean** (IOD) as the predictor basin. This is the **first
genuinely skillful real forecast anywhere in the study**: every Nigerian MME config sat at the
0.46–0.52 no-skill line, whereas Ethiopia's OND clears it decisively. Kiremt and MAM stay
marginal at the pure-CCA/tercile level (the calibration doesn't fully capture the ENSO signal,
and MAM is intrinsically low-predictability — see below), but the *contrast is already made*:
where the driver is the forecastable Indian Ocean, the dynamical ensemble delivers.

## 5. The hybrid — where a real *lead* link meets a forecastable driver

The hybrid feeds each model's forecast SST index into the obs-trained link, using the
*physically-appropriate, search-consistent* driver per target (the Atlantic **gradient** for the
Sahel — its classical driver — not Niño3.4). Two references are reported: the **lead** predictability
(pre-season SST, the realistic bar) and a **concurrent** perfect-SST reference (an upper bound,
partly diagnostic for the IOD). East Africa lands in the skillful regime; Nigeria does not
([`hybrid_vs_mme_*.md`](../outputs/tables/)):

| Target | Index | GCM forecasts driver? | **Lead** predictability | Concurrent ref | **Hybrid** |
|---|---|---|---|---|---|
| **Ethiopia** OND South | IOD | 0.91 | **+0.56** | +0.85 | **+0.73** |
| **Kenya** OND National | IOD | 0.91 | **+0.54** | +0.86 | **+0.75** |
| **Ethiopia** JAS Kiremt | Niño3.4 | 0.83 | +0.41 | +0.71 | **+0.58** |
| **Nigeria** JAS Middle | Atlantic Niño | **0.27** | +0.28 | +0.35 | −0.11 |
| **Nigeria** JAS Sahel | Atlantic gradient | 0.31 | +0.00 | −0.64 | −0.45 |
| **Nigeria** OND National | IOD | 0.91 | +0.16 | +0.18 | −0.32 |
| Ethiopia/Kenya MAM | Niño3.4 | 0.77 | ≈ 0 | ≈ 0 | ≈ 0 |

The decomposition — *(is there a seasonal-lead link?)* × *(can the model forecast that driver?)*:

- **East Africa (skill realized):** OND short rains have a real lead link (≈ 0.5) to the **IOD**,
  which GCMs forecast well (0.91) → hybrid **+0.73/+0.75** (the strongest in the study); Kiremt
  similarly (ENSO, hybrid +0.58).
- **Nigeria (skill limited), two modes:** the **Middle Belt** *has* a lead link (0.28) to the
  Atlantic Niño, but the models forecast that Atlantic index **poorly (0.27)** → hybrid fails; the
  **Sahel** Atlantic-gradient lead link is ≈ 0; and **OND** has a forecastable driver (IOD 0.91) but
  a weak Nigeria lead link (0.16). The well-forecast and rainfall-relevant oceans are, for this
  predictand, largely different.
- **MAM long rains (low predictability):** the *lead* link is ≈ 0 — a genuinely low-skill season
  (controls less SST-mediated: Walker/Congo winds, MJO), not a configuration artifact.

*(All n≈24; only the OND and Kiremt hybrid values clearly exceed the sampling-noise floor. The
concurrent reference is an upper bound and, for the IOD, partly diagnostic — the lead column is the
realistic predictability. See [`docs/14`](14_limitations_and_caveats.md).)*

## 6. Kenya — the third regime, and the limit of predictability

Kenya is the canonical Greater-Horn bimodal country (MAM long rains + OND short rains
everywhere, plus a western/equatorial summer plateau near Lake Victoria) and the region Funk
*designed the WVG for*. Run identically (`AREA=kenya`), it adds the two extreme cases:

- **OND short rains — the most predictable season in the entire study.** The IOD ceiling is the
  highest anywhere (OND North **0.57**, National 0.54, South/Central 0.51–0.52), the MME has
  **real skill** (OND National GROC **0.708**, RPSS **+0.19**, r +0.48; OND South GROC 0.699,
  r **+0.54**, Indian-Ocean domain), and the **hybrid reaches +0.75/+0.69** (IOD forecast 0.91,
  ceiling 0.86). Same signature as Ethiopia's OND, but stronger — the relevant ocean (Indian/IOD)
  is forecastable, so every layer works.
- **MAM long rains — low SST-based predictability.** The perfect-prognosis benchmark is ≈ **0**
  (0.00–0.08 for every predictor, the WVG included), and the MME (GROC 0.525) and hybrid (−0.05)
  follow suit. This is the well-known East African "long-rains problem" — a *structurally low-skill*
  season. Note this means the season is hard to predict *from SST at seasonal lead*, **not** that it
  is driverless: its controls (Congo/Walker zonal winds, the MJO, Gulf-of-Guinea/Sahel circulation)
  are less SST-mediated and harder to forecast. It is a *third*, distinct low-skill mode from
  Nigeria's — weak SST-based predictability rather than an unforecastable SST driver.

(The WVG does surface for Kenya's minor **JAS** western/equatorial rains — JAS Central wvg3 0.37 —
consistent with its Pacific-gradient lineage, but the dominant Kenyan seasons are MAM/OND.)

## Bottom line — a diagnostic ordering of forecast viability (not a law)

> **Read as a diagnostic, not general conclusions.** These are best-of-search, cross-validated but
> configuration-specific rankings over short records; they carry winner's-curse and sampling-noise
> risk, and the benchmark is empirical, not a theoretical limit. See
> [`docs/14_limitations_and_caveats.md`](14_limitations_and_caveats.md). Only the strongest,
> mechanism-supported results (East African OND short rains) should be treated as robust.

Run identically on three countries, the framework *orders* the seasons consistently and points at
*why*, using a physically-motivated lens rather than a hard rule:

| Regime | Example | Statistical SST→rain link | Driver forecastable by GCMs? | Real MME / hybrid | Reading |
|---|---|---|---|---|---|
| **Skill realized** | **Ethiopia Kiremt & OND; Kenya OND short rains** | strong (benchmark 0.7–0.86) | yes (ENSO 0.83 / IOD 0.91) | MME GROC 0.70–0.73, RPSS>0; hybrid +0.58…+0.75 | dynamical value present (robust for OND) |
| **Skill limited** | Nigeria monsoon | present (0.3–0.5) | **less so** (Atlantic ~0.28) | marginal; hybrid ≤ 0 | marginal *for this ensemble/predictand* — not impossible; bias treatment/coupling/regionalization may help |
| **Low SST predictability** | **Ethiopia/Kenya MAM long rains** | **weak** (benchmark ≈ 0) | n/a | ~no skill | structurally low-skill; drivers less SST-mediated (Congo/Walker winds, MJO), **not** driverless |

Nigeria's monsoon and the MAM long rains are two *different* low-skill modes — worth distinguishing
because they imply different directions (better Atlantic SST forecasts / bias treatment vs. process
predictors beyond SST). The "skill realized" regime is where defensible operational value sits.

Used cautiously, the three-country ordering supports a **per-region diagnostic lens**:
*how strong is the statistical SST→rainfall link, and how well can GCMs forecast the ocean index
that carries it?* — computed automatically per region from the observation-only screen + hybrid
decomposition. It **helps diagnose where SST-based seasonal skill appears to be realized, where it
is limited, and why**, and it *orders* the seasons in a way consistent with the literature: it
recovers the documented Western-V-Gradient–East-Africa relationship (well-ranked for Ethiopia's
Kiremt and Kenya's JAS, poorly for Nigeria — a consistency check, not a discovery), the
El-Niño-associated Kiremt drought, and the IOD-associated Greater-Horn short-rain floods, with the
Kenyan OND short rains the highest-benchmark season examined. That per-region, mechanism-aware
diagnostic — *which ocean, which method, how forecastable, how close to the benchmark* — produced
by re-pointing one config across three countries, is the autoscience contribution the AGU abstract
argues for. It is a **diagnostic framework, not a set of general laws**: the rankings are
best-of-search over n≈24–33 and one configuration, so only the strongest, mechanism-supported
results (East African OND) are robust; the rest are hypotheses for multiplicity-controlled,
out-of-sample confirmation (see [`docs/14`](14_limitations_and_caveats.md)).

## Reproducing

Everything here is the *same code* as the Nigeria study, run with `AREA=ethiopia` or `AREA=kenya`:

```bash
AREA=kenya python src/fetch_data.py chirps      # Kenya CHIRPS (~18 min)
AREA=kenya python src/seasons.py                # + teleconnections, feature_discovery,
AREA=kenya python src/composites.py             #   synthesize_recipes, mme_search,
AREA=kenya python src/hybrid_forecast.py        #   ... the whole pipeline
```

Outputs are `*_ethiopia.{png,csv,md}` / `*_kenya.{...}` alongside the Nigeria ones; Nigeria's files
are unchanged. Adding a fourth country is one entry in [`src/areas.py`](../src/areas.py).
