---
title: "Indian Ocean SST and Dipole Outlook"
subtitle: "Forecast issued 13 September 2026 · covering 13 September – 12 October 2026"
author: "ACCORD / CHC — draft for review"
date: "17 September 2026"
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

A positive Indian Ocean Dipole is forecast at every horizon over the coming month, and it has
strengthened with each successive issuance. The dipole index reaches **+0.94 °C in week 1 and
+1.13 °C in week 2, averaging +1.02 °C over the next 30 days** — up from +0.84 °C a week
earlier and +0.72 °C a fortnight earlier. Values above +1.0 °C place this in moderate positive
territory.

The physical signature has completed. The western box has been anomalously warm throughout,
+0.90 to +1.07 °C above its 2006–2025 average, and the **eastern box has now turned slightly
cool** (−0.00 to −0.07 °C, having been +0.08 to +0.16 °C a week ago). A warm west against a
cooling east is the canonical positive-dipole pattern, and its emergence — rather than the
magnitude alone — is the substantive development in this issuance.

Forecasts are produced from the ECMWF sub-seasonal ensemble, corrected against NOAA OI SST by
linear regression fitted on the twenty reforecast years attached to the same calendar date.
Skill is assessed leave-one-year-out and against persistence. On the accumulated evidence of
three issuances, the forecast's demonstrable advantage over persistence lies in the **eastern
box at weeks 2 to 4**, where the gain is consistently positive and clears an 80% interval at
four of five horizons this run; the western box has not been separable from persistence in any
issuance.

**Two cautions qualify the headline.** The dipole has been forecast too positive in all three
verified windows so far, by +0.20 to +0.42 °C. And the eastern calibration has degraded rather
than improved the forecast in each of those windows — the uncorrected model value has been
within 0.04 °C every time, while the corrected value has been 0.18 to 0.32 °C too cool. Because
the dipole is the west-minus-east difference, an over-cooled east inflates it. The values above
should therefore be read as an upper estimate.

## Method

**Model.** ECMWF S2S extended-range ensemble, issued 13 September 2026: 100 members, 46 daily
steps, 1.5° grid, from the ECMWF Data Store (`ecds.ecmwf.int`), dataset `s2s-forecasts`,
variable `sea_surface_temperature`. **Training:** the reforecast set for the same calendar
date (`s2s-reforecasts`) — the same run for 13 September in each of 2006–2025, 10 members
each. **Observations:** NOAA OI SST v2.1, 0.25° daily, from NOAA PSL.
**Boxes:** Saji et al. (1999), west 50–70 °E / 10 °S–10 °N and east 90–110 °E / 10 °S–0,
area-weighted by cosine of latitude on each dataset's own grid.

**Windows.** Days 1–7, 8–14, 15–21, 22–28 and 1–30. S2S SST is filed as a 24-hour mean, so
day 1 is the **day of the 00Z issuance**, not the day after: week 1 verifies 13 to 19
September. *Note that an independent calculation of the same initialisation labels lead day 1
as the 14th, following cfgrib's `valid_time`, which marks the end of the 24-hour averaging
period rather than its start. The two conventions differ by a day and should be reconciled
before values are compared closely.*

**Correction.** Per box and window, ordinary least squares of observed on forecast temperature
across the twenty reforecast years, applied to this year's forecast. Regression rather than
quantile matching, because a straight line continues a warming trend outside the historical
range while quantile matching pulls values back inside it.

**Uncertainty.** An 80% prediction interval on Student's *t*, 18 degrees of freedom, carrying
both fitted-line uncertainty and residual scatter — not the naive `1.28 × residual sd`,
because **this forecast sits 2.3–3.2 standard deviations above the training mean in the
west**, where omitting the extrapolation term would understate the interval by 20–28%. It
reflects how wrong the method has been on past years, not how much this week's 100 members
disagree. **Testing** is leave-one-year-out throughout.

**Issuance dates.** ECMWF files extended-range reforecasts on **odd calendar days of the
month** — verified this week: the 11th, 13th and 15th each have a full 20-year suite, the
12th and 16th have none. **Reproducing:** `iod_pipeline.run("2026-09-13")`.

