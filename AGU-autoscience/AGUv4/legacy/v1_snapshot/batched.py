"""batched.py — evaluate the entire grid as matrix operations instead of a Python loop.

WHY. The per-cell scorer does 9,720 cells x 201 permutation passes x 6 folds = 11.7 MILLION
Python-level regression fits per sweep. The arithmetic is trivial (a 42-point OLS); the
cost is entirely loop overhead. A sweep took 45 minutes.

THE STRUCTURE THAT MAKES THIS COLLAPSE. Within one (window, protocol) every cell shares
the same folds and the same year axis. Only two things vary: which feature vector is the
predictor, and which region's series is the target. So for F features and T targets the
whole fold is one outer product, not F*T fits:

    cov[i,j] = (Xc @ Yc.T)[i,j] / n        <- every regression's covariance at once
    b1[i,j]  = cov[i,j] / var_x[i]
    b0[i,j]  = ym[j] - b1[i,j] * xm[i]

Residual spread also has a closed form, so no residual vector is ever materialised:

    var_resid[i,j] = (var_y[j] - b1[i,j]^2 * var_x[i]) * n / (n - 2)

Predictions, tercile probabilities and RPS then broadcast over (feature, target, year).
Peak working set is F x T x n_test x 3 floats — about 100k numbers. Nothing is large.

CORRECTNESS. This is a second reimplementation of a scorer that already has one, so it
gets a second gate. `verify_batched` checks it cell-by-cell against `score_fast`, which
`grid_sweep.verify` independently checks against the LOCKED `bench.evaluate`. The chain
is batched == score_fast == bench.evaluate, and any break aborts the sweep.

NaNs. In every fixture used here the predictor windows sit inside the SST record, so X
and Y are fully finite. Rather than silently assume that, `prepare` asserts it and the
caller falls back to the per-cell path if it ever fails.
"""
from __future__ import annotations

import numpy as np
from scipy.special import erf

from deepscale.metrics.rpss import _cpt_boundaries

_SQRT2 = np.sqrt(2.0)


def _ncdf(v, mu, sig):
    return 0.5 * (1.0 + erf((v - mu) / (sig * _SQRT2)))


def _detrend_rows(M, tr, t):
    """Remove a train-fitted linear time trend from every row of M. Matrix form of
    grid_sweep._detrend, which it must agree with exactly."""
    tt = t[tr]
    tm = tt.mean()
    dt = tt - tm
    denom = float(dt @ dt)
    if denom <= 0:
        return M
    vm = M[:, tr].mean(axis=1, keepdims=True)
    b = (M[:, tr] - vm) @ dt / denom
    return M - (vm + b[:, None] * (t - tm)[None, :])


def score_block(X, Y, folds, detrend=False, cond_masks=None, min_scored=8):
    """Score every (feature, target) pair over every fold, in matrix form.

    X          (F, n) predictor rows, already composed for this fold set
    Y          (T, n) target rows
    folds      list of (train_idx, test_idx)
    cond_masks dict name -> callable(tr, te) -> bool mask over te, or None for 'all'

    Returns dict: condition name -> (rpss (F,T), n_scored (F,T) int)

    Composite features whose definition contains a train-fitted constant must be built by
    the caller PER FOLD, because that constant is part of the model, not the data. This
    function therefore takes X as a callable when needed; see score_block_dynamic.
    """
    raise NotImplementedError("use score_block_dynamic; kept for signature documentation")


