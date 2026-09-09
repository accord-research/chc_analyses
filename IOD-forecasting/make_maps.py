"""SST anomaly maps in the GHACOF filled-contour style.

The house style used by the GHACOF-74 replication (and by the CHC deck this task
came from) is a *filled contour* map on a cubic-refined grid, not a pcolormesh of
native cells. On a 1.5 deg field a pcolormesh reads as a mosaic of blocks whose
edges are an artefact of the model grid; contours on a refined grid read as a
field, which is what an SST anomaly is.

The refinement is presentational only. Every number reported anywhere in this
analysis comes from the native-resolution field; nothing here feeds back into the
indices or the skill scores.
"""
import warnings; warnings.filterwarnings("ignore")

import numpy as np
import matplotlib
# Do NOT force a backend on import: this module is imported by the notebook, and
# switching to Agg there silently suppresses every inline figure -- no error, just
# no output. The script entry point selects Agg for itself instead.
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from scipy.ndimage import distance_transform_edt

from africas2s.indices import REGIONS

SKILL_FLOOR = 0.4
MASK_GREY = "#b9b9b9"          # low skill: distinct from the colormap centre and from land
LAND_TAN = "#efe7d8"
OCEAN_BASE = "#f7fbfd"
REFINE = 4

# The outermost model row/column has no coarsened observations to fit against, so
# it is never calibrated (see iod_pipeline.regrid_like). Draw the calibrated
# interior rather than a ring of "no data" around every panel.
EXTENT = [46.5, 112.5, -13.5, 13.5]

# Symmetric about zero so the diverging colours mean what they look like, with a
# deliberate flat band across +/-0.15 -- below that the anomaly is not meaningfully
# different from climatology at this lead and should not read as coloured.
LEVELS = [-1.5, -1.0, -0.7, -0.45, -0.15, 0.15, 0.45, 0.7, 1.0, 1.5]

ALL_WINDOWS = (("week1", "Week 1"), ("week2", "Week 2"), ("week3", "Week 3"),
               ("week4", "Week 4"), ("day1_30", "Days 1–30"))


def _fill_nearest(a):
    """Nearest-neighbour fill of non-finite cells; the spline solver rejects NaN."""
    m = ~np.isfinite(a)
    if not m.any():
        return a
    idx = distance_transform_edt(m, return_distances=False, return_indices=True)
    return a[tuple(idx)]


def refine(da, factor=REFINE, method="cubic"):
    """Cubic-upsample onto a finer grid so contours are smooth, not stair-stepped.

    NaNs are nearest-filled first and masked out again afterwards by the caller,
    so the fill never shows: it exists only to keep the spline solver fed.
    """
    lat, lon = da["lat"].values, da["lon"].values
    filled = da.copy(data=_fill_nearest(da.values))
    flat = np.linspace(lat.min(), lat.max(), (len(lat) - 1) * factor + 1)
    flon = np.linspace(lon.min(), lon.max(), (len(lon) - 1) * factor + 1)
    return filled.interp(lat=flat, lon=flon, method=method)


def _basemap(ax, proj):
    ax.add_feature(cfeature.OCEAN.with_scale("50m"), facecolor=OCEAN_BASE, zorder=0)
    ax.add_feature(cfeature.LAND.with_scale("50m"), facecolor=LAND_TAN, edgecolor="none", zorder=5)
    ax.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.5, edgecolor="#444", zorder=6)
    ax.add_feature(cfeature.BORDERS.with_scale("50m"), linewidth=0.3, edgecolor="#8d8d8d", zorder=6)
    ax.set_extent(EXTENT, crs=proj)
    for box, c in (("wtio", "#b8431f"), ("setio", "#12606f")):
        b = REGIONS[box]
        ax.add_patch(plt.Rectangle((b["west"], b["south"]), b["east"] - b["west"],
                                   b["north"] - b["south"], fill=False, ec=c, lw=1.6,
                                   transform=proj, zorder=7))


