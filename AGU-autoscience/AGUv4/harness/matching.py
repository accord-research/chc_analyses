"""matching.py — SPEC 11: fold-to-fold stability, measured independently of skill.

NOTHING IN THIS FILE REACHES A SCORE. Matching, the reference frame, tracks, orphans and
the two coverage bars exist to describe how the discovered objects behave across folds.
The aggregate atlas score is fold-local (SPEC 10, SPEC 12.1) and never consults a track.

The reference frame is fold 5's training partition (1981-2019). Walk-forward training
sets are nested, so fold 5's is the superset of every other fold's, and it excludes fold
5's own test years. Matching is one-to-one by Hungarian assignment on cell overlap, so
tracks can neither split nor merge; unmatched zones in a fold are ORPHANS and unmatched
reference zones are ABSENCES, and both are reported rather than dropped.

The headline stability claim rests on the matching-free metrics -- mean pairwise ARI over
the 15 fold pairs, and the per-cell switch map -- so the story never depends on the
choice of reference frame.
"""
from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.stats import spearmanr
from sklearn.metrics import adjusted_rand_score

MIN_FOLDS_FOR_H1 = 4          # SPEC 11
MIN_SCORED = 8                # SPEC 12.2, pooled across folds
ENUM_CAP = 200_000            # SPEC 11 / 20.5
ORPHAN_UNRELIABLE = 0.20      # SPEC 11

PREDICTOR_GROUP = {"nino34": "Pacific-ENSO", "iod": "Indian-dipole",
                   "wpg": "Pacific-gradient", "wvg": "Pacific-gradient",
                   "iwhg": "composite"}


@dataclass
class Track:
    ref_zone: int
    member: dict = field(default_factory=dict)     # fold -> zone id in that fold
    cells: dict = field(default_factory=dict)      # fold -> cell index array

    @property
    def n_folds(self):
        return len(self.member)


def _labels_by_cell(part, n_cell):
    lab = np.full(n_cell, -1, dtype=int)
    lab[part.cell_index] = part.labels
    return lab


def pairwise_ari(parts, n_cell):
    """Matching-free. ARI between every fold pair on the cells valid in both."""
    n = len(parts)
    M = np.full((n, n), np.nan)
    labs = [_labels_by_cell(p, n_cell) for p in parts]
    for a in range(n):
        for b in range(n):
            if a == b:
                M[a, b] = 1.0
                continue
            m = (labs[a] >= 0) & (labs[b] >= 0)
            M[a, b] = adjusted_rand_score(labs[a][m], labs[b][m])
    return M


def switch_map(parts, n_cell, ref_index=-1):
    """Matching-free. For each cell, the fraction of fold pairs whose aligned labels
    disagree. Alignment is to the reference frame so the labels are comparable."""
    labs = [_labels_by_cell(p, n_cell) for p in parts]
    ref = labs[ref_index]
    aligned = []
    for i, p in enumerate(parts):
        amap = align_to_reference(parts[ref_index], p, n_cell)
        a = np.full(n_cell, -1, dtype=int)
        for zf, zr in amap.items():
            a[labs[i] == zf] = zr
        aligned.append(a)
    n = len(parts)
    switch = np.zeros(n_cell)
    cnt = np.zeros(n_cell)
    for a, b in itertools.combinations(range(n), 2):
        m = (aligned[a] >= 0) & (aligned[b] >= 0)
        switch[m] += (aligned[a][m] != aligned[b][m])
        cnt[m] += 1
    out = np.full(n_cell, np.nan)
    ok = cnt > 0
    out[ok] = switch[ok] / cnt[ok]
    return out, ref


