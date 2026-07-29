"""
showcase_figures.py — regenerate the SHOWCASE figures in one consistent house style.

The per-analysis scripts each grew their own colours and fonts; embedded side by side they read as
patchwork. This redraws the headline results from the saved CSVs against a single validated palette
and one set of typographic rules, so the document reads as one system.

Palette: reference categorical slots 1-3 (blue/orange/aqua). Slots 1-3 are the documented
all-pairs-safe set. Measured contrast on the white page: blue 4.42:1, orange 3.20:1, aqua 2.82:1 —
aqua is sub-3:1, so the relief rule applies and every series carries a visible direct label (and the
numeric tables remain in the document). Identity is never colour-alone: colour + marker + label.
"""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator

ROOT = Path(__file__).resolve().parent.parent
TAB = ROOT / "outputs" / "tables"
OUT = ROOT / "outputs" / "figures" / "showcase"
OUT.mkdir(parents=True, exist_ok=True)

# ---- design tokens -------------------------------------------------------------------
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]          # categorical slots 1-3
SEQ_STRONG, SEQ_MID = "#2a78d6", "#9ec5f4"           # one-hue sequential (blue)
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE, SURFACE = "#e1e0d9", "#c3c2b7", "#ffffff"
MARKERS = ["o", "s", "^", "D", "v"]

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Inter", "Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": BASELINE, "axes.linewidth": 0.9,
    "axes.labelcolor": INK2, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 9, "axes.labelsize": 9, "legend.fontsize": 8.5,
    "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
    "figure.dpi": 200, "savefig.dpi": 200, "savefig.bbox": "tight",
})


def style(ax, ylabel=None, xlabel=None):
    ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    if ylabel:
        ax.set_ylabel(ylabel, color=INK2)
    if xlabel:
        ax.set_xlabel(xlabel, color=INK2)


def title(ax, text, sub=None):
    """Title + optional deck, both drawn above the axes so they can never collide."""
    ax.text(0, 1.16 if sub else 1.05, text, transform=ax.transAxes, color=INK,
            fontsize=10.5, fontweight="bold", va="bottom", ha="left")
    if sub:
        ax.text(0, 1.045, sub, transform=ax.transAxes, color=MUTED,
                fontsize=8.3, va="bottom", ha="left")


def noskill(ax, y=0.5, label="no skill (GROC 0.5)"):
    # label sits at the LEFT so it never collides with the right-edge value labels
    ax.axhline(y, color=MUTED, linestyle=(0, (4, 3)), linewidth=1, zorder=1)
    ax.text(0.008, y, label, transform=ax.get_yaxis_transform(), ha="left", va="bottom",
            color=MUTED, fontsize=7.6)


def rows(name):
    with open(TAB / name) as f:
        return list(csv.DictReader(f))


# ---- 1 · skill vs lead time ----------------------------------------------------------
def fig_lead():
    data = rows("lead_skill.csv")
    regions = list(dict.fromkeys(r["region"] for r in data))
    fig, ax = plt.subplots(figsize=(7.2, 3.5))
    noskill(ax)
    for i, reg in enumerate(regions):
        sub = sorted([r for r in data if r["region"] == reg], key=lambda r: int(r["lead"]))
        x = [int(r["lead"]) for r in sub]; y = [float(r["groc"]) for r in sub]
        ax.plot(x, y, marker=MARKERS[i], color=SERIES[i], linewidth=2, markersize=5.5,
                markeredgecolor=SURFACE, markeredgewidth=1.2, label=reg.split(" (")[0], zorder=3)
        ax.annotate(f" {y[-1]:.2f}", (x[-1], y[-1]), color=INK2, fontsize=8,
                    va="center", ha="left")
    style(ax, ylabel="GROC (leave-one-year-out)", xlabel="forecast lead time (months)")
    ax.set_xticks(range(1, 7)); ax.set_xlim(0.7, 6.9); ax.set_ylim(0.44, 0.71)
    title(ax, "No realized lead-time decay for East African OND (this MME)",
          "Kenya and Ethiopia hold ~0.55–0.66 out to 6 months; Nigeria sits below no-skill throughout")
    ax.legend(frameon=False, loc="upper left", ncols=3, labelcolor=INK2,
              bbox_to_anchor=(0, -0.30), handlelength=1.6)
    fig.savefig(OUT / "lead_skill.png"); plt.close(fig)


