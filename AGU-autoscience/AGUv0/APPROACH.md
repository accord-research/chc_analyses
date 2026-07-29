# APPROACH — autoscience as a search over forecast/downscale configurations

This document describes *how* the Nigeria study works as an automated science loop, and why
the Rosetta + DeepScale stack is the enabling substrate. It is the methods narrative behind
the [`ABSTRACT.md`](ABSTRACT.md); the concrete search space lives in
[`docs/04_experiment_design.md`](docs/04_experiment_design.md).

## The core idea

Operational seasonal forecasting embeds dozens of design choices — the season to target,
the predictor variable and domain, whether to use raw SST fields or teleconnection indices,
the calibration method, the model ensemble, the downscaling technique, the target
resolution, the lead time. Today these are set by convention and expert judgment, fixed per
RCOF, and rarely re-optimized per country/season. They *could* be searched, but the cost of
re-plumbing data and code for each variation has made systematic search impractical.

The claim of this work is that the **modularity of the stack removes that cost**, turning
forecast design into a tractable optimization:

- **Rosetta** makes every dataset reachable through one `fetch(product, variable, region,
  init, target, hindcast, ...)` call with normalized xarray output. Swapping SST domain,
  predictand region, model, or resolution is an argument change, not a new download script.
- **DeepScale** makes every method reachable through one interface —
  `downscale(method=...)`, `calibrate(method=...)`, `ensemble(strategy=...)`,
  `skill(metrics=...)`, `optimize(methods=[...])` — over the same xarray contract. Swapping
  CCA for logit-on-indices, or BCSD for rank-analog, is an argument change.
- Because inputs and methods share a contract, **a single driver can build, run, and score
  an arbitrary configuration from a dict**, and every configuration is scored identically
  under leave-one-year-out cross-validation. That is the precondition for automated search.

So the "experiment" is not one forecast — it is a *function* from a configuration dict to a
cross-validated skill record, and autoscience is the search over the domain of that
function.

## The loop

```
        ┌─────────────────────────────────────────────────────────────┐
        │  propose configuration  (agent / grid / greedy / BO)         │
        │    {season, init, predictand, predictor, index, calib, MME,  │
        │     downscale, resolution}                                   │
        └───────────────┬─────────────────────────────────────────────┘
                        │  dict
                        ▼
        Rosetta.fetch(...)  ──►  DeepScale.calibrate/downscale/ensemble(...)
                        │
                        ▼
        DeepScale.skill(...) under LOYO  ──►  skill record (maps + scalars)
                        │
                        ▼
        score, log to EXPERIMENT_LOG, update belief about the space
                        │
                        └────────────►  propose next configuration
```

Three properties make the loop efficient rather than brute-force:

1. **Physical priors prune the space.** Before any GCM is calibrated, an *observation-only*
   screen (`src/teleconnections.py`) ranks candidate SST indices and domains by their
   pre-season correlation with each season/zone's rainfall. Predictors that carry no
   observed signal are dropped, collapsing axes F/G by orders of magnitude. This is the
   cheap step that makes the expensive step small.
2. **Near-separable axes are searched in stages** (seasons → predictors → calibration/MME →
   downscaling → lead), each holding the others at a default, before a final joint refine.
3. **The agent carries the interpretation between stages.** It reads a stage's skill record,
   forms a hypothesis ("Atlantic gradient dominates the Guinea-coast AMJ signal; ENSO
   dominates the Sahel JAS signal"), and proposes the next configurations to test — an
   analyst's reasoning loop made mechanical and logged.

## What is genuinely automated vs. human-set

| Human sets once | Automated per run |
|---|---|
| The country and the CHIRPS predictand product | Season windows (discovered from data) |
| The candidate axes and their allowed values (`config.yml`) | Which index/domain/method/MME/resolution wins |
| The scoring objective and CV protocol | The skill map, conditional skill, resolution/skill frontier |
| Physical sanity checks (does the winning predictor make sense?) | The ranking and the next configuration to try |

The human defines the *space* and the *objective*; the loop searches and scores. The final
guardrail is physical: a winning configuration must have an interpretable mechanism (an
Atlantic-gradient predictor for the Sahel is credible; a spurious high-latitude SST box is
not), which is exactly the convergence-of-evidence discipline inherited from the CHC
Ethiopia work.

## Provenance and reproducibility

- Every run appends to [`EXPERIMENT_LOG.md`](EXPERIMENT_LOG.md): config key, git SHAs of
  Rosetta/DeepScale, data window, and the resulting skill record path.
- All raw data is fetched (never hand-copied) through Rosetta, so any run is reconstructible
  from `config.yml` + the two library versions.
- Because the harness is country-agnostic, re-pointing `config.yml` at the Greater Horn of
  Africa should recover the known "WVG predicts East African rainfall" result — the built-in
  reproducibility check that the method, not the Nigeria tuning, is what generalizes.

## Why this is the right AGU story

The contribution is not a better Nigeria forecast per se; it is a demonstration that the
**design of a seasonal forecast is itself a searchable, automatable object** when the data
and method layers are modular. Nigeria — with its coexisting bimodal-coast and
unimodal-Sahel regimes and its competing Atlantic/Pacific/Indian drivers — is a demanding
single-country testbed precisely because no one global configuration is optimal across it,
so the value of *per-season, per-zone, per-lead* search is visible in one country.
