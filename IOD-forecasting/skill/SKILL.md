---
name: iod-outlook
description: Produce a weekly Indian Ocean SST and Dipole outlook report from an ECMWF S2S initialisation - run the pipeline, write the report from the template, then run the mandatory scientific/code audit and the stylistic audit before publishing. Use when asked to build, refresh, or reissue an IOD outlook, add an experimental method to it, or audit one.
---

# IOD outlook

Working directory: `experiments/IOD-forecasting` (private). The public mirror is
`chc_analyses/IOD-forecasting`. Python: `/opt/homebrew/Caskroom/miniforge/base/envs/accord-chc/bin/python`.

Every issuance follows the same five steps. **Steps 4 and 5 are not optional** —
each has caught errors that would otherwise have been published.

## 1. Choose the initialisation

ECMWF files extended-range reforecasts on **odd calendar days of the month**. Even days have no
reforecast suite. The forecast suite is also embargoed for the most recent two days, so the
newest usable init is typically 2–4 days back.

```bash
python -c "import iod_pipeline as iod; print(iod.latest_usable_init())"
```

`latest_usable_init()` probes the reforecast only. Confirm the *forecast* suite also resolves
before committing to a date — an embargoed forecast gives a false green.

## 2. Generate artefacts

```bash
python refresh_outputs.py 2026-09-19          # indices, dmi, figures, fields
python -c "import refresh_outputs as ro; ro.refresh_alternatives('2026-09-19')"
```

`refresh_outputs.py` owns every published artefact for the main analysis; `refresh_alternatives`
owns the experimental methods. Never compute a reported number by hand in a scratch script —
that is how the ARIMA dipole ended up on a different climatology from the other two methods in
the same table. If a number belongs in the report, a function in these two files must emit it.

Outputs land in `outputs/` keyed by init date; figures in `report/assets/` keyed by init date.
Per-init filenames are mandatory: shared filenames silently changed the figures in previously
issued reports.

## 3. Write the report

Copy `templates/report_template.md` to `report/IOD_outlook_<init>.md` and fill it. The template
carries the section order, what each section must state, and which output file each number comes
from.

**Three pages is the target and four is the ceiling.** Roughly 1200 words of prose, five tables
and two figures fits three pages at 10pt. Write to that budget from the start rather than
writing long and trimming, which wastes a pass.

Build with:

```bash
cd report && pandoc IOD_outlook_<init>.md -o IOD_outlook_<init>.pdf --pdf-engine=xelatex
```

Target 4–5 pages. Read the previous issuance first and carry forward the verification record.

## 4. Scientific and code audit (mandatory)

Spawn a subagent auditor. The prompt to use is in `templates/audit_prompts.md`. It must cover:

- **Leakage** — any path by which information after a forecast's initialisation reaches it: the
  model fit, the climatology, the verification values, the choice of any hyperparameter.
- **Like-for-like comparisons** — when two methods are compared, are they scored on the same
  years, with the same information available to each? State which is advantaged and why.
- **Every numeric claim in the report** reconciled against the CSV/JSON that produced it,
  including rounding. Report the correct value for any that does not reconcile.
- **Claims about our own record** across issuances — these have been wrong before, and the
  README is an independent check on them.
- **Whether anything in the report is not reproducible** from `refresh_outputs.py`.

Then work through every finding. Verify the substantive ones yourself before acting — an
auditor's mechanism can be right while its magnitude is overstated. Where a finding stands,
fix the code, not just the sentence. Where you disagree, say so and give the reason.

Recurring defect classes in this project, worth checking first:

| Class | What it looks like |
|---|---|
| Silent partial windows | A 7-day mean computed from fewer days. Use `_require_full_window`. |
| Stale or divergent cache keys | A fetch range that no other call refreshes returns old data. Share the pipeline's span. |
| Anomaly vs raw indices | `wtio`/`setio` are anomaly twins of `wio`/`eio`. Pole temperatures need the raw ones. |
| Climatology rebuilt twice | Recover it from published tables rather than recomputing. |
| Lead-day off-by-one | `stepType="avg"` means step 24 is the init day. `forecast(steps=h)[0]` is the step *after* training ends. |
| Claims outrunning n | Four verified windows is not a verification. Say the n. |

