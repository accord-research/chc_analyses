---
title: "Indian Ocean SST and Dipole Outlook"
subtitle: "Forecast issued <D MONTH YYYY> · covering <D MONTH> – <D MONTH YYYY>"
author: "ACCORD / CHC — draft for review"
date: "<D MONTH YYYY, the write-up date>"
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

<!--
HOW TO USE THIS TEMPLATE
Each section below carries an instruction block saying what it must state and which output
file each number comes from. Delete the instruction blocks as you fill them.

Rules that apply throughout:
  - Every number must come from a file in outputs/ emitted by refresh_outputs.py or
    refresh_alternatives(). Read the CSV; do not transcribe from a previous report or
    from a scratch calculation.
  - Round once, from the source CSV. Rounding an already-rounded value has produced
    wrong interval bounds before.
  - Anomalies are against 2006-2025, not 1991-2020. Say so wherever one is quoted.
  - Never claim more than n supports. State the n.
  - No collaborator names anywhere.

Length: three pages, four at the very most. About 1200 words of prose alongside the
tables and figures. Write to that budget rather than writing long and cutting.

Language, enforced by the stylistic audit in step 5 of the skill:
  - No semicolons or colons in prose. Use full sentences.
  - Brevity is not the test. A compressed epigram ("With the east near zero, the dipole is
    the western anomaly") is a stylistic device and does not belong here, however short.
  - Never use a statistic as shorthand. "Two horizons clear zero" is meaningless. Say what
    was measured and against what.
  - Bold locates a figure. It is not for emphasis - never bold a whole clause or sentence.
  - No evaluative adjectives or adverbs: "naive", "harder", "decisively", "notably",
    "the clearest improvement", "the part to distrust", "the obvious next step".
  - No interpretive framing asserted as fact: "the durable finding is", "the substantive
    development is", "the one recurring result".
  - No instruction to the reader ("read the pattern rather than..."), and no summarising
    line closing a section.
  - State a caution at most twice: once in the Abstract, once in Limitations. A third
    occurrence in the body is redundant.
-->

## Abstract

<!--
Four short paragraphs, no more:
  1. The headline dipole values. Week 1 and days 1-30 at minimum, and the direction of
     change from the previous issuance. Source: outputs/dmi_<init>.csv.
  2. The physical signature - which pole is driving it, with both boxes' anomaly ranges.
     Source: outputs/indices_<init>.csv, anomaly_C.
  3. One paragraph on method and on what the skill evidence supports, across issuances
     rather than this one alone. Check claims about the record against every
     outputs/indices_*.csv and against README.md - cross-issuance claims have been
     wrong here before.
  4. The cautions that qualify the headline, from the verification record. If the
     forecast has a known directional bias, it belongs here.
  5. Two or three sentences on any experimental method tested this issuance - what it was
     and what it showed. Same register as the rest of the Abstract.
-->

## Method

<!--
ONE SHORT SECTION of plain prose saying what was done. Three or four paragraphs, no more.
NOT a specification sheet - no bolded "Model." / "Training." / "Windows." labels, and not
every parameter that exists.

Cover, in prose: the forecast and its matching reforecast; the observations; the boxes and
the area weighting; the five windows and that day 1 is the day of issue; that a straight
line of observed on forecast temperature is fitted across the reforecast years and applied
to this year; why regression rather than quantile matching; what the 80% intervals are and
what they describe; that accuracy is leave-one-year-out; that reforecasts exist only on odd
calendar days; and the one-line reproduction command.

Leave out degrees of freedom, dataset identifiers and grid counts unless they change how a
number should be read. They are in the code.

If a lead-indexing convention differs from a collaborator's pipeline, one clause. Do not
argue it.
-->

![**(a)** Forecast anomaly in each box, 80% prediction intervals. **(b)** The dipole, calibrated and raw — the gap is the regression's amplitude correction, not bias removal. **(c,d)** Leave-one-year-out correlation against two persistence baselines; shading is the gain over the 30-day baseline.](assets/fig1_combined_<init>.png){width=92%}

## Results

<!--
The five-row table: horizon, valid dates, west box, east box, dipole with its 80%
interval. Absolute temperatures with the anomaly in brackets.
Source: outputs/indices_<init>.csv and outputs/dmi_<init>.csv.

Then one paragraph stating the baseline caveat, and one on what the regression did to
the amplitude - quote the actual slopes from the CSV. Do NOT assert a fixed direction
for the west; it has been above and below 1 in different runs. Least squares with an
intercept is mean-preserving, so the calibrated-minus-raw gap is amplitude, not bias
removal - state that, it is repeatedly misread.
-->

## Accuracy

<!--
Leave-one-year-out correlation against persistence, with 80% bootstrap intervals on the
gain. Source: outputs/persistence_sensitivity_<init>.csv, and gain30* in the indices CSV.

Show both the 30-day and 14-day persistence baselines. If the model loses to 7-day
persistence at short lead, say so - it is the honest read and it is consistent with the
experimental section.

State how many horizons clear zero this run, and the pattern across all issuances so far.
Verify the cross-issuance claim against every outputs/indices_*.csv before writing it.
-->

![Corrected SST anomaly at every horizon (°C vs the 2006–2025 observed average). Boxes: western (orange) and eastern (teal); land in tan. Grey ocean is where leave-one-year-out correlation falls below 0.4 and the forecast should not be relied on. Each cell is corrected by its own regression, observations averaged from 0.25° to the model's 1.5° grid. Fields are cubic-refined for contouring — presentational only, and the zero contour in particular is placed by the interpolation rather than measured.](assets/fig3_maps_<init>.png){width=88%}

## Alternative calibration and a statistical reference

<!--
THE EXPERIMENTS SECTION. Self-contained: a reader must be able to evaluate it without
the rest of the report. One subsection per method. Source: outputs/tendency_<init>.csv,
outputs/arima_vs_model_<init>.csv, outputs/arima_forecast_<init>.csv, all from
refresh_alternatives().

Open by saying these are reported alongside the standing calibration, not in place of
it, and name any information asymmetry shared by all of them.

For each method, in this order:
  - The equation or model, in one line.
  - Out-of-sample skill against the standing calibration, on IDENTICAL YEARS. State the
    years and the n.
  - Coefficient stability where a coefficient is the question: quote the standard error
    or t-statistic, not a comparison of two initialisations.
  - Where it is worse, and where it is better. Both.
  - Any correction applied to make the comparison fair, and whether that correction is
    itself clean. If a correction introduces a second distortion, say the two are
    confounded rather than reporting one as the answer.

Then BOTH DIRECTIONS of every asymmetry. A statistical method using the observed state
at issue favours it; refitting the regression leave-one-year-out on all years favours the
regression. Disclosing only one is not honest.

Then the live forecast table: every method's dipole, all on the 2006-2025 window
climatology so they occupy one column. Differing baselines moved the dipole by 0.13 C
when this was missed.

Close with "Bearing on the main analysis": what this implies for claims made earlier in
the report. Phrase as "x may imply that y may overstate z". Attribute the implication only
to the method that supports it. Do not retract; do not say prior work was wrong. State
plainly that neither alternative is proposed as a replacement, and why.

Attach no interval you have not computed, and say that none is attached.
-->

## Verification record

<!--
One row per completed window from every prior issuance, cumulative.
Source: iod_pipeline.verify(init, window) - never computed by hand. It recovers the
climatology from the published tables so it cannot drift, and refuses a window the
observations do not fully cover.

Columns: window, forecast, observed, error, and the raw-vs-calibrated comparison for
whichever pole the calibration is suspect in.

Then state which patterns hold across ALL rows, with the count. If every error is inside
its interval, say so.
-->

## Limitations

<!--
Bulleted, one line each, most material first. Always include:
  - Any known directional bias, with the per-window errors.
  - Any part of the calibration that verification shows is hurting.
  - That the gain over persistence depends on which persistence is used.
  - That which horizons clear significance moves between issuances.
  - The 2006-2025 baseline, and non-comparability with published dipole values.
  - Training length and the extrapolation distance.
  - That poles are calibrated separately then differenced, which amplifies the dipole.
  - That the interval is historical, not ensemble-based; and that the experimental
    methods carry no interval.
  - Persistence's one-day advantage.
  - That map and box numbers differ; quote the table for a box.
  - Single model.
-->
