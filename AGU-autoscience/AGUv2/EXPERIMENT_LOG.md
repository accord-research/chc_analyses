# EXPERIMENT LOG — AGU Autoscience v2 (eastern-Horn long-rains correction)

## 2026-07-28 — corrected the AGUv1 MAM "unpredictable" claim (expert-review response)

Prompted by an expert review (CHC/FEWS NET) of the AGUv1 abstract's claim that the East African MAM
long rains have little seasonal-scale predictability. Confirmed the claim was a methodological
artifact of (1) whole-country domains mixing homogeneous + non-homogeneous regimes (western Kenya,
northern Somalia) and (2) a symmetric, all-years metric applied to a one-sided (dry-tail) signal.

**Method** (`src/recover.py`): eastern-Horn (EEA) CHIRPS v3, 38–50.5°E/4.5°S–8.5°N, 1981–2023 (n=43,
fetched to `data/`), + cached ERSSTv5. WVG = z(Niño3.4) − z(Western-V) from pre-season (Jan–Feb) SSTs.
Evaluated symmetrically (all-years LOYO corr) AND asymmetrically (below-median discrimination;
strong-negative-WVG and La-Niña-conditional dry rates). Also ran south-central Somalia (42–48°E,
1–6°N) specifically, per the reviewer.

**Result (recovery):** MAM symmetric corr = −0.21 (reproduces v1's ~no-skill), but P(below-median MAM
| strong-negative WVG) = 0.79 and P(below-median | −WVG & La Niña) = 0.77 (n=13), vs ~0.5 base —
matching CHC's operational negative-WVG analog statistics (~75–80%). South-central Somalia comparable.
OND control: WVG link weaker (IOD/WPG is its driver). Validation: WVG strongly negative in the dry
analog years (1999 −2.22, 2011 −2.17, 2021 −2.91, 2022 −1.97); La-Niña classification recovers CHC's
analog set.

**Finding:** the MAM long rains ARE asymmetrically predictable for the dry, La-Niña seasons that
matter; naive automated search misses it without domain-guided regionalization + conditional,
tail-focused evaluation. The AGUv1 abstract's MAM claim is retracted; the response (with these
numbers) is in `../REVIEW_RESPONSE.md`. Caveats: WVG is an approximation, perfect-prognosis
predictor, small conditional samples.
