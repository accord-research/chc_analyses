"""
report_figures.py — synthesis figures of the main conclusions, for the notebook report.

  fig_taxonomy_scatter.png : the criterion, visualized. x = how well GCMs forecast the driver
      (corr forecast vs observed SST index), y = is there a predictable SST->rainfall link at all
      (perfect-prognosis ceiling), colour = actual hybrid skill. The three cases fall in three
      regions of the plane.
  fig_ond_mme.png          : real dynamical MME skill (GROC) for the OND short rains across the
      three countries — no skill for Nigeria, real skill for East Africa.
"""
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
TAB = ROOT / "outputs" / "tables"
FIG = ROOT / "outputs" / "figures"

COUNTRIES = [("nigeria", "Nigeria", ""), ("ethiopia", "Ethiopia", "_ethiopia"),
             ("kenya", "Kenya", "_kenya")]
CMARK = {"nigeria": "o", "ethiopia": "s", "kenya": "^"}


def load_hybrid():
    rows = []
    for key, label, sfx in COUNTRIES:
        p = TAB / f"hybrid_forecast{sfx}.csv"
        if not p.exists():
            continue
        for r in csv.DictReader(open(p)):
            rows.append(dict(country=label, ckey=key, target=r["target"], index=r["index"],
                             fcst=float(r["sst_fcst_skill"]),
                             lead=float(r.get("lead_predictability", "nan")),
                             ceiling=float(r["ceiling_concurrent"]),
                             hybrid=float(r["hybrid"])))
    return rows


def taxonomy_scatter(rows):
    fig, ax = plt.subplots(figsize=(10, 7))
    # region shading (y = LEAD predictability now, so thresholds are lower than the concurrent ref)
    ax.axhspan(-0.35, 0.15, color="#bbbbbb", alpha=0.25, zorder=0)                 # weak lead link
    ax.fill_between([0.0, 0.55], 0.15, 0.75, color="#f2b8b8", alpha=0.30, zorder=0)  # link but driver hard to forecast
    ax.fill_between([0.55, 1.0], 0.15, 0.75, color="#b8e0b8", alpha=0.35, zorder=0)  # link + driver forecastable

    sc = None
    for r in rows:
        y = r["lead"] if np.isfinite(r["lead"]) else r["ceiling"]
        sc = ax.scatter(r["fcst"], y, c=[r["hybrid"]], cmap="RdYlGn",
                        vmin=-0.4, vmax=0.8, s=260, marker=CMARK[r["ckey"]],
                        edgecolor="black", linewidth=1.1, zorder=3)
        ax.annotate(f"{r['country'][:3]} {r['target']}\n({r['index']})",
                    (r["fcst"], y), fontsize=7.5, ha="center",
                    va="bottom", xytext=(0, 10), textcoords="offset points")
    cb = fig.colorbar(sc, ax=ax); cb.set_label("achieved hybrid skill (LOYO correlation, forecast SST→rain)")

    ax.text(0.27, 0.66, "lead link present,\nbut driver hard for GCMs to forecast\n→ dynamical skill limited here",
            fontsize=9, ha="center", color="#7a1f1f", weight="bold")
    ax.text(0.78, 0.66, "lead link present AND\ndriver GCMs forecast well\n→ dynamical skill realized",
            fontsize=9, ha="center", color="#1f5f1f", weight="bold")
    ax.text(0.55, -0.28, "weak lead predictability from SST: structurally low-skill season\n"
                        "(e.g. E. African MAM long rains — controls less SST-mediated: Walker/Congo winds, MJO)",
            fontsize=8.5, ha="center", color="#444", weight="bold")
    ax.axhline(0, color="k", lw=0.6, ls=":")
    ax.axvline(0.55, color="k", lw=0.8, ls="--", alpha=0.6)
    ax.set_xlim(0.15, 1.0); ax.set_ylim(-0.38, 0.78)
    ax.set_xlabel("How well GCMs forecast the driver  →  corr(forecast SST index, observed SST index)")
    ax.set_ylabel("LEAD predictability from observed SST\n(pre-season SST → rainfall, LOYO — a reference, not a theoretical limit)")
    ax.set_title("A diagnostic of where SST-based seasonal skill is realized (this configuration)\n"
                 "3 countries × 3 seasons, same harness — marker=country, colour=achieved hybrid skill.\n"
                 "y = LEAD predictability (not the concurrent reference). Best-of-search over n≈24–33 —\n"
                 "read as hypotheses; only E. African OND clearly survives multiplicity (see docs/14).",
                 fontsize=10, weight="bold")
    # country legend
    from matplotlib.lines import Line2D
    handles = [Line2D([0], [0], marker=CMARK[k], color="w", markerfacecolor="gray",
                      markeredgecolor="k", markersize=11, label=lab) for k, lab, _ in COUNTRIES]
    ax.legend(handles=handles, loc="lower left", fontsize=9, title="country")
    fig.tight_layout(); fig.savefig(FIG / "fig_taxonomy_scatter.png", dpi=150); plt.close(fig)
    print("wrote fig_taxonomy_scatter.png")


