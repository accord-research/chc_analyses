"""atlas_score_slow.py — the naive reference implementation of SPEC 10.

Deliberately slow and deliberately independent. Where atlas_score.py uses a closed-form
leave-one-out identity, a matrix pass over all 20 predictors at once, and erf, this file
refits np.polyfit inside an explicit leave-one-year-out loop, handles one predictor at a
time, and calls scipy.stats.norm.cdf. If the two agree to 1e-8 then the closed forms are
right; if they ever stop agreeing, the fast path is wrong and the sweep aborts.

SPEC 16 requires this comparison on sampled folds and sampled permutation replicates on
every production run, not once at development time. v4zeek's equivalent gate caught three
real bugs, none of which would have crashed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "harness"))

from deepscale.metrics.rpss import _cpt_boundaries          # noqa: E402
import indices as IX                                        # noqa: E402
from atlas_score import (Forecast, FEATURE_KEYS, fold_weights,   # noqa: E402
                         rainfall_share_weights, zone_window_list)


def _loyo_mse_slow(x, y, tr):
    """Explicit leave-one-year-out: refit the line n times."""
    errs = []
    for h in range(len(tr)):
        inner = np.delete(tr, h)
        held = tr[h]
        if np.std(x[inner]) == 0:
            return np.inf, None
        b1, b0 = np.polyfit(x[inner], y[inner], 1)
        errs.append((y[held] - (b0 + b1 * x[held])) ** 2)
    return float(np.mean(errs)), np.sqrt(np.array(errs))


def _loyo_residuals_slow(x, y, tr):
    res = []
    for h in range(len(tr)):
        inner = np.delete(tr, h)
        held = tr[h]
        b1, b0 = np.polyfit(x[inner], y[inner], 1)
        res.append(y[held] - (b0 + b1 * x[held]))
    return np.array(res)


def score_fold_slow(part, monthly, month_of_col, year_of_col, years, train_years,
                    test_years, sst, arm="zones-specific", leak=False,
                    forced_windows=(), weight_rule="equal"):
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

        feats = {}
        for i, (n, g) in enumerate(FEATURE_KEYS):
            feats[i] = IX.compose(n, comps[g], z_fit)

        chosen = {}
        if arm == "zones-shared":
            pooled = []
            for i in range(len(FEATURE_KEYS)):
                acc = 0.0
                for z, _ in zlist:
                    mse, _ = _loyo_mse_slow(feats[i], ys[z], tr)
                    var = np.var(ys[z][tr]) or 1.0
                    acc += wmap[(z, lab)] * min(mse / var, 1e6)
                pooled.append(acc)
            best = int(np.argmin(pooled))
            for z, _ in zlist:
                chosen[z] = best
        else:
            for z, _ in zlist:
                scores = [_loyo_mse_slow(feats[i], ys[z], tr)[0]
                          for i in range(len(FEATURE_KEYS))]
                chosen[z] = int(np.argmin(scores))

        for z, disc in zlist:
            key = chosen[z]
            fname, gap = FEATURE_KEYS[key]
            x, y = feats[key], ys[z]
            t33, t67 = _cpt_boundaries(y[tr])
            if arm == "climatology":
                p = np.full((len(te), 3), 1.0 / 3.0)
            else:
                mx, sx = x[tr].mean(), x[tr].std()
                xs = (x - mx) / sx
                b1, b0 = np.polyfit(xs[tr], y[tr], 1)
                loo = _loyo_residuals_slow(xs, y, tr)
                sigma = max(float(np.std(loo)), 1e-9)
                mu = b0 + b1 * xs[te]
                pb = norm.cdf(t33, loc=mu, scale=sigma)
                p67 = norm.cdf(t67, loc=mu, scale=sigma)
                p = np.stack([pb, p67 - pb, 1.0 - p67], axis=1)
                p = np.clip(p, 1e-9, 1.0)
                p = p / p.sum(1, keepdims=True)

            rf, rc = [], []
            for j, ti in enumerate(te):
                yy = y[ti]
                cat = 0 if t33 > yy else (1 if t67 > yy else 2)
                oh = np.zeros(3)
                oh[cat] = 1.0
                cp, co = np.cumsum(p[j]), np.cumsum(oh)
                rf.append(float(np.sum((cp - co) ** 2) / 2.0))
                cc = np.cumsum(np.full(3, 1 / 3))
                rc.append(float(np.sum((cc - co) ** 2) / 2.0))
            mse_v, _ = _loyo_mse_slow(x, y, tr)
            out.append(Forecast(zone=z, window=lab, months=tuple(mlist),
                                weight=wmap[(z, lab)],
                                zone_share=part.zone_weight(z) / part.total_weight(),
                                index=fname, lead=gap,
                                test_years=years[te], probs=p, obs=y[te],
                                rps_f=np.array(rf), rps_c=np.array(rc),
                                n_train=len(tr), loyo_mse=float(mse_v),
                                discovered=disc))
    return out
