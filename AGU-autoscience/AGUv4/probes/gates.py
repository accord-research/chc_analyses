"""gates.py — SPEC 17's three gates, plus SPEC 16's climatology tolerance.

Nothing scientific may be read until every one of these passes.

  1. CLIMATOLOGY. Equal thirds must score exactly 0.0000 on the atlas benchmark, both
     protocols, and on the inherited bench.py path. RPSS is defined as skill relative to
     that forecast, so any other value means the harness is wrong and every other number
     is void.

  2. SYNTHETIC SIGNAL. Two parts. (a) The inherited planted-Nino-3.4 target must come
     back positive through bench.evaluate. (b) NEW for this project: a two-zone synthetic
     rainfall field, west driven by Nino-3.4 and east by the IOD, with different annual
     cycles. The atlas pipeline must recover TWO zones on the true boundary and select
     the correct index in each. This is the gate that tests discovery, not just scoring:
     a pipeline that clusters noise or picks predictors at random fails it.

  3. SHUFFLE. Permuting season-year labels must remove positive skill, on 4 seeds.

Run: rx run exec -e e:N -- conda run -n pycpt python probes/gates.py
"""
from __future__ import annotations

import json
import sys
import time
import types
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "harness"))

import bench                       # noqa: E402
import fields as F                 # noqa: E402
import discovery as D              # noqa: E402
import indices as IX               # noqa: E402
import atlas_score as A            # noqa: E402
import pipeline as P               # noqa: E402
import pipeline_v2 as P2           # noqa: E402
import nullperm as NP              # noqa: E402
from sklearn.metrics import adjusted_rand_score   # noqa: E402
from africas2s.metrics.rpss import _cpt_boundaries  # noqa: E402

RESULTS = []


def gate(name, ok, detail=""):
    RESULTS.append((name, bool(ok)))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   {detail}" if detail else ""),
          flush=True)


def rule(t):
    print(f"\n{'=' * 78}\n{t}\n{'=' * 78}", flush=True)


# ── GATE 0: the three scorer-agreement links (Amendment 1 section 2) ─────────
rule("GATE 0 — ALL THREE SPEC 16 SCORER LINKS (Amendment 1 makes this mandatory)")

import subprocess as _sp  # noqa: E402
_r = _sp.run([sys.executable, str(ROOT / "probes" / "scorer_chain.py")],
             capture_output=True, text=True)
for _ln in _r.stdout.splitlines():
    if _ln.strip().startswith(("PASS", "FAIL")):
        print("   ", _ln.strip())
_chain = {}
for _ln in reversed(_r.stdout.splitlines()):
    if _ln.strip().startswith("{"):
        _chain = json.loads(_ln)
        break
gate("all three scorer-agreement links pass (batched==per-cell==bench.evaluate==atlas)",
     _r.returncode == 0 and _chain.get("failed") == 0,
     f"{_chain.get('passed')}/{_chain.get('links')} links, "
     f"link1 {_chain.get('link1_batched_vs_percell_maxdiff', float('nan')):.1e}, "
     f"link2 {_chain.get('link2_percell_vs_bench_maxdiff', float('nan')):.1e}")
if _r.returncode != 0:
    print("  scorer chain FAILED — stopping before any scientific number is read")
    print(_r.stdout[-2000:])
    sys.exit(1)


# ── GATE 1: climatology ───────────────────────────────────────────────────────
rule("GATE 1 — CLIMATOLOGY MUST SCORE EXACTLY ZERO")

for proto in ("walkforward", "kfold"):
    t0 = time.time()
    ff, folds, _ = P2.run_atlas_v2(protocol=proto, arm="climatology")
    r, n = A.pool(ff, select=A.family_selector("atlas/all-windows"),
                  weight=A.family_weight("atlas/all-windows"))
    gate(f"atlas climatology scores 0 under {proto}", abs(r) <= 1e-12,
         f"RPSS = {r:+.15f}, {n} scored years, {time.time() - t0:.0f}s")

sst = IX.load_boxes()
years_syn, y_syn = bench.build_synthetic(sst)
clim_mod = types.ModuleType("clim")
clim_mod.fit_predict = lambda ctx: np.full((len(ctx.test_years), 3), 1.0 / 3.0)
rf, rc, _ = bench.evaluate(clim_mod, sst, [12, 1, 2], years_syn, y_syn, "walkforward", 6)
gate("inherited bench.py climatology scores 0", abs(1 - rf.sum() / rc.sum()) <= 1e-12,
     f"RPSS = {1 - rf.sum() / rc.sum():+.15f}")


