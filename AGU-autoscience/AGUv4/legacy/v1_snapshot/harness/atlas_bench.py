"""atlas_bench.py — the LOCKED evaluator for SPEC 10's complete zonal product.

Registered as `atlas-wf-v1` (walk-forward, primary) and `atlas-kf-v1` (k-fold, reported
alongside). Once a submission exists this file cannot change; a different contract needs
a new benchmark version.

WHAT IS FIXED HERE, and unreachable by any arm:
  - the fixtures, the domain, the 0.25 deg grid and the valid-cell rule
  - the fold split
  - the zone-discovery algorithm, the k rule and the season detector
  - the predictor and lead candidate space
  - the tercile boundaries (train-fitted, never test-fitted)
  - the climatology reference and the pooling rule
  - the score

WHAT AN ARM CHOOSES: whether zones are discovered at all (`pooled` is k=1), and whether
the predictor and lead are chosen per zone or once for all zones. `climatology` is the
harness gate and must score exactly 0.

The environment is asserted before anything is computed: both fixture hashes and both
library source-tree hashes must match outputs/env.json, or the run aborts rather than
silently re-defining a locked benchmark.

Usage:
    python harness/atlas_bench.py --protocol walkforward [--arm zones-specific]
                                  [--leak] [--weight equal|rain]
                                  [--family atlas/all-windows]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import traceback
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "harness"))

import atlas_score as A            # noqa: E402
import pipeline as P               # noqa: E402

ARMS = ("climatology", "pooled", "zones-shared", "zones-specific")


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def assert_env():
    """SPEC 2: content hashes, not git shas. A mismatch aborts."""
    env_path = ROOT / "outputs" / "env.json"
    if not env_path.exists():
        raise SystemExit("outputs/env.json missing — run src/record_env.py")
    env = json.loads(env_path.read_text())["asserted"]
    for name, rel in (("chirps_v3", "data/chirps_v3_ea_monthly.nc"),
                      ("ersst_v5", "data/ersst_v5_monthly.nc")):
        got = _sha(ROOT / rel)
        want = env["fixtures"][name]["sha256"]
        if got != want:
            raise SystemExit(f"FIXTURE DRIFT: {rel} is {got[:16]}, env.json says {want[:16]}")
    sys.path.insert(0, str(ROOT / "src"))
    from record_env import library                                   # noqa: E402
    for lib in ("rosetta", "deepscale"):
        got = library(lib)["tree_sha256"]
        want = env["libraries"][lib]["tree_sha256"]
        if got != want:
            raise SystemExit(f"LIBRARY DRIFT: {lib} tree is {got[:16]}, "
                             f"env.json says {want[:16]}")
    return env


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", default="walkforward", choices=("walkforward", "kfold"))
    ap.add_argument("--folds", type=int, default=6)
    ap.add_argument("--arm", default="zones-specific", choices=ARMS)
    ap.add_argument("--leak", action="store_true",
                    help="SPEC 9.2: standardise WPG/WVG on the full record")
    ap.add_argument("--weight", default="equal", choices=("equal", "rain"))
    ap.add_argument("--family", default="atlas/all-windows", choices=P.FAMILIES)
    ap.add_argument("--per-zone", default=None, help="write the per-zone-window table here")
    a = ap.parse_args()

    try:
        env = assert_env()
        ff, folds, parts = P.run_atlas(protocol=a.protocol, n_folds=a.folds,
                                       arm=("zones-specific" if a.arm == "pooled"
                                            else a.arm),
                                       leak=a.leak,
                                       force_k=1 if a.arm == "pooled" else None,
                                       weight_rule=a.weight, collect_parts=True)
        fam = P.score_families(ff, folds)
        rpss = fam[a.family]["rpss"]

        per_zone = []
        for fi, fold in enumerate(ff):
            for fc in fold:
                r = (1 - fc.rps_f.sum() / fc.rps_c.sum()) if fc.rps_c.sum() > 0 else None
                per_zone.append(dict(
                    fold=fi, zone=int(fc.zone), window=fc.window,
                    months=list(fc.months), discovered=bool(fc.discovered),
                    weight=round(float(fc.weight), 6),
                    zone_share=round(float(fc.zone_share), 6),
                    index=fc.index, lead=int(fc.lead), n_train=int(fc.n_train),
                    n_test=int(len(fc.rps_f)),
                    test_years=[int(y) for y in fc.test_years],
                    rpss=None if r is None else round(float(r), 6)))
        if a.per_zone:
            Path(a.per_zone).parent.mkdir(parents=True, exist_ok=True)
            Path(a.per_zone).write_text(json.dumps(per_zone, indent=2) + "\n")

        ks = [int(p.k) for p in parts]
        wsum = [round(float(sum(fc.weight for fc in fold if fc.discovered)), 8)
                for fold in ff]
        print(json.dumps({
            "rpss_atlas": round(float(rpss), 6),
            "n_scored_years": int(fam[a.family]["n_scored"]),
            "coverage": round(float(fam[a.family]["coverage"]), 6),
            "rpss_mam_all": round(float(fam["MAM/all"]["rpss"]), 6),
            "rpss_mam_lanina": round(float(fam["MAM/lanina"]["rpss"]), 6),
            "rpss_mam_neg_wvg": round(float(fam["MAM/neg_wvg"]["rpss"]), 6),
            "coverage_mam_lanina": round(float(fam["MAM/lanina"]["coverage"]), 6),
            "coverage_mam_neg_wvg": round(float(fam["MAM/neg_wvg"]["coverage"]), 6),
            "n_zone_windows": len(per_zone),
            "k_per_fold": ks,
            "fold_weight_sums": wsum,
            "protocol": a.protocol, "arm": a.arm, "family": a.family,
            "leak": bool(a.leak), "weight_rule": a.weight,
            "chirps_sha256": env["fixtures"]["chirps_v3"]["sha256"][:16],
            "ersst_sha256": env["fixtures"]["ersst_v5"]["sha256"][:16],
            "status": "ok",
        }))
    except SystemExit:
        raise
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"status": "crashed", "error": f"{type(e).__name__}: {e}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
