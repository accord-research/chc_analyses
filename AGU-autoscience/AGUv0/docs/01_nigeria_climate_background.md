# Nigeria climate background — WAM rainfall, regimes, and drivers

Literature-grounded context for the experiment design. This is the physical prior that keeps
the autoscience search honest: a configuration the search selects must have a mechanism that
appears below, or it is treated as spurious. Citations are drawn from a verified literature
sweep; entries marked *(verify)* need author/DOI confirmation before the abstract is
submitted, and two known miscites are corrected explicitly at the end.

## 1. Rainfall climatology and the south–north gradient

Nigerian rainfall is organized by the **West African Monsoon (WAM)** and the seasonal
meridional march of the tropical rain belt / ITCZ (more precisely the inter-tropical
discontinuity, ITD, at the surface). The dominant feature is a steep **south-to-north
rainfall gradient**: from >2000 mm yr⁻¹ on the Guinea coast and southern highlands
(~4–6°N) down to <400–600 mm yr⁻¹ at the Sahel margin (~14°N and beyond). This gradient,
not longitude, is the organizing axis of Nigerian climatology, and it is why *no single
national forecast configuration is optimal* — the predictability regime changes with
latitude.

**The monsoon "jump."** The rain belt tracks the ITCZ northward through spring, then jumps
abruptly from the Guinea coast (~5°N) to the Sahel (~10°N) in **late June–early July**,
after a "preonset" stage (~mid-May) marking the ITF's arrival near 15°N; Sahel rains decay
from **late September into October** (Sultan & Janicot 2003, *J. Climate*).

## 2. Rainfall regimes: bimodal coast vs. unimodal Sahel

The annual cycle changes character with latitude — the single most important fact for
choosing forecast seasons:

- **Guinea coast (~4–8°N): bimodal.** Two rainfall peaks — a main peak around **May–June**
  and a secondary peak around **September–October** — separated by the **"August break"**
  (little dry season), a relative August minimum that occurs when the rain belt is at its
  northernmost (Sahel) position and coastal conditions are least favorable (Adejuwon &
  Odekunle 2006, *J. Climate* *(verify)*). The two peaks are the ITCZ passing overhead twice.
- **Middle belt / Guinea savanna (~8–10°N): transitional.** The bimodal signature weakens
  into a broad single wet season.
- **Sudano-Sahel (~11–14°N): unimodal.** A single **July–August–September (JAS)** peak —
  the deep-monsoon core, short and intense.

**Onset/cessation and growing-season length.** Onset advances from the south (coast: as
early as Feb–Mar) to the far north (late May–June); cessation is earliest in the north
(Sep–Oct), so the wet season *shortens northward* (Odekunle 2004, *Int. J. Climatology*;
Fontaine & Louvet 2006, *JGR-Atmos*, for an objective Sudan–Sahel onset index).

**Conventional homogeneous zones (S→N):** Guinea/coastal (~4–8°N), Guinea savanna / mid-belt
(~8–10°N), Sudan savanna (~10–12°N), Sahel / Sudano-Sahelian (~12–16°N). These latitudinal
belts are the standard basis for zonal rainfall analysis (Nicholson 2013, *ISRN Meteorology*,
review *(verify)*). [`src/seasons.py`](../src/seasons.py) *re-derives* homogeneous zones by
clustering the observed annual cycle, so the zones used downstream are data-driven rather than
imposed — and are checked against these conventional belts.

## 3. SST teleconnections — what drives which season and region

The WAM has *no single dominant ocean basin*; the ranking of drivers is season-, region-, and
epoch-dependent (non-stationary). The autoscience predictor screen
([`docs/03_teleconnections.md`](03_teleconnections.md)) tests each of these empirically for
Nigeria; the mechanisms below are the priors it is tested against.

| Driver (index) | Sign / mechanism | Season | Nigeria region most affected | Key refs |
|---|---|---|---|---|
| **ENSO** (Niño3.4) | El Niño warms the tropical troposphere → stabilization, weaker monsoon convergence → **drier** | JAS | Sahel (interannual) | Sheen et al. 2017; Rowell 2001 *(verify)*; Mohino et al. 2011 |
| **Atlantic Niño / ATL3** (3°S–3°N, 20°W–0°) | Warm equatorial Atlantic → rain belt held south → **wetter Guinea coast, drier inland**; leads coast rainfall ~2 mo | JJA–summer | Guinea coast | Worou et al. 2022 (*ESD*); *npj Clim. Atmos. Sci.* 2024 *(verify)* |
| **Atlantic interhemispheric gradient** (TNA−TSA) | Warm-north/cool-south pulls ITCZ **north → wetter Sahel** (and reverse) | JAS | Sahel vs. coast dipole | Rodríguez-Fonseca et al. 2011; Sheen et al. 2017 |
| **Mediterranean SST** | Warm E. Med → northerly moisture advection across the desert → **wetter Sahel** | JAS | Sahel | Rowell 2003 (*J. Climate*) |
| **Indian Ocean / IOD** | Basin warming → westward-propagating stabilization → **drier Sahel** (strong on decadal scale) | JAS | Sahel | Giannini et al. 2003 (*Science*); Bader & Latif 2011 |
| **Western V Gradient (WVG)** (Pacific) | Designed for **East Africa** (Walker-cell subsidence over *eastern* Africa) — **untested for West Africa** | (MAM, E. Africa) | *hypothesis to test* | Funk et al. 2014, 2018, 2023 |