def align_to_reference(ref_part, part, n_cell):
    """Hungarian assignment of `part`'s zones onto `ref_part`'s, by cell overlap.

    Returns {zone_in_part: ref_zone}. Only min(k_part, k_ref) zones appear; the rest are
    orphans (SPEC 11).
    """
    lr = _labels_by_cell(ref_part, n_cell)
    lp = _labels_by_cell(part, n_cell)
    shared = (lr >= 0) & (lp >= 0)
    ov = np.zeros((part.k, ref_part.k), dtype=int)
    for zp in range(part.k):
        mp = shared & (lp == zp)
        for zr in range(ref_part.k):
            ov[zp, zr] = int(np.sum(mp & (lr == zr)))
    rows, cols = linear_sum_assignment(-ov)
    return {int(r): int(c) for r, c in zip(rows, cols)}


def build_tracks(parts, n_cell, ref_index=-1):
    """SPEC 11 tracks, orphans and absences."""
    ref = parts[ref_index]
    tracks = {z: Track(ref_zone=z) for z in range(ref.k)}
    orphans, absences = [], {}
    for fi, p in enumerate(parts):
        amap = align_to_reference(ref, p, n_cell)
        for zp in range(p.k):
            if zp in amap:
                tracks[amap[zp]].member[fi] = zp
                tracks[amap[zp]].cells[fi] = p.zone_cells(zp)
            else:
                orphans.append({"fold": fi, "zone": zp,
                                "cells": int(len(p.zone_cells(zp))),
                                "area": float(p.zone_weight(zp) / p.total_weight())})
        absences[fi] = [z for z in range(ref.k) if z not in
                        {amap[zp] for zp in amap}]
    return tracks, orphans, absences


def fold_orphan_area(parts, tracks, orphans):
    """SPEC 11's two first-class fold-level stability metrics."""
    oa = {fi: 0.0 for fi in range(len(parts))}
    for o in orphans:
        oa[o["fold"]] += o["area"]
    ar = {fi: 0.0 for fi in range(len(parts))}
    k_ref = len(tracks)
    for fi in range(len(parts)):
        missing = sum(1 for t in tracks.values() if fi not in t.member)
        ar[fi] = missing / max(k_ref, 1)
    return oa, ar


def track_agreement(track, n_cell):
    """Mean pairwise aligned-label agreement: |A and B| / |A or B| over fold pairs."""
    folds = sorted(track.member)
    if len(folds) < 2:
        return float("nan")
    vals = []
    for a, b in itertools.combinations(folds, 2):
        A, B = set(track.cells[a].tolist()), set(track.cells[b].tolist())
        u = len(A | B)
        vals.append(len(A & B) / u if u else np.nan)
    return float(np.nanmean(vals))


def track_centroid_variation(track, lats, lons):
    folds = sorted(track.member)
    if len(folds) < 2:
        return float("nan"), float("nan")
    la = [float(lats[track.cells[f]].mean()) for f in folds]
    lo = [float(lons[track.cells[f]].mean()) for f in folds]
    return float(np.std(la)), float(np.std(lo))


def track_boundary_variation(track):
    """Fraction of cells that change membership between fold pairs, for this track."""
    folds = sorted(track.member)
    if len(folds) < 2:
        return float("nan")
    vals = []
    for a, b in itertools.combinations(folds, 2):
        A, B = set(track.cells[a].tolist()), set(track.cells[b].tolist())
        u = len(A | B)
        vals.append(len(A ^ B) / u if u else np.nan)
    return float(np.nanmean(vals))


def _pairwise_match_rate(values):
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return float("nan")
    pairs = list(itertools.combinations(vals, 2))
    return float(np.mean([a == b for a, b in pairs]))


