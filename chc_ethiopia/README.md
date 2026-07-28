# CHC Ethiopia — Kiremt & OND outlooks

Two CHC / FEWS&nbsp;NET forecast decks, reproduced figure-by-figure with `rosetta`
(data access) and `deepscale` (analysis).

| Notebook | Reproduces | Rendered |
|---|---|---|
| [`1_Ethiopia_Kiremt_outlook.ipynb`](1_Ethiopia_Kiremt_outlook.ipynb) | *"Ethiopia Likely to Experience Very Poor Rains in 2026"* (Chris Funk) — the June–September **Kiremt** outlook, via the SMPG workflow (season-to-date monitoring, El-Niño analogs, dynamic forecast, West-Pacific teleconnection). | [PDF](1_Ethiopia_Kiremt_outlook.pdf) |
| [`2_OND_ocean_state_outlook.ipynb`](2_OND_ocean_state_outlook.ipynb) | *"IOD, Western Indian Ocean & RONI outlook for June 2026"* (Laura Harrison & Chris Funk) — the OND short-rains **ocean-state** outlook (RONI, IOD, western-Indian-Ocean warmth). | [PDF](2_OND_ocean_state_outlook.pdf) |

- `data/` — the Ethiopia admin-3 (woreda) boundaries used for zonal reporting.
- `reference/` — the two source CHC decks (`.pptx`) each notebook reproduces.

Every data pull is a `rosetta.fetch(...)` and every analysis step a `deepscale`
call, so each notebook is self-contained and re-runnable end to end.
