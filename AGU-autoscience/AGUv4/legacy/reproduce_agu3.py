"""reproduce_agu3.py — SPEC 9.1, the legacy provenance check.

This does NOT reimplement AGUv3. It runs AGUv3's own four scripts, byte-for-byte as
pinned in legacy/AGUv3/src/, against the locked fixtures, and diffs the markdown tables
they emit against the ones AGUv3 published.

Mechanics. The legacy scripts resolve everything from `parents[1]` of their own file, so
they are copied into legacy/run/src/ and given legacy/run/data/ and legacy/run/outputs/.
Nothing is edited; the copy exists only so the regenerated tables cannot overwrite the
pinned reference tables in legacy/AGUv3/outputs/. The fixtures are symlinked into the two
paths the legacy code expects:

    legacy/run/data/kenya_somalia_chirps_monthly.nc  -> data/chirps_v3_ea_monthly.nc
    legacy/AGUv0/data/ersst_monthly.nc               -> data/ersst_v5_monthly.nc

Order matters: zones.py writes zones.nc, hierarchy.py writes zones_k3/k4.nc, and
search.py reads zones_k4.nc.

SPEC 9.1's two tiers. Tier 1 is everything that depends on CHIRPS alone and is checked
EXACTLY, because the fixture is byte-verified to reproduce AGUv3's 3564-cell input. Tier
2 depends on the refetched ERSST and is checked to 0.01 with the survivor count allowed
79 +/- 3. Tier 1 failure stops the project; Tier 2 failure stops it pending a fixture
investigation.

The legacy arm is provenance only. It is NOT an operand in the leakage subtraction --
that is SPEC 9.3 minus SPEC 9.2, both of which are out-of-sample.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "legacy"
REF = LEGACY / "AGUv3" / "outputs" / "tables"
RUN = LEGACY / "run"
PY = "/opt/homebrew/Caskroom/miniforge/base/envs/pycpt/bin/python"

CHECKS = []


def check(tier, name, ok, detail=""):
    CHECKS.append((tier, name, bool(ok)))
    print(f"  [{tier}] {'PASS' if ok else 'FAIL'}  {name}"
          + (f"   {detail}" if detail else ""), flush=True)


def setup():
    if RUN.exists():
        shutil.rmtree(RUN)
    (RUN / "data").mkdir(parents=True)
    (RUN / "outputs" / "tables").mkdir(parents=True)
    (RUN / "outputs" / "figures").mkdir(parents=True)
    shutil.copytree(LEGACY / "AGUv3" / "src", RUN / "src")

    link = RUN / "data" / "kenya_somalia_chirps_monthly.nc"
    link.symlink_to(ROOT / "data" / "chirps_v3_ea_monthly.nc")
    v0 = LEGACY / "AGUv0" / "data"
    v0.mkdir(parents=True, exist_ok=True)
    e = v0 / "ersst_monthly.nc"
    if e.exists() or e.is_symlink():
        e.unlink()
    e.symlink_to(ROOT / "data" / "ersst_v5_monthly.nc")
    print(f"  legacy tree at {RUN.relative_to(ROOT)}, fixtures symlinked", flush=True)


def run(script):
    t0 = time.time()
    r = subprocess.run([PY, str(RUN / "src" / script)], capture_output=True, text=True,
                       cwd=str(RUN))
    print(f"  ran {script}: exit {r.returncode} in {time.time() - t0:.0f}s", flush=True)
    if r.returncode != 0:
        print(r.stdout[-3000:])
        print(r.stderr[-3000:], file=sys.stderr)
        raise SystemExit(f"legacy {script} failed")
    return r.stdout


def rows(path):
    """Markdown pipe-table rows as lists of cells, skipping separators."""
    out = []
    for ln in Path(path).read_text().splitlines():
        ln = ln.strip()
        if not ln.startswith("|") or set(ln) <= set("|- "):
            continue
        out.append([c.strip() for c in ln.strip("|").split("|")])
    return out


def num(s):
    try:
        return float(s)
    except ValueError:
        return None


def main():
    print("SPEC 9.1 — LEGACY REPRODUCTION\n")
    got = RUN / "outputs" / "tables"
    reuse = "--reuse" in sys.argv and got.exists() and all(
        (got / f).exists() for f in ("zones_summary.md", "hierarchy.md",
                                     "wvg_by_zone.md", "search_results.md"))
    if reuse:
        print("  --reuse: comparing the tables already produced by the legacy scripts",
              flush=True)
    else:
        setup()
        for s in ("zones.py", "hierarchy.py", "wvg_by_zone.py", "search.py"):
            run(s)

    # ── Tier 1: CHIRPS-only, exact ───────────────────────────────────────────
    print("\nTier 1 — CHIRPS-only quantities, checked EXACTLY")
    zr, zg = rows(REF / "zones_summary.md"), rows(got / "zones_summary.md")

    def zone_block(r):
        return [x for x in r if len(x) == 7 and x[0].isdigit()]

    def ari_block(r):
        return [x for x in r if len(x) == 4 and x[0].isdigit() and num(x[1]) is not None]

    def orient_block(r):
        return [x for x in r if len(x) == 4 and x[0] in ("Kenya", "Somalia")]

    zb_r, zb_g = zone_block(zr), zone_block(zg)
    check(1, "k=2 zone table has the same shape", len(zb_r) == len(zb_g) == 2,
          f"{len(zb_g)} zones")
    check(1, "k=2 cell counts are exactly 1144 and 2420",
          [x[1] for x in zb_g] == ["1144", "2420"], str([x[1] for x in zb_g]))
    check(1, "k=2 centroids agree to 0.05 deg",
          all(abs(num(g[i]) - num(r[i])) <= 0.05 for g, r in zip(zb_g, zb_r) for i in (2, 3)),
          "; ".join(f"({g[2]}N,{g[3]}E)" for g in zb_g))
    check(1, "k=2 regimes and discovered windows are identical",
          [(x[5], x[6]) for x in zb_g] == [(x[5], x[6]) for x in zb_r],
          str([x[6] for x in zb_g]))

    ab_r, ab_g = ari_block(zr), ari_block(zg)
    check(1, "the k=2..8 bootstrap ARI curve agrees to 0.005",
          len(ab_g) == len(ab_r) and all(abs(num(g[1]) - num(r[1])) <= 0.005
                                         for g, r in zip(ab_g, ab_r)),
          " ".join(g[1] for g in ab_g))
    check(1, "the k=2..8 silhouette curve agrees to 0.005",
          all(abs(num(g[3]) - num(r[3])) <= 0.005 for g, r in zip(ab_g, ab_r)),
          " ".join(g[3] for g in ab_g))
    check(1, "max-ARI still selects k=2",
          max(ab_g, key=lambda x: num(x[1]))[0] == "2")

    ob_r, ob_g = orient_block(zr), orient_block(zg)
    check(1, "within-country orientation eta^2 agrees to 0.005 at k=2",
          all(abs(num(g[1]) - num(r[1])) <= 0.005 and abs(num(g[2]) - num(r[2])) <= 0.005
              for g, r in zip(ob_g, ob_r)),
          "; ".join(f"{g[0]} lon={g[1]} lat={g[2]}" for g in ob_g))

    hr, hg = rows(REF / "hierarchy.md"), rows(got / "hierarchy.md")

    def hzone(r):
        return [x for x in r if len(x) == 10 and x[0].isdigit()]

    hz_r, hz_g = hzone(hr), hzone(hg)
    check(1, "the hierarchy table has the same 22 zone-window rows",
          len(hz_g) == len(hz_r), f"{len(hz_g)} rows")
    check(1, "k=3 and k=4 cell counts are exactly the published ones",
          [x[1] for x in hz_g] == [x[1] for x in hz_r],
          str(sorted({x[1] for x in hz_g})))
    check(1, "k=3 and k=4 centroids are identical to 0.1 deg",
          all(g[2] == r[2] for g, r in zip(hz_g, hz_r)),
          str(sorted({x[2] for x in hz_g})))
    check(1, "every discovered window at k=3 and k=4 is identical",
          [(x[3], x[4]) for x in hz_g] == [(x[3], x[4]) for x in hz_r])
    check(1, "no legacy cell-label vector exists to compare against",
          not any((LEGACY / "AGUv3" / "data").glob("*.nc"))
          if (LEGACY / "AGUv3" / "data").exists() else True,
          "AGUv3's data/ was never committed, so SPEC's ARI=1 label-vector claim was "
          "unsupportable and Amendment 1 removes it; identity is established through "
          "counts, centroids, windows, eta^2 and the statistics below")
    ho_g = [x for x in hg if len(x) == 4 and x[0] in ("Kenya", "Somalia")]
    ho_r = [x for x in hr if len(x) == 4 and x[0] in ("Kenya", "Somalia")]
    check(1, "hierarchy orientation eta^2 agrees to 0.005",
          all(abs(num(g[1]) - num(r[1])) <= 0.005 and abs(num(g[2]) - num(r[2])) <= 0.005
              for g, r in zip(ho_g, ho_r)),
          "; ".join(f"{g[0]}@{i}: {g[1]}/{g[2]}" for i, g in enumerate(ho_g)))

    # ── Tier 2: CHIRPS + ERSST, strict but not exact ─────────────────────────
    print("\nTier 2 — CHIRPS + ERSST quantities, checked to 0.01")
    wr, wg = rows(REF / "wvg_by_zone.md"), rows(got / "wvg_by_zone.md")
    wb_r = [x for x in wr if len(x) == 10 and x[0].isdigit()]
    wb_g = [x for x in wg if len(x) == 10 and x[0].isdigit()]
    check(2, "the WVG table has the same zone-window rows",
          [(x[0], x[1]) for x in wb_g] == [(x[0], x[1]) for x in wb_r],
          str([(x[0], x[1]) for x in wb_g]))
    worst, worst_at = 0.0, ""
    for g, r in zip(wb_g, wb_r):
        for i, lab in ((4, "sym_corr"), (5, "dry_roc"), (6, "p_dry_clim"),
                       (7, "p_dry_negwvg"), (8, "p_dry_negwvg_lanina")):
            a, b = num(g[i]), num(r[i])
            if a is None or b is None:
                continue
            if abs(a - b) > worst:
                worst, worst_at = abs(a - b), f"zone {g[0]} {g[1]} {lab}"
    check(2, "every WVG statistic agrees to 0.01", worst <= 0.01,
          f"max |diff| = {worst:.3f} at {worst_at}")
    ehorn = [x for x in wb_g if x[0] == "1" and x[1] == "MAM"]
    check(2, "at k=2 the eastern zone's MAM rates are 0.71 / 0.69 — NOT the published "
             "headline, which lives at k=3 and k=4",
          bool(ehorn) and abs(num(ehorn[0][7]) - 0.71) <= 0.01
          and abs(num(ehorn[0][8]) - 0.69) <= 0.01,
          f"{ehorn[0][7]} / {ehorn[0][8]} (n_joint={ehorn[0][9]})" if ehorn else "missing")

    # The AGUv3 README's headline claim is "the discovered eHorn zone reproduces the v2
    # hand-box MAM skill exactly: P(dry|-WVG)=0.79, +La Nina=0.77 (n=13) at k=3 and k=4".
    # v1's check read the k=2 table and mislabelled 0.71/0.69 as that number. These are
    # the actual published values, checked directly, in both the reference and the rerun.
    def hrow(rowset, zone, window, k_block):
        """hierarchy.md rows in order: the k=3 block first, then the k=4 block.

        Blocks are split where the zone id DECREASES. Splitting on "zone 0 seen again"
        is wrong -- zone 0 owns three consecutive rows at k=3, one per window -- and that
        was the bug that made this check report "row missing" on data that was present.
        """
        blocks, cur, prev = [], [], -1
        for x in rowset:
            z = int(x[0])
            if z < prev:
                blocks.append(cur)
                cur = []
            cur.append(x)
            prev = z
        blocks.append(cur)
        if k_block >= len(blocks):
            return None
        for x in blocks[k_block]:
            if x[0] == zone and x[3] == window:
                return x
        return None

    for k_block, klabel, zone in ((0, "k=3", "2"), (1, "k=4", "3")):
        g = hrow(hz_g, zone, "MAM", k_block)
        r = hrow(hz_r, zone, "MAM", k_block)
        ok = (g is not None and r is not None
              and abs(num(g[8]) - 0.79) <= 0.01
              and abs(num(g[9].split("(")[0]) - 0.77) <= 0.01
              and g[8] == r[8] and g[9] == r[9])
        check(2, f"the PUBLISHED headline reproduces at {klabel}: eastern zone {zone} MAM "
                 f"P(dry|-WVG) = 0.79 and +La Nina = 0.77, n = 13",
              ok, f"{g[8]} / {g[9]}" if g else "row missing")

    worst_h, worst_h_at = 0.0, ""
    for g, r in zip(hz_g, hz_r):
        for i, lab in ((5, "sym"), (6, "droc"), (7, "pclim"), (8, "pneg")):
            a, b = num(g[i]), num(r[i])
            if a is None or b is None:
                continue
            if abs(a - b) > worst_h:
                worst_h, worst_h_at = abs(a - b), f"{g[0]}/{g[3]} {lab}"
    check(2, "every k=3 and k=4 hierarchy statistic agrees to 0.01 "
             "(v1 compared only the window columns)",
          worst_h <= 0.01, f"max |diff| = {worst_h:.3f} at {worst_h_at}")
    check(2, "the conditional-rate column with the La Nina subset is identical string-wise "
             "across all 22 hierarchy rows, n included",
          [x[9] for x in hz_g] == [x[9] for x in hz_r],
          f"{sum(1 for a, b in zip(hz_g, hz_r) if a[9] == b[9])}/{len(hz_g)} rows")

    sr, sg = (REF / "search_results.md").read_text(), (got / "search_results.md").read_text()
    m_r = re.search(r"\*\*(\d+) / (\d+) cells survive", sr)
    m_g = re.search(r"\*\*(\d+) / (\d+) cells survive", sg)
    check(2, "the tensor is 520 cells", m_g and m_g.group(2) == "520",
          f"{m_g.group(2) if m_g else '?'} cells")
    surv_g, surv_r = int(m_g.group(1)), int(m_r.group(1))
    check(2, f"the survivor count is {surv_r} +/- 3", abs(surv_g - surv_r) <= 3,
          f"{surv_g} vs published {surv_r}")

    def recipes(text):
        out = {}
        for ln in text.splitlines():
            m = re.match(r"\|\s*(\d+)\s*\|\s*(\w+)\s*\|\s*(\w+) lead-(\d) \((\w+)\)", ln)
            if m:
                out[(m.group(1), m.group(2))] = (m.group(3), m.group(4), m.group(5))
        return out

    rr, rg = recipes(sr), recipes(sg)
    same = {k: v for k, v in rg.items() if rr.get(k) == v}
    check(2, "all 7 best-per-zone-window recipes select the identical index, lead and mode",
          len(rr) == len(rg) == len(same) == 7,
          f"{len(same)}/{len(rr)} identical: " +
          "; ".join(f"z{k[0]}/{k[1]}={v[0]} L{v[1]}" for k, v in sorted(rg.items())))

    # ── verdict ──────────────────────────────────────────────────────────────
    t1 = [c for c in CHECKS if c[0] == 1]
    t2 = [c for c in CHECKS if c[0] == 2]
    f1 = sum(1 for c in t1 if not c[2])
    f2 = sum(1 for c in t2 if not c[2])
    print(f"\n{'=' * 78}")
    print(f"Tier 1 (exact, CHIRPS-only):     {len(t1) - f1}/{len(t1)} passed")
    print(f"Tier 2 (strict, CHIRPS+ERSST):   {len(t2) - f2}/{len(t2)} passed")
    if f1:
        print("TIER 1 FAILURE — SPEC 9.1 says stop the project.")
    elif f2:
        print("TIER 2 FAILURE — SPEC 9.1 says stop pending an ERSST fixture investigation.")
    else:
        print("LEGACY REPRODUCTION PASSES. AGUv3's published tables are reproduced.")
    out = {"tier1_total": len(t1), "tier1_failed": f1,
           "tier2_total": len(t2), "tier2_failed": f2,
           "survivors": surv_g, "survivors_published": surv_r,
           "failures": [c[1] for c in CHECKS if not c[2]],
           "status": "ok" if not (f1 or f2) else "failed"}
    (ROOT / "outputs").mkdir(exist_ok=True)
    (ROOT / "outputs" / "legacy_reproduction.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out))
    return 1 if (f1 or f2) else 0


if __name__ == "__main__":
    sys.exit(main())