def track_recipe_agreement(track, per_zone_rows):
    """Window, predictor-identity, predictor-region and lead agreement for one track.

    per_zone_rows is the flat per-zone-window table: dicts with fold, zone, window,
    index, lead, discovered.
    """
    by_fold = {}
    for r in per_zone_rows:
        fi = r["fold"]
        if track.member.get(fi) == r["zone"] and r["discovered"]:
            by_fold.setdefault(fi, []).append(r)
    folds = sorted(set(by_fold) & set(track.member))
    winsets = {f: tuple(sorted(r["window"] for r in by_fold[f])) for f in folds}
    exact = _pairwise_match_rate(list(winsets.values()))
    jac = []
    for a, b in itertools.combinations(folds, 2):
        A, B = set(winsets[a]), set(winsets[b])
        jac.append(len(A & B) / len(A | B) if A | B else np.nan)
    # predictor / lead agreement is per window label
    idx_rates, grp_rates, lead_rates, lead_absdiff = [], [], [], []
    labels = set().union(*[set(winsets[f]) for f in folds]) if folds else set()
    for lab in labels:
        picks = {f: next((r for r in by_fold[f] if r["window"] == lab), None)
                 for f in folds}
        got = [p for p in picks.values() if p]
        if len(got) < 2:
            continue
        idx_rates.append(_pairwise_match_rate([p["index"] for p in got]))
        grp_rates.append(_pairwise_match_rate([PREDICTOR_GROUP[p["index"]] for p in got]))
        lead_rates.append(_pairwise_match_rate([p["lead"] for p in got]))
        lead_absdiff.append(float(np.mean([abs(a["lead"] - b["lead"])
                                           for a, b in itertools.combinations(got, 2)])))
    nan = float("nan")
    return {"window_exact_match": exact,
            "window_jaccard": float(np.nanmean(jac)) if jac else nan,
            "predictor_identity": float(np.nanmean(idx_rates)) if idx_rates else nan,
            "predictor_region": float(np.nanmean(grp_rates)) if grp_rates else nan,
            "lead_exact": float(np.nanmean(lead_rates)) if lead_rates else nan,
            "lead_abs_diff": float(np.nanmean(lead_absdiff)) if lead_absdiff else nan}


def track_skill(track, forecasts_by_fold):
    """Pooled held-out skill for a track: raw RPS summed over its zone-window-years."""
    nf = nc = 0.0
    n = 0
    for fi, z in track.member.items():
        for fc in forecasts_by_fold[fi]:
            if fc.zone == z and fc.discovered:
                nf += fc.rps_f.sum()
                nc += fc.rps_c.sum()
                n += len(fc.rps_f)
    if nc <= 0:
        return float("nan"), 0
    return float(1.0 - nf / nc), n


# ── H1 ────────────────────────────────────────────────────────────────────────
def h1_test(stability, skill, seed=1):
    """SPEC 11: one-sided Spearman rho > 0, exact enumeration when tractable.

    Returns a dict with rho, p, the null construction used, and the denominator.
    """
    s = np.asarray(stability, dtype=float)
    y = np.asarray(skill, dtype=float)
    ok = np.isfinite(s) & np.isfinite(y)
    s, y = s[ok], y[ok]
    n = len(s)
    if n < 3:
        return {"n": int(n), "rho": None, "p": None, "null": "insufficient",
                "denominator": 0, "verdict": "not testable"}
    rho = float(spearmanr(s, y).statistic)
    n_perm = math.factorial(n)
    if n_perm <= ENUM_CAP:
        cnt = 0
        for p in itertools.permutations(range(n)):
            if spearmanr(s[list(p)], y).statistic >= rho:
                cnt += 1
        pval = cnt / n_perm
        null, denom = "exact enumeration", n_perm
    else:
        rng = np.random.default_rng(seed)
        draws = 10_000
        cnt = sum(1 for _ in range(draws)
                  if spearmanr(rng.permutation(s), y).statistic >= rho)
        pval = (1 + cnt) / (draws + 1)
        null, denom = "10,000 Monte Carlo permutations", draws
    return {"n": int(n), "rho": round(rho, 4), "p": round(float(pval), 5),
            "null": null, "denominator": int(denom),
            "verdict": "supported" if pval <= 0.05 and rho > 0 else "not supported"}
