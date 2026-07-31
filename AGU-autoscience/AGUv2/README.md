# AGU Autoscience v2 — correcting the eastern-Horn long-rains claim

A targeted correction, in response to an expert review, of the AGUv1 finding that the East African
MAM "long rains" have little seasonal-scale predictability. That reading was a methodological
artifact of (1) pooling skill over whole-country boxes that mix homogeneous and non-homogeneous
rainfall regimes, and (2) a symmetric, all-years skill metric applied to a one-sided (dry-tail)
teleconnection.

`src/recover.py` restricts to the homogeneous eastern-Horn (EEA) domain and to south-central Somalia,
and evaluates the Western-V Gradient (WVG) asymmetrically — below-normal discrimination and the
La-Niña-conditional dry hit rate. Over 1981–2023, the WVG's symmetric MAM correlation is ~0 (as v1
found), yet P(dry MAM | strong-negative WVG) ≈ 0.79 and P(dry | −WVG & La Niña) ≈ 0.77 — matching the
operational negative-WVG analog statistics. The MAM long rains are asymmetrically predictable for the
dry, La-Niña seasons that matter; the naive search averaged that signal away.

Data: eastern-Horn CHIRPS v3 (`data/ehorn_chirps_monthly.nc`, 38–50.5°E, 4.5°S–8.5°N, 1981–2023) +
cached ERSSTv5. Report: `SHOWCASE.pdf`.
