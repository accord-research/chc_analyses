"""grid_sweep.py — search the full configuration grid, against the only null that makes searching legitimate.

THE POINT OF THIS FILE. "Run configurations until something looks like signal" succeeds
on pure noise with probability 1. If you evaluate 2000 cells and report the best one, the
best one is large whether or not any signal exists. That is the mechanism that produced
four versions of the prior program's headline claims.

So the reference here is NOT each cell's own null. It is the distribution of the BEST
CELL IN THE WHOLE GRID under shuffled targets:

    for each of N replicates:
        draw one year-permutation
        apply it to EVERY region's target (one permutation, not one per region, so the
            strong correlation between neighbouring regions is preserved and the grid's
            cells stay as non-independent under the null as they are in reality)
        re-run the ENTIRE grid
        record the maximum RPSS over all cells

    best-of-grid null = that distribution

A real best-cell only means something if it exceeds the 95th percentile of that. This
answers "is there signal anywhere in this design space" with the search cost already
paid for, rather than pretending the winning cell was the only one ever tried.

The grid axes:
    region  x  season window  x  ocean feature  x  lead gap  x  predictor width

The model is held fixed (linear regression + Gaussian predictive distribution, exactly
what candidates/expert_enso.py does) so the grid isolates the design axes rather than
confounding them with the fitting method.

VERIFICATION. The fast scorer here reimplements bench.evaluate in flat numpy for speed.
A fast reimplementation that silently disagrees with the locked harness would be worse
than useless, so --verify cross-checks a sample of cells against bench.evaluate and
refuses to run the sweep if any disagree.

Run:
    python probes/grid_sweep.py --verify           # agreement check only
    python probes/grid_sweep.py --n-null 200       # full sweep
"""
import argparse
import itertools
import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
from scipy.special import erf
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bench
import batched as B
from africas2s.metrics.rpss import _cpt_boundaries

FIXTURE = "ca_precip_monthly.nc"      # overridden by --fixture
SST_PREFIX = "sst_"                   # overridden by --sst-prefix

# ── domains ───────────────────────────────────────────────────────────────────
# A domain is a (regions, windows) pair. California came back empty (f:9); East Africa
# is the better positive control because the prior program's own strongest result was
# the East African October-December short rains. Sub-regions here are the ones the
# literature and AGUv0-v3 actually argue about, so a hit or a miss is directly
# comparable to their claims rather than to an analogy.
DOMAINS = {
    "ca": dict(
        regions={
            "ca-whole":   [32.0, 42.5, -125.0, -114.0],
            "ca-north":   [38.5, 42.5, -125.0, -119.0],
            "ca-central": [35.5, 38.5, -123.0, -117.0],
            "ca-south":   [32.0, 35.5, -121.0, -114.0],
            "ca-n-half":  [37.0, 42.5, -125.0, -118.0],
            "ca-s-half":  [32.0, 37.0, -122.0, -114.0],
            "ca-coastal": [32.0, 42.5, -125.0, -120.0],
            "ca-inland":  [32.0, 42.5, -120.0, -114.0],
            "ca-sierra":  [36.0, 40.0, -121.0, -118.0],
        },
        windows={
            "DJF":    [12, 1, 2],
            "NDJ":    [11, 12, 1],
            "JFM":    [1, 2, 3],
            "NDJFM":  [11, 12, 1, 2, 3],
            "ONDJFM": [10, 11, 12, 1, 2, 3],
        }),
    "ea": dict(
        regions={
            "ea-whole":    [-5.0, 12.0, 33.0, 52.0],
            "ehorn":       [-4.5,  8.5, 38.0, 50.5],   # the AGUv2 hand-drawn domain
            "kenya":       [-4.7,  5.0, 33.9, 41.9],
            "somalia":     [-1.7, 12.0, 41.0, 51.4],
            "sc-somalia":  [ 1.0,  6.0, 42.0, 48.0],   # the reviewer's specific box
            "w-kenya":     [-4.7,  5.0, 34.0, 38.0],   # the "destructive inclusion"
            "e-kenya":     [-4.7,  5.0, 38.0, 42.0],
            "eth-highland":[ 5.0, 12.0, 35.0, 40.0],
            "ea-south":    [-5.0,  2.0, 33.0, 42.0],
        },
        windows={
            "OND":  [10, 11, 12],      # short rains / Deyr — the target of interest
            "SON":  [9, 10, 11],
            "NDJ":  [11, 12, 1],
            "MAM":  [3, 4, 5],         # long rains — where AGUv1 claimed no skill
            "AMJ":  [4, 5, 6],
            "JAS":  [7, 8, 9],         # Kiremt, the anti-phased highland regime
        }),
}

