---
title: "Indian Ocean SST and Dipole Outlook"
subtitle: "Forecast issued 11 October 2026, covering 11 October to 9 November 2026"
author: "ACCORD / CHC — draft for review"
date: "13 October 2026"
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
+0.50 °C in week 1 and +0.66 °C over the next 30 days. Two weeks earlier the same two figures
were +0.62 and +0.69 °C. This issuance and the previous one are fourteen days apart, so two of
their windows cover identical dates. Over 11 to 17 October the dipole is forecast at +0.50 °C
against +0.66 °C two weeks ago, and over 18 to 24 October at +0.58 °C against +0.61 °C.

The western box is 0.66 to 1.01 °C above its 2006–2025 average and the eastern box is 0.12 to
0.18 °C above its own. On the two windows the two issuances share, the west is cooler by 0.16
and 0.08 °C and the east is within 0.06 °C.

Forecasts come from the ECMWF sub-seasonal ensemble, corrected against NOAA OI SST by linear
regression on the twenty past years of the same calendar date. At four of the ten box and window
combinations the 80% interval on the gain in leave-one-year-out correlation over 30-day
persistence lies entirely above zero, and all four are in the west. At the previous issuance
none of the ten did. The counts at the four issuances before 27 September came from an interval
that has since been corrected and are not comparable with these two.

Twenty windows have now verified, against ten reported in the previous issuance. The dipole
forecast is too positive in seventeen of the twenty, by a mean of 0.16 °C, and the errors run
from −0.12 to +0.39 °C. The eastern correction
leaves the forecast further from the observation than the uncorrected model in fifteen of the
twenty windows, closer in three, and within 0.01 °C either way in two.

## Forecast history

Each issuance forecasts four weekly windows, so successive runs cover overlapping calendar weeks
from different lead times. The figure plots all six runs against valid date rather than
lead time. Runs are issued six to fourteen days apart. Where the gap is an exact multiple of
seven days the windows coincide, and otherwise they overlap in part. Seven weekly windows have
been forecast by more than one issuance, and those pairs differ by 0.001 to 0.383 °C against
80% intervals spanning ±0.31 to ±0.64 °C.

![The dipole index from every issuance so far, each issuance a joined line shaded light to dark by date with the current run drawn heaviest, plotted at the mid-date of the week it forecasts. Black points are the observed value for each verified window, averaged where a week was scored from more than one issuance. Windows from successive runs overlap, so neighbouring points describe nearly the same week at different lead times rather than successive weeks. The 30-day window is omitted because it spans the other four.](assets/fig0_history_2026-10-11.png){width=88%}

## Method

We take the ECMWF sub-seasonal forecast issued on 11 October 2026, which runs with 100 members
on a 1.5° grid, together with the matching reforecast for the same calendar date in each year
from 2006 to 2025, with 10 members each. Observations are NOAA OI SST v2.1 at 0.25° daily
resolution. Both are averaged over the two dipole boxes of Saji et al. (1999), the west at
50–70 °E and 10 °S–10 °N and the east at 90–110 °E and 10 °S to the equator, weighting each cell
by the cosine of its latitude.

The lead windows are days 1 to 7, 8 to 14, 15 to 21, 22 to 28 and 1 to 30. Temperature is filed
as a 24-hour mean, so day 1 is the day of issue and week 1 covers 11 to 17 October.

For each box and window we fit a straight line of observed on forecast temperature across the
twenty reforecast years and apply it to this year's forecast. Regression is used rather than
quantile matching, which would pull values back inside the historical range. The 80% intervals
are Student's *t* prediction intervals from that regression, covering both the uncertainty in
the fitted line and the scatter of past residuals. They describe how wrong this method has been
in past years rather than the spread of the members. Accuracy figures are leave-one-year-out.
Reforecasts exist only for odd calendar days of the month. The calculation is reproduced by
`iod_pipeline.run("2026-10-11")`.

![**(a)** Forecast anomaly in each box with 80% prediction intervals. **(b)** The dipole from the corrected and uncorrected forecasts. The difference is a change in amplitude, not the removal of a bias. **(c,d)** Leave-one-year-out correlation against two persistence baselines, shaded by the gain over the 30-day one.](assets/fig1_combined_2026-10-11.png){width=82%}

## Results

| Horizon | Valid | West box | East box | Dipole |
|---|---|---|---|---|
| Week 1 | 11 – 17 Oct | 29.04 °C (+0.66) | 28.48 °C (+0.16) | +0.50 ± 0.31 |
| Week 2 | 18 – 24 Oct | 29.13 °C (+0.73) | 28.60 °C (+0.14) | +0.58 ± 0.47 |
| Week 3 | 25 – 31 Oct | 29.47 °C (+0.96) | 28.72 °C (+0.12) | +0.83 ± 0.54 |
| Week 4 | 1 – 7 Nov | 29.62 °C (+1.01) | 28.80 °C (+0.18) | +0.83 ± 0.55 |
| Days 1–30 | 11 Oct – 9 Nov | 29.31 °C (+0.82) | 28.66 °C (+0.16) | +0.66 ± 0.36 |

