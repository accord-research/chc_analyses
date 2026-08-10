"""secondary_bench.py — the LOCKED evaluator for SPEC 13's two secondary benchmarks.

Registered as `fixedmean-mam-v1`, `fixedmean-ond-v1`, `grid-mam-v1`, `grid-ond-v1`.

These answer different questions from the primary atlas benchmark and never replace it.
`fixedmean` holds the predictand fixed and lets zones be modelling partitions, which
makes it the CONTROLLED test of zonation that SPEC 10 deliberately is not. `grid` scores
probabilities on the common 0.25 deg cell grid against each cell's own train-fitted
terciles.

Usage:
    python harness/secondary_bench.py --kind fixedmean --window OND [--arm zones]
    python harness/secondary_bench.py --kind grid      --window MAM [--arm zones-specific]
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "harness"))

import secondary as SEC            # noqa: E402
from atlas_bench import assert_env  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", required=True, choices=("fixedmean", "grid"))
    ap.add_argument("--window", required=True, choices=("MAM", "OND"))
    ap.add_argument("--arm", default=None)
    ap.add_argument("--protocol", default="walkforward",
                    choices=("walkforward", "kfold"))
    ap.add_argument("--folds", type=int, default=6)
    a = ap.parse_args()

    try:
        env = assert_env()
        if a.kind == "fixedmean":
            arm = a.arm or "zones"
            r, n = SEC.run_fixedmean(a.window, arm=arm, protocol=a.protocol,
                                     n_folds=a.folds)
        else:
            arm = a.arm or "zones-specific"
            r, n = SEC.run_grid(a.window, arm=arm, protocol=a.protocol, n_folds=a.folds)
        print(json.dumps({
            "rpss": round(float(r), 6),
            "n_scored": int(n),
            "kind": a.kind, "window": a.window, "arm": arm, "protocol": a.protocol,
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