![**(a)** Forecast anomaly in each box, 80% prediction intervals. **(b)** The dipole, calibrated and raw — the gap is the regression's amplitude correction, not bias removal. **(c,d)** Leave-one-year-out correlation against two persistence baselines; shading is the gain over the harder 30-day one.](assets/fig1_combined_2026-09-13.png){width=92%}

## Results

| Horizon | Valid | West box | East box | Dipole |
|---|---|---|---|---|
| Week 1 | 13 – 19 Sep | 28.72 °C (+0.94) | 28.09 °C (−0.00) | +0.94 ± 0.49 |
| Week 2 | 20 – 26 Sep | 28.98 °C (+1.07) | 28.12 °C (−0.06) | +1.13 ± 0.56 |
| Week 3 | 27 Sep – 3 Oct | 29.02 °C (+0.95) | 28.08 °C (−0.06) | +1.01 ± 0.49 |
| Week 4 | 4 – 10 Oct | 29.19 °C (+0.90) | 28.11 °C (−0.07) | +0.97 ± 0.49 |
| Days 1–30 | 13 Sep – 12 Oct | 29.01 °C (+0.97) | 28.11 °C (−0.05) | +1.02 ± 0.41 |

Absolute temperatures; brackets are the departure from the **2006–2025** average for the same
dates, dipole in °C with its 80% interval. That baseline is the reforecast period, not the
1991–2020 climatology BoM, CPC and NOAA use — **these anomalies are not directly comparable
with the dipole values those centres publish.**

The raw model dipole is +0.77 to +1.04. That difference is **the regression's amplitude
correction, not bias removal**: least squares with an intercept preserves the mean, so
constant bias cancels on both sides. What changes is amplitude — the west is stretched
(slope 0.95–1.22) and the east shrunk (0.66–0.70). Given the verification record below, that
eastern shrinkage remains the part to distrust.

## Cross-check against an independent calculation

An independent calculation of the same initialisation, performed through a separate pipeline,
provides a check on the box means. Comparing on its lead indexing, raw model anomaly against
the reforecast-mean climatology:

| | this report | independent | difference |
|---|---|---|---|
| West, week 1 | +0.767 | +0.773 | −0.006 |
| West, days 1–30 | +0.868 | +0.880 | −0.012 |
| East, week 1 | −0.003 | −0.050 | +0.047 |
| East, days 1–30 | −0.072 | −0.130 | +0.058 |

The western agreement — within 0.024 °C at every horizon — corroborates the box definition,
area weighting and lead handling. The eastern offset of 0.05–0.07 °C is systematic and most
plausibly reflects the climatology period: 2006–2024 in the independent calculation against
2006–2025 here. It propagates directly into the dipole, which is 0.05–0.09 °C lower in this
report throughout, and is worth reconciling.

## Accuracy

Leave-one-year-out correlation over the twenty reforecast years against persistence — "the
ocean stays as it is at issue". Gains carry an 80% bootstrap interval.

| | Week 1 | Week 2 | Week 3 | Week 4 | Days 1–30 |
|---|---|---|---|---|---|
| **West** — model | 0.87 | 0.78 | 0.86 | 0.79 | 0.89 |
| persistence 30 d / 14 d | 0.76 / 0.85 | 0.74 / 0.77 | 0.78 / 0.80 | 0.63 / 0.59 | 0.80 / 0.83 |
| gain (80% interval) | +0.11 (−0.03, +0.24) | +0.05 (−0.07, +0.21) | +0.07 (−0.04, +0.17) | +0.16 (−0.01, +0.27) | +0.08 (−0.00, +0.18) |
| **East** — model | 0.82 | 0.83 | 0.86 | 0.87 | 0.88 |
| persistence 30 d / 14 d | 0.68 / 0.79 | 0.58 / 0.67 | 0.59 / 0.68 | 0.71 / 0.75 | 0.69 / 0.77 |
| gain (80% interval) | +0.14 (−0.04, +0.27) | **+0.25 (+0.00, +0.37)** | **+0.26 (+0.04, +0.37)** | **+0.15 (+0.03, +0.22)** | **+0.19 (+0.02, +0.29)** |

**The east clears zero at four of five horizons this run**, the strongest showing in three
issuances. Set against the previous two issuances — week 2 in both boxes on 31 August, weeks 4 and
days 1–30 in the east on 7 September — the pattern across runs is that **the eastern gain at
weeks 2–4 is consistently positive and often significant, while the west has never cleared
zero in any run**. Which specific horizons clear still moves between issuances, so read the
consistency rather than any single interval.

![Corrected SST anomaly at every horizon (°C vs the 2006–2025 observed average). Boxes: western (orange) and eastern (teal); land in tan. Grey ocean is where leave-one-year-out correlation falls below 0.4 and the forecast should not be relied on. Each cell is corrected by its own regression, observations averaged from 0.25° to the model's 1.5° grid. Fields are cubic-refined for contouring — presentational only, and the zero contour in particular is placed by the interpolation rather than measured.](assets/fig3_maps_2026-09-13.png){width=88%}

## Verification record

Week 1 of this run (13–19 September) is not yet complete. Three windows from earlier
issuances have verified:

| window | forecast | observed | error | east: raw vs calibrated |
|---|---|---|---|---|
| 31 Aug – 6 Sep | +0.43 | +0.01 | +0.42 | raw exact, calibrated −0.32 |
| 7 – 13 Sep (from 31 Aug run) | +0.82 | +0.56 | +0.26 | raw +0.04, calibrated −0.18 |
| 7 – 13 Sep (from 7 Sep run) | +0.76 | +0.56 | +0.20 | raw −0.02, calibrated −0.23 |

Every error is inside its 80% interval, and the shorter lead beat the longer one on the same
week. But two patterns now hold across all three: **the dipole forecast runs too positive**,
and **the eastern calibration makes the forecast worse** — the raw eastern value has been
within 0.04 °C every time, while the calibrated value has been 0.18–0.32 °C too cool. Since
the dipole is west minus east, a too-cool east inflates it. Given this run forecasts the
strongest dipole yet, that bias is the main reason for caution.

## Limitations

- **The eastern calibration has hurt in all three verified windows**, by 0.18–0.32 °C, while
  the raw eastern value was within 0.04 °C each time. Read the eastern box and the dipole as
  upper estimates; revisiting the eastern shrinkage is the clearest improvement available.
- **The dipole forecast has run too positive in every verified window** (+0.42, +0.26, +0.20).
- **Which horizons clear significance moves between issuances.** The durable finding across
  three runs is the eastern gain at weeks 2–4; the west has never cleared.
- **The baseline is 2006–2025, not 1991–2020**, and on a different SST analysis from BoM's, so
  these anomalies are not directly comparable with published dipole values. Our eastern
  climatology also differs from CHC's by one year, worth 0.05–0.07 °C.
- **Twenty years is a short training record**, and this forecast extrapolates 2.3–3.2 standard
  deviations beyond the training mean in the west.
- **The dipole is built from separately calibrated poles**, which amplifies it relative to
  regressing the observed dipole directly on the model dipole.
- **The interval is historical**, not ensemble-based; a version using the 100 members' spread
  is the obvious next step.
- **Persistence is given a one-day advantage**, so the comparisons are conservative.
- **Map and box numbers differ by 0.15–0.35 °C**: quote the table for a box.
- **One model only**, ECMWF S2S.
