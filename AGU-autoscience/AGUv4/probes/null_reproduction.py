"""null_reproduction.py — did the runner fixes change the null?

The 600-row null produced before the five runner fixes is archived at
legacy/prefix_null/atlas_null_v2_prefix_runner.jsonl. None of those fixes touches `_job`
or `replicate_all_arms`, so the re-run under the corrected runner should reproduce it
exactly. This checks that claim instead of asserting it.

A bit-for-bit match is the strongest available evidence that the fixes were inert with
respect to the science. A mismatch would mean one of them was not, and would need
explaining before any number is read.

Writes outputs/null_reproduction.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
NEW = OUT / "atlas_null_v2.jsonl"
OLD = ROOT / "legacy" / "prefix_null" / "atlas_null_v2_prefix_runner.jsonl"


def load(path):
    rows = {}
    for ln in path.read_text().splitlines():
        if not ln.strip():
            continue
        d = json.loads(ln)
        if "error" in d:
            continue
        rows[(d["replicate"], d["arm"], d["protocol"])] = d
    return rows


def main():
    if not OLD.exists() or not NEW.exists():
        print(f"missing input: old={OLD.exists()} new={NEW.exists()}")
        return 1
    old, new = load(OLD), load(NEW)
    only_old = sorted(set(old) - set(new))
    only_new = sorted(set(new) - set(old))
    shared = sorted(set(old) & set(new))

    worst, worst_at, n_diff = 0.0, None, 0
    for k in shared:
        a, b = old[k]["families"], new[k]["families"]
        for fam in a:
            va, vb = a[fam].get("rpss"), b.get(fam, {}).get("rpss")
            if va is None and vb is None:
                continue
            if va is None or vb is None:
                n_diff += 1
                continue
            d = abs(va - vb)
            if d > 0:
                n_diff += 1
            if d > worst:
                worst, worst_at = d, f"{k} {fam}"

    identical = not only_old and not only_new and n_diff == 0
    out = {"old_rows": len(old), "new_rows": len(new), "shared": len(shared),
           "only_in_old": len(only_old), "only_in_new": len(only_new),
           "family_values_differing": n_diff,
           "max_abs_diff": worst, "max_at": worst_at,
           "bit_identical": bool(identical),
           "conclusion": ("the five runner fixes changed no null value"
                          if identical else
                          "THE NULL CHANGED — a runner fix was not inert; explain before "
                          "reading any number"),
           "status": "ok" if identical else "failed"}
    OUT.mkdir(exist_ok=True)
    (OUT / "null_reproduction.json").write_text(json.dumps(out, indent=2) + "\n")
    print(f"old {len(old)} rows, new {len(new)} rows, shared {len(shared)}")
    print(f"differing family values: {n_diff}, max |diff| {worst:.3e}"
          + (f" at {worst_at}" if worst_at else ""))
    print(out["conclusion"])
    print(json.dumps({"bit_identical": out["bit_identical"],
                      "max_abs_diff": out["max_abs_diff"], "status": out["status"]}))
    return 0 if identical else 1


if __name__ == "__main__":
    sys.exit(main())
