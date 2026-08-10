"""pipeline.py — one atlas run: discover in every fold, forecast, score.

Everything that needs a complete atlas goes through `run_atlas`: the real result, the
leaky and clean OOS arms, the gates, and every one of the 1,200 null replicates. Having
one entry point is what stops the null from quietly differing from the real run.

A null replicate is `run_atlas(..., perm=pi)`. That permutes the FIELD and re-runs
discovery inside every fold, which is what SPEC 14 requires and why the null costs 1,200
discovery runs rather than 1,200 re-scorings.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "harness"))

import bench                       # noqa: E402
import fields as F                 # noqa: E402
import discovery as D              # noqa: E402
import indices as IX               # noqa: E402
import atlas_score as A            # noqa: E402

FORCED_MAM = [("MAM", [3, 4, 5])]
FAMILIES = ("atlas/all-windows", "MAM/all", "MAM/lanina", "MAM/neg_wvg")

_STATE = {}


def get_state():
    """Fixtures, loaded once per process. Workers inherit or rebuild from cache."""
    if "fld" not in _STATE:
        _STATE["fld"] = F.load_chirps()
        _STATE["sst"] = IX.load_boxes()
    return _STATE["fld"], _STATE["sst"]


def run_atlas(protocol="walkforward", n_folds=6, arm="zones-specific", leak=False,
              perm=None, force_k=None, weight_rule="equal", monthly=None,
              collect_parts=False, slow=False):
    """Returns (fold_forecasts, folds, parts).

    fold_forecasts  list of lists of Forecast, one inner list per fold
    folds           list of (train_years, test_years)
    parts           list of Partition (empty unless collect_parts)
    """
    fld, sst = get_state()
    mm = fld.monthly if monthly is None else monthly
    if perm is not None:
        mm = F.permute_field(fld, perm)

    scorer = A.score_fold
    if slow:
        import atlas_score_slow as S
        scorer = S.score_fold_slow

    out, folds, parts = [], [], []
    for tr_i, te_i in bench.make_folds(fld.years, protocol, n_folds):
        tr_y, te_y = fld.years[tr_i], fld.years[te_i]
        part = D.discover(mm, fld.month_of_col, fld.year_of_col, tr_y,
                          fld.lats, fld.lons, force_k=force_k)
        fcs = scorer(part, mm, fld.month_of_col, fld.year_of_col, fld.years,
                     tr_y, te_y, sst, arm=arm, leak=leak,
                     forced_windows=FORCED_MAM, weight_rule=weight_rule)
        out.append(fcs)
        folds.append((tr_y, te_y))
        parts.append(part if collect_parts else None)
    return out, folds, parts


def score_families(fold_forecasts, folds, families=FAMILIES):
    """SPEC 14's four scoring families from one set of forecasts (SPEC 6/8 sharing)."""
    fld, sst = get_state()
    res = {}
    for fam in families:
        sel = A.family_selector(fam)
        wt = A.family_weight(fam)
        cond = "all" if fam in ("atlas/all-windows", "MAM/all") else fam.split("/")[1]
        ff = A.apply_condition(fold_forecasts, cond, sst, fld.years, folds)
        rpss, n = A.pool(ff, select=sel, weight=wt)
        res[fam] = {"rpss": rpss, "n_scored": n,
                    "coverage": A.coverage(ff, select=sel, weight=wt,
                                           n_folds=len(fold_forecasts))}
    return res


def replicate(rep, protocol="walkforward", n_folds=6, arm="zones-specific", leak=False,
              seed=4242):
    """One null replicate: draw permutation `rep`, run the complete pipeline, score all
    four families. Deterministic in `rep` alone, so workers need no shared RNG."""
    fld, _ = get_state()
    rng = np.random.default_rng(seed + rep)
    perm = rng.permutation(len(fld.years))
    ff, folds, _ = run_atlas(protocol=protocol, n_folds=n_folds, arm=arm, leak=leak,
                             perm=perm)
    fam = score_families(ff, folds)
    ks = []
    for fold in ff:
        ks.append(len({fc.zone for fc in fold}))
    return {"replicate": rep, "arm": arm, "protocol": protocol,
            "families": fam, "zones_per_fold": ks}
