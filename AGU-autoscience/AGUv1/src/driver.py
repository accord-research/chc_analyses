"""driver.py — enumerate the reduced tensor and score every cell (AGUv1).

`argmax over the tensor of skill(config)`: builds the discovered targets, enumerates the valid
configs, scores each on all four metrics under LOYO, and writes one tidy row per cell. NMME-MOS
cells fetch through the IRIDL fallback while CCSR is down. Results feed `select.py` (metric-vs-
accuracy selection) and `lead_cof.py` (skill/accuracy vs lead → "when can a COF be held").

Run: python src/driver.py            (all valid cells, Kenya OND+MAM)
     MAXCELLS=6 python src/driver.py  (quick subset)
"""
from __future__ import annotations
import os, sys, csv, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1].parent / "common"))
import iridl_patch
import targets as T
import methods
from searchspace import enumerate_configs, tensor_shape, METRICS

OUT = Path(__file__).resolve().parents[1] / "outputs" / "tables"
OUT.mkdir(parents=True, exist_ok=True)
CFG_COLS = ["target", "predictor_source", "method", "lead", "transform",
            "predictor_domain", "eof_modes", "downscale"]


def main():
    iridl_patch.apply()
    # On a re-run where the NMME hindcasts are already cached, CACHE_MODE=read_only reads the disk
    # cache instead of re-downloading (the patch's default "overwrite" re-fetches every time).
    mode = os.environ.get("CACHE_MODE")
    if mode:
        from nuthatch.nuthatch import set_global_cache_variables
        set_global_cache_variables(cache_mode=mode)
        print(f"cache_mode override: {mode}")
    tgts = [t.name for t in T.discover_targets()]
    shape = tensor_shape(tgts)
    print(f"tensor: {shape['axes']}  → {shape['valid_cells']} valid cells "
          f"× {shape['metrics_per_cell']} metrics")
    configs = enumerate_configs(tgts)
    maxc = int(os.environ.get("MAXCELLS", "0"))
    if maxc:
        configs = configs[:maxc]

    rows = []
    t0 = time.time()
    for i, c in enumerate(configs, 1):
        t = time.time()
        try:
            s = methods.score_config(c)
        except Exception as e:
            print(f"  [{i:02d}/{len(configs)}] {c.key()[:48]:48s} ERR {type(e).__name__}: {str(e)[:40]}", flush=True)
            s = {m: float("nan") for m in METRICS}
        row = {k: getattr(c, k) for k in CFG_COLS}
        row.update({m: round(s.get(m, float("nan")), 4) for m in METRICS})
        rows.append(row)
        print(f"  [{i:02d}/{len(configs)}] {c.target} {c.predictor_source:14s} {c.method:10s} L{c.lead} "
              f"GROC={s.get('generalized_roc', float('nan')):+.3f} hit={s.get('hit_rate', float('nan')):.3f} "
              f"({time.time()-t:.1f}s)", flush=True)

    out = OUT / "search_results.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CFG_COLS + list(METRICS))
        w.writeheader(); w.writerows(rows)
    print(f"\nwrote {len(rows)} rows → {out}  ({time.time()-t0:.0f}s total)")


if __name__ == "__main__":
    main()
