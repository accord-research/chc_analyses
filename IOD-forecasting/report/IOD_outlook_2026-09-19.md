---
title: "Indian Ocean SST and Dipole Outlook"
subtitle: "Forecast issued 19 September 2026, covering 19 September to 18 October 2026"
author: "ACCORD / CHC — draft for review"
date: "21 September 2026"
geometry: "margin=1.4cm"
header-includes:
  - \usepackage{titling}
  - \usepackage{graphicx}
  - \pretitle{\begin{center}\includegraphics[width=0.50\textwidth]{assets/logo_strip.png}\\[0.7em]\LARGE\bfseries}
  - \posttitle{\par\end{center}\vskip 0.2em}
  - \usepackage{caption}
  - \captionsetup{font=small,skip=1pt}
  - \setlength{\parskip}{0.35em}
  - \setlength{\abovecaptionskip}{2pt}
  - \setlength{\belowcaptionskip}{2pt}
  - \usepackage{enumitem}
  - \setlist[itemize]{topsep=2pt,itemsep=1pt,parsep=0pt}
  - \usepackage{float}
  - \let\origfigure\figure \let\endorigfigure\endfigure
  - \renewenvironment{figure}[1][]{\origfigure[H]}{\endorigfigure}
fontsize: 10pt
mainfont: "Helvetica Neue"
colorlinks: true
linkcolor: "black"
---

## Abstract

A positive Indian Ocean Dipole is forecast at every horizon over the coming month. The index is
+1.03 °C in week 1 and +0.86 °C over the next 30 days. Six days earlier the same two figures were
+0.94 and +1.02 °C. The western box is 0.85 to 1.03 °C above its 2006–2025 average and the
eastern box is within 0.15 °C of normal.

Forecasts come from the ECMWF sub-seasonal ensemble, corrected against NOAA OI SST by linear
regression on the twenty past years of the same calendar date. At two of the ten box and window
combinations the forecast is more accurate than 30-day persistence and the 80% interval on that
difference stays above zero, both in the eastern box. At one of the two that interval reaches down
to +0.0002 and so sits on zero.

The forecast has been too positive in all four windows that have verified, by 0.20 to 0.38 °C.
In each of them the eastern correction cooled the forecast by 0.15 to 0.29 °C and made it worse
by 0.14 to 0.29 °C, the uncorrected value having been within 0.06 °C of what was observed. A dipole computed as
west minus east is inflated by an eastern value that is too cool, so the numbers above should be
read as an upper estimate.

Two alternative methods were also tested. Neither is more accurate overall, but both give a
weaker dipole for this run, and an ARIMA model fitted to the observed record alone is more
accurate than the corrected forecast in week 1.

## Method

We take the ECMWF sub-seasonal forecast issued on 19 September 2026, which runs with 100
members on a 1.5° grid, together with the matching reforecast for the same calendar
date in each year from 2006 to 2025 at 10 members. Observations are NOAA OI SST v2.1 at 0.25°
daily resolution. Both are averaged over the two dipole boxes of Saji et al. (1999), the west at
50–70 °E and 10 °S–10 °N and the east at 90–110 °E and 10 °S–0, weighting each cell by the cosine
of its latitude.

The lead windows are days 1 to 7, 8 to 14, 15 to 21, 22 to 28 and 1 to 30. Temperature is filed
as a 24-hour mean, so day 1 is the day of issue and week 1 covers 19 to 25 September. An
independent calculation labels day 1 as the following day.

For each box and window we fit a straight line of observed on forecast temperature across the
twenty reforecast years and apply it to this year's forecast. Regression is used rather than
quantile matching, which would pull values back inside the historical range. The 80% intervals
are prediction intervals from that regression and describe how wrong this method has been in past
years rather than the spread of the members. Accuracy figures are leave-one-year-out. Reforecasts
exist only for odd calendar days of the month. The calculation is reproduced by
`iod_pipeline.run("2026-09-19")`.

