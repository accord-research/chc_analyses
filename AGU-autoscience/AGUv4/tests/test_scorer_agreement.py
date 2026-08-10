"""test_scorer_agreement.py — SPEC 16: the fast atlas scorer must equal the slow one.

atlas_score.py replaces an explicit leave-one-year-out loop with a closed-form identity,
np.polyfit with a hand-rolled OLS, scipy.stats.norm.cdf with erf, and a per-predictor
loop with one matrix pass. Each of those is a place a plausible wrong number can be born.
atlas_score_slow.py does none of them, so agreement to 1e-8 is the evidence that the fast
path is what SPEC 10 describes.

The comparison runs on real folds AND on permutation replicates, because SPEC 16 requires
the sampled-replicate check rather than a development-time-only check.

Run: conda run -n pycpt python tests/test_scorer_agreement.py
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "harness"))

import bench                       # noqa: E402
import fields as F                 # noqa: E402
import discovery as D              # noqa: E402
import indices as IX               # noqa: E402
import atlas_score as A            # noqa: E402
import atlas_score_slow as S       # noqa: E402

TOL = 1e-8


def _key(fc):
    return (fc.zone, fc.window)


def compare(fast, slow, label, tol=TOL):
    """Every Forecast field that could differ, checked one by one."""
    fd = {_key(f): f for f in fast}
    sd = {_key(f): f for f in slow}
    problems = []
    if set(fd) != set(sd):
        problems.append(f"different zone-windows: fast {sorted(set(fd) - set(sd))}, "
                        f"slow {sorted(set(sd) - set(fd))}")
    worst = 0.0
    for k in sorted(set(fd) & set(sd)):
        a, b = fd[k], sd[k]
        if (a.index, a.lead) != (b.index, b.lead):
            problems.append(f"{k}: selected {a.index} lead-{a.lead} vs "
                            f"{b.index} lead-{b.lead}")
        for field in ("weight", "zone_share"):
            d = abs(getattr(a, field) - getattr(b, field))
            worst = max(worst, d)
            if d > tol:
                problems.append(f"{k}: {field} differs by {d:.3e}")
        for field in ("probs", "rps_f", "rps_c", "obs"):
            x, y = np.asarray(getattr(a, field)), np.asarray(getattr(b, field))
            if x.shape != y.shape:
                problems.append(f"{k}: {field} shape {x.shape} vs {y.shape}")
                continue
            d = float(np.max(np.abs(x - y))) if x.size else 0.0
            worst = max(worst, d)
            if d > tol:
                problems.append(f"{k}: {field} max|diff| = {d:.3e}")
    rf = A.pool([fast], select=lambda f: f.discovered)[0]
    rs = A.pool([slow], select=lambda f: f.discovered)[0]
    d = abs(rf - rs)
    worst = max(worst, d)
    if d > tol:
        problems.append(f"pooled RPSS differs by {d:.3e} ({rf:+.10f} vs {rs:+.10f})")
    status = "OK" if not problems else "MISMATCH"
    print(f"  {status:8s} {label:36s} max|diff| = {worst:.3e}   "
          f"RPSS fast {rf:+.8f} slow {rs:+.8f}", flush=True)
    for p in problems:
        print(f"           {p}")
    return problems


def main():
    fld = F.load_chirps()
    sst = IX.load_boxes()
    folds = bench.make_folds(fld.years, "walkforward", 6)
    forced = [("MAM", [3, 4, 5])]
    problems = []

    print("SPEC 16 — atlas fast path vs slow reference (tolerance 1e-8)\n")
    print("real folds:")
    rng = np.random.default_rng(3)
    check_folds = [1, 3, 5]
    parts = {}
    for fi in check_folds:
        tr_i, te_i = folds[fi]
        tr_y, te_y = fld.years[tr_i], fld.years[te_i]
        part = D.discover(fld.monthly, fld.month_of_col, fld.year_of_col, tr_y,
                          fld.lats, fld.lons)
        parts[fi] = (part, tr_y, te_y)
        for arm in ("zones-specific", "zones-shared", "climatology"):
            fast = A.score_fold(part, fld.monthly, fld.month_of_col, fld.year_of_col,
                                fld.years, tr_y, te_y, sst, arm=arm, forced_windows=forced)
            slow = S.score_fold_slow(part, fld.monthly, fld.month_of_col, fld.year_of_col,
                                     fld.years, tr_y, te_y, sst, arm=arm,
                                     forced_windows=forced)
            problems += compare(fast, slow, f"fold {fi} / {arm}")

    print("\nleaky arm (SPEC 9.2, full-record WPG/WVG standardisation):")
    part, tr_y, te_y = parts[5]
    fast = A.score_fold(part, fld.monthly, fld.month_of_col, fld.year_of_col, fld.years,
                        tr_y, te_y, sst, leak=True, forced_windows=forced)
    slow = S.score_fold_slow(part, fld.monthly, fld.month_of_col, fld.year_of_col,
                             fld.years, tr_y, te_y, sst, leak=True, forced_windows=forced)
    problems += compare(fast, slow, "fold 5 / leaky")

    print("\nrainfall-share weighting (SPEC 10's pre-registered variant):")
    fast = A.score_fold(part, fld.monthly, fld.month_of_col, fld.year_of_col, fld.years,
                        tr_y, te_y, sst, weight_rule="rain", forced_windows=forced)
    slow = S.score_fold_slow(part, fld.monthly, fld.month_of_col, fld.year_of_col,
                             fld.years, tr_y, te_y, sst, weight_rule="rain",
                             forced_windows=forced)
    problems += compare(fast, slow, "fold 5 / rainfall-share")

    print("\npermutation replicates (SPEC 16 requires sampled replicates, not just folds).")
    print("A replicate permutes the FIELD and re-runs discovery, so these compare the")
    print("complete null pipeline, not a re-scoring of the real atlas:")
    for r in range(3):
        fi = check_folds[r]
        _, tr_y, te_y = parts[fi]
        perm = np.random.default_rng(4242 + r).permutation(len(fld.years))
        pm = F.permute_field(fld, perm)
        ppart = D.discover(pm, fld.month_of_col, fld.year_of_col, tr_y,
                           fld.lats, fld.lons)
        fast = A.score_fold(ppart, pm, fld.month_of_col, fld.year_of_col,
                            fld.years, tr_y, te_y, sst, forced_windows=forced)
        slow = S.score_fold_slow(ppart, pm, fld.month_of_col, fld.year_of_col,
                                 fld.years, tr_y, te_y, sst, forced_windows=forced)
        problems += compare(fast, slow, f"fold {fi} / permutation {r} (k={ppart.k})")

    print(f"\n{'PASS' if not problems else 'FAIL'}: "
          f"{len(problems)} disagreement(s) at tolerance {TOL}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
