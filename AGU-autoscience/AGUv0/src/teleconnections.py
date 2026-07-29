"""
teleconnections.py — which SST drivers predict which Nigerian season and region?

Reads cached ERSST-v5 (data/ersst_monthly.nc) and CHIRPS-v3 (data/nigeria_chirps_monthly.nc)
and computes, entirely from observations:

  1. monthly SST index series (anomalies vs 1991-2020): Nino3.4, ATL3 (Atlantic Nino),
     TNA, TSA, Atlantic interhemispheric gradient (TNA-TSA), IOD/DMI, WVG 2-box & 3-box.
  2. Nigeria seasonal rainfall series, national and by latitude band (proxy zones:
     South 4-8N, Middle 8-11N, North 11-14N).
  3. lead-lagged correlations index x (season, band): for each candidate season the SST
     predictor is averaged over the months *preceding* the season (the realistic init
     window), so a nonzero correlation is a usable predictive signal, not concurrent.
  4. an "SST field" view: pointwise correlation map of one season's band rainfall against
     the global SST field, to motivate CCA predictor-domain choices vs. scalar indices.

Outputs
  outputs/figures/teleconn_index_series.png     index time series
  outputs/figures/teleconn_skill_matrix.png     corr(index, season x band) heatmap
  outputs/figures/teleconn_lead_curves.png      corr vs lead for the top drivers
  outputs/figures/teleconn_sst_field_JAS.png    pointwise SST-rainfall corr map
  outputs/tables/teleconn_correlations.csv
  outputs/tables/teleconn_summary.md

Run in the accord-chc env after fetch_data.py.
"""
import warnings
from pathlib import Path
from itertools import product
warnings.filterwarnings("ignore")

import sys
import numpy as np
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from areas import BANDS, CHIRPS_FILE, LABEL, suffix

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"
for d in (FIG, TAB):
    d.mkdir(parents=True, exist_ok=True)

CLIM = (1991, 2020)

# SST index boxes in (south, north, west, east) with lon in 0..360; west>east means wrap.
BOXES = {
    "nino34":   (-5, 5, 190, 240),
    "atl3":     (-3, 3, 340, 360),     # Atlantic Nino / Gulf of Guinea
    "tna":      (5.5, 23.5, 302.5, 345),
    "tsa":      (-20, 0, 330, 370),    # 330-360 & 0-10  (wrap via +360)
    "iod_w":    (-10, 10, 50, 70),
    "iod_e":    (-10, 0, 90, 110),
    "wep":      (-15, 20, 120, 160),   # WVG west equatorial Pacific
    "wnp":      (20, 35, 160, 210),    # WVG west north Pacific
    "wsp":      (-30, -15, 155, 210),  # WVG west south Pacific (3-box)
}

# candidate seasons: name -> list of month numbers
SEASONS = {
    "MAM": [3, 4, 5], "AMJ": [4, 5, 6], "JJA": [6, 7, 8], "JAS": [7, 8, 9],
    "JJAS": [6, 7, 8, 9], "ASO": [8, 9, 10], "SON": [9, 10, 11], "OND": [10, 11, 12],
}


def to360(lon):
    return np.where(np.asarray(lon) < 0, np.asarray(lon) + 360, np.asarray(lon))


def load_sst():
    ds = xr.open_dataset(DATA / "ersst_monthly.nc")
    sst = ds["sst"]
    if "zlev" in sst.dims:
        sst = sst.squeeze("zlev")
    # normalize lon to 0..360 ascending
    sst = sst.assign_coords(lon=(to360(sst.lon))).sortby("lon").sortby("lat")
    return sst


def box_mean(sst, south, north, west, east):
    lat = sst.sel(lat=slice(south, north))
    if east > 360:  # wrap box: [west,360) U [0, east-360]
        a = lat.sel(lon=slice(west, 360))
        b = lat.sel(lon=slice(0, east - 360))
        m = xr.concat([a, b], dim="lon")
    else:
        m = lat.sel(lon=slice(west, east))
    return m.mean(["lat", "lon"])