The table gives absolute temperatures, with the departure from the 2006–2025 average in brackets
and the dipole with its 80% interval. Those departures are not comparable with the dipole values
BoM and NOAA publish, which use a 1991–2020 baseline and a different SST analysis.

The uncorrected model dipole is +0.65 to +0.78 °C. Least squares with an intercept is
mean-preserving, so the difference between the corrected and uncorrected dipoles is a change in
amplitude rather than the removal of a bias. Western slopes run from 0.73 to 1.08 and eastern
slopes from 0.65 to 0.82. Least squares sets the slope as correlation times observed spread over
model spread. In the east the model spread is 1.08 to 1.29 times the observed spread, which puts
every eastern slope below one. In the west the ratio runs from 0.81 to 1.20 and the slopes fall
on both sides of one.

## Accuracy

The table gives leave-one-year-out correlation across the twenty reforecast years for the
forecast and for persistence. Persistence is the observed mean of the 30 days before issue and
the issue day itself, carried through the same leave-one-year-out regression. The gain carries an
80% bootstrap interval.

| | Week 1 | Week 2 | Week 3 | Week 4 | Days 1–30 |
|---|---|---|---|---|---|
| **West** forecast / persistence | 0.85 / 0.77 | 0.86 / 0.72 | 0.79 / 0.58 | 0.84 / 0.54 | 0.90 / 0.75 |
| gain | +0.08 (−0.07, +0.25) | +0.14 (+0.01, +0.21) | +0.20 (+0.06, +0.31) | +0.30 (+0.16, +0.50) | +0.15 (+0.07, +0.23) |
| **East** forecast / persistence | 0.85 / 0.76 | 0.83 / 0.75 | 0.84 / 0.80 | 0.77 / 0.73 | 0.86 / 0.80 |
| gain | +0.09 (−0.02, +0.21) | +0.08 (−0.02, +0.21) | +0.04 (−0.03, +0.12) | +0.04 (−0.04, +0.15) | +0.06 (−0.01, +0.16) |

The gain is the forecast's correlation minus persistence's, both measured leave-one-year-out. At
four of the ten box and window combinations the interval on the gain lies entirely above zero,
meaning the forecast is more accurate than 30-day persistence by more than the uncertainty on
that difference. All four are in the west, at weeks 2, 3 and 4 and over days 1 to 30. The
largest is the west at week 4, at +0.30 in correlation with an interval from +0.16 to +0.50.
Williams' test of the difference between two correlations sharing the same observed series gives
p between 0.02 and 0.66 across the ten combinations.

Which combinations separate from persistence moves between issuances. At the previous issuance
none of the ten did, and at 13 September four did and all four were in the east. The counts from
issuances before 27 September came from a bootstrap that resampled the predictors in sample while
the gain it bracketed was measured out of sample, so those intervals bracketed a different
quantity and are not comparable with these two. Whether they ran narrower cannot be determined
from the published files, where the mean interval width was larger at three of the four earlier
issuances. The correction may imply that the separation counts reported before 27 September may
overstate the evidence that the forecast beats persistence.

The gain depends on which persistence baseline is used. The 30-day baseline in the table scores
the lowest leave-one-year-out correlation of the three, below the 14-day baseline at all ten
combinations and the lowest of the three at nine, with a mean correlation of 0.72 against 0.79
at 14 days and 0.81 at 7 days. Against the 14-day baseline the interval on the gain lies entirely
above zero at two of the ten combinations, and against the 7-day baseline at three, with one
combination lying entirely below zero.

![Corrected SST anomaly at every horizon, in °C against the 2006–2025 observed average. The western box is outlined in orange and the eastern in teal. Grey ocean marks cells where leave-one-year-out correlation falls below 0.4. Each cell is corrected by its own regression. Fields are interpolated for contouring, so the zero contour is placed by the interpolation rather than measured.](assets/fig3_maps_2026-10-11.png){width=80%}

## Verification record