# ---- 2 · downscaling resolution frontier ---------------------------------------------
def fig_frontier():
    data = rows("downscale_frontier.csv")
    regions = list(dict.fromkeys(r["region"] for r in data))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.4, 3.4), sharey=True)

    for i, reg in enumerate(regions):                     # panel 1 — by region (delta)
        sub = sorted([r for r in data if r["region"] == reg and r["method"] == "delta"],
                     key=lambda r: -float(r["res_deg"]))
        x = [float(r["res_km"]) for r in sub]; y = [float(r["groc"]) for r in sub]
        a1.plot(x, y, marker=MARKERS[i], color=SERIES[i], linewidth=2, markersize=5,
                markeredgecolor=SURFACE, markeredgewidth=1.1, label=reg.split(" (")[0], zorder=3)
    noskill(a1)
    a1.set_xscale("log"); a1.invert_xaxis()
    a1.xaxis.set_major_locator(FixedLocator([110, 55, 28, 11, 5.5]))
    a1.set_xticklabels(["110", "55", "28", "11", "5.5"])
    style(a1, ylabel="GROC at that resolution", xlabel="target resolution (km), finer to the right")
    title(a1, "A plateau, not a cliff", "skill preserved to ~5 km (delta)")
    # legend below the axes so it can never sit on top of the data
    a1.legend(frameon=False, loc="upper left", bbox_to_anchor=(0, -0.24), ncols=3,
              labelcolor=INK2, handlelength=1.6, fontsize=7.8, columnspacing=1.2)

    # panel 2 — by method (Kenya). Highlight pattern: the winner carries the hue, the rest form a
    # muted reference band. Avoids a 5-hue palette (and its contrast problems) and states the
    # finding directly; identity comes from labels, never colour alone.
    methods = ["delta", "cca", "rank-analog", "qm", "bcsd"]
    for i, m in enumerate(methods):
        sub = sorted([r for r in data if r["region"] == "Kenya OND" and r["method"] == m],
                     key=lambda r: -float(r["res_deg"]))
        if not sub:
            continue
        x = [float(r["res_km"]) for r in sub]; y = [float(r["groc"]) for r in sub]
        strong = m == "delta"
        a2.plot(x, y, marker="o" if strong else None,
                color=SERIES[0] if strong else "#bdbbb4",
                linewidth=2 if strong else 1.3, markersize=5,
                markeredgecolor=SURFACE, markeredgewidth=1.1,
                zorder=5 if strong else 3)
        if strong:
            a2.annotate("  delta", (x[-1], y[-1]), color=SERIES[0], fontsize=8.5,
                        fontweight="bold", va="center", ha="left")
    # label the muted lines truthfully: rank-analog/qm/bcsd cluster ~0.52-0.54, cca is a clear outlier
    a2.annotate("  rank-analog,\n  qm, bcsd", (5.5, 0.531), color=MUTED, fontsize=7.6,
                va="center", ha="left")
    a2.annotate("  cca", (5.5, 0.500), color=MUTED, fontsize=7.6, va="center", ha="left")
    noskill(a2)
    a2.set_xscale("log"); a2.invert_xaxis()
    a2.xaxis.set_major_locator(FixedLocator([110, 55, 28, 11, 5.5]))
    a2.set_xticklabels(["110", "55", "28", "11", "5.5"])
    style(a2, xlabel="target resolution (km), finer to the right")
    title(a2, "Which method preserves skill", "Kenya OND — delta leads at every resolution")
    a1.set_ylim(0.46, 0.63)
    a2.set_xlim(a2.get_xlim()[0], 3.4)      # headroom so the right-edge labels fit
    fig.savefig(OUT / "downscale_frontier.png"); plt.close(fig)


