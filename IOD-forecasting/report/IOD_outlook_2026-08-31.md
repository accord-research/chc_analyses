---
title: "Indian Ocean SST and Dipole Outlook"
subtitle: "Forecast issued 31 August 2026 · covering 1–30 September 2026"
author: "ACCORD / CHC — draft for review"
date: "8 September 2026"
geometry: "margin=1.7cm"
header-includes:
  - \usepackage{titling}
  - \usepackage{graphicx}
  - \pretitle{\begin{center}\includegraphics[width=0.58\textwidth]{assets/logo_strip.png}\\[1.0em]\LARGE\bfseries}
  - \posttitle{\par\end{center}\vskip 0.3em}
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

This is a forecast of sea surface temperature in the two Indian Ocean Dipole boxes, and of
the dipole itself, for the next 30 days and for each of the next four weeks. It uses the
ECMWF sub-seasonal (S2S) forecast, corrected against NOAA OI SST by linear regression.

**The forecast is for a positive Indian Ocean Dipole at every horizon.** The dipole index
is +0.42 °C in week 1, rising to about +0.84 °C in weeks 2 and 3, and +0.73 °C averaged over
the next 30 days. This is driven almost entirely by a warm western box: western Indian Ocean
temperature is forecast at 28.4–28.8 °C, which is 0.7–1.0 °C above its 2006–2025 average for
these dates. The eastern box is close to normal, 0.1–0.3 °C above average.

**The forecast is more accurate than persistence at every horizon, and the margin grows with
lead time.** Tested on twenty years of past forecasts, the model's correlation with what
actually happened is 0.72–0.91, against 0.31–0.85 for simply assuming the ocean stays as it
is now. In the eastern box at weeks 3 and 4, persistence falls to about 0.31 while the model
holds 0.77–0.82. At week 1 the model is only slightly better than persistence, so the useful
range of this product is weeks 2 to 4.

## Method

**Forecast model.** ECMWF S2S extended-range ensemble, issued 31 August 2026: 100 members,
46 daily steps, 1.5° grid. From the ECMWF Data Store (`ecds.ecmwf.int`), dataset
`s2s-forecasts`, variable `sea_surface_temperature`.

**Training data.** The reforecast set for the same calendar date (`s2s-reforecasts`) — the
same run for 31 August in each of the twenty years 2006–2025, 10 members each. The
correction is fitted on these twenty past forecasts.

**Observations.** NOAA OI SST v2.1, 0.25° daily, from NOAA PSL — the record CHC uses.

**Boxes.** Saji et al. (1999) dipole boxes. West 50–70 °E, 10 °S–10 °N; east 90–110 °E,
10 °S–0. Averages are area-weighted by cosine of latitude on each dataset's own grid, so no
regridding is needed to compare them.

**Lead windows.** Week 1 is forecast days 1–7, then 8–14, 15–21, 22–28, and 1–30. Day 1 is
the first full day after the 00Z issuance.

**Correction.** For each box and window separately, a straight line fitted by ordinary least
squares — observed against forecast temperature across the twenty reforecast years — then
applied to this year's forecast. Regression rather than quantile matching, because a straight
line continues a warming trend outside the historical range while quantile matching pulls
values back inside it.

**Uncertainty and testing.** The 80% interval is the spread of the regression's own errors
over the twenty training years: how wrong this method has been, not how much this week's 100
members disagree. All accuracy figures are leave-one-year-out — the line refitted without each
year, then used to predict it — so nothing quoted is measured on data used to fit it.

**Reproducing.** `iod_pipeline.run("2026-08-31")` in `experiments/IOD-forecasting/`; the date
is the only input. Data via `acmadDL`, analysis via `africas2s`.

![**(a)** Forecast temperature anomaly in each box, with 80% intervals. **(b)** The dipole index against both the observed climatology and the model's own. **(c,d)** Correlation between forecast and observation over twenty past years, leave-one-year-out; grey is persistence — assuming the ocean stays as it is at issue — and the shaded gap is what the model adds.](assets/fig1_combined.png){width=100%}

## Results

| Horizon | Valid dates | West box | East box | Dipole |
|---|---|---|---|---|
| Week 1 | 1–7 Sep | 28.35 °C (+0.69) | 28.35 °C (+0.27) | +0.42 |
| Week 2 | 8–14 Sep | 28.77 °C (+1.05) | 28.32 °C (+0.21) | +0.84 |
| Week 3 | 15–21 Sep | 28.81 °C (+0.99) | 28.28 °C (+0.16) | +0.84 |
| Week 4 | 22–28 Sep | 28.81 °C (+0.85) | 28.27 °C (+0.10) | +0.75 |
| Days 1–30 | 1–30 Sep | 28.70 °C (+0.89) | 28.29 °C (+0.17) | +0.73 |

Temperatures are absolute; brackets are the departure from the 2006–2025 average for the same
dates, dipole in °C. Against the model's own climatology the dipole is smaller (+0.33 to +0.64); the difference
between the two is the model's bias at each lead, which the regression removes. Both are
shown because neither is more correct — the observed version asks how warm the ocean is
against its own recent history, the model version how warm against what this model usually
predicts at this range.

## Accuracy

| | Week 1 | Week 2 | Week 3 | Week 4 | Days 1–30 |
|---|---|---|---|---|---|
| West — model | 0.88 | 0.87 | 0.76 | 0.72 | 0.82 |
| West — persistence | 0.85 | 0.66 | 0.60 | 0.64 | 0.74 |
| East — model | 0.88 | 0.91 | 0.82 | 0.77 | 0.90 |
| East — persistence | 0.83 | 0.58 | 0.33 | 0.31 | 0.57 |

Typical error is 0.16–0.28 °C (west) and 0.21–0.38 °C (east).

![Corrected SST anomaly at every horizon (°C vs the 2006–2025 observed average). Boxes: western (orange) and eastern (teal) poles; land in tan. Grey ocean cells are where leave-one-year-out correlation falls below 0.4 and the forecast should not be relied on — note how that area grows from week 1 to week 4. Each cell is corrected by its own regression; observations are averaged from 0.25° to the model's 1.5° grid.](assets/fig3_maps.png){width=100%}

## Limitations

- **Week 1 adds little** — at that range assuming no change is nearly as accurate, so the
  value of this product is weeks 2 to 4.
- **Twenty years is a short training record**, so one unusual year moves a correction. This
  follows from how ECMWF produces reforecasts, not from a choice we made.
- **The interval is historical**, not ensemble-based; a version using the 100 members'
  spread is the obvious next step.
- **Map and box numbers differ by 0.1–0.3 °C** — correcting each cell then averaging is not
  the same calculation as correcting the box average; quote the table for a box.
- **One model only**, ECMWF S2S. GEFSv12 was considered and set aside.

