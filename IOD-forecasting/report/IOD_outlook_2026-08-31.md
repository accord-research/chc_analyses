---
title: "Indian Ocean SST and Dipole Outlook"
subtitle: "Forecast issued 31 August 2026 · covering 31 August – 29 September 2026"
author: "ACCORD / CHC — draft for review"
date: "8 September 2026"
geometry: "margin=1.5cm"
header-includes:
  - \usepackage{titling}
  - \usepackage{graphicx}
  - \pretitle{\begin{center}\includegraphics[width=0.50\textwidth]{assets/logo_strip.png}\\[0.7em]\LARGE\bfseries}
  - \posttitle{\par\end{center}\vskip 0.2em}
  - \usepackage{caption}
  - \captionsetup{font=small,skip=2pt}
  - \usepackage{float}
  - \let\origfigure\figure \let\endorigfigure\endfigure
  - \renewenvironment{figure}[1][]{\origfigure[H]}{\endorigfigure}
fontsize: 10pt
mainfont: "Helvetica Neue"
colorlinks: true
linkcolor: "black"
---

## Abstract

A forecast of sea surface temperature in the two Indian Ocean Dipole boxes, and of the
dipole, for the next 30 days and each of the next four weeks, from the ECMWF sub-seasonal
(S2S) forecast corrected against NOAA OI SST by linear regression.

**A positive dipole at every horizon**, weak-to-moderate: +0.43 °C in week 1, +0.82 and +0.86
in weeks 2 and 3, +0.72 over 30 days. It is driven almost entirely by a warm western box,
0.7–1.0 °C above its 2006–2025 average; the eastern box is near normal, +0.1 to +0.3.

**A positive IOD developing through spring is the broad consensus** — BoM, JAMSTEC, IRI and
the WMO Global Seasonal Climate Update all forecast one — **but our near-term values sit above
the independent observed estimates.** BoM's index for our week-1 window is +0.25 and it calls
the IOD *neutral*, after five straight weeks below the +0.4 threshold with forecast magnitudes
easing; on our own data and baseline the observed dipole for that week is +0.01. Treat the
first week as an upper estimate.

**Only at week 2 does the forecast measurably beat persistence**, there in both boxes (+0.16
west, +0.15 east, 80% intervals excluding zero). At every other horizon the gain is **not
separable from sampling noise on twenty years** — including the east's larger +0.21 and +0.18
at weeks 3–4 and the +0.11 on the 30-day window. This cuts both ways: the small negative gains
at week 1, and at week 4 in the west, are equally inconclusive.

## Method

**Model.** ECMWF S2S extended-range ensemble, issued 31 August 2026: 100 members, 46 daily
steps, 1.5° grid, from the ECMWF Data Store (`ecds.ecmwf.int`), dataset `s2s-forecasts`,
variable `sea_surface_temperature`. **Training:** the reforecast set for the same calendar
date (`s2s-reforecasts`) — the same run for 31 August in each of 2006–2025, 10 members each.
**Observations:** NOAA OI SST v2.1, 0.25° daily, from NOAA PSL — the record CHC uses.
**Boxes:** Saji et al. (1999), west 50–70 °E / 10 °S–10 °N and east 90–110 °E / 10 °S–0,
area-weighted by cosine of latitude on each dataset's own grid.

**Windows.** Days 1–7, 8–14, 15–21, 22–28 and 1–30. S2S SST is filed as a 24-hour mean, so
day 1 is the **day of the 00Z issuance**, not the day after: week 1 verifies 31 August to
6 September, and the 30-day window includes the issuance day, whose ocean state is already
partly known.

**Correction.** Per box and window, ordinary least squares of observed on forecast temperature
across the twenty reforecast years, applied to this year's forecast. Regression rather than
quantile matching, because a straight line continues a warming trend outside the historical
range while quantile matching pulls values back inside it.

