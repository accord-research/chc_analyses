"""smoke_discovery.py — archived one-shot. Does one discovery run work, and does the budget hold?

Not on regenerate.sh. Run: python legacy/probes/smoke_discovery.py

SPEC 15 budgets 1,200 complete discovery runs inside 4 CPU-hours. That is 12 seconds per
run at 1 core, or 96 seconds per run across 8 workers. This measures the real number
before anything is registered, because if a discovery run costs 60 s single-core the
sweep does not fit and the design has to change now rather than four hours in.
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "harness"))

import bench                                  # noqa: E402
import fields as F                            # noqa: E402
import discovery as D                         # noqa: E402
import indices as IX                          # noqa: E402

t0 = time.time()
fld = F.load_chirps()
print(f"field: {fld.monthly.shape} cells x cols, {len(fld.years)} years "
      f"({time.time() - t0:.1f}s)", flush=True)

folds = bench.make_folds(fld.years, "walkforward", 6)
tr_i, te_i = folds[-1]
train_years, test_years = fld.years[tr_i], fld.years[te_i]
print(f"fold 5: train {train_years.min()}-{train_years.max()} (n={len(train_years)}), "
      f"test {test_years.min()}-{test_years.max()}", flush=True)

t0 = time.time()
part = D.discover(fld.monthly, fld.month_of_col, fld.year_of_col, train_years,
                  fld.lats, fld.lons)
dt = time.time() - t0
print(f"\ndiscovery run: {dt:.2f}s   ->  1200 runs = {1200 * dt / 3600:.2f} core-hours",
      flush=True)
print(f"selected k = {part.k}  (tau = {D.TAU})")
print(f"valid cells = {len(part.cell_index)}")
print("\n  k   ARI     sd     silhouette")
for k in sorted(part.ari_curve):
    print(f"  {k}   {part.ari_curve[k]:.3f}  {part.ari_sd[k]:.3f}  {part.silhouette[k]:.3f}")

print("\n  zone  cells  cen_lat  cen_lon  annual_mm  regime    windows")
for z in range(part.k):
    cells = part.zone_cells(z)
    cyc = part.cycles[z]
    wins = part.windows[z]
    print(f"  {z:4d}  {len(cells):5d}  {fld.lats[cells].mean():7.2f}  "
          f"{fld.lons[cells].mean():7.2f}  {cyc.sum():9.0f}  "
          f"{'bimodal' if len(wins) > 1 else 'unimodal':8s}  "
          f"{' + '.join(lab for lab, _ in wins)}")

# timing the scoring side too
t0 = time.time()
sst = IX.load_boxes()
print(f"\nSST boxes loaded ({time.time() - t0:.1f}s)", flush=True)

import atlas_score as A                       # noqa: E402
t0 = time.time()
fcs = A.score_fold(part, fld.monthly, fld.month_of_col, fld.year_of_col, fld.years,
                   train_years, test_years, sst,
                   forced_windows=[("MAM", [3, 4, 5])])
dt_s = time.time() - t0
print(f"score_fold: {dt_s:.2f}s for {len(fcs)} zone-windows", flush=True)
print(f"\n  zone window disc  weight  recipe            n_test  RPSS")
for fc in sorted(fcs, key=lambda f: (f.zone, f.window)):
    r = 1 - fc.rps_f.sum() / fc.rps_c.sum() if fc.rps_c.sum() > 0 else float("nan")
    print(f"  {fc.zone:4d} {fc.window:6s} {'y' if fc.discovered else 'forced':6s} "
          f"{fc.weight:6.3f}  {fc.index:6s} lead-{fc.lead}   {len(fc.rps_f):5d}  {r:+.4f}")

disc = [fc for fc in fcs if fc.discovered]
num = sum(fc.weight * fc.rps_f.sum() for fc in disc)
den = sum(fc.weight * fc.rps_c.sum() for fc in disc)
print(f"\n  weight of discovered windows = {sum(fc.weight for fc in disc):.4f} (must be 1)")
print(f"  fold-5 atlas RPSS = {1 - num / den:+.4f}")
print(f"\nestimated full null: 1200 x ({dt:.1f}s discovery + ~{dt_s:.1f}s scoring) "
      f"= {1200 * (dt + dt_s) / 3600:.2f} core-hours")
