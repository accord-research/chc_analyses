# Rolling Indian Ocean SST & IOD Forecasts — scope

A weekly-refresh product predicting western and eastern Indian Ocean SST fields, their box
indices, and the Dipole Mode Index at five lead horizons — and what we would have to build
in acmadDL and africas2s to make it run.

| | |
|---|---|
| **Requested by** | Funk & Shukla (CHC) |
| **Primary model** | ECMWF S2S |
| **Verification** | NOAA OI SST |
| **Baseline** | 2006–2025 |
| **Reference materials** | `chc-reference-materials/` (Funk's two cdsapi scripts + the October rains deck) |
| **Index definitions** | `../chc_ethiopia/2_OND_ocean_state_outlook_v2.ipynb` |

---

## 1. What is being asked for

Five products, each at five lead horizons, refreshed weekly. Funk's reply settles the time
question: *"next 30 days, and next 1, 2, 3, 4 weeks."* He also asks explicitly that the west
and east boxes be carried as **separate results** and then combined, rather than only
reporting the dipole difference.

| Target | Next 30 d | Week 1 | Week 2 | Week 3 | Week 4 |
|---|:--:|:--:|:--:|:--:|:--:|
| SST field — west box | ● | ● | ● | ● | ● |
| SST field — east box | ● | ● | ● | ● | ● |
| WIO index (absolute °C) | ● | ● | ● | ● | ● |
| EIO index (absolute °C) | ● | ● | ● | ● | ● |
| DMI / IOD (anomaly °C) | ● | ● | ● | ● | ● |

> **Settled.** Our email said "next 30 days, and next 1, 2, 3 weeks"; Funk's reply says
> 1, 2, 3, *and* 4 weeks. **Week 4 is in** — all five horizons above. It is nearly free
> once weeks 1–3 exist, since the 46-day S2S range covers it.

---

## 2. The indices, as already defined in our code

Three of the five already exist in `2_OND_ocean_state_outlook_v2.ipynb`. The boxes are the
standard Saji et al. (1999) Dipole Mode Index poles, and the deck confirms CHC uses the
same ones.

```
        30°E      50°E      70°E      90°E     110°E
  25°N ┌───────────────────────────────────────────┐
       │                                           │
       │         ┌─────────────┐                   │
       │         │  WEST POLE  │                   │
   0° ─┼─ ─ ─ ─ ─│─ ─ ─ ─ ─ ─ ─│─ ─ ─ ─┌───────────┤─ equator
       │         │  50–70°E    │       │ EAST POLE │
       │         │  10°S–10°N  │       │ 90–110°E  │
       │         └─────────────┘       │ 10°S–0°   │
       │                               └───────────┘
  25°S └───────────────────────────────────────────┘
```

The east box is the asymmetric one — it stops at the equator.

**WIO — western pole.** `[-10, 10, 50, 70]`, `transform="raw"`, `weights="cos_lat"`.
Exists today as `wio_index`. Absolute temperature, deliberately not an anomaly, so the
deck's ~29 °C threshold stays meaningful.

**EIO — eastern pole.** `[-10, 0, 90, 110]`, `transform="raw"`, `weights="cos_lat"`.
**New.** Trivially built: take the WIO recipe and swap in the DMI east box. Roughly six lines.

**DMI / IOD.** Already exists as `dmi_index` — `west − east`, each an `anomaly` with
`cos_lat` weights against the configured baseline.

> Note the DMI is *not* simply `WIO − EIO` as those two are defined: the indices are
> absolute, the dipole is built from anomalies. Keep all three so the poles and the
> difference can be read independently, which is exactly what Funk asked for.

---

## 3. What we already have

Better than expected. The ECMWF S2S route is already built in acmadDL — including the
reforecast suite, which is the part that is normally painful.

| Capability | Status | Where it stands |
|---|---|---|
| `c3s/ecmwf-s2s` | **have** | Catalogued against the ECMWF ECDS endpoint (`ecds.ecmwf.int/api`), `s2s-forecasts`, `origin=ecmwf`, `perturbed_forecast`, `level_type=single_level` — the same request shape as Funk's own script. 1.5° grid, 50 forecast members. |
| `sst` variable | **have** | Declared on the S2S product: `sea_surface_temperature`, K → K. No conversion work needed. |
| Reforecast suite | **have** | `fetch(..., reforecast=True)` switches the collection to `s2s-reforecasts` and `perturbed_reforecast` — the adapter comments note the realtime collection's reforecast flag is broken upstream, and this route works around it. |
| Hindcast window default | **have** | Defaults to `(init_year − 20, init_year − 1)` = **2006–2025** for a 2026 init. Exactly the window Funk's follow-up email corrects to. |
| Lead axis + hindcast shape | **have** | `normalize` maps `step → lead_time` and converts the reforecast `hdate` axis to integer `year`, yielding the standard `(year, member, lead_time, lat, lon)` convention. Default leads `0/to/1104/by/24` — 46 days, covering all five horizons. |
| Index machinery | **have** | `africas2s.Index.custom` with regions / combine / transform / cos_lat weights. `reduce()` already accepts a `time` dim, not just `year`. |
| Uncertainty + skill | **have** | `error_bounds`, `skill`, `quantile_map`, `plot_field`, `plot_index_scatter` — all already used by the OND notebook. |

---

## 4. What has to be built

Five gaps. Only the first is genuinely on the critical path; the rest are contained.

| Gap | Status | What it takes |
|---|---|---|
| NOAA OI SST | **missing** | **The blocker.** Funk wants regression against NOAA OI, and the deck's own baseline is "1981–2025 NCEI Optimal Interpolation SST". Our only SST observation is `obs/ersst-v5` — 2°, *monthly* — which cannot verify a one-week lead. Need OISST v2.1 daily 0.25° added as a new catalogued product. The good news: it lives on the same PSL THREDDS server as ERSSTv5, so the existing `opendap` adapter pattern should carry over almost directly. |
| Lead-window aggregation | **missing** | `seasonal_reduce` is calendar-month based and collapses to a `year` dim — wrong shape here. Need a helper that averages a `lead_time` axis over day windows (1–7, 8–14, 15–21, 22–28, 1–30). Small, self-contained addition to africas2s. |
| Daily climatology / anomaly | **missing** | The DMI needs anomalies. At seasonal scale the baseline is a set of years; at daily/weekly scale it must be a day-of-year (or lead-window) climatology, computed separately for the model and the observations. No day-of-year climatology helper exists today. |
| Simple regression calibration | **partial** | `calibrate()` offers `ereg` and `logit`, both year-indexed and tercile-oriented. Funk explicitly prefers plain regression against OI values over Harrison's quantile matching, "particularly appropriate given climate change" — so a per-cell and per-index OLS fit across the ~20 reforecast years, per lead window, fitted separately for west and east. Thin new code, but it should not be forced through the seasonal API. |
| GEFSv12 SST | **missing** | Not in the catalog at all — the only GEFS presence is `chc/chirps-gefs-*`, which is CHC's bias-corrected *precipitation*, not raw GEFS SST. Funk's steer makes this optional: *"If we had to choose... I think most Africans would prefer ECMWF. Just ECMWF alone would be great."* Recommend deferring. |

### Two unknowns to verify live before committing to a schedule

- The S2S branch of the CDS adapter never sends `hyear`/`hmonth`/`hday`, which Funk's
  hindcast script sets explicitly. The computed date range does not reach the request, so we
  are relying on whatever ECDS returns by default. It may well be all 20 years — the `hdate`
  handling in `normalize` implies it — but this is unproven.
- `sst` is declared on `c3s/ecmwf-s2s` but **never exercised**: every S2S test covers
  `precip` only. First real task is a single live fetch of both suites.

---

## 5. Proposed pipeline

One weekly run, driven by the most recent ECMWF extended-range init:

1. **Fetch** the real-time S2S SST forecast for the current init, region `[-15, 15, 45, 115]`
   — a single box covering both poles with margin.
2. **Fetch** the matching reforecast suite for the same calendar init, 2006–2025, giving
   ~20 years × 11 members × 46 leads.
3. **Aggregate** both to the five lead windows.
4. **Fetch** OISST for the corresponding historical valid windows — the regression target.
5. **Fit** per lead window, separately for west and east: OLS of observed on ensemble-mean
   forecast across the 20 reforecast years. Apply to the live forecast.
6. **Derive** WIO and EIO from the calibrated absolute fields; derive DMI from the
   calibrated anomalies — **twice, once per climatology** (see below).
7. **Report** calibrated SST fields, the three index values with error bounds, and
   leave-one-year-out skill per lead — with DMI carried as a pair of results, one per
   climatology, side by side.

### Both climatologies, reported separately

DMI is an anomaly index, so it inherits whatever baseline the anomaly is taken against.
We compute **both** and present them per climatology rather than picking one:

| Climatology | Built from | Property |
|---|---|---|
| **Model** | The 2006–2025 reforecast ensemble, per lead window | Self-consistent with the forecast — removes the model's own lead-dependent SST bias, so the anomaly is "warm relative to what this model usually predicts at this lead". |
| **Observed** | NOAA OI SST over the same 2006–2025 window | Anchored to reality — the anomaly is "warm relative to what the ocean actually does", which is the framing the deck's warmest-on-record language uses. |

Reporting both is cheap once the day-of-year climatology helper exists (it is the same
function applied to two inputs), and the spread between them is itself diagnostic: a large
gap means the model carries a lead-dependent bias that the regression is having to absorb.
WIO and EIO are absolute °C and are unaffected — they have no baseline.

Because the reforecast is keyed to the calendar init, the training sample is re-fit every
run — which is the right behaviour, and also why each run is self-contained and cacheable.

---

## 6. Plan

Sequenced so the riskiest unknown — whether the S2S SST route actually returns data — is
settled first, before any modelling work is built on top of it.

**01 · Prove the data route.** One live fetch of `c3s/ecmwf-s2s` `sst`, forecast and
reforecast, for a recent init over the IO box. Confirm member counts, lead coverage, the
`hdate → year` conversion, and how many hindcast years actually come back without an
explicit `hyear`.
→ *Output:* a go/no-go note; an adapter fix for `hyear` if the default is wrong.

**02 · Add NOAA OI SST to acmadDL.** ✅ **DONE — PR #12.** Bigger than this plan first
estimated: not a catalog addition but an adapter feature. PSL serves OISST one file per
calendar year with no aggregation endpoint, and the opendap adapter substituted only
`{base}`/`{native_name}`, so `url_template` gained a `{year}` placeholder and a per-year
open/region-slice/concat path. The DAP ceiling bit twice, not once — across years *and*
within a single year (~50 MB fails), so each year loads in 90-day blocks.
→ *Output:* PR #12. Verified live: 731 daily steps, 0.25°, °C, 89.9% finite.

**03 · Lead-window aggregation + daily climatology.** ✅ **DONE — africas2s PR #9.**
`lead_window_reduce` (collapses `lead_time` to a `window` dim; reads lead units from the
axis rather than assuming; refuses an incomplete window), `doy_climatology`/`doy_anomaly`
(with year-boundary-wrapping smoothing), and the `eio` index — which belonged in the index
registry, not the notebook, since `setio` already existed as its anomaly counterpart.
→ *Output:* PR #9, 18 tests, 1014 passing offline.

**04 · Hindcast experiment.** ✅ **DONE — and the answer is all five horizons.** Skill is
quoted leave-one-year-out throughout, and against a **persistence baseline**, because SST is
so autocorrelated that a bare correlation says almost nothing. The model beats persistence at
every horizon and the gain *widens* with lead:

| | week1 | week2 | week3 | week4 | days 1–30 |
|---|---|---|---|---|---|
| WIO model r | 0.88 | 0.87 | 0.76 | 0.72 | 0.82 |
| WIO persistence r | 0.85 | 0.66 | 0.60 | 0.64 | 0.74 |
| EIO model r | 0.88 | 0.91 | 0.82 | 0.77 | 0.90 |
| EIO persistence r | 0.83 | 0.58 | 0.33 | 0.31 | 0.57 |

Weeks 3–4 in the east are where the model earns its keep — persistence collapses to r≈0.31
while the model holds 0.77. Week 1 is the honest caveat: barely better than persistence.

**05 · Executed notebook, one real init.** ✅ **DONE.** `IOD_forecast.py` (percent source) →
`IOD_forecast.ipynb`, executed clean, 3 figures. Reproduced on a second independent init
(2026-09-03) with consistent results. Per-cell field calibration included, with low-skill
cells greyed rather than shown.
→ *Output:* notebook + `outputs/{indices,dmi}_<init>.csv`, `calibrated_fields_<init>.nc`.

**06 · Weekly automation.** Not started. The pipeline is already parameterised on init date
(`iod_pipeline.run(init)`), so this is scheduling plus output archiving.

## Findings worth carrying forward

* **A poisoned cache entry** from any pre-PR-#11 S2S sst fetch keeps being served, because
  the raw cache key omits `leadtime_hour`. Symptom: `lead_window_reduce` reports no
  `lead_time` dimension. Delete the entry under `~/.nuthatch/caches/acmaddl/` or fetch once
  with `cache=False`.
* **Field and index calibration disagree by 0.1–0.3 °C** on WIO. Fitting per cell then
  area-averaging is not the same operation as fitting the area-average once slopes vary
  across the box. Quote the index table for an index; the maps are for spatial pattern.
* **One global `~/.cdsapirc` cannot hold both endpoints.** While it holds the ECDS key,
  Copernicus products fail — this silently broke an unrelated agreement test in africas2s.
  Restore from `~/.cdsapirc.copernicus.bak` when needed; the real fix is per-endpoint
  credential resolution in acmadDL's `cds` adapter.
* **The interval is historical, not ensemble-based.** The 80% band comes from regression
  residuals over 20 years, so it reflects past error rather than this week's ensemble
  disagreement. With 100 real-time members a spread-aware interval is the natural upgrade.

## 7. Open questions

**For Funk & Shukla**

- **Windows relative to init, or to calendar?** "Next 30 days" from a Monday init is a
  different window than "the month of October". The rolling reading is assumed here.
- **Is planette.ai worth pursuing now?** Shukla's pointer to cloud-hosted reforecasts
  addresses exactly the CDS slowness Funk describes — but our ECDS route already works, so
  this is an optimisation, not a dependency. Worth a look mainly for the "harvest
  cloud-hosted forecasts for Rosetta" ambition.

**Internal**

- **Deterministic or probabilistic?** Everything above assumes a calibrated ensemble mean
  plus error bounds. With 50 real-time members, tercile probabilities per box are also
  reachable — but nobody has asked for them yet.

**Settled**

- ~~Week 4 in or out?~~ **In** — five horizons.
- ~~Which climatology for anomalies?~~ **Both**, reported per climatology (§5).

---

## 8. Development workflow

Two different rules apply here, deliberately.

**The analysis stays local and uncommitted.** Everything under
`experiments/IOD-forecasting/` — this scope, the notebook, cached fetches, figures —
stays uncommitted until we have something functional. Nothing else consumes it, so there
is no cost to leaving it dirty.

**Library changes do not get that treatment.** `libraries/acmadDL` and
`libraries/africas2s` are editable-installed into `accord-chc` and shared across sessions,
so whatever branch a checkout sits on *is* the code every runtime and notebook executes,
and an uncommitted edit there can be erased by another session's `checkout`/`reset`. That
is exactly the failure mode `ACCORD/CLAUDE.md` exists to prevent, so the two library
additions in this plan follow the 5-step loop even while the analysis stays local:

```bash
cd libraries/acmadDL
git fetch && git switch main && git pull --ff-only    # 1. start from current main
git switch -c feat/iod-oisst-daily                    # 2. one branch, off main
#   ... add obs/oisst-v2 to catalog.yaml ...
git commit -am "catalog: NOAA OI SST v2.1 daily"      # 3. commit immediately
git push -u origin feat/iod-oisst-daily               # 4. push + PR
gh pr create --base main --fill
#   ... test — the change is live because the branch is checked out ...
git switch main && git pull && git branch -d feat/iod-oisst-daily   # 5. after merge
```

Same loop, separate branch and PR, in `libraries/africas2s` for the lead-window
aggregation, day-of-year climatology, and EIO index. **Two changes, two branches, two PRs**
— they are independent and should not be bundled.

### Access facts that shape this

- **We have admin on both repos** (verified 2026-09-04: `push=true admin=true`). Branch,
  push, and PR all go to `origin`; no fork is involved. The `fork` remotes on both
  checkouts (`emmettFC/rosetta`, `emmettFC/deepscale`) are now vestigial and can be removed.
- **Neither `main` is branch-protected.** Nothing *enforces* the PR flow — a push straight
  to `main` would silently succeed. The protocol is ours to honour, not the server's to
  impose. Worth turning on protection so the rule is real.
- **Timing of the PR.** The protocol says push and open the PR immediately. The *push* is
  non-negotiable — it is what stops work living only in a working tree. The PR itself is
  reasonably held (or opened as a draft) until phase 01 proves the route, so we are not
  asking reviewers to look at an adapter nobody has run.

### One judgement call

Developing on a branch in the shared canonical checkout means every other session's
notebooks get our branch while we work. For an additive catalog entry — a new product key,
touching nothing existing — that risk is low and a branch in place is fine. If it turns out
we have to modify the shared CDS adapter (e.g. the `hyear` fix from §4), that is no longer
additive, and it should move to a worktree instead:

```bash
git worktree add ../acmadDL-iod -b feat/iod-s2s-hyear origin/main
```