def ond_mme_bars():
    """OND short-rains real MME GROC across the three countries (best OND target × domain)."""
    data = []
    for key, label, sfx in COUNTRIES:
        p = TAB / f"mme_domain_search{sfx}.csv"
        best, besttgt = np.nan, "OND"
        if p.exists():
            for r in csv.DictReader(open(p)):
                if "OND" in r["target"]:
                    g = float(r["groc"])
                    if best != best or g > best:
                        best, besttgt = g, r["target"].replace(" (short rains)", "")
        data.append((label, besttgt, best))
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#E15759", "#59A14F", "#4E79A7"]
    bars = ax.bar([d[0] for d in data], [d[2] for d in data], color=colors, edgecolor="black")
    ax.axhline(0.5, color="red", ls="--", lw=1.2, label="no-skill line (GROC = 0.5)")
    for b, d in zip(bars, data):
        ax.text(b.get_x() + b.get_width() / 2, d[2] + 0.005, f"{d[2]:.2f}\n{d[1]}",
                ha="center", fontsize=8)
    ax.set_ylim(0.4, 0.78); ax.set_ylabel("real NMME MME skill (best-domain GROC, LOYO)")
    ax.set_title("Real ensemble skill for the OND short rains, by region (this ensemble & predictand)\n"
                 "Marginal for Nigeria; higher for East Africa, where the IOD link is strong and forecastable.\n"
                 "n≈24 — differences near the 0.5 line are within sampling noise (see docs/14).", fontsize=10)
    ax.legend(fontsize=9)
    fig.tight_layout(); fig.savefig(FIG / "fig_ond_mme.png", dpi=150); plt.close(fig)
    print("wrote fig_ond_mme.png", [(d[0], round(d[2], 3)) for d in data])


def replot_domain_heatmap(area="nigeria", sfx=""):
    """Regenerate the domain heatmap from the existing CSV with an honest (de-saturated) scale
    and a noise-floor caption — without re-running the heavy MME search."""
    p = TAB / f"mme_domain_search{sfx}.csv"
    if not p.exists():
        return
    rows = list(csv.DictReader(open(p)))
    targets = list(dict.fromkeys(r["target"] for r in rows))
    doms = list(dict.fromkeys(r["domain"] for r in rows))
    M = np.full((len(targets), len(doms)), np.nan)
    mos = {}
    for r in rows:
        i, j = targets.index(r["target"]), doms.index(r["domain"])
        M[i, j] = float(r["groc"])
        if r["domain"] == "precip_mos":
            mos[r["target"]] = float(r["groc"])
    fig, ax = plt.subplots(figsize=(9, 4.6))
    im = ax.imshow(M, cmap="RdBu_r", vmin=0.30, vmax=0.75, aspect="auto")
    ax.set_xticks(range(len(doms))); ax.set_xticklabels(doms, rotation=30, ha="right")
    ax.set_yticks(range(len(targets))); ax.set_yticklabels(targets)
    for i in range(len(targets)):
        for j in range(len(doms)):
            if np.isfinite(M[i, j]):
                ax.text(j, i, f"{M[i,j]:.2f}", ha="center", va="center", fontsize=8,
                        color="white" if M[i, j] > 0.68 else "black")
    fig.colorbar(im, label="MME GROC (0.5 = no skill)")
    ax.set_title(f"MME skill by SST predictor domain — {area.title()} (CCA, LOYO)\n"
                 "Spread across domains is ~0.02–0.05 GROC (within the ~0.1 noise floor); the best\n"
                 "cell is usually NOT robust, and SST-CCA barely beats the precip-MOS baseline.", fontsize=9.5)
    fig.tight_layout(); fig.savefig(FIG / f"mme_domain_search{sfx}.png", dpi=150); plt.close(fig)
    print(f"replotted mme_domain_search{sfx}.png (precip-MOS vs best:",
          {t: (round(mos.get(t, np.nan), 3), round(np.nanmax(M[targets.index(t)]), 3)) for t in targets}, ")")


def replot_method_heatmap(area="nigeria", sfx=""):
    p = TAB / f"mme_method_search{sfx}.csv"
    if not p.exists():
        return
    rows = list(csv.DictReader(open(p)))
    targets = list(dict.fromkeys(r["target"] for r in rows))
    methods = list(dict.fromkeys(r["method"] for r in rows))
    G = np.full((len(targets), len(methods)), np.nan)
    R = np.full((len(targets), len(methods)), np.nan)
    for r in rows:
        i, j = targets.index(r["target"]), methods.index(r["method"])
        if r["metric"] == "generalized_roc":
            G[i, j] = float(r["mean"])
        elif r["metric"] == "rpss":
            R[i, j] = float(r["mean"])
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    im = ax.imshow(G, cmap="RdBu_r", vmin=0.30, vmax=0.75, aspect="auto")
    ax.set_xticks(range(len(methods))); ax.set_xticklabels(methods, rotation=30, ha="right")
    ax.set_yticks(range(len(targets))); ax.set_yticklabels(targets)
    for i in range(len(targets)):
        for j in range(len(methods)):
            if np.isfinite(G[i, j]):
                ax.text(j, i, f"{G[i,j]:.2f}\n({R[i,j]:+.2f})", ha="center", va="center", fontsize=7,
                        color="black")
    fig.colorbar(im, label="mean GROC across models")
    ax.set_title(f"Method skill (GROC, with RPSS in parentheses) — {area.title()} (precip MOS, LOYO)\n"
                 "GROC spread is within the ~0.1 noise floor, and RPSS is NEGATIVE throughout\n"
                 "(worse than climatology) — GROC alone is not usable skill (see docs/14).", fontsize=9.5)
    fig.tight_layout(); fig.savefig(FIG / f"mme_method_search{sfx}.png", dpi=150); plt.close(fig)
    print(f"replotted mme_method_search{sfx}.png")


if __name__ == "__main__":
    rows = load_hybrid()
    taxonomy_scatter(rows)
    ond_mme_bars()
    replot_domain_heatmap("nigeria", "")
    replot_method_heatmap("nigeria", "")
