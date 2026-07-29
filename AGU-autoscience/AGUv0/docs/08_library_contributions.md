# Library contributions register — what this work should upstream

**Status: first fixes landed on `_autoscience`; the rest are planned.** The Rosetta R1/R2
fixes are committed on the isolated `_autoscience` branch (`4f76818`, off `_chc`, **not**
integrated); everything else below still lives as a one-off in
[`AGU-autoscience/src/`](../src/). This register is the plan for moving the reusable parts
*into the libraries* (on `_autoscience` only), because that migration is the actual proof of
the AGU thesis: **an autoscience run should leave the stack more capable than it found it.**
Each entry is scoped like the Ethiopia gap register
(`analyses/chc_ethiopia/ROSETTA_DEEPSCALE_MAPPING.md`).

Ordering is by leverage — how much of the autoscience loop each unlocks for *every* future
country/season, not just Nigeria.

## DeepScale — new capabilities

| # | Capability | Prototype (here) | Proposed home | Effort | Notes |
|---|---|---|---|---|---|
| **D1** | **Feature search / predictor ranking** — score a pool of candidate predictors by honest LOYO CV skill, per target; return a leaderboard | `src/feature_discovery.py` | `deepscale.select_features()` / a `feature_search` module | M | The core autoscience primitive. Mostly *composition* of existing `deepscale.cv` (LOYO) + `deepscale.skill`; the new part is the pool abstraction + the discovery-inside-fold contract |
| **D2** | **Data-driven SST-projection predictor** — pre-season covariance pattern with the target, refit inside each CV fold, projected onto held-out year | `loyo_corr_projection()` in `feature_discovery.py` | a calibrate method `method="sst_projection"` or `Index.discovered(...)` | M | Turns "discover a new teleconnection" into a first-class, CV-safe feature. Sits beside `Index.named` |
| **D3** | **Seasonal-regime / partition discovery** — per-pixel harmonic bimodality index + annual-cycle clustering + candidate-window proposal | `src/seasons.py` | `deepscale.climate.seasonal_regimes()` | S–M | `deepscale.climate` already exists; add the harmonic diagnostic + regime label (peak-count, *not* a2/a1 alone — see docs/02 caveat) |
| **D4** | **Tercile-conditioned composites** — composite any predictor field over the driest/wettest tercile years of a target (drought/flood setups) | `src/composites.py` | `deepscale.composite(field, target, by="tercile")` | S | Descriptive diagnostic; complements existing `analog`, `frequency_below` |
| **D5** | **Named Atlantic indices** — `atl3` (Atlantic Niño), `tna`, `tsa`, `atl_grad` (TNA−TSA) added to the named registry | boxes in `src/teleconnections.py` | `deepscale.indices` named registry | S | `Index.named` today has nino34/wvg/roni/dmi; these are standard WAM indices and belong there |
| **D6** | **Persistence / antecedent covariate** — antecedent-window rainfall (or any field) as a predictor series | `persistence_series()` in `feature_discovery.py` | `deepscale.series` feature helper | S | Trivial but generalizes the pool beyond SST |
| **D7** | **MME objective-average helper** — equal-weight mean of {CCA, eReg, logit} tercile probabilities (the GHACOF recipe) | referenced in `src/hindcast.py` | `deepscale.ensemble(strategy="objective_avg")` or a pipeline | S | Needed to wire `hindcast.py`'s `calibration="objective_avg"` path |

## Rosetta — fixes and enhancements (friction hit this session)

| # | Item | What happened | Change | Status |
|---|---|---|---|---|
| **R1** | **NetCDF round-trip conflict** | Fetched datasets carry `time_bnds` + inherited encoding; `to_netcdf` fails with *"NetCDF: String match to name in use"* | Added `normalize.sanitize_for_netcdf()` (fresh rebuild — in-place encoding/bounds clearing does **not** fix it); applied to the returned dataset in `fetch()`, so both the object and `destination=` round-trip | ✅ **DONE** — `_autoscience` `4f76818` |
| **R2** | **Longitude convention footgun** | An SST bbox `lon=[-180,180]` silently returned only `0–180°E`, dropping the Pacific Niño boxes and half the Atlantic; a `[-170,-120]` Pacific box came back empty | Added `normalize.select_lon()`: full-globe→keep all, translate bounds to the source convention, seam-wrap safe. Applied in the OPeNDAP adapter (where the sub-select first happens) + normalize backstop | ✅ **DONE** — `_autoscience` `4f76818` |
| **R3** | **Serial CHIRPS COG download** | `obs/chirps-v3-monthly` pulls one COG/month at `workers=1`, ~3 s each → ~18 min for 33 yr | Expose a `workers` / parallel-download option through `fetch()` (the http adapter already has the arg internally) | pending |

*R1/R2 landed with offline tests (`tests/test_lon_convention.py`, 9 cases); existing
`tests/test_region.py` (23) still passes; CHIRPS-Nigeria http path re-verified unaffected.
`main` (`f21f783`) and `_chc` (`b4084eb`) unchanged — nothing integrated.*

