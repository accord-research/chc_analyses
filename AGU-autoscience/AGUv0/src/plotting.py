"""
plotting.py — shared figure style for the Nigeria autoscience outputs.

Small on purpose: seasons.py and teleconnections.py do their own plotting; this centralizes
the look (fonts, Nigeria extent, a consistent diverging/sequential palette) so figures read
as one set. Import and call apply_style() at the top of a script.
"""
import matplotlib as mpl

# Nigeria map extent [lon_w, lon_e, lat_s, lat_n] for cartopy/imshow set_extent
NIGERIA_EXTENT = [2.5, 15.0, 4.0, 14.0]

# diverging (correlation/anomaly) and sequential (rainfall) palettes
DIVERGING = "RdBu_r"
SEQUENTIAL = "YlGnBu"


def apply_style():
    mpl.rcParams.update({
        "figure.dpi": 120,
        "savefig.dpi": 150,
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.facecolor": "white",
        "savefig.bbox": "tight",
    })