![**(a)** Forecast anomaly in each box with 80% prediction intervals. **(b)** The dipole from the corrected and uncorrected forecasts, the gap being the change in amplitude made by the regression rather than the removal of a bias. **(c,d)** Leave-one-year-out correlation against two persistence baselines, shaded by the gain over the 30-day one.](assets/fig1_combined_2026-09-19.png){width=96%}

## Results

| Horizon | Valid | West box | East box | Dipole |
|---|---|---|---|---|
| Week 1 | 19 – 25 Sep | 28.92 °C (+1.03) | 28.17 °C (−0.00) | +1.03 ± 0.56 |
| Week 2 | 26 Sep – 2 Oct | 28.94 °C (+0.89) | 28.23 °C (+0.08) | +0.81 ± 0.52 |
| Week 3 | 3 – 9 Oct | 29.19 °C (+0.93) | 28.30 °C (+0.14) | +0.79 ± 0.43 |
| Week 4 | 10 – 16 Oct | 29.23 °C (+0.85) | 28.41 °C (+0.12) | +0.74 ± 0.42 |
| Days 1–30 | 19 Sep – 18 Oct | 29.10 °C (+0.94) | 28.29 °C (+0.09) | +0.86 ± 0.35 |

Absolute temperatures, with the departure from the 2006–2025 average in brackets and the dipole
with its 80% interval. That baseline is the reforecast period rather than the 1991–2020
climatology used by BoM, CPC and NOAA, so these anomalies are not comparable with the dipole
values those centres publish. The uncorrected model dipole is +0.78 to +0.93. The regression
changes amplitude rather than removing a bias, with western slopes of 0.83 to 1.12 and eastern
slopes of 0.72 to 0.75.

## Accuracy

Leave-one-year-out correlation across the twenty reforecast years against persistence, meaning
the observed mean of the 31 days ending at issue, carried forward through the same
leave-one-year-out regression. The gain carries an 80% bootstrap interval.

| | Week 1 | Week 2 | Week 3 | Week 4 | Days 1–30 |
|---|---|---|---|---|---|
| **West** forecast / persistence | 0.83 / 0.84 | 0.84 / 0.84 | 0.80 / 0.70 | 0.76 / 0.72 | 0.87 / 0.85 |
| gain | −0.00 (−0.07, +0.10) | −0.00 (−0.09, +0.10) | +0.10 (−0.04, +0.23) | +0.03 (−0.07, +0.18) | +0.02 (−0.06, +0.12) |
| **East** forecast / persistence | 0.83 / 0.72 | 0.84 / 0.71 | 0.88 / 0.78 | 0.79 / 0.79 | 0.90 / 0.82 |
| gain | +0.11 (−0.02, +0.23) | +0.13 (−0.01, +0.24) | **+0.09 (+0.01, +0.16)** | −0.00 (−0.11, +0.08) | **+0.08 (+0.00, +0.15)** |

The gain is the forecast's correlation minus persistence's. Two of the ten box and window
combinations have an interval above zero, both in the east, and the other eight include zero. The
days 1 to 30 lower bound is shown as +0.00 above because its actual value is +0.0002, so that
interval sits on zero rather than above it. The previous issuance had four above zero. Across four
issuances the eastern gain at weeks 2 to 4 has been positive in eleven of twelve cases, with an
interval above zero in six, and the western gain in one of twenty. Against 7-day persistence the
forecast is less accurate in both boxes at week 1.

![Corrected SST anomaly at every horizon, in °C against the 2006–2025 observed average. The western box is outlined in orange and the eastern in teal. Grey ocean marks cells where leave-one-year-out correlation falls below 0.4 and the forecast should not be relied on. Each cell is corrected by its own regression. Fields are interpolated for contouring, so the zero contour is placed by the interpolation rather than measured.](assets/fig3_maps_2026-09-19.png){width=93%}

## Alternative methods

Two alternatives were tested alongside the standing correction. Both use the observed ocean
temperature at the time of issue, which the standing correction does not use.

