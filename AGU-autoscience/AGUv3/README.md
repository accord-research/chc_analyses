# AGUv3 — discovered forecast zones (Kenya + Somalia)

The v1→v2 lesson made "region" the load-bearing flaw: v1 pooled skill over admin boxes and missed
the asymmetric eastern-Horn MAM signal; v2 recovered it, but with a **hand-drawn** domain taken
from the expert critique. v3 asks whether the pipeline can *discover* that regionalization from
rainfall structure alone — making the homogeneous sub-national zone an output, then chaining
zone → season window → teleconnection → asymmetric skill through it.

## Method (src/)

| script | what it does |
|---|---|
| `fetch_data.py` | one wide CHIRPS v3 field (33–52°E, 5°S–12°N, 1981–2023) — both validation gradients in frame |
| `zones.py` | k-means on two standardized feature blocks per 0.25°-coarsened cell: (1) 12-month cycle **shape**, (2) loadings on the leading 5 EOFs of monthly **anomalies** (interannual co-variability — zones are forecast units, not atlas units). k selected by year-bootstrap ARI stability; bimodal-aware windows (one per detected peak); per-country η² orientation statistic |
| `wvg_by_zone.py` | AGUv2's WVG machinery on zone masks and discovered windows (year-wrap-safe pre-seasons); symmetric metric reported alongside dry-tail / La-Niña-conditional metrics |
| `hierarchy.py` | k=3 and k=4 levels (both near the ≥0.9 ARI bar; max-ARI has a coarseness bias toward k=2) |
| `search.py` | the tensor search with the corrections as axes: zone(4) × window(discovered + MAM/OND) × index(5) × lead(0–3) × mode(sym \| dry-tail) = 520 cells, one permutation null (1,000 shuffles), one BH family at α=0.10 — zonation inside the multiplicity correction. Perfect-prognosis slice; gcm_index/MOS/CCA axes deferred |

## Acceptance criteria (stated in advance) and outcomes

The two known gradients are **orthogonal** — Kenya splits at a meridian (~38°E), Somalia at a
parallel (~6–8°N) — so latitude banding (the v0 fallback geometry) cannot pass both.

| criterion | outcome |
|---|---|
| Kenya meridional ~38°E split | ✅ with caveat: longitude-organized at every level (η²(lon)=0.52 vs η²(lat)=0.12 at k=4), but the boundary is diagonal — crosses ~38°E in the north, east of it in the south — matching the EEA "east and south of ~38°E/~8°N" corner rather than a strict meridian |
| Somalia zonal ~6–8°N split | ⚠️ partial: a Golis-highland strip at ~9–10°N separates (η²(lat)=0.21 > η²(lon)=0.10) but ~2/3 of the north stays with the south — N/S anomalies co-vary at r=0.73, so on these features most of Somalia is one regime; the ~8°N operational cut may be a conservative simplification (full-eHorn vs S-C-Somalia skill is identical) |
| discovered eHorn zone reproduces v2 hand-box MAM skill | ✅ exactly: P(dry\|−WVG)=0.79, +La Niña=0.77 (n=13) at k=3 and k=4 |
| western/central-Kenya zone shows weaker MAM signal | ✅ direction confirmed: 0.64/0.62 vs eHorn 0.79/0.77 (moderate, not null) |

Bonus: the Ethiopian-highlands zone surfaces the **sign-flipped** JAS/Kiremt teleconnection
(dry-tail ROC 0.23 ≡ 0.77 reversed — El Niño→dry Kiremt), the anti-phased regime that makes
pooled whole-domain evaluation destructive.

## Tensor-search results (`outputs/tables/search_results.md`)

**79/520 cells survive FDR.** Each zone's best surviving recipe matches its operationally
documented driver — Kenya OND→IOD (r=0.60), eastern-Horn OND/Deyr→Niño3.4/IWHG (r≈0.6, dry-AUC
≈0.8, persisting to lead 3), highlands JAS/Kiremt→WPG sign-reversed (q=0.025), MJJ/Belg→IOD at
lead 3 — none supplied to the search. **No MAM cell survives** under either unconditional mode:
the long-rains signal is conditional (−WVG/La-Niña subsets), so conditional evaluation is itself
a necessary search axis — the instructive negative result of the pass. An AGU abstract draft is
§7 of the SHOWCASE.

## Caveats

- The conditional rates across zones share the same 13 joint (−WVG ∧ La Niña) years — zones are
  not independent tests, and no multiplicity correction is applied: this is a targeted validation
  of pre-stated criteria, not an open search.
- Max-ARI k-selection is coarseness-biased (k=2 wins; k=3 ≈ as stable); we therefore report the
  hierarchy, with the pre-stated selection unchanged.
- Same v2 caveats inherit: approximate WVG, perfect-prognosis predictor, small conditional n.

Outputs in `outputs/figures` (zone maps k=2/3/4 with the expected splits overlaid, annual cycles,
stability curve) and `outputs/tables` (`zones_summary.md`, `wvg_by_zone.md`, `hierarchy.md`).
