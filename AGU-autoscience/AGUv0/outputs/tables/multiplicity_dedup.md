# Multiplicity de-duplication (audit S-F2)

BH-FDR recomputed over a de-duplicated family. **L1** = original (every season×band×index cell). **L2** = drop the composite `National` band (area-mean of the sub-bands) and the `wvg2`/`wvg3` indices (deterministic functions of `nino34`) — an objective removal of redundant cells, no cherry-picking. The **independent-signal count** then collapses collinear (season, cluster) groups, counting the ENSO/IOD/Atlantic family once per season, using the L2 q-values (not a min-p re-selection, which would double-dip).

Flagship = the strongest OND·IOD short-rains cell (the headline East-African signal).

| Country | Level | family size m | survivors q<0.05 | survivors q<0.10 | flagship | flagship r | flagship q |
|---|---|---|---|---|---|---|---|
| Nigeria | L1 original | 144 | 0 | 0 | JJA National·atl3 | +0.29 | 0.202 |
| Nigeria | L2 de-duplicated | 84 | 0 | 0 | JJA Middle·atl3 | +0.36 | 0.118 |
| Ethiopia | L1 original | 208 | 10 | 12 | OND South·iod_dmi | +0.56 | 0.017 |
| Ethiopia | L2 de-duplicated | 114 | 4 | 5 | OND South·iod_dmi | +0.56 | 0.011 |
| Kenya | L1 original | 160 | 27 | 35 | OND National·iod_dmi | +0.55 | 0.006 |
| Kenya | L2 de-duplicated | 96 | 12 | 13 | OND South·iod_dmi | +0.51 | 0.005 |

## Independent physical signals (q<0.10)

| Country | raw survivors (L1, q<0.10) | independent signals | the signals |
|---|---|---|---|
| Nigeria | 0 | 0 | — |
| Ethiopia | 12 | 3 | SON·enso_iod; OND·enso_iod; JAS·enso_iod |
| Kenya | 35 | 3 | OND·enso_iod; SON·enso_iod; ASO·enso_iod |

**Reading.** Two corrections, opposite in direction:

1. **The survivor _count_ is inflated** — the East-African OND short-rains signal is ~1 physical hypothesis (IOD/ENSO), counted 12+ times across composite bands, ENSO-derived indices, and collinear ENSO/IOD. Kenya's "27 survivors" and Ethiopia's "10" are a *handful* of independent signals, and this is what should be reported.

2. **The flagship q is _not_ ~5× optimistic.** Contrary to the audit's estimate, removing pseudo-replicates *lowers* the family size `m` faster than it changes the flagship's rank, so the flagship OND·IOD q is robust and if anything slightly *stronger* de-duplicated (Kenya 0.006→0.005; Ethiopia 0.017→0.011) — not 0.03. The pseudo-replication distorts the *count*, not the flagship's significance.

3. **Nigeria still has 0 survivors** at L2 — the "no West-African textbook-index signal survives" conclusion holds under de-duplication (this is the textbook-index family; the adaptive `sst_projection` winner is tested separately in `multiplicity_adaptive.md`).
