"""nullperm.py — SPEC Amendment 1: the complete-season target permutation.

WHY v1's NULL WAS WRONG. v1 permuted the rainfall FIELD by whole calendar years and
re-ran discovery. Moving 12-month blocks keeps each calendar year intact, but a season is
not a calendar year: a wrapping window such as NDJ takes November and December from year
Y-1 and January from year Y. After a calendar-year permutation those two halves come from
two unrelated donor years, so the null's "observations" are spliced seasons that never
occurred. The real atlas is scored on complete seasons; a null scored on spliced ones is
not the same measurement. v1's own runs happened to discover only non-wrapping windows,
which hid the defect rather than removing it.

WHAT REPLACES IT. The permutation acts on the season-year axis of the TARGET, after each
zone-window's complete seasonal totals have been assembled:

  1. Zones and windows are discovered from each fold's UNPERMUTED training rainfall.
  2. One `numpy.random.default_rng(4242)` is drawn from ONCE and yields all 200
     permutations sequentially, so replicate r is reproducible and the arms are paired.
  3. The same year permutation is applied to every zone-window seasonal target series in
     the fold, so cross-zone and cross-window donor-year alignment is exact.
  4. SST is untouched, and condition membership (SPEC 8) is therefore untouched too: a
     test year is a La Nina year in the null exactly when it is one in the real run.
  5. Predictor and lead selection, the regression, the residual spread and the tercile
     thresholds are all re-fitted inside every replicate.

WHY DISCOVERY IS NOT PERMUTED, AND WHY THAT IS CORRECT RATHER THAN CONVENIENT. The null
exists to price a skill-selected search. Zone discovery and window detection consult
neither SST nor any score -- they see rainfall alone -- and SPEC 10 forces EVERY
discovered zone-window into the report, so nothing is retained because it scored well.
Discovery is therefore not a skill-selected axis and there is no selection there to pay
for. The axis that IS skill-selected is predictor and lead, chosen by inner LOYO from 20
candidates per zone-window, and the null re-runs exactly that.

DONOR-YEAR ALIGNMENT. Windows differ in their usable years, because a deep lead on an
early window can fall before the SST record (MAM loses 1981, OND does not). To keep one
donor map valid for every window, the fold restricts every zone-window to the COMMON
usable year set. No test year is ever lost -- the earliest walk-forward test year is 2002
-- and at most one early training year is dropped from the windows that would have had
it. The real run uses the identical restriction, so real and null share their support.

The calendar-year field permutation survives as `sensitivity_field_perm`, clearly
labelled, with its wrapping-season limitation stated wherever it is reported.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "harness"))

from africas2s.metrics.rpss import _cpt_boundaries      # noqa: E402
import indices as IX                                    # noqa: E402
import atlas_score as A                                 # noqa: E402

SEED = 4242
N_REPS = 200


def permutations(n_years, n_reps=N_REPS, seed=SEED):
    """All replicates from ONE rng, drawn sequentially. Replicate r is permutations()[r]."""
    rng = np.random.default_rng(seed)
    return [rng.permutation(n_years) for _ in range(n_reps)]


def common_usable(part, monthly, month_of_col, year_of_col, years, sst,
                  forced_windows=()):
    """The season-years usable by EVERY zone-window this fold will forecast.

    One shared support is what makes a single donor map coherent across windows.
    """
    pairs = A.zone_window_list(part, forced_windows)
    ok_all = np.ones(len(years), dtype=bool)
    for (lab, months) in {(l, m) for _, l, m, _ in pairs}:
        mlist = list(months)
        ok_all &= IX.coverage_mask(sst, mlist, years)
        for z in range(part.k):
            cells = part.zone_cells(z)
            if len(cells) == 0:
                continue
            w = part.weights[part.labels == z]
            _, ok = IX.season_totals(monthly, month_of_col, year_of_col, cells, w,
                                     mlist, years)
            ok_all &= ok
    return np.flatnonzero(ok_all)


def score_fold_target_perm(part, monthly, month_of_col, year_of_col, years, train_years,
                           test_years, sst, usable, perm=None, arm="zones-specific",
                           leak=False, forced_windows=(), weight_rule="equal"):
    """One fold, scored on the shared support, with an optional target permutation.

    `perm` is a permutation of range(len(years)); it is restricted to `usable` by rank
    order, which gives one donor map used identically by every zone-window. `perm=None`
    is the real run and takes the identical code path, so real and null differ in exactly
    one thing.
    """
    pairs = A.zone_window_list(part, forced_windows)
    wmap = (A.fold_weights(part, pairs) if weight_rule == "equal"
            else A.rainfall_share_weights(part, pairs))

    tr = np.array([i for i in usable if years[i] in set(train_years)], dtype=int)
    te = np.array([i for i in usable if years[i] in set(test_years)], dtype=int)
    if len(tr) < 10 or len(te) == 0:
        return []

    # ONE donor map for the whole fold: the rank-restriction of `perm` to `usable`.
    if perm is None:
        donor = {int(i): int(i) for i in usable}
    else:
        order = usable[np.argsort(perm[usable], kind="stable")]
        donor = {int(u): int(d) for u, d in zip(usable, order)}

    by_window = {}
    for z, lab, months, disc in pairs:
        by_window.setdefault((lab, months), []).append((z, disc))

    out = []
    for (lab, months), zlist in by_window.items():
        mlist = list(months)
        ys = {}
        for z, _ in zlist:
            cells = part.zone_cells(z)
            w = part.weights[part.labels == z]
            v, _ = IX.season_totals(monthly, month_of_col, year_of_col, cells, w,
                                    mlist, years)
            if perm is not None:
                vv = v.copy()
                for u in usable:
                    vv[u] = v[donor[int(u)]]
                v = vv
            ys[z] = v

        comps = {g: IX.raw_components(sst, mlist, years, g) for g in IX.LEADS}
        z_fit = np.arange(len(years)) if leak else tr
        X = np.array([IX.compose(n, comps[g], z_fit) for n, g in A.FEATURE_KEYS])

        chosen = {}
        if arm == "zones-shared":
            pooled = np.zeros(len(A.FEATURE_KEYS))
            for z, _ in zlist:
                mse, _ = A._loyo_mse_block(X, ys[z], tr)
                var = np.var(ys[z][tr]) or 1.0
                pooled += wmap[(z, lab)] * np.minimum(mse / var, 1e6)
            best = int(np.argmin(pooled))
            for z, _ in zlist:
                chosen[z] = best
        else:
            for z, _ in zlist:
                mse, _ = A._loyo_mse_block(X, ys[z], tr)
                chosen[z] = int(np.argmin(mse))

        for z, disc in zlist:
            key = chosen[z]
            fname, gap = A.FEATURE_KEYS[key]
            y = ys[z]
            t33, t67 = _cpt_boundaries(y[tr])
            if arm == "climatology":
                p = np.full((len(te), 3), 1.0 / 3.0)
                rc = A.climatology_rps(y[te], t33, t67)
                rf = rc.copy()
            else:
                fit = A._fit_predict(X[key], y, tr, te)
                if fit is None:
                    p = np.full((len(te), 3), 1.0 / 3.0)
                    rc = A.climatology_rps(y[te], t33, t67)
                    rf = rc.copy()
                else:
                    mu, sigma = fit
                    p, rf, rc = A._probs_and_rps(mu, sigma, y[te], t33, t67)
            out.append(A.Forecast(
                zone=z, window=lab, months=tuple(mlist), weight=wmap[(z, lab)],
                zone_share=part.zone_weight(z) / part.total_weight(),
                index=fname, lead=gap, test_years=years[te], probs=p, obs=y[te],
                rps_f=rf, rps_c=rc, n_train=len(tr),
                loyo_mse=float(A._loyo_mse_block(X[key:key + 1], y, tr)[0][0]),
                discovered=disc))
    return out
