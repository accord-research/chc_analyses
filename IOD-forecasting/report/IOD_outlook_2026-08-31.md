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

**The forecast is for a positive Indian Ocean Dipole at every horizon**, of weak-to-moderate
amplitude: +0.43 °C over the first week, about +0.82 to +0.86 °C in weeks 2 and 3, and
+0.73 °C averaged over the next 30 days. This is driven almost entirely by a warm western
box, forecast at 28.4–28.8 °C, 0.7–1.0 °C above its 2006–2025 average for these dates. The
eastern box is close to normal, 0.1–0.3 °C above.

**A positive IOD developing through spring is the broad consensus** — the Bureau of
Meteorology, JAMSTEC, IRI and the WMO Global Seasonal Climate Update all forecast one. But
**our near-term values sit above the independent observed estimates**, and this should be
weighed before acting on the first week. The Bureau's index for the same week is +0.25 and
it calls the IOD *neutral*, having been below the +0.4 threshold for five consecutive weeks
with forecast magnitudes easing. Computed on our own data and baseline, the observed dipole
for that week is +0.01 against our forecast +0.43 — inside the stated interval, but at its
edge (see *Early verification*).

**The forecast is more accurate than persistence at weeks 2 to 4, and the eastern box is
where it earns its keep.** Against a 30-day persistence baseline, the eastern box gains
+0.15 to +0.21 in correlation at weeks 2–4. **Week 1 is not better than persistence** at any
baseline tested, and the **western box at week 4 is not either**. The useful range of this
product is weeks 2 to 4, and it is strongest in the east.

## Method

**Forecast model.** ECMWF S2S extended-range ensemble, issued 31 August 2026: 100 members,
46 daily steps, 1.5° grid. From the ECMWF Data Store (`ecds.ecmwf.int`), dataset
`s2s-forecasts`, variable `sea_surface_temperature`.

**Training data.** The reforecast set for the same calendar date (`s2s-reforecasts`) — the
same run for 31 August in each of the twenty years 2006–2025, 10 members each. The
correction is fitted on these twenty past forecasts.

**Observations.** NOAA OI SST v2.1, 0.25° daily, from NOAA PSL — the record CHC uses.

**Boxes.** Saji et al. (1999) dipole boxes. West 50–70 °E, 10 °S–10 °N; east 90–110 °E,
10 °S–0. Averages are area-weighted by cosine of latitude on each dataset's own grid.

**Lead windows.** Week 1 is forecast days 1–7, then 8–14, 15–21, 22–28, and 1–30. S2S SST is
filed as a 24-hour mean, so day 1 is the **day of the 00Z issuance**, not the day after —
week 1 therefore verifies 31 August to 6 September. The 30-day window includes the issuance
day, whose ocean state is already partly known.

**Correction.** For each box and window separately, a straight line fitted by ordinary least
squares — observed temperature against forecast temperature across the twenty reforecast
years — then applied to this year's forecast. Regression rather than quantile matching,
because a straight line continues a warming trend outside the historical range while
quantile matching pulls values back inside it.

**Uncertainty.** The 80% figure is a prediction interval on Student's *t* with 18 degrees of
freedom, carrying both the uncertainty in the fitted line and the residual scatter. It is
deliberately not the naive `1.28 × residual sd`: **this forecast sits 2.3–3.0 standard
deviations above the training mean in the western box**, so the extrapolation term is
substantial, and ignoring it understated the western interval by 20–28%. The interval
reflects how wrong this method has been on past years — not how much this week's 100 members
disagree with each other.

**Testing.** All accuracy figures are leave-one-year-out: the line is refitted without each
year, then used to predict it, so nothing quoted is measured on data used to fit it.

**Reproducing.** `iod_pipeline.run("2026-08-31")` in `experiments/IOD-forecasting/`; the date
is the only input. Reforecasts exist only for Monday and Thursday issuances, so those are the
valid init dates. Data via `acmadDL`, analysis via `africas2s`.