# ---- 3 · Kenya OND skill by SST predictor domain -------------------------------------
def fig_domains():
    data = [r for r in rows("mme_domain_search_kenya.csv")
            if r["target"].startswith("OND National")]
    order = sorted(data, key=lambda r: float(r["groc"]))
    labels = [r["domain"].replace("_", " ") for r in order]
    groc = [float(r["groc"]) for r in order]
    rpss = [float(r["rpss"]) for r in order]
    best = max(range(len(groc)), key=lambda i: groc[i])

    # Both measures are "distance from a baseline" (GROC vs 0.5 no-skill, RPSS vs 0 climatology),
    # so both are DIVERGING bars anchored on that baseline — never bars on a truncated axis, which
    # would misencode magnitude by length. Blue above / red below, the documented diverging pair.
    POS, NEG = "#2a78d6", "#e34948"
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.4, 3.0), sharey=True)
    ypos = list(range(len(labels)))

    a1.barh(ypos, [v - 0.5 for v in groc], left=0.5, height=0.62, zorder=3,
            color=[POS if v >= 0.5 else NEG for v in groc])
    a1.axvline(0.5, color=BASELINE, linewidth=1.2, zorder=4)
    for i, v in enumerate(groc):
        a1.text(v + 0.004, i, f"{v:.3f}", va="center", color=INK2, fontsize=8)
    a1.set_yticks(ypos); a1.set_yticklabels(labels, color=INK2)
    a1.set_xlim(0.48, 0.75)
    a1.grid(axis="x", color=GRID, linewidth=0.8); a1.set_axisbelow(True); a1.tick_params(length=0)
    a1.set_xlabel("GROC", color=INK2)
    title(a1, "Discrimination (GROC)", "bars measured from 0.5 = no skill")

    a2.barh(ypos, rpss, height=0.62, zorder=3,
            color=[POS if v >= 0 else NEG for v in rpss])
    a2.axvline(0, color=BASELINE, linewidth=1.2, zorder=4)
    for i, v in enumerate(rpss):
        a2.text(v + (0.004 if v >= 0 else -0.004), i, f"{v:+.3f}", va="center",
                ha="left" if v >= 0 else "right", color=INK2, fontsize=8)
    a2.set_xlim(-0.12, 0.23)
    a2.grid(axis="x", color=GRID, linewidth=0.8); a2.set_axisbelow(True); a2.tick_params(length=0)
    a2.set_xlabel("RPSS", color=INK2)
    title(a2, "Probabilistic value (RPSS)", "bars measured from 0 = climatology")
    fig.savefig(OUT / "domain_skill.png"); plt.close(fig)


# ---- 4 · genuine out-of-sample block validation --------------------------------------
def fig_heldout():
    """Genuine OOS: the search re-run on train (1991-2009), winners scored on 2010-2023 with 95%
    CIs. Reads heldout_genuine.csv. Green = OOS CI excludes 0 (holds); muted = CI spans 0 (collapse)."""
    import csv as _csv
    rows = {}
    with open(TAB / "heldout_genuine.csv") as f:
        for r in _csv.DictReader(f):
            rows[(r["country"], r["season"], r["predictor"])] = r
    # curated set mirroring the showcase table: East-African OND (holds) + Nigeria winners (collapse)
    want = [("Kenya", "OND", None, "Kenya  OND · ENSO/IOD"),
            ("Ethiopia", "OND", None, "Ethiopia  OND · ENSO/IOD"),
            ("Nigeria", "JJA", "atl3", "Nigeria  JJA · ATL3"),
            ("Nigeria", "JAS", "persistence", "Nigeria  JAS · persistence")]
    items = []
    for country, season, pred, lab in want:
        match = None
        for (c, s, p), r in rows.items():
            if c == country and s == season and (pred is None or p == pred):
                match = r; break
        if match:
            items.append((lab, float(match["train_r"]), float(match["oos_r"]),
                          float(match["oos_lo"]), float(match["oos_hi"])))
    fig, ax = plt.subplots(figsize=(7.4, 2.7))
    for i, (lab, tr, oos, lo, hi) in enumerate(items):
        holds = lo > 0                      # CI excludes zero -> genuine OOS signal
        col = SERIES[0] if holds else MUTED
        ax.plot([lo, hi], [i, i], color=col, linewidth=2.4, zorder=2, alpha=0.5)   # 95% CI bar
        ax.scatter([tr], [i], s=44, facecolor=SURFACE, edgecolor=MUTED, linewidth=1.6, zorder=3)  # train (hollow)
        ax.scatter([oos], [i], s=54, color=col, zorder=4)                          # OOS (filled)
        ax.text(hi + 0.02, i, f"{oos:+.2f}", va="center", color=INK2, fontsize=8)
        ax.text(tr - 0.02, i, f"train {tr:+.2f}", va="center", ha="right", color=MUTED, fontsize=7.5)
    ax.axvline(0, color=BASELINE, linewidth=1, zorder=1)
    ax.set_yticks(range(len(items)))
    ax.set_yticklabels([i[0] for i in items], color=INK2, fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlim(-0.75, 1.0); ax.set_xlabel("out-of-sample correlation (2010–2023), 95% CI", color=INK2)
    ax.grid(axis="x", color=GRID, linewidth=0.8); ax.set_axisbelow(True); ax.tick_params(length=0)
    ax.spines["left"].set_visible(False)
    title(ax, "Genuinely out-of-sample: East African OND holds, Nigeria's winners collapse",
          "hollow = train (1991–2009) · filled = OOS (2010–2023) · bar = 95% CI · green = CI excludes zero")
    fig.savefig(OUT / "heldout_block.png"); plt.close(fig)


if __name__ == "__main__":
    fig_lead(); fig_frontier(); fig_domains(); fig_heldout()
    for p in sorted(OUT.glob("*.png")):
        print(f"wrote {p.relative_to(ROOT)} ({p.stat().st_size // 1024} KB)")
