"""run_atlas.py — the restartable production runner (SPEC 15).

Two jobs.

  --real   the real atlas: every arm, both protocols, both weighting rules, plus the
           leaky and clean out-of-sample arms of SPEC 9.2/9.3. Writes the per-zone-window
           table with every zone present and no minimum-year threshold.

  --null   the 6 x 200 paired permutation sweep. Each replicate permutes the rainfall
           field, re-runs discovery in all six folds, and scores all four families of
           SPEC 14 -- so 1,200 complete discovery runs produce 4,800 family scores.
           Every completed replicate is appended to outputs/atlas_null.jsonl keyed by
           (arm, protocol, replicate); a restart reads the file, skips finished keys and
           continues, so killing the runner loses at most one replicate per worker.

SPEC 16's verification runs inside the sweep, not only at development time: three
randomly chosen (fold, replicate) pairs are re-scored end to end by atlas_score_slow and
must agree to 1e-8, or the sweep aborts before writing anything.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import warnings
from multiprocessing import Pool
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "harness"))

import bench                       # noqa: E402
import fields as F                 # noqa: E402
import discovery as D              # noqa: E402
import indices as IX               # noqa: E402
import atlas_score as A            # noqa: E402
import atlas_score_slow as S       # noqa: E402
import pipeline as P               # noqa: E402

OUT = ROOT / "outputs"
NULL_JSONL = OUT / "atlas_null.jsonl"
N_REPS = 200
ARMS = ("climatology", "pooled", "zones-shared", "zones-specific")


# ── SPEC 16 verification, run before the sweep ────────────────────────────────
def verify(n_pairs=3, tol=1e-8, seed=11):
    fld, sst = P.get_state()
    folds = bench.make_folds(fld.years, "walkforward", 6)
    rng = np.random.default_rng(seed)
    worst = 0.0
    print(f"SPEC 16 verification: {n_pairs} (fold, replicate) pairs re-scored by the "
          f"slow reference", flush=True)
    for _ in range(n_pairs):
        fi = int(rng.integers(len(folds)))
        rep = int(rng.integers(N_REPS))
        tr_i, te_i = folds[fi]
        tr_y, te_y = fld.years[tr_i], fld.years[te_i]
        perm = np.random.default_rng(4242 + rep).permutation(len(fld.years))
        mm = F.permute_field(fld, perm)
        part = D.discover(mm, fld.month_of_col, fld.year_of_col, tr_y, fld.lats, fld.lons)
        kw = dict(forced_windows=P.FORCED_MAM)
        fast = A.score_fold(part, mm, fld.month_of_col, fld.year_of_col, fld.years,
                            tr_y, te_y, sst, **kw)
        slow = S.score_fold_slow(part, mm, fld.month_of_col, fld.year_of_col, fld.years,
                                 tr_y, te_y, sst, **kw)
        rf = A.pool([fast], select=lambda f: f.discovered)[0]
        rs = A.pool([slow], select=lambda f: f.discovered)[0]
        d = abs(rf - rs)
        worst = max(worst, d)
        print(f"  fold {fi} replicate {rep}: fast {rf:+.10f}  slow {rs:+.10f}  "
              f"|diff| {d:.2e}", flush=True)
    if worst > tol:
        raise SystemExit(f"SPEC 16 FAILURE: max |diff| {worst:.2e} exceeds {tol} — "
                         "sweep aborted")
    print(f"  agreement holds: max |diff| = {worst:.2e} <= {tol}\n", flush=True)
    return worst


# ── the real atlas ────────────────────────────────────────────────────────────
def real():
    rows = []
    per_zone_all = {}
    for protocol in ("walkforward", "kfold"):
        for arm in ARMS:
            for leak in ((False, True) if arm == "zones-specific" else (False,)):
                for wr in (("equal", "rain") if (arm == "zones-specific" and not leak)
                           else ("equal",)):
                    t0 = time.time()
                    ff, folds, parts = P.run_atlas(
                        protocol=protocol,
                        arm="zones-specific" if arm == "pooled" else arm,
                        leak=leak, force_k=1 if arm == "pooled" else None,
                        weight_rule=wr, collect_parts=True)
                    fam = P.score_families(ff, folds)
                    tag = f"{arm}{'/leaky' if leak else ''}{'' if wr == 'equal' else '/rain'}"
                    rows.append(dict(protocol=protocol, arm=arm, leak=leak,
                                     weight_rule=wr, tag=tag,
                                     k_per_fold=[int(p.k) for p in parts],
                                     families={k: {kk: (None if not np.isfinite(vv) else
                                                        round(float(vv), 6))
                                                   for kk, vv in v.items()}
                                               for k, v in fam.items()},
                                     seconds=round(time.time() - t0, 1)))
                    print(f"  {protocol:12s} {tag:28s} "
                          f"atlas {fam['atlas/all-windows']['rpss']:+.4f}  "
                          f"({time.time() - t0:.0f}s)", flush=True)
                    if wr == "equal" and not leak:
                        pz = []
                        for fi, fold in enumerate(ff):
                            for fc in fold:
                                r = ((1 - fc.rps_f.sum() / fc.rps_c.sum())
                                     if fc.rps_c.sum() > 0 else None)
                                pz.append(dict(
                                    fold=fi, zone=int(fc.zone), window=fc.window,
                                    months=list(fc.months),
                                    discovered=bool(fc.discovered),
                                    weight=round(float(fc.weight), 6),
                                    zone_share=round(float(fc.zone_share), 6),
                                    index=fc.index, lead=int(fc.lead),
                                    n_train=int(fc.n_train), n_test=int(len(fc.rps_f)),
                                    test_years=[int(y) for y in fc.test_years],
                                    rpss=None if r is None else round(float(r), 6)))
                        per_zone_all[f"{protocol}/{arm}"] = pz
    OUT.mkdir(exist_ok=True)
    (OUT / "atlas_real.json").write_text(json.dumps(rows, indent=2) + "\n")
    (OUT / "atlas_per_zone.json").write_text(json.dumps(per_zone_all, indent=2) + "\n")
    print(f"\nwrote {OUT / 'atlas_real.json'} and {OUT / 'atlas_per_zone.json'}")
    return rows


# ── the null sweep ────────────────────────────────────────────────────────────
def _job(spec):
    """One replicate, ALL THREE ARMS, from ONE discovery pass per fold.

    SPEC 10.6 states the three comparison arms ride on the same 1,200 discovery runs.
    That is only true if the code actually shares them, so it does: `zones-specific` and
    `zones-shared` consume the identical partition and windows and differ only in
    selection, and `pooled` needs a k=1 partition that costs no k-means and no bootstrap
    ARI curve. Running them as three independent sweeps would have tripled the budget for
    nothing.

    This lives here rather than in pipeline.py because pipeline.py is locked by all six
    benchmarks; the locked primitives are called, not modified.
    """
    rep, protocol = spec
    try:
        fld, sst = P.get_state()
        perm = np.random.default_rng(4242 + rep).permutation(len(fld.years))
        mm = F.permute_field(fld, perm)
        acc = {a: [] for a in ("zones-specific", "zones-shared", "pooled")}
        folds = []
        ks = []
        for tr_i, te_i in bench.make_folds(fld.years, protocol, 6):
            tr_y, te_y = fld.years[tr_i], fld.years[te_i]
            part = D.discover(mm, fld.month_of_col, fld.year_of_col, tr_y,
                              fld.lats, fld.lons)
            ks.append(int(part.k))
            for arm in ("zones-specific", "zones-shared"):
                acc[arm].append(A.score_fold(
                    part, mm, fld.month_of_col, fld.year_of_col, fld.years,
                    tr_y, te_y, sst, arm=arm, forced_windows=P.FORCED_MAM))
            p1 = D.discover(mm, fld.month_of_col, fld.year_of_col, tr_y,
                            fld.lats, fld.lons, force_k=1)
            acc["pooled"].append(A.score_fold(
                p1, mm, fld.month_of_col, fld.year_of_col, fld.years,
                tr_y, te_y, sst, arm="zones-specific", forced_windows=P.FORCED_MAM))
            folds.append((tr_y, te_y))
        return [{"replicate": rep, "arm": arm, "protocol": protocol,
                 "families": P.score_families(acc[arm], folds),
                 "zones_per_fold": ks if arm != "pooled" else [1] * len(folds)}
                for arm in acc]
    except Exception as e:
        return [{"replicate": rep, "arm": a, "protocol": protocol,
                 "error": f"{type(e).__name__}: {e}"}
                for a in ("zones-specific", "zones-shared", "pooled")]


def done_keys():
    if not NULL_JSONL.exists():
        return set()
    keys = set()
    for ln in NULL_JSONL.read_text().splitlines():
        if not ln.strip():
            continue
        try:
            d = json.loads(ln)
        except json.JSONDecodeError:
            continue
        if "error" not in d:
            keys.add((d["replicate"], d["arm"], d["protocol"]))
    return keys


def _clean(o):
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(float(o)) else round(float(o), 8)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, list):
        return [_clean(v) for v in o]
    return o


def null(n_reps=N_REPS, protocol="walkforward", workers=None):
    OUT.mkdir(exist_ok=True)
    workers = workers or max(1, min(10, (os.cpu_count() or 4) - 2))
    have = done_keys()
    todo = [(r, protocol) for r in range(n_reps)
            if (r, "zones-specific", protocol) not in have]
    print(f"null sweep: {len(have)} replicate-arms already done, {len(todo)} replicates "
          f"to run x 3 arms from one discovery pass each, {workers} workers", flush=True)
    if not todo:
        return
    t0 = time.time()
    n_done = 0
    with Pool(workers) as pool, open(NULL_JSONL, "a") as fh:
        for rows in pool.imap_unordered(_job, todo, chunksize=1):
            for res in rows:
                fh.write(json.dumps(_clean(res)) + "\n")
            fh.flush()
            n_done += 1
            if n_done % 10 == 0:
                el = time.time() - t0
                print(f"  {n_done}/{len(todo)} replicates  {el / 60:.1f} min elapsed, "
                      f"~{el / n_done * (len(todo) - n_done) / 60:.1f} min left",
                      flush=True)
    print(f"null sweep done in {(time.time() - t0) / 60:.1f} min -> {NULL_JSONL}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", action="store_true")
    ap.add_argument("--null", action="store_true")
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--reps", type=int, default=N_REPS)
    ap.add_argument("--workers", type=int, default=None)
    a = ap.parse_args()

    verify()
    if a.verify_only:
        return
    if a.real:
        print("REAL ATLAS\n")
        real()
    if a.null:
        print("\nNULL SWEEP\n")
        null(n_reps=a.reps, workers=a.workers)


if __name__ == "__main__":
    main()