def score_block_dynamic(build_X, Y, folds, t, detrend=False, cond_specs=(("all", None),),
                        min_scored=8):
    """As above, but `build_X(tr)` returns the (F, n) predictor block for a given training
    fold, so features carrying train-fitted constants (standardised gradient indices) are
    rebuilt per fold rather than leaked across the split.

    Returns {cond_name: (rpss (F,T) float array, n_scored (F,T) int array)}.
    """
    T_, n = Y.shape
    acc = {c: None for c, _ in cond_specs}
    cnt = {c: None for c, _ in cond_specs}

    for tr, te in folds:
        X = np.asarray(build_X(tr), dtype=float)
        Yf = Y
        if detrend:
            X = _detrend_rows(X, tr, t)
            Yf = _detrend_rows(Y, tr, t)
        F = X.shape[0]

        Xtr, Ytr = X[:, tr], Yf[:, tr]
        m = len(tr)
        xm = Xtr.mean(axis=1)
        xv = Xtr.var(axis=1)                        # population, matches xo.std()
        ym = Ytr.mean(axis=1)
        yv = Ytr.var(axis=1)

        good = xv > 0
        xs_scale = np.where(good, np.sqrt(xv), 1.0)
        # standardised predictor, exactly as the per-cell path builds it
        Xs = (Xtr - xm[:, None]) / xs_scale[:, None]
        Xsc = Xs - Xs.mean(axis=1, keepdims=True)
        Yc = Ytr - ym[:, None]

        denom = np.einsum("ij,ij->i", Xsc, Xsc)      # (F,)
        denom = np.where(denom > 0, denom, 1.0)
        b1 = (Xsc @ Yc.T) / denom[:, None]           # (F, T)  every regression at once
        b0 = ym[None, :] - b1 * Xs.mean(axis=1)[:, None]

        # closed-form residual spread; ddof=2 to match np.polyfit-based path
        var_x_s = np.einsum("ij,ij->i", Xsc, Xsc) / m
        resid_var = (yv[None, :] - b1 ** 2 * var_x_s[:, None]) * m / max(m - 2, 1)
        sig = np.sqrt(np.clip(resid_var, 1e-18, None))

        # train-fitted tercile edges, one pair per target
        edges = np.array([_cpt_boundaries(Ytr[j]) for j in range(T_)])   # (T,2)
        t33, t67 = edges[:, 0], edges[:, 1]

        Xte_s = (X[:, te] - xm[:, None]) / xs_scale[:, None]             # (F, k)
        mu = b0[:, :, None] + b1[:, :, None] * Xte_s[:, None, :]          # (F,T,k)
        s3 = sig[:, :, None]
        pb = _ncdf(t33[None, :, None], mu, s3)
        p67 = _ncdf(t67[None, :, None], mu, s3)
        p = np.stack([pb, p67 - pb, 1.0 - p67], axis=-1)                  # (F,T,k,3)
        bad = ~good
        if bad.any():
            p[bad] = 1.0 / 3.0
        p = np.clip(p, 1e-9, 1.0)
        p /= p.sum(-1, keepdims=True)

        yte = Yf[:, te]                                                   # (T,k)
        cat = np.where(t33[:, None] > yte, 0, np.where(t67[:, None] > yte, 1, 2))
        oh = np.stack([(cat == i).astype(float) for i in range(3)], axis=-1)  # (T,k,3)

        rps_f = np.sum((np.cumsum(p, -1) - np.cumsum(oh, -1)[None]) ** 2, axis=-1) / 2.0
        clim = np.full(3, 1.0 / 3.0)
        rps_c = np.sum((np.cumsum(clim) - np.cumsum(oh, -1)) ** 2, axis=-1) / 2.0  # (T,k)

        for cname, fn in cond_specs:
            keep = np.ones(len(te), dtype=bool) if fn is None else np.asarray(fn(tr, te))
            if not keep.any():
                continue
            sf = rps_f[:, :, keep].sum(-1)
            sc = np.broadcast_to(rps_c[:, keep].sum(-1), sf.shape)
            k = np.full(sf.shape, int(keep.sum()))
            if acc[cname] is None:
                acc[cname] = [sf.copy(), np.array(sc, dtype=float), k.copy()]
            else:
                acc[cname][0] += sf
                acc[cname][1] += sc
                acc[cname][2] += k

    out = {}
    for cname, _ in cond_specs:
        if acc[cname] is None:
            continue
        sf, sc, k = acc[cname]
        with np.errstate(divide="ignore", invalid="ignore"):
            rpss = 1.0 - sf / sc
        rpss = np.where((k >= min_scored) & (sc > 0), rpss, np.nan)
        out[cname] = (rpss, k)
    return out
