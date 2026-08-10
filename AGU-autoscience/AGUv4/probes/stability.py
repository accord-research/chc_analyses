"""stability.py — SPEC 11 in full, plus the figures the report needs.

Runs the real walk-forward atlas once, keeps the six partitions, and computes every
stability metric SPEC 11 lists: the matching-free ones (6x6 ARI, per-cell switch map),
the track-level ones (centroid, boundary, windows, predictor identity and region, lead),
the two fold-level ones (orphan area, absence rate), and the H1 test.

Also draws the zone maps, the annual cycles, the ARI hierarchy and the switch map, and
computes the descriptive expert-overlap statistics.

Writes outputs/stability.json and outputs/figures/*.png.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "harness"))

import fields as F                 # noqa: E402
import pipeline as P               # noqa: E402
import pipeline_v2 as P2           # noqa: E402
import matching as M               # noqa: E402

OUT = ROOT / "outputs"
FIG = OUT / "figures"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# SPEC 11: descriptive only, never ground truth.
EXPERT = {"AGUv2 eastern-Horn box": (-4.5, 8.5, 38.0, 50.5),
          "reviewer south-central Somalia": (1.0, 6.0, 42.0, 48.0)}
COUNTRY = {"Kenya": (-4.7, 5.0, 33.9, 41.9), "Somalia": (-1.7, 12.0, 41.0, 51.4)}


def eta2(lab, coord):
    gm = coord.mean()
    ssb = 0.0
    for z in np.unique(lab):
        c = coord[lab == z]
        if len(c):
            ssb += len(c) * (c.mean() - gm) ** 2
    return float(ssb / ((coord - gm) ** 2).sum())


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    fld, _ = P.get_state()
    n_cell = fld.monthly.shape[0]

    print("running the real walk-forward atlas and keeping the partitions ...", flush=True)
    ff, folds, parts = P2.run_atlas_v2()
    per_zone = []
    for fi, fold in enumerate(ff):
        for fc in fold:
            r = (1 - fc.rps_f.sum() / fc.rps_c.sum()) if fc.rps_c.sum() > 0 else None
            per_zone.append(dict(fold=fi, zone=int(fc.zone), window=fc.window,
                                 discovered=bool(fc.discovered), index=fc.index,
                                 lead=int(fc.lead), n_test=int(len(fc.rps_f)),
                                 rpss=None if r is None else float(r)))

    # ── matching-free metrics ────────────────────────────────────────────────
    ari = M.pairwise_ari(parts, n_cell)
    off = ari[~np.eye(len(parts), dtype=bool)]
    sw, ref_lab = M.switch_map(parts, n_cell)

    # ── tracks, orphans, absences ────────────────────────────────────────────
    tracks, orphans, absences = M.build_tracks(parts, n_cell)
    oa, ar = M.fold_orphan_area(parts, tracks, orphans)

    rows = []
    for z, tr in sorted(tracks.items()):
        agree = M.track_agreement(tr, n_cell)
        clat, clon = M.track_centroid_variation(tr, fld.lats, fld.lons)
        rec = M.track_recipe_agreement(tr, per_zone)
        sk, nsc = M.track_skill(tr, ff)
        rows.append(dict(track=int(z), n_folds=tr.n_folds,
                         folds=sorted(tr.member),
                         agreement=None if not np.isfinite(agree) else round(agree, 4),
                         centroid_sd_lat=None if not np.isfinite(clat) else round(clat, 4),
                         centroid_sd_lon=None if not np.isfinite(clon) else round(clon, 4),
                         boundary_variation=round(M.track_boundary_variation(tr), 4)
                         if np.isfinite(M.track_boundary_variation(tr)) else None,
                         **{k: (None if not np.isfinite(v) else round(v, 4))
                            for k, v in rec.items()},
                         pooled_rpss=None if not np.isfinite(sk) else round(sk, 4),
                         n_scored=int(nsc),
                         enters_h1=bool(tr.n_folds >= M.MIN_FOLDS_FOR_H1
                                        and nsc >= M.MIN_SCORED),
                         status=("ok" if nsc >= M.MIN_SCORED
                                 else f"unscored (n={nsc} < {M.MIN_SCORED})")))

    elig = [r for r in rows if r["enters_h1"]]
    h1 = M.h1_test([r["agreement"] for r in elig], [r["pooled_rpss"] for r in elig])
    max_orphan = max(oa.values()) if oa else 0.0
    h1["orphan_area_max"] = round(float(max_orphan), 4)
    h1["reliable"] = bool(max_orphan <= M.ORPHAN_UNRELIABLE)
    h1["excluded_tracks"] = len(rows) - len(elig)

    # ── descriptive expert overlap (SPEC 11: determines nothing) ─────────────
    ref_part = parts[-1]
    overlap = []
    lat, lon = fld.lats[ref_part.cell_index], fld.lons[ref_part.cell_index]
    for name, (s, n, w, e) in EXPERT.items():
        box = (lat >= s) & (lat <= n) & (lon >= w) & (lon <= e)
        for z in range(ref_part.k):
            m = ref_part.labels == z
            inter = int(np.sum(m & box))
            overlap.append(dict(expert=name, zone=int(z),
                                frac_of_box_in_zone=round(inter / max(box.sum(), 1), 4),
                                frac_of_zone_in_box=round(inter / max(m.sum(), 1), 4)))
    orient = []
    for cname, (s, n, w, e) in COUNTRY.items():
        m = (lat >= s) & (lat <= n) & (lon >= w) & (lon <= e)
        if m.sum() > 1:
            orient.append(dict(country=cname,
                               eta2_lon=round(eta2(ref_part.labels[m], lon[m]), 3),
                               eta2_lat=round(eta2(ref_part.labels[m], lat[m]), 3)))

    # ── figures ──────────────────────────────────────────────────────────────
    _fig_zone_maps(fld, parts)
    _fig_cycles(fld, parts)
    _fig_hierarchy(parts)
    _fig_switch(fld, sw)
    _fig_ari(ari)

    out = {
        "pairwise_ari": [[round(float(v), 4) for v in r] for r in ari],
        "mean_offdiag_ari": round(float(np.mean(off)), 4),
        "min_offdiag_ari": round(float(np.min(off)), 4),
        "k_per_fold": [int(p.k) for p in parts],
        "ari_curve_per_fold": [{int(k): round(v, 4) for k, v in p.ari_curve.items()}
                               for p in parts],
        "silhouette_per_fold": [{int(k): round(v, 4) for k, v in p.silhouette.items()}
                                for p in parts],
        "orphan_area": {int(k): round(float(v), 4) for k, v in oa.items()},
        "absence_rate": {int(k): round(float(v), 4) for k, v in ar.items()},
        "orphans": orphans,
        "tracks": rows,
        "h1": h1,
        "switch_map_mean": round(float(np.nanmean(sw)), 4),
        "switch_map_frac_ever": round(float(np.nanmean(sw > 0)), 4),
        "expert_overlap": overlap,
        "orientation_eta2": orient,
        "per_zone_window": per_zone,
    }
    (OUT / "stability.json").write_text(json.dumps(out, indent=2) + "\n")

    print(f"\nmean off-diagonal ARI = {out['mean_offdiag_ari']:.4f} "
          f"(min {out['min_offdiag_ari']:.4f})")
    print(f"k per fold = {out['k_per_fold']}")
    print(f"orphan area per fold = {out['orphan_area']}")
    print(f"absence rate per fold = {out['absence_rate']}")
    print(f"tracks = {len(rows)}, entering H1 = {len(elig)}")
    for r in rows:
        print(f"  track {r['track']}: {r['n_folds']}/6 folds, agreement="
              f"{r['agreement']}, pooled RPSS={r['pooled_rpss']}, n={r['n_scored']}, "
              f"{r['status']}")
    print(f"H1: {h1}")
    print(f"\nwrote {OUT / 'stability.json'} and {FIG}")
    print(json.dumps({"tracks": len(rows), "h1_n": h1["n"], "h1_p": h1["p"],
                      "mean_ari": out["mean_offdiag_ari"], "status": "ok"}))


# ── plotting ──────────────────────────────────────────────────────────────────
def _fig_zone_maps(fld, parts):
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    n = len(parts)
    fig, axes = plt.subplots(2, 3, figsize=(15, 9),
                             subplot_kw={"projection": ccrs.PlateCarree()})
    for i, (ax, p) in enumerate(zip(axes.ravel(), parts)):
        m = F.to_map(fld, p.cell_index, p.labels.astype(float))
        ax.pcolormesh(fld.lon_axis, fld.lat_axis, m, cmap="viridis",
                      vmin=-0.5, vmax=max(p.k - 0.5, 0.5),
                      transform=ccrs.PlateCarree())
        ax.add_feature(cfeature.BORDERS, lw=0.6)
        ax.add_feature(cfeature.COASTLINE, lw=0.6)
        ax.axvline(38, color="r", ls=":", lw=0.8)
        ax.axhline(7, color="r", ls=":", lw=0.8)
        ax.set_title(f"fold {i}  (train -{int(1981 + 20 + i * 3.6)}, k={p.k})", fontsize=10)
    fig.suptitle("Discovered forecast zones per outer fold "
                 "(red: the expert ~38E / ~7N splits, descriptive only)")
    fig.tight_layout()
    fig.savefig(FIG / "zone_maps_by_fold.png", dpi=140)
    plt.close(fig)


def _fig_cycles(fld, parts):
    fig, axes = plt.subplots(2, 3, figsize=(15, 7), sharex=True)
    for i, (ax, p) in enumerate(zip(axes.ravel(), parts)):
        cmap = plt.cm.viridis(np.linspace(0, 0.85, p.k))
        for z in range(p.k):
            wins = " + ".join(lab for lab, _ in p.windows[z])
            ax.plot(range(1, 13), p.cycles[z], "-o", ms=3, color=cmap[z],
                    label=f"z{z} ({wins})")
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels([m[0] for m in MONTHS])
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7)
        ax.set_title(f"fold {i} (k={p.k})", fontsize=10)
        if i % 3 == 0:
            ax.set_ylabel("mm/month")
    fig.suptitle("Annual cycle of each discovered zone, per fold (training years only)")
    fig.tight_layout()
    fig.savefig(FIG / "annual_cycles_by_fold.png", dpi=140)
    plt.close(fig)


def _fig_hierarchy(parts):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for i, p in enumerate(parts):
        ks = sorted(p.ari_curve)
        ax.errorbar(ks, [p.ari_curve[k] for k in ks],
                    yerr=[p.ari_sd[k] for k in ks], marker="o", ms=4, lw=1,
                    alpha=0.8, label=f"fold {i} (k={p.k})")
    ax.axhline(0.90, color="r", ls="--", lw=1, label="tau = 0.90")
    ax.set_xlabel("k")
    ax.set_ylabel("mean year-bootstrap ARI")
    ax.set_title("The complete k = 2..8 hierarchy, every fold (SPEC 4)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(FIG / "k_hierarchy.png", dpi=140)
    plt.close(fig)


def _fig_switch(fld, sw):
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    fig = plt.figure(figsize=(7.5, 6.5))
    ax = plt.axes(projection=ccrs.PlateCarree())
    m = sw.reshape(fld.shape)
    pc = ax.pcolormesh(fld.lon_axis, fld.lat_axis, m, cmap="magma", vmin=0, vmax=1,
                       transform=ccrs.PlateCarree())
    fig.colorbar(pc, ax=ax, label="fraction of fold pairs disagreeing")
    ax.add_feature(cfeature.BORDERS, lw=0.6)
    ax.add_feature(cfeature.COASTLINE, lw=0.6)
    ax.set_title("Per-cell zone-switch frequency across the 15 fold pairs")
    fig.tight_layout()
    fig.savefig(FIG / "switch_map.png", dpi=140)
    plt.close(fig)


def _fig_ari(ari):
    fig, ax = plt.subplots(figsize=(5.5, 4.6))
    im = ax.imshow(ari, vmin=0, vmax=1, cmap="viridis")
    for a in range(ari.shape[0]):
        for b in range(ari.shape[1]):
            ax.text(b, a, f"{ari[a, b]:.2f}", ha="center", va="center",
                    color="w" if ari[a, b] < 0.6 else "k", fontsize=8)
    ax.set_xticks(range(ari.shape[0]))
    ax.set_yticks(range(ari.shape[0]))
    ax.set_xlabel("fold")
    ax.set_ylabel("fold")
    ax.set_title("Pairwise partition agreement (ARI), matching-free")
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(FIG / "ari_matrix.png", dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    main()