def monthly_anom(series):
    clim = series.sel(time=slice(f"{CLIM[0]}-01", f"{CLIM[1]}-12")).groupby("time.month").mean("time")
    return series.groupby("time.month") - clim


def build_indices(sst):
    raw = {k: box_mean(sst, *BOXES[k]) for k in BOXES}
    an = {k: monthly_anom(v) for k, v in raw.items()}
    idx = {}
    idx["nino34"] = an["nino34"]
    idx["atl3"] = an["atl3"]
    idx["tna"] = an["tna"]
    idx["tsa"] = an["tsa"]
    idx["atl_grad"] = an["tna"] - an["tsa"]           # interhemispheric Atlantic gradient
    idx["iod_dmi"] = an["iod_w"] - an["iod_e"]
    idx["wvg2"] = an["nino34"] - (an["wep"] + an["wnp"]) / 2.0
    idx["wvg3"] = an["nino34"] - (an["wep"] + an["wnp"] + an["wsp"]) / 3.0
    return idx


def seasonal_sum(precip, months, s, n):
    band = precip.sel(lat=slice(s, n)).mean(["lat", "lon"])
    sel = band.sel(time=band["time.month"].isin(months))
    return sel.groupby("time.year").sum("time")  # (year,)


def index_preseason_mean(index, season_months):
    """Average the SST index over the 3 months ending the month before the season starts
    (a realistic pre-season init window). Returns (year,) aligned to season year."""
    start = min(season_months)
    lead_months = [((start - 1 - k - 1) % 12) + 1 for k in range(3)]  # 3 months before start
    # collect per-year mean over those calendar months (handle year wrap)
    yrs = np.unique(index["time.year"].values)
    out = {}
    for y in yrs:
        vals = []
        for lm in lead_months:
            yy = y if lm < start else y - 1  # a lead month >= season start belongs to prior year
            try:
                v = index.sel(time=f"{yy}-{lm:02d}")
                vals.append(float(np.asarray(v.values).mean()))
            except Exception:
                pass
        if vals:
            out[y] = np.mean(vals)
    ys = sorted(out)
    return xr.DataArray([out[y] for y in ys], coords={"year": ys}, dims="year")


def corr(a, b):
    ay, by = a.dropna("year"), b.dropna("year")
    yrs = np.intersect1d(ay.year, by.year)
    if len(yrs) < 8:
        return np.nan
    x = ay.sel(year=yrs).values
    y = by.sel(year=yrs).values
    if np.std(x) == 0 or np.std(y) == 0:
        return np.nan
    return float(np.corrcoef(x, y)[0, 1])


