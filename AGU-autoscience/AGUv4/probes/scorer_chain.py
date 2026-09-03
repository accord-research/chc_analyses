"""scorer_chain.py — SPEC 16's THREE agreement links, all of them, actually run.

The v1 gate ran only the third link. SPEC names three, and the first two are the chain
v4zeek built and this project inherited, so leaving them unexecuted meant inheriting the
code without inheriting the evidence.

    link 1   batched.score_block_dynamic   ==   grid_sweep.score_fast
    link 2   grid_sweep.score_fast         ==   bench.evaluate       (the LOCKED path)
    link 3   atlas_score.score_fold        ==   atlas_score_slow.score_fold_slow

Links 1 and 2 are run here against this project's own fixtures rather than v4zeek's:
grid_sweep.precompute wants per-box `sst_*_monthly.nc` files that do not exist here, so
the SST components come from indices.load_boxes() -- which returns exactly the structure
bench.Context expects -- and the targets from bench.build_target on the CHIRPS fixture.
The scorers themselves are the inherited ones, unmodified.

Tolerance 1e-8 on every link. Any failure aborts.

Run: rx run exec -e e:N -- conda run -n pycpt python probes/scorer_chain.py
"""
from __future__ import annotations

import itertools
import json
import sys
import types
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "harness"))
sys.path.insert(0, str(ROOT / "probes"))

import bench                                          # noqa: E402
import batched as B                                   # noqa: E402
import grid_sweep as G                                # noqa: E402
import indices as IX                                  # noqa: E402
from africas2s.metrics.rpss import _cpt_boundaries    # noqa: E402

TOL = 1e-8
FIXTURE = "chirps_v3_ea_monthly.nc"
# A handful of real sub-regions of the locked domain; the point is the scorer chain,
# not these boxes, so they are simply a spread of shapes.
REGIONS = {"ea-whole": [-5.0, 12.0, 33.0, 52.0],
           "ehorn": [-4.5, 8.5, 38.0, 50.5],
           "kenya": [-4.7, 5.0, 33.9, 41.9],
           "somalia": [-1.7, 12.0, 41.0, 51.4]}
WINDOWS = {"OND": [10, 11, 12], "MAM": [3, 4, 5], "JAS": [7, 8, 9]}
GAPS, WIDTHS = (0, 1, 2, 3, 4), (1, 2, 3)
PROTOCOLS = ("walkforward", "kfold")
N_FOLDS = 6

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok)))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   {detail}" if detail else ""),
          flush=True)


def rule(t):
    print(f"\n{'=' * 78}\n{t}\n{'=' * 78}", flush=True)


def build():
    """Targets, features and folds, using this project's fixtures."""
    sst = IX.load_boxes()
    targets, feats, yearsets, folds_cache = {}, {}, {}, {}
    for wname, months in WINDOWS.items():
        per_region, common = {}, None
        for rname, bbox in REGIONS.items():
            yrs, vals = bench.build_target(FIXTURE, bbox, months)
            per_region[rname] = (yrs, vals)
            common = yrs if common is None else np.intersect1d(common, yrs)
        for rname, (yrs, vals) in per_region.items():
            targets[(rname, wname)] = vals[np.searchsorted(yrs, common)]

        # drop years lacking full predictor coverage once per window, as grid_sweep does
        ctx = bench.Context(sst, months, common, common, common, np.zeros(len(common)))
        finite = np.ones(len(common), dtype=bool)
        for g, w in itertools.product(GAPS, WIDTHS):
            for b in G.RAW_BOXES:
                finite &= np.isfinite(ctx.feature(b, gap=g, width=w, years=common))
        if not finite.all():
            common = common[finite]
            for rname in per_region:
                targets[(rname, wname)] = targets[(rname, wname)][finite]
        yearsets[wname] = common
        ctx = bench.Context(sst, months, common, common, common, np.zeros(len(common)))
        for g, w in itertools.product(GAPS, WIDTHS):
            feats[(wname, g, w)] = {b: ctx.feature(b, gap=g, width=w, years=common)
                                    for b in G.RAW_BOXES}
        for proto in PROTOCOLS:
            folds_cache[(wname, proto)] = bench.make_folds(common, proto, N_FOLDS)
    return sst, targets, feats, yearsets, folds_cache


