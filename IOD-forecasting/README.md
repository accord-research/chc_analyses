# Rolling Indian Ocean SST & IOD forecasts

Weekly-refresh outlooks for Indian Ocean sea surface temperature in the two Dipole
boxes, and for the Dipole Mode Index, at five lead horizons — next 30 days and weeks
1–4. Requested by Chris Funk and Shraddhanand Shukla (CHC).

## What this does

One ECMWF S2S issuance in; calibrated western (WIO) and eastern (EIO) pole
temperatures, the dipole, and corrected SST maps out. The correction is a plain OLS
fit against NOAA OI SST across the 20 reforecast years attached to the same calendar
date — Funk's stated preference over quantile matching, since a straight line
continues a warming trend where a quantile map clamps to the historical range.

Both poles are carried as absolute temperatures and calibrated separately, then
combined. The dipole is reported twice — calibrated and raw — so the size of the
regression's amplitude correction is visible. These are **not** two climatologies: least
squares with an intercept preserves the mean, so the observed climatology cancels out of
the difference and what remains is the change in amplitude.

## Layout

| Path | What it is |
|---|---|
| `SCOPE.md` | Scoping memo: what was asked, what existed, what had to be built, and the plan |
| `iod_pipeline.py` | The pipeline. `run("YYYY-MM-DD")` is the whole thing — the init date is the only input |
| `refresh_outputs.py` | Regenerates every published artefact for one init; `refresh_alternatives()` does the experimental methods and the report's two diagnostics |
| `make_maps.py` | Map rendering (coastlines, skill masking) shared by the notebook and the report |
| `IOD_forecast.py` / `.ipynb` | Narrative notebook, percent-format source + executed output |
| `report/` | PDF outlook, markdown source and per-init figures |
| `chc-reference-materials/` | Funk's cdsapi download scripts and the October-rains deck that framed the task |
| `skill/` | The issuance process itself, with the report template and both mandatory audit prompts |
| `tools/py2nb.py` | Percent-`.py` → executed `.ipynb` (no jupytext in the shared env) |
| `outputs/` | Per-init CSV/netCDF and figures — regenerable, so gitignored |

## Running one

```python
import iod_pipeline as iod
res = iod.run("2026-08-31")        # forecast + reforecast + OISST, calibrated
```

Needs ECDS credentials for `c3s/ecmwf-s2s` (see acmadDL's README — ECDS is a separate
service from the Copernicus CDS, with its own key and licences). A run takes a few
minutes once the observational record is cached; the first OISST fetch is ~40 minutes.

**Valid init dates.** ECMWF files extended-range reforecasts on **odd calendar days of
the month**, and they are available the same day. Verified across two weeks and seven
weekdays: the 11th (Fri), 13th (Sun), 15th (Tue), 17th (Thu), 19th (Sat) and 21st (Mon)
each have a full 20-year suite — the 21st probed on the 21st itself — while the 12th (Sat)
and 16th (Wed) have none. Without training reforecasts a run cannot
calibrate and fails with `MarsNoDataError`, so a weekly job must land on an odd day —
`iod_pipeline.latest_usable_init()` walks back and probes cheaply for one.

> An earlier version of this README claimed Monday/Thursday issuances with a roughly
> one-week reforecast lag. That was inferred from four dates that happened to fit it and
> was wrong on both counts; the odd-day rule comes from Chris Funk and is confirmed above.

Rebuild the notebook and report:

```bash
python tools/py2nb.py IOD_forecast.py IOD_forecast.ipynb
cd report && pandoc IOD_outlook_<init>.md -o IOD_outlook_<init>.pdf --pdf-engine=xelatex
```

## Findings so far

Six issuances (31 Aug, 7, 13, 19, 27 Sep, 11 Oct 2026), twenty completed verification windows
covering fifteen distinct calendar spans.

- **A positive dipole at every horizon in every run**, +0.43 to +1.13 °C, driven throughout by a
  warm western box. The eastern box has stayed within 0.27 °C of normal.
- **The dipole has run too positive in seventeen of the twenty verified windows**, range −0.12 to
  +0.39 °C. Averaging the five spans scored twice gives fourteen of fifteen positive, mean
  +0.18 °C. Every error is inside its 80% interval, where sixteen of twenty would be expected at
  80%, and the mean absolute error is 0.38 of the interval half-width, so the dipole interval
  looks too wide rather than the forecast unusually accurate.
- **The eastern calibration has made the forecast worse in fifteen of twenty**, better in three
  and indistinguishable within 0.01 °C in two. The uncorrected eastern value is not uniformly
  accurate either, its own error reaching 0.26 °C.
- **Which combinations separate from persistence moves between issuances.** On 11 October the 80%
  interval on the gain over 30-day persistence clears zero at four of ten box and window
  combinations, all four in the west. On 27 September none of the ten did, and on 13 September
  four did and all four were in the east. The interval was corrected on 27 September, having
  previously bracketed an in-sample quantity while the gain beside it was measured out of sample,
  so counts from earlier issuances are not comparable with these two. Whether those earlier
  intervals ran narrower cannot be determined, and the mean width recorded was in fact larger at
  three of the four.
- **The headline persistence baseline is the weakest of the three tested.** On 11 October 30-day
  persistence scored below 14-day at all ten combinations and was the lowest of 7/14/30 at nine,
  so the count of combinations that separate from it is the largest of the three. The sweep is
  reported for that reason.
- **The eastern shrinkage is an amplitude problem.** Model spread in the east runs 1.08 to 1.29
  times the observed spread, and least squares sets the slope to correlation times observed over
  model spread, which is where the 0.65 to 0.82 eastern slopes of the 11 October issuance come
  from.
- **Pole interval coverage is near nominal.** Leave-one-year-out coverage across twenty years and
  ten box-window combinations is 77.5% against the 80% target. The dipole interval is constructed
  separately and is not covered by that check.
- **A cached observed series silently shortened the record.** Until 11 October each verification
  window was scored against its own cached OISST fetch. That cache stopped at 27 September, which
  left ten completed windows unscored, and it held pre-revision values that disagreed with a
  fresh retrieval by 0.095 °C on 14-20 September. All windows are now scored against one series
  retrieved per run. Ten of the twenty rows still verify inside OISST's two-week revision window,
  so their errors will move.

## Process

Issuance follows the `iod-outlook` skill (`ACCORD/.claude/skills/iod-outlook/`): pick an odd
calendar day with both suites available, run `refresh_outputs.py`, then
`refresh_outputs.refresh_diagnostics()` and `refresh_outputs.refresh_history()`, and
`refresh_outputs.refresh_alternatives()` only when the experimental methods are reported, write
the report from the skill's template, then run
a scientific/code audit and a separate stylistic audit before publishing. Both audits are
mandatory; each has caught errors that would otherwise have been published.