DOMAIN = "ca"                          # overridden by --domain
REGIONS = DOMAINS[DOMAIN]["regions"]
WINDOWS = DOMAINS[DOMAIN]["windows"]

RAW_BOXES = ("nino34", "iod_w", "iod_e", "wpac", "wv")
FEATURES = ("nino34", "iod", "wpac", "wv", "wpg", "wvg")
GAPS = (0, 1, 2, 3, 4)
WIDTHS = (1, 2, 3)
PROTOCOLS = ("walkforward", "kfold")

# ── conditional evaluation (see PREREGISTRATION_conditional.md, committed first) ──
# A condition restricts which TEST years are scored. Every rule below is computed from
# pre-season SST alone, so it is knowable before the season starts and corresponds to a
# real operational choice: issue a forecast only when the ocean is in this state.
# The conditioning predictor is FIXED at gap 0 / width 2 for every cell, independent of
# that cell's own gap and width, so conditioning cannot become a second searchable knob.
CONDITIONS = ("all", "lanina", "neg_wvg")
COND_GAP, COND_WIDTH = 0, 2
MIN_SCORED = 8          # a cell scoring fewer test years than this is dropped entirely


def condition_mask(cname, comp0, tr, te):
    """Boolean mask over the TEST indices `te`. Thresholds are fitted on TRAIN only."""
    if cname == "all":
        return np.ones(len(te), dtype=bool)
    if cname == "lanina":
        v = comp0["nino34"]
        m, sd = np.nanmean(v[tr]), np.nanstd(v[tr])
        return v[te] < (m - 0.5 * sd)
    if cname == "neg_wvg":
        v = compose("wvg", comp0, tr)
        return v[te] < np.nanpercentile(v[tr], 100.0 / 3.0)
    raise ValueError(cname)


# ── feature construction ──────────────────────────────────────────────────────
# Two of the six indices (wpg, wvg) contain a standardization step. That step is a
# FITTED QUANTITY and must be fitted on training years only, then applied to test years
# — the same discipline as the regression coefficients. Fitting it on all years leaks
# test information into the predictor; fitting train and test separately puts them on
# two different scales. The --verify gate caught both mistakes, so composites are
# composed per fold from raw components rather than precomputed once.
def compose(name, comp, tr):
    """Build a named index from raw box arrays. `tr` indexes the training years, and
    every fitted constant inside the index comes from those years alone."""
    def z(v):
        m, s = np.nanmean(v[tr]), np.nanstd(v[tr])
        return (v - m) / s if s > 0 else v * 0.0

    if name == "nino34":
        return comp["nino34"]
    if name == "iod":
        return comp["iod_w"] - comp["iod_e"]        # a difference of like units; no fit
    if name == "wpac":
        return comp["wpac"]
    if name == "wv":
        return comp["wv"]
    if name == "wpg":
        return z(comp["wpac"]) - z(comp["nino34"])
    if name == "wvg":
        return z(comp["nino34"]) - z(comp["wv"])
    raise ValueError(name)