**Decadal non-stationarity.** Atlantic-vs-Pacific dominance and the ENSO–Sahel link are
non-stationary; the ENSO–Sahel teleconnection strengthened after the 1970s, and multi-decadal
Sahel rainfall reflects competition among the AMO (positive → wetter), the IPO/Pacific
decadal variability and global warming (→ drier) (Mohino et al. 2011; Rodríguez-Fonseca et
al. 2011). *Implication for autoscience:* skill and the winning predictor can drift across the
hindcast period, so the search reports skill over a fixed CV window and flags epoch
sensitivity rather than assuming stationarity.

**Relative rank.** For the **Sahel monsoon (JAS)** the controls are remote/basin-wide —
Atlantic meridional gradient, Mediterranean, Indian Ocean (decadal), ENSO (interannual) — with
no permanent leader. For the **Guinea coast**, the **local equatorial Atlantic (Atlantic Niño)**
dominates boreal summer, with an *inverse* rainfall relationship to the Sahel. This
coast/Sahel inversion is exactly why per-zone predictor selection (axis C×G in the matrix)
should beat one national model.

## 4. Documented forecast skill (what "good" looks like here)

- **Skill is higher over the Sahel than the Guinea coast, and peaks in the JAS monsoon** —
  a direct consequence of stronger large-scale SST control on Sahel rainfall (S2S evaluation,
  MDPI *Atmosphere* 2025 *(verify)*; consistent with NMME studies below).
- **NMME Sahel JAS skill is low-but-real**, and is largely explained by how well models
  predict eastern-Mediterranean and equatorial-Pacific SSTs and their teleconnections
  (Martín-Gómez & Mohino 2022, *Clim. Dyn.* *(verify author list)*); lead-time gains in
  Giannini et al. 2020 (*GRL*).
- **Multi-year Sahel skill exists** (N. Atlantic + Mediterranean warming → meridional moisture
  convergence), distinct from interannual ENSO-driven skill (Sheen et al. 2017, *Nat.
  Commun.*).
- **Dynamical WAM onset is skillful at ~2–3 month lead, tied to tropical Atlantic June SST**
  (Vellinga et al. 2013, *Clim. Dyn.*).
- **RCOF operational skill (PRESAO/PRESASS):** tercile-probability outlooks show skill for the
  above- and below-normal categories but weak sharpness and poor near-normal skill; max
  economic value Vmax ≈ 0.39 (dry) / 0.34 (wet) over JAS 1998–2013 (Bliefernicht et al. 2019,
  *JAMC*). The West African RCOF is now split into **PRESASS** (Sudano-Sahel; covers Nigeria)
  and **PRESAGG** (Gulf of Guinea), under ACMAD + AGRHYMET/RCC-ECOWAS.
- **Statistical downscaling** (CCA / CPT / PyCPT, and stochastic disaggregation) is the RCOF
  workhorse over West Africa (Houngnibo et al. 2023, *Int. J. Climatology*). *No single
  definitive PyCPT-over-Nigeria headline-skill paper was found* — a gap the hindcast harness
  is positioned to fill.

## 5. Corrections and caveats carried into the abstract

- **There is no verifiable distinct "Funk et al. 2019" Western-V paper.** The WVG lineage is
  **2014 (HESS, West Pacific Gradient), 2018 (QJRMS, "Western V" pattern), 2023 (Earth's
  Future, WVG index)** — all Greater-Horn-of-Africa / East-Africa targeted.
- **Rodríguez-Fonseca et al. 2011 is in *Atmospheric Science Letters*,** not *Climate
  Dynamics* (common miscite).
- **The WVG's relevance to West Africa is untested in the published literature** — a genuine,
  defensible novelty hook, but one to frame as an *empirical hypothesis*, since WAM physics
  points to Atlantic/Mediterranean/Indian/ENSO forcing rather than a Pacific Walker-cell
  control on the Sahel.
