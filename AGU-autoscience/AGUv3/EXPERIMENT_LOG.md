# AGUv3 experiment log (append-only)

## 2026-07-31 — zone discovery built, validated, run

- **Motivation**: v2 recovered eHorn MAM predictability with a *hand-drawn* domain; the Funk
  critique's deeper point is that regionalization was the missing discovery step. v3 makes zones
  an output. Validation targets stated in advance: the orthogonal Kenya (~38°E meridional) and
  Somalia (~6–8°N zonal) boundaries; eHorn skill match; weak west-Kenya contrast.
- **Data**: `obs/chirps-v3-monthly` 33–52°E, 5°S–12°N, 1981–2023 via rosetta (new cache key, full
  HTTP download ~27 min, 267 MB). Integrity-gated: every month max>0 (NMME zero-fill lesson).
- **Smoke test** (clipped v2 eHorn file, scratchpad): pipeline end-to-end clean; discovered dry-core
  zone reproduced v2 hand-box MAM numbers exactly (0.79/0.77) through the independent mask path.
- **Bug found in smoke**: string-date `.sel(time="YYYY-MM")` returns 1-element array → `float()`
  TypeError; fixed with `.mean()` scalar reduction in `_preseason`.
- **Full run** (3564 land cells @0.25°, 17 features):
  - Stability: ARI 0.949 (k=2), 0.901 (k=3), ≤0.72 beyond. Pre-stated max-ARI rule → k=2;
    coarseness bias acknowledged, k=3/k=4 reported as hierarchy.
  - k=2 first split ≈ **Funk's EEA boundary** (eastern drylands vs highlands), Kenya boundary
    meridional at ~37–38°E.
  - k=3: eHorn zone (5.5°N, 43.9°E; discovered windows MAM+SON ≈ Gu/Deyr) → MAM
    P(dry|−WVG)=**0.79**, +La Niña=**0.77** (n=13) — exact v2 reference match on a discovered zone.
    Ethiopian-highlands zone JAS shows the sign-flipped El Niño→dry Kiremt signal (ROC 0.23).
  - k=4: northern Somalia (Golis) splits → Somalia η²(lat)=0.21 > η²(lon)=0.10 (zonal ✓);
    Kenya η²(lon)=0.52 ≫ η²(lat)=0.12 (meridional ✓); central-Kenya zone MAM weakens to
    0.64/0.62 (contrast ✓, moderate).
- **All four pre-stated acceptance criteria pass.** Caveats: shared 13 conditional years across
  zones (not independent tests); no multiplicity correction (targeted validation, not a search);
  v2's approximate-WVG / perfect-prog / small-n caveats inherit.
- Next candidates: wire discovered zones into the v1 tensor as the region axis; sweep the WVG box
  definitions; forecast-WVG (NMME) instead of perfect-prog; SHOWCASE render.

## 2026-07-31 (later) — SHOWCASE rendered; tensor search added; abstract drafted

- SHOWCASE.md/.pdf rendered (v2 pipeline, Jataware masthead); caption fix (annual-cycles figure
  is k=2, windows MAM+OND there vs MAM+SON at k=3).
- **`search.py`**: re-posed the v1 tensor question with the corrections as axes — zone(4, discovered)
  × window(discovered + MAM/OND) × index(nino34/iod/wpg/wvg/iwhg, AGUv1 defs) × lead(0–3) ×
  mode(sym Pearson | dry-tail AUC) = 520 cells; one shared permutation null (1,000 year-shuffles),
  one BH family α=0.10 (zonation inside the family). Obs-index/perfect-prog slice only;
  gcm_index/MOS/CCA deferred (CCSR restoration settling).
- **Results**: 79/520 survive. Recipes match operational drivers zone-by-zone: Kenya OND→IOD
  r=0.60; eHorn OND→Niño3.4/IWHG r=0.59–0.63, dry-AUC 0.79–0.80, persists to lead 3; highlands
  JAS→WPG sign-reversed r=0.57/AUC 0.78; MJJ Belg→IOD r=0.51 at lead 3.
- **Instructive absence**: no MAM cell survives either unconditional mode — the §3 conditional
  signal (0.79/0.77) is invisible to unconditional AUC over 42 years. Evaluation design is a
  search axis; a conditional-metric extension must be pre-specified before running (forking-path
  guard, noted in caveats).
- SHOWCASE retitled ("Autoscience discovery of an operational seasonal-forecast process"), §4
  search section + §7 AGU abstract draft added (agentic angle as subordinate clause; no
  colons/semicolons; closes with "…for which seasons, and at what lead intervals"). PDF re-rendered
  (587 KB) and visually verified.

## 2026-07-31 (later still) — Somalia acceptance claim downgraded to partial

- User flagged Somalia is near-uniform in the k=4 map. Diagnostic confirms: south-of-8N 98% one
  zone; north-of-8N 66% the SAME zone, only ~31% (Golis strip, ~9-10N) splits; stable at k=5/6.
  North–south monthly anomaly correlation r=0.73; similar standardized cycle shapes (north adds a
  weak Karan element). The eta2(lat)=0.21 "pass" was driven by the strip alone.
- Honest re-score: criterion "Somalia zonal split near 6-8N" → **partial** (boundary found is
  ~9-10N, strip only). Two readings kept in the SHOWCASE: feature set under-separates (amount
  discarded by standardization; arid-cell noise), or the operational ~8N cut is conservative
  relative to rainfall structure — skill evidence (identical 0.79/0.77 for full eHorn vs S-C
  Somalia) is consistent with the latter for forecast purposes.
- SHOWCASE §5 note added, acceptance table amended, README updated, PDF re-rendered.

## 2026-07-31 (cont.) — Kenya "meridian" claim precised

- User flagged the k=4 map: the red 38E line does not trace the yellow/blue divide. Correct — the
  discovered dryland boundary is DIAGONAL (crosses ~38E in northern Kenya, lies ~39-40E in the
  south). eta2 supports "longitude-organized," not "splits at a meridian." Notably the EEA
  operational definition is a corner ("east and south of ~38E, ~8N"), which a diagonal boundary
  matches better than a straight meridian. Caption, §2, and acceptance row reworded (pass → pass
  with caveat); red lines relabeled as literature reference marks, not discovered boundaries.
