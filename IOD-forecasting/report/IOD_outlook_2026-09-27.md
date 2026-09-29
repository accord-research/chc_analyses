---
title: "Indian Ocean SST and Dipole Outlook"
subtitle: "Forecast issued 27 September 2026, covering 27 September to 26 October 2026"
author: "ACCORD / CHC — draft for review"
date: "29 September 2026"
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
+0.62 °C in week 1 and +0.69 °C over the next 30 days. Eight days earlier the same two figures
were +1.03 and +0.86 °C. The forecast is lower than the previous issuance's at every horizon.

The western box is 0.76 to 0.92 °C above its 2006–2025 average and the eastern box is 0.14 to
0.20 °C above its own. Against the previous issuance the west is cooler at four of the five
horizons and warmer at week 2, while the east is warmer at all five.

Forecasts come from the ECMWF sub-seasonal ensemble, corrected against NOAA OI SST by linear
regression on the twenty past years of the same calendar date. At all ten box and window combinations the 80% interval on the gain
over 30-day persistence includes zero. The largest gain is in the west at week 2, at +0.14 in correlation, and its
80% interval runs from −0.00 to +0.34.

Ten windows have now verified, against four reported in the previous issuance. The dipole forecast is too
positive in eight of the ten, by a mean of 0.11 °C, and the errors run from −0.14 to +0.39 °C. The eastern correction makes the forecast worse in seven of ten, better
in two, and is indistinguishable in one.

## Forecast history

Each issuance forecasts four weekly windows, so successive runs cover overlapping calendar weeks
from different lead times. Plotted against valid date rather than lead time, the five runs to
date can be compared where they overlap. The forecast lies above the observed value at eight of
the ten windows that have verified. Runs are issued six to eight days apart, so their windows overlap
without generally coinciding. The differences between runs are small against the 80% intervals,
which span ±0.35 to ±0.64 °C.

![The dipole index from every issuance so far, each issuance a joined line shaded light to dark by date with the current run drawn heaviest, plotted at the mid-date of the week it forecasts. Black points are the observed value for each verified window, averaged where a week was scored from two issuances. Windows from successive runs overlap by six days, so neighbouring points describe nearly the same week at different lead times rather than successive weeks. The 30-day window is omitted because it spans the other four.](assets/fig0_history_2026-09-27.png){width=88%}

## Method

We take the ECMWF sub-seasonal forecast issued on 27 September 2026, which runs with 100 members
on a 1.5° grid, together with the matching reforecast for the same calendar date in each year
from 2006 to 2025, with 10 members each. Observations are NOAA OI SST v2.1 at 0.25° daily resolution.
Both are averaged over the two dipole boxes of Saji et al. (1999), the west at 50–70 °E and
10 °S–10 °N and the east at 90–110 °E and 10 °S to the equator, weighting each cell by the cosine of its
latitude.

The lead windows are days 1 to 7, 8 to 14, 15 to 21, 22 to 28 and 1 to 30. Temperature is filed
as a 24-hour mean, so day 1 is the day of issue and week 1 covers 27 September to 3 October.

For each box and window we fit a straight line of observed on forecast temperature across the
twenty reforecast years and apply it to this year's forecast. Regression is used rather than
quantile matching, which would pull values back inside the historical range. The 80% intervals
are Student's *t* prediction intervals from that regression, covering both the uncertainty in the
fitted line and the scatter of past residuals. They describe how wrong this method has been
in past years rather than the spread of the members, and they widen here because this year's
western forecast sits outside the training range. Accuracy figures are leave-one-year-out, and
reforecasts exist only for odd calendar days of the month. The calculation is reproduced by
`iod_pipeline.run("2026-09-27")`.

![**(a)** Forecast anomaly in each box with 80% prediction intervals. **(b)** The dipole from the corrected and uncorrected forecasts. The difference is a change in amplitude, not the removal of a bias. **(c,d)** Leave-one-year-out correlation against two persistence baselines, shaded by the gain over the 30-day one.](assets/fig1_combined_2026-09-27.png){width=82%}

## Results

| Horizon | Valid | West box | East box | Dipole |
|---|---|---|---|---|
| Week 1 | 27 Sep – 3 Oct | 28.84 °C (+0.76) | 28.28 °C (+0.14) | +0.62 ± 0.54 |
| Week 2 | 4 – 10 Oct | 29.21 °C (+0.92) | 28.35 °C (+0.17) | +0.75 ± 0.42 |
| Week 3 | 11 – 17 Oct | 29.20 °C (+0.82) | 28.47 °C (+0.16) | +0.66 ± 0.42 |
| Week 4 | 18 – 24 Oct | 29.21 °C (+0.81) | 28.65 °C (+0.20) | +0.61 ± 0.51 |
| Days 1–30 | 27 Sep – 26 Oct | 29.16 °C (+0.86) | 28.46 °C (+0.17) | +0.69 ± 0.36 |

The table gives absolute temperatures, with the departure from the 2006–2025 average in brackets
and the dipole with its 80% interval. The uncorrected model dipole is +0.64 to +0.77. The regression changes
amplitude rather than removing a bias, with western slopes of 0.86 to 0.92 and eastern slopes of
0.71 to 0.73. The eastern slopes sit further below one because model spread there is 1.16 to
1.26 times the observed spread, with in-sample correlation in the east of 0.84 to 0.91. Least squares sets the slope as
correlation times observed spread over model spread. In the west the model spread is 0.90 to 1.00 times the observed spread.

## Accuracy

The table gives leave-one-year-out correlation across the twenty reforecast years for the
forecast and for persistence. Persistence is the observed mean of the 31 days ending at issue,
carried through the same leave-one-year-out regression. The gain carries an 80% bootstrap
interval.