def link2(sst, targets, feats, yearsets, folds_cache, n_check=16, seed=7):
    """per-cell score_fast  ==  the LOCKED bench.evaluate."""
    rng = np.random.default_rng(seed)
    keys = list(targets)
    worst, bad = 0.0, 0
    for _ in range(n_check):
        rname, wname = keys[rng.integers(len(keys))]
        fname = G.FEATURES[rng.integers(len(G.FEATURES))]
        gap = int(GAPS[rng.integers(len(GAPS))])
        width = int(WIDTHS[rng.integers(len(WIDTHS))])
        proto = PROTOCOLS[rng.integers(2)]
        y = targets[(rname, wname)]
        fast, _ = G.score_fast(feats[(wname, gap, width)], fname, y,
                               folds_cache[(wname, proto)])

        def fit_predict(ctx, _f=fname, _g=gap, _w=width):
            comp = {b: ctx.feature(b, gap=_g, width=_w, years=ctx.years)
                    for b in G.RAW_BOXES}
            tr = np.isin(ctx.years, ctx.train_years)
            te = np.isin(ctx.years, ctx.test_years)
            x = G.compose(_f, comp, tr)
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
            pb, p67 = norm.cdf(t33, mu, sig), norm.cdf(t67, mu, sig)
            p = np.stack([pb, p67 - pb, 1 - p67], axis=1)
            p[~np.isfinite(xe)] = 1 / 3
            return p / p.sum(1, keepdims=True)

        mod = types.ModuleType("tmp")
        mod.fit_predict = fit_predict
        rf, rc, _ = bench.evaluate(mod, sst, WINDOWS[wname], yearsets[wname], y,
                                   proto, N_FOLDS)
        slow = 1.0 - rf.sum() / rc.sum()
        d = abs(fast - slow)
        worst = max(worst, d)
        bad += d > TOL
        print(f"    {rname:10s} {wname:4s} {fname:7s} g{gap} w{width} {proto:12s} "
              f"fast {fast:+.8f}  bench {slow:+.8f}  |d| {d:.1e}", flush=True)
    return worst, bad


