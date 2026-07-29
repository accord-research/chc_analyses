# Downscaling — method choice and the resolution/skill frontier

Downscaling is axes **K** (method) and **L** (target resolution) of the experiment matrix.
Its job: take a coarse (~1°) calibrated GCM/CCA tercile or continuous forecast and produce a
high-resolution (down to CHIRPS 0.05°) product that is *sharper* without being *false*.

## The two distinct questions

1. **Does downscaling add skill?** Can a downscaling method recover fine-scale variance
   (orography, coast, the south-north rainfall gradient) that verifies against CHIRPS at the
   fine grid — i.e., does fine-grid RPSS/GROC exceed what you get by naively interpolating
   the coarse forecast?
2. **Does downscaling add usable resolution even when it only holds skill?** Often the
   coarse forecast's skill is real but its *presentation* at 1° is too blocky for
   district-level decisions. A method that redistributes the skillful coarse signal onto a
   fine grid *consistently with observed fine-scale climatology* delivers decision value
   (sharper maps, admin-unit readouts) even at unchanged verified skill. Both outcomes are
   logged; they are different kinds of win.

## Methods to compare (DeepScale `downscale(method=...)`)

| Method | Mechanism | Adds skill? | Adds resolution? | Notes |
|---|---|---|---|---|
| **delta / interpolation** | regrid coarse anomaly onto fine climatology | baseline | cosmetic | the null model to beat |
| **BCSD** | bias-correct + spatial disaggregation vs. fine obs climatology | sometimes | yes | classic, robust, cheap |
| **QM / DQM** | (detrended) quantile mapping to fine obs distribution | distribution fix | yes | good for tercile calibration |
| **CCA** | statistical link coarse predictors → fine predictand patterns | yes, where a real cross-scale signal exists | yes | can genuinely add skill, not just detail |
| **rank-analog** | rank forecast in hindcast climatology, index into sorted fine obs climatology | inherits coarse skill | yes | the CHIRPS-GEFS-style construction; strong default |
| **CorrDiff (ML)** | diffusion model, learned fine-scale structure | potentially highest | yes | data/compute-heavy; the upper bound test |

## The frontier we report

For each downscaling config we plot **effective resolution added** (x) against **skill
retained/gained** (y), producing a Pareto frontier per season × zone:

```
skill
retained  ^
(GROC)    │        CCA ●            ● CorrDiff        ← "adds skill AND resolution"
          │   rank-analog ●
          │ BCSD ●   ● QM
          │────────────────────────────────────────  skill floor (config.yml)
          │ delta ●  (interpolation: resolution but no verified skill gain)
          └───────────────────────────────────────►  effective resolution (deg)
              1.0        0.25      0.1       0.05
```

- **Effective resolution** is estimated from the verified skill spectrum, not the nominal
  grid: a forecast on a 0.05° grid whose skill only verifies at 0.25° scales has *effective*
  resolution 0.25°. This prevents rewarding methods that merely upsample.
- **Skill floor** (default GROC > 0.5, `config.yml:skill.skill_floor_value`) marks the
  usable region; the selection rule is *maximize resolution subject to staying above the
  floor and inside the reliability band*.

## Where downscaling should matter most in Nigeria

- **The south (Guinea coast / Niger Delta):** strong rainfall gradients and coastal/orographic
  structure — the regime where fine-scale methods (CCA, CorrDiff) have the most real variance
  to recover, and where the coarse forecast is blurriest.
- **The Jos Plateau and the eastern highlands (Mambilla/Adamawa):** orographic enhancement
  invisible at 1°; a test case for whether downscaling recovers terrain-driven skill.
- **The Sudano-Sahel:** rainfall is smoother and more large-scale, so downscaling is expected
  to add resolution (presentation) more than skill — a useful contrast that the frontier
  should reveal automatically.

## Interaction with lead time (axis B)

Downscaling is applied to whatever coarse forecast the lead-sweep produces, so the frontier
is recomputed per init month. The expectation to test: added *resolution* is roughly
lead-invariant (it rides on fine-scale climatology), while added *skill* decays with lead in
step with the coarse forecast's skill. If true, that is a clean, quotable result — downscaling
buys presentation at all leads but only buys skill while the coarse signal is strong.