| | Week 1 | Week 2 | Week 3 | Week 4 | Days 1–30 |
|---|---|---|---|---|---|
| **West** forecast / persistence | 0.85 / 0.89 | 0.83 / 0.69 | 0.80 / 0.67 | 0.75 / 0.65 | 0.89 / 0.81 |
| gain | −0.05 (−0.12, +0.05) | +0.14 (−0.00, +0.34) | +0.13 (−0.04, +0.35) | +0.10 (−0.05, +0.22) | +0.07 (−0.01, +0.18) |
| **East** forecast / persistence | 0.82 / 0.85 | 0.88 / 0.86 | 0.81 / 0.76 | 0.80 / 0.72 | 0.89 / 0.85 |
| gain | −0.04 (−0.12, +0.03) | +0.01 (−0.06, +0.07) | +0.05 (−0.04, +0.14) | +0.08 (−0.02, +0.19) | +0.04 (−0.04, +0.10) |

The gain is the forecast's correlation minus persistence's, both measured leave-one-year-out.
At all ten box and window combinations the 80% interval on the gain includes zero, so no forecast
is more accurate than persistence by more than the uncertainty on that difference. Williams' test
of the difference between two correlations sharing the same observed series gives p between 0.26
and 0.81 across the ten combinations. The largest gain is the west at week 2, at +0.14 with an interval of
−0.00 to +0.34 and p of 0.26. At week 1 the forecast is less accurate than 30-day persistence in
both boxes.

The bootstrap interval on the gain was corrected for this issuance. It previously resampled the
predictors in sample while the gain it bracketed was measured out of sample, so the two described
different quantities.
Both are now out of sample, which widens the intervals. Counts of horizons reported as more accurate than
persistence in earlier issuances came from the uncorrected interval and may therefore overstate
how many were separable from noise.

![Corrected SST anomaly at every horizon, in °C against the 2006–2025 observed average. The western box is outlined in orange and the eastern in teal. Grey ocean marks cells where leave-one-year-out correlation falls below 0.4 and the forecast should not be relied on. Each cell is corrected by its own regression. Fields are interpolated for contouring, so the zero contour is placed by the interpolation rather than measured.](assets/fig3_maps_2026-09-27.png){width=80%}

## Verification record

| run | valid | forecast | observed | error | east raw err | east cal err |
|---|---|---|---|---|---|---|
| 31 Aug | 31 Aug – 6 Sep | +0.43 | +0.04 | +0.39 | −0.06 | −0.36 |
| 31 Aug | 7 – 13 Sep | +0.82 | +0.59 | +0.23 | +0.06 | −0.16 |
| 31 Aug | 14 – 20 Sep | +0.86 | +0.80 | +0.06 | +0.25 | +0.06 |
| 31 Aug | 21 – 27 Sep | +0.73 | +0.87 | −0.14 | +0.03 | −0.07 |
| 7 Sep | 7 – 13 Sep | +0.76 | +0.59 | +0.17 | −0.00 | −0.21 |
| 7 Sep | 14 – 20 Sep | +0.88 | +0.80 | +0.08 | +0.20 | +0.02 |
| 7 Sep | 21 – 27 Sep | +0.73 | +0.87 | −0.14 | +0.06 | −0.06 |
| 13 Sep | 13 – 19 Sep | +0.94 | +0.72 | +0.22 | +0.00 | −0.15 |
| 13 Sep | 20 – 26 Sep | +1.13 | +0.93 | +0.20 | −0.12 | −0.17 |
| 19 Sep | 19 – 25 Sep | +1.03 | +0.99 | +0.04 | +0.01 | −0.07 |

All ten errors are inside their 80% intervals. Three weeks are scored from two initialisations each, so the ten rows
cover seven distinct calendar weeks and are not ten independent tests. Eight of the ten errors are positive, and averaging the duplicated weeks first gives six
of seven positive with a mean of +0.14 °C. Both negative errors are the same week, 21 to
27 September, counted twice. The eastern correction is worse than leaving the model uncorrected
in seven of the ten, better in two, and indistinguishable in one at a margin of 0.002 °C. The
uncorrected eastern forecast is also in error, by up to 0.25 °C. Observations are
revised for about two weeks after real time, which moved four of the previously reported errors
by up to 0.03 °C.

## Limitations

- **The eastern correction** is worse than no correction in seven of the ten verified windows,
  better in two and indistinguishable in one. Read the eastern box and the dipole as upper
  estimates.
- **The gain over persistence** depends on which persistence is used, and at week 1 the forecast
  is less accurate than 30-day persistence in both boxes.
- **The baseline** is 2006–2025 rather than 1991–2020, and is computed on a different SST analysis from BoM's,
  so these anomalies are not comparable with published dipole values.
- **Twenty years** is a short training record. The western forecast lies 2.2 to 2.8 standard
  deviations beyond the training mean, so the regression is extrapolating.
- **Separate correction** of the two boxes before differencing changes the dipole's amplitude in
  a direction that varies by window. In this run the amplitude is damped at every window.
- **The intervals** come from past errors, not the ensemble spread. Leave-one-year-out coverage
  across all twenty years and ten combinations is 79.5%, consistent with the 80% target on a
  sample of twenty years.
- **Box and map numbers** differ. In this run the map is 0.05 to 0.09 °C cooler than the box in
  the west at every window, and within 0.02 °C in the east. The table values are the ones to quote.
- **One model** only, the ECMWF sub-seasonal ensemble.
- **Persistence** is given a one-day advantage, because it uses observations through the day of
  issue.
