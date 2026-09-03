"""
multiplicity.py — does any predictor survive multiple-comparison control?

The feature search reports the best of ~300 cross-validated correlations per country, so the
"winners" are upward-biased (winner's curse). This runs the control the reviewers asked for:

  1. a PERMUTATION test for each (season, band, predictor) cell — shuffle the rainfall years,
     recompute the leave-one-year-out (LOO) skill, build a null, get a p-value;
  2. Benjamini–Hochberg FDR across all cells per country (q < 0.10 and q < 0.05);
  3. a held-out BLOCK test — train on 1991–2009, test on 2010–2023 (genuinely out-of-sample) —
     for the headline predictors.

Uses a closed-form LOO correlation (leverage formula) so 5,000 permutations × 288 cells × 3
countries run in seconds. Scalar predictors only (textbook indices + persistence); the
data-driven sst_projection is multivariate and reported separately in the notebook.

Outputs
  outputs/tables/multiplicity_fdr.md        survivors per country (q<0.10, q<0.05)
  outputs/tables/multiplicity_fdr.csv       every cell: cv_corr, p_perm, q_bh, survives
  outputs/tables/heldout_block.md           out-of-sample (2010–2023) skill for headline cells
  outputs/figures/multiplicity_fdr.png      cv_corr vs significance, FDR survivors highlighted
"""
import warnings, csv, sys
from pathlib import Path
warnings.filterwarnings("ignore")
import numpy as np
import xarray as xr
import africas2s
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import teleconnections as T

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TAB = ROOT / "outputs" / "tables"
FIG = ROOT / "outputs" / "figures"
RNG = np.random.default_rng(0)
NPERM = 5000

COUNTRIES = [("Nigeria", "nigeria_chirps_monthly.nc",
              {"National": (4, 14), "South": (4, 8), "Middle": (8, 11), "North": (11, 14)}),
             ("Ethiopia", "ethiopia_chirps_monthly.nc",
              {"National": (3, 15), "South": (3, 7), "Central": (7, 10), "North": (10, 15)}),
             ("Kenya", "kenya_chirps_monthly.nc",
              {"National": (-5, 5), "South": (-5, -1), "Central": (-1, 2), "North": (2, 5)})]
TEXTBOOK = ["nino34", "atl3", "tna", "tsa", "atl_grad", "iod_dmi", "wvg2", "wvg3"]


# Leave-one-out CV correlation, its one-sided permutation test (upper tail — the LOO null is
# biased negative, so a two-sided |r| test would be invalid) and Benjamini–Hochberg FDR all now
# live in africas2s.metrics. Passing the module-level RNG through preserves the exact permutation
# draw sequence, so this reproduces the published leaderboard bit-for-bit.
from africas2s.metrics import loo_corr, permutation_test, fdr


def perm_pvalue(x, y, nperm=NPERM):
    return permutation_test(x, y, statistic=loo_corr, alternative="greater", n=nperm, rng=RNG)


def seasonal_rain(precip, months, s, n):
    band = precip.sel(lat=slice(s, n)).mean(["lat", "lon"])
    return africas2s.seasonal_reduce(band, months)