def link1(targets, feats, yearsets, folds_cache, n_check=60, seed=11):
    """batched score_block_dynamic  ==  per-cell score_fast."""
    keys = G.feature_keys()
    fd, bd, expected = {}, {}, set()
    rng0 = np.random.default_rng(seed)
    sample_keys = {}
    for wname in sorted({w for _, w in targets}):
        regs = [r for (r, w) in targets if w == wname]
        for proto in PROTOCOLS:
            allk = [(r, wname, f, g, wd, proto) for r in regs for f, g, wd in keys]
            idx = rng0.choice(len(allk), min(n_check // 6 + 1, len(allk)), replace=False)
            sample_keys[(wname, proto)] = [allk[i] for i in idx]
    for wname in sorted({w for _, w in targets}):
        regions = [r for (r, w) in targets if w == wname]
        Y = np.array([targets[(r, wname)] for r in regions], dtype=float)
        t = np.arange(Y.shape[1], dtype=float)

        def build_X(tr, _w=wname):
            return np.array([G.compose(f, feats[(_w, g, wd)], tr) for f, g, wd in keys])

        for proto in PROTOCOLS:
            res = B.score_block_dynamic(build_X, Y, folds_cache[(wname, proto)], t,
                                        cond_specs=(("all", None),),
                                        min_scored=G.MIN_SCORED)
            rpss, _ = res["all"]
            for i, (f, g, wd) in enumerate(keys):
                for j, rname in enumerate(regions):
                    if np.isfinite(rpss[i, j]):
                        bd[(rname, wname, f, g, wd, proto)] = float(rpss[i, j])
            # The per-cell path is the slow one, so it runs on a SAMPLE. Coverage is
            # still compared over the full key set below, which is what the
            # symmetric-difference check needs.
            for i, (f, g, wd) in enumerate(keys):
                for j, rname in enumerate(regions):
                    expected.add((rname, wname, f, g, wd, proto))
            for k in sample_keys[wname, proto]:
                rname, _, f, g, wd, _ = k
                v, _ = G.score_fast(feats[(wname, g, wd)], f, targets[(rname, wname)],
                                    folds_cache[(wname, proto)])
                if np.isfinite(v):
                    fd[k] = float(v)
    missing = expected ^ set(bd)
    shared = sorted(set(fd) & set(bd))
    rng = np.random.default_rng(seed)
    pick = [shared[i] for i in rng.choice(len(shared), min(n_check, len(shared)),
                                          replace=False)]
    worst = max(abs(fd[k] - bd[k]) for k in shared)
    bad = sum(1 for k in shared if abs(fd[k] - bd[k]) > TOL)
    return worst, bad, len(expected), len(bd), len(missing), len(shared)


def main():
    rule("SPEC 16 — ALL THREE SCORER-AGREEMENT LINKS")
    print("building targets and features from this project's locked fixtures ...",
          flush=True)
    sst, targets, feats, yearsets, folds_cache = build()
    print(f"  {len(targets)} region-window targets, {len(feats)} feature blocks")
    for w, yy in yearsets.items():
        print(f"  window {w}: {len(yy)} years {yy.min()}-{yy.max()}")

    rule("LINK 2 — per-cell score_fast == the LOCKED bench.evaluate")
    w2, b2 = link2(sst, targets, feats, yearsets, folds_cache)
    check("per-cell scorer agrees with bench.evaluate on every checked cell", b2 == 0,
          f"max |diff| = {w2:.2e}, {b2} mismatches, tolerance {TOL}")

    rule("LINK 1 — batched score_block_dynamic == per-cell score_fast")
    w1, b1, nf, nb, nmiss, npick = link1(targets, feats, yearsets, folds_cache)
    check("the batched and per-cell paths cover the identical cell set", nmiss == 0,
          f"per-cell {nf}, batched {nb}, symmetric difference {nmiss}")
    check("batched agrees with the per-cell scorer on every checked cell", b1 == 0,
          f"checked {npick}, max |diff| = {w1:.2e}, {b1} mismatches")

    rule("LINK 3 — atlas fast == atlas slow reference")
    import subprocess
    r = subprocess.run([sys.executable, str(ROOT / "tests" / "test_scorer_agreement.py")],
                       capture_output=True, text=True)
    tail = [ln for ln in r.stdout.splitlines() if ln.strip().startswith(("OK", "MISMATCH",
                                                                        "PASS", "FAIL"))]
    for ln in tail[-4:]:
        print("   ", ln.strip())
    check("the atlas fast path agrees with the atlas slow reference", r.returncode == 0,
          f"{sum(1 for ln in tail if ln.strip().startswith('OK'))} comparisons OK")

    rule("VERDICT")
    nf_ = sum(1 for _, ok in RESULTS if not ok)
    print(f"  {len(RESULTS) - nf_}/{len(RESULTS)} links passed")
    out = {"links": len(RESULTS), "passed": len(RESULTS) - nf_, "failed": nf_,
           "link1_batched_vs_percell_maxdiff": float(w1),
           "link2_percell_vs_bench_maxdiff": float(w2),
           "tolerance": TOL,
           "status": "ok" if nf_ == 0 else "failed"}
    (ROOT / "outputs").mkdir(exist_ok=True)
    (ROOT / "outputs" / "scorer_chain.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out))
    sys.exit(1 if nf_ else 0)


if __name__ == "__main__":
    main()