# ── fast scorer: must agree with bench.evaluate exactly ───────────────────────
# np.polyfit (Vandermonde + lstsq) and scipy.stats.norm.cdf dominated the runtime: the
# first sweep took 40 minutes for 201 grid passes. Both are replaced with closed forms
# below. This is a pure speed change and it is NOT taken on trust — the --verify gate
# re-checks the fast path against the locked bench.evaluate (which still uses polyfit)
# on every run, so any numerical divergence aborts the sweep instead of silently
# altering results.
_SQRT2 = np.sqrt(2.0)


def _ncdf(v, mu, sig):
    """Normal CDF via erf — same value as scipy.stats.norm.cdf, far less call overhead."""
    return 0.5 * (1.0 + erf((v - mu) / (sig * _SQRT2)))


def _detrend(v, tr, t):
    """Remove a linear time trend fitted on the TRAINING years only.

    Over 1940-2023 tropical SST warms substantially and regional precipitation may drift
    too. A permutation null destroys time ordering, so two series that merely share a
    trend produce a large apparent signal against it. Removing the trend asks the
    stricter and more useful question: is there interannual information beyond the drift?

    The trend is a fitted quantity, so like every other fitted quantity here it comes
    from the training fold and is then applied to the test years.
    """
    ok = np.isfinite(v[tr])
    if ok.sum() < 5:
        return v
    tt, vv = t[tr][ok], v[tr][ok]
    tm, vm = tt.mean(), vv.mean()
    dt = tt - tm
    denom = dt @ dt
    if denom <= 0:
        return v
    b = float(dt @ (vv - vm) / denom)
    return v - (vm + b * (t - tm))


def score_fast(comp, fname, y, folds, detrend=False, cond="all", comp0=None):
    """Pooled out-of-sample RPSS for one (feature, target) pair over precomputed folds."""
    rps_f, rps_c = [], []
    t = np.arange(len(y), dtype=float)
    for tr, te in folds:
        x = compose(fname, comp, tr)               # index re-fitted on THIS fold's train
        yf = y                                     # per-fold copy: never rebind `y`,
        if detrend:                                # or fold 2 detrends fold 1's output
            x = _detrend(x, tr, t)
            yf = _detrend(y, tr, t)
        xt, yt = x[tr], yf[tr]
        ok = np.isfinite(xt) & np.isfinite(yt)
        t33, t67 = _cpt_boundaries(yt)
        if ok.sum() < 10 or np.std(xt[ok]) == 0:
            p = np.full((len(te), 3), 1.0 / 3.0)
        else:
            xo, yo = xt[ok], yt[ok]
            mx, sx = xo.mean(), xo.std()
            xs = (xo - mx) / sx
            # closed-form OLS, identical to np.polyfit(xs, yo, 1)
            xm, ym = xs.mean(), yo.mean()
            dx = xs - xm
            b1 = float(dx @ (yo - ym) / (dx @ dx))
            b0 = float(ym - b1 * xm)
            resid = yo - (b0 + b1 * xs)
            sig = max(resid.std(ddof=2) if ok.sum() > 2 else yo.std(), 1e-9)
            mu = b0 + b1 * (x[te] - mx) / sx
            pb = _ncdf(t33, mu, sig)
            p67 = _ncdf(t67, mu, sig)
            p = np.stack([pb, p67 - pb, 1.0 - p67], axis=1)
            p[~np.isfinite(x[te])] = 1.0 / 3.0
        p = np.clip(p, 1e-9, 1.0)
        p = p / p.sum(1, keepdims=True)
        cat = np.where(t33 > yf[te], 0, np.where(t67 > yf[te], 1, 2))
        oh = np.stack([(cat == i).astype(float) for i in range(3)], axis=1)
        rf = np.sum((np.cumsum(p, 1) - np.cumsum(oh, 1)) ** 2, axis=1) / 2.0
        rc = np.sum((np.cumsum(np.full_like(p, 1 / 3), 1) - np.cumsum(oh, 1)) ** 2, axis=1) / 2.0
        if cond != "all":
            keep = condition_mask(cond, comp0, tr, te)
            rf, rc = rf[keep], rc[keep]
        rps_f.append(rf)
        rps_c.append(rc)
    f, c = np.concatenate(rps_f), np.concatenate(rps_c)
    if len(f) < MIN_SCORED or c.sum() <= 0:
        return np.nan, len(f)
    return 1.0 - f.sum() / c.sum(), len(f)


