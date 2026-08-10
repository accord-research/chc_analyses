"""secondary.py — SPEC 13's two secondary benchmarks.

They answer different questions from the primary one and never replace it.

A. FIXED REGIONAL AREA-MEAN. The predictand is one number per year: the cos(lat)-weighted
   month-summed rainfall over ALL valid cells of the domain. Discovered zones are
   MODELLING PARTITIONS -- each zone gets its own recipe, zone predictions are combined
   in the continuous domain, and the aggregate is converted to tercile probabilities
   using inner-LOYO residual spread. This is v4zeek's candidates/search_zones.py
   contract, inherited.

   Because the predictand is identical across arms, this IS the controlled comparison
   that SPEC 10 is not, and it is the direct re-test of v4zeek's f:19.

B. FIXED GRIDDED FIELD. Every candidate emits below/near/above probabilities on the
   common 0.25 deg valid-cell grid; a zonal candidate broadcasts its zone forecast to
   every cell in that zone. Each cell is scored against its OWN train-fitted tercile
   boundaries of its own seasonal total, pooled with cos(lat) weights.

Both are scored on the fixed windows MAM and OND, separately.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "harness"))

import bench                       # noqa: E402
import discovery as D              # noqa: E402
import indices as IX               # noqa: E402
import atlas_score as A            # noqa: E402
import pipeline as P               # noqa: E402
from deepscale.metrics.rpss import _cpt_boundaries   # noqa: E402

WINDOWS = {"MAM": [3, 4, 5], "OND": [10, 11, 12]}


def _series(monthly, month_of_col, year_of_col, cells, w, months, years):
    return IX.season_totals(monthly, month_of_col, year_of_col, cells, w, months, years)


# ── A. fixed regional area-mean ───────────────────────────────────────────────
def fixedmean_fold(part, monthly, month_of_col, year_of_col, years, tr_y, te_y, sst,
                   months, arm="zones"):
    """One fold of secondary benchmark A. Returns (rps_f, rps_c) over the test years."""
    all_cells = part.cell_index
    all_w = part.weights
    target, ok = _series(monthly, month_of_col, year_of_col, all_cells, all_w, months, years)
    cov = IX.coverage_mask(sst, months, years)
    usable = np.flatnonzero(cov & ok)
    tr = np.array([i for i in usable if years[i] in set(tr_y)], dtype=int)
    te = np.array([i for i in usable if years[i] in set(te_y)], dtype=int)
    if len(tr) < 10 or len(te) == 0:
        return None

    comps = {g: IX.raw_components(sst, months, years, g) for g in IX.LEADS}
    X = np.array([IX.compose(n, comps[g], tr) for n, g in A.FEATURE_KEYS])

    zones = range(part.k) if arm == "zones" else [None]
    parts_list = []
    for z in zones:
        if z is None:
            cells, w = all_cells, all_w
        else:
            cells, w = part.zone_cells(z), part.weights[part.labels == z]
        if len(cells) == 0:
            continue
        zs, _ = _series(monthly, month_of_col, year_of_col, cells, w, months, years)
        mse, _ = A._loyo_mse_block(X, zs, tr)
        key = int(np.argmin(mse))
        parts_list.append((float(w.sum()), zs, key))
    if not parts_list:
        return None
    tot_w = sum(w for w, _, _ in parts_list)

    # aggregate prediction, continuous domain, then one conversion to probabilities
    def agg_at(idx_tr, idx_at):
        acc = np.zeros(len(idx_at))
        for w, zs, key in parts_list:
            fit = A._fit_predict(X[key], zs, idx_tr, idx_at)
            if fit is None:
                return None
            acc += w * fit[0]
        return acc / tot_w

    mu_te = agg_at(tr, te)
    if mu_te is None:
        return None
    # inner-LOYO spread of the AGGREGATE against the fixed target
    resid = []
    for h in range(len(tr)):
        inner = np.delete(tr, h)
        a = agg_at(inner, np.array([tr[h]]))
        if a is None:
            continue
        resid.append(target[tr[h]] - _rescale(a, agg_at(inner, inner), target[inner])[0])
    sigma = max(float(np.std(resid)) if len(resid) > 3 else float(np.std(target[tr])), 1e-9)

    mu_te = _rescale(mu_te, agg_at(tr, tr), target[tr])
    t33, t67 = _cpt_boundaries(target[tr])
    _, rf, rc = A._probs_and_rps(mu_te, sigma, target[te], t33, t67)
    return rf, rc


def _rescale(mu, mu_train, y_train):
    """Put the zone aggregate on the fixed target's scale using the training relation."""
    a = np.polyfit(mu_train, y_train, 1)
    return a[0] * mu + a[1]


def run_fixedmean(window, arm="zones", protocol="walkforward", n_folds=6, perm=None):
    fld, sst = P.get_state()
    import fields as F
    mm = fld.monthly if perm is None else F.permute_field(fld, perm)
    months = WINDOWS[window]
    RF, RC = [], []
    for tr_i, te_i in bench.make_folds(fld.years, protocol, n_folds):
        tr_y, te_y = fld.years[tr_i], fld.years[te_i]
        part = D.discover(mm, fld.month_of_col, fld.year_of_col, tr_y, fld.lats, fld.lons,
                          force_k=1 if arm == "pooled" else None)
        r = fixedmean_fold(part, mm, fld.month_of_col, fld.year_of_col, fld.years,
                           tr_y, te_y, sst, months, arm="zones")
        if r is None:
            continue
        RF.append(r[0])
        RC.append(r[1])
    if not RF:
        return float("nan"), 0
    f, c = np.concatenate(RF), np.concatenate(RC)
    return float(1.0 - f.sum() / c.sum()), int(len(f))