**Uncertainty.** An 80% prediction interval on Student's *t*, 18 degrees of freedom, carrying
both fitted-line uncertainty and residual scatter — deliberately not the naive
`1.28 × residual sd`, because **this forecast sits 2.3–3.0 standard deviations above the
training mean in the west**, where omitting the extrapolation term understated the interval by
20–28%. It reflects how wrong the method has been on past years, not how much this week's 100
members disagree. **Testing** is leave-one-year-out throughout: the line is refitted without
each year, then used to predict it. **Reproducing:** `iod_pipeline.run("2026-08-31")` — the
date is the only input, and reforecasts exist only for Monday and Thursday issuances.

![**(a)** Forecast anomaly in each box, 80% prediction intervals. **(b)** The dipole, calibrated and raw — the gap is the regression's amplitude correction, not bias removal. **(c,d)** Leave-one-year-out correlation against two persistence baselines; shading is the gain over the harder 30-day one.](assets/fig1_combined.png){width=92%}

## Results

| Horizon | Valid | West box | East box | Dipole |
|---|---|---|---|---|
| Week 1 | 31 Aug – 6 Sep | 28.36 °C (+0.70) | 28.36 °C (+0.27) | +0.43 ± 0.50 |
| Week 2 | 7–13 Sep | 28.73 °C (+1.03) | 28.31 °C (+0.21) | +0.82 ± 0.40 |
| Week 3 | 14–20 Sep | 28.81 °C (+1.02) | 28.26 °C (+0.16) | +0.86 ± 0.62 |
| Week 4 | 21–27 Sep | 28.78 °C (+0.83) | 28.28 °C (+0.10) | +0.73 ± 0.59 |
| Days 1–30 | 31 Aug – 29 Sep | 28.68 °C (+0.89) | 28.29 °C (+0.17) | +0.72 ± 0.42 |

Absolute temperatures; brackets are the departure from the **2006–2025** average for the same
dates, dipole in °C with its 80% interval. That baseline is the reforecast period, not the
1991–2020 climatology BoM, CPC and NOAA use — **these anomalies are not directly comparable
with the dipole values those centres publish.**

The raw model dipole is smaller (+0.33 to +0.64). That difference is **the regression's
amplitude correction, not bias removal**: least squares with an intercept preserves the mean,
so constant bias cancels on both sides. What changes is amplitude — the west is stretched
(slope 1.04–1.42, the ensemble mean under-disperses it) and the east shrunk (0.62–0.80, where
the model over-amplifies variability). The calibrated dipole is the product; the raw column
shows the size of that correction.

## Accuracy

Leave-one-year-out correlation over the twenty reforecast years against persistence — "the
ocean stays as it is at issue". Persistence is a hard baseline for SST and how hard depends on
the window it averages, so both are shown. Gains carry an 80% bootstrap interval, resampling
the (model, persistence, observed) triples so the dependence between the predictors is kept.

| | Week 1 | Week 2 | Week 3 | Week 4 | Days 1–30 |
|---|---|---|---|---|---|
| **West** — model | 0.89 | 0.90 | 0.76 | 0.69 | 0.83 |
| persistence 30 d / 14 d | 0.85 / 0.88 | 0.74 / 0.68 | 0.68 / 0.60 | 0.71 / 0.63 | 0.81 / 0.75 |
| gain (80% interval) | +0.04 (−0.04, +0.12) | **+0.16 (+0.02, +0.28)** | +0.08 (−0.07, +0.22) | −0.02 (−0.11, +0.14) | +0.02 (−0.07, +0.14) |
| **East** — model | 0.87 | 0.92 | 0.83 | 0.77 | 0.90 |
| persistence 30 d / 14 d | 0.87 / 0.85 | 0.77 / 0.61 | 0.62 / 0.36 | 0.60 / 0.31 | 0.79 / 0.60 |
| gain (80% interval) | −0.01 (−0.06, +0.04) | **+0.15 (+0.03, +0.20)** | +0.21 (−0.02, +0.32) | +0.18 (−0.05, +0.30) | +0.11 (−0.02, +0.19) |

**Week 2 is the only horizon whose gain excludes zero, and it does so in both boxes.** Weeks 3
and 4 in the east have the largest point gains in the table and still cannot be separated from
noise; nor can the 30-day window, the horizon most likely to be quoted. The same standard
applies to the negatives — week 1, and week 4 in the west, are inconclusive rather than
demonstrated failures. Typical error is 0.15–0.29 °C (west) and 0.20–0.37 °C (east). Baseline
length matters: an earlier draft used only the 14-day window, the weakest of the three tested,
and claimed the forecast beat persistence at every horizon by a margin growing with lead —
that claim is withdrawn.

![Corrected SST anomaly at every horizon (°C vs the 2006–2025 observed average). Boxes: western (orange) and eastern (teal); land in tan. Grey ocean is where leave-one-year-out correlation falls below 0.4 and the forecast should not be relied on; that area expands with lead across the basin, and the eastern box is consistently the more affected. Each cell is corrected by its own regression, observations averaged from 0.25° to the model's 1.5° grid. Fields are cubic-refined for contouring — presentational only, and the zero contour in particular is placed by the interpolation rather than measured.](assets/fig3_maps.png){width=88%}

## Early verification

OISST now covers the whole week-1 window, so that forecast can be checked.

| | calibrated | raw | observed | error (interval) |
|---|---|---|---|---|
| West | 28.36 | 28.47 | 28.23 | **+0.13** (±0.22) |
| East | 28.36 | 28.65 | 28.65 | **−0.29** (±0.36) |
| Dipole | +0.43 | +0.33 | **+0.01** | **+0.42** (±0.50) |

Every error is inside its interval, but two things deserve saying. The dipole error is near
the edge and in the direction of the forecast being **too positive**, consistent with BoM
calling the IOD neutral that week. And in the east the **raw model was essentially exact
(28.65 against 28.65) while the calibration moved it 0.29 °C the wrong way** — the shrinkage
risk of a twenty-point fit made concrete, since a slope of 0.80 estimated from twenty years
cannot know when a year does not need shrinking. One week is not a verification, but it is
reason to treat the eastern calibration with caution and keep verifying.

## Limitations

- **Only week 2 shows a gain over persistence that twenty years can resolve.** Weeks 3–4 and
  the 30-day window have larger point gains in the east but intervals straddling zero; week 1
  is indistinguishable from persistence rather than worse than it.
- **Near-term values run above independent estimates** (BoM +0.25 and neutral, our own
  observations +0.01, against our +0.43). Direction over the season is not in dispute.
- **The baseline is 2006–2025, not 1991–2020**, and on a different SST analysis from BoM's, so
  these anomalies are not directly comparable with published dipole values.
- **Twenty years is a short training record**, and this forecast extrapolates 2.3–3.0 standard
  deviations beyond the training mean in the west. The interval accounts for that; the slope
  estimate still rests on twenty points.
- **The dipole is built from separately calibrated poles, and that choice is worth ~0.4 °C.**
  Calibrating each pole and differencing multiplies the raw dipole by 1.15–1.82×; regressing
  the observed dipole directly on the model dipole gives shrinkage instead, and a week-2
  forecast of +0.41 against our +0.82. Ours verifies better out-of-sample and is what was
  asked for (poles separately, then combined), but a choice moving the headline by more than
  the +0.4 °C threshold itself deserves stating.
- **The interval is historical**, not ensemble-based; a version using the 100 members' spread
  is the obvious next step.
- **Persistence is given a one-day advantage** — its window ends on the init day and assumes
  same-day observations unavailable at issue — so the comparisons are conservative.
- **Map and box numbers differ by 0.15–0.35 °C**: correcting each cell then averaging is not
  the same calculation as correcting the box average. Quote the table for a box.
- **Box footprints differ slightly** between the 1.5° model and 0.25° observations, so part of
  the model–observation offset is footprint rather than model error.
- **One model only**, ECMWF S2S. GEFSv12 was considered and set aside.
