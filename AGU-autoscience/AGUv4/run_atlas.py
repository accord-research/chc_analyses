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
import pipeline_v2 as P2           # noqa: E402
import nullperm as NP              # noqa: E402

OUT = ROOT / "outputs"
NULL_JSONL = OUT / "atlas_null_v2.jsonl"
SENS_JSONL = OUT / "sensitivity_field_perm.jsonl"
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
                    ff, folds, parts = P2.run_atlas_v2(
                        protocol=protocol,
                        arm="zones-specific" if arm == "pooled" else arm,
                        leak=leak, force_k=1 if arm == "pooled" else None,
                        weight_rule=wr)
                    fam = P2.score_families(ff, folds)
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


# ── fix 5: pin the code that produces the null, before it runs ───────────────
MANIFEST = OUT / "null_manifest.json"
MANIFEST_FILES = ("run_atlas.py", "harness/nullperm.py", "harness/pipeline_v2.py",
                  "harness/atlas_score.py", "harness/discovery.py", "harness/indices.py",
                  "harness/fields.py", "bench.py")


def _sha(rel):
    import hashlib
    h = hashlib.sha256()
    with open(ROOT / rel, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_null_manifest(n_reps, protocol):
    """Record the exact code and parameters the null is about to be produced by.

    Written BEFORE the sweep so the artifact cannot be attributed to a later edit, and
    re-asserted by check_null afterwards. run_atlas.py hashes itself here, which is the
    point: the runner is part of the null's definition.
    """
    OUT.mkdir(exist_ok=True)
    m = {"n_reps": int(n_reps), "protocol": protocol, "seed": NP.SEED,
         "arms": list(ARMS_PER_REPLICATE),
         "expected_rows": int(n_reps) * len(ARMS_PER_REPLICATE),
         "null_kind": "complete-season target permutation (SPEC Amendment 1 section 3)",
         "sha256": {rel: _sha(rel) for rel in MANIFEST_FILES}}
    MANIFEST.write_text(json.dumps(m, indent=2, sort_keys=True) + "\n")
    print(f"null manifest pinned: run_atlas.py {m['sha256']['run_atlas.py'][:16]}, "
          f"nullperm.py {m['sha256']['harness/nullperm.py'][:16]}", flush=True)
    return m


def check_null(n_reps, protocol):
    """Fix 2: the sweep must have produced exactly n_reps x 3 valid unique rows.

    Anything else -- a duplicate, an error row, a missing arm, a short sweep -- aborts
    with a non-zero exit rather than letting a partial null reach a decision.
    """
    rows, errs, keys = 0, 0, set()
    by_rep = {}
    for ln in NULL_JSONL.read_text().splitlines() if NULL_JSONL.exists() else []:
        if not ln.strip():
            continue
        d = json.loads(ln)
        rows += 1
        if "error" in d:
            errs += 1
            continue
        if d["protocol"] != protocol:
            continue
        keys.add((d["replicate"], d["arm"], d["protocol"]))
        by_rep.setdefault(d["replicate"], set()).add(d["arm"])
    expect = int(n_reps) * len(ARMS_PER_REPLICATE)
    full = {r for r, a in by_rep.items() if a == set(ARMS_PER_REPLICATE)}
    dups = rows - errs - len(keys)
    problems = []
    if errs:
        problems.append(f"{errs} error row(s)")
    if dups > 0:
        problems.append(f"{dups} duplicate row(s)")
    if len(keys) != expect:
        problems.append(f"{len(keys)} valid unique rows, expected {expect}")
    if len(full) != int(n_reps):
        problems.append(f"{len(full)} replicates with all 3 arms, expected {n_reps}")
    if MANIFEST.exists():
        m = json.loads(MANIFEST.read_text())
        drift = [rel for rel, want in m["sha256"].items() if _sha(rel) != want]
        if drift:
            problems.append(f"code changed since the manifest was pinned: {drift}")
    else:
        problems.append("no null manifest")
    print(f"\nNULL COMPLETENESS GUARD: {len(keys)} valid unique rows, "
          f"{len(full)}/{n_reps} replicates with all 3 arms, {errs} errors, "
          f"{dups} duplicates", flush=True)
    if problems:
        raise SystemExit("NULL INCOMPLETE — " + "; ".join(problems))
    print("  guard passed: exactly 200 x 3 = 600 valid unique rows, no errors\n",
          flush=True)
    return True


# ── the null sweep ────────────────────────────────────────────────────────────
_PERMS = None


def _job(spec):
    """One replicate, all three arms, under Amendment 1's complete-season target
    permutation. Discovery is unpermuted and shared, so a replicate is selection +
    fitting + scoring only."""
    global _PERMS
    rep, protocol = spec
    try:
        fld, _ = P.get_state()
        if _PERMS is None:
            _PERMS = NP.permutations(len(fld.years))
        return P2.replicate_all_arms(rep, _PERMS, protocol=protocol)
    except Exception as e:
        return [{"replicate": rep, "arm": a, "protocol": protocol,
                 "error": f"{type(e).__name__}: {e}"}
                for a in ("zones-specific", "zones-shared", "pooled")]


def _job_sens(spec):
    """Amendment 1 3.4 sensitivity analysis: the v1 calendar-year FIELD permutation.
    Labelled, reported separately, adjudicates nothing."""
    rep, protocol = spec
    try:
        return [P2.sensitivity_field_perm(rep, protocol=protocol)]
    except Exception as e:
        return [{"replicate": rep, "arm": "zones-specific", "protocol": protocol,
                 "error": f"{type(e).__name__}: {e}"}]


ARMS_PER_REPLICATE = ("zones-specific", "zones-shared", "pooled")


def done_keys():
    """Restart support: (replicate, arm, protocol) triples already written OK."""
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


def complete_replicates(protocol):
    """Replicates that have ALL THREE arms.

    Keying restart on zones-specific alone was wrong: a worker killed between writing
    its first arm and its last would leave a replicate that looks finished and is not,
    and the sweep would silently end with fewer than 600 rows.
    """
    have = done_keys()
    return {r for (r, a, p) in have if p == protocol
            and all((r, arm, protocol) in have for arm in ARMS_PER_REPLICATE)}


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
    """Amendment 1's null runs in ONE process by design.

    Discovery is unpermuted and shared across every replicate, so the sweep is selection +
    fitting + scoring only -- about 0.2 s per replicate against a ~4 min one-off discovery
    warm-up. Fanning out to workers would make each worker repeat that warm-up and make
    the whole thing slower. `--workers N` forces the pool if ever needed.
    """
    OUT.mkdir(exist_ok=True)
    write_null_manifest(n_reps, protocol)
    done = complete_replicates(protocol)
    todo = [(r, protocol) for r in range(n_reps) if r not in done]
    print(f"null sweep: {len(done)} replicates complete (all 3 arms), {len(todo)} to run, "
          f"{workers or 1} worker(s)", flush=True)
    if not todo:
        return check_null(n_reps, protocol)
    t0 = time.time()
    n_done = 0
    if workers and workers > 1:
        it = Pool(workers).imap_unordered(_job, todo, chunksize=1)
    else:
        it = map(_job, todo)
    with open(NULL_JSONL, "a") as fh:
        for rows in it:
            for res in rows:
                fh.write(json.dumps(_clean(res)) + "\n")
            fh.flush()
            n_done += 1
            if n_done % 25 == 0:
                el = time.time() - t0
                print(f"  {n_done}/{len(todo)} replicates  {el / 60:.1f} min elapsed",
                      flush=True)
    print(f"null sweep done in {(time.time() - t0) / 60:.1f} min -> {NULL_JSONL}")
    return check_null(n_reps, protocol)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", action="store_true")
    ap.add_argument("--null", action="store_true")
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--sensitivity", type=int, default=0,
                    help="replicates of the v1 field permutation, "
                         "Amendment 1 3.4 sensitivity analysis only")
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
        print("\nPRIMARY NULL SWEEP — complete-season target permutation "
              "(SPEC Amendment 1 section 3)\n")
        null(n_reps=a.reps, workers=a.workers)
    if a.sensitivity:
        print("\nSENSITIVITY — v1 calendar-year FIELD permutation. This CANNOT preserve")
        print("complete outcomes for wrapping windows and adjudicates nothing.\n")
        sensitivity(n_reps=a.sensitivity, workers=a.workers)




def sensitivity(n_reps=20, protocol="walkforward", workers=None):
    """Amendment 1 3.4. Reported beside the primary null, never in place of it."""
    OUT.mkdir(exist_ok=True)
    have = set()
    if SENS_JSONL.exists():
        for ln in SENS_JSONL.read_text().splitlines():
            if ln.strip():
                d = json.loads(ln)
                if "error" not in d:
                    have.add(d["replicate"])
    todo = [(r, protocol) for r in range(n_reps) if r not in have]
    print(f"sensitivity sweep: {len(todo)} replicates, {workers} workers", flush=True)
    if not todo:
        return
    t0 = time.time()
    workers = workers or max(1, min(8, (os.cpu_count() or 4) - 2))
    with Pool(workers) as pool, open(SENS_JSONL, "a") as fh:
        for rows in pool.imap_unordered(_job_sens, todo, chunksize=1):
            for res in rows:
                fh.write(json.dumps(_clean(res)) + "\n")
            fh.flush()
    print(f"sensitivity done in {(time.time() - t0) / 60:.1f} min -> {SENS_JSONL}")

if __name__ == "__main__":
    main()