# ── GATE 2a: the inherited planted signal ─────────────────────────────────────
rule("GATE 2a — THE INHERITED PLANTED NINO-3.4 SIGNAL MUST BE RECOVERED")


def _nino_candidate(ctx):
    from scipy.stats import norm
    x = ctx.feature("nino34", gap=0, width=2, years=ctx.years)
    tr = np.isin(ctx.years, ctx.train_years)
    te = np.isin(ctx.years, ctx.test_years)
    mx, sx = x[tr].mean(), x[tr].std()
    b1, b0 = np.polyfit((x[tr] - mx) / sx, ctx.y_train, 1)
    resid = ctx.y_train - (b0 + b1 * (x[tr] - mx) / sx)
    sig = max(resid.std(ddof=2), 1e-9)
    mu = b0 + b1 * (x[te] - mx) / sx
    t33, t67 = _cpt_boundaries(ctx.y_train)
    pb, p67 = norm.cdf(t33, mu, sig), norm.cdf(t67, mu, sig)
    p = np.stack([pb, p67 - pb, 1 - p67], 1)
    return p / p.sum(1, keepdims=True)


mod = types.ModuleType("nino")
mod.fit_predict = _nino_candidate
rf, rc, _ = bench.evaluate(mod, sst, [12, 1, 2], years_syn, y_syn, "walkforward", 6)
r_syn = 1 - rf.sum() / rc.sum()
gate("planted Nino-3.4 dependence recovered by the inherited harness", r_syn > 0.15,
     f"RPSS = {r_syn:+.4f}")


# ── GATE 2b: the two-zone synthetic atlas ─────────────────────────────────────
rule("GATE 2b — A TWO-ZONE SYNTHETIC FIELD MUST BE RECOVERED, ZONES AND RECIPES")

fld = F.load_chirps()
LON_SPLIT = 42.5
truth = (fld.lons >= LON_SPLIT).astype(int)          # 0 = west, 1 = east

# Annual cycles: west unimodal peaking in August, east bimodal peaking April and November.
mm = np.arange(1, 13)
cyc_w = 1.0 + 6.0 * np.exp(-0.5 * ((mm - 8) / 1.2) ** 2)
cyc_e = 1.0 + 4.0 * np.exp(-0.5 * ((mm - 4) / 1.1) ** 2) + 4.5 * np.exp(-0.5 * ((mm - 11) / 1.1) ** 2)

# Drivers, each the pre-season index its own window would see at lead 0.
n34_mj = IX.raw_components(sst, [7, 8, 9], fld.years, 0)["nino34"]        # May+Jun
comp_as = IX.raw_components(sst, [10, 11, 12], fld.years, 0)             # Aug+Sep
iod_as = comp_as["iod_w"] - comp_as["iod_e"]


def _z(v):
    return (v - np.nanmean(v)) / (np.nanstd(v) + 1e-12)


drv_w, drv_e = _z(n34_mj), _z(iod_as)
rng = np.random.default_rng(7)

# Vectorised. The element-by-element version was 2.67 million Python iterations and was
# the step the gate suite stalled on under load; this is the same field, built with array
# ops. Determinism is preserved by drawing the whole noise array from the same seed.
year_idx = np.array([{int(y): i for i, y in enumerate(fld.years)}[int(v)]
                     for v in fld.year_of_col])
mo_idx = fld.month_of_col - 1
scale_w = np.nan_to_num(1.0 + 0.55 * drv_w, nan=1.0)[year_idx]        # (n_col,)
scale_e = np.nan_to_num(1.0 + 0.55 * drv_e, nan=1.0)[year_idx]
base_w, base_e = cyc_w[mo_idx], cyc_e[mo_idx]                        # (n_col,)
west_row = base_w * scale_w
east_row = base_e * scale_e
syn = np.where(truth[:, None] == 0, west_row[None, :], east_row[None, :])
syn = np.maximum(syn + rng.normal(0, 0.25, size=syn.shape), 0.01)

tr_i, te_i = bench.make_folds(fld.years, "walkforward", 6)[-1]
tr_y, te_y = fld.years[tr_i], fld.years[te_i]
part = D.discover(syn, fld.month_of_col, fld.year_of_col, tr_y, fld.lats, fld.lons)
ari = adjusted_rand_score(truth[part.cell_index], part.labels)
gate("the synthetic partition is recovered as k = 2", part.k == 2, f"k = {part.k}")
gate("the recovered partition matches the true west/east split", ari > 0.99,
     f"ARI vs truth = {ari:.4f}")