def precompute(folds_cache, n_folds, fixture=None, sst_prefix=None):
    """Targets per (region, window); features per (window, feature, gap, width).

    Years are intersected across every region within a window, so one permutation index
    applies coherently to all of them.
    """
    fixture = fixture or FIXTURE
    sst = bench.load_sst(sst_prefix or SST_PREFIX)
    targets, feats, yearsets = {}, {}, {}
    for wname, months in WINDOWS.items():
        per_region, common = {}, None
        for rname, bbox in REGIONS.items():
            try:
                yrs, vals = bench.build_target(fixture, bbox, months)
            except SystemExit as e:
                print(f"  [skip] {rname}/{wname}: {e}", flush=True)
                continue
            per_region[rname] = (yrs, vals)
            common = yrs if common is None else np.intersect1d(common, yrs)
        if common is None or len(common) < 25:
            continue
        yearsets[wname] = common
        for rname, (yrs, vals) in per_region.items():
            idx = np.searchsorted(yrs, common)
            targets[(rname, wname)] = vals[idx]

        # A year whose deepest predictor window (max gap + max width) falls before the
        # SST record cannot be scored for EVERY cell. The per-cell scorer silently used a
        # DIFFERENT year set per cell in that case, which quietly made cells
        # non-comparable; the batched path cannot do that at all. So drop such years once,
        # for the whole window, and every cell then sees an identical sample.
        ctx = bench.Context(sst, months, common, common, common, np.zeros(len(common)))
        probe = {(g, w): {b: ctx.feature(b, gap=g, width=w, years=common) for b in RAW_BOXES}
                 for g, w in itertools.product(GAPS, WIDTHS)}
        finite = np.ones(len(common), dtype=bool)
        for d in probe.values():
            for v in d.values():
                finite &= np.isfinite(v)
        if finite.sum() < 25:
            print(f"  [skip] {wname}: only {finite.sum()} years with full predictor coverage")
            continue
        if not finite.all():
            dropped = common[~finite]
            print(f"  {wname}: dropped {len(dropped)} year(s) lacking predictor coverage "
                  f"({', '.join(str(int(y)) for y in dropped)})", flush=True)
            common = common[finite]
            for rname in list(per_region):
                targets[(rname, wname)] = targets[(rname, wname)][finite]
        yearsets[wname] = common

        ctx = bench.Context(sst, months, common, common, common, np.zeros(len(common)))
        for gap, width in itertools.product(GAPS, WIDTHS):
            feats[(wname, gap, width)] = {
                b: ctx.feature(b, gap=gap, width=width, years=common) for b in RAW_BOXES}

        for proto in PROTOCOLS:
            folds_cache[(wname, proto)] = bench.make_folds(common, proto, n_folds)
    return targets, feats, yearsets


def feature_keys():
    """Fixed enumeration of the feature axis, shared by the batched and per-cell paths."""
    return [(f, g, w) for f in FEATURES for g in GAPS for w in WIDTHS]