def main():
    sst = T.load_sst(); idx = T.build_indices(sst)
    rows = []
    for country, cf, bands in COUNTRIES:
        precip = xr.open_dataset(DATA / cf)["precip"]
        cells = []
        for band, (s, n) in bands.items():
            # Restrict the multiplicity family to WET-SEASON cells per zone: dry-season totals
            # are near zero and produce spurious, outlier-driven correlations. Keep only seasons
            # whose mean rainfall exceeds 45% of the zone's wettest season.
            smeans = {se: float(seasonal_rain(precip, mo, s, n).mean()) for se, mo in T.SEASONS.items()}
            thr = 0.45 * max(smeans.values())
            for season, months in T.SEASONS.items():
                if smeans[season] < thr:
                    continue
                rain = seasonal_rain(precip, months, s, n)
                for ik in TEXTBOOK:
                    pre = T.index_preseason_mean(idx[ik], months)
                    yrs = np.intersect1d(pre.dropna("year").year, rain.dropna("year").year)
                    if len(yrs) < 12:
                        continue
                    x = pre.sel(year=yrs).values.astype(float)
                    y = rain.sel(year=yrs).values.astype(float)
                    r, p = perm_pvalue(x, y)
                    cells.append([country, season, band, ik, r, p])
        pv = [c[5] for c in cells]
        q = fdr(pv)
        for c, qq in zip(cells, q):
            c.append(qq); rows.append(c)
        n10 = sum(np.isfinite(qq) and qq < 0.10 for qq in q)
        n05 = sum(np.isfinite(qq) and qq < 0.05 for qq in q)
        print(f"  {country}: {len(cells)} cells, {n05} survive FDR q<0.05, {n10} survive q<0.10", flush=True)

    with open(TAB / "multiplicity_fdr.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["country", "season", "band", "predictor", "cv_corr", "p_perm", "q_bh"])
        w.writerows([[c[0], c[1], c[2], c[3], round(c[4], 3), round(c[5], 4), round(c[6], 4)] for c in rows])

    # survivors table
    md = ["# Multiplicity control — permutation FDR over the feature leaderboard\n",
          f"Permutation test ({NPERM} shuffles) per (season, band, textbook index) cell, then "
          "Benjamini–Hochberg FDR across all cells per country. Only cells that survive are "
          "defensible as more than best-of-search noise.\n",
          "| Country | cells | survive q<0.05 | survive q<0.10 | strongest survivors (q<0.10) |",
          "|---|---|---|---|---|"]
    for country, _, _ in COUNTRIES:
        cc = [r for r in rows if r[0] == country]
        s05 = [r for r in cc if np.isfinite(r[6]) and r[6] < 0.05]
        s10 = [r for r in cc if np.isfinite(r[6]) and r[6] < 0.10]
        s10.sort(key=lambda r: -abs(r[4]))
        top = "; ".join(f"{r[1]} {r[2]}·{r[3]} (r={r[4]:+.2f}, q={r[6]:.3f})" for r in s10[:5]) or "—"
        md.append(f"| {country} | {len(cc)} | {len(s05)} | {len(s10)} | {top} |")
    (TAB / "multiplicity_fdr.md").write_text("\n".join(md) + "\n")

    # figure: cv_corr vs -log10(p), FDR survivors highlighted
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), sharey=True)
    for ax, (country, _, _) in zip(axes, COUNTRIES):
        cc = [r for r in rows if r[0] == country and np.isfinite(r[5])]
        x = [r[4] for r in cc]; yv = [-np.log10(max(r[5], 1e-4)) for r in cc]
        surv = [np.isfinite(r[6]) and r[6] < 0.10 for r in cc]
        ax.scatter([x[i] for i in range(len(cc)) if not surv[i]], [yv[i] for i in range(len(cc)) if not surv[i]],
                   c="#bbb", s=22, label="not significant")
        ax.scatter([x[i] for i in range(len(cc)) if surv[i]], [yv[i] for i in range(len(cc)) if surv[i]],
                   c="#59A14F", s=42, edgecolor="k", label="survives FDR q<0.10")
        # annotate only the 3 strongest distinct survivor seasons (avoid label pile-up)
        seen = set()
        for i in sorted(range(len(cc)), key=lambda k: -x[k]):
            if surv[i] and cc[i][1] not in seen:
                seen.add(cc[i][1])
                ax.annotate(f"{cc[i][1]} {cc[i][2]}\n{cc[i][3]}", (x[i], yv[i]), fontsize=7,
                            ha="right", va="center", xytext=(-6, 0), textcoords="offset points")
                if len(seen) >= 3:
                    break
        ax.axhline(-np.log10(0.05), color="r", ls="--", lw=0.8)
        nsurv = sum(surv)
        ax.set_title(f"{country} — {nsurv} of {len(cc)} survive FDR q<0.10")
        ax.set_xlabel("LOO CV correlation"); ax.axvline(0, color="k", lw=0.5)
    axes[0].set_ylabel("−log10(permutation p)"); axes[0].legend(fontsize=7)
    fig.suptitle("Multiplicity control: which predictor cells survive permutation-FDR (q<0.10)?\n"
                 "Most best-of-search 'winners' do NOT; the East African OND/IOD cells do.", fontweight="bold")
    fig.tight_layout(); fig.savefig(FIG / "multiplicity_fdr.png", dpi=150); plt.close(fig)

    # ---- held-out block test (train 1991-2009, test 2010-2023) ----
    HEAD = [("Nigeria", "nigeria_chirps_monthly.nc", "JAS", (8, 11), "Middle", "atl3"),
            ("Ethiopia", "ethiopia_chirps_monthly.nc", "OND", (3, 7), "South", "iod_dmi"),
            ("Ethiopia", "ethiopia_chirps_monthly.nc", "JAS", (10, 15), "Kiremt", "wvg3"),
            ("Kenya", "kenya_chirps_monthly.nc", "OND", (-5, 5), "National", "iod_dmi"),
            ("Kenya", "kenya_chirps_monthly.nc", "MAM", (-5, 5), "National", "nino34")]
    hb = ["# Held-out block test — train 1991–2009, test 2010–2023 (out-of-sample)\n",
          "| Country | Season | Zone | Index | in-sample LOO r | **out-of-sample r (2010–2023)** |",
          "|---|---|---|---|---|---|"]
    for country, cf, season, (s, n), band, ik in HEAD:
        precip = xr.open_dataset(DATA / cf)["precip"]
        months = T.SEASONS[season]
        rain = seasonal_rain(precip, months, s, n)
        pre = T.index_preseason_mean(idx[ik], months)
        yrs = np.intersect1d(pre.dropna("year").year, rain.dropna("year").year)
        x = pre.sel(year=yrs); y = rain.sel(year=yrs)
        tr = yrs <= 2009; te = yrs >= 2010
        xr_, yr_ = x.values[tr], y.values[tr]
        b1, b0 = np.polyfit(xr_, yr_, 1)
        pred_te = b0 + b1 * x.values[te]
        oos = np.corrcoef(pred_te, y.values[te])[0, 1] if te.sum() > 4 else np.nan
        ins = loo_corr(x.values, y.values)
        hb.append(f"| {country} | {season} | {band} | {ik} | {ins:+.2f} | **{oos:+.2f}** |")
        print(f"  held-out {country} {season} {band} {ik}: in-sample {ins:+.2f}, OOS {oos:+.2f}", flush=True)
    (TAB / "heldout_block.md").write_text("\n".join(hb) + "\n")
    print("\nwrote multiplicity_fdr.{md,csv,png} and heldout_block.md")


if __name__ == "__main__":
    main()
