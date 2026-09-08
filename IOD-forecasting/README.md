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
combined; the dipole is reported against **both** a model and an observed climatology.

## Layout

| Path | What it is |
|---|---|
| `SCOPE.md` | Scoping memo: what was asked, what existed, what had to be built, and the plan |
| `iod_pipeline.py` | The pipeline. `run("YYYY-MM-DD")` is the whole thing — the init date is the only input |
| `make_maps.py` | Map rendering (coastlines, skill masking) shared by the notebook and the report |
| `IOD_forecast.py` / `.ipynb` | Narrative notebook, percent-format source + executed output |
| `report/` | Two-to-three page PDF outlook, markdown source and figures |
| `tools/py2nb.py` | Percent-`.py` → executed `.ipynb` (no jupytext in the shared env) |
| `outputs/` | Per-init CSV/netCDF and figures — regenerable, written by a run; not committed |

> The CHC reference materials that framed this task (Funk's cdsapi download scripts and
> the October-rains deck) are not committed here — they are unpublished CHC material and
> live in the private `experiments` copy of this directory.

## Running one

```python
import iod_pipeline as iod
res = iod.run("2026-08-31")        # forecast + reforecast + OISST, calibrated
```

Needs ECDS credentials for `c3s/ecmwf-s2s` (see acmadDL's README — ECDS is a separate
service from the Copernicus CDS, with its own key and licences). A run takes a few
minutes once the observational record is cached; the first OISST fetch is ~40 minutes.

Rebuild the notebook and report:

```bash
python tools/py2nb.py IOD_forecast.py IOD_forecast.ipynb
cd report && pandoc IOD_outlook_<init>.md -o IOD_outlook_<init>.pdf --pdf-engine=xelatex
```

## Findings so far

- **Positive dipole at every horizon** for the 31 Aug 2026 init (+0.42 to +0.84 °C),
  driven by a warm western box 0.7–1.0 °C above its 2006–2025 average.
- **Skill beats persistence at every horizon and the margin widens with lead.** This
  matters: SST is so autocorrelated that a bare correlation says little. In the eastern
  box at weeks 3–4 persistence collapses to r≈0.31 while the model holds 0.77–0.82.
- **Week 1 adds little** over assuming no change — the product's value is weeks 2–4.

## Library work this required

- acmadDL **#11** — S2S `sst` silently returned 1 lead instead of 46 (ECDS needs
  explicit leadtimes for instantaneous fields; the MARS range shorthand only works for
  accumulated ones).
- acmadDL **#12** — `obs/oisst-v2-daily`, plus per-year file support in the opendap
  adapter (PSL files one NetCDF per year with no aggregation endpoint).
- africas2s **#9** — `lead_window_reduce`, `doy_climatology`/`doy_anomaly`, and the
  `eio` index.
