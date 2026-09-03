"""atlas_score.py — SPEC 10, the complete zonal product, vectorised.

WHAT IS SCORED. For each outer fold: every zone the fold discovered, every window that
zone discovered, every test year. Weighted by omega(f,z,m) = A(f,z)/A_total(f)/W(f,z),
which sums to 1 within each fold. Losses pooled across folds, never averaged as ratios.

FOLD-LOCAL BY CONSTRUCTION (SPEC 10, SPEC 12.1). Zone indices are whatever the fold
produced. Nothing here consults a cross-fold track identity, and no minimum-year
threshold is applied. Renaming every zone leaves the pooled score bit-identical.

THE SPEED. Within one (fold, window) every zone shares the same 20 predictor vectors
(5 indices x 4 leads) and the same year axis, so the inner leave-one-year-out selection
is one matrix pass rather than 20 x n_zones x n_train regression fits. Leave-one-out for
simple OLS has a closed form -- e_i^(-i) = e_i / (1 - h_ii) -- so LOYO costs one fit,
not n. atlas_score_slow.py recomputes all of it with explicit loops, np.polyfit and
scipy.stats.norm, and tests/test_scorer_agreement.py holds the two to 1e-8.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.special import erf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "harness"))

from africas2s.metrics.rpss import _cpt_boundaries          # noqa: E402
import indices as IX                                        # noqa: E402

_SQRT2 = np.sqrt(2.0)
FEATURE_KEYS = [(n, g) for n in IX.INDEX_NAMES for g in IX.LEADS]


def _ncdf(v, mu, sig):
    return 0.5 * (1.0 + erf((v - mu) / (sig * _SQRT2)))


@dataclass
class Forecast:
    """One zone-window's out-of-sample forecast in one fold."""
    zone: int
    window: str
    months: tuple
    weight: float                 # omega(f, z, m) for the complete-atlas family
    zone_share: float             # A(f,z)/A_total(f), the family weight for MAM/*
    index: str
    lead: int
    test_years: np.ndarray
    probs: np.ndarray             # (n_test, 3)
    obs: np.ndarray               # (n_test,) seasonal total, mm
    rps_f: np.ndarray
    rps_c: np.ndarray
    n_train: int
    loyo_mse: float
    discovered: bool = True       # False for a forced window (SPEC 8's MAM)


# ── the vectorised core ───────────────────────────────────────────────────────
def _loyo_mse_block(X, y, tr):
    """Closed-form leave-one-year-out MSE for every predictor row against one target.

    X (F, n) predictors, y (n,) target, tr training indices. Returns (F,) LOYO MSE and
    (F, n_tr) the LOYO residuals, both exact for simple OLS.
    """
    Xt, yt = X[:, tr], y[tr]
    m = len(tr)
    xm = Xt.mean(1, keepdims=True)
    dx = Xt - xm
    sxx = np.einsum("ij,ij->i", dx, dx)
    sxx_safe = np.where(sxx > 0, sxx, 1.0)
    ym = yt.mean()
    dy = yt - ym
    b1 = (dx @ dy) / sxx_safe
    resid = dy[None, :] - b1[:, None] * dx
    lev = 1.0 / m + dx ** 2 / sxx_safe[:, None]
    denom = np.clip(1.0 - lev, 1e-12, None)
    loo = resid / denom
    mse = (loo ** 2).mean(1)
    mse = np.where(sxx > 0, mse, np.inf)
    return mse, loo


def _fit_predict(X, y, tr, te):
    """Train-fitted regression + inner-LOYO spread, evaluated on test indices."""
    xt, yt = X[tr], y[tr]
    m = len(tr)
    mx, sx = xt.mean(), xt.std()
    if sx == 0:
        return None
    xs = (xt - mx) / sx
    xsm = xs.mean()
    dx = xs - xsm
    sxx = float(dx @ dx)
    if sxx <= 0:
        return None
    ym = yt.mean()
    b1 = float(dx @ (yt - ym) / sxx)
    b0 = float(ym - b1 * xsm)
    resid = yt - (b0 + b1 * xs)
    lev = 1.0 / m + dx ** 2 / sxx
    loo = resid / np.clip(1.0 - lev, 1e-12, None)
    sigma = max(float(np.std(loo)), 1e-9)
    mu = b0 + b1 * (X[te] - mx) / sx
    return mu, sigma


def _probs_and_rps(mu, sigma, y_te, t33, t67):
    pb = _ncdf(t33, mu, sigma)
    p67 = _ncdf(t67, mu, sigma)
    p = np.stack([pb, p67 - pb, 1.0 - p67], axis=1)
    p[~np.isfinite(mu)] = 1.0 / 3.0
    p = np.clip(p, 1e-9, 1.0)
    p = p / p.sum(1, keepdims=True)
    cat = np.where(t33 > y_te, 0, np.where(t67 > y_te, 1, 2))
    oh = np.stack([(cat == i).astype(float) for i in range(3)], axis=1)
    rps_f = np.sum((np.cumsum(p, 1) - np.cumsum(oh, 1)) ** 2, axis=1) / 2.0
    clim = np.full_like(p, 1.0 / 3.0)
    rps_c = np.sum((np.cumsum(clim, 1) - np.cumsum(oh, 1)) ** 2, axis=1) / 2.0
    return p, rps_f, rps_c