west = int(np.argmin([fld.lons[part.zone_cells(z)].mean() for z in range(part.k)]))
east = 1 - west
wins = {z: [lab for lab, _ in part.windows[z]] for z in range(part.k)}
gate("the west zone is unimodal around JAS", any(w in ("JAS", "ASO", "JJA") for w in wins[west]),
     f"west windows {wins[west]}")
gate("the east zone is bimodal with a MAM-like and an OND-like season",
     len(wins[east]) == 2 and any(w in ("MAM", "AMJ", "FMA") for w in wins[east])
     and any(w in ("OND", "SON", "NDJ") for w in wins[east]),
     f"east windows {wins[east]}")

_usable = NP.common_usable(part, syn, fld.month_of_col, fld.year_of_col, fld.years,
                           sst, forced_windows=P.FORCED_MAM)
fcs = NP.score_fold_target_perm(part, syn, fld.month_of_col, fld.year_of_col, fld.years,
                                tr_y, te_y, sst, _usable, perm=None,
                                forced_windows=P.FORCED_MAM)
picks = {(fc.zone, fc.window): (fc.index, fc.lead) for fc in fcs if fc.discovered}
w_pick = [v for (z, lab), v in picks.items() if z == west]
e_ond = [v for (z, lab), v in picks.items() if z == east and lab in ("OND", "SON", "NDJ")]
gate("the west zone selects Nino-3.4, the index that actually drives it",
     any(p[0] == "nino34" for p in w_pick), f"west picks {w_pick}")
gate("the east zone's short-rains window selects the IOD, the index that drives it",
     any(p[0] == "iod" for p in e_ond), f"east short-rains picks {e_ond}")

r_atlas, n = A.pool([fcs], select=A.family_selector("atlas/all-windows"),
                    weight=A.family_weight("atlas/all-windows"))
gate("the synthetic atlas scores strongly positive", r_atlas > 0.30,
     f"RPSS = {r_atlas:+.4f} on {n} forecasts")


# ── GATE 3: shuffle ───────────────────────────────────────────────────────────
rule("GATE 3 — SHUFFLING SEASON-YEAR LABELS MUST REMOVE POSITIVE SKILL")

print("  Amendment 1: the shuffle is a COMPLETE-SEASON target permutation. Discovery")
print("  comes from unpermuted training rainfall; the same donor map is applied to every")
print("  zone-window seasonal series, so no wrapping window is spliced.\n")
perms = NP.permutations(len(fld.years))
vals = []
for s in range(4):
    t0 = time.time()
    ff, folds, _ = P2.run_atlas_v2(perm=perms[s])
    r, n = A.pool(ff, select=A.family_selector("atlas/all-windows"),
                  weight=A.family_weight("atlas/all-windows"))
    vals.append(r)
    print(f"    replicate {s}: RPSS = {r:+.4f}  ({n} scored years, "
          f"{time.time() - t0:.0f}s)", flush=True)
mean_shuf = float(np.mean(vals))
gate("mean shuffled atlas RPSS is at or below zero within Monte-Carlo noise",
     mean_shuf <= 0.05, f"mean = {mean_shuf:+.4f} over 4 seeds, "
     f"range {min(vals):+.4f}..{max(vals):+.4f}")
gate("not every shuffled seed is positive", not all(v > 0 for v in vals),
     f"{sum(1 for v in vals if v > 0)}/4 positive")


# ── verdict ───────────────────────────────────────────────────────────────────
rule("VERDICT")
n_fail = sum(1 for _, ok in RESULTS if not ok)
print(f"  {len(RESULTS) - n_fail}/{len(RESULTS)} gates passed")
for name, ok in RESULTS:
    if not ok:
        print(f"    FAILED: {name}")
out = {"gates": len(RESULTS), "passed": len(RESULTS) - n_fail, "failed": n_fail,
       "synthetic_bench_rpss": round(float(r_syn), 4),
       "synthetic_atlas_rpss": round(float(r_atlas), 4),
       "synthetic_partition_ari": round(float(ari), 4),
       "shuffle_mean_rpss": round(mean_shuf, 4),
       "shuffle_values": [round(float(v), 4) for v in vals],
       "spec_version": "amendment-1",
       "scorer_links": _chain.get("passed"),
       "status": "ok" if n_fail == 0 else "failed"}
(ROOT / "outputs").mkdir(exist_ok=True)
(ROOT / "outputs" / "gates.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out))
sys.exit(1 if n_fail else 0)