## 5. Stylistic audit (mandatory, last)

Spawn a second subagent, after the scientific fixes are in. Its only job is language. The
prompt is in `templates/audit_prompts.md`. The standard:

- Facts only. Every sentence states a measurement, a method, or a limitation.
- Terse, scientific, professional. No flourish in prose or in section titles.
- No overstatement. No claim stronger than its n supports.
- No hedging so heavy it obscures the meaning. One hedge, not two.
- Where a finding suggests earlier work was weaker than implied, phrase it as *"x may imply
  that y may overstate z"* — never as a retraction, and never assert that prior work was wrong.
- No writerly summarising line at the end of a section.

Four rules that a style audit tends to miss, because each can pass a check for brevity:

1. **Brevity is not the test — melodrama can be short.** "With the east near zero, the dipole is
   the western anomaly" and "Two cautions apply." are both compact and both unserious. A
   compressed epigram is a stylistic device, not plainer language. Write "almost all of the
   forecast dipole comes from the west" and simply state the cautions.
2. **No semicolons or colons in prose.** They have been used here to staple unrelated clauses
   together and to label paragraphs. Use full sentences. A `Label.` at the start of a sentence
   is acceptable in a bulleted limitation, nowhere else.
3. **Never use a statistic as shorthand.** "Two horizons clear zero" says nothing to a reader —
   two *what*, and *clearing* what? Say what was measured: "at two of the ten box and window
   combinations the forecast beats 30-day persistence by more than the uncertainty on that
   difference".
4. **Method is one short section of plain prose** saying what was done. Not a specification
   sheet of bolded `Model.` / `Training.` / `Windows.` labels, and not every parameter that
   exists. Degrees of freedom and dataset identifiers belong in the code, not the report.

It should return a list of specific sentences with replacements, not general advice. Apply them,
rebuild, and only then report the issuance as done.

## Adding an experimental method

Experimental methods live in the report's **"Alternative calibration and a statistical
reference"** section and in `refresh_alternatives()`. To add one:

1. Implement it in `iod_pipeline.py` next to the existing alternatives.
2. Emit its numbers from `refresh_alternatives()` into `outputs/<method>_<init>.csv`.
3. Score it against the standing calibration on **identical years** with a function like
   `arima_vs_model`, and state both directions of any information asymmetry.
4. Put it on the **2006–2025 window climatology** if you report an anomaly or a dipole, so it
   sits in the same column as the other methods.
5. Add it to the template's experiments section with its own subsection.
6. Add one short paragraph to the Abstract saying what was tested and what it showed. Two or
   three sentences, same register as the rest of the Abstract.

Current alternatives, for reference:

- `calibrate_pole_tendency` — observed anchor plus model tendency; nests 30-day persistence at
  `c = 0`. Scores worse than the standing calibration at every window.
- `arima_window_forecast` / `arima_skill` / `arima_vs_model` / `arima_forecast_dipole` —
  ARIMA(1,0,1) on the daily observed series. Beats the model at week 1, loses from week 2.

## Library changes

`acmadDL` and `africas2s` are editable-installed and shared across sessions. Follow the
five-step loop in `ACCORD/CLAUDE.md`: branch off current `main`, commit and push immediately,
open a PR, return to `main` after merge. Never leave a library checkout dirty or on an
unmerged branch.

## Standing facts

- Boxes: Saji et al. (1999). West 50–70 °E / 10 °S–10 °N; east 90–110 °E / 10 °S–0.
- Windows: days 1–7, 8–14, 15–21, 22–28, 1–30. **Day 1 is the init day** (`stepType="avg"`).
- Baseline: 2006–2025, the reforecast period — *not* the 1991–2020 climatology BoM/CPC/NOAA
  publish against. Say so whenever an anomaly is quoted.
- Observations: NOAA OI SST v2.1, 0.25° daily, from NOAA PSL. Revised for ~2 weeks after real
  time, so early verification numbers move slightly.
- Training: 20 reforecast years, 10 members each. Forecast: 100 members, 46 daily steps, 1.5°.
- Poles are calibrated separately then differenced. This amplifies the dipole relative to
  regressing the observed dipole on the model dipole; it is the requested design, and worth
  stating each time.
- Report anonymously. No collaborator names.
