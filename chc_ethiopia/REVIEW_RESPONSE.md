# Response to CHC review — Kiremt & OND notebooks

Point-by-point response to the CHC (UCSB) review of the two reproductions. Each item
gives the reviewer's comment, our response, and — where a change was made — what we
did and the resulting number in the rebuilt notebooks. All figures below are from the
current executed notebooks, which now sit on **native CHIRPS v3.0** (0.05°, final;
June 2026 posted) over the deck's **1981–** record, with precipitation percentiles on
the **conditional (Bernoulli-)Gamma** CDF.

Legend: ✅ changed & verified · 💬 discussion / agreement (no change needed).

---

## 1 · Ethiopia Kiremt

**a. June CHIRPS is available (final ~15th of following month; prelim before).**
✅ Adopted. The observed layer is now native CHIRPS v3.0 — final for the completed
record and June 2026 (posted). This also resolves (f) and (j). We wired
`obs/chirps-v3-monthly` (final) and `obs/chirps-v3-monthly-prelim` into rosetta; the
notebooks fetch JJAS 1981–2026 directly.

**b. "normalize" — is it a conditional Gamma?**
✅ You were right to flag the wording — it was being used in the loose CS sense. The
operation is `deepscale.percentile_of`, previously an empirical mid-rank percentile,
**not** a conditional Gamma. We (i) added `method="gamma"` to `percentile_of` — a
conditional Bernoulli-Gamma (dry-fraction mass `p0` + method-of-moments Gamma on the
positive amounts), CHC's precipitation standard — and (ii) switched the percentile
maps to it and corrected the prose. Same clarification applies to the AGU abstract.

