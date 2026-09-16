---
title: "Indian Ocean SST and Dipole Outlook"
subtitle: "Forecast issued 7 September 2026 · covering 7 September – 6 October 2026"
author: "ACCORD / CHC — draft for review"
date: "15 September 2026"
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
(S2S) forecast corrected against NOAA OI SST by linear regression. This is the second
issuance; the first covered 31 August – 29 September.

**A positive dipole at every horizon, stronger than a week ago**: +0.76 °C in week 1, +0.88
in week 2, +0.84 over the next 30 days — up 0.06 to 0.33 on the equivalent horizons of the
31 August run. It remains driven almost entirely by a warm western box, now 0.8–1.0 °C above
its 2006–2025 average; the eastern box is near normal, +0.08 to +0.16.

**Two verifications now exist, and both say the same thing: the forecast runs too positive.**
The 7–13 September window has been observed. This run forecast +0.76 for it and the ocean
delivered **+0.56**; the previous run, forecasting the same week two weeks ahead, said +0.82.
Errors of +0.20 and +0.26, both inside their intervals, both in the same direction — and the
same direction as the first verification (+0.42 on 31 August – 6 September). Three windows,
three over-forecasts of the dipole.

**The eastern calibration is actively hurting, twice in a row.** In week 1 the raw model put
the eastern box at 28.47 against 28.49 observed — near exact — while the calibration moved it
to 28.27, an error of −0.23. The previous run did the same thing. A shrinkage slope of
0.66–0.74 estimated from twenty years is being applied when the model did not need shrinking.
**Treat the eastern box, and therefore the dipole, as an upper estimate.**

## Method

**Model.** ECMWF S2S extended-range ensemble, issued 7 September 2026: 100 members, 46 daily
steps, 1.5° grid, from the ECMWF Data Store (`ecds.ecmwf.int`), dataset `s2s-forecasts`,
variable `sea_surface_temperature`. **Training:** the reforecast set for the same calendar
date (`s2s-reforecasts`) — the same run for 7 September in each of 2006–2025, 10 members each.
**Observations:** NOAA OI SST v2.1, 0.25° daily, from NOAA PSL — the record CHC uses.
**Boxes:** Saji et al. (1999), west 50–70 °E / 10 °S–10 °N and east 90–110 °E / 10 °S–0,
area-weighted by cosine of latitude on each dataset's own grid.

**Windows.** Days 1–7, 8–14, 15–21, 22–28 and 1–30. S2S SST is filed as a 24-hour mean, so
day 1 is the **day of the 00Z issuance**, not the day after: week 1 verifies 7 to 13
September, and the 30-day window includes the issuance day, whose ocean state is already
partly known.

**Correction.** Per box and window, ordinary least squares of observed on forecast temperature
across the twenty reforecast years, applied to this year's forecast. Regression rather than
quantile matching, because a straight line continues a warming trend outside the historical
range while quantile matching pulls values back inside it.

**Uncertainty.** An 80% prediction interval on Student's *t*, 18 degrees of freedom, carrying
both fitted-line uncertainty and residual scatter — deliberately not the naive
`1.28 × residual sd`, because **this forecast sits 2.6–3.0 standard deviations above the
training mean in the west**, where omitting the extrapolation term would understate the
interval by 20–28%. It reflects how wrong the method has been on past years, not how much
this week's 100 members disagree. **Testing** is leave-one-year-out throughout.

**Issuance dates.** Reforecasts exist only for Monday and Thursday issuances, **and the
reforecast suite lags the real-time forecast by about a week** — on 15 September the forecast
for the 14th was available but its reforecasts were not, so this run uses the 7th, the most
recent issuance with both. **Reproducing:** `iod_pipeline.run("2026-09-07")`.

![**(a)** Forecast anomaly in each box, 80% prediction intervals. **(b)** The dipole, calibrated and raw — the gap is the regression's amplitude correction, not bias removal. **(c,d)** Leave-one-year-out correlation against two persistence baselines; shading is the gain over the harder 30-day one.](assets/fig1_combined_2026-09-07.png){width=92%}

## Results

| Horizon | Valid | West box | East box | Dipole |
|---|---|---|---|---|
| Week 1 | 7 – 13 Sep | 28.62 °C (+0.92) | 28.27 °C (+0.16) | +0.76 ± 0.41 |
| Week 2 | 14 – 20 Sep | 28.80 °C (+1.00) | 28.23 °C (+0.12) | +0.88 ± 0.63 |
| Week 3 | 21 – 27 Sep | 28.78 °C (+0.84) | 28.28 °C (+0.11) | +0.73 ± 0.64 |
| Week 4 | 28 Sep – 4 Oct | 29.05 °C (+0.95) | 28.23 °C (+0.08) | +0.87 ± 0.52 |
| Days 1–30 | 7 Sep – 6 Oct | 28.87 °C (+0.95) | 28.25 °C (+0.11) | +0.84 ± 0.48 |

Absolute temperatures; brackets are the departure from the **2006–2025** average for the same
dates, dipole in °C with its 80% interval. That baseline is the reforecast period, not the
1991–2020 climatology BoM, CPC and NOAA use — **these anomalies are not directly comparable
with the dipole values those centres publish.**

The raw model dipole is smaller (+0.58 to +0.68). That difference is **the regression's
amplitude correction, not bias removal**: least squares with an intercept preserves the mean,
so constant bias cancels on both sides. What changes is amplitude — the west is stretched
(slope 1.10–1.32, the ensemble mean under-disperses it) and the east shrunk (0.66–0.74). Given
the verification below, that eastern shrinkage is the part to distrust.

## Accuracy

Leave-one-year-out correlation over the twenty reforecast years against persistence — "the
ocean stays as it is at issue". Gains carry an 80% bootstrap interval, resampling the (model,
persistence, observed) triples so the dependence between the predictors is kept.