def _panel(ax, anom_w, skill_w, proj, norm, title):
    # Low-skill cells are masked on the REFINED grid, the same way GHACOF applies
    # its dry mask: refine the boolean, threshold it back, then paint the masked
    # area explicitly. Painting it (rather than relying on the axes facecolour)
    # matters because the OCEAN feature underneath would otherwise show through
    # and an unskilful cell would read as pale ocean -- i.e. as no anomaly.
    # Masking before refining would let the spline drag unskilful values into
    # neighbouring cells.
    fine = refine(anom_w)
    keep = refine(skill_w.astype(float), method="linear").values > 0.5
    lon, lat = fine["lon"].values, fine["lat"].values
    if (~keep).any():
        ax.contourf(lon, lat, (~keep).astype(float), levels=[0.5, 1.5],
                    colors=[MASK_GREY], transform=proj, zorder=1)
    vals = np.where(keep, fine.values, np.nan)
    cs = ax.contourf(lon, lat, vals, levels=LEVELS, cmap="RdBu_r", norm=norm,
                     extend="both", transform=proj, zorder=2)
    # a hairline on the zero crossing, so the sign boundary is locatable
    ax.contour(lon, lat, vals, levels=[0.0], colors="#5a5a5a", linewidths=0.5,
               transform=proj, zorder=3)
    _basemap(ax, proj)
    ax.set_title(title, fontsize=10, pad=3)
    return cs


def render(cf, out, windows=ALL_WINDOWS, ncols=2, panel_w=3.5):
    """All lead windows as filled-contour maps, colourbar in the spare cell.

    Laid out 2-across rather than 5-across: five panels in one row leaves each too
    narrow for the coastline to be readable, which defeats the point of drawing it.
    The odd count leaves one cell free, which the colourbar occupies.
    """
    anom = cf.calibrated_sst - cf.obs_climatology
    proj = ccrs.PlateCarree()
    norm = BoundaryNorm(LEVELS, ncolors=plt.get_cmap("RdBu_r").N, extend="both")
    plt.rcParams.update({"font.size": 9})

    n = len(windows)
    nrows = int(np.ceil(n / ncols))
    aspect = (EXTENT[1] - EXTENT[0]) / (EXTENT[3] - EXTENT[2])
    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(panel_w * ncols, panel_w / aspect * nrows * 1.28),
                             subplot_kw={"projection": proj})
    axes = np.atleast_1d(axes).ravel()

    for ax, (w, title) in zip(axes, windows):
        cs = _panel(ax, anom.sel(window=w), cf.loyo_r.sel(window=w) >= SKILL_FLOOR,
                    proj, norm, title)
        ax.set_xticks([50, 70, 90, 110], crs=proj); ax.set_yticks([-10, 0, 10], crs=proj)
        ax.set_xticklabels(["50°E", "70°E", "90°E", "110°E"])
        ax.set_yticklabels(["10°S", "0°", "10°N"])
        ax.tick_params(labelsize=7.5, pad=1)

    spare = list(axes[n:])
    for ax in spare:
        ax.axis("off")
    fig.tight_layout(pad=0.7)
    if spare:
        box = spare[0].get_position()
        cax = fig.add_axes([box.x0 + box.width * 0.16, box.y0 + box.height * 0.50,
                            box.width * 0.58, box.height * 0.055])
        cb = fig.colorbar(cs, cax=cax, orientation="horizontal", ticks=LEVELS[::2])
    else:
        cb = fig.colorbar(cs, ax=axes.tolist(), fraction=.030, pad=.015, ticks=LEVELS[::2])
    cb.set_label("°C vs observed climatology", fontsize=8, labelpad=2)
    cb.ax.tick_params(labelsize=7)
    fig.savefig(out, dpi=230, bbox_inches="tight"); plt.close(fig)
    return out


if __name__ == "__main__":
    matplotlib.use("Agg")
    import sys; sys.path.insert(0, ".")
    import iod_pipeline as iod
    res = iod.run("2026-08-31", verbose=False)
    print("wrote", render(res["calibrated_fields"], "outputs/figures/fig3_maps.png"))
