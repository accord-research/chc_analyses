"""lead_cof.py — for each discovered target, skill/accuracy vs lead → "when can a COF be held?" (AGUv1).

This is the reframing (critique #2): lead is not a separate analysis but the question asked *of each
rainy-season target*. For every target we take, at each lead, the best **realizable** forecast (the
GCM-MOS configs) and the perfect-prognosis **ceiling** (obs SST), and find the longest lead at which
realizable skill still clears a usefulness threshold — the lead by which a Climate Outlook Forum
could issue a skillful outlook, and the calendar month that implies.

Reads `outputs/tables/search_results.csv` (+ the selected metric from `select.py`).
Writes `cof_windows.md`, `lead_curves.csv`, and `outputs/figures/lead_cof.png`.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import targets as T
from metric_select import main as select_metric

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "outputs" / "tables"
FIG = ROOT / "outputs" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
_MONTH = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
REALIZABLE = ("gcm_mos_precip", "gcm_mos_sst", "gcm_index")   # real forecasts (genuine lead)
CEILING = "obs_sst_field"                          # perfect-prognosis upper bound
# usefulness thresholds per metric (n≈24 noise-aware)
THRESH = {"generalized_roc": 0.60, "rpss": 0.05, "pearson_r": 0.30, "hit_rate": 0.40}


def _issue_month(start_month: int, lead: int) -> str:
    return _MONTH[((start_month - lead - 1) % 12) + 1]


def main():
    metric = select_metric()          # runs metric selection, returns the chosen metric
    df = pd.read_csv(TAB / "search_results.csv")
    thr = THRESH.get(metric, 0.5)
    tgt_objs = {t.name: t for t in T.discover_targets()}

    curves, cof = [], []
    for tname in sorted(df["target"].unique()):
        g = df[df["target"] == tname]
        leads = sorted(g["lead"].unique())
        for ld in leads:
            gl = g[g["lead"] == ld]
            real = gl[gl["predictor_source"].isin(REALIZABLE)]
            ceil = gl[gl["predictor_source"] == CEILING]
            best_real = real[metric].max() if real[metric].notna().any() else np.nan
            best_real_acc = (real.loc[real[metric].idxmax(), "hit_rate"]
                             if real[metric].notna().any() else np.nan)
            curves.append(dict(target=tname, lead=ld, best_realizable=best_real,
                               ceiling=ceil[metric].max() if ceil[metric].notna().any() else np.nan,
                               realizable_accuracy=best_real_acc))
        cur = pd.DataFrame([c for c in curves if c["target"] == tname])
        useful = cur[cur["best_realizable"] >= thr]
        cof_lead = int(useful["lead"].max()) if len(useful) else -1
        sm = tgt_objs[tname].start_month
        peak = float(cur["best_realizable"].max()) if cur["best_realizable"].notna().any() else float("nan")
        cof.append(dict(target=tname, months=tgt_objs[tname].months, selected_metric=metric,
                        threshold=thr, cof_lead=cof_lead,
                        issue_by=_issue_month(sm, cof_lead) if cof_lead >= 0 else "—",
                        peak_skill=round(peak, 3)))

    pd.DataFrame(curves).to_csv(TAB / "lead_curves.csv", index=False)

    # ── COF windows write-up ──
    md = ["# Skill and accuracy vs lead for the selected configuration, per target (AGUv1)", "",
          f"Selection metric (from `metric_selection.md`): **`{metric}`**, usefulness threshold "
          f"**{thr}**. *Realizable* = best GCM-MOS config at that lead; *SST benchmark* = "
          "perfect-prognosis obs-SST (a reference, **not** an upper bound — a dynamical precip "
          "forecast can and here does exceed it). **COF lead** = the longest lead at which realizable "
          "skill still clears the threshold; **issue-by** = the calendar month that lead implies.", "",
          "| target | season | COF lead (months) | issue outlook by | peak realizable skill |",
          "|---|---|---:|---|---:|"]
    for c in cof:
        season = "".join(_MONTH[m][0] for m in c["months"])
        lead_txt = f"{c['cof_lead']}" if c["cof_lead"] >= 0 else "**no useful lead**"
        md.append(f"| {c['target']} | {season} | {lead_txt} | {c['issue_by']} | {c['peak_skill']} |")
    md += ["", "**Reading.** For the selected configuration, this reports how skill and accuracy vary "
           "with lead — including the longest lead at which skill still clears a usefulness threshold "
           "(one operational reading is the latest date by which an outlook could be issued). A target "
           "whose skill never clears the threshold is one where a confident seasonal forecast is not "
           "statistically supported at these leads."]
    (TAB / "cof_windows.md").write_text("\n".join(md) + "\n")

    # ── figure: skill vs lead per target (realizable + ceiling) + accuracy ──
    cdf = pd.DataFrame(curves)
    tlist = sorted(cdf["target"].unique())
    fig, axes = plt.subplots(1, len(tlist), figsize=(5.2 * len(tlist), 4.2), sharey=True)
    if len(tlist) == 1:
        axes = [axes]
    for ax, tname in zip(axes, tlist):
        c = cdf[cdf["target"] == tname].sort_values("lead")
        ax.plot(c["lead"], c["ceiling"], "o--", color="#8a8a8a", label="perfect-prog SST benchmark (obs, not a ceiling)")
        ax.plot(c["lead"], c["best_realizable"], "o-", color="#4E79A7", lw=2, label="best realizable (GCM-MOS)")
        ax.plot(c["lead"], c["realizable_accuracy"], "s:", color="#59A14F", label="realizable accuracy (hit-rate)")
        ax.axhline(thr, color="#E15759", lw=1, ls=":", label=f"usefulness threshold ({thr})")
        cl = [x for x in cof if x["target"] == tname][0]["cof_lead"]
        if cl >= 0:
            ax.axvline(cl, color="#E15759", lw=1, alpha=0.4)
        ax.set_title(tname); ax.set_xlabel("lead (months before season start)")
        ax.invert_xaxis(); ax.grid(alpha=0.3)
    axes[0].set_ylabel(f"{metric} / accuracy")
    axes[-1].legend(fontsize=7, loc="lower left")
    fig.suptitle("Skill and accuracy vs lead, per rainy season (best realizable configuration)",
                 fontweight="bold")
    fig.tight_layout(); fig.savefig(FIG / "lead_cof.png", dpi=150); plt.close(fig)

    print("\n".join(md))
    print(f"\nwrote cof_windows.md, lead_curves.csv, figures/lead_cof.png")


if __name__ == "__main__":
    main()