| run | valid | forecast | observed | error | east raw err | east cal err |
|---|---|---|---|---|---|---|
| 31 Aug | 31 Aug – 6 Sep | +0.43 | +0.04 | +0.39 | −0.06 | −0.36 |
| 31 Aug | 7 Sep – 13 Sep | +0.82 | +0.59 | +0.23 | +0.06 | −0.16 |
| 31 Aug | 14 Sep – 20 Sep | +0.86 | +0.70 | +0.16 | +0.14 | −0.05 |
| 31 Aug | 21 Sep – 27 Sep | +0.73 | +0.85 | −0.12 | +0.04 | −0.06 |
| 31 Aug | 31 Aug – 29 Sep | +0.72 | +0.55 | +0.17 | +0.03 | −0.18 |
| 7 Sep | 7 Sep – 13 Sep | +0.76 | +0.59 | +0.17 | −0.00 | −0.21 |
| 7 Sep | 14 Sep – 20 Sep | +0.88 | +0.70 | +0.18 | +0.09 | −0.09 |
| 7 Sep | 21 Sep – 27 Sep | +0.73 | +0.85 | −0.12 | +0.07 | −0.05 |
| 7 Sep | 28 Sep – 4 Oct | +0.87 | +0.64 | +0.23 | −0.09 | −0.29 |
| 7 Sep | 7 Sep – 6 Oct | +0.84 | +0.69 | +0.16 | +0.01 | −0.17 |
| 13 Sep | 13 Sep – 19 Sep | +0.94 | +0.65 | +0.29 | −0.08 | −0.23 |
| 13 Sep | 20 Sep – 26 Sep | +1.13 | +0.90 | +0.23 | −0.14 | −0.20 |
| 13 Sep | 27 Sep – 3 Oct | +1.01 | +0.67 | +0.34 | −0.26 | −0.40 |
| 13 Sep | 4 Oct – 10 Oct | +0.97 | +0.73 | +0.24 | −0.08 | −0.27 |
| 13 Sep | 13 Sep – 12 Oct | +1.02 | +0.75 | +0.28 | −0.12 | −0.26 |
| 19 Sep | 19 Sep – 25 Sep | +1.03 | +0.93 | +0.11 | −0.05 | −0.13 |
| 19 Sep | 26 Sep – 2 Oct | +0.81 | +0.67 | +0.14 | −0.04 | −0.22 |
| 19 Sep | 3 Oct – 9 Oct | +0.79 | +0.68 | +0.11 | +0.12 | −0.13 |
| 27 Sep | 27 Sep – 3 Oct | +0.62 | +0.67 | −0.04 | +0.01 | −0.20 |
| 27 Sep | 4 Oct – 10 Oct | +0.75 | +0.73 | +0.02 | +0.23 | −0.03 |

All twenty errors are inside their 80% intervals. The twenty rows cover fifteen distinct calendar
spans, because five spans are scored from two initialisations each, so they are not twenty
independent tests. Averaging the five duplicated spans first gives fourteen of the
fifteen spans positive, with a mean error of +0.18 °C. The uncorrected eastern forecast is in
error by up to 0.26 °C.

Seven of the ten rows carried in the previous issuance have changed, by up to 0.095 °C on 14 to
20 September. Observations are revised for about two weeks after real time, and those rows were
scored when the days in question were still inside that window. The verification code was also
changed for this issuance. It previously scored each window against a cached observed series
that was never refreshed, which stopped at 27 September and left ten completed windows unscored.
That cache also held the pre-revision values, so the 0.095 °C is one revision surfaced by the
cache rather than a second effect added to it. All windows are now scored against one series
retrieved for this run.

Ten of the twenty rows verify to a date on or after 29 September, inside the revision window, so
the errors quoted for them will change. On the ten rows the
two issuances share, revision moved the mean error from +0.11 to +0.15 °C.

## Limitations

- **The eastern correction** leaves the forecast further from the observation than no correction
  in fifteen of the twenty verified windows, closer in three, and within 0.01 °C either way in
  two. The eastern box and the dipole are likely to be upper estimates.
- **Positive bias.** The forecast lies above the observation in seventeen of the twenty verified
  windows, by a mean of 0.16 °C and by up to 0.39 °C.
- **The gain over persistence** depends on which persistence is used. The table above uses the
  30-day baseline, where four of ten combinations separate from persistence. Against the 14-day
  baseline two do and against the 7-day baseline three do, with one combination lying entirely
  below zero.
- **Which combinations separate.** The set of box and window combinations whose gain interval
  lies entirely above zero changes between issuances. At this issuance all four are in the west,
  and at 13 September all four were in the east.
- **The baseline** is 2006–2025 rather than 1991–2020, and is computed on a different SST
  analysis from BoM's, so these anomalies are not comparable with published dipole values.
- **Twenty years** is a short training record. The western forecast lies 2.0 to 2.8 standard
  deviations beyond the training mean, so the regression is extrapolating.
- **Separate correction** of the two boxes before differencing changes the dipole's amplitude in
  a direction that varies by window. At weeks 1 and 2 the amplitude is damped and at weeks 3 and
  4 it is increased.
- **The intervals** come from past errors, not the ensemble spread. Leave-one-year-out coverage
  of the box intervals across all twenty years and ten combinations is 77.5%, against the 80%
  target. The dipole interval is built separately and is not covered by that check. All twenty
  verified dipole errors fall inside it, where sixteen would be expected at 80%, and the mean
  error is 0.38 of the interval half-width, which is consistent with the dipole interval being
  too wide.
- **Persistence** uses the observed state up to and including the day of issue, which the
  forecast does not have.
- **Box and map numbers.** The map anomaly is 0.20 °C cooler to 0.02 °C warmer than the box mean
  in the west and 0.00 to 0.05 °C warmer in the east. The table gives the box means computed on
  the native grid.
- **One model** only, with no multi-model comparison.