# ── B. fixed gridded field ────────────────────────────────────────────────────
def grid_fold(part, monthly, month_of_col, year_of_col, years, tr_y, te_y, sst, months,
              arm="zones-specific"):
    """One fold of secondary benchmark B: every valid cell scored on its own terciles."""
    cov = IX.coverage_mask(sst, months, years)
    cells = part.cell_index
    w_cell = part.weights

    # per-cell seasonal totals
    wraps = months[0] > months[-1]
    roll = [m for m in months if m > months[-1]] if wraps else []
    label = np.where(np.isin(month_of_col, roll), year_of_col + 1, year_of_col)
    keep = np.isin(month_of_col, months)
    dpm = IX.DAYS_PER_MONTH[month_of_col - 1]
    Y = np.full((len(cells), len(years)), np.nan)
    for i, y in enumerate(years):
        sel = keep & (label == y)
        if sel.sum() == len(months):
            Y[:, i] = (monthly[np.ix_(cells, np.flatnonzero(sel))]
                       * dpm[sel][None, :]).sum(1)
    ok = np.isfinite(Y).all(0)
    usable = np.flatnonzero(cov & ok)
    tr = np.array([i for i in usable if years[i] in set(tr_y)], dtype=int)
    te = np.array([i for i in usable if years[i] in set(te_y)], dtype=int)
    if len(tr) < 10 or len(te) == 0:
        return None

    comps = {g: IX.raw_components(sst, months, years, g) for g in IX.LEADS}
    X = np.array([IX.compose(n, comps[g], tr) for n, g in A.FEATURE_KEYS])

    # one forecast per zone, broadcast to its cells
    probs = np.full((len(cells), len(te), 3), 1.0 / 3.0)
    if arm != "climatology":
        for z in range(part.k):
            m = part.labels == z
            if not m.any():
                continue
            zc, zw = part.zone_cells(z), part.weights[m]
            zs, _ = _series(monthly, month_of_col, year_of_col, zc, zw, months, years)
            mse, _ = A._loyo_mse_block(X, zs, tr)
            key = int(np.argmin(mse))
            fit = A._fit_predict(X[key], zs, tr, te)
            if fit is None:
                continue
            mu, sigma = fit
            # a zone-level anomaly signal, applied to each cell's own distribution
            zmu_tr = A._fit_predict(X[key], zs, tr, tr)[0]
            zsd = np.std(zs[tr]) or 1.0
            znorm = (mu - zmu_tr.mean()) / zsd
            for ci in np.flatnonzero(m):
                yv = Y[ci]
                cmu = yv[tr].mean() + znorm * yv[tr].std()
                csd = max(float(np.std(yv[tr])) * np.sqrt(max(1 - 0.0, 1e-6)), 1e-9)
                t33, t67 = _cpt_boundaries(yv[tr])
                p, _, _ = A._probs_and_rps(cmu, csd, yv[te], t33, t67)
                probs[ci] = p

    rf = np.zeros(len(cells))
    rc = np.zeros(len(cells))
    for ci in range(len(cells)):
        yv = Y[ci]
        t33, t67 = _cpt_boundaries(yv[tr])
        cat = np.where(t33 > yv[te], 0, np.where(t67 > yv[te], 1, 2))
        oh = np.stack([(cat == i).astype(float) for i in range(3)], axis=1)
        p = probs[ci]
        rf[ci] = np.sum((np.cumsum(p, 1) - np.cumsum(oh, 1)) ** 2) / 2.0
        clim = np.full_like(p, 1 / 3)
        rc[ci] = np.sum((np.cumsum(clim, 1) - np.cumsum(oh, 1)) ** 2) / 2.0
    return float((w_cell * rf).sum()), float((w_cell * rc).sum()), len(te)


def run_grid(window, arm="zones-specific", protocol="walkforward", n_folds=6, perm=None):
    fld, sst = P.get_state()
    import fields as F
    mm = fld.monthly if perm is None else F.permute_field(fld, perm)
    months = WINDOWS[window]
    num = den = 0.0
    nyr = 0
    for tr_i, te_i in bench.make_folds(fld.years, protocol, n_folds):
        tr_y, te_y = fld.years[tr_i], fld.years[te_i]
        part = D.discover(mm, fld.month_of_col, fld.year_of_col, tr_y, fld.lats, fld.lons,
                          force_k=1 if arm == "pooled" else None)
        r = grid_fold(part, mm, fld.month_of_col, fld.year_of_col, fld.years,
                      tr_y, te_y, sst, months,
                      arm="climatology" if arm == "climatology" else "zones-specific")
        if r is None:
            continue
        num += r[0]
        den += r[1]
        nyr += r[2]
    if den <= 0:
        return float("nan"), 0
    return float(1.0 - num / den), nyr
