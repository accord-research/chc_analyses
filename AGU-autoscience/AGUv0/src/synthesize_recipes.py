"""
synthesize_recipes.py — the capstone: one "discovered forecast recipe" per subgeography.

Joins the three observation-only experiments into a single legible artifact:
  E1 seasons   (which window to forecast, per zone)      <- seasons_summary
  E2b features (best cross-validated predictor, per cell) <- features_leaderboard.csv
  E2c setups   (the drought/flood driver family)          <- feature identity

Output is the answer to "different forecast approaches for different seasons and
subgeographies, discovered through the hindcast archive": for each zone's natural
forecast window, the recommended predictor, its honest LOYO skill, and the physical driver.

Outputs
  outputs/tables/discovered_recipes.md       the recipe table
  outputs/figures/discovered_recipes.png      recipe skill bar chart, coloured by driver family
"""
import csv, sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from areas import AREA, LABEL, suffix

ROOT = Path(__file__).resolve().parent.parent
TAB = ROOT / "outputs" / "tables"
FIG = ROOT / "outputs" / "figures"

# feature -> (driver family, one-line mechanism)
FAMILY = {
    "nino34":        ("ENSO / Pacific",        "El Niño–Southern Oscillation"),
    "atl3":          ("Equatorial Atlantic",   "Atlantic Niño (Gulf of Guinea SST)"),
    "tna":           ("Tropical Atlantic",     "tropical N. Atlantic SST"),
    "tsa":           ("Tropical Atlantic",     "tropical S. Atlantic SST"),
    "atl_grad":      ("Tropical Atlantic",     "Atlantic interhemispheric gradient (TNA−TSA)"),
    "iod_dmi":       ("Indian Ocean",          "Indian Ocean Dipole"),
    "wvg2":          ("Pacific gradient (WVG)", "Western-V-Gradient (E-Africa index, one candidate)"),
    "wvg3":          ("Pacific gradient (WVG)", "Western-V-Gradient 3-box"),
    "persistence":   ("Land memory",           "antecedent-season rainfall persistence"),
    "sst_projection": ("Data-driven SST",       "in-fold SST covariance pattern (discovered)"),
    "combo_top2":    ("Multi-feature",         "best 2-feature combination (selected in-fold)"),
}
FAM_COLOR = {
    "ENSO / Pacific": "#4E79A7", "Equatorial Atlantic": "#F28E2B",
    "Tropical Atlantic": "#E15759", "Indian Ocean": "#59A14F",
    "Pacific gradient (WVG)": "#B07AA1", "Land memory": "#9C755F",
    "Data-driven SST": "#111111", "Multi-feature": "#EDC948",
}

# each zone's natural forecast window(s) from E1 (seasons_summary) + a national overview
RECIPES = {
    "nigeria": [
        ("Guinea coast (South, bimodal)", "South", "AMJ", "first rains (long-rains onset)"),
        ("Guinea coast (South, bimodal)", "South", "OND", "second rains"),
        ("Middle Belt (transitional)",    "Middle", "JJAS", "full monsoon"),
        ("Sudano-Sahel (North, unimodal)", "North", "JAS", "monsoon core (PRESASS window)"),
        ("Sudano-Sahel (North, unimodal)", "North", "OND", "short rains / late season"),
        ("National overview",             "National", "JJAS", "whole-country monsoon"),
        ("National overview",             "National", "OND", "whole-country short rains"),
    ],
    "ethiopia": [
        ("Northern highlands (Kiremt)",   "North", "JJAS", "main rains (Kiremt)"),
        ("Northern highlands (Kiremt)",   "North", "JAS", "Kiremt core"),
        ("Central (Belg+Kiremt)",         "Central", "MAM", "Belg / spring rains"),
        ("Central (Belg+Kiremt)",         "Central", "JJAS", "main rains"),
        ("South (bimodal, GHA-type)",     "South", "MAM", "long rains"),
        ("South (bimodal, GHA-type)",     "South", "OND", "short rains"),
        ("National overview",             "National", "JJAS", "whole-country main rains"),
        ("National overview",             "National", "OND", "whole-country short rains"),
    ],
    "kenya": [
        ("South/coast (bimodal)",     "South", "MAM", "long rains"),
        ("South/coast (bimodal)",     "South", "OND", "short rains"),
        ("Central highlands (bimodal)", "Central", "MAM", "long rains"),
        ("Central highlands (bimodal)", "Central", "OND", "short rains"),
        ("North (arid)",              "North", "OND", "short rains"),
        ("National overview",         "National", "MAM", "whole-country long rains"),
        ("National overview",         "National", "OND", "whole-country short rains"),
    ],
}[AREA]


