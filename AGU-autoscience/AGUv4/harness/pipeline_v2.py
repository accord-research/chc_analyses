"""pipeline_v2.py — the atlas pipeline under SPEC Amendment 1.

Two changes from pipeline.py, both from Amendment 1:

  1. Every zone-window in a fold is scored on the fold's COMMON usable year set, so one
     donor map is valid across zones and windows. The real run and the null therefore
     share their support exactly and differ only in whether the target is permuted.

  2. The null is a complete-season TARGET permutation. Discovery runs once per fold on
     unpermuted training rainfall and is reused by every replicate; the permutation acts
     on assembled seasonal totals, so a wrapping window can never be spliced from two
     donor years.

Consequence for cost: discovery runs 6 times per protocol instead of 1,200 times.

pipeline.py is left untouched because atlas-wf-v1 locks it and that pilot record is
preserved.
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
import nullperm as NP              # noqa: E402
import pipeline as P               # noqa: E402

FORCED_MAM = P.FORCED_MAM
FAMILIES = P.FAMILIES

_DISCOVERY_CACHE = {}


def discover_folds(protocol="walkforward", n_folds=6, force_k=None):
    """Discovery from UNPERMUTED training rainfall, once per (protocol, k-mode).

    Amendment 1 3.2: discovery consults neither SST nor any score, and every discovered
    zone-window is scored, so it is not a skill-selected axis and the null has nothing to
    pay for there. It is therefore computed once and shared by every replicate.
    """
    key = (protocol, n_folds, force_k)
    if key in _DISCOVERY_CACHE:
        return _DISCOVERY_CACHE[key]
    fld, sst = P.get_state()
    out = []
    for tr_i, te_i in bench.make_folds(fld.years, protocol, n_folds):
        tr_y, te_y = fld.years[tr_i], fld.years[te_i]
        part = D.discover(fld.monthly, fld.month_of_col, fld.year_of_col, tr_y,
                          fld.lats, fld.lons, force_k=force_k)
        usable = NP.common_usable(part, fld.monthly, fld.month_of_col, fld.year_of_col,
                                  fld.years, sst, forced_windows=FORCED_MAM)
        out.append((part, tr_y, te_y, usable))
    _DISCOVERY_CACHE[key] = out
    return out


def run_atlas_v2(protocol="walkforward", n_folds=6, arm="zones-specific", leak=False,
                 perm=None, force_k=None, weight_rule="equal"):
    """Returns (fold_forecasts, folds, parts). `perm=None` is the real run."""
    fld, sst = P.get_state()
    disc = discover_folds(protocol, n_folds, force_k)
    out, folds, parts = [], [], []
    for part, tr_y, te_y, usable in disc:
        fcs = NP.score_fold_target_perm(
            part, fld.monthly, fld.month_of_col, fld.year_of_col, fld.years,
            tr_y, te_y, sst, usable, perm=perm, arm=arm, leak=leak,
            forced_windows=FORCED_MAM, weight_rule=weight_rule)
        out.append(fcs)
        folds.append((tr_y, te_y))
        parts.append(part)
    return out, folds, parts


def score_families(fold_forecasts, folds, families=FAMILIES):
    return P.score_families(fold_forecasts, folds, families=families)


def replicate_all_arms(rep, perms, protocol="walkforward", n_folds=6):
    """One replicate, all three arms, from the shared unpermuted discovery.

    `perms` is the full list from nullperm.permutations(), so replicate r always uses
    perms[r] no matter which worker runs it or in what order.
    """
    perm = perms[rep]
    rows = []
    for arm, fk in (("zones-specific", None), ("zones-shared", None), ("pooled", 1)):
        ff, folds, parts = run_atlas_v2(protocol=protocol, n_folds=n_folds,
                                        arm="zones-specific" if arm == "pooled" else arm,
                                        perm=perm, force_k=fk)
        rows.append({"replicate": rep, "arm": arm, "protocol": protocol,
                     "families": score_families(ff, folds),
                     "zones_per_fold": [int(p.k) for p in parts]})
    return rows


def sensitivity_field_perm(rep, protocol="walkforward", n_folds=6, seed=4242):
    """Amendment 1 3.4: the v1 calendar-year field permutation, retained as a labelled
    sensitivity analysis ONLY.

    A calendar-year field permutation cannot preserve complete outcomes for wrapping
    windows, because NDJ splices November-December from one donor year with January from
    another. It adjudicates nothing.
    """
    fld, _ = P.get_state()
    perm = np.random.default_rng(seed + rep).permutation(len(fld.years))
    ff, folds, parts = P.run_atlas(protocol=protocol, n_folds=n_folds, perm=perm,
                                   collect_parts=True)
    wrapping = sorted({fc.window for fold in ff for fc in fold
                       if fc.months[0] > fc.months[-1]})
    return {"replicate": rep, "arm": "zones-specific", "protocol": protocol,
            "families": P.score_families(ff, folds),
            "zones_per_fold": [int(p.k) for p in parts],
            "wrapping_windows_present": wrapping,
            "caveat": "calendar-year field permutation splices wrapping seasons across "
                      "donor years; sensitivity analysis only"}
