"""decide.py — SPEC 10.6 and SPEC 12/14: turn the null sweep into verdicts.

Reads outputs/atlas_real.json (the real arms) and outputs/atlas_null.jsonl (the 200
paired replicates), and applies the decision rules exactly as SPEC fixed them BEFORE any
of these numbers existed:

  primary   the complete discovered-window atlas under `zones-specific` is USEFUL if and
            only if rpss_atlas > 0 AND p <= 0.05, one-sided, p = (1 + #{null >= real})/201

            The null is SPEC Amendment 1's complete-season target permutation. It prices
            predictor and lead selection -- the one skill-selected axis -- and by design
            does NOT price zone discovery, which consults neither SST nor any score and
            whose every output is reported. Any statement of the p-value must carry that
            scope.

  paired    zones-specific vs pooled and vs zones-shared, differenced replicate by
            replicate because every arm sees the same 200 draws

  families  each MAM family against its own null, subject to SPEC 12.1's coverage rule:
            below 0.5 coverage a family is reported but NOT adjudicated

Writes outputs/decisions.json.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
FAMILIES = ("atlas/all-windows", "MAM/all", "MAM/lanina", "MAM/neg_wvg")
PRIMARY_ARM = "zones-specific"
ALPHA = 0.05
COVERAGE_BAR = 0.5


def load_null():
    """{(arm, family): {replicate: rpss}} plus the per-replicate coverage."""
    vals = defaultdict(dict)
    cov = defaultdict(dict)
    errs = 0
    for ln in (OUT / "atlas_null_v2.jsonl").read_text().splitlines():
        if not ln.strip():
            continue
        d = json.loads(ln)
        if "error" in d:
            errs += 1
            continue
        for fam, v in d["families"].items():
            r = v.get("rpss")
            if r is None or not np.isfinite(r):
                continue
            vals[(d["arm"], fam)][d["replicate"]] = float(r)
            cov[(d["arm"], fam)][d["replicate"]] = float(v.get("coverage", np.nan))
    return vals, cov, errs


def pval(real, null):
    null = np.asarray(null, dtype=float)
    return float((1 + int(np.sum(null >= real))) / (len(null) + 1))


def main():
    real_rows = json.loads((OUT / "atlas_real.json").read_text())
    real = {}
    for r in real_rows:
        if r["protocol"] != "walkforward" or r["leak"] or r["weight_rule"] != "equal":
            continue
        for fam, v in r["families"].items():
            real[(r["arm"], fam)] = v
    nulls, ncov, errs = load_null()

    out = {"errors_in_null": errs, "families": {}, "paired": {}, "primary": None}
    print(f"null replicates with errors: {errs}\n")

    # ── the primary claim ────────────────────────────────────────────────────
    key = (PRIMARY_ARM, "atlas/all-windows")
    r_real = real[key]["rpss"]
    nd = nulls[key]
    nv = [nd[k] for k in sorted(nd)]
    p = pval(r_real, nv)
    useful = bool(r_real > 0 and p <= ALPHA)
    out["primary"] = {
        "arm": PRIMARY_ARM, "family": "atlas/all-windows", "protocol": "walkforward",
        "rpss_atlas": round(r_real, 6), "coverage": round(real[key]["coverage"], 4),
        "n_null": len(nv), "null_mean": round(float(np.mean(nv)), 6),
        "null_sd": round(float(np.std(nv)), 6),
        "null_p95": round(float(np.percentile(nv, 95)), 6),
        "null_max": round(float(np.max(nv)), 6),
        "p_value": round(p, 5),
        "condition_positive": bool(r_real > 0), "condition_p": bool(p <= ALPHA),
        "verdict": "USEFUL" if useful else "NOT USEFUL",
    }
    print("PRIMARY CLAIM (SPEC 10.6)")
    print(f"  rpss_atlas        {r_real:+.4f}")
    print(f"  null mean +/- sd  {np.mean(nv):+.4f} +/- {np.std(nv):.4f}   (n={len(nv)})")
    print(f"  null p95 / max    {np.percentile(nv, 95):+.4f} / {np.max(nv):+.4f}")
    print(f"  one-sided p       {p:.4f}")
    print(f"  rpss > 0 ?        {r_real > 0}")
    print(f"  p <= 0.05 ?       {p <= ALPHA}")
    print(f"  VERDICT           {out['primary']['verdict']}\n")

    # ── every family, every arm ──────────────────────────────────────────────
    print("ALL FAMILIES AND ARMS")
    print(f"  {'arm':16s} {'family':18s} {'real':>9s} {'cov':>6s} {'null mean':>10s} "
          f"{'p':>7s}  adjudicated")
    for arm in ("climatology", "pooled", "zones-shared", "zones-specific"):
        for fam in FAMILIES:
            if (arm, fam) not in real:
                continue
            rr = real[(arm, fam)]["rpss"]
            cc = real[(arm, fam)]["coverage"]
            nd = nulls.get((arm, fam), {})
            nv = [nd[k] for k in sorted(nd)]
            pv = pval(rr, nv) if nv else None
            adj = cc >= COVERAGE_BAR
            rec = {"rpss": None if rr is None else round(rr, 6),
                   "coverage": round(cc, 4), "n_null": len(nv),
                   "null_mean": round(float(np.mean(nv)), 6) if nv else None,
                   "p_value": None if pv is None else round(pv, 5),
                   "adjudicated": bool(adj),
                   "clears": bool(adj and pv is not None and pv <= ALPHA and rr > 0)}
            if not adj:
                rec["note"] = f"coverage {cc:.2f} < {COVERAGE_BAR}: UNAVAILABLE for a headline claim"
            out["families"][f"{arm}|{fam}"] = rec
            print(f"  {arm:16s} {fam:18s} {rr:+9.4f} {cc:6.2f} "
                  f"{(np.mean(nv) if nv else float('nan')):+10.4f} "
                  f"{(pv if pv is not None else float('nan')):7.4f}  "
                  f"{'yes' if adj else 'NO (coverage)'}")

    # ── paired arm comparisons ───────────────────────────────────────────────
    print("\nPAIRED ARM COMPARISONS (same 200 draws, differenced replicate by replicate)")
    for other in ("pooled", "zones-shared"):
        a = nulls.get((PRIMARY_ARM, "atlas/all-windows"), {})
        b = nulls.get((other, "atlas/all-windows"), {})
        shared = sorted(set(a) & set(b))
        if not shared:
            print(f"  {other}: no shared replicates")
            continue
        d_null = np.array([a[k] - b[k] for k in shared])
        d_real = real[(PRIMARY_ARM, "atlas/all-windows")]["rpss"] - \
            real[(other, "atlas/all-windows")]["rpss"]
        pv = pval(d_real, d_null)
        out["paired"][f"zones-specific_minus_{other}"] = {
            "delta_real": round(float(d_real), 6), "n_pairs": len(shared),
            "delta_null_mean": round(float(np.mean(d_null)), 6),
            "delta_null_sd": round(float(np.std(d_null)), 6),
            "p_value": round(pv, 5),
            "clears": bool(d_real > 0 and pv <= ALPHA)}
        print(f"  zones-specific - {other:14s} delta = {d_real:+.4f}  "
              f"null {np.mean(d_null):+.4f} +/- {np.std(d_null):.4f}  "
              f"p = {pv:.4f}  ({len(shared)} pairs)")

    # Amendment 1 3.4: the v1 field permutation, reported beside the primary null.
    sens = OUT / "sensitivity_field_perm.jsonl"
    if sens.exists() and sens.stat().st_size:
        sv = []
        wraps = set()
        for ln in sens.read_text().splitlines():
            if not ln.strip():
                continue
            d = json.loads(ln)
            if "error" in d:
                continue
            v = d["families"]["atlas/all-windows"].get("rpss")
            if v is not None and np.isfinite(v):
                sv.append(float(v))
            wraps.update(d.get("wrapping_windows_present", []))
        if sv:
            out["sensitivity_field_perm"] = {
                "n": len(sv), "mean": round(float(np.mean(sv)), 6),
                "sd": round(float(np.std(sv)), 6),
                "p95": round(float(np.percentile(sv, 95)), 6),
                "p_value_vs_real": round(pval(r_real, sv), 5),
                "wrapping_windows_present": sorted(wraps),
                "caveat": "calendar-year field permutation splices wrapping seasons "
                          "across donor years; adjudicates nothing"}
            print(f"\nSENSITIVITY (v1 field permutation, adjudicates nothing): "
                  f"n={len(sv)} mean={np.mean(sv):+.4f} p={pval(r_real, sv):.4f} "
                  f"wrapping windows seen: {sorted(wraps) or 'none'}")

    out["null_scope"] = ("prices predictor and lead selection; does not price zone "
                         "discovery, which is not skill-selected (Amendment 1 3.2)")
    (OUT / "decisions.json").write_text(json.dumps(out, indent=2) + "\n")
    print(f"\nwrote {OUT / 'decisions.json'}")
    print(json.dumps({"verdict": out["primary"]["verdict"],
                      "rpss_atlas": out["primary"]["rpss_atlas"],
                      "p_value": out["primary"]["p_value"],
                      "n_null": out["primary"]["n_null"], "status": "ok"}))


if __name__ == "__main__":
    sys.exit(main())