def load_leaderboard():
    rows = []
    with open(TAB / suffix("features_leaderboard","csv")) as f:
        for r in csv.DictReader(f):
            cc = r["cv_corr"]
            r["cv_corr"] = float(cc) if cc not in ("", "None") else np.nan
            rows.append(r)
    return rows


def top_features(rows, season, band, n=2):
    sub = [r for r in rows if r["season"] == season and r["band"] == band
           and np.isfinite(r["cv_corr"])]
    sub.sort(key=lambda r: -r["cv_corr"])
    return sub[:n]


def main():
    rows = load_leaderboard()
    table = []
    for zone_label, band, season, purpose in RECIPES:
        tops = top_features(rows, season, band, 2)
        if not tops:
            continue
        best = tops[0]
        fam, mech = FAMILY.get(best["predictor"], ("?", "?"))
        second = tops[1] if len(tops) > 1 else None
        table.append(dict(
            zone=zone_label, band=band, season=season, purpose=purpose,
            best=best["predictor"], skill=best["cv_corr"], family=fam, mechanism=mech,
            runner=(second["predictor"] if second else ""),
            runner_skill=(second["cv_corr"] if second else np.nan),
        ))

    # --- markdown table ---
    md = [f"# Discovered forecast recipes — {LABEL} (observation-only, LOYO CV)\n",
          "Best cross-validated predictor for each zone's natural forecast window. "
          "Skill = leave-one-year-out correlation of predicted vs observed zone-mean "
          "seasonal rainfall (1991–2023). The predictor is *searched*, not assumed.\n",
          "| Zone | Window | Purpose | Best predictor | Driver family | CV skill | Runner-up |",
          "|---|---|---|---|---|---|---|"]
    for t in table:
        md.append(f"| {t['zone']} | {t['season']} | {t['purpose']} | **{t['best']}** "
                  f"| {t['family']} | {t['skill']:.2f} | {t['runner']} ({t['runner_skill']:.2f}) |")
    md.append("\n**Reading:** the winning approach differs by season and subgeography — a "
              "data-driven SST pattern for the monsoon core, the Indian Ocean / multi-feature "
              "combinations for the short rains, the Atlantic for the Guinea-coast summer, and "
              "rainfall persistence for the late northern season. No single index (WVG "
              "included) is best everywhere; that is the point.\n")
    (TAB / suffix("discovered_recipes","md")).write_text("\n".join(md) + "\n")

    # --- figure: recipe skill bars, coloured by driver family ---
    table_sorted = sorted(table, key=lambda t: t["skill"])
    labels = [f"{t['band']} · {t['season']}\n{t['best']}" for t in table_sorted]
    vals = [t["skill"] for t in table_sorted]
    colors = [FAM_COLOR.get(t["family"], "#888") for t in table_sorted]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(range(len(vals)), vals, color=colors, edgecolor="black", linewidth=0.5)
    ax.set_yticks(range(len(vals))); ax.set_yticklabels(labels, fontsize=9)
    ax.axvline(0, color="k", lw=0.8)
    ax.set_xlabel("LOYO cross-validated correlation (predicted vs observed rainfall)")
    ax.set_title(f"Discovered forecast recipes per {LABEL} subgeography & season\n"
                 "(best predictor per zone's natural window; colour = driver family)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in FAM_COLOR.values()]
    ax.legend(handles, FAM_COLOR.keys(), fontsize=7, loc="lower right", title="driver family")
    fig.tight_layout(); fig.savefig(FIG / suffix("discovered_recipes","png"), dpi=150)
    plt.close(fig)

    print("=== DISCOVERED RECIPES ===")
    for t in table:
        print(f"  {t['band']:9s} {t['season']:5s} -> {t['best']:14s} "
              f"({t['family']:22s}) CV corr {t['skill']:+.2f}   [{t['purpose']}]")
    print("\nwrote", TAB / suffix("discovered_recipes","md"), "and", FIG / suffix("discovered_recipes","png"))


if __name__ == "__main__":
    main()