def climatology_rps(y_te, t33, t67):
    cat = np.where(t33 > y_te, 0, np.where(t67 > y_te, 1, 2))
    oh = np.stack([(cat == i).astype(float) for i in range(3)], axis=1)
    clim = np.full((len(y_te), 3), 1.0 / 3.0)
    r = np.sum((np.cumsum(clim, 1) - np.cumsum(oh, 1)) ** 2, axis=1) / 2.0
    return r


# ── window assembly ───────────────────────────────────────────────────────────
def zone_window_list(part, forced_windows=()):
    """(zone, label, months, discovered) for every zone-window the fold will forecast."""
    out = []
    for z in range(part.k):
        got = list(part.windows.get(z, []))
        labels = {lab for lab, _ in got}
        for lab, months in got:
            out.append((z, lab, tuple(months), True))
        for lab, months in forced_windows:
            if lab not in labels:
                out.append((z, lab, tuple(months), False))
    return out


def fold_weights(part, zone_window_pairs):
    """omega(f,z,m) = A(f,z)/A_total(f)/W(f,z). Only DISCOVERED windows share a zone's
    weight; a forced window (SPEC 8's MAM) carries the zone's full area weight in its own
    family and is excluded from the complete-atlas family."""
    tot = part.total_weight()
    n_disc = {z: max(1, sum(1 for zz, _, _, d in zone_window_pairs if zz == z and d))
              for z in range(part.k)}
    w = {}
    for z, lab, months, disc in zone_window_pairs:
        a = part.zone_weight(z) / tot
        w[(z, lab)] = a / n_disc[z] if disc else a
    return w


def rainfall_share_weights(part, zone_window_pairs):
    """SPEC 10's pre-registered alternative: split a zone's weight by window rainfall."""
    tot = part.total_weight()
    w = {}
    for z in range(part.k):
        disc = [(lab, months) for zz, lab, months, d in zone_window_pairs if zz == z and d]
        if not disc:
            continue
        sums = {lab: float(part.cycles[z][[m - 1 for m in months]].sum())
                for lab, months in disc}
        s = sum(sums.values()) or 1.0
        for lab, _ in disc:
            w[(z, lab)] = (part.zone_weight(z) / tot) * (sums[lab] / s)
    for z, lab, months, d in zone_window_pairs:
        if not d:
            w[(z, lab)] = part.zone_weight(z) / tot
    return w


# ── one fold ──────────────────────────────────────────────────────────────────
def score_fold(part, monthly, month_of_col, year_of_col, years, train_years, test_years,
               sst, arm="zones-specific", leak=False, forced_windows=(),
               weight_rule="equal"):
    """Every zone-window of one fold, forecast and scored. Returns a list of Forecast.

    arm      "zones-specific" | "zones-shared" | "climatology"
    leak     SPEC 9.2: standardise WPG/WVG on the full record instead of on train
    A null replicate does NOT arrive here as a flag. SPEC 14 permutes the rainfall FIELD
    and re-runs discovery on it, so by the time this function is called the permutation is
    already baked into `monthly`. See fields.permute_field.
    """
    pairs = zone_window_list(part, forced_windows)
    wmap = (fold_weights(part, pairs) if weight_rule == "equal"
            else rainfall_share_weights(part, pairs))

    by_window = {}
    for z, lab, months, disc in pairs:
        by_window.setdefault((lab, months), []).append((z, disc))

    out = []
    for (lab, months), zlist in by_window.items():
        mlist = list(months)
        cov = IX.coverage_mask(sst, mlist, years)
        # predictand for every zone in this window
        ys, oks = {}, None
        for z, _ in zlist:
            cells = part.zone_cells(z)
            w = part.weights[part.labels == z]
            v, ok = IX.season_totals(monthly, month_of_col, year_of_col, cells, w,
                                     mlist, years)
            ys[z] = v
            oks = ok if oks is None else (oks & ok)
        usable = np.flatnonzero(cov & oks)

        tr = np.array([i for i in usable if years[i] in set(train_years)], dtype=int)
        te = np.array([i for i in usable if years[i] in set(test_years)], dtype=int)
        if len(tr) < 10 or len(te) == 0:
            continue

        comps = {g: IX.raw_components(sst, mlist, years, g) for g in IX.LEADS}
        z_fit = np.arange(len(years)) if leak else tr
        X = np.array([IX.compose(n, comps[g], z_fit) for n, g in FEATURE_KEYS])

        # ── selection, inner LOYO on the training years ──────────────────────
        chosen = {}
        if arm == "zones-shared":
            pooled = np.zeros(len(FEATURE_KEYS))
            for z, _ in zlist:
                mse, _ = _loyo_mse_block(X, ys[z], tr)
                var = np.var(ys[z][tr]) or 1.0
                pooled += wmap[(z, lab)] * np.minimum(mse / var, 1e6)
            best = int(np.argmin(pooled))
            for z, _ in zlist:
                chosen[z] = best
        else:
            for z, _ in zlist:
                mse, _ = _loyo_mse_block(X, ys[z], tr)
                chosen[z] = int(np.argmin(mse))

        for z, disc in zlist:
            key = chosen[z]
            fname, gap = FEATURE_KEYS[key]
            y = ys[z]
            t33, t67 = _cpt_boundaries(y[tr])
            if arm == "climatology":
                p = np.full((len(te), 3), 1.0 / 3.0)
                rc = climatology_rps(y[te], t33, t67)
                rf = rc.copy()
                mse_v = float("nan")
            else:
                fit = _fit_predict(X[key], y, tr, te)
                if fit is None:
                    p = np.full((len(te), 3), 1.0 / 3.0)
                    rc = climatology_rps(y[te], t33, t67)
                    rf = rc.copy()
                else:
                    mu, sigma = fit
                    p, rf, rc = _probs_and_rps(mu, sigma, y[te], t33, t67)
                mse_v = float(_loyo_mse_block(X[key:key + 1], y, tr)[0][0])
            out.append(Forecast(zone=z, window=lab, months=tuple(mlist),
                                weight=wmap[(z, lab)],
                                zone_share=part.zone_weight(z) / part.total_weight(),
                                index=fname, lead=gap,
                                test_years=years[te], probs=p, obs=y[te],
                                rps_f=rf, rps_c=rc, n_train=len(tr),
                                loyo_mse=mse_v, discovered=disc))
    return out