The first fits observed temperature on the observed mean of the 30 days to issue and on the
model's forecast change from day 1, so the starting point comes from observations and the model
supplies only the change. Out of sample it is less accurate at every window in both boxes, and
the weight on the model's change is not distinguishable from zero in the west.

The second is an ARIMA(1,0,1) model fitted to the daily observed record up to the day before
issue, using no model data. Root mean square error in °C, on the seventeen years both methods
cover, 2009 to 2025.

| | Week 1 | Week 2 | Week 3 | Week 4 | Days 1–30 |
|---|---|---|---|---|---|
| **West** forecast / ARIMA | 0.196 / **0.117** | **0.167** / 0.207 | **0.198** / 0.294 | **0.240** / 0.337 | **0.139** / 0.210 |
| **East** forecast / ARIMA | 0.283 / **0.184** | 0.290 / 0.293 | **0.266** / 0.342 | **0.284** / 0.443 | **0.219** / 0.290 |

ARIMA is more accurate in week 1 in both boxes and less accurate from week 2 onward, consistent
with the persistence comparison above. No interval is attached, and the smaller differences are
not resolvable on seventeen years.

The comparison is uneven in both directions. ARIMA sees the observed temperature at issue and the
regression does not, but the regression is refitted leaving out one year at a time from all
twenty, so its prediction for an early year is informed by later ones. The seasonal cycle removed
before the ARIMA fit is rebuilt from prior data only, which removes one bias and introduces
another that runs cool. The two effects cannot be separated here. Under the alternative cycle the
ordering is unchanged at weeks 3 and 4 and over days 1–30, while the east at week 2 reverses.

Dipole forecasts for this run, on the 2006–2025 average used in Results.

| | Week 1 | Week 2 | Week 3 | Week 4 | Days 1–30 |
|---|---|---|---|---|---|
| Standing correction | +1.03 | +0.81 | +0.79 | +0.74 | +0.86 |
| Observed start, model change | +0.32 | +0.17 | +0.02 | +0.11 | +0.14 |
| ARIMA | +0.54 | +0.39 | +0.20 | +0.21 | +0.33 |

Both are below the standing forecast, which the verification record also shows running too
positive. Because
ARIMA is a stronger comparison than flat persistence at week 1, the measured gain over
persistence at that lead may overstate what the forecast adds. Neither is proposed as a
replacement.

## Verification record

| run | valid | forecast | observed | error | east raw err | east cal err |
|---|---|---|---|---|---|---|
| 31 Aug | 31 Aug – 6 Sep | +0.43 | +0.05 | +0.38 | −0.06 | −0.35 |
| 31 Aug | 7 – 13 Sep | +0.82 | +0.56 | +0.26 | +0.04 | −0.18 |
| 7 Sep | 7 – 13 Sep | +0.76 | +0.56 | +0.20 | −0.02 | −0.23 |
| 13 Sep | 13 – 19 Sep | +0.94 | +0.69 | +0.25 | −0.01 | −0.16 |

Every error is inside its 80% interval. In all four the dipole forecast was too positive.

## Limitations

- **The eastern correction** has made the forecast worse in all four verified windows, by 0.14 to
  0.29 °C. Read the eastern box and the dipole as upper estimates.
- **The gain over persistence** depends on which persistence is used, and at week 1 the forecast
  is less accurate than 7-day persistence in both boxes.
- **The baseline** is 2006–2025 rather than 1991–2020, and on a different SST analysis from BoM's,
  so these anomalies are not comparable with published dipole values.
- **Twenty years** is a short training record. The western forecast lies 2.6 to 2.9 standard
  deviations beyond the training mean, so the regression is extrapolating.
- **Separate correction** of the two boxes before differencing changes the dipole's amplitude in
  a direction that varies by window. This run it is amplified at weeks 1 and 2 and damped at
  weeks 3 and 4.
- **The intervals** come from past errors, not the ensemble spread, and none is attached to the
  alternative methods.
- **Box and map numbers** differ by up to 0.19 °C in this run. Quote the table.
- **One model.** All figures come from the ECMWF ensemble.
