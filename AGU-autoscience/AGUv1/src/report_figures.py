"""report_figures.py — v1 showcase figures from the search results (AGUv1)."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "outputs" / "tables"
FIG = ROOT / "outputs" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
_SRC_LABEL = {"obs_sst_field": "obs SST (perfect-prog)", "gcm_mos_sst": "NMME SST-MOS",
              "gcm_mos_precip": "NMME precip-MOS", "persistence": "persistence",
              "gcm_index": "NMME index (best)", "obs_index": "obs index (best)"}


def groc_heatmap():
    df = pd.read_csv(TAB / "search_results.csv")
    df["row"] = df["predictor_source"].map(_SRC_LABEL).fillna(df["predictor_source"]) + \
        np.where(df["method"] == "qm", " (QM)", "")
    targets = sorted(df["target"].unique())
    fig, axes = plt.subplots(1, len(targets), figsize=(5.4 * len(targets), 4.0))
    if len(targets) == 1:
        axes = [axes]
    row_order = ["NMME precip-MOS", "NMME precip-MOS (QM)", "NMME SST-MOS", "NMME index (best)",
                 "obs SST (perfect-prog)", "obs index (best)", "persistence"]
    for ax, t in zip(axes, targets):
        g = df[df["target"] == t]
        # best achievable per (source, lead) across the widened axes (domain/transform/EOF)
        piv = g.pivot_table(index="row", columns="lead", values="generalized_roc", aggfunc="max")
        piv = piv.reindex([r for r in row_order if r in piv.index])
        im = ax.imshow(piv.values, aspect="auto", cmap="RdYlBu_r", vmin=0.40, vmax=0.75)
        ax.set_xticks(range(piv.shape[1])); ax.set_xticklabels([f"L{c}" for c in piv.columns])
        ax.set_yticks(range(piv.shape[0]))
        ax.set_yticklabels(piv.index if ax is axes[0] else [], fontsize=8)   # label rows once
        for i in range(piv.shape[0]):
            for j in range(piv.shape[1]):
                v = piv.values[i, j]
                if np.isfinite(v):
                    ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7.5,
                            color="white" if (v > 0.68 or v < 0.47) else "black")
        ax.set_title(t); ax.set_xlabel("lead (months before season)")
    fig.colorbar(im, ax=axes, shrink=0.8, label="GROC (0.5 = no skill)")
    fig.suptitle("Discrimination (GROC) across the search: predictor source × lead, per season",
                 fontweight="bold")
    fig.savefig(FIG / "groc_matrix.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"wrote {FIG/'groc_matrix.png'}")


if __name__ == "__main__":
    groc_heatmap()