![**(a)** Forecast temperature anomaly in each box, with 80% prediction intervals. **(b)** The dipole index, calibrated and raw — the gap between them is the regression's amplitude correction, not bias removal. **(c,d)** Leave-one-year-out correlation over twenty past years against two persistence baselines; the shaded gap is what the model adds over the harder 30-day one.](assets/fig1_combined.png){width=100%}

## Results

| Horizon | Valid dates | West box | East box | Dipole |
|---|---|---|---|---|
| Week 1 | 31 Aug – 6 Sep | 28.36 °C (+0.70) | 28.36 °C (+0.27) | +0.43 ± 0.50 |
| Week 2 | 7–13 Sep | 28.73 °C (+1.03) | 28.31 °C (+0.21) | +0.82 ± 0.40 |
| Week 3 | 14–20 Sep | 28.81 °C (+1.02) | 28.26 °C (+0.16) | +0.86 ± 0.62 |
| Week 4 | 21–27 Sep | 28.78 °C (+0.83) | 28.28 °C (+0.10) | +0.73 ± 0.59 |
| Days 1–30 | 31 Aug – 29 Sep | 28.68 °C (+0.89) | 28.29 °C (+0.17) | +0.73 ± 0.42 |

Temperatures are absolute; brackets are the departure from the **2006–2025** average for the
same dates, dipole in °C with its 80% interval. That baseline is the reforecast period, not
the 1991–2020 climatology BoM, CPC and NOAA use — so **these anomalies are not directly
comparable with the dipole values those centres publish**.

The raw model dipole is smaller (+0.33 to +0.64). The difference between the raw and
calibrated columns is **the regression's amplitude correction, not bias removal**: least
squares with an intercept preserves the mean, so any constant bias cancels on both sides.
What the calibration changes is amplitude — it stretches the western box (slope 1.04–1.42,
i.e. the ensemble mean under-disperses it) and shrinks the eastern one (slope 0.62–0.80,
where the model over-amplifies variability). The calibrated dipole is the product; the raw
column is shown only so the size of that correction is visible.

## Accuracy

Leave-one-year-out correlation over the twenty reforecast years, against persistence —
"the ocean stays as it is at issue". Persistence is a hard baseline for SST, and how hard
depends on how long a window it averages, so both are shown.

| | Week 1 | Week 2 | Week 3 | Week 4 | Days 1–30 |
|---|---|---|---|---|---|
| **West** — model | 0.89 | 0.90 | 0.76 | 0.69 | 0.83 |
| West — persistence, 30 d | 0.85 | 0.74 | 0.68 | **0.71** | 0.81 |
| West — persistence, 14 d | 0.88 | 0.68 | 0.60 | 0.63 | 0.75 |
| **East** — model | 0.87 | 0.92 | 0.83 | 0.77 | 0.90 |
| East — persistence, 30 d | **0.87** | 0.77 | 0.62 | 0.60 | 0.79 |
| East — persistence, 14 d | 0.85 | 0.61 | 0.36 | 0.31 | 0.60 |

Read this carefully, because the choice of baseline changes the conclusion:

- **The east at weeks 2–4 is a genuine gain** — +0.15 to +0.21 over the 30-day baseline, and
  more against the 14-day one. This is the product's real contribution.
- **Week 1 is not an improvement on persistence** in either box, at any baseline tested.
- **The west at week 4 is not either** (0.69 model against 0.71 for 30-day persistence).

An earlier draft of this report used only the 14-day baseline and claimed the forecast beat
persistence at every horizon with a margin that grew with lead. That is true only for that
one window, which is the weakest of the three tested; it does not survive the 30-day
comparison and has been withdrawn.

Typical error of the corrected forecast is 0.15–0.29 °C (west) and 0.20–0.37 °C (east).

## Early verification

OISST is already available for the whole of the week-1 window, so that forecast can be
checked now.

| | forecast (calibrated) | forecast (raw) | observed | error |
|---|---|---|---|---|
| West | 28.36 | 28.47 | 28.23 | **+0.13** (interval ±0.22) |
| East | 28.36 | 28.65 | 28.65 | **−0.29** (interval ±0.36) |
| Dipole | +0.43 | +0.33 | **+0.01** | **+0.42** (interval ±0.50) |

Every error is inside its 80% interval, but two things deserve saying plainly. The dipole
error is close to the edge of the interval, and it is in the direction of the forecast being
**too positive** — consistent with BoM calling the IOD neutral for the same week. And in the
eastern box the **raw model was essentially exact (28.65 against 28.65 observed) while the
calibration moved it 0.29 °C the wrong way**. That is the shrinkage risk of a twenty-point
fit made concrete: the slope of 0.80 is estimated from twenty years and cannot know when a
given year does not need shrinking. One week is not a verification, but it is a reason to
treat the eastern calibration with some caution and to keep verifying.

## Limitations

- **Week 1 adds nothing over persistence**, and the west at week 4 adds nothing either. The
  value of this product is weeks 2–4, most clearly in the eastern box.
- **Near-term values run above independent estimates.** BoM has the IOD neutral (+0.25) for
  the week we forecast at +0.43; our own observations give +0.01 for that week. The
  disagreement on *direction over the season* is nil — everyone forecasts a positive IOD —
  but the near-term level should be treated as an upper estimate.
- **The baseline is 2006–2025, not 1991–2020.** Anomalies and the dipole here are not
  directly comparable with BoM, CPC or NOAA published values, which also use different SST
  analyses.
- **Twenty years is a short training record**, and this forecast extrapolates 2.3–3.0
  standard deviations beyond the training mean in the west. The interval accounts for that;
  the slope estimate itself still rests on twenty points.
- **The interval is historical**, not ensemble-based. A version using the 100 members' spread
  is the obvious next step.
- **Map and box numbers differ by 0.1–0.3 °C** — correcting each cell then averaging is not
  the same calculation as correcting the box average; quote the table for a box.
- **Box footprints differ slightly between model and observations** (cell-centre masking on a
  1.5° grid versus 0.25°), so part of the model–observation offset is footprint rather than
  model error. The intercept absorbs the constant part.
- **One model only**, ECMWF S2S. GEFSv12 was considered and set aside.