def run_grid_batched(targets, feats, folds_cache, yearsets, perms=None, detrend=False,
                     conditions=("all",)):
    """Same grid as run_grid, evaluated as matrix operations. ~100x fewer Python-level
    iterations: one pass per (window, protocol) instead of one per cell."""
    keys = feature_keys()
    rows = []
    windows = sorted({w for _, w in targets})
    for wname in windows:
        regions = [r for (r, w) in targets if w == wname]
        Y = np.array([targets[(r, wname)] for r in regions], dtype=float)
        if perms is not None:
            Y = Y[:, perms[wname]]
        t = np.arange(Y.shape[1], dtype=float)
        comp0 = feats[(wname, COND_GAP, COND_WIDTH)]

        def build_X(tr, _w=wname):
            return np.array([compose(f, feats[(_w, g, wd)], tr) for f, g, wd in keys])

        cond_specs = [(c, None if c == "all"
                       else (lambda tr, te, _c=c: condition_mask(_c, comp0, tr, te)))
                      for c in conditions]

        for proto in PROTOCOLS:
            res = B.score_block_dynamic(build_X, Y, folds_cache[(wname, proto)], t,
                                        detrend=detrend, cond_specs=cond_specs,
                                        min_scored=MIN_SCORED)
            for cname, (rpss, nsc) in res.items():
                for i, (f, g, wd) in enumerate(keys):
                    for j, rname in enumerate(regions):
                        v = rpss[i, j]
                        if np.isfinite(v):
                            rows.append((rname, wname, f, g, wd, proto, cname,
                                         float(v), int(nsc[i, j])))
    return rows


def verify_batched(targets, feats, folds_cache, yearsets, conditions, n_check=40):
    """Second gate: batched must equal the per-cell scorer, which grid_sweep.verify has
    already checked against the LOCKED bench.evaluate. Chain: batched == score_fast ==
    bench.evaluate."""
    fast_rows = run_grid(targets, feats, folds_cache, conditions=conditions)
    bat_rows = run_grid_batched(targets, feats, folds_cache, yearsets, conditions=conditions)
    fd = {r[:7]: r[7] for r in fast_rows}
    bd = {r[:7]: r[7] for r in bat_rows}
    missing = set(fd) ^ set(bd)
    rng = np.random.default_rng(11)
    shared = sorted(set(fd) & set(bd))
    pick = [shared[i] for i in rng.choice(len(shared), min(n_check, len(shared)), replace=False)]
    worst, bad = 0.0, 0
    for k in pick:
        d = abs(fd[k] - bd[k])
        worst = max(worst, d)
        if d > 1e-8:
            bad += 1
            print(f"  MISMATCH {k} fast={fd[k]:+.8f} batched={bd[k]:+.8f} d={d:.2e}")
    print(f"  cells: per-cell {len(fd)}, batched {len(bd)}, symmetric-difference {len(missing)}")
    print(f"  checked {len(pick)} shared cells, max |diff| = {worst:.2e}, mismatches = {bad}")
    return bad + len(missing)


def run_grid(targets, feats, folds_cache, perms=None, detrend=False, conditions=("all",)):
    """Every cell of the grid. `perms[window]` permutes the year axis of every target
    for that window identically, so cross-region correlation survives into the null.
    Cells whose condition leaves fewer than MIN_SCORED test years are dropped."""
    rows = []
    for (rname, wname), y in targets.items():
        yy = y[perms[wname]] if perms is not None else y
        comp0 = feats[(wname, COND_GAP, COND_WIDTH)]
        for gap, width in itertools.product(GAPS, WIDTHS):
            comp = feats[(wname, gap, width)]
            for fname in FEATURES:
                for proto in PROTOCOLS:
                    for cname in conditions:
                        v, n = score_fast(comp, fname, yy, folds_cache[(wname, proto)],
                                          detrend, cname, comp0)
                        if np.isfinite(v):
                            rows.append((rname, wname, fname, gap, width, proto, cname, v, n))
    return rows


