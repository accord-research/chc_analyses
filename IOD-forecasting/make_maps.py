"""Render the report's SST anomaly maps: land on top, low-skill cells clearly flagged."""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import cartopy.crs as ccrs, cartopy.feature as cfeature
from africas2s.indices import REGIONS

SKILL_FLOOR = 0.4
MASK_GREY = "#b9b9b9"      # low skill: distinct from both the colormap centre (white) and land
LAND_TAN  = "#efe7d8"

ALL_WINDOWS = (("week1","Week 1"), ("week2","Week 2"), ("week3","Week 3"),
               ("week4","Week 4"), ("day1_30","Days 1–30"))


def render(cf, out, windows=ALL_WINDOWS, ncols=2, panel_w=3.5):
    """All lead windows as a grid of maps, with the colourbar in the spare cell.

    Laid out 2-across rather than 5-across: five panels in one row leaves each too
    narrow for the coastline to be readable, which defeats the point of drawing it.
    The odd count leaves one cell free, which the colourbar occupies.
    """
    anom = cf.calibrated_sst - cf.obs_climatology
    lim = float(np.nanpercentile(np.abs(anom.values), 98))
    norm = TwoSlopeNorm(vcenter=0, vmin=-lim, vmax=lim)
    proj = ccrs.PlateCarree()
    plt.rcParams.update({"font.size": 9})

    n = len(windows)
    nrows = int(np.ceil(n / ncols))
    aspect = (115 - 45) / (15 - -15)                      # extent is 70 deg by 30 deg
    fig, axes = plt.subplots(nrows, ncols, figsize=(panel_w * ncols, panel_w / aspect * nrows * 1.5),
                             subplot_kw={"projection": proj})
    axes = np.atleast_1d(axes).ravel()

    for ax, (w, title) in zip(axes, windows):
        # Masked cells must not fall through to white -- white is the colormap's own
        # centre, so an unskilful cell would read as "no anomaly".
        ax.set_facecolor(MASK_GREY)
        a = anom.sel(window=w).where(cf.loyo_r.sel(window=w) >= SKILL_FLOOR)
        im = ax.pcolormesh(anom.lon, anom.lat, a, cmap="RdBu_r", norm=norm,
                           shading="auto", transform=proj, zorder=2)
        ax.add_feature(cfeature.LAND.with_scale("50m"), facecolor=LAND_TAN, edgecolor="none", zorder=3)
        ax.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.4, edgecolor="#5a5a5a", zorder=4)
        ax.add_feature(cfeature.BORDERS.with_scale("50m"), linewidth=0.25, edgecolor="#9a9a9a", zorder=4)
        ax.set_extent([45, 115, -15, 15], crs=proj)
        ax.set_title(title, fontsize=10, pad=3)
        ax.set_xticks([50, 70, 90, 110], crs=proj); ax.set_yticks([-10, 0, 10], crs=proj)
        ax.set_xticklabels(["50°E","70°E","90°E","110°E"]); ax.set_yticklabels(["10°S","0°","10°N"])
        ax.tick_params(labelsize=7.5, pad=1)
        for box, c in (("wtio", "#c4552f"), ("setio", "#1f6f80")):
            b = REGIONS[box]
            ax.add_patch(plt.Rectangle((b["west"], b["south"]), b["east"]-b["west"], b["north"]-b["south"],
                                       fill=False, ec=c, lw=1.3, transform=proj, zorder=5))

    spare = list(axes[n:])
    for ax in spare:
        ax.axis("off")
    fig.tight_layout(pad=0.7)
    if spare:
        # colourbar sits in the empty grid cell rather than stealing width from the maps
        box = spare[0].get_position()
        cax = fig.add_axes([box.x0 + box.width * 0.16, box.y0 + box.height * 0.50,
                            box.width * 0.58, box.height * 0.055])
        cb = fig.colorbar(im, cax=cax, orientation="horizontal")
    else:
        cb = fig.colorbar(im, ax=axes.tolist(), fraction=.030, pad=.015)
    cb.set_label("°C vs observed climatology", fontsize=8, labelpad=2)
    cb.ax.tick_params(labelsize=7)
    fig.savefig(out, dpi=230, bbox_inches="tight"); plt.close(fig)
    return out


if __name__ == "__main__":
    import sys; sys.path.insert(0, ".")
    import iod_pipeline as iod
    res = iod.run("2026-08-31", verbose=False)
    print("wrote", render(res["calibrated_fields"], "outputs/figures/fig3_maps.png"))
