# AGU Autoscience — versioned analyses

Treating seasonal-forecast **design** as a searchable space over the `rosetta` + `deepscale`
stack. Work is versioned so each pass is a self-contained, reproducible snapshot, with genuinely
general utilities factored to the top level.

## Layout

| Path | What it is |
|---|---|
| [`AGUv0/`](AGUv0/) | **Frozen** first pass (Nigeria + Ethiopia + Kenya): the SST-teleconnection search, the expert-audit response, and the finished SHOWCASE / abstract / report. Not re-run. |
| [`AGUv1/`](AGUv1/) | **Active** revised analysis: a formally specified search over a WMO-compliant objective-forecast design space, framed as *seasonality → rainy-season targets → lead ("when can a COF be held?")*, on one country. |
| [`common/`](common/) | Version-agnostic utilities shared across passes — `style.py` (Jataware logo/brand, resolved from the shared `JATAWARE/style-resources`, never duplicated), and the IRIDL provider-fallback patch. |
| [`chc_blog/`](chc_blog/) | A scrape of recent UCSB Climate Hazards Center blog posts plus `REGIONAL_WIKI.md`, a by-region consolidation used to (a) choose the v1 target region and (b) cross-check our discovered patterns against CHC's published insight. |

## Conventions

- **The Jataware logo is never copied into an analysis dir.** Render scripts call
  `common.style.logo_path()`, which resolves the design-system copy in `JATAWARE/style-resources/`.
- **Data provider outages** (e.g. the CCSR NMME OPeNDAP) are handled by the labeled, temporary
  IRIDL fallback in `common/` — the analysis code stays provider-agnostic and canonical data
  overwrites the fallback on recovery. See `common/iridl_patch.py`.
- Each version keeps its own `docs/`, `src/`, and `outputs/`. Raw CHIRPS/ERSST
  NetCDF is not committed — regenerate it into each version's `data/` with the fetch
  scripts in `src/` (see the note in `data/`).