# ── pooling (SPEC 10) ─────────────────────────────────────────────────────────
def family_selector(name):
    """SPEC 14's four scoring families."""
    if name == "atlas/all-windows":
        return lambda fc: fc.discovered
    if name.startswith("MAM/"):
        return lambda fc: fc.months == (3, 4, 5)
    raise ValueError(name)


def family_weight(name):
    """The weight a family pools with. Both choices sum to 1 within every fold.

    `atlas/all-windows` splits a zone's area share across its discovered windows, so a
    bimodal zone's two seasons together carry the same weight as a unimodal zone's one.

    The MAM families see exactly ONE window per zone, so the equal split would hand a
    bimodal zone half the weight of a unimodal zone for no reason -- and the MAM weights
    would not sum to 1. They therefore pool on the zone's full area share. This is a
    clarification of SPEC 10 forced by the arithmetic, not by any score: it was found by
    noticing that the smoke run's MAM weights summed to 0.657 rather than 1.
    """
    if name == "atlas/all-windows":
        return lambda fc: fc.weight
    if name.startswith("MAM/"):
        return lambda fc: fc.zone_share
    raise ValueError(name)


def pool(fold_forecasts, select=None, weight=None):
    """RPSS_atlas over a list-of-lists of Forecast, one inner list per fold.

    `select(fc) -> bool` restricts to a scoring family; `weight(fc) -> float` supplies
    that family's weight. No minimum-year threshold and no renormalisation: SPEC 12.1.
    """
    weight = weight or (lambda fc: fc.weight)
    num = den = 0.0
    n = 0
    for fold in fold_forecasts:
        for fc in fold:
            if select is not None and not select(fc):
                continue
            if len(fc.rps_f) == 0:
                continue
            w = weight(fc)
            num += w * fc.rps_f.sum()
            den += w * fc.rps_c.sum()
            n += len(fc.rps_f)
    if den <= 0:
        return float("nan"), 0
    return float(1.0 - num / den), n


def coverage(fold_forecasts, select=None, weight=None, n_folds=None):
    """SPEC 12.1 fold-local coverage: mean over folds of the weight that scored >=1 year."""
    weight = weight or (lambda fc: fc.weight)
    n_folds = n_folds or len(fold_forecasts)
    tot = 0.0
    for fold in fold_forecasts:
        for fc in fold:
            if select is not None and not select(fc):
                continue
            if len(fc.rps_f) >= 1:
                tot += weight(fc)
    return tot / max(n_folds, 1)


def apply_condition(fold_forecasts, cname, sst, years, folds, forced_months=(3, 4, 5)):
    """Restrict each forecast to the test years its condition admits (SPEC 8)."""
    if cname == "all":
        return fold_forecasts
    out = []
    for (tr_years, te_years), fold in zip(folds, fold_forecasts):
        keep_fold = []
        for fc in fold:
            comp0 = IX.raw_components(sst, list(fc.months), years, IX.COND_GAP,
                                      IX.COND_WIDTH)
            tr = np.flatnonzero(np.isin(years, tr_years))
            te = np.flatnonzero(np.isin(years, fc.test_years))
            m = IX.condition_mask(cname, comp0, tr, te)
            keep_fold.append(Forecast(
                zone=fc.zone, window=fc.window, months=fc.months, weight=fc.weight,
                zone_share=fc.zone_share, index=fc.index, lead=fc.lead, test_years=fc.test_years[m],
                probs=fc.probs[m], obs=fc.obs[m], rps_f=fc.rps_f[m], rps_c=fc.rps_c[m],
                n_train=fc.n_train, loyo_mse=fc.loyo_mse, discovered=fc.discovered))
        out.append(keep_fold)
    return out