## Not a library change (stays in the analysis layer)

- The *experiment matrix* and *search strategy* (`config.yml`, `docs/04`) — orchestration over
  the libraries, country-specific, belongs here.
- The Nigeria-specific zone/season definitions and the drought/flood atlas — outputs, not
  methods.

## Wiring `hindcast.py` (partly library, partly glue)

The `NotImplementedError` in [`src/hindcast.py`](../src/hindcast.py) is mostly *composition* of
existing DeepScale APIs (`seasonal_mme`, `calibrate(method="ereg"|"logit")`,
`ensemble(strategy=...)`, `skill(cv="loyo")`) plus the multi-model Rosetta fetch/regrid glue.
The only genuinely new library pieces it needs are **D7** (objective-average helper) and,
optionally, **D2** (to feed a discovered feature into the calibration stage). Everything else
is downloads + orchestration.

## Does any of this block current work?

**No.** Every R-item is already worked around in the analysis layer, and every D-item has a
working prototype in `src/` that produced the real results. These contributions are about
*reusability* (the "extensible stack" claim), not about unblocking Nigeria. The only
unfinished piece is wiring `hindcast.py`'s GCM path — independent of these refactors. So:
**store and integrate on their own schedule; keep the science moving.**

## Integration policy — ISOLATED, nothing merged, `main` never touched

**Hard constraints (owner's instruction, 2026-07-17):**
1. **Never touch `main`.** No branch is cut from `main`, no PR targets `main`, `main` never moves.
2. **Leave `_chc` unintegrated.** `_chc` is not merged anywhere and its pointer does not move.
3. **All investigation library changes live on one isolated branch per library, based on
   `_chc`, and are merged *nowhere*.** They accumulate as commits on that branch only.

**Branches (created 2026-07-17).** `_autoscience`, cut off `_chc` in each library:
- rosetta `_autoscience` ← `_chc` `b4084eb`
- deepscale `_autoscience` ← `_chc` `ee84179`

`main` and `_chc` are byte-for-byte unchanged (verified: rosetta `main f21f783`, `_chc
b4084eb`; deepscale `main 984a722`, `_chc ee84179`). The env's editable installs now resolve to
`_autoscience`, so any change is picked up immediately without reinstall.

**Everything bases on `_autoscience` (off `_chc`) — no exceptions.** Even the capabilities that
*could* technically build on `main` (D2/D4/D7) go here instead, because the point is isolation:
one place, nothing on `main`, nothing integrated. The dependency column below is kept only to
record *why* `_chc` is the correct base (the Nigeria pipeline already needs `_chc`'s catalog
and API), not to justify any `main`-based work.

**Working rules on the branch.**
- Atomic, per-capability commits (one D-item per commit or short commit series) so the history
  stays legible and any capability can be split out *later* if the owner ever chooses to
  integrate — that decision is explicitly deferred, not part of this plan.
- Develop the generalized version *inside the library repo* on `_autoscience`; never import
  `AGU-autoscience/src` from the library. Keep the `src/` prototype as the executable spec +
  regression fixture; once a capability exists on the branch, the prototype may import it to
  dogfood.
- Generalization checklist (library validity): remove Nigeria hardcoding (boxes, lat bands,
  `COARSEN`, fixed index names) → parameters; conform to the DeepScale dim contract
  (`year/member/lat/lon`); register in the method/index registry where applicable; add tests
  with synthetic data; handle NaN masks and short records.

### Ledger — where each contribution lives (all on `_autoscience`)

| # | Capability | Edits `_chc`-modified file? | Why `_chc` is the base | Lands on |
|---|---|---|---|---|
| D1 | Feature search / ranking | new module | uses `Index.named` (wvg → `_chc` indices) | `_autoscience` |
| D2 | SST-projection predictor | new file | isolation policy (pure xarray otherwise) | `_autoscience` |
| D3 | Seasonal-regime discovery | `climate.py` (`_chc`-only) | file only exists on `_chc` | `_autoscience` |
| D4 | Tercile composites | new file | isolation policy | `_autoscience` |
| D5 | Named Atlantic indices | `indices.py` (`_chc` +474 lines) | `_chc` expanded this file | `_autoscience` |
| D6 | Persistence covariate | `series.py` (`_chc`-only) | file only exists on `_chc` | `_autoscience` |
| D7 | Objective-avg MME | `ensemble.py` (on main) | isolation policy | `_autoscience` |
| R1–R3 | Rosetta fixes | `http/opendap/fetch/catalog` (all `_chc`) | `_chc` changed these files | `_autoscience` |

*Note:* the products this analysis fetched (`obs/ersst-v5`, `obs/chirps-v3-monthly`) live in the
**`_chc` catalog**, not `main` — the Nigeria pipeline depends on `_chc` today, which is exactly
why `_chc` (not `main`) is the base for the isolated branch.

**If integration is ever wanted (out of scope now).** Because `_chc` is a clean linear superset
of `main`, `_autoscience` could later rebase/merge through `_chc`; but per the constraints above
that is deferred and not done here.