def verify(targets, feats, folds_cache, yearsets, n_folds, sst_prefix=None, n_check=16):
    """Cross-check the fast scorer against the locked bench.evaluate path.

    This gate has already earned its keep: it caught the composite-index standardization
    bug that made wpg and wvg disagree between the two paths.
    """
    import types
    sst = bench.load_sst(sst_prefix or SST_PREFIX)
    rng = np.random.default_rng(7)
    keys = list(targets)
    bad = 0
    print(f"verifying {n_check} random cells against bench.evaluate ...", flush=True)
    for _ in range(n_check):
        rname, wname = keys[rng.integers(len(keys))]
        fname = FEATURES[rng.integers(len(FEATURES))]
        gap = int(GAPS[rng.integers(len(GAPS))])
        width = int(WIDTHS[rng.integers(len(WIDTHS))])
        proto = PROTOCOLS[rng.integers(2)]

        y = targets[(rname, wname)]
        fast, _n = score_fast(feats[(wname, gap, width)], fname, y,
                              folds_cache[(wname, proto)])

        def fit_predict(ctx, _f=fname, _g=gap, _w=width):
            comp = {b: ctx.feature(b, gap=_g, width=_w, years=ctx.years) for b in RAW_BOXES}
            tr = np.isin(ctx.years, ctx.train_years)
            te = np.isin(ctx.years, ctx.test_years)
            x = compose(_f, comp, tr)              # train-fitted, applied to both
            xt, xe, yt = x[tr], x[te], ctx.y_train
            ok = np.isfinite(xt) & np.isfinite(yt)
            t33, t67 = _cpt_boundaries(yt)
            if ok.sum() < 10 or np.std(xt[ok]) == 0:
                return np.full((len(ctx.test_years), 3), 1 / 3)
            mx, sx = xt[ok].mean(), xt[ok].std()
            b1, b0 = np.polyfit((xt[ok] - mx) / sx, yt[ok], 1)
            resid = yt[ok] - (b0 + b1 * (xt[ok] - mx) / sx)
            sig = max(resid.std(ddof=2), 1e-9)
            mu = b0 + b1 * (xe - mx) / sx
            pb = norm.cdf(t33, loc=mu, scale=sig)
            p67 = norm.cdf(t67, loc=mu, scale=sig)
            p = np.stack([pb, p67 - pb, 1 - p67], axis=1)
            p[~np.isfinite(xe)] = 1 / 3
            return p / p.sum(1, keepdims=True)

        mod = types.ModuleType("tmpcand")
        mod.fit_predict = fit_predict
        rf, rc, _ = bench.evaluate(mod, sst, WINDOWS[wname], yearsets[wname], y,
                                   proto, n_folds)
        slow = 1.0 - rf.sum() / rc.sum()
        agree = abs(fast - slow) < 1e-8   # closed-form vs polyfit: float noise only
        bad += (not agree)
        print(f"  {rname:10s} {wname:6s} {fname:6s} g{gap} w{width} {proto:12s} "
              f"fast={fast:+.6f} bench={slow:+.6f} {'OK' if agree else 'MISMATCH'}")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-null", type=int, default=100)
    ap.add_argument("--folds", type=int, default=6)
    ap.add_argument("--verify", action="store_true", help="agreement check only, no sweep")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--out", default="outputs/grid_sweep.json")
    ap.add_argument("--domain", default="ca", choices=tuple(DOMAINS))
    ap.add_argument("--conditions", default="all",
                    help="comma-separated subset of " + ",".join(CONDITIONS))
    ap.add_argument("--windows", default=None,
                    help="comma-separated subset of the domain's windows")
    ap.add_argument("--fixture", default=FIXTURE)
    ap.add_argument("--sst-prefix", default=SST_PREFIX)
    ap.add_argument("--no-batched", action="store_true",
                    help="use the slow per-cell scorer (the batched path is default)")
    ap.add_argument("--detrend", action="store_true",
                    help="remove a train-fitted linear time trend from target and "
                         "predictor; asks whether signal survives beyond shared drift")
    a = ap.parse_args()

    global REGIONS, WINDOWS
    REGIONS = DOMAINS[a.domain]["regions"]
    WINDOWS = DOMAINS[a.domain]["windows"]
    if a.windows:
        keep = a.windows.split(",")
        WINDOWS = {k: v for k, v in WINDOWS.items() if k in keep}
        if len(WINDOWS) != len(keep):
            raise SystemExit(f"--windows {a.windows} not all in {list(DOMAINS[a.domain]['windows'])}")
    conditions = tuple(a.conditions.split(","))
    for c in conditions:
        if c not in CONDITIONS:
            raise SystemExit(f"unknown condition {c}; allowed: {CONDITIONS}")
    root = Path(__file__).resolve().parents[1]
    folds_cache = {}
    print("precomputing targets and features ...", flush=True)
    t0 = time.time()
    print(f"domain={a.domain}  fixture={a.fixture}  sst_prefix={a.sst_prefix}  "
          f"detrend={a.detrend}", flush=True)
    targets, feats, yearsets = precompute(folds_cache, a.folds, a.fixture, a.sst_prefix)
    n_cells = (len(targets) * len(FEATURES) * len(GAPS) * len(WIDTHS)
               * len(PROTOCOLS) * len(conditions))
    print(f"  {len(targets)} region-window targets, {len(feats)} feature vectors, "
          f"{n_cells} grid cells  ({time.time() - t0:.1f}s)", flush=True)
    for w, yy in yearsets.items():
        print(f"  window {w:6s}: {len(yy)} years {yy.min()}-{yy.max()}")

    bad = verify(targets, feats, folds_cache, yearsets, a.folds, a.sst_prefix)
    if bad:
        raise SystemExit(f"{bad} cell(s) disagree with bench.evaluate — sweep aborted")
    print("fast scorer agrees with the locked harness on every checked cell.", flush=True)
    if not a.no_batched:
        print("\nsecond gate: batched vs per-cell ...", flush=True)
        nb = verify_batched(targets, feats, folds_cache, yearsets, conditions)
        if nb:
            raise SystemExit(f"batched path disagrees on {nb} cell(s) - sweep aborted")
        print("batched path agrees with the per-cell scorer.", flush=True)
    print(flush=True)
    if a.verify:
        return

    grid = ((lambda **kw: run_grid(targets, feats, folds_cache, **kw)) if a.no_batched
            else (lambda **kw: run_grid_batched(targets, feats, folds_cache, yearsets, **kw)))

    t0 = time.time()
    real = grid(detrend=a.detrend, conditions=conditions)
    per_pass = time.time() - t0
    print(f"real grid: {len(real)} cells in {per_pass:.1f}s", flush=True)
    real_sorted = sorted(real, key=lambda r: -r[7])
    best_real = real_sorted[0][7]

    print(f"\nbuilding best-of-grid null, {a.n_null} replicates "
          f"(~{per_pass * a.n_null / 60:.1f} min) ...", flush=True)
    n_years = {w: len(y) for w, y in yearsets.items()}
    rng = np.random.default_rng(99)
    null_max, null_max_by_proto = [], {p: [] for p in PROTOCOLS}
    # Amendment 1: the null must be restricted to the family being asked about. Recording
    # each replicate's maximum PER FAMILY as well as globally costs nothing and is what
    # makes a per-season claim adjudicable at all.
    fam_null = {}          # family key -> list of per-replicate maxima
    t0 = time.time()
    for i in range(a.n_null):
        # ONE permutation per replicate per window, applied to every region's target
        perms = {w: rng.permutation(n) for w, n in n_years.items()}
        rows = grid(perms=perms, detrend=a.detrend, conditions=conditions)
        null_max.append(max(r[7] for r in rows))
        by_fam = {}
        for r in rows:
            for key in (r[1], f"{r[1]}/{r[6]}"):
                if r[7] > by_fam.get(key, -9e9):
                    by_fam[key] = r[7]
        for k, v in by_fam.items():
            fam_null.setdefault(k, []).append(v)
        for p in PROTOCOLS:
            vals = [r[7] for r in rows if r[5] == p]
            if vals:
                null_max_by_proto[p].append(max(vals))
        if (i + 1) % 10 == 0:
            print(f"  {i + 1}/{a.n_null}  ({time.time() - t0:.0f}s elapsed)", flush=True)

    null_max = np.array(null_max)
    p_val = float((1 + (null_max >= best_real).sum()) / (a.n_null + 1))

    print(f"\n{'=' * 78}\nBEST-OF-GRID RESULT\n{'=' * 78}")
    print(f"grid cells                {n_cells}")
    print(f"best real RPSS            {best_real:+.4f}")
    print(f"best-of-grid null mean    {null_max.mean():+.4f} +/- {null_max.std():.4f}")
    print(f"best-of-grid null p95     {np.percentile(null_max, 95):+.4f}")
    print(f"best-of-grid null max     {null_max.max():+.4f}")
    print(f"one-sided p               {p_val:.4f}   ({a.n_null} replicates)")
    print(f"-> {'SIGNAL: the grid beats what noise produces' if p_val <= 0.05 else 'NO SIGNAL: the best cell is what searching noise this hard produces anyway'}")

    # ── per-family verdicts (Amendment 1) ────────────────────────────────────
    real_by_fam = {}
    for r in real:
        for key in (r[1], f"{r[1]}/{r[6]}"):
            if r[7] > real_by_fam.get(key, (-9e9,))[0]:
                real_by_fam[key] = (r[7], r)
    print(f"\n{'=' * 96}\nPER-FAMILY RESULT (null restricted to each family; see "
          f"PREREGISTRATION_conditional_AMENDMENT.md)\n{'=' * 96}")
    print(f"{'family':16s} {'best real':>10s} {'null mean':>10s} {'null p95':>9s} "
          f"{'p':>7s}  {'verdict':7s}  winning cell")
    print("-" * 112)
    fam_out = {}
    for key in sorted(fam_null, key=lambda k: (len(k.split('/')), k)):
        nv = np.array(fam_null[key])
        if key not in real_by_fam:
            continue
        rb, rr = real_by_fam[key]
        pv = float((1 + (nv >= rb).sum()) / (len(nv) + 1))
        verdict = "CLEARS" if pv <= 0.05 else "no"
        cell = f"{rr[0]} {rr[2]} g{rr[3]} w{rr[4]} {rr[5]} n={rr[8]}"
        print(f"{key:16s} {rb:+10.4f} {nv.mean():+10.4f} {np.percentile(nv, 95):+9.4f} "
              f"{pv:7.4f}  {verdict:7s}  {cell}")
        fam_out[key] = dict(best_real=round(float(rb), 4), null_mean=round(float(nv.mean()), 4),
                            null_p95=round(float(np.percentile(nv, 95)), 4),
                            p_value=round(pv, 4), clears=bool(pv <= 0.05), cell=cell)

    print(f"\ntop {a.top} cells (read against the null above, not against zero):")
    print(f"{'region':13s} {'window':7s} {'feat':7s} {'gap':>3s} {'w':>2s} {'protocol':12s} "
          f"{'condition':10s} {'n':>4s} {'rpss':>8s}")
    print("-" * 78)
    for r in real_sorted[:a.top]:
        print(f"{r[0]:13s} {r[1]:7s} {r[2]:7s} {r[3]:3d} {r[4]:2d} {r[5]:12s} "
              f"{r[6]:10s} {r[8]:4d} {r[7]:+8.4f}")

    out = root / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "domain": a.domain, "fixture": a.fixture,
        "sst_prefix": a.sst_prefix, "detrend": a.detrend,
        "n_cells": n_cells, "n_null": a.n_null,
        "best_real": round(float(best_real), 4),
        "null_mean": round(float(null_max.mean()), 4),
        "null_sd": round(float(null_max.std()), 4),
        "null_p95": round(float(np.percentile(null_max, 95)), 4),
        "null_max": round(float(null_max.max()), 4),
        "p_value": round(p_val, 4),
        "null_p95_by_protocol": {p: round(float(np.percentile(v, 95)), 4)
                                 for p, v in null_max_by_proto.items()},
        "conditions": list(conditions),
        "families": fam_out,
        "top": [dict(region=r[0], window=r[1], feature=r[2], gap=r[3], width=r[4],
                     protocol=r[5], condition=r[6], n_scored=r[8],
                     rpss=round(float(r[7]), 4)) for r in real_sorted[:100]],
    }, indent=2))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