**c. June–July RHS panel looks surprisingly wet in the NE — were the models really
that wet for July?**
✅ Good eye — and it's misplacement, not real wetness (your point i). The
areal-mean NMME July over Ethiopia is slightly *dry* (near climatology), but the
model spreads what signal it has off the highlands, so the NE reads near-normal. The
forecast reliability we compute is **R² = 0.16** (deck's sub-seasonal ≈ 0.48). We
now say this explicitly on the §2 panel and in §8.

**d. §3 conclusion (El Niño like 1997/2015) is correct — note it's ONI, not RONI.**
💬 Agreed. The 2026 anchor is Niño-3.4 anomaly = **+1.66 °C** (ONI), nearest 1997/2015.
Confirmed it is ONI; difference from RONI is immaterial for analog selection.

**e. The §4 left scatter should have ONI on the x-axis, not RONI.**
✅ Fixed. The §4 scatter used genuine RONI while the §3 anchor used ONI — an internal
inconsistency. Both now use **ONI** (Niño-3.4 anomaly), one index throughout.

**f. ERA5 for JAS misses a lot in Ethiopia (CHIRPS has the station density).**
✅ Confirmed and fixed by (a). On native CHIRPS over the deck's 1981– record, the §4
ENSO–rainfall fit rises to **R² = 0.43** (was 0.37 on ERA5-from-1991); the deck
reports ≈ 0.5.

**g. §5 composite map is very similar to CHC's. Bravo.**
💬 Thank you — built entirely from `deepscale.complete()` + `frequency_below()`.

**h. §6 woreda-level analysis is compelling.**
✅ Now even better: native CHIRPS 0.05° resolves districts directly (no resampling
hack), **681/690 woredas** resolved; highland drill-down near Sebeta (Alem Gena) at
the 2nd percentile.

**i. The dynamical models don't do it well — sometimes they get the El Niño response
but put the dry signal in the wrong place (as in Southern Africa / Zimbabwe).**
💬 Agreed, and this is now the stated interpretation of the low skill in §8: the
teleconnection is right, the *placement* is wrong. We fold in the Southern-Africa
framing directly. (config A obs+analogs 37%/56% below 21st/33rd; config B
obs+forecast+analogs 36%/49% — the NMME July *softens* rather than sharpens.)

**j. In §10, ERA5 is not a reliable stand-in for CHIRPS (mean field, stations, IR).**
✅ Agreed — and with (a) the point is moot: we use CHIRPS. The §10 ERA5↔CHIRPS
correspondence section has been removed.

**k. Great to see the Ethiopia analysis re-created inside deepscale/rosetta.**
💬 Thank you.

---

## 2 · OND Ocean State

**a. We always use CHIRPS3 now.**
✅ Done — the rainfall-tercile colouring is computed from CHIRPS v3.0 over the EEA box.

**b. §3 forecasts look like Laura's and very extreme; WIO > 29 °C ↔ very heavy rains.**
💬 Agreed. 2026 WIO forecast = **+29.12 °C**, in the heavy-rains regime.

**c. Are you calculating RONI or ONI?**
✅ Clarified in-text: this notebook uses **genuine RONI** — Niño-3.4 anomaly minus the
20°S–20°N tropical-mean anomaly (L'Heureux et al. 2024). 2026 RONI = **+1.93 °C**.
(By contrast, notebook 1 uses ONI — the two decks make different choices.)

**c′. In the §3 time series Laura's forecasts look a bit better. Her recipe: (1) mean
across sims per model → regional SST; (2) mean across models per region/year;
(3) quantile-map.**
✅ Our pipeline is the **same three steps** (we take the regional average after the
model average — identical for a linear mean). To test whether any recipe truly does
better, we added an **out-of-sample bake-off (new §6e)**: leave-one-year-out, refit,
predict, correlate. RONI-clamp **0.82**, RONI-linear **0.82**, ONI-clamp **0.84** —
all within 0.02. So the recipes are equivalent to within skill; an apparent
time-series difference is the clamp reshaping the strongest years, not a skill gap.

**d. §6a clamping discussion is good — but CHC would champion different choices at
different stages (conservative long-lead clamp in June; a non-clamped forecast may be
more defensible now in August with RONI very high).**
✅ Adopted your framing: §6a now states the clamp-vs-linear choice is
**lead-dependent** — the cautious long-lead default in June, with the un-clamped
forecast the more defensible call by August.

**e. §6b — LOYO cross-validation is the more accurate assessment.**
💬 Agreed (RONI in-sample ±0.74 → LOYO ±0.84 °C, etc.).

**f. §6c — not convinced. WIO > 29 °C drives precipitable water / destabilization /
zonal winds. 2015's difference was the eastern IO not being cold (weak gradient / no
pIOD). It looks like 1997 is the year with weak relative-to-tropics warming.**
✅ **You are right and we conceded — §6c is rewritten.** The executed table confirms
your reading: **1997** (one of the wettest OND on record, EEA ≈ 7.5 mm/day) has the
*weakest* rel-to-tropics WIO warmth (**−0.03 °C**), while 2015 is +0.23. So the
trend-relative metric fails as a discriminator. §6c now argues, as you do, from the
**absolute WIO convective threshold** (~28–29 °C, physical, not a warming artefact)
plus the **IOD gradient** — with 2015 explained by its weak dipole (IOD 0.35 vs
~1.1–1.25 for 1997/2019/2023), i.e. the eastern pole wasn't cold.

**g. 6d — the June IOD forecast is surprisingly skillful; much of it is likely
ENSO-forced.**
✅ Agreed and reframed: June-init OND skill is RONI **r=0.84**, WIO **0.81**, IOD
**0.75** — the IOD is the *lowest*, but 0.75 across the predictability barrier is
genuinely high, and we attribute much of it to ENSO forcing (RONI is the most
skillful term). §6d now presents this as **high-but-lowest**, a point in the
outlook's favour rather than a caveat.

---

## Summary of changes

| Area | Change |
|---|---|
| Data | Observed layer → native **CHIRPS v3.0** (0.05°, 1981–, June 2026); OND terciles on CHIRPS3 |
| Method | `percentile_of(method="gamma")` conditional Bernoulli-Gamma (CHC standard); "normalize" wording corrected |
| Kiremt §4 | RONI → **ONI** (consistent with §3); R² 0.37 → **0.43** on CHIRPS/1981 |
| Kiremt §6 | Native 0.05° woreda choropleth, no resample (681/690) |
| Kiremt §2/§8 | Reframed as a dynamical-model **placement error** (misplaced El Niño dryness) |
| OND §6c | **Rewritten** — absolute WIO threshold + IOD gradient (trend-relative argument dropped) |
| OND §6a/§6d | Clamp = lead-dependent; IOD skill = high-but-lowest |
| OND §6e | New **out-of-sample recipe bake-off** (recipes within 0.02) |
