# AGU Autoscience — versioned analyses

Treating seasonal-forecast **design** as a searchable space over the `rosetta` + `deepscale`
stack. Work is versioned so each pass is a self-contained, reproducible snapshot, with genuinely
general utilities factored to the top level.

## Layout

| Path | What it is |
|---|---|
| [`AGUv0/`](AGUv0/) | **Frozen** first pass (Nigeria + Ethiopia + Kenya): the SST-teleconnection search, the expert-audit response, and the finished SHOWCASE / abstract / report. Not re-run. |
| [`AGUv2/`](AGUv2/) | **Correction** (expert-review response): recovers the eastern-Horn MAM long-rains predictability AGUv1 mislabeled as absent, via a homogeneous domain + asymmetric dry-tail/La-Niña-conditional evaluation. |
| [`AGUv3/`](AGUv3/) | **Zone discovery + corrected tensor search**: makes the homogeneous sub-national region an *output* — clusters CHIRPS cells on cycle shape + interannual co-variability (stability-selected k), then chains zone → discovered season window → teleconnection → lead through an FDR-controlled 520-cell tensor. Rediscovers the EEA boundary, the meridional Kenya (~38°E) split (Somalia's ~8°N cut only partially — most of Somalia genuinely co-varies as one regime), v2's 0.79/0.77 exactly, and each zone's documented predictor recipe; MAM survives only conditional evaluation. AGU abstract draft in the SHOWCASE. |
| [`AGUv1/`](AGUv1/) | **Active** revised analysis: a formally specified search over a WMO-compliant objective-forecast design space, framed as *seasonality → rainy-season targets → lead ("when can a COF be held?")*, on one country. |
| [`REVIEW_RESPONSE.md`](REVIEW_RESPONSE.md) | Point-by-point response to the expert review of the AGUv1 abstract (the critique that drove v2 and v3), updated to reflect the final v3 results. |
| [`common/`](common/) | Version-agnostic utilities shared across passes — `style.py` (Jataware logo/brand, resolved from the shared `JATAWARE/style-resources`, never duplicated), and the IRIDL provider-fallback patch. |
| [`chc_blog/`](chc_blog/) | A scrape of recent UCSB Climate Hazards Center blog posts plus `REGIONAL_WIKI.md`, a by-region consolidation used to (a) choose the v1 target region and (b) cross-check our discovered patterns against CHC's published insight. |

## Conventions

- **The Jataware logo is never copied into an analysis dir.** Render scripts call
  `common.style.logo_path()`, which resolves the design-system copy in `JATAWARE/style-resources/`.
- **Data provider outages** (e.g. the CCSR NMME OPeNDAP) are handled by the labeled, temporary
  IRIDL fallback in `common/` — the analysis code stays provider-agnostic and canonical data
  overwrites the fallback on recovery. See `common/iridl_patch.py`.
- Each version keeps its own `EXPERIMENT_LOG.md`, `docs/`, `src/`, and `outputs/`.