def main():
    sst = load_sst()
    idx = build_indices(sst)
    print("indices:", list(idx), flush=True)

    ds = xr.open_dataset(DATA / CHIRPS_FILE)
    precip = ds["precip"]

    # ---- index time series figure ----
    fig, ax = plt.subplots(figsize=(11, 5))
    for k in ["nino34", "atl3", "atl_grad", "iod_dmi", "wvg2"]:
        s = idx[k].sel(time=slice("1991", "2023")).groupby("time.year").mean("time")
        ax.plot(s.year, s.values, label=k, lw=1.2)
    ax.axhline(0, color="k", lw=0.5); ax.legend(ncol=5, fontsize=8)
    ax.set_title("Annual-mean SST index anomalies (ERSST v5, 1991-2020 base)")
    ax.set_ylabel("index"); fig.tight_layout()
    fig.savefig(FIG / suffix("teleconn_index_series","png"), dpi=150); plt.close(fig)

    # ---- skill matrix: corr(index preseason, season x band rainfall) ----
    index_keys = ["nino34", "atl3", "tna", "tsa", "atl_grad", "iod_dmi", "wvg2", "wvg3"]
    rows = []
    for season, (bname, (s, n)) in product(SEASONS, BANDS.items()):
        months = SEASONS[season]
        rain = seasonal_sum(precip, months, s, n)
        for ik in index_keys:
            pre = index_preseason_mean(idx[ik], months)
            r = corr(pre, rain)
            rows.append(dict(season=season, band=bname, index=ik, corr=r))

    import csv
    with open(TAB / suffix("teleconn_correlations","csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["season", "band", "index", "corr"])
        w.writeheader(); w.writerows(rows)

    # heatmap for National + South + North: index x season
    for bname in ["National", "South", "North"]:
        M = np.full((len(index_keys), len(SEASONS)), np.nan)
        for i, ik in enumerate(index_keys):
            for j, season in enumerate(SEASONS):
                rr = [r["corr"] for r in rows if r["band"] == bname and r["index"] == ik and r["season"] == season]
                M[i, j] = rr[0] if rr else np.nan
        fig, ax = plt.subplots(figsize=(9, 5))
        im = ax.imshow(M, cmap="RdBu_r", vmin=-0.7, vmax=0.7, aspect="auto")
        ax.set_xticks(range(len(SEASONS))); ax.set_xticklabels(list(SEASONS), rotation=45)
        ax.set_yticks(range(len(index_keys))); ax.set_yticklabels(index_keys)
        for i in range(len(index_keys)):
            for j in range(len(SEASONS)):
                if np.isfinite(M[i, j]):
                    ax.text(j, i, f"{M[i,j]:.2f}", ha="center", va="center", fontsize=7,
                            color="white" if abs(M[i, j]) > 0.45 else "black")
        fig.colorbar(im, label="pre-season correlation")
        ax.set_title(f"SST index vs {bname} {LABEL} seasonal rainfall (pre-season lead)")
        fig.tight_layout(); fig.savefig(FIG / suffix(f"teleconn_skill_matrix_{bname}","png"), dpi=150)
        plt.close(fig)

    # ---- SST-field correlation map for JAS North (the monsoon core) ----
    months, (s, n) = SEASONS["JAS"], BANDS["North"]
    rain = seasonal_sum(precip, months, s, n)
    # pre-season SST field (AMJ mean) anomaly per year
    sst_an = monthly_anom(sst)
    pre_field = sst_an.sel(time=sst_an["time.month"].isin([4, 5, 6])).groupby("time.year").mean("time")
    yrs = np.intersect1d(rain.year, pre_field.year)
    rr = rain.sel(year=yrs); ff = pre_field.sel(year=yrs)
    rn = (rr - rr.mean()) / rr.std()
    fn = (ff - ff.mean("year")) / ff.std("year")
    cmap_field = (fn * rn).mean("year")
    fig, ax = plt.subplots(figsize=(11, 4.5))
    cmap_field.plot(ax=ax, cmap="RdBu_r", vmin=-0.7, vmax=0.7,
                    cbar_kwargs={"label": "corr(AMJ SST, JAS North rainfall)"})
    ax.set_title(f"Where does SST predict JAS North-band {LABEL} rainfall?\n(AMJ SST anomaly vs JAS North-band rainfall, per-pixel correlation)")
    fig.tight_layout(); fig.savefig(FIG / suffix("teleconn_sst_field_JAS","png"), dpi=150); plt.close(fig)

    # ---- markdown summary: strongest driver per season x band ----
    md = ["| season | band | top driver | corr | 2nd | corr |", "|---|---|---|---|---|---|"]
    for season, bname in product(SEASONS, ["National", "South", "Middle", "North"]):
        sub = [r for r in rows if r["season"] == season and r["band"] == bname and np.isfinite(r["corr"])]
        sub.sort(key=lambda r: -abs(r["corr"]))
        if len(sub) >= 2:
            md.append(f"| {season} | {bname} | {sub[0]['index']} | {sub[0]['corr']:.2f} "
                      f"| {sub[1]['index']} | {sub[1]['corr']:.2f} |")
    (TAB / suffix("teleconn_summary","md")).write_text("\n".join(md) + "\n")

    print("\n=== TELECONNECTION RESULTS (top driver per season x band) ===")
    print("\n".join(md))
    print("\nfigures ->", FIG, "\ntables ->", TAB)


if __name__ == "__main__":
    main()