| | Week 1 | Week 2 | Week 3 | Week 4 | Days 1–30 |
|---|---|---|---|---|---|
| **West** — model | 0.91 | 0.74 | 0.62 | 0.80 | 0.81 |
| persistence 30 d / 14 d | 0.79 / 0.80 | 0.69 / 0.68 | 0.70 / 0.69 | 0.75 / 0.74 | 0.78 / 0.77 |
| gain (80% interval) | +0.12 (−0.01, +0.23) | +0.05 (−0.09, +0.23) | −0.09 (−0.15, +0.08) | +0.05 (−0.05, +0.17) | +0.03 (−0.06, +0.16) |
| **East** — model | 0.90 | 0.81 | 0.80 | 0.86 | 0.87 |
| persistence 30 d / 14 d | 0.78 / 0.79 | 0.59 / 0.54 | 0.53 / 0.48 | 0.55 / 0.50 | 0.65 / 0.61 |
| gain (80% interval) | +0.12 (−0.00, +0.17) | +0.23 (−0.02, +0.35) | +0.27 (−0.00, +0.39) | **+0.30 (+0.06, +0.40)** | **+0.23 (+0.01, +0.33)** |

**Read this alongside the previous issuance, not on its own.** A week ago the only horizons
clearing zero were week 2 in *both* boxes; this week they are week 4 and the 30-day window in
the *east* only, and week 2 no longer clears. Shifting the sampling window by seven days — the
same twenty years, seven days later in each — moves the verdict almost entirely. With twenty
points per fit, which horizons "clear" is not a stable property of the method.

What does survive both runs is the **sign and rough size of the eastern gain at longer leads**:
+0.15 to +0.30 over 30-day persistence at weeks 2–4 in both issuances. That consistency is
more informative than any single interval. The west is inconsistent between runs — a +0.16
gain at week 2 last time, −0.09 at week 3 this time — and should not be claimed.

![Corrected SST anomaly at every horizon (°C vs the 2006–2025 observed average). Boxes: western (orange) and eastern (teal); land in tan. Grey ocean is where leave-one-year-out correlation falls below 0.4 and the forecast should not be relied on. Each cell is corrected by its own regression, observations averaged from 0.25° to the model's 1.5° grid. Fields are cubic-refined for contouring — presentational only, and the zero contour in particular is placed by the interpolation rather than measured.](assets/fig3_maps_2026-09-07.png){width=88%}

## Verification

The 7–13 September window is now fully observed, and two independent forecasts covered it:
this run's week 1, and the previous run's week 2 issued a week earlier.

| | this run (wk 1) | prev run (wk 2) | observed |
|---|---|---|---|
| West — calibrated | 28.62 (err −0.03) | 28.73 (err +0.08) | **28.65** |
| East — calibrated | 28.27 (err **−0.23**) | 28.31 (err **−0.18**) | **28.49** |
| East — **raw** | 28.47 (err −0.02) | 28.53 (err +0.04) | **28.49** |
| Dipole — calibrated | +0.76 (err +0.20) | +0.82 (err +0.26) | **+0.56** |

Three things follow. The shorter lead beat the longer one on the dipole, as it should.
Every error sits inside its 80% interval, so the uncertainty treatment is holding up across
three verified windows. But **the eastern calibration made the forecast worse in both runs**,
and by more than the western calibration helped: the raw eastern value was within 0.04 °C both
times, and shrinking it by a slope of ~0.7 introduced errors of 0.18–0.23 °C. That is the
shrinkage risk of a twenty-point fit, now observed twice rather than argued once. Since the
dipole is west minus east, an eastern box pushed too cool pushes the dipole too warm — which
is exactly the bias all three verifications show.

## Limitations

- **The eastern calibration has hurt in both verified runs.** Until more windows accumulate,
  read the eastern box and the dipole as upper estimates; the raw eastern value has been the
  better forecast twice.
- **Which horizons beat persistence is not stable between issuances.** Compare the accuracy
  table with the previous run's before quoting any single horizon. The durable finding is the
  eastern gain at weeks 2–4, present in both.
- **The baseline is 2006–2025, not 1991–2020**, and on a different SST analysis from BoM's, so
  these anomalies are not directly comparable with published dipole values.
- **Twenty years is a short training record**, and this forecast extrapolates 2.6–3.0 standard
  deviations beyond the training mean in the west. The interval accounts for that; the slope
  estimate still rests on twenty points.
- **The dipole is built from separately calibrated poles, and that choice is worth ~0.4 °C.**
  Calibrating each pole and differencing amplifies the raw dipole; regressing the observed
  dipole directly on the model dipole gives shrinkage instead. Ours verifies better
  out-of-sample on the reforecast years and is what was asked for, but the verifications above
  suggest revisiting it.
- **The interval is historical**, not ensemble-based; a version using the 100 members' spread
  is the obvious next step.
- **Persistence is given a one-day advantage** — its window ends on the init day and assumes
  same-day observations unavailable at issue — so the comparisons are conservative.
- **Map and box numbers differ by 0.15–0.35 °C**: correcting each cell then averaging is not
  the same calculation as correcting the box average. Quote the table for a box.
- **Box footprints differ slightly** between the 1.5° model and 0.25° observations, so part of
  the model–observation offset is footprint rather than model error.
- **One model only**, ECMWF S2S. GEFSv12 was considered and set aside.
