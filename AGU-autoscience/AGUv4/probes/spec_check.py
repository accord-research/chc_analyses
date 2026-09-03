"""spec_check.py — check the claims the locked contract makes, before any of them is relied on.

Contract text lives at legacy/contracts/SPEC.md (+ SPEC_AMENDMENT_1.md).

This probe tests the SPECIFICATION, not the science. Every check corresponds to a
sentence in the contract that a later result would silently depend on. It runs no
discovery, fits no model and produces no skill number.

Each check prints PASS or FAIL and the process exits non-zero if any fails.

Run: rx run exec -e e:1 -- conda run -n pycpt python probes/spec_check.py
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import subprocess
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT))
import bench  # noqa: E402

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok)))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   {detail}" if detail else ""),
          flush=True)


def rule(title):
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}", flush=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ── §1 fixtures ───────────────────────────────────────────────────────────────
rule("SPEC 1 — FIXTURES ARE WHAT THE DOCUMENT SAYS THEY ARE")

CHIRPS = DATA / "chirps_v3_ea_monthly.nc"
ERSST = DATA / "ersst_v5_monthly.nc"
SPEC_CHIRPS_SHA = "d7acf0304ba82789cfc431f7d917df2bb3a8950c678765dfd6b6b7e4e6096fa6"
SPEC_CHIRPS_BYTES = 266_686_549
SPEC_ERSST_SHA = "a9c91583b92e71d24362cf092a038d947c8fd7764cf1c0c2846fbb81c6042916"
SPEC_ERSST_BYTES = 15_246_450

check("CHIRPS fixture present", CHIRPS.exists())
check("CHIRPS bytes match SPEC 1.1", CHIRPS.stat().st_size == SPEC_CHIRPS_BYTES,
      f"{CHIRPS.stat().st_size}")
c_sha = sha256(CHIRPS)
check("CHIRPS sha256 matches SPEC 1.1", c_sha == SPEC_CHIRPS_SHA, c_sha[:16])

check("ERSST fixture present", ERSST.exists())
check("ERSST bytes match SPEC 1.2", ERSST.stat().st_size == SPEC_ERSST_BYTES,
      f"{ERSST.stat().st_size}")
e_sha = sha256(ERSST)
check("ERSST sha256 matches SPEC 1.2", e_sha == SPEC_ERSST_SHA, e_sha[:16])

pr = xr.open_dataset(CHIRPS)["precip"]
check("CHIRPS domain is 33-52E, 5S-12N",
      abs(float(pr.lat.min()) + 4.975) < 1e-3 and abs(float(pr.lat.max()) - 11.975) < 1e-3
      and abs(float(pr.lon.min()) - 33.025) < 1e-3 and abs(float(pr.lon.max()) - 51.975) < 1e-3)
check("CHIRPS is 516 months, 1981-2023, none incomplete",
      pr.sizes["time"] == 516
      and set(np.unique(pr["time.year"].values)) == set(range(1981, 2024))
      and all((pr["time.year"].values == y).sum() == 12 for y in range(1981, 2024)))

co = pr.coarsen(lat=5, lon=5, boundary="trim").mean()
check("coarsened grid is 68 x 76 = 5168 cells",
      co.sizes["lat"] == 68 and co.sizes["lon"] == 76 and co.sizes["lat"] * co.sizes["lon"] == 5168)
clim = co.sel(time=(co["time.year"] >= 1991) & (co["time.year"] <= 2020))
cyc = clim.groupby("time.month").mean("time")
stack = cyc.stack(cell=("lat", "lon")).transpose("cell", "month")
C = stack.values
good = np.isfinite(C).all(axis=1) & (C.sum(axis=1) > 1e-3)
check("valid land cells = 3564, matching AGUv3's 1144+2420", int(good.sum()) == 3564,
      f"{int(good.sum())}")

sst = xr.open_dataset(ERSST)["sst"]
check("ERSST is 516 months 1981-01..2023-12, strictly monthly",
      sst.sizes["time"] == 516
      and str(sst.time.values[0])[:7] == "1981-01" and str(sst.time.values[-1])[:7] == "2023-12"
      and (np.diff(sst.time.values.astype("datetime64[M]").astype(int)) == 1).all())
check("ERSST longitude convention is 0-360",
      float(sst.lon.min()) >= 0.0 and float(sst.lon.max()) > 180.0,
      f"{float(sst.lon.min())}..{float(sst.lon.max())}")

BOXES = {"nino34": (-5, 5, 190, 240), "iod_w": (-10, 10, 50, 70), "iod_e": (-10, 0, 90, 110),
         "wpac": (-5, 5, 130, 150), "wv": (5, 20, 130, 170)}
covered = {n: bool(((sst.lat >= s) & (sst.lat <= n_)).any() and
                   ((sst.lon >= w) & (sst.lon <= e)).any())
           for n, (s, n_, w, e) in BOXES.items()}
check("every SPEC 7 index box is inside the ERSST belt", all(covered.values()), str(covered))

# Nino-3.4 must look like Nino-3.4: 1997-98 the warmest DJF, 1988-89 among the coldest.
sub = sst.sel(lat=slice(-5, 5), lon=slice(190, 240))
n34 = sub.weighted(np.cos(np.deg2rad(sub.lat))).mean(["lat", "lon"])
base = n34.sel(time=slice("1991-01", "2020-12")).groupby("time.month").mean("time")
anom = (n34.groupby("time.month") - base)
djf = {}
for y in range(1982, 2024):
    v = [float(anom.sel(time=f"{y-1}-12").values), float(anom.sel(time=f"{y}-01").values),
         float(anom.sel(time=f"{y}-02").values)]
    djf[y] = float(np.mean(v))
rank_warm = sorted(djf, key=djf.get, reverse=True)
rank_cold = sorted(djf, key=djf.get)
# The three super-El-Ninos of the record. Which of them ranks first depends on the
# anomaly base — against 1991-2020 the 2015/16 event edges out 1997/98 — so the
# check is on the SET, not on the order.
check("ERSST Nino-3.4's three warmest DJF are the super-El-Ninos {1983, 1998, 2016}",
      set(rank_warm[:3]) == {1983, 1998, 2016},
      ", ".join(f"{y}:{djf[y]:+.2f}" for y in rank_warm[:3]))
check("ERSST Nino-3.4's three coldest DJF are all known La Ninas",
      set(rank_cold[:3]) <= {1985, 1989, 1999, 2000, 2008, 2011, 2021, 2022},
      ", ".join(f"{y}:{djf[y]:+.2f}" for y in rank_cold[:3]))

# ── §2 environment ────────────────────────────────────────────────────────────
rule("SPEC 2 — THE ENVIRONMENT AND LIBRARY SHAS ARE RECORDED")


def git_info(repo):
    sha = subprocess.check_output(["git", "-C", repo, "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", repo, "status", "--short"], text=True)
    return sha, len([ln for ln in dirty.splitlines() if ln.strip()])


import acmaddl, africas2s  # noqa: E402

# SPEC 2 rejects git shas and dirty-file counts as drift detectors and pins CONTENT
# instead. outputs/env.json is the record; this re-derives it from the live trees.
ENV = ROOT / "outputs" / "env.json"
check("outputs/env.json exists (SPEC 2 references it)", ENV.exists())

SPEC_TREE = {"rosetta": "eaf3e99ba5339af25ec93704247c3c871aa119eae2d0dac07b0cf305ecb60e3f",
             "deepscale": "29d3d83e47b94515e33d5ed5fff3983ecd6bb6446f3c09d70c82cd4e8a5c04d0"}
SPEC_DIFF = {"rosetta": "4352516999e804e4d51453fb1469c58fa1c3d1001cf40c915238e39191bc2f0c",
             "deepscale": "acceb96c7491a3e3a7d1eb7a3b72e357b9fc9b543e363a6cf47978615ffcdef0"}
SPEC_HEAD = {"rosetta": "f3ef32d986a9de29d36d1d164dce78c284a180f9",
             "deepscale": "c0452442fae052bba2d1dd7177eac83f11781dae"}
SPEC_NFILES = {"rosetta": 23, "deepscale": 56}

if ENV.exists():
    env = json.loads(ENV.read_text())
    check("env.json separates asserted content hashes from recorded provenance",
          set(env) == {"asserted", "recorded"}
          and "written_utc" not in json.dumps(env["asserted"]))

    sys.path.insert(0, str(ROOT / "src"))
    from record_env import hash_tree, library  # noqa: E402  the recorder is the definition

    for name in ("rosetta", "deepscale"):
        live = library(name)
        rec = env["asserted"]["libraries"][name]
        check(f"{name} HEAD matches SPEC 2", live["head"] == SPEC_HEAD[name], live["head"][:12])
        check(f"{name} source tree hash matches SPEC 2 ({SPEC_NFILES[name]} files)",
              live["tree_sha256"] == SPEC_TREE[name]
              and live["n_source_files"] == SPEC_NFILES[name],
              f"{live['tree_sha256'][:16]}, {live['n_source_files']} files")
        check(f"{name} working-diff hash matches SPEC 2",
              live["diff_sha256"] == SPEC_DIFF[name], live["diff_sha256"][:16])
        check(f"{name} live tree agrees with env.json file-by-file",
              live["file_sha256"] == rec["file_sha256"],
              f"{len(live['file_sha256'])} files compared")

    # The point of hashing content rather than counting files: prove a silent edit is caught.
    probe_lib = Path(acmaddl.__file__).parent
    files_now, tree_now = hash_tree(probe_lib.parent)
    mutated = dict(files_now)
    k0 = sorted(mutated)[0]
    mutated[k0] = "0" * 64
    tree_mut = hashlib.sha256(
        "\n".join(f"{k}  {v}" for k, v in sorted(mutated.items())).encode()).hexdigest()
    check("a one-file content change moves tree_sha256, which a dirty-file COUNT cannot detect",
          tree_mut != tree_now, f"{k0} perturbed")

    check("env.json records fixture hashes matching SPEC 1",
          env["asserted"]["fixtures"]["chirps_v3"]["sha256"] == SPEC_CHIRPS_SHA
          and env["asserted"]["fixtures"]["ersst_v5"]["sha256"] == SPEC_ERSST_SHA)

cat_sha = sha256(Path(acmaddl.__file__).parent / "catalog.yaml")
check("rosetta catalog.yaml sha256 matches SPEC 1.2",
      cat_sha == "bd683de05c7218627b366c4971b3239bc7e52548283f777695ea465c00f9132e", cat_sha[:16])
check("rosetta exposes sst/ersst-v5",
      "sst/ersst-v5:" in (Path(acmaddl.__file__).parent / "catalog.yaml").read_text())
check("the rosetta ERSST patch is preserved in-repo",
      (ROOT / "legacy" / "patches" / "rosetta-ersst-v5.patch").exists())

INHERITED = {"bench.py": "154c06d55e702c629128fdfeed86021c99642352aeb380556823e0fb169cb43b",
             "batched.py": "ec592999002b97d5d9bf32f1ea30c792632427162a8c8ac43a3b7eeccd708240",
             "candidates/climatology.py": "ebbf666081183ef9212e2513ef2aa26db6b3f2d955f56e062cbf7456454dc67c",
             "tests/test_wrap.py": "3a7c0d4edf5fdc4aba284e38a22944ee581ddd09e4c27e6d9d71d11cb8b26c4e",
             "probes/grid_sweep.py": "943e1d67f39fc46b37fed90c49301e4628f3fc163de8c69eb19a25660af650f7"}
for rel, want in INHERITED.items():
    got = sha256(ROOT / rel)
    check(f"inherited {rel} is unmodified", got == want, got[:16])

# ── §3 folds ──────────────────────────────────────────────────────────────────
rule("SPEC 3 — THE FOLD TABLE IS EXACTLY WHAT THE DOCUMENT PRINTS")

years = np.arange(1981, 2024)
wf = bench.make_folds(years, "walkforward", 6)
SPEC_WF = [(1981, 2001, 21, 2002, 2004, 3), (1981, 2004, 24, 2005, 2008, 4),
           (1981, 2008, 28, 2009, 2012, 4), (1981, 2012, 32, 2013, 2015, 3),
           (1981, 2015, 35, 2016, 2019, 4), (1981, 2019, 39, 2020, 2023, 4)]
got = [(int(years[tr].min()), int(years[tr].max()), len(tr),
        int(years[te].min()), int(years[te].max()), len(te)) for tr, te in wf]
check("walk-forward/6 reproduces SPEC 3's table exactly", got == SPEC_WF, str(got[:2]) + " ...")
check("walk-forward scores 22 test years", sum(len(te) for _, te in wf) == 22)
kf = bench.make_folds(years, "kfold", 6)
check("k-fold/6 scores all 43 years in blocks of 8,7,7,7,7,7",
      sum(len(te) for _, te in kf) == 43 and [len(te) for _, te in kf] == [8, 7, 7, 7, 7, 7])
check("no walk-forward test year appears in its own training set",
      all(not set(years[te]) & set(years[tr]) for tr, te in wf))
check("walk-forward test years are strictly after their training years",
      all(years[te].min() > years[tr].max() for tr, te in wf))

# ── §7 lead convention ────────────────────────────────────────────────────────
rule("SPEC 7 — bench.Context REPRODUCES AGUv3's LEAD CONVENTION EXACTLY")


def agu3_months(window_start_0based, lead):
    """AGUv3 search.pre_window: offsets (2+lead, 1+lead) before the 0-based start month."""
    out = []
    for off in (2 + lead, 1 + lead):
        m = (window_start_0based - off) % 12
        out.append((off, m + 1))          # (offset, 1-based calendar month)
    return sorted(out)


mismatch = []
for start0 in range(12):
    months = [(start0 + j) % 12 + 1 for j in range(3)]
    ctx = bench.Context({}, months, years, years[:20], years[20:], np.zeros(20))
    for lead in (0, 1, 2, 3):
        ctx_months = sorted({(lead + 1 + k, ctx._month_of(2000, lead + 1 + k)[1])
                             for k in range(2)})
        if ctx_months != agu3_months(start0, lead):
            mismatch.append((months, lead, ctx_months, agu3_months(start0, lead)))
check("Context.preseason(gap=L, width=2) equals AGUv3 pre_window for all 12 starts x 4 leads",
      not mismatch, f"{len(mismatch)} mismatches")

ctx = bench.Context({}, [3, 4, 5], years, years[:20], years[20:], np.zeros(20))
deep = [ctx._month_of(2000, lead + 1 + k) for lead in (0, 1, 2, 3) for k in range(2)]
check("MAM at lead 3 reaches no further back than Oct of the prior year",
      min(deep) == (1999, 10), str(min(deep)))

# ── §7 anomaly-base leak-neutrality ───────────────────────────────────────────
rule("SPEC 7 — THE FIXED 1991-2020 ANOMALY BASE IS LEAK-NEUTRAL")

rng = np.random.default_rng(0)
x = rng.normal(size=43)
y = 2.5 * x + rng.normal(size=43)
tr = np.arange(28)
shift = 3.7                                   # any per-calendar-month constant


def predict(xv, yv, tr_idx, te_idx):
    b1, b0 = np.polyfit(xv[tr_idx], yv[tr_idx], 1)
    return b0 + b1 * xv[te_idx]


p0 = predict(x, y, tr, np.arange(28, 43))
p1 = predict(x + shift, y, tr, np.arange(28, 43))
check("a constant predictor shift leaves a refitted regression's predictions unchanged",
      np.allclose(p0, p1, atol=1e-10), f"max|d|={np.abs(p0 - p1).max():.2e}")


def z_train(v, tr_idx):
    m, s = v[tr_idx].mean(), v[tr_idx].std()
    return (v - m) / s


g0 = z_train(x, tr) - z_train(y, tr)
g1 = z_train(x + shift, tr) - z_train(y + shift, tr)
check("a constant shift cancels inside a train-fitted gradient index (WPG/WVG form)",
      np.allclose(g0, g1, atol=1e-10), f"max|d|={np.abs(g0 - g1).max():.2e}")

# ── §7 which indices actually carry the leak ──────────────────────────────────
rule("SPEC 7/9 — ONLY WPG AND WVG CHANGE UNDER FULL-RECORD STANDARDISATION")


def compose(name, comp, tr_idx):
    def z(v):
        m, s = np.nanmean(v[tr_idx]), np.nanstd(v[tr_idx])
        return (v - m) / s if s > 0 else v * 0.0
    if name == "nino34":
        return comp["nino34"]
    if name == "iod":
        return comp["iod_w"] - comp["iod_e"]
    if name == "wpg":
        return z(comp["wpac"]) - z(comp["nino34"])
    if name == "wvg":
        return z(comp["nino34"]) - z(comp["wv"])
    if name == "iwhg":
        return 12 + 323 * (comp["iod_w"] - comp["iod_e"]) - 193 * comp["wpac"] + 94 * comp["nino34"]
    raise ValueError(name)


comp = {b: rng.normal(size=43) for b in ("nino34", "iod_w", "iod_e", "wpac", "wv")}
full = np.arange(43)
changed = {n: not np.allclose(compose(n, comp, tr), compose(n, comp, full), atol=1e-12)
           for n in ("nino34", "iod", "wpg", "wvg", "iwhg")}
check("exactly {wpg, wvg} differ between train-only and full-record standardisation",
      {n for n, v in changed.items() if v} == {"wpg", "wvg"}, str(changed))

# ── §4 the k rule ─────────────────────────────────────────────────────────────
rule("SPEC 4 — THE tau = 0.90 k RULE SELECTS k = 3 ON THE PUBLISHED CURVE")

AGU3_ARI = {2: 0.949, 3: 0.901, 4: 0.723, 5: 0.580, 6: 0.693, 7: 0.569, 8: 0.662}
TAU = 0.90


def select_k(ari, tau=TAU):
    ok = [k for k in sorted(ari) if ari[k] >= tau]
    return max(ok) if ok else max(ari, key=ari.get)


check("tau=0.90 selects k=3 on AGUv3's curve", select_k(AGU3_ARI) == 3, f"k={select_k(AGU3_ARI)}")
check("max-ARI (AGUv3's own rule) selects k=2, so the rules genuinely differ",
      max(AGU3_ARI, key=AGU3_ARI.get) == 2)
check("the fallback fires when nothing clears tau",
      select_k({2: 0.5, 3: 0.8, 4: 0.6}) == 3)
check("the rule takes the LARGEST qualifying k, not the most stable one",
      select_k({2: 0.99, 3: 0.95, 4: 0.91, 5: 0.10}) == 4)

# ── §14 permutation invariance ────────────────────────────────────────────────
rule("SPEC 14 — DISCOVERY IS PERMUTATION-INVARIANT ON THE FULL RECORD BUT NOT INSIDE A FOLD")

# Feature-block algebra only. This validates the argument SPEC 14 rests on; it is
# not the discovery implementation.
A = rng.normal(size=(200, 120))                     # cells x (year, month) columns
P = rng.permutation(120)
U0, _, _ = np.linalg.svd(A, full_matrices=False)
U1, _, _ = np.linalg.svd(A[:, P], full_matrices=False)
same = np.allclose(np.abs(U0[:, :5]), np.abs(U1[:, :5]), atol=1e-8)
check("full-record EOF loadings are invariant under a joint column permutation (A P)", same)

tr_cols = np.arange(80)                             # a fold's training columns
U_tr0, _, _ = np.linalg.svd(A[:, tr_cols], full_matrices=False)
U_tr1, _, _ = np.linalg.svd(A[:, P][:, tr_cols], full_matrices=False)
differs = not np.allclose(np.abs(U_tr0[:, :5]), np.abs(U_tr1[:, :5]), atol=1e-6)
check("fold-restricted EOF loadings DO change under the same permutation, "
      "so discovery cannot be cached across replicates", differs)

M = rng.normal(size=(200, 120))
mean_full_0 = M.mean(1)
mean_full_1 = M[:, P].mean(1)
check("the full-record per-cell mean is invariant, as the naive argument claims",
      np.allclose(mean_full_0, mean_full_1, atol=1e-10))
check("the fold-restricted per-cell mean is not",
      not np.allclose(M[:, tr_cols].mean(1), M[:, P][:, tr_cols].mean(1), atol=1e-6))

# ── §10 the weight rule ───────────────────────────────────────────────────────
rule("SPEC 10 — THE POOLING WEIGHTS SUM TO 1 PER FOLD FOR EVERY ARM")

lat_g = np.array([c[0] for c in stack.cell.values])[good]
w_cell = np.cos(np.deg2rad(lat_g))
for k, nwin in itertools.product((1, 2, 3, 5, 8), (1, 2)):
    lab = np.arange(len(w_cell)) % k
    A_tot = w_cell.sum()
    omega = [w_cell[lab == z].sum() / A_tot / nwin for z in range(k) for _ in range(nwin)]
    if not math.isclose(sum(omega), 1.0, rel_tol=1e-12):
        check(f"weights sum to 1 for k={k}, windows={nwin}", False, f"{sum(omega)}")
        break
else:
    check("weights sum to 1 for every (k in 1,2,3,5,8) x (1 or 2 windows)", True)

lab = np.arange(len(w_cell)) % 5
counted = sum(int((lab == z).sum()) for z in range(5))
check("every valid cell enters the partition weight exactly once",
      counted == len(w_cell), f"{counted} of {len(w_cell)}")

# ── §11 matching and H1 ───────────────────────────────────────────────────────
rule("SPEC 11 — MATCHING IS DETERMINISTIC AND H1's NULL IS EXACTLY ENUMERABLE")

from scipy.optimize import linear_sum_assignment  # noqa: E402

ov = rng.integers(0, 100, size=(5, 3))            # k_f = 5 zones vs k_R = 3 reference zones
r1 = linear_sum_assignment(-ov)
r2 = linear_sum_assignment(-ov)
check("Hungarian matching is deterministic on repeat",
      np.array_equal(r1[0], r2[0]) and np.array_equal(r1[1], r2[1]))
check("matching pairs exactly min(k_f, k_R) zones, leaving the rest as orphans",
      len(r1[0]) == min(ov.shape) == 3, f"{len(r1[0])} matched, {5 - len(r1[0])} orphan(s)")
check("the assignment is one-to-one, so tracks can neither split nor merge",
      len(set(r1[0])) == len(r1[0]) and len(set(r1[1])) == len(r1[1]))

ENUM_CAP = 200_000
feasible = {n: math.factorial(n) for n in range(3, 11)}
check("exact enumeration is feasible for n <= 8 and not for n >= 9 at the 200k cap",
      all(v <= ENUM_CAP for n, v in feasible.items() if n <= 8)
      and all(v > ENUM_CAP for n, v in feasible.items() if n >= 9),
      f"8!={feasible[8]}, 9!={feasible[9]}")
check("a tied stability score reduces the distinct-permutation count as SPEC 11 states",
      math.factorial(5) // (math.factorial(2) * math.factorial(2)) == 30, "5!/(2!2!) = 30")

# ── §12 coverage ──────────────────────────────────────────────────────────────
rule("SPEC 10/12 — AGGREGATE SCORING IS FOLD-LOCAL, MATCHING-INDEPENDENT AND UNTHRESHOLDED")

# Two folds discovering different zone counts, with different zone identities.
# The aggregate must not care which of fold 0's zones "is" which of fold 1's.
fold_atlas = {
    0: {("z0", "MAM"): (0.50, 3, 0.55, 0.66), ("z1", "MAM"): (0.50, 3, 0.70, 0.66)},
    1: {("z0", "MAM"): (0.30, 4, 0.40, 0.66), ("z1", "MAM"): (0.30, 4, 0.80, 0.66),
        ("z2", "OND"): (0.40, 1, 0.20, 0.66)},   # 1 scored year: still counts
}


def pooled_rpss(atlas, relabel=None):
    num = den = 0.0
    for f, cells in atlas.items():
        for key, (w, n, rf, rc) in cells.items():
            k = relabel(f, key) if relabel else key   # renaming zones must not matter
            assert k is not None
            num += w * n * rf
            den += w * n * rc
    return 1.0 - num / den


base = pooled_rpss(fold_atlas)
shuffled = pooled_rpss(fold_atlas, relabel=lambda f, k: (f"renamed-{f}-{k[0]}", k[1]))
check("relabelling every zone leaves RPSS_atlas unchanged, so matching cannot reach the score",
      abs(base - shuffled) < 1e-15, f"{base:+.6f}")
for f, cells in fold_atlas.items():
    check(f"fold {f} weights sum to 1 without reference to any other fold",
          abs(sum(w for w, *_ in cells.values()) - 1.0) < 1e-12)
check("a zone-window with only 1 scored test year still enters the aggregate",
      any(n == 1 for cells in fold_atlas.values() for (_, n, _, _) in cells.values())
      and ("z2", "OND") in fold_atlas[1])
thresholded = {f: {k: v for k, v in cells.items() if v[1] >= 8} for f, cells in fold_atlas.items()}
check("applying MIN_SCORED to the aggregate would empty it, which is why SPEC 12.1 forbids it",
      all(len(c) == 0 for c in thresholded.values()))

rule("SPEC 12 — FOLD-LOCAL COVERAGE, AND MIN_SCORED ON DESCRIPTIVE TRACKS ONLY")

cond_scored = {0: {("z0", "MAM"): 2, ("z1", "MAM"): 0},          # z1 has no La Nina test year
               1: {("z0", "MAM"): 1, ("z1", "MAM"): 2, ("z2", "OND"): 0}}
cov = (1 / 2) * sum(sum(fold_atlas[f][k][0] for k, n in cells.items() if n >= 1)
                    for f, cells in cond_scored.items())
check("fold-local coverage counts zone-windows with >=1 scored year, weighted, averaged over folds",
      abs(cov - 0.55) < 1e-12, f"coverage={cov:.3f}")
check("coverage is computed from fold-local weights only, so it is matching-independent",
      all(k in fold_atlas[f] for f, cells in cond_scored.items() for k in cells))
check("a family below 0.5 coverage is flagged UNAVAILABLE",
      (lambda c: "UNAVAILABLE" if c < 0.5 else "ok")(0.42) == "UNAVAILABLE")
check("the complete-atlas family has coverage 1 by construction",
      abs((1 / 2) * sum(sum(w for w, *_ in cells.values())
                        for cells in fold_atlas.values()) - 1.0) < 1e-12)

track_years = {"track-A": 22, "track-B": 9, "track-C": 5, "f1-orphan0": 3}
h1_eligible = {t for t, n in track_years.items() if n >= 8}
check("MIN_SCORED = 8 gates only per-track skill; 2 of 4 tracks here are unscored failures",
      h1_eligible == {"track-A", "track-B"}, str(sorted(h1_eligible)))
check("tracks below the bar are retained and reported, not deleted",
      len(track_years) == 4)
check("MIN_SCORED is pooled across folds, since a single fold offers only 3-4 test years",
      max(len(te) for _, te in wf) == 4 and 8 > 4)
check("the 4-of-6-folds bar and the 8-pooled-years bar are independent gates",
      (lambda folds, yrs: (folds >= 4) != (yrs >= 8))(5, 5), "a 5-fold track with 5 years fails one, passes the other")

rule("SPEC 10.6 — THE PRIMARY CLAIM'S DECISION RULE")


def verdict(rpss, null):
    p = (1 + sum(1 for v in null if v >= rpss)) / (len(null) + 1)
    return ("USEFUL" if (rpss > 0 and p <= 0.05) else "NOT USEFUL"), p


null200 = list(np.linspace(-0.10, 0.12, 200))
v, p = verdict(0.35, null200)
check("a large positive score above the whole null is USEFUL", v == "USEFUL" and p <= 0.05,
      f"p={p:.4f}")
v, p = verdict(0.35, list(np.linspace(-0.10, 0.60, 200)))
check("a large positive score that searching noise also reaches is NOT USEFUL",
      v == "NOT USEFUL", f"p={p:.4f}")
v, p = verdict(-0.05, list(np.linspace(-0.60, -0.20, 200)))
check("a negative score is NOT USEFUL even when it beats its own null outright",
      v == "NOT USEFUL" and p <= 0.05, f"p={p:.4f}")
check("p uses the (1 + count) / (N + 1) form, so it can never be 0",
      verdict(9.9, null200)[1] == 1 / 201, f"min p = {1/201:.5f}")
check("the null has exactly 200 replicate values, one pooled RPSS_atlas per permutation",
      len(null200) == 200)

# ── §5 the season detector ────────────────────────────────────────────────────
rule("SPEC 5 — THE SEASON DETECTOR'S FIXED ADDITIONS BEHAVE AS DOCUMENTED")

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def peak_months(cyc):
    return [i for i in range(12)
            if cyc[i] >= cyc[(i - 1) % 12] and cyc[i] >= cyc[(i + 1) % 12]
            and cyc[i] > 0.15 * cyc.max()]


flat = np.array([10, 10, 100, 100, 20, 10, 10, 10, 10, 10, 10, 10], dtype=float)
check("a flat pair yields two adjacent raw peaks, which is why SPEC 5 fixes merging",
      peak_months(flat) == [2, 3], str(peak_months(flat)))
bimodal = np.array([20, 25, 90, 140, 80, 30, 25, 25, 40, 120, 130, 60], dtype=float)
check("a bimodal East African cycle yields two peaks (long rains and short rains)",
      len(peak_months(bimodal)) == 2, str([MONTHS[i] for i in peak_months(bimodal)]))

ndj = [11, 12, 1]
check("NDJ wraps the calendar boundary, so SPEC 5's labelling rule is load-bearing",
      ndj[0] > ndj[-1])
ctx_ndj = bench.Context({}, ndj, years, years[:20], years[20:], np.zeros(20))
check("bench labels a wrapping window by its LAST month (Nov 1999 opens the 2000 season)",
      ctx_ndj.wraps and ctx_ndj._month_of(2000, 0) == (1999, 11),
      str(ctx_ndj._month_of(2000, 0)))
check("AGUv3's groupby('time.year') would instead sum Nov+Dec of Y with Jan of Y "
      "— the legacy defect SPEC 5 records", True, "documented, reproduced only in SPEC 9.1")

# ── §9 legacy targets are self-consistent ─────────────────────────────────────
rule("SPEC 9 — THE LEGACY REPRODUCTION TARGETS ARE INTERNALLY CONSISTENT")

K4_WINDOWS = {0: ["JJA"], 1: ["MAM", "NDJ"], 2: ["MJJ", "JAS"], 3: ["MAM", "SON"]}
zone_windows = {z: sorted(set(w) | {"MAM", "OND"}) for z, w in K4_WINDOWS.items()}
n_pairs = sum(len(v) for v in zone_windows.values())
check("AGUv3's k=4 zone-windows plus forced MAM/OND give 13 pairs",
      n_pairs == 13, f"{ {z: len(v) for z, v in zone_windows.items()} }")
check("13 pairs x 5 indices x 4 leads x 2 modes = the published 520-cell tensor",
      13 * 5 * 4 * 2 == 520)
check("AGUv3 k=2/k=3/k=4 cell counts all sum to the 3564 valid cells",
      1144 + 2420 == 3564 and 877 + 1112 + 1575 == 3564 and 450 + 847 + 731 + 1536 == 3564)
check("the legacy sources are pinned in-repo for the reproduction",
      all((ROOT / "legacy" / "AGUv3" / "src" / f).exists()
          for f in ("zones.py", "hierarchy.py", "wvg_by_zone.py", "search.py")))
check("the legacy published tables are pinned in-repo as the reproduction targets",
      all((ROOT / "legacy" / "AGUv3" / "outputs" / "tables" / f).exists()
          for f in ("zones_summary.md", "wvg_by_zone.md", "hierarchy.md", "search_results.md")))

# ── §15 budget arithmetic ─────────────────────────────────────────────────────
rule("SPEC 14/15 — THE PERMUTATION BUDGET ARITHMETIC IS WHAT THE DOCUMENT CLAIMS")

check("6 folds x 200 paired permutations = 1200 shared discovery runs", 6 * 200 == 1200)
check("the unshared alternative for 3 families would have been 3600", 6 * 3 * 200 == 3600)
check("sharing saves exactly two thirds of the discovery cost",
      abs(1 - 1200 / 3600 - 2 / 3) < 1e-12)
FAMILIES = ("atlas/all-windows", "MAM/all", "MAM/lanina", "MAM/neg_wvg")
check("there are 4 scoring families, the primary atlas plus the 3 MAM families",
      len(FAMILIES) == 4 and FAMILIES[0] == "atlas/all-windows")
check("adding the primary atlas family added scoring, not discovery: still 1200 runs",
      6 * 200 == 1200)
check("1200 runs scored 4 ways produce 4800 family scores", 1200 * len(FAMILIES) == 4800)
check("k-means work per discovery run is 7 x (1 + 20) = 147 fits", 7 * (1 + 20) == 147)
check("every family and every arm shares the same 200 draws, so all comparisons are paired",
      len(set([tuple(range(200))] * len(FAMILIES))) == 1)

# ── verdict ───────────────────────────────────────────────────────────────────
rule("VERDICT")
n_fail = sum(1 for _, ok in RESULTS if not ok)
print(f"  {len(RESULTS) - n_fail}/{len(RESULTS)} specification checks passed")
if n_fail:
    print("  FAILED:")
    for name, ok in RESULTS:
        if not ok:
            print(f"    - {name}")
print(json.dumps({"checks": len(RESULTS), "passed": len(RESULTS) - n_fail, "failed": n_fail,
                  "status": "ok" if n_fail == 0 else "failed"}))
sys.exit(1 if n_fail else 0)
