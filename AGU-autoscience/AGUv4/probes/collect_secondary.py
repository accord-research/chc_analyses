"""collect_secondary.py — gather the secondary-benchmark submissions into outputs/secondary.json."""
import json, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
runs = json.loads(subprocess.check_output(["rx", "run", "list", "--kind", "submission", "--json"]))
rows = []
for r in runs:
    b = r.get("benchmark_name") or ""
    if not (b.startswith("fixedmean-") or b.startswith("grid-")) or not b.endswith("-v2"):
        continue
    m = r.get("metrics") or {}
    if "rpss" not in m:
        continue
    kind, window, _ = b.split("-")
    rows.append({"benchmark": b, "kind": kind, "window": window.upper(),
                 "arm": (r.get("params") or {}).get("arm", "?"),
                 "rpss": round(float(m["rpss"]), 6),
                 "n_scored": int(m.get("n_scored", 0)), "run": r.get("id") or r.get("run_id")})
rows.sort(key=lambda x: (x["kind"], x["window"], x["arm"]))
(ROOT / "outputs" / "secondary.json").write_text(json.dumps({"rows": rows}, indent=2) + "\n")
print(f"collected {len(rows)} secondary submissions")
for x in rows:
    print(f"  {x['kind']:10s} {x['window']:4s} {x['arm']:16s} rpss={x['rpss']:+.4f}")
print(json.dumps({"n": len(rows), "status": "ok"}))
